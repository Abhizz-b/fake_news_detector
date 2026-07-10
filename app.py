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
# ---- CONFIG / SETUP LOGIC (unchanged from before) ----
# ===========================================================================

def check_user_config_status():
    """Check user config status, determine if config wizard needs to be shown"""
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
# Redesigned to be a minimal, centered "Think Twice. Verify Everything."
# layout: hero copy, a single-line headline/claim search bar, a larger
# drop-zone-style textarea for full articles/posts, and Clear / Check Now
# actions underneath. The old two-column layout (with "How it works" /
# "Powered by" side cards) is no longer used on the home page — those
# components still exist in components.py untouched, in case they're
# wanted elsewhere later.
# ===========================================================================

def render_home_page():
    spacer_l, center, spacer_r = st.columns([1, 2.4, 1])

    with center:
        with st.container(key="home_center_wrap"):
            st.markdown(
                """
                <div class="fnd-hero-minimal">
                    <h1>Think Twice.<br/><span class="accent">Verify Everything.</span></h1>
                    <p>Paste any news, headline, or claim and our AI will fact-check it using trusted sources.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            claim_input = st.text_area(
                "Claim input",
                placeholder="Paste a headline, article, or claim...",
                height=140,
                label_visibility="collapsed",
                key="claim_input_box",
            )

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            c1, c2 = st.columns([1, 1.5])
            with c1:
                if st.button("Clear", use_container_width=True, key="clear_home_btn"):
                    st.session_state.claim_input_box = ""
                    st.rerun()
            with c2:
                check_clicked = st.button("Check Now →", type="primary", use_container_width=True)

            final_claim = (claim_input or "").strip()

            if check_clicked:
                if final_claim:
                    run_fact_check(final_claim)
                else:
                    st.warning("Please paste a headline or claim first.")

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            st.info(
                "This is a student project demo using free-tier AI models. "
                "Please verify important claims through official sources."
            )


def run_fact_check(user_input: str):
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

    with st.spinner("Extracting the core claim..."):
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
        if "claim:" in claim.lower():
            claim = claim.split("claim:")[-1].strip()

    with st.spinner("Searching for relevant evidence..."):
        search_max_results = search_config.get("max_results", 5)
        evidence_docs = fact_checker.search_evidence(claim, search_max_results)

        base_results = search_config.get("max_results", 5)
        expansion_factor = (
            model_manager.get_current_config().get("defaults", {}).get("evidence_display_multiplier", 2.0)
        )
        max_evidence_display = int(base_results * 1 * expansion_factor)
        evidence_chunks = fact_checker.get_evidence_chunks(evidence_docs, claim, top_k=max_evidence_display)

    evaluation_evidence = evidence_chunks[:-1] if len(evidence_chunks) > 1 else evidence_chunks

    with st.spinner("Evaluating claim accuracy..."):
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

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()

    if not result:
        st.info("No fact-check result yet. Go to Home and paste a claim to check.")
        return

    meta = verdict_meta(result["verdict"])

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
        pdf_b64 = base64.b64encode(pdf_data).decode()
        href = f"""
        <a href="data:application/pdf;base64,{pdf_b64}"
        download="{filename}" target="_blank"
        style="display:inline-block;padding:0.5em 1em;
        background:linear-gradient(90deg,#8b5cf6,#7c3aed);color:white;
        text-decoration:none;border-radius:8px;font-weight:600;">
        📄 Export as PDF
        </a>
        """
        st.markdown(href, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        st.info("Please make sure the ReportLab library is installed: pip install reportlab")


# ===========================================================================
# ---- HISTORY PAGE ----
# ===========================================================================

def render_history_page():
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
        pdf_b64 = base64.b64encode(pdf_data).decode()
        href = f"""
        <a href="data:application/pdf;base64,{pdf_b64}"
        download="{filename}" target="_blank"
        style="display:inline-block;padding:0.5em 1em;
        background:linear-gradient(90deg,#8b5cf6,#7c3aed);color:white;
        text-decoration:none;border-radius:8px;font-weight:600;">
        📄 Export as PDF
        </a>
        """
        st.markdown(href, unsafe_allow_html=True)
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

if "user_id" not in st.session_state or st.session_state.user_id is None:
    saved_login = auth.check_saved_login()
    if saved_login:
        st.session_state.user_id = saved_login["user_id"]
        st.session_state.username = saved_login["username"]
        st.session_state.persisted_login = saved_login

is_authenticated = auth.show_auth_ui()

if is_authenticated:
    if not check_user_config_status():
        show_initial_config_wizard()
    else:
        # Sidebar removed entirely. Instead: a slim header (brand mark on
        # the left, circular account avatar on the right). The avatar
        # opens a small popover with History / Logout — no persistent nav
        # rail taking up screen space anymore.
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
