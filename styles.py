"""
Custom CSS for the Fake News Detector app.
Import and call `inject_css()` once at the top of app.py.
"""

import streamlit as st

CSS = """
<style>
/* ---------- Global ---------- */
.stApp {
    background:
        radial-gradient(ellipse 900px 480px at 50% -8%, rgba(139, 92, 246, 0.16), transparent 60%),
        #0b0b14;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
/* FIX: visibility:hidden still reserves the element's box (that's the
   empty rounded rectangle that was floating above "How it works").
   display:none removes it from layout entirely. */
[data-testid="stToolbar"] {
    display: none !important;
}
[data-testid="stStatusWidget"] {
    display: none !important;
}
/* FIX: these reserve empty space even when just visibility:hidden (that
   was likely the empty rounded box floating above "How it works" in the
   screenshot). display:none removes them from layout entirely. */
[data-testid="stHeader"] {
    display: none !important;
}
[data-testid="stDecoration"] {
    display: none !important;
}
/* FIX: Streamlit auto-adds a small anchor/link icon next to any
   h1-h6 it renders (even inside raw unsafe_allow_html HTML like our
   hero heading) — this was the stray chain-link icon floating next
   to "Verify everything." Hiding it globally since we don't use
   deep-linkable headers anywhere in this app. */
[data-testid="stHeaderActionElements"] {
    display: none !important;
}

/* FIX: was 2rem, pushing the whole app (header + hero) down and
   forcing an extra scroll to see everything. Trimmed to bring the
   header close to the top of the viewport. */
.block-container {
    padding-top: 0.6rem;
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

/* =========================================================================
   NEW: Slim top header (replaces the sidebar entirely)
   Left: a plain outline search-glass icon + wordmark. Right: a circular
   avatar (rendered via st.popover in components.py) that opens a small
   History/Logout menu on click — there's no persistent nav rail anymore.
   ========================================================================= */
/* =========================================================================
   FIX: Navbar container — previously had its own solid background
   (#0e0c18), which read as a separate "search bar" card floating on
   top of the page instead of a proper header. Now it's fully
   transparent (matches the page background exactly, since it's the
   same stack the .stApp gradient/base-color sits on), and the only
   separation from the hero content below is a single, very
   low-opacity 1px line — matching the approved mockup exactly.
   FIX (round 2): padding/margin trimmed down — the navbar was
   sitting too far from the top of the page and leaving too big a
   gap above the "Think twice." headline below it.
   ========================================================================= */
.st-key-app_header_bar {
    background: transparent;
    padding: 0.55rem 0.5rem;
    margin-bottom: 0.2rem;
    position: relative;
}
/* =========================================================================
   Avatar trigger: circle avatar + separate chevron, both inside a
   rounded "pill" — matching the approved mockup. This time done more
   carefully than before: `display: inline-flex` is applied ONLY to
   the outer [data-testid="stPopover"] container (a real box with real
   dimensions — safe, doesn't break Streamlit's position measurement).
   We do NOT use `display: contents` on the inner wrapper div anymore —
   that was the actual change that broke the dropdown's positioning
   last time (it removes the element's box entirely, so
   getBoundingClientRect() returned nothing usable). Leaving that inner
   div's own display untouched keeps positioning fully stable while
   still giving us the pill look via simple flex + background/border/
   radius on the outer element.
   ========================================================================= */
[data-testid="stPopover"] {
    display: inline-flex;
    align-items: center;
    margin-right: -0.4rem;
}
/* FIX: a plain border-bottom on this element only spans the padded
   block-container width, not the full page. This pseudo-element
   breaks out to 100vw and re-centers itself so the separator line
   touches the true left and right edges of the browser window,
   matching the reference mockup. */
.st-key-app_header_bar::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 100vw;
    height: 1px;
    background: rgba(255, 255, 255, 0.06);
}

.fnd-header-brand {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    color: #f3f1f9;
    font-weight: 700;
    font-size: 0.9rem;
    padding-top: 0.4rem;
}
.fnd-header-brand svg {
    color: #cfcfe0;
    flex-shrink: 0;
}

/* Avatar circle button itself — plain, bold initial, no icon overlap.
   FIX: Streamlit's popover trigger button can carry its own native
   disclosure marker/pseudo-content depending on browser + baseweb
   version — this is what was showing up as a *second*, stray gray
   triangle outside the circle in addition to our own intentional
   chevron on [data-testid="stPopover"]::after above. Forcing both
   ::before and ::after to `content: none` directly on the button
   guarantees only our single external chevron ever renders. */
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
/* The letter itself: Streamlit renders the button's text label inside
   its own inner wrapper (markdown container / <p>). THIS inner element
   — not the button — is what gets the circular purple-gradient avatar
   look, fixed to a neat 34x34 circle with the bold initial centered
   inside it. */
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
/* FIX (round 3): rather than hiding Streamlit's native trigger icon
   (that just made the chevron decorative/unclickable), we keep it —
   it's a real child of the real <button>, so it's clickable by
   definition — and simply restyle its color/size so it reads as a
   quiet chevron sitting in the pill's empty space to the right of the
   circle, instead of an oversized icon crammed inside the circle. */
[data-testid="stPopover"] button svg,
[data-testid="stPopover"] button [data-testid*="Icon"] {
    width: 14px !important;
    height: 14px !important;
    color: #9d97b3 !important;
    flex-shrink: 0;
}

/* =========================================================================
   NEW: Account dropdown card — matches the approved mockup: rounded
   card, name + role header block, thin dividers, and quiet plain-text
   rows for History/Logout (no icons — see components.py), with Logout
   styled as a destructive action.
   ========================================================================= */
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
    margin-bottom: 0.3rem;
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
    margin: 0.3rem 0.2rem;
}

/* FIX: excessive gap between the History row and the Logout row.
   Streamlit wraps each st.button in its own element-container with a
   default vertical gap/margin meant for full-page layouts, which
   looked huge inside this small popover. Tightening the vertical
   block gap and zeroing each element-container's own margin fixes
   the spacing without touching the divider's own margin above. */
[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {
    gap: 0.1rem !important;
}
[data-testid="stPopoverBody"] [data-testid="element-container"] {
    margin: 0 !important;
}

/* Restyle the History / Logout st.button rows inside the popover from
   generic Streamlit buttons into quiet, left-aligned menu items. */
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
/* FIX: text-align/justify-content on the button itself weren't enough —
   Streamlit renders the button's label inside a nested
   [data-testid="stMarkdownContainer"] > p, which carries its own
   center-aligned default and was winning over the outer button's
   text-align. Forcing left-align (and full width so there's room to
   actually sit left) on that inner element is what actually moves
   "History"/"Logout" to the left instead of the middle. */
[data-testid="stPopoverBody"] .stButton button p,
[data-testid="stPopoverBody"] .stButton button div {
    text-align: left !important;
    width: 100%;
}
[data-testid="stPopoverBody"] .stButton button:hover {
    background: rgba(139, 92, 246, 0.12) !important;
    color: #fff !important;
}
/* FIX: Logout wasn't rendering red — `[data-testid="stPopoverBody"]
   .stButton button` above has higher CSS specificity (attribute +
   class + element = 0,2,1) than the old `.st-key-account_menu_logout_btn
   button` rule (class + element = 0,1,1), so the generic gray color
   always won even with !important on both sides (equal !important
   weight falls back to specificity, not source order). Prefixing with
   the same [data-testid="stPopoverBody"] attribute selector brings
   this rule to equal-or-higher specificity so red actually applies. */
[data-testid="stPopoverBody"] .st-key-account_menu_logout_btn button {
    color: #f87171 !important;
}
[data-testid="stPopoverBody"] .st-key-account_menu_logout_btn button:hover {
    background: rgba(248, 113, 113, 0.1) !important;
    color: #f87171 !important;
}

/* =========================================================================
   NEW: Minimal, vertically-centered home page hero
   ("Think Twice. Verify Everything.")
   The whole block is wrapped in st.container(key="home_center_wrap") in
   app.py; this class turns that wrapper into a flex column that centers
   its children both horizontally and vertically, giving the generous,
   uncluttered spacing from the approved mockup instead of everything
   being pinned to the top of the page.
   FIX: top padding was 4rem, which — stacked on top of the header's
   own padding/margin above it — created a huge, page-lengthening gap
   between the navbar and "Think twice." Reduced so the hero sits right
   under the header without needing to scroll to see the whole page.
   ========================================================================= */
.st-key-home_center_wrap {
    display: flex !important;
    flex-direction: column;
    align-items: center;
    max-width: 1180px;
    margin: 0 auto;
    padding: 1.4rem 2rem 2rem;
}
.fnd-hero-minimal {
    text-align: center;
    margin-bottom: 2.6rem;
    animation: fndFadeUp 0.5s ease-out both;
}
.fnd-hero-minimal h1 {
    font-size: 3.4rem;
    font-weight: 800;
    line-height: 1.12;
    letter-spacing: -0.02em;
    margin-bottom: 0.4rem;
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
    font-size: 1rem;
    line-height: 1.7;
    max-width: 520px;
    margin: 1rem auto 0;
}

/* The claim textarea + quick-action pills + Clear/Check Now row all
   live inside this shell, capped at the same 880px the mockup uses —
   this (not a per-widget max-width) is what controls the box's width,
   so it stays wide and spacious instead of looking cramped. */
.st-key-claim_shell {
    width: 100%;
    max-width: 880px;
}

/* Quick-action pills below the claim textarea — three equal-width
   buttons restyled from generic Streamlit buttons into rounded outline
   pills, matching the approved mockup. */
[class*="quick_pill"] button {
    background: #0f0c1a !important;
    border: 1px solid #2a2a3a !important;
    color: #8d87a3 !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.2s ease;
}
[class*="quick_pill"] button:hover {
    border-color: #8b5cf6 !important;
    color: #f3f1f9 !important;
    background: rgba(139, 92, 246, 0.12) !important;
}

/* Minimal home page: the single claim/article box (headline or full
   article — same field), with a soft purple glow border */
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

/* Minimal home page: Clear button styled as a quiet outline button
   (rather than default Streamlit "secondary" gray) */
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

/* ---------- Input card focus glow (results/other pages) ---------- */
.stTextArea textarea {
    border-radius: 12px !important;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.stTextArea textarea:focus {
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.25) !important;
    border-color: #8b5cf6 !important;
}

/* ---------- How it works: card heading + steps ----------
   FIX: previously each step was rendered via its own st.markdown()
   call, which meant Streamlit injected its own default block spacing
   between them — on top of our own margins — making the gaps look
   uneven and "ugly". Now all steps render inside a single markdown
   call (see components.py) so spacing is fully controlled by this
   CSS. A thin connecting line between icons gives it a cleaner,
   timeline-style feel instead of three disconnected rows. */
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
