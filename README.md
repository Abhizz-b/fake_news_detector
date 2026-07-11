# AI Fake News Detector

An intelligent news verification system that uses semantic embeddings and large language models to fact-check news claims with evidence-backed reasoning.

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.43+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Student Project Notice** — This is a student project demo built on free-tier AI models. Please verify important claims through official fact-checking sources as well.

---

## What It Does

Paste in a news headline, claim, or article, and the app runs it through a full fact-checking pipeline in real time:

1. **Claim Extraction** — pulls out the core, verifiable factual claim from the input text
2. **Evidence Search** — searches the live web for relevant, recent sources
3. **Semantic Ranking** — matches evidence to the claim using embedding-based similarity, not just keyword overlap
4. **Verdict** — returns TRUE, FALSE, PARTIALLY TRUE, or UNVERIFIABLE, backed by clear reasoning and cited sources

Input can be in English, Japanese, Korean, or Chinese — the output is always normalized to English, regardless of input language.

---

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| Frontend / App Framework | Streamlit | Interactive web UI, session handling |
| Language Model | Groq (Llama 3.3 70B) | Claim extraction, evidence reasoning, final verdict |
| Embeddings | Google Gemini (`gemini-embedding-001`) | Semantic similarity between claim and evidence |
| Web Search | DuckDuckGo (`ddgs`) | Live evidence retrieval, no API key required |
| Database | SQLite | User auth, fact-check history |
| Reports | Custom PDF export | Downloadable, shareable fact-check reports |
| Auth | Salted password hashing | Secure multi-user support |

Every AI service runs on a free-tier cloud API — no local models, no GPU, nothing to self-host.

---

## Getting Started

**Prerequisites:** Python 3.12+, a free [Groq API key](https://console.groq.com), and a free [Gemini API key](https://aistudio.google.com)

```bash
git clone https://github.com/Abhizz-b/fake_news_detector.git
cd fake_news_detector/backend
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

Then run:
```bash
streamlit run app.py
```

---

## Usage

1. Sign up or log in
2. Paste in the news content you want verified
3. Review the verdict, reasoning, and evidence sources
4. Export a PDF report, or revisit past checks in your history

Full walkthrough: [docs/usage.md](docs/usage.md)

---

## Troubleshooting

**Model not responding / empty results** — check that your Groq and Gemini API keys are correct and haven't hit free-tier limits.

**Search not working** — check your internet connection; DuckDuckGo occasionally rate-limits repeated requests.

For anything else, open an [issue](https://github.com/Abhizz-b/fake_news_detector/issues).

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

If this project helps you, a star would mean a lot.
