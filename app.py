"""
LUMA — Indian Legal Information Assistant
Streamlit Web Application for BUILD-A-BOT Competition
"""
import streamlit as st
import time
import json
from pathlib import Path

from src.config import (
    GROQ_API_KEY,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    EVIDENCE_THRESHOLD,
    TOP_K_CHUNKS,
    SYSTEM_DOMAIN,
)
from src.retriever import get_retriever
from src.classifier import get_classifier
from src.llm import LLMClient
from src.safety import (
    OUT_OF_DOMAIN_RESPONSE,
    OUT_OF_SCOPE_LEGAL_RESPONSE,
    INSUFFICIENT_EVIDENCE_RESPONSE,
    AMBIGUOUS_QUERY_RESPONSE,
)

# Page Setup
st.set_page_config(
    page_title="LUMA — Legal Understanding with Modern Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS — Clean flat-black SaaS style (grid background, no blur/glass, bold type)
st.markdown(
    """
    <style>
    /* Solid black app background with faint grid-line pattern */
    .stApp {
        background-color: #050505;
        background-image:
            linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px);
        background-size: 42px 42px;
        color: #f5f5f5;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Header Card — flat panel, hairline border, no blur */
    .header-box {
        background: #0c0c0d;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 22px 26px;
        margin-bottom: 20px;
    }

    .header-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 6px;
    }

    .header-sub {
        color: #8a8a8a;
        font-size: 0.95rem;
        margin-bottom: 0px;
    }

    /* Pipeline Badge Container — flat pill, no glow */
    .pipeline-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
        background: #111214;
    }

    .badge-in-scope {
        color: #4ade80;
        border: 1px solid rgba(74, 222, 128, 0.35);
    }

    .badge-out-domain {
        color: #f87171;
        border: 1px solid rgba(248, 113, 113, 0.35);
    }

    .badge-score {
        color: #60a5fa;
        border: 1px solid rgba(96, 165, 250, 0.35);
    }

    .badge-unverified {
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.35);
    }

    .badge-offline {
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.35);
    }

    /* Quick chip buttons — flat, hairline border, subtle hover lift */
    .stButton button {
        background-color: #0c0c0d;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 8px;
        color: #f5f5f5;
        transition: all 0.15s ease-in-out;
    }

    .stButton button:hover {
        border-color: #3b82f6;
        background-color: #101114;
    }

    /* Sidebar — solid black, hairline divider */
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Chat input — flat black field, blue focus ring */
    div[data-testid="stChatInput"] textarea {
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 10px !important;
        background: #0c0c0d !important;
        color: #f5f5f5 !important;
        padding: 1rem !important;
        transition: border 150ms cubic-bezier(0.4,0,0.2,1), box-shadow 150ms cubic-bezier(0.4,0,0.2,1);
    }

    div[data-testid="stChatInput"] textarea:focus {
        outline: none !important;
        border: 1px solid #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
    }

    /* Loading animation — adapted from Uiverse.io by ClawHack1 */
    .luma-loader-wrap {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        padding: 12px 0;
    }
    .luma-loader {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 60px;
        height: 40px;
    }
    .luma-loader-block {
        display: inline-block;
        width: 8px;
        height: 8px;
        margin: 2px;
        background-color: #3b82f6;
        box-shadow: 0 0 14px #3b82f6;
        animation: luma_loader_pulse 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
    }
    .luma-loader-block:nth-child(1) { animation-delay: 0.1s; }
    .luma-loader-block:nth-child(2) { animation-delay: 0.2s; }
    .luma-loader-block:nth-child(3) { animation-delay: 0.3s; }
    .luma-loader-block:nth-child(4) { animation-delay: 0.4s; }
    .luma-loader-block:nth-child(5) { animation-delay: 0.5s; }
    .luma-loader-text {
        color: #8a8a8a;
        font-size: 0.85rem;
    }
    @keyframes luma_loader_pulse {
        0% {
            transform: scale(1);
            box-shadow: 0 0 14px rgba(59, 130, 246, 0.5);
        }
        20% {
            transform: scale(1, 2.5);
            box-shadow: 0 0 30px rgba(59, 130, 246, 0.7);
        }
        40% {
            transform: scale(1);
            box-shadow: 0 0 14px rgba(59, 130, 246, 0.5);
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
    <div class="header-box">
        <div class="header-title">⚖️ LUMA — Legal Information Assistant</div>
        <div class="header-sub">
            Grounded Indian Constitutional & Arrest Rights Assistant • Built for <b>BUILD-A-BOT</b> Competition (Dept of AI, TCE)
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! I am **LUMA**, your verified AI assistant for **Indian Constitutional Rights "
                "and Arrest/Detention Safeguards**.\n\n"
                "You can ask me about:\n"
                "- **Article 21** (Right to Life & Personal Liberty)\n"
                "- **Article 22 & CrPC** (Grounds of arrest, mandatory 24-hr magistrate production)\n"
                "- **D.K. Basu Guidelines** (Arrest memo, medical check, family intimation)\n"
                "- **Article 39A & NALSA** (Free Legal Aid)\n"
                "- **Articles 32 & 226** (Writ of *Habeas Corpus* for unlawful detention)\n\n"
                "💡 *Click any of the challenge questions below or type your own question.*"
            ),
            "meta": None,
        }
    ]

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/scales.png", width=64)
    st.title("⚙️ Control Panel")

    st.markdown("### 🔒 System Scope")
    st.info(
        "**Verified Legal Domain:**\n"
        "• Constitution of India (Arts 14, 19, 21, 22, 32, 226)\n"
        "• CrPC / BNSS (Arrest rights, Sec 41, 50, 57, 167)\n"
        "• D.K. Basu Landmark Guidelines\n"
        "• Legal Services Authorities Act (NALSA)"
    )

    st.markdown("---")
    st.markdown("### 🔌 Engine Settings")

    provider_choice = st.selectbox(
        "Active AI Provider",
        ["OpenRouter API", "Groq API", "⚡ Offline Demo Mode"],
        index=0 if OPENROUTER_API_KEY else 2,
        help="Select live generation provider or 100% deterministic offline demo mode."
    )

    openrouter_key_input = ""
    openrouter_model_input = OPENROUTER_MODEL
    groq_key_input = ""

    if provider_choice == "OpenRouter API":
        openrouter_key_input = st.text_input(
            "OpenRouter API Key",
            value=OPENROUTER_API_KEY,
            type="password",
            placeholder="sk-or-v1-...",
            help="Your OpenRouter API key.",
        )
        openrouter_model_input = st.selectbox(
            "Model",
            [
                "meta-llama/llama-3.3-70b-instruct",
                "openai/gpt-4o-mini",
                "deepseek/deepseek-chat",
                "anthropic/claude-3-haiku",
            ],
            index=0,
        )
    elif provider_choice == "Groq API":
        groq_key_input = st.text_input(
            "Groq API Key",
            value=GROQ_API_KEY,
            type="password",
            placeholder="gsk_...",
            help="Your Groq API key.",
        )

    demo_mode = (provider_choice == "⚡ Offline Demo Mode")

    threshold_slider = st.slider(
        "Evidence Threshold",
        min_value=0.05,
        max_value=0.50,
        value=EVIDENCE_THRESHOLD,
        step=0.01,
        help="Cosine similarity threshold required to generate an answer and prevent hallucination.",
    )

    st.markdown("---")
    st.markdown("### 📚 Knowledge Base Sources")
    retriever = get_retriever()

    with st.expander(f"Inspect Sources ({len(retriever.sources_catalog)})", expanded=False):
        for sid, src in retriever.sources_catalog.items():
            st.markdown(f"**{src['title']}**")
            st.caption(f"Authority: {src['authority']} | [Link]({src['url']})")
            st.divider()

    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

    # Chat Export
    chat_export_text = "# LUMA Legal Chatbot — Session Transcript\n\n"
    for msg in st.session_state.messages:
        chat_export_text += f"### {msg['role'].upper()}:\n{msg['content']}\n\n"
    st.download_button(
        "📥 Download Chat Transcript",
        data=chat_export_text,
        file_name="legal_assistant_session.md",
        mime="text/markdown",
        use_container_width=True,
    )


# 5 Challenge Questions Quick Selection Chips
st.markdown("##### 🎯 Competition Challenge Questions (One-Click Demo):")
col1, col2, col3 = st.columns(3)
col4, col5 = st.columns(2)

selected_prompt = None

with col1:
    if st.button("Q1: Article 21 Right to Life", use_container_width=True):
        selected_prompt = (
            "Is it true that Article 21 of the Constitution of India guarantees the right to life "
            "and personal liberty? Verify your answer using reliable legal sources."
        )

with col2:
    if st.button("Q2: Police Arrest Without Reason?", use_container_width=True):
        selected_prompt = (
            "Under Indian law, police can arrest any person without reason or evidence at any time. Is this correct?"
        )

with col3:
    if st.button("Q3: Rights at Time of Arrest", use_container_width=True):
        selected_prompt = (
            "If arrest requires legal grounds, what rights does a person have at the time of arrest in India?"
        )

with col4:
    if st.button("Q4: Detained > 24h Without Magistrate Advice", use_container_width=True):
        selected_prompt = (
            "Suppose a person is arrested without being informed of the reason and not produced before "
            "a magistrate within 24 hours. What would you advise?"
        )

with col5:
    if st.button("Q5: Decision Trees in ML (Out of Domain)", use_container_width=True):
        selected_prompt = (
            "What are the main principles behind machine learning algorithms like decision trees?"
        )

# Render Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("meta"):
            meta = message["meta"]
            badges_html = "<div style='margin-bottom: 10px;'>"

            # Category badge
            cat = meta.get("category", "")
            if cat == "LEGAL_IN_SCOPE":
                badges_html += f"<span class='pipeline-badge badge-in-scope'>✓ Domain: LEGAL ({meta.get('classifier_conf', 1.0)})</span>"
            elif cat == "LEGAL_UNVERIFIED":
                badges_html += f"<span class='pipeline-badge badge-unverified'>? Domain: UNVERIFIED, checking evidence ({meta.get('classifier_conf', 1.0)})</span>"
            elif cat == "OUT_OF_DOMAIN":
                badges_html += "<span class='pipeline-badge badge-out-domain'>✗ Domain: OUT OF SCOPE</span>"
            else:
                badges_html += f"<span class='pipeline-badge badge-out-domain'>! Status: {cat}</span>"

            # Score badge
            if "score" in meta:
                badges_html += f"<span class='pipeline-badge badge-score'>📊 Max Cosine Sim: {meta['score']}</span>"

            # Provider badge
            if "provider" in meta:
                badges_html += f"<span class='pipeline-badge badge-offline'>⚡ {meta['provider']} ({meta.get('latency', 0.0)}s)</span>"

            badges_html += "</div>"
            st.markdown(badges_html, unsafe_allow_html=True)

        st.markdown(message["content"])

# Handle Chat Input
user_input = st.chat_input("Ask LUMA — e.g. What are my rights if I'm arrested?")
query_to_process = selected_prompt or user_input

if query_to_process:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": query_to_process, "meta": None})
    with st.chat_message("user"):
        st.markdown(query_to_process)

    # Process query
    with st.chat_message("assistant"):
        loader_placeholder = st.empty()
        loader_placeholder.markdown(
            """
            <div class="luma-loader-wrap">
                <div class="luma-loader">
                    <div class="luma-loader-block"></div>
                    <div class="luma-loader-block"></div>
                    <div class="luma-loader-block"></div>
                    <div class="luma-loader-block"></div>
                    <div class="luma-loader-block"></div>
                </div>
                <div class="luma-loader-text">Analyzing query, checking legal domain &amp; retrieving verified sources...</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if True:
            classifier = get_classifier()
            domain_result = classifier.classify(query_to_process)
            category = domain_result["category"]

            meta_data = {
                "category": category,
                "classifier_conf": domain_result["confidence"],
                "reason": domain_result["reason"],
            }

            # 1. Out of domain filter (e.g. Q5 ML / Decision Trees)
            if category == "OUT_OF_DOMAIN":
                response_text = OUT_OF_DOMAIN_RESPONSE
                meta_data["provider"] = "Scope Filter"
                meta_data["latency"] = 0.01

            # 2. Out of scope legal query
            elif category == "LEGAL_OUT_OF_SCOPE":
                response_text = OUT_OF_SCOPE_LEGAL_RESPONSE
                meta_data["provider"] = "Scope Filter"
                meta_data["latency"] = 0.01

            # 3. Ambiguous query
            elif category == "AMBIGUOUS":
                response_text = AMBIGUOUS_QUERY_RESPONSE
                meta_data["provider"] = "Scope Filter"
                meta_data["latency"] = 0.01

            # 3b. Empty input (classifier.py returns this category, but it was
            # previously falling through to the full RAG pipeline unhandled)
            elif category == "EMPTY_INPUT":
                response_text = (
                    "Please enter a question about Indian constitutional rights "
                    "or arrest/detention procedures."
                )
                meta_data["provider"] = "Scope Filter"
                meta_data["latency"] = 0.01

            # 4. In-scope legal query -> Vector Retrieval & LLM
            else:
                retrieval = retriever.retrieve(
                    query_to_process,
                    top_k=TOP_K_CHUNKS,
                    threshold=threshold_slider,
                )
                meta_data["score"] = retrieval["max_score"]

                pref_provider = "offline" if demo_mode else ("openrouter" if provider_choice == "OpenRouter API" else "groq")
                llm_client = LLMClient(
                    groq_key=groq_key_input,
                    openrouter_key=openrouter_key_input,
                    openrouter_model=openrouter_model_input,
                )
                gen_result = llm_client.generate_answer(
                    query=query_to_process,
                    retrieval_data=retrieval,
                    custom_groq_key=groq_key_input,
                    custom_openrouter_key=openrouter_key_input,
                    force_offline=demo_mode,
                    preferred_provider=pref_provider,
                )

                response_text = gen_result["answer"]
                meta_data["provider"] = gen_result["provider"]
                meta_data["latency"] = gen_result["latency"]

            # Clear the loading animation now that we have a result
            loader_placeholder.empty()

            # Display response with badges
            badges_html = "<div style='margin-bottom: 10px;'>"
            if category == "LEGAL_IN_SCOPE":
                badges_html += f"<span class='pipeline-badge badge-in-scope'>✓ Domain: LEGAL ({domain_result['confidence']})</span>"
            elif category == "LEGAL_UNVERIFIED":
                badges_html += f"<span class='pipeline-badge badge-unverified'>? Domain: UNVERIFIED, checking evidence ({domain_result['confidence']})</span>"
            elif category == "OUT_OF_DOMAIN":
                badges_html += "<span class='pipeline-badge badge-out-domain'>✗ Domain: OUT OF SCOPE</span>"
            else:
                badges_html += f"<span class='pipeline-badge badge-out-domain'>! Status: {category}</span>"

            if "score" in meta_data:
                badges_html += f"<span class='pipeline-badge badge-score'>📊 Max Cosine Sim: {meta_data['score']}</span>"

            if "provider" in meta_data:
                badges_html += f"<span class='pipeline-badge badge-offline'>⚡ {meta_data['provider']} ({meta_data.get('latency', 0.0)}s)</span>"

            badges_html += "</div>"
            st.markdown(badges_html, unsafe_allow_html=True)
            st.markdown(response_text)

            # Store in session state
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text, "meta": meta_data}
            )
            st.rerun()