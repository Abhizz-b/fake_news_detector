import os
from datetime import datetime
from typing import Dict, List, Tuple, Any
import streamlit as st
from openai import OpenAI
import requests
from ddgs import DDGS
import numpy as np
import re


class FactChecker:
    def __init__(
        self,
        api_base: str,
        model: str,
        temperature: float,
        max_tokens: int,
        api_key: str = "EMPTY",
        embedding_base_url: str = None,
        embedding_model: str = "text-embedding-nomic-embed-text-v1.5",
        embedding_api_key: str = "lm-studio",
        search_engine: str = "searxng",
        searxng_url: str = None,
        output_language: str = "en",
        search_config: dict = None,
    ):
        """
        Initialize the fact checker with configuration parameters.

        Args:
            api_base: The base URL for the LLM API
            model: The model to use for fact checking
            temperature: Temperature parameter for LLM
            max_tokens: Maximum tokens for LLM response
            api_key: API key for the chat/LLM provider (e.g. Groq key). Defaults to
                "EMPTY" for local setups (Ollama/LM Studio) that don't need real auth.
            embedding_base_url: The base URL for embedding API
            embedding_model: The embedding model name
            embedding_api_key: API key for embedding service
            search_engine: Search engine to use ('duckduckgo' or 'searxng')
            searxng_url: Base URL for SearXNG instance
            output_language: Output language for claims/verdicts. Hardcoded default
                is "en" (English-only project requirement) instead of "auto", so the
                app never auto-switches to another language based on input text.
        """
        self.api_base = api_base
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.openai_api_key = api_key or "EMPTY"

        # Initialize the OpenAI client with local settings
        self.client = OpenAI(
            api_key=self.openai_api_key,
            base_url=self.api_base,
        )

        # Initialize embedding client for online API
        # If no address provided, use environment variable or default to localhost
        if embedding_base_url is None:
            import os
            embedding_base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:11435/v1")

        self.embedding_base_url = embedding_base_url
        self.embedding_model_name = embedding_model
        self.embedding_api_key = embedding_api_key

        # Create embedding client
        self.embedding_client = OpenAI(
            api_key=self.embedding_api_key,
            base_url=self.embedding_base_url,
        )

        # Set embedding_model to None as we're not using local model
        self.embedding_model = None

        # Search engine configuration
        self.search_engine = search_engine
        # If no SearXNG address provided, use environment variable or default to localhost
        if searxng_url is None:
            import os
            searxng_url = os.getenv("SEARXNG_BASE_URL", "http://localhost:8090")
        self.searxng_url = searxng_url

        # Language configuration - always English for this project.
        # NOTE: even if "auto" or some other value is passed in accidentally,
        # _get_language_prompts() below only has an "en" prompt set left,
        # so it will always fall back to English regardless.
        self.output_language = output_language

        # Search configuration
        self.search_config = search_config or {}

    def _detect_language(self, text: str) -> str:
        """
        Simple language detection based on character patterns.
        Kept only for internal bookkeeping (e.g. tagging evidence chunks) -
        no longer used to switch prompt/output language, since this project
        is English-only.
        """
        # Check for Chinese characters
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        # Check for Japanese characters
        japanese_chars = len(re.findall(r"[\u3040-\u309f\u30a0-\u30ff]", text))
        # Check for Korean characters
        korean_chars = len(re.findall(r"[\uac00-\ud7af]", text))

        total_chars = len(text)
        if total_chars == 0:
            return "en"

        # If more than 30% are CJK characters, detect specific language
        cjk_ratio = (chinese_chars + japanese_chars + korean_chars) / total_chars
        if cjk_ratio > 0.3:
            if chinese_chars > japanese_chars and chinese_chars > korean_chars:
                return "zh"
            elif japanese_chars > korean_chars:
                return "ja"
            elif korean_chars > 0:
                return "ko"

        return "en"

    # =======================================================================
    # URL HANDLING
    # -----------------------------------------------------------------------
    # FIX: the "🔗 Paste a URL" quick-action pill on the home page implies
    # users can paste a bare link and have it fact-checked. But previously,
    # extract_claim() just handed the raw URL *string* to the LLM as "the
    # text to extract a claim from". The model can't browse, so it had
    # nothing real to work with - it would hallucinate a meta-claim about
    # the URL itself (e.g. "this link lacks a specific claim that can be
    # verified"), and the app would then fact-check THAT instead of any
    # actual news content. Symptom seen: pasting a homepage/article URL
    # returned a verdict about "insufficient link text", evaluated against
    # random unrelated search results.
    #
    # Fix: detect when the input is a bare URL, fetch the page's HTML
    # ourselves, and extract its title + visible text so the LLM has real
    # article content to read - the same as if the user had copy-pasted
    # the headline/article text directly.
    # =======================================================================

    def _is_url(self, text: str) -> bool:
        """True if the entire input is just a single http(s) URL (as
        opposed to a headline/claim/article that happens to mention or
        end with a link)."""
        return bool(re.match(r"^\s*https?://\S+\s*$", text or ""))

    # Platforms that (a) block automated scraping via robots.txt, so we
    # can't reliably fetch the actual post content, and (b) mostly host
    # personal posts/experiences that no public news source will have
    # independently reported on - so even a perfect fetch wouldn't be
    # verifiable via web search evidence. Rather than silently producing
    # a misleading verdict (e.g. FALSE just because no public source
    # happens to mention someone's personal LinkedIn post), we detect
    # these upfront and explain the limitation clearly instead.
    _SOCIAL_MEDIA_DOMAINS = (
        "linkedin.com",
        "instagram.com",
        "twitter.com",
        "x.com",
        "facebook.com",
        "tiktok.com",
        "threads.net",
    )

    def _is_social_media_url(self, url: str) -> bool:
        try:
            from urllib.parse import urlparse

            netloc = urlparse(url.strip()).netloc.lower()
            return any(domain in netloc for domain in self._SOCIAL_MEDIA_DOMAINS)
        except Exception:
            return False

    def _fetch_url_content(self, url: str, max_chars: int = 4000) -> str:
        """Fetch a URL and extract its page title + readable text, so the
        claim-extraction step has actual article content instead of a
        bare link string. Returns an empty string if the page couldn't be
        fetched or parsed (dead link, blocks bots, not HTML, etc.) - the
        caller is responsible for handling that case."""
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                )
            }
            response = requests.get(url.strip(), headers=headers, timeout=10)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.lower() and content_type:
                return ""

            html = response.text

            title_match = re.search(
                r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
            )
            title = ""
            if title_match:
                title = re.sub(r"\s+", " ", title_match.group(1)).strip()

            # Drop script/style blocks entirely - their text isn't article
            # content and would just add noise (or JS code) to the claim.
            cleaned_html = re.sub(
                r"<(script|style|noscript)[^>]*>.*?</\1>",
                " ",
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )
            # Strip all remaining HTML tags
            text = re.sub(r"<[^>]+>", " ", cleaned_html)
            # Collapse repeated whitespace/newlines from the markup
            text = re.sub(r"\s+", " ", text).strip()

            combined = f"{title}. {text}" if title else text
            return combined[:max_chars]

        except Exception:
            return ""

    def _get_language_prompts(self, target_lang: str) -> dict:
        """
        Get localized prompts for the specified language.

        English-only project: only the "en" prompt set is defined. Any
        target_lang value (including "zh"/"ja"/"ko"/"auto") falls back to
        English via prompts.get(target_lang, prompts["en"]) below.
        """

        prompts = {
            "en": {
                "extract_claim": """
                You are a precise claim extraction assistant. Your ONLY job is to restate
                the exact factual claim made in the input text, exactly as it is asserted.

                CRITICAL RULES:
                - Do NOT judge, verify, fix, or negate the claim, even if you believe it is false.
                - Do NOT add corrections like "actually" or "but rather".
                - Simply restate what the text is asserting, as a single verifiable statement,
                  preserving the original meaning exactly (including if it is false).
                - You MUST write the restated claim in English, no matter what language the
                  input text is written in. Translate the claim into English while preserving
                  its exact meaning. Do NOT respond in Chinese, Japanese, Korean, or any other
                  language under any circumstances.

                output format:
                claim: <claim>
                """,
                "evaluate_claim": """
                You are a fact-checking assistant. Judge if the claim is true based on evidence.

                CRITICAL LANGUAGE RULE: You MUST write your entire response in English,
                regardless of the language used in the claim or in the evidence provided
                below. Even if the claim or evidence is in Chinese, Japanese, Korean, or
                any other language, your VERDICT and REASONING must be written only in
                English. Never switch to another language under any circumstances.

                Format required:
                VERDICT: TRUE/FALSE/PARTIALLY TRUE
                REASONING: Your reasoning process (in English only)
                """,
                "user_extract": "Extract the key factual claims from this text:",
                "user_evaluate": "CLAIM: {claim}\n\nEVIDENCE:\n{evidence}",
            },
        }

        return prompts.get(target_lang, prompts["en"])

    def _translate_claim(self, claim: str, target_languages: list) -> dict:
        """
        Translate claim to multiple languages for comprehensive search

        Args:
            claim: The claim to translate
            target_languages: List of target language codes ['en', 'zh', 'ja']

        Returns:
            Dictionary with language code as key and translated text as value
        """
        translations = {self._detect_language(claim): claim}  # Original language

        for target_lang in target_languages:
            if target_lang in translations:
                continue

            try:
                # Use LLM to translate the claim
                translation_prompt = {
                    "en": f"Please translate the following text to English, keep the meaning precise: {claim}",
                    "zh": f"请将以下文本翻译成中文，保持意思准确: {claim}",
                    "ja": f"以下のテキストを日本語に翻訳してください、意味を正確に保ってください: {claim}",
                    "ko": f"다음 텍스트를 한국어로 번역해주세요, 의미를 정확하게 유지하세요: {claim}"
                }

                if target_lang not in translation_prompt:
                    continue

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional translator. Translate accurately and concisely."},
                        {"role": "user", "content": translation_prompt[target_lang]}
                    ],
                    temperature=0.0,
                    max_tokens=200
                )

                translated_text = response.choices[0].message.content.strip()
                # Clean up any translation artifacts
                if translated_text and not translated_text.startswith("Translation:"):
                    translations[target_lang] = translated_text

            except Exception:
                # NOTE: previously surfaced via st.warning(...), which leaked
                # a translation-failure box into the UI. Silently skip this
                # language instead — the calling code already tolerates a
                # missing translation (falls back to the original claim).
                continue

        return translations

    def _optimize_language_diversity(self, ranked_chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        Optimize evidence selection to ensure language diversity while maintaining relevance.

        Args:
            ranked_chunks: Chunks ranked by similarity score
            top_k: Target number of chunks to return

        Returns:
            Optimized list of chunks with language diversity
        """
        if len(ranked_chunks) <= top_k:
            return ranked_chunks

        # Group chunks by search language (if available)
        language_groups = {}
        no_lang_chunks = []

        for chunk in ranked_chunks:
            # Check if we have search language metadata first
            search_lang = chunk.get('detected_language') or chunk.get('search_language')

            if not search_lang:
                # Fallback to content-based language detection
                text_content = chunk.get('text', '')
                if any('\u4e00' <= char <= '\u9fff' for char in text_content):  # Chinese
                    search_lang = 'zh'
                elif any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text_content):  # Japanese
                    search_lang = 'ja'
                elif text_content and all(ord(char) < 256 for char in text_content if char.isalpha()):  # Likely English
                    search_lang = 'en'

            if search_lang:
                if search_lang not in language_groups:
                    language_groups[search_lang] = []
                language_groups[search_lang].append(chunk)
            else:
                no_lang_chunks.append(chunk)

        # Select diverse evidence - aim for balanced representation
        selected_chunks = []
        remaining_slots = top_k

        # First, select top chunks from each language group
        languages = list(language_groups.keys())
        if languages:
            chunks_per_language = max(1, remaining_slots // len(languages))

            for lang in languages:
                lang_chunks = language_groups[lang][:chunks_per_language]
                selected_chunks.extend(lang_chunks)
                remaining_slots -= len(lang_chunks)

        # Fill remaining slots with highest scoring chunks
        all_remaining = []
        for lang, chunks in language_groups.items():
            chunks_per_language = max(1, top_k // len(languages)) if languages else 0
            all_remaining.extend(chunks[chunks_per_language:])
        all_remaining.extend(no_lang_chunks)

        # Sort remaining by similarity and take what we need
        all_remaining.sort(key=lambda x: x.get('similarity', 0), reverse=True)

        selected_chunks.extend(all_remaining[:remaining_slots])

        # Final sort by similarity to maintain quality
        selected_chunks.sort(key=lambda x: x.get('similarity', 0), reverse=True)

        return selected_chunks[:top_k]

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for a single text using online API.

        Args:
            text: Text to get embedding for

        Returns:
            numpy array of embedding
        """
        try:
            response = self.embedding_client.embeddings.create(
                model=self.embedding_model_name, input=[text]
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            st.error(f"Error getting single embedding: {str(e)}")
            return np.array([])

    def _get_embeddings(self, texts: list) -> np.ndarray:
        """
        Get embeddings for multiple texts using online API.

        Args:
            texts: List of texts to get embeddings for

        Returns:
            numpy array of embeddings
        """
        try:
            response = self.embedding_client.embeddings.create(
                model=self.embedding_model_name, input=texts
            )
            embeddings = [item.embedding for item in response.data]
            return np.array(embeddings)
        except Exception as e:
            st.error(f"Error getting embeddings: {str(e)}")
            st.info(f"Embedding API URL: {self.embedding_base_url}")
            st.info(f"Embedding Model: {self.embedding_model_name}")
            return np.array([])

    def extract_claim(self, text: str) -> str:
        """
        Extract core claims from the input text using LLM.

        Args:
            text: The input text to extract claims from

        Returns:
            extracted claim
        """
        # FIX: if the user pasted a bare URL (e.g. via the "Paste a URL"
        # quick-action), fetch the actual page content first instead of
        # handing the LLM a raw link string it can't do anything useful
        # with. See the URL HANDLING section above for the full story.
        if self._is_url(text):
            if self._is_social_media_url(text):
                return (
                    "This looks like a social media post (LinkedIn, "
                    "Instagram, X/Twitter, Facebook, etc.). These platforms "
                    "block automated access, so the post content can't be "
                    "reliably fetched - and personal posts/experiences "
                    "generally don't have public news coverage to verify "
                    "them against anyway. This tool works best for public "
                    "news claims and reported events. Please paste the "
                    "specific claim or headline text directly instead."
                )

            page_text = self._fetch_url_content(text)
            if page_text:
                text = page_text
            else:
                # Couldn't fetch/parse the page (bot-blocked, dead link,
                # non-HTML content, homepage with no article, etc). Tell
                # the user plainly rather than letting the LLM invent a
                # claim about the URL string itself.
                return (
                    "Could not extract article content from this URL. The "
                    "site may block automated requests, the link may not "
                    "point to a specific article, or it may not be "
                    "reachable. Please paste the headline or article text "
                    "directly instead."
                )

        # English-only project: always use English prompts regardless of
        # input text language or output_language setting.
        prompts = self._get_language_prompts("en")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompts["extract_claim"]},
                    {"role": "user", "content": f"{prompts['user_extract']} {text}"},
                ],
                temperature=0.0,  # Use low temperature for consistent claim extraction
                max_tokens=500,
            )

            claims_text = response.choices[0].message.content

            # Parse the numbered list into separate claims
            claims = re.findall(r"\d+\.\s+(.*?)(?=\n\d+\.|\Z)", claims_text, re.DOTALL)

            # Clean up the claims
            claims = [claim.strip() for claim in claims if claim.strip()]

            # If no numbered claims were found, split by newlines
            if not claims and claims_text.strip():
                claims = [
                    line.strip()
                    for line in claims_text.strip().split("\n")
                    if line.strip()
                ]

            # Return the first claim if available, otherwise return the original text
            if claims:
                return claims[0]
            else:
                # Fallback: return the original text or a cleaned version
                return claims_text.strip() if claims_text.strip() else text

        except Exception as e:
            st.error(f"Error extracting claims: {str(e)}")
            return text  # Return original text as fallback

    def search_evidence(self, claim: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search for evidence. English-only project, so this always runs a
        single search pass.

        FIX: this used to push a stream of st.empty()/st.info()/st.success()
        boxes into the page ("Running multi-language search...", "Searching
        language: en - ...", "found N pieces of evidence", plus two
        time.sleep(2) pauses to let each one be read) — that's the extra
        blue/grey status boxes that were appearing below the Check Now
        button in the UI. All of that UI plumbing is removed here; progress
        is now shown by the single morphing status line in app.py instead,
        and search runs straight through with no artificial delays.
        """
        search_languages = ['en']
        translations = self._translate_claim(claim, search_languages)

        all_evidence = []

        for lang_code, translated_claim in translations.items():
            try:
                if self.search_engine == "searxng":
                    evidence_docs = self._search_with_searxng(translated_claim, num_results)
                else:
                    evidence_docs = self._search_with_duckduckgo(translated_claim, num_results)

                for doc in evidence_docs:
                    doc['search_language'] = lang_code
                    doc['search_query'] = translated_claim
                    doc['detected_language'] = lang_code

                all_evidence.extend(evidence_docs)

            except Exception:
                continue

        # Remove duplicates based on URL
        seen_urls = set()
        unique_evidence = []
        for doc in all_evidence:
            if doc['url'] not in seen_urls:
                seen_urls.add(doc['url'])
                unique_evidence.append(doc)

        return unique_evidence

    def _search_with_searxng(
        self, query: str, num_results: int = 5
    ) -> List[Dict[str, str]]:
        """
        Search using SearXNG API.
        """
        try:
            search_url = f"{self.searxng_url}/search"
            params = {"q": query, "format": "json", "categories": "general"}

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }

            # Get timeout from config
            timeout_setting = self.search_config.get('timeout', 30)
            response = requests.get(
                search_url, params=params, headers=headers, timeout=timeout_setting
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            evidence_docs = []
            for result in results[:num_results]:
                evidence_docs.append(
                    {
                        "title": result.get("title", "No title"),
                        "url": result.get("url", "No URL"),
                        "snippet": result.get("content", "No snippet"),
                    }
                )

            return evidence_docs

        except Exception:
            # NOTE: previously surfaced via st.error(...), leaking a search
            # failure box into the UI. The caller already handles an empty
            # list gracefully (falls back to "no evidence found"), so we
            # just fail silently here.
            return []

    def _search_with_duckduckgo(
        self, query: str, num_results: int = 5
    ) -> List[Dict[str, str]]:
        """
        Search using DuckDuckGo (fallback method).
        """
        try:
            # Use proxy from search configuration if available
            proxy_setting = None
            if hasattr(self, 'search_config') and 'proxy' in self.search_config:
                proxy_setting = self.search_config['proxy']

            # Get timeout from config
            timeout_setting = self.search_config.get('timeout', 60)
            ddgs = DDGS(proxy=proxy_setting, timeout=timeout_setting)
            results = list(
                ddgs.text(query, region="us-en", max_results=num_results)
            )

            evidence_docs = []
            for result in results:
                evidence_docs.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                    }
                )

            return evidence_docs

        except Exception:
            # NOTE: previously surfaced via st.warning(...), leaking a
            # search-failure box into the UI. Fail silently instead — the
            # caller already handles an empty list gracefully.
            return []

    def get_evidence_chunks(
        self,
        evidence_docs: List[Dict[str, str]],
        claim: str,
        chunk_size: int = 200,
        chunk_overlap: int = 50,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Extract and rank evidence chunks related to the claim using embeddings.

        Args:
            evidence_docs: List of evidence documents
            claim: The claim to match with evidence
            chunk_size: Size of text chunks in characters
            chunk_overlap: Overlap between chunks in characters
            top_k: Number of top chunks to return

        Returns:
            List of ranked evidence chunks with similarity scores
        """
        if not self.embedding_client:
            return [
                {
                    "text": "Evidence ranking unavailable - Embedding API not available.",
                    "source": "System",
                    "similarity": 0.0,
                }
            ]

        if not evidence_docs:
            return [
                {
                    "text": "No evidence was found for this claim (search returned no results).",
                    "source": "System",
                    "similarity": 0.0,
                }
            ]

        try:
            # Create text chunks from evidence documents
            all_chunks = []

            for doc in evidence_docs:
                # Add title as a separate chunk
                chunk_data = {
                    "text": doc["title"],
                    "source": doc["url"],
                }
                # Preserve language metadata if available
                if 'detected_language' in doc:
                    chunk_data['detected_language'] = doc['detected_language']
                if 'search_language' in doc:
                    chunk_data['search_language'] = doc['search_language']
                all_chunks.append(chunk_data)

                # Process the snippet into overlapping chunks
                snippet = doc["snippet"]
                if len(snippet) <= chunk_size:
                    # If snippet is shorter than chunk_size, use it as is
                    chunk_data = {
                        "text": snippet,
                        "source": doc["url"],
                    }
                    # Preserve language metadata if available
                    if 'detected_language' in doc:
                        chunk_data['detected_language'] = doc['detected_language']
                    if 'search_language' in doc:
                        chunk_data['search_language'] = doc['search_language']
                    all_chunks.append(chunk_data)
                else:
                    # Create overlapping chunks
                    for i in range(0, len(snippet), chunk_size - chunk_overlap):
                        chunk_text = snippet[i : i + chunk_size]
                        if (
                            len(chunk_text) >= chunk_size // 2
                        ):  # Only keep chunks of reasonable size
                            chunk_data = {
                                "text": chunk_text,
                                "source": doc["url"],
                            }
                            # Preserve language metadata if available
                            if 'detected_language' in doc:
                                chunk_data['detected_language'] = doc['detected_language']
                            if 'search_language' in doc:
                                chunk_data['search_language'] = doc['search_language']
                            all_chunks.append(chunk_data)

            # Compute embeddings for claim using online API
            claim_embedding = self._get_embedding(claim)

            # Compute embeddings for chunks
            chunk_texts = [chunk["text"] for chunk in all_chunks]
            chunk_embeddings = self._get_embeddings(chunk_texts)

            # Calculate similarities
            similarities = []
            for i, chunk_embedding in enumerate(chunk_embeddings):
                similarity = np.dot(claim_embedding, chunk_embedding) / (
                    np.linalg.norm(claim_embedding) * np.linalg.norm(chunk_embedding)
                )
                similarities.append(float(similarity))

            # Add similarities to chunks
            for i, similarity in enumerate(similarities):
                all_chunks[i]["similarity"] = similarity

            # Sort chunks by similarity (descending)
            ranked_chunks = sorted(
                all_chunks, key=lambda x: x["similarity"], reverse=True
            )

            # Optimize evidence selection for language diversity
            optimized_chunks = self._optimize_language_diversity(ranked_chunks, top_k)

            # Return optimized chunks
            return optimized_chunks

        except Exception as e:
            st.error(f"Error ranking evidence: {str(e)}")
            return [
                {
                    "text": f"Error ranking evidence: {str(e)}",
                    "source": "System",
                    "similarity": 0.0,
                }
            ]

    def evaluate_claim(
        self, claim: str, evidence_chunks: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Evaluate the truthfulness of a claim based on evidence using LLM.

        Args:
            claim: The claim to evaluate
            evidence_chunks: The evidence chunks to use for evaluation

        Returns:
            Dictionary with verdict and reasoning
        """
        # English-only project: always use English prompts.
        prompts = self._get_language_prompts("en")

        # Check if evidence chunks are available
        if not evidence_chunks:
            st.warning("No evidence found for evaluation. Returning unverifiable verdict.")
            return {
                "verdict": "UNVERIFIABLE",
                "reasoning": "Could not find relevant evidence to fact-check this claim."
            }

        # Prepare evidence text for the prompt
        evidence_text = "\n\n".join(
            [
                f"EVIDENCE {i+1} (Relevance: {chunk.get('similarity', 0.0):.2f}):\n{chunk['text']}\nSource: {chunk['source']}"
                for i, chunk in enumerate(evidence_chunks)
            ]
        )

        try:
            messages = [
                {"role": "system", "content": prompts["evaluate_claim"]},
                {
                    "role": "user",
                    "content": prompts["user_evaluate"].format(
                        claim=claim, evidence=evidence_text
                    ),
                },
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            result_text = response.choices[0].message.content

            # Clean up Unicode characters that might cause encoding issues
            if result_text:
                # Replace problematic Unicode characters
                result_text = result_text.replace('\u2011', '-')  # Non-breaking hyphen to normal hyphen
                result_text = result_text.replace('\u2013', '-')  # En dash to normal hyphen
                result_text = result_text.replace('\u2014', '-')  # Em dash to normal hyphen
                result_text = result_text.replace('\u2010', '-')  # Hyphen to normal hyphen
                # Remove other potentially problematic characters
                result_text = ''.join(char for char in result_text if ord(char) < 65536)

            # Handle empty response
            if not result_text or result_text.strip() == "":
                st.error("⚠️ The model returned an empty response!")
                st.info("🔧 Suggested fixes:")
                st.info("1. Switch to a stronger model (e.g. llama-3.3-70b-versatile)")
                st.info("2. Check that your Groq API key is valid and not rate-limited")
                st.info("3. Try reducing the length of the input text")
                return {
                    "verdict": "UNVERIFIABLE",
                    "reasoning": f"The current model '{self.model}' returned an empty response. Try switching to a stronger model or check your API key/rate limits."
                }

            # Extract verdict and reasoning
            verdict_match = re.search(
                r"VERDICT[:：]\s*(TRUE|FALSE|PARTIALLY TRUE)",
                result_text,
                re.IGNORECASE,
            )

            if verdict_match:
                verdict = verdict_match.group(1).upper()
            else:
                # Try to infer from content if no explicit verdict found
                if "is true" in result_text.lower() or "supported" in result_text.lower():
                    verdict = "TRUE"
                elif "is false" in result_text.lower() or "contradicted" in result_text.lower():
                    verdict = "FALSE"
                else:
                    verdict = "UNVERIFIABLE"

            reasoning_match = re.search(
                r"REASONING[:：]\s*(.*)",
                result_text,
                re.DOTALL | re.IGNORECASE,
            )
            reasoning = (
                reasoning_match.group(1).strip()
                if reasoning_match
                else result_text.strip()
            )

            return {"verdict": verdict, "reasoning": reasoning}

        except Exception as e:
            st.error(f"Error evaluating claim: {str(e)}")
            return {
                "verdict": "ERROR",
                "reasoning": f"An error occurred during evaluation: {str(e)}",
            }

    def check_fact(self, text: str) -> Dict[str, Any]:
        """
        Main function to check the factuality of a statement.

        Args:
            text: The statement to fact-check

        Returns:
            Dictionary with all results of the fact-checking process
        """
        # 1. Extract core claim
        claim = self.extract_claim(text)

        result = {"original_text": text, "claim": claim, "results": []}
        # 2. Search for evidence
        evidence_docs = self.search_evidence(claim)

        # 3. Get relevant evidence chunks
        evidence_chunks = self.get_evidence_chunks(evidence_docs, claim)

        # 4. Evaluate claim based on evidence
        evaluation = self.evaluate_claim(claim, evidence_chunks)

        # Add results for this claim
        result = {
            "claim": claim,
            "evidence_docs": evidence_docs,
            "evidence_chunks": evidence_chunks,
            "verdict": evaluation["verdict"],
            "reasoning": evaluation["reasoning"],
        }

        return result


# Function to be imported in the main Streamlit app
def check_fact(
    claim: str, api_base: str, model: str, temperature: float, max_tokens: int
) -> Dict[str, Any]:
    """
    Public interface for fact checking to be used by the Streamlit app.

    Args:
        claim: The statement to fact-check
        api_base: The base URL for the LLM API
        model: The model to use for fact checking
        temperature: Temperature parameter for LLM
        max_tokens: Maximum tokens for LLM response

    Returns:
        Dictionary with all results of the fact-checking process
    """
    checker = FactChecker(api_base, model, temperature, max_tokens)
    return checker.check_fact(claim)
