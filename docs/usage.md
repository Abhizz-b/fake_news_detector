# AI Fake News Detector — User Guide

This document explains how to use the AI Fake News Detector, including account management, fact-checking, and history features.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Account Management](#account-management)
4. [Fact-Checking](#fact-checking)
5. [History Management](#history-management)
6. [Troubleshooting](#troubleshooting)

## Overview

The AI Fake News Detector is a web-based fact-checking tool. Paste in a news headline, claim, article, or a news article URL, and it will:

1. **Extract the core claim** from your text (via Groq LLM) — if you paste a URL, it fetches the page content first
2. **Search the web** for relevant evidence (via DuckDuckGo)
3. **Rank evidence** by semantic similarity to the claim (via Google Gemini embeddings)
4. **Return a verdict** — True / False / Partially True / Unverifiable — with reasoning based on the evidence

The app runs entirely on cloud-based AI services (Groq + Gemini), so there's nothing to install or configure locally — just open the link and use it.

## Getting Started

Simply open the deployed app link in your browser:

**[fake-news-detector-abhiz.streamlit.app](https://fake-news-detector-abhiz.streamlit.app/)**

No installation, API keys, or local setup required — everything runs on the hosted version.

> **Note for developers:** If you want to run this project locally instead of using the hosted link, see the `README.md` for setup instructions (Python environment, dependencies, and your own Groq/Gemini API keys).

## Account Management

### Register a New Account

1. Open the app — the login page is shown by default
2. Click the "Register" button
3. Fill in the registration form:
   - Username (at least 3 characters)
   - Password (at least 6 characters)
   - Confirm password
4. Click the "Register" button
5. After successful registration, the system automatically returns to the login page

### Log In

1. Enter your username and password on the login page
2. Click the "Login" button
3. After successful login, the system redirects to the home page

### Log Out

On any page, click the "Logout" button in the top navigation bar (account dropdown) to sign out.

## Fact-Checking

### Run a New Fact-Check

1. After logging in, the home page shows the fact-checking interface by default
2. Enter the news text — a headline, claim, article, or a direct news article URL — into the input box
3. Submit it
4. The system will automatically:
   - Extract the core claim (fetching the page first if you pasted a URL)
   - Search the web for relevant evidence
   - Verify the claim's accuracy based on that evidence

> **Note:** Links from social platforms (LinkedIn, Instagram, X, Facebook, TikTok, Threads) aren't supported — these sites block scraping and personal posts don't have public evidence to check against. Use news article URLs instead.

### View the Result

Once the check is complete, the system displays:

1. **Core Claim**: The verifiable statement extracted from the news
2. **Evidence Sources**: Relevant evidence gathered from web search, with sources
3. **Verdict**: One of the following:
   - ✅ True
   - ❌ False
   - ⚠️ Partially True
   - ❓ Unverifiable
4. **Reasoning**: A detailed analysis of the claim's accuracy based on the evidence

## History Management

### View History

1. Click "History" in the top navigation bar (account dropdown)
2. All past fact-checks are shown in reverse chronological order
3. Each entry shows:
   - Core claim (summary)
   - Verdict (True/False/Partially True/Unverifiable)
   - Check timestamp
   - A "View Details" button

### View History Details

1. In the history list, click "View Details" on any entry
2. The system shows the full report for that check, including:
   - The original news text
   - The extracted core claim
   - All evidence sources
   - The verdict and reasoning

### Export as PDF

1. On the history detail page, find the "Export Report" section
2. Click "Export as PDF"
3. The system generates and downloads a PDF containing the full report

## Troubleshooting

### Search Engine Rate Limits

If you encounter a search/evidence error:

1. This usually means the DuckDuckGo search backend is temporarily rate-limiting requests
2. Wait a moment and try again
3. If it persists, try rephrasing the claim slightly

### Login / Account Issues

If you can't log in or register:

1. Make sure your username is at least 3 characters and password at least 6 characters
2. Try refreshing the page and registering again if the issue persists

### Other Issues

For any other issues:

1. Refresh the page and try again
2. If the problem persists, please open an Issue on the GitHub repository

---

*This is a student project built for academic demonstration purposes.*
