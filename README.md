# AI Email GTM Outreach Agent Team 🚀

An intelligent multi-agent system that automates B2B outreach campaigns using GPT-4o, Agno framework, and Exa AI. This application discovers target companies, finds decision-makers, conducts research, and generates personalized outreach emails in minutes.

## 🌟 Features

- **Multi-Agent Architecture**: Four specialized AI agents working together:
  - **Company Finder**: Discovers relevant companies using semantic search
  - **Contact Finder**: Identifies 2-3 key decision makers per company
  - **Research Agent**: Gathers genuine insights from company websites
  - **Email Writer**: Creates personalized outreach emails in multiple styles

- **Intelligent Web Search**: Powered by Exa AI's embedding-based search
- **Multiple Email Styles**: Professional, Casual, Cold, and Consultative
- **Real-time Progress Tracking**: Stage-by-stage updates
- **Persistent Memory**: SQLite database for agent context

## 📋 Prerequisites

- Python 3.13 (recommended) or 3.11/3.12
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Exa AI API key ([Get one here](https://dashboard.exa.ai/api-keys))

## 🛠️ Installation

### 1. Clone the Repository

```bash
    git clone <your-repo-url>
    cd ai_email_gtm_outreach_agent
```


### 2. Create Conda Environment

```bash
    conda create -n email_agent python=3.13 pip
    conda activate email_agent
```



### 3. Install Dependencies
```bash
    pip install -r requirements.txt
```


**Note**: If you encounter pyarrow build errors, install via conda:
```bash
    conda install -c conda-forge pyarrow
    pip install -r requirements.txt
```

## ⚙️ Configuration

### Create .env File

Create a `.env` file in the project root:
```bash
    OPENAI_API_KEY=your_openai_api_key_here
    EXA_API_KEY=your_exa_api_key_here
```


Alternatively, you can enter API keys directly in the Streamlit sidebar.

## 🚀 Usage

### Start the Application

```bash
    streamlit run ai_email_gtm_outreach_agent.py
```


The app will open in your browser at `http://localhost:8501`

### Using the App

1. **Enter API Keys**: Add your OpenAI and Exa API keys in the sidebar
2. **Define Target Companies**: Describe your ideal customers (industry, size, location, etc.)
3. **Describe Your Offering**: Explain your product/service in 1-3 sentences
4. **Configure Sender Info**: Set your name, company, and optional calendar link
5. **Choose Settings**: Select number of companies (1-5) and email style
6. **Start Outreach**: Click "Start Outreach" and watch the pipeline execute

### Example Input

**Target Companies:**
B2B SaaS companies in healthcare, 50-500 employees, US-based,
using cloud infrastructure


**Your Offering:**
AI-powered patient data management platform that reduces
administrative overhead by 40% and improves compliance.


## 📁 Project Structure

ai_email_gtm_outreach_agent/
├── ai_email_gtm_outreach_agent.py # Main Streamlit application
├── requirements.txt # Python dependencies
├── .env # API keys (not in git)
├── .gitignore # Git ignore rules
├── tmp/ # SQLite database storage
│ └── gtm_outreach.db # Agent memory database
└── README.md # This file


## 🔧 Troubleshooting

### App Stuck on Research Stage

**Solution**: The app limits research to 5 companies and website-only searches. If still slow:
- Reduce number of companies to 2-3
- Check your Exa AI API rate limits
- Clear the database: `rm -rf tmp/`

### PyArrow Installation Errors

**Solution**: Use conda instead of pip:
```bash
    conda install -c conda-forge pyarrow
```


### Python 3.14 Compatibility Issues

**Solution**: Use Python 3.13 or 3.12:
```bash
    conda create -n email_agent python=3.13 pip
``` 


### Debug Logs Appearing

**Solution**: Ensure `debug_mode=False` in all agent creation functions and restart:
```bash
    rm -rf tmp/
    streamlit run ai_email_gtm_outreach_agent.py
```


## 📦 Dependencies

- `agno>=2.2.10` - AI agent framework
- `streamlit>=1.33.0` - Web app framework
- `pydantic>=2.7.0` - Data validation
- `openai>=1.30.0` - OpenAI API client
- `exa_py>=1.0.7` - Exa search API

## 🎯 How It Works

1. **Company Discovery**: Uses Exa AI's semantic search to find companies matching your criteria
2. **Contact Research**: Identifies decision-makers in GTM, Sales, Partnerships, and Founder roles
3. **Insight Gathering**: Analyzes company websites for recent news, products, and initiatives
4. **Email Generation**: Combines research insights with GPT-4o to create personalized emails

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Powered by [Agno](https://agno.com) multi-agent framework
- Search by [Exa AI](https://exa.ai)
- LLM by [OpenAI](https://openai.com)

## 📧 Support

For questions or issues:
- Open an issue on GitHub
- Check the [troubleshooting section](#-troubleshooting)
- Review the [Agno documentation](https://docs.agno.com)

## ⚠️ Important Notes

- **API Costs**: This app makes multiple API calls. Monitor your OpenAI and Exa usage.
- **Rate Limits**: Respect API rate limits. Start with 2-3 companies for testing.
- **Email Validation**: Always verify generated emails before sending to prospects.
- **Data Privacy**: The app stores agent memory locally in SQLite. Keep API keys secure.


**Built with ❤️ using AI Agents**