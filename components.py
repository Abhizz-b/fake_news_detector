"""
Reusable UI building blocks for the Fake News Detector Streamlit app.
These mirror the sections in the mockup: sidebar nav, verdict card,
confidence ring, evidence sources list, and history table rows.
"""

from datetime import datetime

import streamlit as st

VERDICT_META = {
    "TRUE": {"emoji": "✅", "label": "True", "class": "true", "badge": "fnd-badge-true", "color": "#4ade80"},
    "FALSE": {"emoji": "❌", "label": "False", "class": "false", "badge": "fnd-badge-false", "color": "#f87171"},
    "PARTIALLY TRUE": {"emoji": "⚠️", "label": "Partially True", "class": "partial", "badge": "fnd-badge-partial", "color": "#fbbf24"},
    "UNVERIFIABLE": {"emoji": "❓", "label": "Unverifiable", "class": "unverifiable", "badge": "fnd-badge-unverifiable", "color": "#a1a1c0"},
}


def verdict_meta(verdict: str) -> dict:
    return VERDICT_META.get((verdict or "").upper(), VERDICT_META["UNVERIFIABLE"])


def _short_checked_at(checked_at: str) -> str:
    """Best-effort compact version of a checked-at timestamp, used only
    on mobile (<640px) where the full 'YYYY-MM-DD HH:MM:SS' string was
    forcing the confidence-ring card to grow taller than the verdict
    card next to it. e.g. '2026-07-12 17:24:10' -> 'Jul 12, 5:24 PM'.
    Falls back to the original string untouched if it doesn't match
    the expected format (so nothing breaks if the caller ever passes a
    differently-formatted string).
    """
    if not checked_at:
        return checked_at
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(checked_at, fmt)
            return dt.strftime("%b %d, %I:%M %p").replace(" 0", " ")
        except (ValueError, TypeError):
            continue
    return checked_at


# ---------------------------------------------------------------------------
# NEW: Minimal top header (replaces the sidebar entirely)
# ---------------------------------------------------------------------------
def render_account_menu(username: str):
    """Minimal top-right account control: a plain circular avatar button
    that opens a small popover dropdown — styled to match the approved
    mockup: name + role header up top, a divider, then plain-text
    History and Logout rows (Logout styled as a destructive/red action).
    No icons are used for History/Logout — plain text only, to avoid
    Streamlit's native emoji rendering (colorful, cartoon-ish) clashing
    with the mockup's clean monochrome look.
    """
    clicked = None
    with st.popover(username[:1].upper() if username else "?"):
        st.markdown(
            f"""
            <div class="fnd-account-header">
                <div class="fnd-account-name">{username}</div>
                <div class="fnd-account-role">Student</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("History", key="account_menu_history_btn", use_container_width=True):
            clicked = "history"

        st.markdown("<div class='fnd-account-divider'></div>", unsafe_allow_html=True)

        if st.button("Logout", key="account_menu_logout_btn", use_container_width=True):
            clicked = "logout"
    return clicked


def render_header(username: str):
    """Slim top header replacing the sidebar: a simple search-glass icon
    + wordmark on the left, and the circular account avatar (with its
    History/Logout popover) on the right. The bar itself has no distinct
    background of its own — it blends with the page background, with
    only a thin, low-opacity bottom divider separating it from the hero
    content below (matching the approved mockup exactly, instead of
    looking like a separate "search bar" card). Returns 'history',
    'logout', or None depending on what the person clicked in the
    account menu.
    """
    clicked = None
    with st.container(key="app_header_bar"):
        left, right = st.columns([6, 1], vertical_alignment="center")
        with left:
            st.markdown(
                """
                <div class="fnd-header-brand">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="11" cy="11" r="7"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                    <span class="fnd-brand-wordmark">Fake News Detector</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            clicked = render_account_menu(username)
    return clicked


# ---------------------------------------------------------------------------
# Sidebar (with working, reliable collapse / expand toggle)
# NOTE: kept here unused, in case a sidebar-based nav is wanted again later.
# The app now uses render_header()/render_account_menu() above instead.
# ---------------------------------------------------------------------------
def render_sidebar(active_page: str, username: str):
    """Renders logo + collapse toggle, nav buttons, and user card.
    Returns the page the user clicked on (or None if no click happened).
    """
    clicked = None
    with st.sidebar:
        if not st.session_state.get("sidebar_open", True):
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

    steps_html = ""
    for i, (num, title, subtitle) in enumerate(steps):
        is_last = i == len(steps) - 1
        line_class = "" if is_last else "fnd-step-line"
        steps_html += (
            f'<div class="fnd-step-row {line_class}">'
            f'<div class="fnd-step-icon">{num}</div>'
            f'<div>'
            f'<div class="fnd-step-title">{title}</div>'
            f'<div class="fnd-step-subtitle">{subtitle}</div>'
            f'</div>'
            f'</div>'
        )

    quote_html = (
        '<div class="fnd-quote">'
        '"Think before you share.<br/>Verify before you believe."'
        '<svg class="fnd-quote-underline" viewBox="0 0 70 6" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M2 4 Q 12 -1, 22 4 T 42 4 T 62 4" stroke="#8b5cf6" stroke-width="2" '
        'fill="none" stroke-linecap="round"/>'
        '</svg>'
        '</div>'
    )

    card_html = (
        '<div class="fnd-card">'
        '<div class="fnd-card-heading">💡 How it works</div>'
        f'{steps_html}'
        f'{quote_html}'
        '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)


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
    conf_score = confidence or 0
    conf_full = (
        "High Confidence" if conf_score >= 75 else
        "Medium Confidence" if conf_score >= 45 else
        "Low Confidence"
    )
    # FIX (mobile): "High Confidence" / "Medium Confidence" / "Low
    # Confidence" is what was forcing the badge (and the whole card) to
    # be wider/taller than needed on a phone screen. A short version
    # ("High" / "Medium" / "Low") is rendered alongside it in a
    # separate span — styles.py shows only one of the two depending on
    # viewport width, so desktop keeps the full wording and mobile gets
    # the compact one.
    conf_short = "High" if conf_score >= 75 else "Medium" if conf_score >= 45 else "Low"
    conf_line = (
        f'<div class="fnd-badge {meta["badge"]}">'
        f'<span class="fnd-text-full">{conf_full}</span>'
        f'<span class="fnd-text-short">{conf_short}</span>'
        f'</div>'
    )

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

    # FIX (mobile): "Checked At" / "Sources Found" are the full labels
    # kept for desktop; "Checked" / "Sources" are the compact versions
    # shown only on phones. Same idea for the timestamp itself — the
    # full 'YYYY-MM-DD HH:MM:SS' string is kept for desktop, and a short
    # 'Jul 12, 5:24 PM' version (via _short_checked_at) is shown on
    # mobile instead. This is what was making the ring card taller than
    # the verdict card next to it on a phone screen.
    short_checked_at = _short_checked_at(checked_at)

    st.markdown(
        f"""
        <div class="fnd-card fnd-ring-card">
            <div>{svg}</div>
            <div style="font-size:0.85rem;color:#cfcfe0;">
                <div style="color:#8a8aa3;">
                    <span class="fnd-text-full">Checked At</span><span class="fnd-text-short">Checked</span>
                </div>
                <div style="margin-bottom:0.6rem;">
                    <span class="fnd-text-full">{checked_at}</span><span class="fnd-text-short">{short_checked_at}</span>
                </div>
                <div style="color:#8a8aa3;">
                    <span class="fnd-text-full">Sources Found</span><span class="fnd-text-short">Sources</span>
                </div>
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
    import html

    rows_html = ""
    for chunk in evidence_chunks:
        source = chunk.get("source", "Unknown source")
        # FIX: source was rendered as plain text (no <a> tag), so links
        # weren't clickable. Real URLs now render as an actual anchor
        # (opens in a new tab); anything that isn't a proper http(s) URL
        # falls back to plain text instead of a broken/dead link.
        is_link = isinstance(source, str) and source.startswith(("http://", "https://"))
        safe_source = html.escape(source)
        display_text = safe_source if len(safe_source) <= 70 else safe_source[:67] + "..."

        if is_link:
            name_html = (
                f'<a class="fnd-source-name fnd-source-link" href="{safe_source}" '
                f'target="_blank" rel="noopener noreferrer" title="{safe_source}">{display_text}</a>'
            )
        else:
            name_html = f'<div class="fnd-source-name">{safe_source}</div>'

        # FIX (mobile overflow): wrapped name+tag in a dedicated
        # .fnd-source-body div (previously a bare, class-less <div>).
        # Without a class here there was nothing for styles.py to
        # target, so this block could never shrink below the natural
        # width of the longest URL inside it — that's what let the
        # 5th/6th evidence links overflow past the card's right edge
        # on a phone. See .fnd-source-body + a.fnd-source-link in
        # styles.py for the actual shrink/wrap rules.
        rows_html += f"""
        <div class="fnd-source-row">
            <div class="fnd-source-icon">🔗</div>
            <div class="fnd-source-body">
                {name_html}
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
    # NOTE: this header row is hidden outright on phones (<640px) via
    # styles.py — a 5-column grid header has nothing left to line up
    # with once history rows switch to a stacked layout there, so each
    # row shows its own inline label (via the data-label attributes in
    # render_history_row below) instead of relying on this header.
    st.markdown(
        """
        <div class="fnd-history-header">
            <div>Claim</div><div>Verdict</div><div>Confidence</div>
            <div>Sources</div><div>Checked At</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_history_row(claim_text: str, verdict: str, confidence: int, sources: int, checked_at: str):
    meta = verdict_meta(verdict)
    claim_short = (claim_text[:60] + "...") if len(claim_text) > 60 else claim_text
    # FIX (mobile overflow): the old 5-column CSS grid (Claim / Verdict /
    # Confidence / Sources / Checked At) has no room to breathe below
    # ~640px — columns squeeze together and "Checked At" in particular
    # wraps its date and time across multiple broken lines. Below that
    # breakpoint, styles.py switches .fnd-history-row from `display:
    # grid` to a stacked `display: flex; flex-direction: column`, and
    # uses each div's `data-label` attribute (via a CSS ::before) to
    # print a small "CLAIM" / "VERDICT" / etc. label above its value —
    # these attributes are inert (ignored) at desktop width, where the
    # grid + header row above still do the labelling instead.
    st.markdown(
        f"""
        <div class="fnd-history-row">
            <div data-label="Claim">{claim_short}</div>
            <div data-label="Verdict"><span class="fnd-badge {meta['badge']}">{meta['label']}</span></div>
            <div data-label="Confidence">{confidence}%</div>
            <div data-label="Sources">{sources}</div>
            <div data-label="Checked At" style="color:#8a8aa3;">{checked_at}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
