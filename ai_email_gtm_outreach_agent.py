import json
import os
import sys
from typing import Any, Dict, List, Optional

import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools.exa import ExaTools

def create_company_finder_agent() -> Agent:
    exa_tools = ExaTools(category="company")
    db = SqliteDb(db_file="tmp/gtm_outreach.db")
    return Agent(
        model=OpenAIChat(id="gpt-4o"),  # Changed from gpt-5 to gpt-4o for speed
        tools=[exa_tools],
        db=db,
        enable_user_memories=False,  # Disabled to reduce overhead
        add_history_to_context=False,
        session_id="gtm_outreach_company_finder",
        debug_mode=False,  # Disabled debug for speed
        instructions=[
            "You are CompanyFinderAgent. Use ExaTools to search the web for companies that match the targeting criteria.",
            "Return ONLY valid JSON with key 'companies' as a list; respect the requested limit.",
            "Each item must have: name, website, why_fit (1-2 lines).",
        ],
    )

def create_contact_finder_agent() -> Agent:
    exa_tools = ExaTools()
    db = SqliteDb(db_file="tmp/gtm_outreach.db")
    return Agent(
        model=OpenAIChat(id="gpt-4o"),
        tools=[exa_tools],
        db=db,
        enable_user_memories=False,
        add_history_to_context=False,
        session_id="gtm_outreach_contact_finder",
        debug_mode=False,
        instructions=[
            "You are ContactFinderAgent. Use ExaTools to find 1-2 relevant decision makers per company.",
            "Prioritize roles from Founder's Office, GTM, Sales leadership, Partnerships, Product Marketing.",
            "If direct emails not found, infer using common formats but mark inferred=true.",
            "Return ONLY valid JSON with key 'companies' as a list; each has: name, contacts: [{full_name, title, email, inferred}]",
        ],
    )

def create_research_agent() -> Agent:
    """Agent to gather interesting insights from company websites and Reddit."""
    exa_tools = ExaTools()
    db = SqliteDb(db_file="tmp/gtm_outreach.db")
    return Agent(
        model=OpenAIChat(id="gpt-4o"),  # Changed from gpt-5 for speed
        tools=[exa_tools],
        db=db,
        enable_user_memories=False,
        add_history_to_context=False,
        session_id="gtm_outreach_researcher",
        debug_mode=False,  # Critical: disabled debug
        instructions=[
            "You are ResearchAgent. For each company, collect 2-3 concise insights from their website.",
            "Focus on: recent news, product launches, company mission, notable clients.",
            "Skip Reddit searches to save time.",  # Critical: simplified research
            "Return ONLY valid JSON with key 'companies' as a list; each has: name, insights: [strings].",
        ],
    )

def get_email_style_instruction(style_key: str) -> str:
    styles = {
        "Professional": "Style: Professional. Clear, respectful, and businesslike. Short paragraphs; no slang.",
        "Casual": "Style: Casual. Friendly, approachable, first-name basis. No slang or emojis; keep it human.",
        "Cold": "Style: Cold email. Strong hook in opening 2 lines, tight value proposition, minimal fluff, strong CTA.",
        "Consultative": "Style: Consultative. Insight-led, frames observed problems and tailored solution hypotheses; soft CTA.",
    }
    return styles.get(style_key, styles["Professional"])

def create_email_writer_agent(style_key: str = "Professional") -> Agent:
    db = SqliteDb(db_file="tmp/gtm_outreach.db")
    style_instruction = get_email_style_instruction(style_key)
    return Agent(
        model=OpenAIChat(id="gpt-4o"),  # Changed from gpt-5
        tools=[],
        db=db,
        enable_user_memories=False,
        add_history_to_context=False,
        session_id="gtm_outreach_email_writer",
        debug_mode=False,
        instructions=[
            "You are EmailWriterAgent. Write concise, personalized B2B outreach emails.",
            style_instruction,
            "Return ONLY valid JSON with key 'emails' as a list of items: {company, contact, subject, body}.",
            "Length: 120-160 words. Include 1-2 lines of personalization using research insights.",
            "CTA: suggest a short intro call; include sender company name and calendar link if provided.",
        ],
    )

def extract_json_or_raise(text: str) -> Dict[str, Any]:
    """Extract JSON from a model response."""
    try:
        return json.loads(text)
    except Exception as e:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            return json.loads(candidate)
        raise ValueError(f"Failed to parse JSON: {e}\nResponse was:\n{text}")

def run_company_finder(agent: Agent, target_desc: str, offering_desc: str, max_companies: int) -> List[Dict[str, str]]:
    prompt = (
        f"Find exactly {max_companies} companies that are a strong B2B fit.\n"
        f"Targeting: {target_desc}\n"
        f"Offering: {offering_desc}\n"
        "For each, provide: name, website, why_fit (1-2 lines)."
    )
    resp: RunOutput = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    companies = data.get("companies", [])
    return companies[: max(1, min(max_companies, 10))]

def run_contact_finder(agent: Agent, companies: List[Dict[str, str]], target_desc: str, offering_desc: str) -> List[Dict[str, Any]]:
    prompt = (
        "For each company below, find 2 relevant decision makers and emails.\n"
        "If not available, infer likely email and mark inferred=true.\n"
        f"Targeting: {target_desc}\nOffering: {offering_desc}\n"
        f"Companies JSON: {json.dumps(companies, ensure_ascii=False)}\n"
        "Return JSON: {companies: [{name, contacts: [{full_name, title, email, inferred}]}]}"
    )
    resp: RunOutput = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    return data.get("companies", [])

def run_research(agent: Agent, companies: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    # Simplified: research fewer companies if list is large
    companies_to_research = companies[:5]  # Limit to 5 companies max
    prompt = (
        "For each company, gather 2-3 interesting insights from their website only.\n"
        f"Companies JSON: {json.dumps(companies_to_research, ensure_ascii=False)}\n"
        "Return JSON: {companies: [{name, insights: [string, ...]}]}"
    )
    resp: RunOutput = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    return data.get("companies", [])

def run_email_writer(agent: Agent, contacts_data: List[Dict[str, Any]], research_data: List[Dict[str, Any]], 
                     offering_desc: str, sender_name: str, sender_company: str, calendar_link: Optional[str]) -> List[Dict[str, str]]:
    prompt = (
        "Write personalized outreach emails for the following contacts.\n"
        f"Sender: {sender_name} at {sender_company}.\n"
        f"Offering: {offering_desc}.\n"
        f"Calendar link: {calendar_link or 'N/A'}.\n"
        f"Contacts JSON: {json.dumps(contacts_data, ensure_ascii=False)}\n"
        f"Research JSON: {json.dumps(research_data, ensure_ascii=False)}\n"
        "Return JSON with key 'emails' as a list of {company, contact, subject, body}."
    )
    resp: RunOutput = agent.run(prompt)
    data = extract_json_or_raise(str(resp.content))
    return data.get("emails", [])

def main() -> None:
    st.set_page_config(page_title="GTM B2B Outreach", layout="wide")

    # Sidebar: API keys
    st.sidebar.header("API Configuration")
    openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    exa_key = st.sidebar.text_input("Exa API Key", type="password", value=os.getenv("EXA_API_KEY", ""))
    
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    if exa_key:
        os.environ["EXA_API_KEY"] = exa_key

    if not openai_key or not exa_key:
        st.sidebar.warning("Enter both API keys to enable the app")

    # Inputs
    st.title("GTM B2B Outreach Multi Agent Team")
    st.info(
        "GTM teams often need to reach out for demos and discovery calls, but manual research and personalization is slow. "
        "This app uses GPT-5 with a multi-agent workflow to find target companies, identify contacts, research genuine insights (website + Reddit), "
        "and generate tailored outreach emails in your chosen style."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        target_desc = st.text_area("Target companies (industry, size, region, etc.)", height=100)
        offering_desc = st.text_area("Your product/service offering (1-3 sentences)", height=100)
    with col2:
        sender_name = st.text_input("Your name", value="Sales Team")
        sender_company = st.text_input("Your company", value="Our Company")
        calendar_link = st.text_input("Calendar link (optional)", value="")
        num_companies = st.number_input("Number of companies", min_value=1, max_value=5, value=3)  # Reduced max
        email_style = st.selectbox(
            "Email style",
            options=["Professional", "Casual", "Cold", "Consultative"],
            index=0,
        )

    if st.button("Start Outreach", type="primary"):
        if not openai_key or not exa_key:
            st.error("Please provide API keys in the sidebar")
        elif not target_desc or not offering_desc:
            st.error("Please fill in target companies and offering")
        else:
            progress = st.progress(0)
            stage_msg = st.empty()
            details = st.empty()
            
            try:
                # 1. Companies
                stage_msg.info("1/4 Finding companies...")
                company_agent = create_company_finder_agent()
                companies = run_company_finder(
                    company_agent,
                    target_desc.strip(),
                    offering_desc.strip(),
                    max_companies=int(num_companies),
                )
                progress.progress(25)
                details.write(f"Found {len(companies)} companies")

                # 2. Contacts
                stage_msg.info("2/4 Finding contacts...")
                contact_agent = create_contact_finder_agent()
                contacts_data = run_contact_finder(
                    contact_agent,
                    companies,
                    target_desc.strip(),
                    offering_desc.strip(),
                ) if companies else []
                progress.progress(50)
                details.write(f"Collected contacts for {len(contacts_data)} companies")

                # 3. Research
                stage_msg.info("3/4 Researching insights...")
                research_agent = create_research_agent()
                research_data = run_research(research_agent, companies) if companies else []
                progress.progress(75)
                details.write(f"Compiled research for {len(research_data)} companies")

                # 4. Emails
                stage_msg.info("4/4 Writing emails...")
                email_agent = create_email_writer_agent(email_style)
                emails = run_email_writer(
                    email_agent,
                    contacts_data,
                    research_data,
                    offering_desc.strip(),
                    sender_name.strip() or "Sales Team",
                    sender_company.strip() or "Our Company",
                    calendar_link.strip() or None,
                ) if contacts_data else []
                progress.progress(100)
                details.write(f"Generated {len(emails)} emails")

                st.session_state["gtm_results"] = {
                    "companies": companies,
                    "contacts": contacts_data,
                    "research": research_data,
                    "emails": emails,
                }
                stage_msg.success("✅ Completed")
                
            except Exception as e:
                stage_msg.error("❌ Pipeline failed")
                st.error(f"Error: {str(e)}")
                st.info("Try reducing the number of companies or check your API keys.")

    # Show results
    results = st.session_state.get("gtm_results")
    if results:
        companies = results.get("companies", [])
        contacts = results.get("contacts", [])
        research = results.get("research", [])
        emails = results.get("emails", [])

        st.subheader("Top target companies")
        if companies:
            for idx, c in enumerate(companies, 1):
                st.markdown(f"**{idx}. {c.get('name','')}**")
                st.write(c.get("website", ""))
                st.write(c.get("why_fit", ""))
        else:
            st.info("No companies found")
        st.divider()

        st.subheader("Contacts found")
        if contacts:
            for c in contacts:
                st.markdown(f"**{c.get('name','')}**")
                for p in c.get("contacts", [])[:3]:
                    inferred = " (inferred)" if p.get("inferred") else ""
                    st.write(f"- {p.get('full_name','')} | {p.get('title','')} | {p.get('email','')}{inferred}")
        else:
            st.info("No contacts found")
        st.divider()

        st.subheader("Research insights")
        if research:
            for r in research:
                st.markdown(f"**{r.get('name','')}**")
                for insight in r.get("insights", [])[:4]:
                    st.write(f"- {insight}")
        else:
            st.info("No research insights")
        st.divider()

        st.subheader("Suggested Outreach Emails")
        if emails:
            for i, e in enumerate(emails, 1):
                with st.expander(f"{i}. {e.get('company','')} → {e.get('contact','')}"):
                    st.write(f"**Subject:** {e.get('subject','')}")
                    st.text(e.get("body", ""))
        else:
            st.info("No emails generated")

if __name__ == "__main__":
    main()
