import streamlit as st
import os
from datetime import datetime
import time
import base64
from fact_checker import FactChecker
import auth
import db_utils
from pdf_export import generate_fact_check_pdf
from model_manager import model_manager

from styles import inject_css
from components import (
    render_header,
    render_verdict_card,
    render_confidence_ring,
    render_reasoning_card,
    render_evidence_card,
    render_history_header,
    render_history_row,
    verdict_meta,
)

# Initialize database
db_utils.init_db()

# Page config
st.set_page_config(
    page_title="AI Fake News Detector",
    page_icon="🔍",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

inject_css()


# ===========================================================================
# ---- CONFIG / SETUP LOGIC ----
# ===========================================================================
#
# DEPLOYMENT FIX: the original flow always sent every visitor through
# show_initial_config_wizard() to collect their own Groq + Gemini keys,
# because check_user_config_status() / get_config_parameters() only ever
# looked at a per-user config file (via user_config.py) and never checked
# Streamlit Secrets. That's fine for local dev but wrong for a public
# demo link — nobody visiting the deployed app should have to go generate
# their own API keys.
#
# Fix: if the app owner has set GROQ_API_KEY + GEMINI_API_KEY in Streamlit
# Community Cloud's "Secrets" (Settings -> Secrets), every visitor
# transparently uses those shared keys and the wizard is skipped
# entirely. If secrets are NOT set (e.g. running locally without a
# secrets.toml), everything falls back to the original per-user wizard
# flow untouched, so local/dev behavior doesn't change.
# ===========================================================================

def has_shared_secrets_config() -> bool:
    """True if the app owner has configured shared Groq + Gemini keys via
    Streamlit Secrets. When True, ALL visitors use these shared keys
    automatically and never see the API-key setup wizard."""
    try:
        return bool(st.secrets.get("GROQ_API_KEY")) and bool(st.secrets.get("GEMINI_API_KEY"))
    except Exception:
        # st.secrets raises/behaves oddly if no secrets.toml exists at all
        # (e.g. fresh local clone) - treat that as "no shared config".
        return False


def get_shared_config_parameters() -> dict:
    """Build the same shape of dict as get_config_parameters(), but
    sourced directly from Streamlit Secrets instead of any per-user
    config file. This is what powers the public, no-key-required demo."""
    groq_key = st.secrets["GROQ_API_KEY"]
    gemini_key = st.secrets["GEMINI_API_KEY"]
    chat_model = st.secrets.get("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")
    embedding_model = "gemini-embedding-001"
    search_provider = st.secrets.get("SEARCH_PROVIDER", "duckduckgo")

    provider_config = {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": groq_key,
    }

    return {
        "provider_key": "groq",
        "api_base": provider_config["base_url"],
        "api_key": groq_key,
        "chat_model": chat_model,
        "embedding_model": embedding_model,
        "embedding_api_base": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "embedding_api_key": gemini_key,
        "search_provider": search_provider,
        "selected_language": "en",
        "provider_config": provider_config,
    }


def check_user_config_status():
    """Check whether config is ready and the wizard can be skipped."""
    if has_shared_secrets_config():
        return True

    from user_config import get_user_config_manager

    config_manager = get_user_config_manager()
    if not config_manager:
        return False

    user_config = config_manager.get_user_config()
    has_model_config = bool(user_config.get("model_config", {}))
    has_working_config = "config_completed" in user_config
    return has_model_config and has_working_config


def show_initial_config_wizard():
    """Show initial config wizard"""
    st.title("🚀 Welcome to the AI Fake News Detector")
    st.markdown(
        """
    Before you start, please complete a one-time setup.
    Once configured, you can use the system directly.
    """
    )
    st.divider()
    st.subheader("⚙️ Setup")

    config_option = st.radio(
        "Select AI service type",
        options=[
            "⚡ Groq + Gemini (Free Cloud - Recommended)",
            "💻 LM Studio (Local GUI)",
            "☁️ OpenAI (Cloud service)",
            "🔧 Custom configuration",
        ],
        help="Select the AI service type you want to use",
    )

    manual_config = None

    if "⚡ Groq + Gemini" in config_option:
        st.subheader("⚡ Groq + Gemini configuration")
        st.info(
            "💡 Groq powers the chat/reasoning (fast & free), Gemini powers the "
            "embeddings (also free). Get a Groq key at console.groq.com and a "
            "Gemini key at aistudio.google.com"
        )

        groq_api_key = st.text_input(
            "🔑 Groq API Key", type="password",
            help="Get this free at console.groq.com", key="groq_api_key_input",
        )
        gemini_api_key = st.text_input(
            "🔑 Gemini API Key", type="password",
            help="Get this free at aistudio.google.com", key="gemini_api_key_input",
        )

        if groq_api_key and gemini_api_key:
            groq_chat_models = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "openai/gpt-oss-120b",
            ]
            chat_model = st.selectbox("💬 Chat model (Groq)", options=groq_chat_models)
            embedding_model = "gemini-embedding-001"
            st.caption(f"🧠 Embedding model: **{embedding_model}** (via Gemini, fixed)")

            st.subheader("🔍 Select search engine")
            search_options = {
                "🦆 DuckDuckGo (Recommended)": "duckduckgo",
                "🔍 SearXNG (Local)": "searxng",
            }
            selected_search = st.radio(
                "Search engine", options=list(search_options.keys()),
                help="DuckDuckGo needs no setup, SearXNG requires local deployment",
                horizontal=True, key="groqgemini_search",
            )
            search_provider = search_options[selected_search]
            searxng_url = None
            if search_provider == "searxng":
                searxng_url = st.text_input(
                    "🌐 SearXNG service address", value="http://localhost:8090",
                    help="Enter your SearXNG instance address",
                    placeholder="http://localhost:8090", key="groqgemini_searxng_url",
                )

            manual_config = {
                "name": "Groq + Gemini",
                "provider": "groq",
                "url": "https://api.groq.com/openai/v1",
                "api_key": groq_api_key,
                "chat_model": chat_model,
                "embedding_provider": "gemini",
                "embedding_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "embedding_api_key": gemini_api_key,
                "embedding_model": embedding_model,
                "search_provider": search_provider,
            }
            if searxng_url:
                manual_config["searxng_url"] = searxng_url
        else:
            st.warning("⚠️ Please enter both API keys to continue")

    elif "💻 LM Studio" in config_option:
        st.subheader("💻 LM Studio configuration")
        models = get_models_for_provider("lmstudio", "http://localhost:1234")
        if models:
            chat_models, embedding_models = categorize_models(models)
            col1, col2 = st.columns(2)
            with col1:
                chat_model = st.selectbox("💬 Chat model", options=chat_models if chat_models else models)
            with col2:
                embedding_model = st.selectbox("🧠 Embedding model", options=embedding_models if embedding_models else models)

            if chat_model and embedding_model:
                st.subheader("🔍 Select search engine")
                search_options = {
                    "🦆 DuckDuckGo (Recommended)": "duckduckgo",
                    "🔍 SearXNG (Local)": "searxng",
                }
                selected_search = st.radio(
                    "Search engine", options=list(search_options.keys()),
                    help="DuckDuckGo needs no setup, SearXNG requires local deployment",
                    horizontal=True, key="lmstudio_search",
                )
                search_provider = search_options[selected_search]
                searxng_url = None
                if search_provider == "searxng":
                    searxng_url = st.text_input(
                        "🌐 SearXNG service address", value="http://localhost:8090",
                        help="Enter your SearXNG instance address",
                        placeholder="http://localhost:8090", key="lmstudio_searxng_url",
                    )
                manual_config = {
                    "name": "LM Studio", "provider": "lmstudio",
                    "url": "http://localhost:1234/v1",
                    "chat_model": chat_model, "embedding_model": embedding_model,
                    "search_provider": search_provider,
                }
                if searxng_url:
                    manual_config["searxng_url"] = searxng_url
        else:
            st.warning("⚠️ Could not connect to LM Studio service, please make sure LM Studio is running")

    elif "☁️ OpenAI" in config_option:
        st.subheader("☁️ OpenAI configuration")
        api_key = st.text_input("🔑 OpenAI API Key", type="password", help="Enter your OpenAI API key")
        if api_key:
            openai_models = {
                "💬 Chat models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "🧠 Embedding models": ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"],
            }
            col1, col2 = st.columns(2)
            with col1:
                chat_model = st.selectbox("💬 Chat model", options=openai_models["💬 Chat models"])
            with col2:
                embedding_model = st.selectbox("🧠 Embedding model", options=openai_models["🧠 Embedding models"])

            st.subheader("🔍 Select search engine")
            search_options = {
                "🦆 DuckDuckGo (Recommended)": "duckduckgo",
                "🔍 SearXNG (Local)": "searxng",
            }
            selected_search = st.radio(
                "Search engine", options=list(search_options.keys()),
                help="DuckDuckGo needs no setup, SearXNG requires local deployment",
                horizontal=True, key="openai_search",
            )
            search_provider = search_options[selected_search]
            searxng_url = None
            if search_provider == "searxng":
                searxng_url = st.text_input(
                    "🌐 SearXNG service address", value="http://localhost:8090",
                    help="Enter your SearXNG instance address",
                    placeholder="http://localhost:8090", key="openai_searxng_url",
                )
            manual_config = {
                "name": "OpenAI", "provider": "openai",
                "url": "https://api.openai.com/v1", "api_key": api_key,
                "chat_model": chat_model, "embedding_model": embedding_model,
                "search_provider": search_provider,
            }
            if searxng_url:
                manual_config["searxng_url"] = searxng_url

    elif "🔧 Custom" in config_option:
        with st.expander("🚀 Custom configuration", expanded=True):
            url = st.text_input("🌐 API address", placeholder="http://localhost:8000/v1")
            if url:
                models = get_models_for_provider("custom", url.rstrip("/v1"))
                if models:
                    st.success(f"✅ Detected {len(models)} available models")
                    chat_models, embedding_models = categorize_models(models)
                    col1, col2 = st.columns(2)
                    with col1:
                        chat_model = st.selectbox("💬 Chat model", options=chat_models if chat_models else models)
                    with col2:
                        embedding_model = st.selectbox("🧠 Embedding model", options=embedding_models if embedding_models else models)

                    if chat_model and embedding_model:
                        st.subheader("🔍 Select search engine")
                        search_options = {
                            "🦆 DuckDuckGo (Recommended)": "duckduckgo",
                            "🔍 SearXNG (Local)": "searxng",
                        }
                        selected_search = st.radio(
                            "Search engine", options=list(search_options.keys()),
                            help="DuckDuckGo needs no setup, SearXNG requires local deployment",
                            horizontal=True, key="custom_search_1",
                        )
                        search_provider = search_options[selected_search]
                        searxng_url = None
                        if search_provider == "searxng":
                            searxng_url = st.text_input(
                                "🌐 SearXNG service address", value="http://localhost:8090",
                                help="Enter your SearXNG instance address",
                                placeholder="http://localhost:8090", key="custom_searxng_url_1",
                            )
                        manual_config = {
                            "name": "Custom configuration", "provider": "custom", "url": url,
                            "chat_model": chat_model, "embedding_model": embedding_model,
                            "search_provider": search_provider,
                        }
                        if searxng_url:
                            manual_config["searxng_url"] = searxng_url
                else:
                    st.warning("⚠️ Could not fetch model list from this address, please check the address")
                    st.info("📝 Please manually enter model names")
                    col1, col2 = st.columns(2)
                    with col1:
                        chat_model = st.text_input("💬 Chat model", placeholder="e.g. llama2")
                    with col2:
                        embedding_model = st.text_input("🧠 Embedding model", placeholder="e.g. nomic-embed-text")

                    if chat_model and embedding_model:
                        st.subheader("🔍 Select search engine")
                        search_options = {
                            "🦆 DuckDuckGo (Recommended)": "duckduckgo",
                            "🔍 SearXNG (Local)": "searxng",
                        }
                        selected_search = st.radio(
                            "Search engine", options=list(search_options.keys()),
                            help="DuckDuckGo needs no setup, SearXNG requires local deployment",
                            horizontal=True, key="custom_search_2",
                        )
                        search_provider = search_options[selected_search]
                        searxng_url = None
                        if search_provider == "searxng":
                            searxng_url = st.text_input(
                                "🌐 SearXNG service address", value="http://localhost:8090",
                                help="Enter your SearXNG instance address",
                                placeholder="http://localhost:8090", key="custom_searxng_url_2",
                            )
                        manual_config = {
                            "name": "Custom configuration", "provider": "custom", "url": url,
                            "chat_model": chat_model, "embedding_model": embedding_model,
                            "search_provider": search_provider,
                        }
                        if searxng_url:
                            manual_config["searxng_url"] = searxng_url

    if manual_config:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔗 Test connection", use_container_width=True):
                with st.spinner("Testing connection..."):
                    if test_config_connection(manual_config):
                        st.success("✅ Connection successful!")
                    else:
                        st.error("❌ Connection failed, please check configuration")
        with col2:
            if st.button("✨ Save configuration", type="primary", use_container_width=True):
                save_manual_config(manual_config)
                st.success("✅ Configuration complete! Entering main interface...")
                time.sleep(1)
                st.rerun()


def categorize_models(models):
    chat_models = []
    embedding_models = []
    for model in models:
        model_lower = model.lower()
        if any(keyword in model_lower for keyword in ["embed", "embedding", "nomic", "bge", "gte"]):
            embedding_models.append(model)
        else:
            chat_models.append(model)
    return chat_models, embedding_models


def get_models_for_provider(provider_type, url):
    import requests
    try:
        response = requests.get(f"{url}/models", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            if "data" in models_data:
                return [model["id"] for model in models_data["data"]]
            elif "models" in models_data:
                return [model["name"] for model in models_data["models"]]
            elif isinstance(models_data, list):
                return models_data
        return []
    except Exception:
        return []


def test_config_connection(config):
    try:
        import requests
        headers = {}
        if config.get("api_key"):
            headers["Authorization"] = f"Bearer {config['api_key']}"
        response = requests.get(f"{config['url']}/models", headers=headers, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def save_manual_config(config):
    from user_config import get_user_config_manager

    config_manager = get_user_config_manager()
    if config_manager:
        providers = {config["provider"]: {"base_url": config["url"]}}
        if "api_key" in config:
            providers[config["provider"]]["api_key"] = config["api_key"]

        embedding_provider_key = config.get("embedding_provider", config["provider"])
        if embedding_provider_key not in providers:
            providers[embedding_provider_key] = {"base_url": config.get("embedding_url", config["url"])}
            if "embedding_api_key" in config:
                providers[embedding_provider_key]["api_key"] = config["embedding_api_key"]

        user_config = {
            "model_config": {
                "providers": providers,
                "defaults": {
                    "llm_provider": config["provider"],
                    "llm_model": config["chat_model"],
                    "embedding_provider": embedding_provider_key,
                    "embedding_model": config["embedding_model"],
                    "search_provider": config.get("search_provider", "duckduckgo"),
                    "output_language": "en",
                },
            },
            "config_completed": True,
            "config_source": "manual",
        }

        if config.get("searxng_url"):
            user_config["search_config"] = {
                "search_providers": {"searxng": {"base_url": config["searxng_url"]}}
            }

        config_manager.save_user_config(user_config)


def get_saved_config_info():
    from user_config import get_user_config_manager

    config_manager = get_user_config_manager()
    if not config_manager:
        return None
    user_config = config_manager.get_user_config()
    model_config = user_config.get("model_config", {})
    defaults = model_config.get("defaults", {})
    return {
        "model_name": defaults.get("llm_model", "Not configured"),
        "search_name": get_search_display_name(defaults.get("search_provider", "duckduckgo")),
    }


def get_search_display_name(search_provider):
    search_names = {"duckduckgo": "DuckDuckGo", "searxng": "SearXNG"}
    return search_names.get(search_provider, search_provider)


def get_config_parameters():
    """Return the active model/search config, preferring the shared
    Streamlit-Secrets config (public deployment) over any per-user
    config file (local/manual wizard flow)."""
    if has_shared_secrets_config():
        return get_shared_config_parameters()

    from user_config import get_user_config_manager

    config_manager = get_user_config_manager()
    if not config_manager:
        return None
    user_config = config_manager.get_user_config()
    model_config = user_config.get("model_config", {})
    if not model_config:
        return None

    providers = model_config.get("providers", {})
    defaults = model_config.get("defaults", {})
    provider_key = defaults.get("llm_provider")
    if not provider_key or provider_key not in providers:
        return None

    provider_config = providers[provider_key]
    embedding_provider_key = defaults.get("embedding_provider", provider_key)
    embedding_provider_config = providers.get(embedding_provider_key, provider_config)

    return {
        "provider_key": provider_key,
        "api_base": provider_config.get("base_url"),
        "api_key": provider_config.get("api_key", "EMPTY"),
        "chat_model": defaults.get("llm_model"),
        "embedding_model": defaults.get("embedding_model"),
        "embedding_api_base": embedding_provider_config.get("base_url"),
        "embedding_api_key": embedding_provider_config.get("api_key", "lm-studio"),
        "search_provider": defaults.get("search_provider", "duckduckgo"),
        "selected_language": defaults.get("output_language", "en"),
        "provider_config": provider_config,
    }


def reset_user_config():
    from user_config import get_user_config_manager

    config_manager = get_user_config_manager()
    if config_manager:
        config_manager.reset_config()


def estimate_confidence(verdict: str, evidence_count: int) -> int:
    """Fallback confidence heuristic, used only if fact_checker doesn't
    return a numeric confidence itself. Feel free to replace this with a
    real score once evaluate_claim() returns one (e.g. based on how many
    sources agree with the verdict)."""
    base = {"TRUE": 82, "FALSE": 78, "PARTIALLY TRUE": 55, "UNVERIFIABLE": 35}
    score = base.get((verdict or "").upper(), 50)
    score += min(evidence_count * 2, 10)
    return max(5, min(99, score))


# ===========================================================================
# ---- HOME PAGE ----
# Rebuilt to match the approved HTML mockup exactly:
#   - hero copy in sentence case ("Think twice." / "Verify everything.")
#   - claim textarea
#   - three quick-action pills underneath (Try a headline / Paste a URL /
#     Check a viral claim) — clicking one fills the box with a sample so
#     first-time visitors can see how the checker behaves immediately
#   - a right-hugging Clear / Check Now button pair (not full-width),
#     matching the mockup's flex-end action row
# ===========================================================================

SAMPLE_HEADLINE = "NASA confirms discovery of a second moon orbiting Earth"
SAMPLE_URL = "https://example-news-site.com/breaking-story"
SAMPLE_VIRAL_CLAIM = "Drinking bleach cures COVID-19"


def _clear_claim_input():
    """FIX: setting st.session_state.claim_input_box directly inside the
    button's if-block (after st.text_area(key="claim_input_box") has
    already run earlier in the same script) is exactly what Streamlit's
    'cannot be modified after the widget ... is instantiated' error is
    about — the widget already exists for this run by the time the
    button's code executes. The supported way to do this is an on_click
    callback: Streamlit runs callbacks *before* the script re-executes
    and widgets are recreated, so mutating session_state here is safe.
    """
    st.session_state.claim_input_box = ""


def _render_hero(placeholder, status_text: str = None):
    """Renders the hero heading + either the static tagline (idle state)
    or an animated status line (while a fact-check is running) inside
    the SAME placeholder. This is what makes the tagline morph into the
    progress indicator in place, instead of separate status boxes
    appearing below the button.
    """
    if status_text is None:
        body_html = (
            '<p class="fnd-hero-tagline">'
            "Paste any news, headline, or claim — our AI cross-checks it "
            "against live web sources and tells you what's real."
            "</p>"
        )
    else:
        body_html = (
            '<div class="fnd-status-line">'
            '<span class="fnd-spinner"></span>'
            f'<span class="fnd-status-text">{status_text}</span>'
            "</div>"
        )

    placeholder.markdown(
        f"""
        <div class="fnd-hero-minimal">
            <h1><span class="muted-line">Think twice.</span><br/><span class="accent">Verify everything.</span></h1>
            {body_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_page():
    with st.container(key="home_center_wrap"):
        hero_placeholder = st.empty()
        _render_hero(hero_placeholder)

        with st.container(key="claim_shell"):
            claim_input = st.text_area(
                "Claim input",
                placeholder="Paste a headline, article, or claim...",
                height=150,
                label_visibility="collapsed",
                key="claim_input_box",
            )

            # FIX: these were st.button()s that filled the textarea with a
            # sample on click via st.session_state.claim_input_box = ... —
            # but by the time they're clicked, the claim_input_box widget
            # has already been instantiated above, so Streamlit throws
            # StreamlitAPIException ("cannot be modified after the widget
            # ... is instantiated"). Rather than working around that with
            # extra rerun/key-juggling, these are now plain static pills:
            # no st.button, no click handler, no hover glow — just a
            # decorative row of labels, so there's nothing left to throw.
            # FIX: on phones, the full labels ("Try a headline", "Check
            # a viral claim") don't fit in a single line at any width
            # small enough to keep three pills side-by-side, so they
            # kept wrapping into lopsided two-line splits no matter how
            # the wrap point was tuned. Each pill now carries BOTH a
            # full label (.fnd-pill-full, shown on desktop) and a short
            # one-word/two-word label (.fnd-pill-short, shown on mobile
            # instead via a CSS display swap in styles.py) — so phones
            # get a short label that comfortably fits on one line, and
            # desktop is completely unchanged.
            st.markdown(
                """
                <div class="fnd-static-pill-row">
                    <div class="fnd-static-pill">📰&nbsp;&nbsp;<span class="fnd-pill-full">Try a headline</span><span class="fnd-pill-short">Headline</span></div>
                    <div class="fnd-static-pill">🔗&nbsp;&nbsp;<span class="fnd-pill-full">Paste a URL</span><span class="fnd-pill-short">URL</span></div>
                    <div class="fnd-static-pill">🌐&nbsp;&nbsp;<span class="fnd-pill-full">Check a viral claim</span><span class="fnd-pill-short">Viral claim</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # FIX: was a 1.1rem spacer, adding unnecessary extra vertical
            # length to the page on top of the other spacing fixes in
            # styles.py. Tightened to 0.5rem — still a clear visual gap
            # between the pills and the Clear/Check Now row, just not a
            # page-lengthening one.
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            # Action row — a wide spacer column pushes Clear + Check Now
            # to the right edge, matching the mockup's flex-end row
            # instead of stretching them full-width across the card.
            # Wrapped in a keyed container ("home_action_row") so
            # styles.py can force this specific row to stay side-by-side
            # (Clear left / Check Now right) on mobile instead of
            # Streamlit's default column-stacking below 640px.
            with st.container(key="home_action_row"):
                spacer, c1, c2 = st.columns([3, 1, 1.3])
                with c1:
                    st.button("Clear", use_container_width=True, key="clear_home_btn", on_click=_clear_claim_input)
                with c2:
                    check_clicked = st.button("Check Now →", type="primary", use_container_width=True, key="check_now_btn")

            final_claim = (claim_input or "").strip()

            if check_clicked:
                if final_claim:
                    run_fact_check(final_claim, hero_placeholder)
                else:
                    st.warning("Please paste a headline or claim first.")

        # FIX: was a 1rem spacer before the disclaimer note — trimmed to
        # 0.5rem as part of the overall vertical tightening.
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.info(
            "This is a student project demo using free-tier AI models. "
            "Please verify important claims through official sources."
        )


def run_fact_check(user_input: str, hero_placeholder):
    config_params = get_config_parameters()
    if not config_params:
        st.error("Failed to get configuration, please reconfigure")
        if st.button("Reconfigure"):
            reset_user_config()
            st.rerun()
        return

    api_base = config_params["api_base"]
    api_key = config_params["api_key"]
    chat_model = config_params["chat_model"]
    embedding_model = config_params["embedding_model"]
    search_provider = config_params["search_provider"]
    selected_language = config_params["selected_language"]
    embedding_api_base = config_params["embedding_api_base"]
    embedding_api_key = config_params["embedding_api_key"]

    if not api_base or not chat_model or not embedding_model:
        st.error("Configuration incomplete, please reconfigure the model/embedding provider")
        st.stop()

    search_config = model_manager.get_search_provider_config(search_provider)
    searxng_url = search_config.get("base_url", "http://localhost:8090")

    # FIX: the three st.spinner(...) boxes below (each with its own
    # standalone message) were replaced by a single morphing status line
    # in the hero area — the tagline text fades into whichever of these
    # three messages is currently active, then fades back to the tagline
    # once the result is ready (page navigates to "results" via
    # st.rerun() below, so the hero unmounts naturally after that).
    _render_hero(hero_placeholder, "Extracting the core claim...")
    fact_checker = FactChecker(
        api_base=api_base,
        api_key=api_key,
        model=chat_model,
        temperature=0.0,
        max_tokens=1000,
        embedding_base_url=embedding_api_base,
        embedding_model=embedding_model,
        embedding_api_key=embedding_api_key,
        search_engine=search_provider,
        searxng_url=searxng_url,
        output_language=selected_language,
        search_config=search_config,
    )
    claim = fact_checker.extract_claim(user_input)

    # FIX: if the input was a bare URL that fact_checker couldn't
    # fetch/parse (bot-blocked, dead link, homepage with no single
    # article, etc.), extract_claim() returns a plain explanatory
    # message rather than a real claim. Stop here and show it as a
    # warning instead of continuing to search/evaluate that message
    # text as if it were the actual claim.
    if claim.startswith("Could not extract article content from this URL") or claim.startswith(
        "This looks like a social media post"
    ):
        _render_hero(hero_placeholder)
        st.warning(claim)
        return

    if "claim:" in claim.lower():
        claim = claim.split("claim:")[-1].strip()

    _render_hero(hero_placeholder, "Searching for relevant evidence...")
    search_max_results = search_config.get("max_results", 5)
    evidence_docs = fact_checker.search_evidence(claim, search_max_results)

    base_results = search_config.get("max_results", 5)
    expansion_factor = (
        model_manager.get_current_config().get("defaults", {}).get("evidence_display_multiplier", 2.0)
    )
    max_evidence_display = int(base_results * 1 * expansion_factor)
    evidence_chunks = fact_checker.get_evidence_chunks(evidence_docs, claim, top_k=max_evidence_display)

    evaluation_evidence = evidence_chunks[:-1] if len(evidence_chunks) > 1 else evidence_chunks

    _render_hero(hero_placeholder, "Evaluating claim accuracy...")
    evaluation = fact_checker.evaluate_claim(claim, evaluation_evidence)

    verdict = evaluation["verdict"]
    confidence = evaluation.get("confidence") or estimate_confidence(verdict, len(evaluation_evidence))

    # Save to DB
    db_utils.save_fact_check(
        st.session_state.user_id, user_input, claim, verdict,
        evaluation["reasoning"], evaluation_evidence,
    )

    st.session_state.last_result = {
        "claim": claim,
        "verdict": verdict,
        "confidence": confidence,
        "reasoning": evaluation["reasoning"],
        "evidence": evaluation_evidence,
        "checked_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }
    st.session_state.page = "results"
    st.rerun()


# ===========================================================================
# ---- RESULTS PAGE ----
# ===========================================================================

def render_results_page():
    result = st.session_state.get("last_result")

    if st.button("← Back to Home", key="back_to_home_btn"):
        st.session_state.page = "home"
        st.rerun()

    if not result:
        st.info("No fact-check result yet. Go to Home and paste a claim to check.")
        return

    meta = verdict_meta(result["verdict"])

    # FIX (mobile): wrapped in a keyed container ("results_top_row") so
    # styles.py can target this specific columns row and force it to
    # stay side-by-side (instead of Streamlit's default stacking) below
    # the 640px breakpoint, with both cards shrunk to fit two-up.
    with st.container(key="results_top_row"):
        left, right = st.columns([1.4, 1], vertical_alignment="center")
        with left:
            render_verdict_card(result["verdict"], result["confidence"])
        with right:
            render_confidence_ring(
                result["confidence"],
                checked_at=result["checked_at"],
                sources_found=len(result["evidence"]),
                color=meta["color"],
            )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    render_reasoning_card(result["reasoning"])
    render_evidence_card(result["evidence"])

    with st.expander("Extracted claim"):
        st.write(result["claim"])

    st.divider()
    st.subheader("Export report")
    try:
        history_item_for_pdf = {
            "original_text": result["claim"],
            "claim": result["claim"],
            "verdict": result["verdict"],
            "reasoning": result["reasoning"],
            "evidence": result["evidence"],
        }
        pdf_data = generate_fact_check_pdf(history_item_for_pdf)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fact_check_report_{current_time}.pdf"
        # FIX: a raw HTML <a href="data:application/pdf;base64,..."> tag
        # doesn't reliably trigger a download on Streamlit Community
        # Cloud — deployed apps run inside a sandboxed iframe that blocks
        # data-URI download clicks, so the click silently no-ops (browser
        # shows a local file:/// path that was never actually written).
        # st.download_button is Streamlit's native download mechanism,
        # built specifically to work inside that sandboxed iframe.
        st.download_button(
            label="📄 Export as PDF",
            data=pdf_data,
            file_name=filename,
            mime="application/pdf",
            key="download_pdf_results",
        )
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        st.info("Please make sure the ReportLab library is installed: pip install reportlab")


# ===========================================================================
# ---- HISTORY PAGE ----
# ===========================================================================

def render_history_page():
    if st.button("← Back to Home", key="back_to_home_btn"):
        st.session_state.page = "home"
        st.rerun()

    st.markdown("## 🕒 History")
    st.caption("Your past fact-checks")

    items_per_page = 8
    total_items = db_utils.count_user_history(st.session_state.user_id)

    if "history_page" not in st.session_state:
        st.session_state.history_page = 0

    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

    history_items = db_utils.get_user_history(
        st.session_state.user_id,
        limit=items_per_page,
        offset=st.session_state.history_page * items_per_page,
    )

    if not history_items:
        st.info("You don't have any history yet. Go check a claim on the Home page!")
        return

    render_history_header()
    for item in history_items:
        evidence = item.get("evidence") or []
        confidence = estimate_confidence(item["verdict"], len(evidence))
        render_history_row(
            claim_text=item["claim"],
            verdict=item["verdict"],
            confidence=confidence,
            sources=len(evidence),
            checked_at=item["created_at"],
        )
        if st.button("View details", key=f"view_{item['id']}"):
            st.session_state.current_history_id = item["id"]
            st.session_state.page = "details"
            st.rerun()

    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            if st.button("← Previous", disabled=(st.session_state.history_page == 0)):
                st.session_state.history_page -= 1
                st.rerun()
        with col2:
            st.write(f"Page {st.session_state.history_page + 1} of {total_pages}")
        with col3:
            if st.button("Next →", disabled=(st.session_state.history_page >= total_pages - 1)):
                st.session_state.history_page += 1
                st.rerun()


def render_history_detail_page():
    if st.session_state.current_history_id is None:
        st.error("History record not found")
        if st.button("Back to history list"):
            st.session_state.page = "history"
            st.rerun()
        return

    history_item = db_utils.get_history_by_id(st.session_state.current_history_id)
    if not history_item:
        st.error("History record not found")
        if st.button("Back to history list"):
            st.session_state.page = "history"
            st.rerun()
        return

    if st.button("← Back to history list"):
        st.session_state.page = "history"
        st.rerun()

    evidence = history_item.get("evidence") or []
    confidence = estimate_confidence(history_item["verdict"], len(evidence))
    meta = verdict_meta(history_item["verdict"])

    # FIX (mobile): same keyed-container fix as render_results_page() —
    # keeps the verdict card + confidence ring side-by-side on phones
    # instead of Streamlit's default column-stacking below 640px.
    with st.container(key="results_top_row"):
        left, right = st.columns([1.4, 1], vertical_alignment="center")
        with left:
            render_verdict_card(history_item["verdict"], confidence)
        with right:
            render_confidence_ring(
                confidence,
                checked_at=history_item["created_at"],
                sources_found=len(evidence),
                color=meta["color"],
            )

    render_reasoning_card(history_item["reasoning"])
    render_evidence_card(evidence)

    with st.expander("Original text & extracted claim"):
        st.markdown("**Original text**")
        st.write(history_item["original_text"])
        st.markdown("**Extracted claim**")
        st.write(history_item["claim"])

    st.divider()
    st.subheader("Export report")
    try:
        pdf_data = generate_fact_check_pdf(history_item)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fact_check_report_{current_time}.pdf"
        # FIX: same iframe/data-URI issue as the results page — use
        # Streamlit's native download_button instead of a raw HTML anchor.
        st.download_button(
            label="📄 Export as PDF",
            data=pdf_data,
            file_name=filename,
            mime="application/pdf",
            key="download_pdf_history",
        )
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        st.info("Please make sure the ReportLab library is installed: pip install reportlab")


# ===========================================================================
# ---- GLOBAL STATE + ROUTING ----
# ===========================================================================

if "page" not in st.session_state:
    st.session_state.page = "home"
if "current_history_id" not in st.session_state:
    st.session_state.current_history_id = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# SECURITY FIX: this used to call auth.check_saved_login(), which read a
# login token from a file on disk (data/.login_cache.json). On Streamlit
# Community Cloud every visitor shares the same server filesystem, so
# that file was effectively global — whoever logged in last with
# "Remember me" got their session handed to every new visitor. That
# function has been removed from auth.py entirely; login state now lives
# only in st.session_state (which Streamlit keeps separate per browser
# session on its own), initialized here as plain None defaults.
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None

is_authenticated = auth.show_auth_ui()

if is_authenticated:
    if not check_user_config_status():
        show_initial_config_wizard()
    else:
        # Sidebar removed entirely. Instead: a slim header (brand mark on
        # the left, circular account avatar on the right). The avatar
        # opens a small popover with History / Logout — no persistent nav
        # rail taking up screen space anymore.
        nav_click = None
        if st.session_state.page == "home":
            nav_click = render_header(username=st.session_state.get("username", "User"))

        if nav_click == "history":
            st.session_state.page = "history"
            st.rerun()
        elif nav_click == "logout":
            auth.logout()
            st.rerun()

        if st.session_state.page == "home":
            render_home_page()
        elif st.session_state.page == "results":
            render_results_page()
        elif st.session_state.page == "history":
            render_history_page()
        elif st.session_state.page == "details":
            render_history_detail_page()
