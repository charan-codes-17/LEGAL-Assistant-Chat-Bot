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
    initial_sidebar_state="collapsed",
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

    /* ── Fixed bottom gradient wrapper ───────────────────────────────
       Streamlit's [data-testid="stBottom"] is already position:fixed at
       the bottom of the viewport.  We strip its opaque background and
       replace it with a top-to-bottom linear gradient that fades from
       fully transparent (top edge, where chat messages scroll behind it)
       to solid dark (bottom edge, behind the input field + disclaimer).
       This gives the exact "content fades under the bar" effect seen in
       Gemini / ChatGPT without any extra DOM wrappers. */

    /* 1. Strip inner containers so no solid box sits behind the gradient */
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] > div,
    [data-testid="stChatInputContainer"],
    .stChatFloatingInputContainer > div {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
    }

    /* 2. Apply the gradient to stBottom itself.  The gradient starts
       transparent at the top so chat bubbles show through as they scroll
       up, and ends fully opaque at the same dark colour as the app bg.
       `bottom: 0px` pins the whole dock flush to the viewport edge
       (Streamlit's default leaves a small gap); padding-bottom is kept
       small since it no longer needs to reserve a large empty strip. */
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"],
    .stChatFloatingInputContainer {
        bottom: 13px !important;
        background: linear-gradient(
            to bottom,
            transparent 0%,
            rgba(5, 5, 5, 0.55) 35%,
            rgba(5, 5, 5, 0.92) 65%,
            #050505 100%
        ) !important;
        border: none !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
        /* Small bottom room for the disclaimer text */
        padding-bottom: 0.7rem !important;
    }

    /* 3. Disclaimer sits directly under the input, on top of the solid
       part of the gradient (bottom ~20 % of the container). */
    .luma-input-caption {
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0.55rem;
        text-align: center;
        font-size: 0.75rem;
        color: #8a8a8a;
        z-index: 1000;
        pointer-events: none;
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
    /* Hide Streamlit's default chrome: main menu, header toolbar, footer,
       "Manage app" pill, and Fork/GitHub controls — this was previously
       only suggested as a snippet and never actually landed in the file */
    #MainMenu {visibility: hidden; height: 0;}
    footer {visibility: hidden; height: 0;}
    header {visibility: hidden; height: 0;}

    [data-testid="stToolbar"],
    [data-testid="stStatusWidget"],
    [data-testid="stHeader"],
    [data-testid="stDecoration"] {
        visibility: hidden !important;
        height: 0 !important;
        position: fixed !important;
    }

    .stAppDeployButton,
    .stDeployButton {
        display: none !important;
    }

    /* No sidebar content remains — hide the empty toggle arrow entirely */
    [data-testid="collapsedControl"] {
        display: none;
    }

    /* Prevent the focused textarea from pulling the page down on mobile
       or when Streamlit auto-focuses it after a rerun */
    div[data-testid="stChatInput"] textarea {
        overscroll-behavior: contain;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Suppress Streamlit's auto-scroll-to-bottom ────────────────────────────
# Streamlit's front-end JS calls window.scrollTo({top: <large>, …}) and
# element.scrollIntoView() after every DOM update to snap the viewport to
# the newest message.  The snippet below intercepts both entry points and
# turns them into no-ops ONLY for downward jumps triggered by Streamlit
# itself — user-initiated scrolls (mouse wheel, touch, scrollbar drag) are
# never affected because those don't go through these JS APIs.
st.markdown(
    """
    <script>
    (function () {
        if (window.__lumaScrollPatched) return;
        window.__lumaScrollPatched = true;

        /* 1. Intercept window.scrollTo so Streamlit can't snap the whole
              page downward.  Upward scrolls and scrolls to the very top
              (top === 0) are still allowed so the page isn't completely
              frozen. */
        const _origScrollTo = window.scrollTo.bind(window);
        window.scrollTo = function (xOrOpts, y) {
            if (typeof xOrOpts === 'object' && xOrOpts !== null) {
                const t = xOrOpts.top;
                // Block any large downward snap (> 200 px from current pos)
                if (typeof t === 'number' && t > window.scrollY + 200) return;
                return _origScrollTo(xOrOpts);
            }
            if (typeof y === 'number' && y > window.scrollY + 200) return;
            return _origScrollTo(xOrOpts, y);
        };

        /* 2. Intercept Element.prototype.scrollIntoView — Streamlit calls
              this on chat message elements to pull them into view.  We
              block it only for elements that live inside the main chat
              scroll area; any other callers (e.g. anchor links) still work. */
        const _origSIV = Element.prototype.scrollIntoView;
        Element.prototype.scrollIntoView = function (arg) {
            const inChat = this.closest(
                '[data-testid="stChatMessageContainer"], '
                + '[data-testid="stBottom"], '
                + '.stChatMessage'
            );
            if (inChat) return;   // suppress auto-scroll for chat elements
            return _origSIV.call(this, arg);
        };

        /* 3. Intercept scrollTop assignment on the main scrollable element
              so nothing can jump the page by setting elem.scrollTop. */
        const patchScrollTop = (el) => {
            if (!el || el.__lumaPatched) return;
            el.__lumaPatched = true;
            let _st = el.scrollTop;
            Object.defineProperty(el, 'scrollTop', {
                get: () => _st,
                set: (v) => {
                    if (v > _st + 200) return;   // block downward snap
                    _st = v;
                    /* Use the real setter via a temporary clone trick */
                    const proto = Object.getPrototypeOf(el);
                    const desc = Object.getOwnPropertyDescriptor(proto, 'scrollTop');
                    if (desc && desc.set) desc.set.call(el, v);
                },
                configurable: true,
            });
        };

        /* Apply the scrollTop patch to the viewport and any inner scroll
           container Streamlit might use, once the DOM is ready. */
        const tryPatch = () => {
            patchScrollTop(document.documentElement);
            patchScrollTop(document.body);
            const main = document.querySelector(
                '[data-testid="stAppViewContainer"] > section.main, '
                + '.main.st-emotion-cache-uf99v8'
            );
            if (main) patchScrollTop(main);
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', tryPatch);
        } else {
            tryPatch();
        }
    })();
    </script>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 20px;">
        <span style="font-size: 2.1rem; font-weight: 700; color: #ffffff;">
            ⚖️ LUMA — Your Legal Assistant
        </span>
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

# Engine config — no sidebar UI. Provider auto-selects from configured
# Secrets/.env in priority order: OpenRouter -> Groq -> Offline Demo Mode.
if OPENROUTER_API_KEY:
    provider_choice = "OpenRouter API"
elif GROQ_API_KEY:
    provider_choice = "Groq API"
else:
    provider_choice = "⚡ Offline Demo Mode"

demo_mode = (provider_choice == "⚡ Offline Demo Mode")
openrouter_key_input = OPENROUTER_API_KEY
openrouter_model_input = OPENROUTER_MODEL
groq_key_input = GROQ_API_KEY
threshold_slider = EVIDENCE_THRESHOLD

retriever = get_retriever()


# Chat-only mode — quick question chips removed
selected_prompt = None

# Render Chat History — once a real exchange has happened (more than
# just the initial welcome message), the welcome/bullet list is hidden
# so only the active conversation shows.
messages_to_render = st.session_state.messages
if len(messages_to_render) > 1:
    messages_to_render = messages_to_render[1:]

for message in messages_to_render:
    with st.chat_message(message["role"]):
        # Pipeline debug badges (domain / cosine similarity / provider &
        # latency) are intentionally not rendered — internal diagnostics,
        # not something an end user should see. `message["meta"]` is still
        # stored in session state untouched, so nothing downstream breaks.
        st.markdown(message["content"])

# Handle Chat Input
user_input = st.chat_input("Ask LUMA")
st.markdown(
    '<div class="luma-input-caption">LUMA is an AI assistant providing general '
    'information, not formal legal advice. Verify critical details with a '
    'qualified advocate.</div>',
    unsafe_allow_html=True,
)
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

            # Pipeline debug badges (domain / cosine similarity / provider &
            # latency) are intentionally not rendered here either — meta_data
            # is still computed above and stored in session state below, so
            # nothing downstream (citations, fallback logic, etc.) breaks.
            st.markdown(response_text)

            # Store in session state — no st.rerun() needed here.
            # The response is already rendered live above in this same script
            # execution.  Calling st.rerun() would trigger a full page reload
            # which (a) snaps the viewport back to the bottom and (b) wastes
            # a round-trip.  On the next user submission Streamlit naturally
            # re-runs the script, replaying all messages from session state.
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text, "meta": meta_data}
            )