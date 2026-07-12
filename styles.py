"""
Custom CSS for the Fake News Detector app.
Import and call `inject_css()` once at the top of app.py.
"""

import streamlit as st

CSS = """
<style>
/* ---------- Global ---------- */
/* FIX (final): the previous horizontal-scroll fix targeted html/body,
   but Streamlit's real scrolling container is
   [data-testid="stAppViewContainer"] / [data-testid="stMain"], not
   body itself — so overflow-x could still leak through there. Locking
   overflow-x down on every layer (html, body, stApp, and Streamlit's
   own view container) closes that gap completely. Background stays
   only on .stApp so the radial glow doesn't get painted twice by
   nested containers. */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main {
    overflow-x: hidden !important;
}
.stApp {
    background:
        radial-gradient(ellipse 900px 480px at 50% -8%, rgba(139, 92, 246, 0.16), transparent 60%),
        #0b0b14;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stToolbar"] {
    display: none !important;
}
[data-testid="stStatusWidget"] {
    display: none !important;
}
[data-testid="stHeader"] {
    display: none !important;
}
[data-testid="stDecoration"] {
    display: none !important;
}
[data-testid="stHeaderActionElements"] {
    display: none !important;
}

.block-container {
    padding-top: 0.4rem;
    padding-bottom: 1rem;
    animation: fndFadeIn 0.4s ease-out;
}

[data-testid="collapsedControl"] {
    display: none !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
section[data-testid="stSidebar"] button[kind="header"] {
    display: none !important;
}
[data-testid="stSidebarResizeHandle"] {
    display: none !important;
}

section[data-testid="stSidebar"] {
    min-width: 280px !important;
    max-width: 280px !important;
    width: 280px !important;
    background: #0e0e18 !important;
    border-right: 1px solid #1c1c2a;
    transition: min-width 0.28s cubic-bezier(0.4, 0, 0.2, 1),
                max-width 0.28s cubic-bezier(0.4, 0, 0.2, 1),
                width 0.28s cubic-bezier(0.4, 0, 0.2, 1) !important;
    overflow: hidden !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 1.6rem;
    transition: opacity 0.2s ease;
}

.st-key-sidebar_expand_btn button,
.st-key-sidebar_collapse_btn button {
    width: 42px !important;
    height: 42px !important;
    padding: 0 !important;
    border-radius: 12px !important;
    background: #1c1c2a !important;
    border: 1px solid #2a2a3a !important;
    color: #cfcfe0 !important;
    font-size: 1.1rem !important;
    min-height: 0 !important;
    transition: background 0.15s ease, transform 0.15s ease;
    margin: 0 auto !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
}
.st-key-sidebar_expand_btn button:hover,
.st-key-sidebar_collapse_btn button:hover {
    background: #23233a !important;
    color: #fff !important;
    transform: scale(1.05);
}

/* ---------- Generic card ---------- */
.fnd-card {
    background: #14141f;
    border: 1px solid #23232f;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    animation: fndFadeUp 0.4s ease-out both;
}
.fnd-card:hover {
    border-color: #34344a;
    box-shadow: 0 8px 24px rgba(139, 92, 246, 0.08);
}

/* ---------- Sidebar logo ---------- */
.fnd-logo {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-weight: 700;
    font-size: 1.05rem;
    margin-bottom: 0;
    padding: 0 0.2rem;
}
.fnd-logo-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, #8b5cf6, #6d28d9);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.05rem;
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35);
    flex-shrink: 0;
}

section[data-testid="stSidebar"] .stButton button {
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    color: #cfcfe0;
    font-weight: 500;
    padding: 0.55rem 0.8rem;
    border-radius: 10px;
    margin-bottom: 0.2rem;
    transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: #1c1c2a;
    color: #fff;
    transform: translateX(2px);
}
section[data-testid="stSidebar"] .stButton button:focus:not(:active) {
    color: #fff;
}
section[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: linear-gradient(90deg, #8b5cf6, #6d28d9) !important;
    color: #fff !important;
    text-align: left;
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.25);
}
section[data-testid="stSidebar"] .st-key-sidebar_collapse_btn button,
section[data-testid="stSidebar"] .st-key-sidebar_expand_btn button {
    width: 42px !important;
}

.fnd-user-card {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    background: #14141f;
    border: 1px solid #23232f;
    border-radius: 14px;
    padding: 0.7rem 0.9rem;
    margin: 0 0.2rem;
}
.fnd-user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #8b5cf6, #6d28d9);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    flex-shrink: 0;
}
.fnd-user-meta { flex: 1; }
.fnd-user-name { font-weight: 600; font-size: 0.9rem; }
.fnd-user-role { color: #8a8aa3; font-size: 0.78rem; }
.fnd-user-chevron { color: #6f6f8a; font-size: 0.9rem; }

/* ---------- Buttons (primary) ---------- */
.stButton > button[kind="primary"], button[kind="primary"] {
    background: linear-gradient(90deg, #8b5cf6, #7c3aed);
    border: none;
    border-radius: 10px;
    font-weight: 600;
    color: white;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.2s ease;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(90deg, #9b6cfb, #8b47f0);
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(139, 92, 246, 0.35);
}
.stButton > button[kind="secondary"] {
    border-radius: 10px;
    transition: transform 0.15s ease;
}
.stButton > button[kind="secondary"]:hover {
    transform: translateY(-1px);
}

/* ---------- Hero heading (old two-column home layout, kept in case
   it's reused elsewhere) ---------- */
.fnd-hero {
    position: relative;
    padding: 0.5rem 0 0.5rem;
    animation: fndFadeUp 0.5s ease-out both;
}
.fnd-hero::before {
    content: "";
    position: absolute;
    top: -60px;
    left: -60px;
    width: 260px;
    height: 260px;
    background: radial-gradient(circle, rgba(139,92,246,0.18) 0%, rgba(139,92,246,0) 70%);
    pointer-events: none;
    z-index: 0;
}
.fnd-hero h1 {
    position: relative;
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1.2;
    margin-bottom: 0.4rem;
    z-index: 1;
}
.fnd-hero .accent {
    background: linear-gradient(90deg, #a78bfa, #8b5cf6);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.fnd-hero p {
    position: relative;
    color: #9c9cb0;
    font-size: 1.02rem;
    z-index: 1;
}

.st-key-app_header_bar {
    background: transparent;
    padding: 0.55rem 0.5rem;
    margin-bottom: 0.2rem;
    position: relative;
}
[data-testid="stPopover"] {
    display: inline-flex;
    align-items: center;
    margin-right: -0.4rem;
}
.st-key-app_header_bar::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    width: 100%;
    height: 1px;
    background: rgba(255, 255, 255, 0.06);
}

.fnd-header-brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    color: #f3f1f9;
    font-weight: 700;
    font-size: 0.9rem;
    padding-top: 0.4rem;
}
.fnd-header-brand svg {
    color: #a78bfa;
    flex-shrink: 0;
}
.fnd-brand-wordmark {
    font-size: 1.2rem;
    font-weight: 800;
    letter-spacing: -0.01em;
    background: linear-gradient(90deg, #f3f1f9, #c4b5fd);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

[data-testid="stPopover"] button {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    height: auto !important;
    min-height: 0 !important;
    width: auto !important;
    padding: 5px 16px 5px 5px !important;
    margin: 0 !important;
    background: #15111f !important;
    border: 1px solid #29233b !important;
    border-radius: 999px !important;
    color: #fff !important;
    transition: border-color 0.15s ease;
}
[data-testid="stPopover"] button:hover {
    border-color: #3a3350 !important;
}
[data-testid="stPopover"] button [data-testid="stMarkdownContainer"],
[data-testid="stPopover"] button [data-testid="stMarkdownContainer"] p {
    width: 34px !important;
    height: 34px !important;
    min-width: 34px !important;
    border-radius: 50% !important;
    background: linear-gradient(135deg, #8b5cf6, #6d28d9) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.01em;
    color: #fff !important;
    margin: 0 !important;
    line-height: 1 !important;
}
[data-testid="stPopover"] button svg,
[data-testid="stPopover"] button [data-testid*="Icon"] {
    width: 14px !important;
    height: 14px !important;
    color: #9d97b3 !important;
    flex-shrink: 0;
}

[data-testid="stPopoverBody"] {
    background: #15111f !important;
    border: 1px solid #29233b !important;
    border-radius: 14px !important;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45) !important;
    min-width: 230px !important;
    padding: 0.5rem !important;
}

.fnd-account-header {
    padding: 0.6rem 0.7rem 0.75rem;
    border-bottom: 1px solid #29233b;
    margin-bottom: 0.7rem;
    position: relative;
    z-index: 2;
}
.fnd-account-name {
    font-weight: 700;
    font-size: 0.9rem;
    color: #f3f1f9;
}
.fnd-account-role {
    font-size: 0.78rem;
    color: #8a8aa3;
    margin-top: 0.15rem;
}
.fnd-account-divider {
    height: 1px;
    background: #29233b;
    margin: 0.6rem 0.2rem;
    position: relative;
    z-index: 2;
}

[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {
    gap: 0.35rem !important;
}
[data-testid="stPopoverBody"] [data-testid="element-container"] {
    margin: 0 !important;
}

[data-testid="stPopoverBody"] .stButton button {
    background: transparent !important;
    border: none !important;
    color: #cfcfe0 !important;
    font-weight: 500 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 0.55rem 0.6rem !important;
    border-radius: 9px !important;
    box-shadow: none !important;
}
[data-testid="stPopoverBody"] .stButton button p,
[data-testid="stPopoverBody"] .stButton button div {
    text-align: left !important;
    width: 100%;
}
[data-testid="stPopoverBody"] .stButton button:hover {
    background: rgba(139, 92, 246, 0.12) !important;
    color: #fff !important;
}
[data-testid="stPopoverBody"] .st-key-account_menu_logout_btn button {
    color: #f87171 !important;
}
[data-testid="stPopoverBody"] .st-key-account_menu_logout_btn button:hover {
    background: rgba(248, 113, 113, 0.1) !important;
    color: #f87171 !important;
}

.st-key-home_center_wrap {
    display: flex !important;
    flex-direction: column;
    align-items: center;
    max-width: 1180px;
    margin: 0 auto;
    padding: 0.4rem 2rem 1rem;
}
.st-key-home_center_wrap [data-testid="stVerticalBlock"] {
    gap: 0.7rem !important;
}
.fnd-hero-minimal {
    text-align: center;
    margin-bottom: 0.9rem;
    animation: fndFadeUp 0.5s ease-out both;
}
.fnd-hero-minimal h1 {
    font-size: 2.7rem;
    font-weight: 800;
    line-height: 1.12;
    letter-spacing: -0.02em;
    margin-bottom: 0.3rem;
}
.fnd-hero-minimal .muted-line {
    color: #9d97b3;
}
.fnd-hero-minimal .accent {
    background: linear-gradient(90deg, #8b5cf6, #c4b5fd);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.fnd-hero-minimal p {
    color: #8d87a3;
    font-size: 0.95rem;
    line-height: 1.6;
    max-width: 520px;
    margin: 0.4rem auto 0;
}

.st-key-claim_shell {
    width: 100%;
    max-width: 880px;
}

.fnd-static-pill-row {
    display: flex;
    gap: 0.6rem;
    width: 100%;
}
.fnd-static-pill {
    flex: 1;
    background: #0f0c1a;
    border: 1px solid #2a2a3a;
    color: #8d87a3;
    border-radius: 12px;
    font-weight: 500;
    font-size: 0.85rem;
    padding: 0.75rem 1rem;
    text-align: center;
    cursor: default;
    user-select: none;
}
.fnd-pill-full { display: inline; }
.fnd-pill-short { display: none; }

.fnd-text-full { display: inline; }
.fnd-text-short { display: none; }

.fnd-block-full { display: block; }
.fnd-block-short { display: none; }

.st-key-claim_input_box textarea {
    border-radius: 12px !important;
    border: 1px solid #29233b !important;
    background: #14141f !important;
    color: #f3f1f9 !important;
    font-size: 0.9rem !important;
    padding: 1.05rem 1.2rem !important;
}
.st-key-claim_input_box textarea::placeholder {
    color: #75758c !important;
}
.st-key-claim_input_box textarea:focus {
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
    border-color: #8b5cf6 !important;
}

.st-key-clear_home_btn button {
    background: #14141f !important;
    border: 1px solid #2a2a3a !important;
    color: #cfcfe0 !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
}
.st-key-clear_home_btn button:hover {
    border-color: #34344a !important;
    color: #fff !important;
}

.st-key-clear_home_btn button,
.st-key-check_now_btn button {
    transition: transform 0.08s ease, box-shadow 0.15s ease, background 0.2s ease, border-color 0.15s ease, color 0.15s ease !important;
}
.st-key-clear_home_btn button:hover,
.st-key-check_now_btn button:hover {
    transform: none !important;
    box-shadow: none !important;
}
.st-key-clear_home_btn button:active,
.st-key-check_now_btn button:active {
    transform: scale(0.96) !important;
}

.fnd-status-line {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin: 0.4rem auto 0;
    font-size: 0.95rem;
    font-weight: 500;
    animation: fndFadeUp 0.25s ease-out both;
}
.fnd-status-text {
    background: linear-gradient(90deg, #4fc3f7, #a855f7);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.fnd-spinner {
    width: 15px;
    height: 15px;
    border: 2px solid rgba(139, 92, 246, 0.25);
    border-top-color: #a855f7;
    border-radius: 50%;
    animation: fndSpin 0.7s linear infinite;
    flex-shrink: 0;
}
@keyframes fndSpin {
    to { transform: rotate(360deg); }
}

.stTextArea textarea {
    border-radius: 12px !important;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.stTextArea textarea:focus {
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.25) !important;
    border-color: #8b5cf6 !important;
}

.fnd-card-heading {
    font-weight: 700;
    font-size: 1.05rem;
    margin-bottom: 1.15rem;
}
.fnd-step-row {
    display: flex;
    gap: 0.9rem;
    position: relative;
    padding-bottom: 1.15rem;
}
.fnd-step-row.fnd-step-line::after {
    content: "";
    position: absolute;
    left: 15px;
    top: 34px;
    width: 2px;
    height: calc(100% - 22px);
    background: #23232f;
}
.fnd-step-icon {
    width: 32px;
    height: 32px;
    border-radius: 9px;
    background: linear-gradient(135deg, rgba(139,92,246,0.28), rgba(109,40,217,0.22));
    border: 1px solid rgba(139,92,246,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-weight: 700;
    font-size: 0.85rem;
    color: #d8cffa;
    position: relative;
    z-index: 1;
}
.fnd-step-title {
    font-weight: 600;
    font-size: 0.92rem;
    color: #f0eefc;
    margin-bottom: 0.15rem;
}
.fnd-step-subtitle {
    color: #8a8aa3;
    font-size: 0.8rem;
    line-height: 1.4;
}
.fnd-quote {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #23232f;
    color: #cfcfe0;
    font-style: italic;
    font-size: 0.9rem;
    position: relative;
}
.fnd-quote-underline {
    margin-top: 0.4rem;
    width: 70px;
    height: 6px;
}

.fnd-tech-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}
.fnd-tech-chip {
    background: #1b1b28;
    border: 1px solid #2a2a3a;
    border-radius: 999px;
    padding: 0.35rem 0.85rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: #e4e0fa;
    transition: border-color 0.15s ease, transform 0.15s ease;
}
.fnd-tech-chip:hover {
    border-color: #8b5cf6;
    transform: translateY(-2px);
}

.fnd-badge {
    display: inline-block;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
}
.fnd-badge-true { background: #123a24; color: #4ade80; }
.fnd-badge-false { background: #3a1414; color: #f87171; }
.fnd-badge-partial { background: #3a2f10; color: #fbbf24; }
.fnd-badge-unverifiable { background: #202030; color: #a1a1c0; }

.fnd-verdict-card {
    border-radius: 16px;
    padding: 1.5rem 1.6rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    animation: fndFadeUp 0.4s ease-out both;
}
.fnd-verdict-card.true { background: linear-gradient(135deg, #0f2e1c, #123a24); border: 1px solid #1f5c38; }
.fnd-verdict-card.false { background: linear-gradient(135deg, #2e0f0f, #3a1414); border: 1px solid #5c1f1f; }
.fnd-verdict-card.partial { background: linear-gradient(135deg, #2e2410, #3a2f10); border: 1px solid #5c4a1f; }
.fnd-verdict-card.unverifiable { background: linear-gradient(135deg, #1c1c2a, #202030); border: 1px solid #34344a; }

.fnd-verdict-icon {
    width: 54px;
    height: 54px;
    border-radius: 50%;
    background: rgba(255,255,255,0.08);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    flex-shrink: 0;
}
.fnd-verdict-text {
    font-size: 1.55rem;
    font-weight: 800;
    line-height: 1.1;
}

.fnd-ring-card {
    display: flex;
    align-items: center;
    gap: 1.2rem;
}
.fnd-ring-wrap {
    animation: fndScaleIn 0.5s ease-out both;
    filter: drop-shadow(0 4px 10px rgba(0,0,0,0.25));
}
.fnd-ring-wrap circle:nth-child(2) {
    transition: stroke-dashoffset 0.6s ease-out;
}

.fnd-source-row {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid #1e1e2a;
}
.fnd-source-row:last-child { border-bottom: none; }
.fnd-source-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: #1e1e2e;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
    flex-shrink: 0;
}
.fnd-source-body {
    flex: 1;
    min-width: 0;
}
.fnd-source-name { font-weight: 600; font-size: 0.88rem; color: #f0eefc; }
.fnd-source-tag { color: #8a8aa3; font-size: 0.75rem; }
a.fnd-source-link {
    display: inline-block;
    max-width: 100%;
    text-decoration: none;
    color: #f0eefc;
    cursor: pointer;
    word-break: break-all;
    overflow-wrap: anywhere;
}
a.fnd-source-link:hover {
    color: #c4b5fd;
    text-decoration: underline;
}

.fnd-history-header {
    display: grid;
    grid-template-columns: 3fr 1fr 1.2fr 0.8fr 1.4fr;
    gap: 0.5rem;
    color: #8a8aa3;
    font-size: 0.78rem;
    padding: 0.4rem 1rem;
}
.fnd-history-row {
    display: grid;
    grid-template-columns: 3fr 1fr 1.2fr 0.8fr 1.4fr;
    gap: 0.5rem;
    align-items: center;
    background: #14141f;
    border: 1px solid #23232f;
    border-radius: 12px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.88rem;
    animation: fndFadeUp 0.35s ease-out both;
}

.st-key-back_to_home_btn button {
    transition: transform 0.08s ease !important;
}
.st-key-back_to_home_btn button:hover {
    transform: none !important;
    box-shadow: none !important;
}
.st-key-back_to_home_btn button:active {
    transform: scale(0.96) !important;
}

[data-testid="stSpinner"] {
    background: #14141f;
    border: 1px solid #23232f;
    border-radius: 12px;
    padding: 0.85rem 1.1rem;
    margin: 0.7rem 0;
    animation: fndFadeUp 0.3s ease-out both;
}
[data-testid="stSpinner"] svg {
    color: #8b5cf6 !important;
}
[data-testid="stSpinner"] p {
    color: #cfcfe0 !important;
    font-size: 0.88rem;
    margin: 0 !important;
}
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: 1px solid #23232f !important;
    animation: fndFadeUp 0.3s ease-out both;
}

@keyframes fndFadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes fndFadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fndScaleIn {
    from { opacity: 0; transform: scale(0.85); }
    to { opacity: 1; transform: scale(1); }
}

/* ===========================================================
   NEW: Large monitor breakpoint (1400px and wider)
   ===========================================================
   Only .st-key-home_center_wrap's max-width changes here — every
   other rule (cards, buttons, spacing) is left completely alone, so
   nothing about the *look* of individual elements changes, only how
   much total width the centered home-page content is allowed to use.
   This makes big external monitors feel less "an island in a sea of
   empty space" without ever going edge-to-edge (which would make
   the hero text/paragraph uncomfortably wide to read). 1180px (the
   original) still applies on anything narrower than 1400px, i.e.
   every normal laptop screen is completely unaffected. */
@media (min-width: 1400px) {
    .st-key-home_center_wrap {
        max-width: 1400px;
    }
}

/* ===========================================================
   NEW: Tablet breakpoint (641px – 1024px)
   ===========================================================
   Previously there was a big gap between the mobile fixes below
   (<=640px) and the desktop-oriented default styles above — so an
   iPad-ish/tablet-width screen (and some small laptops) got the full
   desktop hero font-size/padding with none of the mobile
   space-saving tweaks, and none of the width-safety tweaks either.
   This section only trims font sizes and horizontal padding a bit
   (nothing structural, no layout/flex-direction changes) so text and
   spacing feel proportional at these in-between widths, while still
   keeping the same side-by-side layouts (pills row, verdict +
   confidence ring, Clear/Check Now row) that desktop uses — those
   already fit fine at 641px+, they just don't need full desktop-size
   text and padding. */
@media (min-width: 641px) and (max-width: 1024px) {
    /* FIX: on tablet-height screens (e.g. iPad, 768x1024) the home
       page's content (heading + textarea + pills + buttons + note) is
       shorter than the viewport, so it all sat pinned to the top with
       a large empty gap below it. min-height + justify-content:center
       vertically centers that content in the available viewport space
       instead, splitting the empty space evenly above/below rather
       than dumping all of it at the bottom. Scoped to ONLY this
       min-width:641px/max-width:1024px breakpoint, so phones (<=640px)
       and laptops/monitors (>1024px) are completely unaffected — this
       rule simply doesn't exist outside this range. `100px` is a rough
       allowance for the top header bar above .st-key-home_center_wrap;
       if content is ever taller than the viewport it just scrolls
       normally, nothing gets clipped. */
    .st-key-home_center_wrap {
        min-height: calc(100vh - 100px);
        justify-content: center;
    }
    .st-key-home_center_wrap {
        padding: 0.4rem 1.1rem 1rem;
    }
    .fnd-hero-minimal h1 {
        font-size: 2.15rem;
    }
    .fnd-hero-minimal p {
        font-size: 0.9rem;
        max-width: 90%;
    }
    .fnd-static-pill {
        font-size: 0.78rem;
        padding: 0.65rem 0.6rem;
    }
    .fnd-card {
        padding: 1.1rem 1.2rem;
    }
    .fnd-verdict-card {
        padding: 1.2rem 1.3rem;
    }
    .fnd-verdict-text {
        font-size: 1.3rem;
    }
    .fnd-history-header,
    .fnd-history-row {
        grid-template-columns: 2.4fr 0.9fr 1fr 0.7fr 1.2fr;
        font-size: 0.82rem;
    }
}

@media (max-width: 640px) {

    .st-key-app_header_bar [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 0.5rem !important;
    }
    .st-key-app_header_bar [data-testid="stColumn"] {
        width: auto !important;
        min-width: 0 !important;
    }
    .st-key-app_header_bar [data-testid="stColumn"]:first-child {
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }
    .st-key-app_header_bar [data-testid="stColumn"]:last-child {
        flex: 0 0 auto !important;
    }
    .fnd-header-brand {
        min-width: 0;
    }
    .fnd-brand-wordmark {
        display: inline-block;
        max-width: 46vw;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        vertical-align: middle;
        font-size: 1.05rem;
    }

    .fnd-pill-full { display: none; }
    .fnd-pill-short { display: inline; }
    .fnd-static-pill-row {
        flex-direction: row;
        gap: 0.35rem;
    }
    .fnd-static-pill {
        width: auto;
        font-size: 0.7rem;
        padding: 0.6rem 0.3rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .fnd-text-full { display: none !important; }
    .fnd-text-short { display: inline !important; }
    .fnd-block-full { display: none !important; }
    .fnd-block-short { display: block !important; }

    .fnd-source-row {
        gap: 0.5rem;
        align-items: flex-start;
    }

    .fnd-history-header {
        display: none;
    }
    .fnd-history-row {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 0.55rem;
        padding: 0.9rem 1rem;
    }
    .fnd-history-row > div {
        width: 100%;
    }
    .fnd-history-row > div::before {
        content: attr(data-label);
        display: block;
        color: #8a8aa3;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.2rem;
    }

    /* --- Fix 5: verdict card + confidence ring stacking / ending up
       unequal sizes instead of sitting neatly side-by-side ---
       `:has(.fnd-verdict-card)` finds whichever
       [data-testid="stHorizontalBlock"] actually contains the verdict
       card, on ANY page, so this applies everywhere the pair is
       rendered (results page AND history-detail page alike). */
    [data-testid="stHorizontalBlock"]:has(.fnd-verdict-card),
    .st-key-results_top_row [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        flex-direction: row !important;
        align-items: stretch !important;
        gap: 0.5rem !important;
        width: 100% !important;
        max-width: 100% !important;
    }
    [data-testid="stHorizontalBlock"]:has(.fnd-verdict-card) > [data-testid="stColumn"],
    .st-key-results_top_row [data-testid="stColumn"] {
        width: 50% !important;
        max-width: 50% !important;
        min-width: 0 !important;
        flex: 1 1 0 !important;
        display: flex !important;
    }
    [data-testid="stHorizontalBlock"]:has(.fnd-verdict-card) [data-testid="stColumn"] > div,
    [data-testid="stHorizontalBlock"]:has(.fnd-verdict-card) [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"]:has(.fnd-verdict-card) [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stHorizontalBlock"]:has(.fnd-verdict-card) [data-testid="element-container"],
    [data-testid="stHorizontalBlock"]:has(.fnd-verdict-card) [data-testid="stMarkdown"],
    [data-testid="stHorizontalBlock"]:has(.fnd-verdict-card) [data-testid="stMarkdownContainer"],
    .st-key-results_top_row [data-testid="stColumn"] > div,
    .st-key-results_top_row [data-testid="stVerticalBlock"],
    .st-key-results_top_row [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-results_top_row [data-testid="element-container"],
    .st-key-results_top_row [data-testid="stMarkdown"],
    .st-key-results_top_row [data-testid="stMarkdownContainer"] {
        height: 100% !important;
        width: 100% !important;
        max-width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        box-sizing: border-box !important;
    }

    /* FIX (v4): the previous version used `overflow: hidden` together
       with a rigid `height: 135px`. On the history-detail page the
       actual rendered content (icon + "VERDICT" + "TRUE" + badge, or
       ring + date/sources line) was very slightly taller than 135px,
       so overflow:hidden silently CUT OFF most of the box instead of
       showing it — that's what made the cards look empty/collapsed.
       Removing overflow:hidden and switching from a fixed `height` to
       `min-height` + `height: 100%` fixes this two ways at once:
       content is never clipped again, AND both cards still end up
       exactly the same height as each other, because `height: 100%`
       makes each card fill its own column, and the column row above
       has `align-items: stretch` — so both columns (and therefore
       both cards) automatically match whichever one is naturally
       tallest, with `min-height: 135px` as a floor so they never look
       too short either. */
    .fnd-verdict-card,
    .fnd-ring-card {
        box-sizing: border-box;
    }

    .fnd-verdict-card {
        background: #14141f !important;
        border: 1px solid #23232f !important;
    }

    /* `width: 100%` (not a fixed px width) makes each card fill its
       own 50%-width column exactly, so both boxes are always
       identically sized and aligned no matter the exact viewport
       width. Nothing rendered *inside* either card changes. */
    .fnd-verdict-card {
        flex: 1 1 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        height: 100% !important;
        min-height: 135px !important;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        gap: 0.15rem;
        padding: 0.6rem 0.6rem;
    }
    .fnd-verdict-icon {
        width: 36px;
        height: 36px;
        font-size: 1.05rem;
        margin: 0 auto;
    }
    .fnd-verdict-text {
        font-size: 1rem;
    }
    .fnd-verdict-card .fnd-badge {
        font-size: 0.68rem;
        padding: 0.2rem 0.55rem;
    }

    /* Same fix mirrored on the ring card: width:100% + height:100%
       instead of a fixed 135px box, so it fills its column exactly
       and matches the verdict card's box exactly — same width, same
       (stretched, equal) height, same alignment, content never
       clipped. */
    .fnd-ring-card {
        flex: 1 1 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        height: 100% !important;
        min-height: 135px !important;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        gap: 0.35rem;
        padding: 0.6rem 0.6rem;
    }
    .fnd-ring-wrap {
        width: 64px !important;
        height: 64px !important;
        margin: 0 auto;
    }
    .fnd-ring-card > div:last-child {
        font-size: 0.7rem !important;
        text-align: center;
        width: 100%;
    }

    .st-key-home_action_row [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        flex-direction: row !important;
        gap: 0.6rem !important;
    }
    .st-key-home_action_row [data-testid="stColumn"]:first-child {
        display: none !important;
    }
    .st-key-home_action_row [data-testid="stColumn"]:nth-child(2),
    .st-key-home_action_row [data-testid="stColumn"]:nth-child(3) {
        width: 50% !important;
        min-width: 0 !important;
        flex: 1 1 0 !important;
    }
}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
