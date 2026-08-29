"""
Configuration module for Indian Legal Assistant Chatbot
Handles paths, model settings, retrieval thresholds, and environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
CONSTITUTION_DIR = KNOWLEDGE_BASE_DIR / "constitution"
ARREST_DIR = KNOWLEDGE_BASE_DIR / "arrest_and_detention"
METADATA_DIR = KNOWLEDGE_BASE_DIR / "metadata"
SOURCES_JSON_PATH = METADATA_DIR / "sources.json"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"

# Ensure directories exist
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY", "")

# LLM Parameters
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "1024"))

# Retrieval & Thresholds
EVIDENCE_THRESHOLD = float(os.getenv("EVIDENCE_THRESHOLD", "0.10"))
TOP_K_CHUNKS = int(os.getenv("TOP_K_CHUNKS", "3"))

# Demo & Reliability
FALLBACK_TO_OFFLINE_DEMO = os.getenv("FALLBACK_TO_OFFLINE_DEMO", "true").lower() == "true"
SYSTEM_DOMAIN = "Indian Constitutional Law & Arrest/Detention Rights"