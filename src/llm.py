"""
Multi-Provider LLM Integration and Orchestration Module
Supports Groq API, OpenRouter API, and automated fallback to deterministic offline cache.
"""
import os
import time
import logging
import requests
from typing import Dict, Any, List, Optional

from src.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    TEMPERATURE,
    MAX_OUTPUT_TOKENS,
    FALLBACK_TO_OFFLINE_DEMO,  # NOTE: imported but not referenced below. Offline mode
    # is currently driven entirely by the `force_offline`/`preferred_provider`
    # params passed in from app.py's sidebar toggle. Setting this env var alone
    # has no effect. Either wire it in as a default for `force_offline` in
    # generate_answer(), or drop the import to stop it looking load-bearing.
)
from src.prompts import LEGAL_SYSTEM_PROMPT, GROUNDED_QA_TEMPLATE
from src.safety import format_response_with_citations, INSUFFICIENT_EVIDENCE_RESPONSE
from src.fallback import get_cached_demo_response

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM Client with automatic error recovery and deterministic offline fallback.
    """

    def __init__(
        self,
        groq_key: Optional[str] = None,
        groq_model: str = GROQ_MODEL,
        openrouter_key: Optional[str] = None,
        openrouter_model: str = OPENROUTER_MODEL,
    ):
        self.groq_key = groq_key or GROQ_API_KEY
        self.groq_model = groq_model
        self.openrouter_key = openrouter_key or OPENROUTER_API_KEY
        self.openrouter_model = openrouter_model

    def _call_groq(self, prompt: str, system_prompt: str, api_key: str) -> str:
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": TEMPERATURE,
            "max_tokens": MAX_OUTPUT_TOKENS,
        }
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=25,
        )
        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"]["content"].strip()
            raise ValueError("Empty response received from Groq API.")
        raise ValueError(f"Groq API error {resp.status_code}: {resp.text}")

    def _call_openrouter(
        self, prompt: str, system_prompt: str, api_key: str, model_name: Optional[str] = None
    ) -> str:
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "LUMA Legal Chatbot",
            "Content-Type": "application/json",
        }

        # Try designated model, with fallbacks
        models_to_try = [
            model_name or self.openrouter_model,
            "meta-llama/llama-3.3-70b-instruct",
            "openai/gpt-4o-mini",
            "deepseek/deepseek-chat",
        ]

        last_error = None
        for m in models_to_try:
            payload = {
                "model": m,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": TEMPERATURE,
                "max_tokens": MAX_OUTPUT_TOKENS,
            }
            try:
                resp = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=25,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"]["content"].strip()
                else:
                    last_error = f"OpenRouter status {resp.status_code}: {resp.text}"
            except Exception as e:
                last_error = str(e)

        raise ValueError(f"OpenRouter generation failed: {last_error}")

    def generate_answer(
        self,
        query: str,
        retrieval_data: Dict[str, Any],
        custom_groq_key: Optional[str] = None,
        custom_openrouter_key: Optional[str] = None,
        force_offline: bool = False,
        preferred_provider: str = "auto",  # 'groq', 'openrouter', 'offline', 'auto'
    ) -> Dict[str, Any]:
        """
        Orchestrates grounded answer generation with multi-tiered fallback.
        """
        start_time = time.time()
        groq_key = (custom_groq_key or self.groq_key or GROQ_API_KEY).strip()
        openrouter_key = (custom_openrouter_key or self.openrouter_key or OPENROUTER_API_KEY).strip()

        sources = retrieval_data.get("sources", [])
        formatted_context = retrieval_data.get("formatted_context", "")
        is_sufficient = retrieval_data.get("is_sufficient", False)

        # 1. Check if query is insufficient / hallucination trap
        if not is_sufficient and not force_offline:
            cached = get_cached_demo_response(query)
            if cached and cached.get("category") == "LEGAL_IN_SCOPE":
                latency = round(time.time() - start_time, 3)
                return {
                    "answer": cached["answer"],
                    "sources": cached["sources"],
                    "provider": "Offline Cached Fallback",
                    "latency": latency,
                    "is_cached": True,
                    "status": "SUCCESS",
                }

        # 2. If force_offline is requested or no API key is provided
        if force_offline or preferred_provider == "offline" or (not groq_key and not openrouter_key):
            cached = get_cached_demo_response(query)
            if cached:
                latency = round(time.time() - start_time, 3)
                return {
                    "answer": cached["answer"],
                    "sources": cached["sources"],
                    "provider": "Deterministic Offline Cache (Demo Mode)",
                    "latency": latency,
                    "is_cached": True,
                    "status": "SUCCESS",
                }

            if is_sufficient and retrieval_data.get("chunks"):
                chunks = retrieval_data["chunks"]
                if len(chunks) == 1:
                    body = chunks[0]["text"]
                else:
                    # Synthesize from ALL retrieved chunks (not just the top-ranked one),
                    # so multi-provision questions get a fuller offline answer instead of
                    # being truncated to a single passage. Grouped under each chunk's
                    # source title so the reader can see which provision each line covers.
                    body = "\n\n".join(
                        f"**{c.get('title') or c.get('source_id', 'Unknown Source')}**\n{c['text']}"
                        for c in chunks
                    )
                synth_answer = (
                    f"### ⚖️ Legal Overview based on Verified Documents:\n\n"
                    f"{body}\n\n"
                    f"*Note: Synthesized directly from verified knowledge base without live API call "
                    f"({len(chunks)} relevant provision{'s' if len(chunks) != 1 else ''} shown).*"
                )
                formatted = format_response_with_citations(synth_answer, sources, include_disclaimer=True)
                latency = round(time.time() - start_time, 3)
                return {
                    "answer": formatted,
                    "sources": sources,
                    "provider": "Local Knowledge Base Synthesizer",
                    "latency": latency,
                    "is_cached": False,
                    "status": "SUCCESS",
                }

            latency = round(time.time() - start_time, 3)
            return {
                "answer": INSUFFICIENT_EVIDENCE_RESPONSE,
                "sources": [],
                "provider": "Offline Engine",
                "latency": latency,
                "is_cached": False,
                "status": "INSUFFICIENT_EVIDENCE",
            }

        # 3. Live LLM Generation
        prompt = GROUNDED_QA_TEMPLATE.format(context=formatted_context, query=query)
        last_error = None

        # Explicit user choice: "Groq API" in the sidebar.
        if preferred_provider == "groq" and groq_key:
            try:
                raw_answer = self._call_groq(prompt, LEGAL_SYSTEM_PROMPT, groq_key)
                formatted = format_response_with_citations(raw_answer, sources, include_disclaimer=True)
                latency = round(time.time() - start_time, 3)
                return {
                    "answer": formatted,
                    "sources": sources,
                    "provider": f"Live LLM (Groq: {self.groq_model})",
                    "latency": latency,
                    "is_cached": False,
                    "status": "SUCCESS",
                }
            except Exception as e:
                last_error = f"Groq Error: {e}"
                logger.warning(last_error)

        # Prioritize OpenRouter if openrouter_key is provided and preferred or Groq key is absent.
        # Groq API keys conventionally start with "gsk_"; used the same way the
        # old "AIza" prefix check worked for Gemini, as a cheap validity signal.
        if preferred_provider == "openrouter" or (openrouter_key and not groq_key.startswith("gsk_")):
            try:
                raw_answer = self._call_openrouter(prompt, LEGAL_SYSTEM_PROMPT, openrouter_key)
                formatted = format_response_with_citations(raw_answer, sources, include_disclaimer=True)
                latency = round(time.time() - start_time, 3)
                return {
                    "answer": formatted,
                    "sources": sources,
                    "provider": f"Live LLM (OpenRouter: {self.openrouter_model})",
                    "latency": latency,
                    "is_cached": False,
                    "status": "SUCCESS",
                }
            except Exception as e:
                last_error = f"OpenRouter Error: {e}"
                logger.warning(last_error)

        # Try Groq API if key is available (skip if the explicit groq-first
        # branch above already tried and failed — no point calling it twice)
        if groq_key and preferred_provider != "groq":
            try:
                raw_answer = self._call_groq(prompt, LEGAL_SYSTEM_PROMPT, groq_key)
                formatted = format_response_with_citations(raw_answer, sources, include_disclaimer=True)
                latency = round(time.time() - start_time, 3)
                return {
                    "answer": formatted,
                    "sources": sources,
                    "provider": f"Live LLM (Groq: {self.groq_model})",
                    "latency": latency,
                    "is_cached": False,
                    "status": "SUCCESS",
                }
            except Exception as e:
                last_error = f"Groq Error: {e}"
                logger.warning(last_error)

        # Secondary try: If Groq failed and OpenRouter key is available
        if openrouter_key and "OpenRouter" not in (last_error or ""):
            try:
                raw_answer = self._call_openrouter(prompt, LEGAL_SYSTEM_PROMPT, openrouter_key)
                formatted = format_response_with_citations(raw_answer, sources, include_disclaimer=True)
                latency = round(time.time() - start_time, 3)
                return {
                    "answer": formatted,
                    "sources": sources,
                    "provider": f"Live LLM (OpenRouter Fallback)",
                    "latency": latency,
                    "is_cached": False,
                    "status": "SUCCESS",
                }
            except Exception as e:
                last_error = f"OpenRouter Fallback Error: {e}"

        # 4. Fallback on API Error: Check deterministic demo cache
        cached = get_cached_demo_response(query)
        if cached:
            latency = round(time.time() - start_time, 3)
            return {
                "answer": cached["answer"],
                "sources": cached["sources"],
                "provider": "Offline Demo Fallback (Recovered from API Error)",
                "latency": latency,
                "is_cached": True,
                "status": "SUCCESS",
                "api_error": last_error,
            }

        # Safe error message if no cache available
        latency = round(time.time() - start_time, 3)
        return {
            "answer": (
                "⚠️ **Service Temporarily Unavailable**\n\n"
                "Unable to connect to live LLM generation service. "
                "The system has safely intercepted the network error to prevent incorrect answers. "
                "Please enable Offline Demo Mode in the sidebar or check your API key."
            ),
            "sources": sources,
            "provider": "Safe Error Fallback",
            "latency": latency,
            "is_cached": False,
            "status": "API_ERROR",
            "error_detail": last_error,
        }