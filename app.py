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

from reportlab.pdfgen import canvas
from io import BytesIO


def generate_test_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "This is a test PDF")
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# Initialize database
db_utils.init_db()

# Page config
st.set_page_config(
    page_title="AI Fake News Detector",
    page_icon="🔍",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)


def check_user_config_status():
    """Check user config status, determine if config wizard needs to be shown"""
    from user_config import get_user_config_manager

    config_manager = get_user_config_manager()
    if not config_manager:
        return False  # Not logged in, no need to check config

    user_config = config_manager.get_user_config()

    # Check if basic config exists
    has_model_config = bool(user_config.get("model_config", {}))
    has_working_config = "config_completed" in user_config

    return has_model_config and has_working_config

def show_initial_config_wizard():
    """Show initial config wizard"""
    st.title("🚀 Welcome to the AI Fake News Detector")
    st.markdown("""
    Before you start, please complete a one-time setup.
    Once configured, you can use the system directly.
    """)

    st.divider()

    # Manual configuration
    st.subheader("⚙️ Setup")

    # Simplified config options
    config_option = st.radio(
        "Select AI service type",
        options=[
            "⚡ Groq + Gemini (Free Cloud - Recommended)",
            "💻 LM Studio (Local GUI)",
            "☁️ OpenAI (Cloud service)",
            "🔧 Custom configuration"
        ],
        help="Select the AI service type you want to use"
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
            "🔑 Groq API Key",
            type="password",
            help="Get this free at console.groq.com",
            key="groq_api_key_input",
        )
        gemini_api_key = st.text_input(
            "🔑 Gemini API Key",
            type="password",
            help="Get this free at aistudio.google.com",
            key="gemini_api_key_input",
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

            # Add search engine selection
            st.subheader("🔍 Select search engine")
            search_options = {
                "🦆 DuckDuckGo (Recommended)": "duckduckgo",
                "🔍 SearXNG (Local)": "searxng"
            }

            selected_search = st.radio(
                "Search engine",
                options=list(search_options.keys()),
                help="DuckDuckGo needs no setup, SearXNG requires local deployment",
                horizontal=True,
                key="groqgemini_search"
            )

            search_provider = search_options[selected_search]
            searxng_url = None

            if search_provider == "searxng":
                searxng_url = st.text_input(
                    "🌐 SearXNG service address",
                    value="http://localhost:8090",
                    help="Enter your SearXNG instance address",
                    placeholder="http://localhost:8090",
                    key="groqgemini_searxng_url"
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
                "search_provider": search_provider
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
                # Add search engine selection
                st.subheader("🔍 Select search engine")
                search_options = {
                    "🦆 DuckDuckGo (Recommended)": "duckduckgo",
                    "🔍 SearXNG (Local)": "searxng"
                }

                selected_search = st.radio(
                    "Search engine",
                    options=list(search_options.keys()),
                    help="DuckDuckGo needs no setup, SearXNG requires local deployment",
                    horizontal=True,
                    key="lmstudio_search"
                )

                search_provider = search_options[selected_search]
                searxng_url = None

                # If SearXNG selected, let user configure address
                if search_provider == "searxng":
                    searxng_url = st.text_input(
                        "🌐 SearXNG service address",
                        value="http://localhost:8090",
                        help="Enter your SearXNG instance address",
                        placeholder="http://localhost:8090",
                        key="lmstudio_searxng_url"
                    )

                manual_config = {
                    "name": "LM Studio",
                    "provider": "lmstudio",
                    "url": "http://localhost:1234/v1",
                    "chat_model": chat_model,
                    "embedding_model": embedding_model,
                    "search_provider": search_provider
                }

                if searxng_url:
                    manual_config["searxng_url"] = searxng_url
        else:
            st.warning("⚠️ Could not connect to LM Studio service, please make sure LM Studio is running")

    elif "☁️ OpenAI" in config_option:
        st.subheader("☁️ OpenAI configuration")
        api_key = st.text_input("🔑 OpenAI API Key", type="password", help="Enter your OpenAI API key")
        if api_key:
            # Predefined OpenAI models (API key needed to fetch list)
            openai_models = {
                "💬 Chat models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "🧠 Embedding models": ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"]
            }

            col1, col2 = st.columns(2)
            with col1:
                chat_model = st.selectbox("💬 Chat model", options=openai_models["💬 Chat models"])
            with col2:
                embedding_model = st.selectbox("🧠 Embedding model", options=openai_models["🧠 Embedding models"])

            # Add search engine selection
            st.subheader("🔍 Select search engine")
            search_options = {
                "🦆 DuckDuckGo (Recommended)": "duckduckgo",
                "🔍 SearXNG (Local)": "searxng"
            }

            selected_search = st.radio(
                "Search engine",
                options=list(search_options.keys()),
                help="DuckDuckGo needs no setup, SearXNG requires local deployment",
                horizontal=True,
                key="openai_search"
            )

            search_provider = search_options[selected_search]
            searxng_url = None

            # If SearXNG selected, let user configure address
            if search_provider == "searxng":
                searxng_url = st.text_input(
                    "🌐 SearXNG service address",
                    value="http://localhost:8090",
                    help="Enter your SearXNG instance address",
                    placeholder="http://localhost:8090",
                    key="openai_searxng_url"
                )

            manual_config = {
                "name": "OpenAI",
                "provider": "openai",
                "url": "https://api.openai.com/v1",
                "api_key": api_key,
                "chat_model": chat_model,
                "embedding_model": embedding_model,
                "search_provider": search_provider
            }

            if searxng_url:
                manual_config["searxng_url"] = searxng_url

    elif "🔧 Custom" in config_option:
        with st.expander("🚀 Custom configuration", expanded=True):
            url = st.text_input("🌐 API address", placeholder="http://localhost:8000/v1")

            if url:
                # Try to fetch model list
                models = get_models_for_provider("custom", url.rstrip('/v1'))

                if models:
                    st.success(f"✅ Detected {len(models)} available models")
                    chat_models, embedding_models = categorize_models(models)

                    col1, col2 = st.columns(2)
                    with col1:
                        chat_model = st.selectbox("💬 Chat model", options=chat_models if chat_models else models)
                    with col2:
                        embedding_model = st.selectbox("🧠 Embedding model", options=embedding_models if embedding_models else models)

                    if chat_model and embedding_model:
                        # Add search engine selection
                        st.subheader("🔍 Select search engine")
                        search_options = {
                            "🦆 DuckDuckGo (Recommended)": "duckduckgo",
                            "🔍 SearXNG (Local)": "searxng"
                        }

                        selected_search = st.radio(
                            "Search engine",
                            options=list(search_options.keys()),
                            help="DuckDuckGo needs no setup, SearXNG requires local deployment",
                            horizontal=True,
                            key="custom_search_1"
                        )

                        search_provider = search_options[selected_search]
                        searxng_url = None

                        # If SearXNG selected, let user configure address
                        if search_provider == "searxng":
                            searxng_url = st.text_input(
                                "🌐 SearXNG service address",
                                value="http://localhost:8090",
                                help="Enter your SearXNG instance address",
                                placeholder="http://localhost:8090",
                                key="custom_searxng_url_1"
                            )

                        manual_config = {
                            "name": "Custom configuration",
                            "provider": "custom",
                            "url": url,
                            "chat_model": chat_model,
                            "embedding_model": embedding_model,
                            "search_provider": search_provider
                        }

                        if searxng_url:
                            manual_config["searxng_url"] = searxng_url
                else:
                    st.warning("⚠️ Could not fetch model list from this address, please check the address")
                    # Manually enter model names
                    st.info("📝 Please manually enter model names")
                    col1, col2 = st.columns(2)
                    with col1:
                        chat_model = st.text_input("💬 Chat model", placeholder="e.g. llama2")
                    with col2:
                        embedding_model = st.text_input("🧠 Embedding model", placeholder="e.g. nomic-embed-text")

                    if chat_model and embedding_model:
                        # Add search engine selection
                        st.subheader("🔍 Select search engine")
                        search_options = {
                            "🦆 DuckDuckGo (Recommended)": "duckduckgo",
                            "🔍 SearXNG (Local)": "searxng"
                        }

                        selected_search = st.radio(
                            "Search engine",
                            options=list(search_options.keys()),
                            help="DuckDuckGo needs no setup, SearXNG requires local deployment",
                            horizontal=True,
                            key="custom_search_2"
                        )

                        search_provider = search_options[selected_search]
                        searxng_url = None

                        # If SearXNG selected, let user configure address
                        if search_provider == "searxng":
                            searxng_url = st.text_input(
                                "🌐 SearXNG service address",
                                value="http://localhost:8090",
                                help="Enter your SearXNG instance address",
                                placeholder="http://localhost:8090",
                                key="custom_searxng_url_2"
                            )

                        manual_config = {
                            "name": "Custom configuration",
                            "provider": "custom",
                            "url": url,
                            "chat_model": chat_model,
                            "embedding_model": embedding_model,
                            "search_provider": search_provider
                        }

                        if searxng_url:
                            manual_config["searxng_url"] = searxng_url

    # Test configuration
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
    """Categorize models into chat models and embedding models"""
    chat_models = []
    embedding_models = []

    for model in models:
        model_lower = model.lower()
        # Determine if it's an embedding model
        if any(keyword in model_lower for keyword in ['embed', 'embedding', 'nomic', 'bge', 'gte']):
            embedding_models.append(model)
        else:
            chat_models.append(model)

    return chat_models, embedding_models

def get_models_for_provider(provider_type, url):
    """Fetch model list for a given provider"""
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
    except:
        return []

def test_searxng_connection(searxng_url="http://localhost:8090"):
    """Test SearXNG connection"""
    try:
        import requests
        # Make sure URL format is correct
        if not searxng_url.startswith('http'):
            searxng_url = f"http://{searxng_url}"

        # Test search endpoint
        response = requests.get(f"{searxng_url}/search",
                               params={"q": "test", "format": "json"},
                               timeout=3)
        return response.status_code == 200
    except:
        return False

def test_config_connection(config):
    """Test configuration connection"""
    try:
        import requests
        headers = {}
        if config.get("api_key"):
            headers["Authorization"] = f"Bearer {config['api_key']}"
        response = requests.get(f"{config['url']}/models", headers=headers, timeout=5)
        return response.status_code == 200
    except:
        return False

def save_manual_config(config):
    """Save manual configuration"""
    from user_config import get_user_config_manager

    config_manager = get_user_config_manager()
    if config_manager:
        providers = {
            config["provider"]: {
                "base_url": config["url"]
            }
        }
        if "api_key" in config:
            providers[config["provider"]]["api_key"] = config["api_key"]

        # Support a separate embedding provider (e.g. Groq for chat + Gemini for embeddings)
        embedding_provider_key = config.get("embedding_provider", config["provider"])
        if embedding_provider_key not in providers:
            providers[embedding_provider_key] = {
                "base_url": config.get("embedding_url", config["url"])
            }
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
                    "output_language": "en"
                }
            },
            "config_completed": True,
            "config_source": "manual"
        }

        # If custom SearXNG address exists, save it to search config
        if config.get("searxng_url"):
            user_config["search_config"] = {
                "search_providers": {
                    "searxng": {
                        "base_url": config["searxng_url"]
                    }
                }
            }

        config_manager.save_user_config(user_config)

def get_saved_config_info():
    """Get saved config info for display"""
    from user_config import get_user_config_manager

    config_manager = get_user_config_manager()
    if not config_manager:
        return None

    user_config = config_manager.get_user_config()
    model_config = user_config.get("model_config", {})
    defaults = model_config.get("defaults", {})

    return {
        "model_name": defaults.get("llm_model", "Not configured"),
        "search_name": get_search_display_name(defaults.get("search_provider", "duckduckgo"))
    }

def get_search_display_name(search_provider):
    """Get search engine display name"""
    search_names = {
        "duckduckgo": "DuckDuckGo",
        "searxng": "SearXNG"
    }
    return search_names.get(search_provider, search_provider)

def get_config_parameters():
    """Get parameters from saved configuration"""
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

    # Embedding provider can be different from the chat provider
    # (e.g. Groq for chat + Gemini for embeddings)
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
        "provider_config": provider_config
    }

def reset_user_config():
    """Reset user configuration"""
    from user_config import get_user_config_manager

    config_manager = get_user_config_manager()
    if config_manager:
        config_manager.reset_config()

def show_simplified_fact_check_page():
    """Show simplified fact-check page - no complex config UI"""
    st.markdown(
        """
    This app uses AI models to verify the accuracy of statements.
    Enter the news you want to check below, and the system will retrieve web evidence to fact-check it.
    """
    )

    st.info(
        "ℹ️ This is a student project demo using free-tier AI models. "
        "Please verify important claims through official sources."
    )

    # Simplified sidebar - only shows status and basic info
    with st.sidebar:
        st.header("📊 System status")

        # Get saved configuration
        config_info = get_saved_config_info()
        if config_info:
            st.success(f"✅ AI model: {config_info['model_name']}")
            st.success(f"✅ Search engine: {config_info['search_name']}")

        st.divider()

        # Quick settings - only shows what's necessary
        with st.expander("⚙️ Quick settings"):
            temperature = st.slider(
                "Creativity",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1,
                help="Lower values make responses more deterministic, higher values make them more creative",
            )
            language = st.selectbox(
                "Output language",
                options=["Auto-detect", "Chinese", "English"],
                help="Select the language for AI responses"
            )

        st.divider()

        # Config management link
        if st.button("🔧 Reconfigure", help="Reconfigure the AI model and service"):
            reset_user_config()
            st.rerun()

        st.divider()
        st.markdown("### About")
        st.markdown("Fake News Detector:")
        st.markdown("1. Extracts the core claim from the news")
        st.markdown("2. Searches the web for evidence")
        st.markdown("3. Ranks evidence by relevance using embeddings")
        st.markdown("4. Provides a conclusion based on the evidence")
        st.markdown("Built with Streamlit, Groq, and Gemini ❤️")

    # Use saved configuration to get parameters
    config_params = get_config_parameters()
    if not config_params:
        st.error("Failed to get configuration, please reconfigure")
        if st.button("Reconfigure"):
            reset_user_config()
            st.rerun()
        return

    # The logic below stays the same, just uses saved config parameters
    # Initialize session state to store chat history if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Main input area
    user_input = st.chat_input("Enter the news you want to fact-check below...")

    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Show user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Create assistant message container for streaming output
        assistant_message = st.chat_message("assistant")

        # Create empty placeholder components for step-by-step updates
        claim_placeholder = assistant_message.empty()
        evidence_placeholder = assistant_message.empty()
        verdict_placeholder = assistant_message.empty()

        # Check if model config is valid - use saved configuration
        api_base = config_params["api_base"]
        api_key = config_params["api_key"]
        chat_model = config_params["chat_model"]
        embedding_model = config_params["embedding_model"]
        search_provider = config_params["search_provider"]
        selected_language = config_params["selected_language"]
        embedding_api_base = config_params["embedding_api_base"]
        embedding_api_key = config_params["embedding_api_key"]

        if not api_base or not chat_model:
            st.error("Configuration incomplete, please reconfigure the model provider")
            st.stop()

        if not embedding_model:
            st.error("Configuration incomplete, please reconfigure the embedding model")
            st.stop()

        # Get configuration
        search_config = model_manager.get_search_provider_config(search_provider)
        searxng_url = search_config.get("base_url", "http://localhost:8090")

        # Use sidebar settings to override defaults
        max_tokens = 1000  # fixed value, simplified config

        # Initialize FactChecker
        fact_checker = FactChecker(
            api_base=api_base,
            api_key=api_key,
            model=chat_model,
            temperature=temperature,
            max_tokens=max_tokens,
            embedding_base_url=embedding_api_base,
            embedding_model=embedding_model,
            embedding_api_key=embedding_api_key,
            search_engine=search_provider,
            searxng_url=searxng_url,
            output_language=selected_language,
            search_config=search_config,
        )

        # Step 1: Extract claim
        claim_placeholder.markdown("### 🔍 Extracting the core claim from the news...")
        claim = fact_checker.extract_claim(user_input)
        # Process claim string, extract content after "claim:"
        if "claim:" in claim.lower():
            claim = claim.split("claim:")[-1].strip()
        claim_placeholder.markdown(f"### 🔍 Core claim extracted\n\n{claim}")

        # Step 2: Search evidence
        evidence_placeholder.markdown("### 🌐 Searching for relevant evidence...")
        # Get number of search results from configuration
        search_max_results = search_config.get("max_results", 5)
        evidence_docs = fact_checker.search_evidence(claim, search_max_results)

        # Step 3: Get relevant evidence chunks
        evidence_placeholder.markdown("### 🌐 Analyzing evidence relevance...")
        # Dynamically calculate the number of evidence items to display: based on search config * language count * expansion factor
        base_results = search_config.get("max_results", 5)
        language_count = 1  # English only
        expansion_factor = (
            model_manager.get_current_config()
            .get("defaults", {})
            .get("evidence_display_multiplier", 2.0)
        )
        max_evidence_display = int(base_results * language_count * expansion_factor)

        evidence_chunks = fact_checker.get_evidence_chunks(
            evidence_docs, claim, top_k=max_evidence_display
        )

        # Show evidence results
        evidence_md = "### 🔗 Evidence sources\n\n"
        # Use the same evidence chunks for display and evaluation
        evaluation_evidence = (
            evidence_chunks[:-1] if len(evidence_chunks) > 1 else evidence_chunks
        )

        for j, chunk in enumerate(evaluation_evidence):
            evidence_md += f"**[{j+1}]:**\n"
            evidence_md += f"{chunk['text']}\n"
            evidence_md += f"Source: {chunk['source']}\n\n"

        evidence_placeholder.markdown(evidence_md)

        # Step 4: Evaluate claim
        verdict_placeholder.markdown("### ⚖️ Evaluating claim accuracy...")
        evaluation = fact_checker.evaluate_claim(claim, evaluation_evidence)

        # Determine verdict emoji
        verdict = evaluation["verdict"]
        if verdict.upper() == "TRUE":
            emoji = "✅"
            verdict_en = "True"
        elif verdict.upper() == "FALSE":
            emoji = "❌"
            verdict_en = "False"
        elif verdict.upper() == "PARTIALLY TRUE":
            emoji = "⚠️"
            verdict_en = "Partially True"
        else:
            emoji = "❓"
            verdict_en = "Unverifiable"

        # Show final verdict
        verdict_md = f"### {emoji} Verdict: {verdict_en}\n\n"
        verdict_md += f"### Reasoning\n\n{evaluation['reasoning']}\n\n"

        verdict_placeholder.markdown(verdict_md)

        # Combine full response content to save to chat history
        full_response = f"""
### 🔍 Core claim extracted from the news

{claim}

---

{evidence_md}

---

{verdict_md}
"""

        # Add assistant response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )

        # Save to database
        db_utils.save_fact_check(
            st.session_state.user_id,
            user_input,
            claim,
            verdict,
            evaluation["reasoning"],
            evaluation_evidence,
        )


def show_history_page():
    """Show history page"""
    st.header("History")
    st.write("Below are your past fact-checks")

    # Pagination controls
    items_per_page = 5
    total_items = db_utils.count_user_history(st.session_state.user_id)

    if "history_page" not in st.session_state:
        st.session_state.history_page = 0

    total_pages = (total_items + items_per_page - 1) // items_per_page

    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            if st.button("Previous page", disabled=(st.session_state.history_page == 0)):
                st.session_state.history_page -= 1
                st.rerun()
        with col2:
            st.write(f"Page {st.session_state.history_page + 1} of {total_pages}")
        with col3:
            if st.button(
                "Next page",
                disabled=(
                    st.session_state.history_page == total_pages - 1 or total_pages == 0
                ),
            ):
                st.session_state.history_page += 1
                st.rerun()

    # Get user history
    history_items = db_utils.get_user_history(
        st.session_state.user_id,
        limit=items_per_page,
        offset=st.session_state.history_page * items_per_page,
    )

    if not history_items:
        st.info("You don't have any history yet")
        return

    # Show history
    for item in history_items:
        with st.container():
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.subheader(
                    f"{item['claim'][:100]}..."
                    if len(item["claim"]) > 100
                    else item["claim"]
                )

                # Add verdict and timestamp
                verdict = item["verdict"].upper()
                if verdict == "TRUE":
                    emoji = "✅"
                    verdict_en = "True"
                elif verdict == "FALSE":
                    emoji = "❌"
                    verdict_en = "False"
                elif verdict == "PARTIALLY TRUE":
                    emoji = "⚠️"
                    verdict_en = "Partially True"
                else:
                    emoji = "❓"
                    verdict_en = "Unverifiable"

                st.write(f"Verdict: {emoji} {verdict_en}")
                st.write(f"Time: {item['created_at']}")

            with cols[1]:
                if st.button("View details", key=f"view_{item['id']}"):
                    st.session_state.current_history_id = item["id"]
                    st.session_state.page = "details"
                    st.rerun()

            st.divider()


def show_history_detail_page():
    """Show history detail page"""
    if st.session_state.current_history_id is None:
        st.error("History record not found")
        if st.button("Back to history list"):
            st.session_state.page = "history"
            st.rerun()
        return

    # Get history record details
    history_item = db_utils.get_history_by_id(st.session_state.current_history_id)

    if not history_item:
        st.error("History record not found")
        if st.button("Back to history list"):
            st.session_state.page = "history"
            st.rerun()
        return

    # Show back button
    if st.button("Back to history list"):
        st.session_state.page = "history"
        st.rerun()

    # Show history record details
    st.header("Fact-check details")

    st.subheader("Original text")
    st.write(history_item["original_text"])

    st.subheader("🔍 Extracted core claim")
    st.write(history_item["claim"])

    # Show evidence
    st.subheader("🔗 Evidence sources")
    for j, chunk in enumerate(history_item["evidence"]):
        st.markdown(f"**[{j+1}]:**")
        st.markdown(f"{chunk['text']}")
        st.markdown(f"Source: {chunk['source']}")
        if "similarity" in chunk and chunk["similarity"] is not None:
            st.markdown(f"Relevance: {chunk['similarity']:.2f}")
        st.markdown("---")

    # Show verdict
    verdict = history_item["verdict"].upper()
    if verdict == "TRUE":
        emoji = "✅"
        verdict_en = "True"
    elif verdict == "FALSE":
        emoji = "❌"
        verdict_en = "False"
    elif verdict == "PARTIALLY TRUE":
        emoji = "⚠️"
        verdict_en = "Partially True"
    else:
        emoji = "❓"
        verdict_en = "Unverifiable"

    st.subheader(f"{emoji} Verdict: {verdict_en}")

    st.subheader("Reasoning")
    st.write(history_item["reasoning"])

    # Show export options
    st.divider()
    st.subheader("Export report")

    # Create PDF export button
    try:
        pdf_data = generate_fact_check_pdf(history_item)

        # Generate filename
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fact_check_report_{current_time}.pdf"

        # Force download using HTML
        pdf_b64 = base64.b64encode(pdf_data).decode()
        href = f"""
        <a href="data:application/pdf;base64,{pdf_b64}" 
        download="{filename}" 
        target="_blank"
        style="display: inline-block; padding: 0.25em 0.5em; 
        background-color: #4CAF50; color: white; 
        text-decoration: none; border-radius: 4px;">
        Export as PDF
        </a>
        """
        st.markdown(href, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        st.info("Please make sure the ReportLab library is installed: pip install reportlab")


# Global state initialization
if "page" not in st.session_state:
    st.session_state.page = "home"  # possible values: 'home', 'history', 'details'

if "current_history_id" not in st.session_state:
    st.session_state.current_history_id = None

# Early check for persisted login state - before any UI is shown
if "user_id" not in st.session_state or st.session_state.user_id is None:
    saved_login = auth.check_saved_login()
    if saved_login:
        st.session_state.user_id = saved_login["user_id"]
        st.session_state.username = saved_login["username"]
        st.session_state.persisted_login = saved_login

# Check if logged in, otherwise show login screen
is_authenticated = auth.show_auth_ui()

if is_authenticated:
    # User is logged in, check if configuration is needed

    # Check user config status
    if not check_user_config_status():
        # Show config wizard
        show_initial_config_wizard()
    else:
        # Config complete, show main app
        # Show top navigation bar
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.title("AI Fake News Detector")
        with col2:
            if st.button("Home", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()
        with col3:
            if st.button("History", use_container_width=True):
                st.session_state.page = "history"
                st.rerun()
        with col4:
            if st.button("Log out", use_container_width=True):
                auth.logout()
                st.rerun()

        # Show current user info
        st.write(f"Logged in as: {st.session_state.username}")

        # Show different content based on current page
        if st.session_state.page == "home":
            # Home page - simplified fact-check interface
            show_simplified_fact_check_page()
        elif st.session_state.page == "history":
            # History page
            show_history_page()
        elif st.session_state.page == "details":
            # History detail page
            show_history_detail_page()
