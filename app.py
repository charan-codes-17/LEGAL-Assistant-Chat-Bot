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

# Custom CSS for Premium Modern Glassmorphism & High-Contrast Typography
st.markdown(
    """
    <style>
    /* Dark glassmorphic styling */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d131f 100%);
        color: #e6edf3;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Header Card */
    .header-box {
        background: rgba(22, 27, 34, 0.75);
        border: 1px solid rgba(56, 139, 253, 0.3);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #58a6ff, #79c0ff, #d2a8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    
    .header-sub {
        color: #8b949e;
        font-size: 0.95rem;
        margin-bottom: 0px;
    }
    
    /* Pipeline Badge Container */
    .pipeline-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    
    .badge-in-scope {
        background-color: rgba(35, 134, 54, 0.25);
        color: #3fb950;
        border: 1px solid rgba(63, 185, 80, 0.4);
    }
    
    .badge-out-domain {
        background-color: rgba(218, 54, 51, 0.25);
        color: #f85149;
        border: 1px solid rgba(248, 81, 73, 0.4);
    }
    
    .badge-score {
        background-color: rgba(88, 166, 255, 0.2);
        color: #58a6ff;
        border: 1px solid rgba(88, 166, 255, 0.4);
    }
    
    .badge-unverified {
        background-color: rgba(210, 153, 34, 0.2);
        color: #d29922;
        border: 1px solid rgba(210, 153, 34, 0.4);
    }
    
    .badge-offline {
        background-color: rgba(210, 153, 34, 0.2);
        color: #d29922;
        border: 1px solid rgba(210, 153, 34, 0.4);
    }
    
    /* Quick chip buttons */
    .stButton button {
        border-radius: 8px;
        transition: all 0.2s ease-in-out;
    }
    
    .stButton button:hover {
        border-color: #58a6ff;
        box-shadow: 0 0 12px rgba(88, 166, 255, 0.3);
    }
    
    /* Sidebar enhancements */
    [data-testid="stSidebar"] {
        background-color: #0b0f14;
        border-right: 1px solid #30363d;
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
user_input = st.chat_input("Ask a legal question regarding Indian Constitutional & Arrest Rights...")
query_to_process = selected_prompt or user_input

if query_to_process:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": query_to_process, "meta": None})
    with st.chat_message("user"):
        st.markdown(query_to_process)

    # Process query
    with st.chat_message("assistant"):
        with st.spinner("Analyzing query, checking legal domain & retrieving verified sources..."):
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