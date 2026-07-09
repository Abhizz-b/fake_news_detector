"""
Custom CSS for the Fake News Detector app.
Import and call `inject_css()` once at the top of app.py.
"""

import streamlit as st

CSS = """
<style>
/* ---------- Global ---------- */
.stApp {
    background-color: #0b0b14;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden;}
/* FIX: these reserve empty space even when just visibility:hidden (that
   was likely the empty rounded box floating above "How it works" in the
   screenshot). display:none removes them from layout entirely. */
[data-testid="stHeader"] {
    display: none !important;
}
[data-testid="stDecoration"] {
    display: none !important;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    animation: fndFadeIn 0.4s ease-out;
}

/* =========================================================================
   SIDEBAR
   We drive our own collapse/expand instead of Streamlit's native control
   (that was the source of the old "sidebar disappears, can't reopen"
   bug). The native collapse arrow + resize handle are hidden here; the
   actual show/hide logic and the two custom toggle buttons are handled
   in app.py / components.py via session_state.
   ========================================================================= */
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

/* FIX: added `transition` on width/min-width/max-width so collapse <->
   expand animates smoothly instead of snapping instantly between
   280px and 60px. `overflow: hidden` prevents inner content from
   spilling out mid-transition while the sidebar is narrower than its
   content. The inner wrapper gets its own opacity transition so
   content fades rather than abruptly popping in/out. */
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

/* FIX: collapse button (expanded state) and expand button (collapsed
   state) now share one style block so they look and feel identical —
   only the glyph inside differs (rendered via components.py), and even
   that now uses matching chevron glyphs ("«" / "»") instead of two
   visually unrelated icons ("⟨⟨" vs "☰"). */
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

/* Sidebar nav buttons */
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
/* the collapse/expand buttons also match .stButton above by default, so
   we re-assert their compact style with higher specificity */
section[data-testid="stSidebar"] .st-key-sidebar_collapse_btn button,
section[data-testid="stSidebar"] .st-key-sidebar_expand_btn button {
    width: 42px !important;
}

/* Sidebar user card */
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

/* ---------- Hero heading ---------- */
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

/* ---------- Input card focus glow ---------- */
.stTextArea textarea {
    border-radius: 12px !important;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.stTextArea textarea:focus {
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.25) !important;
    border-color: #8b5cf6 !important;
}

/* ---------- How it works step icon ---------- */
.fnd-step-icon {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    background: linear-gradient(135deg, rgba(139,92,246,0.25), rgba(109,40,217,0.2));
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-weight: 700;
    color: #d8cffa;
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

/* ---------- Tech badge chips ("Powered by") ---------- */
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

/* ---------- Verdict badges ---------- */
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

/* ---------- Results row: verdict card + confidence ring ----------
   vertical_alignment="center" on st.columns() (set in app.py) takes
   care of matching the two cards vertically; these rules just make
   sure each card's own content is centered and doesn't leave dead
   space at the bottom. */
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

/* ---------- Source rows ---------- */
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
.fnd-source-name { font-weight: 600; font-size: 0.88rem; color: #f0eefc; }
.fnd-source-tag { color: #8a8aa3; font-size: 0.75rem; }

/* ---------- History table ---------- */
.fnd-history-header {
    display: grid;
    grid-template-columns: 3fr 1fr 1.2fr 0.8fr 1.4fr 0.4fr;
    gap: 0.5rem;
    color: #8a8aa3;
    font-size: 0.78rem;
    padding: 0.4rem 1rem;
}
.fnd-history-row {
    display: grid;
    grid-template-columns: 3fr 1fr 1.2fr 0.8fr 1.4fr 0.4fr;
    gap: 0.5rem;
    align-items: center;
    background: #14141f;
    border: 1px solid #23232f;
    border-radius: 12px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.88rem;
    transition: border-color 0.15s ease, transform 0.15s ease;
    animation: fndFadeUp 0.35s ease-out both;
}
.fnd-history-row:hover {
    border-color: #8b5cf6;
    transform: translateX(2px);
}

/* =========================================================================
   FIX: Themed loading spinner + status alerts.
   Previously st.spinner() rendered as Streamlit's plain default gray
   box, full-width, with no styling — which is what looked "ugly" and
   out of place below the input card. Now it matches the app's dark
   card aesthetic and (combined with the app.py fix that moves
   run_fact_check() inside the left column) stays constrained to the
   same width as the claim input card instead of spanning the page.
   ========================================================================= */
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

/* ---------- Keyframes ---------- */
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
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
