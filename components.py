"""
Reusable UI building blocks for the Fake News Detector Streamlit app.
These mirror the sections in the mockup: sidebar nav, verdict card,
confidence ring, evidence sources list, and history table rows.
"""

import streamlit as st

VERDICT_META = {
    "TRUE": {"emoji": "✅", "label": "True", "class": "true", "badge": "fnd-badge-true", "color": "#4ade80"},
    "FALSE": {"emoji": "❌", "label": "False", "class": "false", "badge": "fnd-badge-false", "color": "#f87171"},
    "PARTIALLY TRUE": {"emoji": "⚠️", "label": "Partially True", "class": "partial", "badge": "fnd-badge-partial", "color": "#fbbf24"},
    "UNVERIFIABLE": {"emoji": "❓", "label": "Unverifiable", "class": "unverifiable", "badge": "fnd-badge-unverifiable", "color": "#a1a1c0"},
}


def verdict_meta(verdict: str) -> dict:
    return VERDICT_META.get((verdict or "").upper(), VERDICT_META["UNVERIFIABLE"])


# ---------------------------------------------------------------------------
# Sidebar (with working, reliable collapse / expand toggle)
# ---------------------------------------------------------------------------
def render_sidebar(active_page: str, username: str):
    """Renders logo + collapse toggle, nav buttons, and user card.
    Returns the page the user clicked on (or None if no click happened).

    FIX: collapsing no longer hides the sidebar completely (display:none).
    Instead, when collapsed, the sidebar is shrunk to a narrow strip (see
    app.py) that shows ONLY the expand button, rendered here in its normal
    place inside the sidebar. This replaces the old approach of hiding the
    sidebar and floating a separate button in the main content area via a
    fragile CSS selector — if that selector didn't match (which depends on
    Streamlit version/DOM structure), the button silently lost its style
    and became invisible/undiscoverable. Now the button is guaranteed to
    render somewhere sensible even with zero custom CSS applied.

    FIX 2: collapse button and expand button now use matching chevron
    glyphs ("«" collapses, "»" expands) instead of two visually unrelated
    icons ("⟨⟨" vs "☰"). Combined with the shared CSS rule in styles.py
    (`.st-key-sidebar_expand_btn button, .st-key-sidebar_collapse_btn
    button { ... }`), both buttons now look and animate identically —
    only the arrow direction changes to indicate what the click will do.
    """
    clicked = None
    with st.sidebar:
        if not st.session_state.get("sidebar_open", True):
            # Collapsed view: just the expand button, centered in the
            # narrow strip.
            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
            if st.button("»", key="sidebar_expand_btn", help="Show sidebar"):
                st.session_state.sidebar_open = True
                st.rerun()
            return None

        top_l, top_r = st.columns([4, 1], vertical_alignment="center")
        with top_l:
            st.markdown(
                """
                <div class="fnd-logo">
                    <div class="fnd-logo-icon">🔍</div>
                    <div>Fake News<br/>Detector</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with top_r:
            if st.button("«", key="sidebar_collapse_btn", help="Collapse sidebar"):
                st.session_state.sidebar_open = False
                st.rerun()

        nav_items = [("home", "🏠  Home"), ("history", "🕒  History"), ("logout", "↪️  Logout")]
        for key, label in nav_items:
            is_active = key == active_page
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                clicked = key

        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="fnd-user-card">
                <div class="fnd-user-avatar">{username[:1].upper()}</div>
                <div class="fnd-user-meta">
                    <div class="fnd-user-name">{username}</div>
                    <div class="fnd-user-role">Student</div>
                </div>
                <div class="fnd-user-chevron">⌄</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    return clicked


# ---------------------------------------------------------------------------
# "How it works" side panel (home page)
# ---------------------------------------------------------------------------
def render_how_it_works():
    steps = [
        ("1", "Paste a claim", "Add any news or statement"),
        ("2", "Our AI analyzes", "We scan multiple trusted sources"),
        ("3", "Get the verdict", "See result with evidence & reasoning"),
    ]
    st.markdown('<div class="fnd-card">', unsafe_allow_html=True)
    st.markdown("#### 💡 How it works")
    for num, title, subtitle in steps:
        st.markdown(
            f"""
            <div style="display:flex;gap:0.7rem;margin:0.8rem 0;">
                <div class="fnd-step-icon">{num}</div>
                <div>
                    <div style="font-weight:600;font-size:0.9rem;">{title}</div>
                    <div style="color:#8a8aa3;font-size:0.8rem;">{subtitle}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <div class="fnd-quote">
            "Think before you share.<br/>Verify before you believe."
            <svg class="fnd-quote-underline" viewBox="0 0 70 6" xmlns="http://www.w3.org/2000/svg">
                <path d="M2 4 Q 12 -1, 22 4 T 42 4 T 62 4" stroke="#8b5cf6" stroke-width="2"
                      fill="none" stroke-linecap="round"/>
            </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# "Powered by" tech badge panel (home page, fills the right column so it
# doesn't look empty under "How it works")
# ---------------------------------------------------------------------------
def render_tech_badge():
    st.markdown(
        """
        <div class="fnd-card">
            <div style="font-weight:700;margin-bottom:0.9rem;">⚙️ Powered by</div>
            <div class="fnd-tech-row">
                <div class="fnd-tech-chip">⚡ Groq</div>
                <div class="fnd-tech-chip">✨ Gemini</div>
                <div class="fnd-tech-chip">🦆 DuckDuckGo</div>
            </div>
            <div style="color:#8a8aa3;font-size:0.8rem;margin-top:0.9rem;line-height:1.5;">
                Runs on free-tier cloud AI models — no local server or GPU needed,
                so this always stays online.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Verdict card (results page, left box)
# ---------------------------------------------------------------------------
def render_verdict_card(verdict: str, confidence: int | None = None):
    meta = verdict_meta(verdict)
    conf_line = f'<div class="fnd-badge {meta["badge"]}">' + (
        "High Confidence" if (confidence or 0) >= 75 else
        "Medium Confidence" if (confidence or 0) >= 45 else
        "Low Confidence"
    ) + "</div>"

    st.markdown(
        f"""
        <div class="fnd-verdict-card {meta['class']}">
            <div class="fnd-verdict-icon">{meta['emoji']}</div>
            <div>
                <div style="color:#9c9cb0;font-size:0.78rem;letter-spacing:0.05em;">VERDICT</div>
                <div class="fnd-verdict-text">{meta['label'].upper()}</div>
                <div style="margin-top:0.35rem;">{conf_line}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Confidence ring (SVG donut) — color now matches the verdict so it never
# clashes (e.g. no more purple ring next to a red FALSE card).
# ---------------------------------------------------------------------------
def render_confidence_ring(score: int, checked_at: str = "", sources_found: int = 0, color: str = "#8b5cf6"):
    score = max(0, min(100, int(score)))
    radius = 44
    stroke_width = 8
    circumference = 2 * 3.14159265 * radius
    offset = circumference * (1 - score / 100)

    svg = f"""
    <svg class="fnd-ring-wrap" width="118" height="118" viewBox="0 0 118 118">
        <circle cx="59" cy="59" r="{radius}" stroke="#20202c" stroke-width="{stroke_width}" fill="none"/>
        <circle cx="59" cy="59" r="{radius}" stroke="{color}" stroke-width="{stroke_width}" fill="none"
            stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{offset:.1f}"
            stroke-linecap="round" transform="rotate(-90 59 59)"/>
        <text x="59" y="55" text-anchor="middle" font-size="21" font-weight="700" fill="#f3f1f9">{score}%</text>
        <text x="59" y="73" text-anchor="middle" font-size="9.5" fill="#8a8aa3">Confidence</text>
    </svg>
    """

    st.markdown(
        f"""
        <div class="fnd-card fnd-ring-card">
            <div>{svg}</div>
            <div style="font-size:0.85rem;color:#cfcfe0;">
                <div style="color:#8a8aa3;">Checked At</div>
                <div style="margin-bottom:0.6rem;">{checked_at}</div>
                <div style="color:#8a8aa3;">Sources Found</div>
                <div>{sources_found}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# "Why this verdict" reasoning card
# ---------------------------------------------------------------------------
def render_reasoning_card(reasoning: str):
    st.markdown(
        f"""
        <div class="fnd-card">
            <div style="font-weight:700;margin-bottom:0.6rem;">🧩 Why this verdict?</div>
            <div style="color:#cfcfe0;font-size:0.9rem;line-height:1.6;">{reasoning}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Evidence sources card
# ---------------------------------------------------------------------------
def render_evidence_card(evidence_chunks: list):
    rows_html = ""
    for chunk in evidence_chunks:
        source = chunk.get("source", "Unknown source")
        rows_html += f"""
        <div class="fnd-source-row">
            <div class="fnd-source-icon">🔗</div>
            <div>
                <div class="fnd-source-name">{source}</div>
                <div class="fnd-source-tag">Web source</div>
            </div>
        </div>
        """

    st.markdown(
        f"""
        <div class="fnd-card">
            <div style="font-weight:700;margin-bottom:0.4rem;">🔗 Evidence sources</div>
            {rows_html if rows_html else '<div style="color:#8a8aa3;font-size:0.85rem;">No sources found</div>'}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# History table
# ---------------------------------------------------------------------------
def render_history_header():
    st.markdown(
        """
        <div class="fnd-history-header">
            <div>Claim</div><div>Verdict</div><div>Confidence</div>
            <div>Sources</div><div>Checked At</div><div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_history_row(claim_text: str, verdict: str, confidence: int, sources: int, checked_at: str):
    meta = verdict_meta(verdict)
    claim_short = (claim_text[:60] + "...") if len(claim_text) > 60 else claim_text
    st.markdown(
        f"""
        <div class="fnd-history-row">
            <div>{claim_short}</div>
            <div><span class="fnd-badge {meta['badge']}">{meta['label']}</span></div>
            <div>{confidence}%</div>
            <div>{sources}</div>
            <div style="color:#8a8aa3;">{checked_at}</div>
            <div>→</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
