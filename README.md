# 🔍 AI Fake News Detector

An intelligent news verification system based on fact-checking, supporting multiple languages and multiple model providers, using advanced semantic embedding technology and large language models for accurate fact-checking.

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.43+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

![App Screenshot](docs/images/screenshot.png)

## ✨ Core Features

### 🌍 Multilingual Support
- **Intelligent Language Detection**: Automatically recognizes Chinese, English, Japanese, and Korean input
- **Multilingual Output**: Supports user-defined output language or automatic detection
- **Localized Interface**: Full Chinese and English interface support

### 🤖 Multi-Provider Model Support
- **Ollama**: Locally deployed models (default: GPT-OSS 120B Cloud + Nomic Embed)
- **LM Studio**: Local model service
- **OpenAI**: Official GPT series models
- **Custom API**: Any model service compatible with the OpenAI format

### 🔍 High-Precision Fact-Checking
- **Claim Extraction**: Intelligently extracts core verifiable claims from news
- **Multi-Source Search**: Supports search engines such as SearXNG and DuckDuckGo
- **Semantic Matching**: Uses advanced embedding models to calculate evidence relevance
- **Transparent Reasoning**: Provides detailed reasoning processes and evidence sources

### 📊 Complete Data Management
- **History**: Save and view all fact-checking history
- **PDF Export**: Generate professional fact-check reports
- **User System**: Supports independent use by multiple users

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **Ollama** (recommended) or another OpenAI-API-compatible model service
- **SearXNG** (optional, for search functionality)

### Installation Steps

1. **Clone the repository**
```bash
git clone https://github.com/CaptainYifei/fake-news-detector.git
cd fake-news-detector
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure the model service** (Ollama recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the recommended models
ollama pull gpt-oss:120b-cloud
ollama pull nomic-embed-text:latest
```

4. **Configure the search service** (optional)
```bash
# Start SearXNG using Docker
docker run -d -p 8090:8080 searxng/searxng
```

### Launch the Application

```bash
streamlit run app.py
```

The application will start at http://localhost:8501

## 📋 Project Structure

```
fake-news-detector/
├── app.py                 # Main Streamlit application
├── fact_checker.py        # Core fact-checking logic
├── model_manager.py       # Model management and configuration
├── model_config.json      # Model and service configuration file
├── auth.py                # User authentication system
├── db_utils.py            # Database operations
├── pdf_export.py          # PDF report generation
├── requirements.txt       # Project dependencies
├── api.py                 # RESTful API interface
├── docs/                  # Documentation and usage instructions
└── test/                  # Test files
```

## ⚙️ Configuration Guide

### Model Configuration (`model_config.json`)

The system is configured centrally through `model_config.json`, supporting:

```json
{
  "providers": {
    "ollama": {
      "name": "Ollama",
      "type": "openai_compatible",
      "base_url": "http://localhost:11434/v1",
      "models": {
        "gpt-oss:120b-cloud": {
          "name": "GPT-OSS 120B Cloud",
          "type": "chat",
          "max_tokens": 8192
        },
        "nomic-embed-text:latest": {
          "name": "Nomic Embed Text",
          "type": "embedding",
          "dimensions": 768
        }
      }
    }
  },
  "defaults": {
    "llm_provider": "ollama",
    "llm_model": "gpt-oss:120b-cloud",
    "embedding_provider": "ollama",
    "embedding_model": "nomic-embed-text:latest",
    "output_language": "zh"
  }
}
```

### Search Engine Configuration

Multiple search engines are supported and can be set in the configuration file:
- **SearXNG**: A locally deployed privacy-focused search engine
- **DuckDuckGo**: Online search (proxy configuration supported)

## 🔄 Workflow

1. **Claim Extraction** - Uses an LLM to extract core claims from the input text
2. **Evidence Search** - Retrieves relevant web evidence via search engines
3. **Semantic Ranking** - Uses an embedding model to calculate evidence relevance
4. **Fact Judgment** - Makes a TRUE/FALSE/PARTIALLY TRUE determination based on the evidence
5. **Result Presentation** - Provides a detailed reasoning process and evidence sources

## 🌐 Multilingual Support

- **Automatic Detection**: Automatically selects the appropriate language template based on the input text
- **Manual Selection**: Users can specify the output language (Chinese/English/Japanese/Korean)
- **Intelligent Switching**: Language recognition based on Unicode character patterns

## 📖 Usage Instructions

### Using the Web Interface

1. Select the model provider and specific model
2. Configure the search engine and output language
3. Enter the news content to be fact-checked
4. View real-time processing progress and the final result
5. Export a PDF report or view history

### Using the API Interface

```bash
# Start the API service
python api.py

# Send a fact-check request
curl -X POST http://localhost:5000/fact-check \
  -H "Content-Type: application/json" \
  -d '{"text": "News content to be fact-checked"}'
```

For detailed API documentation, see `docs/api_doc.html`

## 🛠️ Development Guide

### Environment Setup

```bash
# Install the development environment
pip install -r requirements.txt

# Run tests
python -m pytest test/

# Start the development server
streamlit run app.py --server.runOnSave true
```

### Contributing Code

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

## 📝 Changelog

### v2.0.0 (Latest)
- ✨ Added multilingual support (Chinese/English/Japanese/Korean)
- 🔧 Unified model management system
- 🌐 Support for multiple search engines (SearXNG/DuckDuckGo)
- 📱 Improved user interface and interaction experience
- 🛡️ Enhanced error handling and configuration management
- 📄 Improved PDF export functionality

### v1.0.0
- 🎉 Initial release
- ✅ Basic fact-checking functionality
- 👤 User authentication system
- 💾 Persistent data storage

## 🐛 Troubleshooting

### FAQ

**Q: The model is unresponsive or returns empty results**
A: Check whether the model service is running normally, and confirm that the API address and port are configured correctly

**Q: The search function doesn't work**
A: Check your network connection, confirm the search engine service status, and configure a proxy if necessary

**Q: Multilingual output is behaving abnormally**
A: Confirm that the model in use supports the target language, and try switching to a more capable model

For more issues, please see [Issues](https://github.com/CaptainYifei/fake-news-detector/issues) or submit a new issue report.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🔗 Related Links

- **GitHub**: [https://github.com/CaptainYifei/fake-news-detector](https://github.com/CaptainYifei/fake-news-detector)
- **Gitee**: [https://gitee.com/love2eat/fake-news-detector](https://gitee.com/love2eat/fake-news-detector)
- **Documentation**: [docs/usage.md](docs/usage.md)
- **API Documentation**: [docs/api_doc.html](docs/api_doc.html)

---

⭐ If this project helps you, please give us a Star!
