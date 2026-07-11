# 🔍 AI Fake News Detector

An intelligent news verification system that uses semantic embeddings and large language models to fact-check news claims with evidence-backed reasoning.

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.43+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> ⚠️ **Student Project Notice**: This is a student project demo using free-tier AI models. Please verify important claims through official fact-checking sources.

## ✨ Features

- **Multilingual Input, English Output** — detects the input language automatically and always returns claims, verdicts, and reasoning in English
- **Evidence-Based Fact-Checking** — extracts the core claim, searches the web for evidence, and ranks it by semantic relevance before making a verdict
- **Transparent Reasoning** — every result comes with a clear explanation and cited sources
- **History & PDF Export** — save your fact-checks and export professional PDF reports
- **Multi-User Support** — secure login system with salted password hashing

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend / App | Streamlit |
| LLM (reasoning) | Groq (Llama 3.3 70B) |
| Embeddings | Google Gemini |
| Web Search | DuckDuckGo (`ddgs`) |
| Database | SQLite |
| PDF Reports | Python PDF export |

100% free-tier cloud APIs — no local models, no GPU required.

## 🚀 Quick Start

**Prerequisites:** Python 3.12+, a free [Groq API key](https://console.groq.com), and a free [Gemini API key](https://aistudio.google.com)

```bash
git clone https://github.com/Abhizz-b/fake_news_detector.git
cd fake_news_detector/backend
pip install -r requirements.txt
```

Create a `.env` file with:
```
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

Run it:
```bash
streamlit run app.py
```

App opens at `http://localhost:8501`

## 📖 Usage

1. Sign up or log in
2. Paste in the news content you want to fact-check
3. View the verdict, reasoning, and evidence sources
4. Export a PDF or check your history anytime

Full walkthrough: [docs/usage.md](docs/usage.md)

## 🐛 Troubleshooting

**Model not responding / empty results** — check that your Groq and Gemini API keys are correct and haven't hit free-tier limits

**Search not working** — check your internet connection; DuckDuckGo occasionally rate-limits repeated requests

For anything else, open an [issue](https://github.com/Abhizz-b/fake_news_detector/issues).

## 📄 License

MIT License — see [LICENSE](LICENSE) for details

---

⭐ If this project helps you, a star would mean a lot!
