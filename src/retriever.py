"""
Hybrid Vector Retriever Module for Indian Legal Assistant Chatbot
Implements chunking, vector indexing, cosine similarity scoring, and evidence thresholding.
Zero heavy dependencies required: works instantly offline and online.
"""
import os
import json
import re
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

from src.config import (
    CONSTITUTION_DIR,
    ARREST_DIR,
    SOURCES_JSON_PATH,
    EVIDENCE_THRESHOLD,
    TOP_K_CHUNKS,
)


class LegalChunk:
    def __init__(self, text: str, source_id: str, title: str, url: str, authority: str, chunk_index: int):
        self.text = text.strip()
        self.source_id = source_id
        self.title = title
        self.url = url
        self.authority = authority
        self.chunk_index = chunk_index

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source_id": self.source_id,
            "title": self.title,
            "url": self.url,
            "authority": self.authority,
            "chunk_index": self.chunk_index,
        }


class HybridRetriever:
    """
    High-resilience vector & semantic retriever designed for competition-grade stability.
    Uses TF-IDF / Sublinear Term-Weighting vector space model with subword n-gram overlap
    and cosine similarity, providing deterministic, instant, zero-latency retrieval.
    """

    def __init__(self, threshold: float = EVIDENCE_THRESHOLD):
        self.threshold = threshold
        self.chunks: List[LegalChunk] = []
        self.sources_catalog: Dict[str, Dict[str, Any]] = {}
        self.vocabulary: Dict[str, int] = {}
        self.idf: np.ndarray = np.array([])
        self.chunk_vectors: np.ndarray = np.array([])
        self._load_sources_catalog()
        self._build_index()

    def _load_sources_catalog(self):
        if SOURCES_JSON_PATH.exists():
            with open(SOURCES_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("sources", []):
                    self.sources_catalog[item["id"]] = item

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, alphanumeric extraction + legal term expansions
        tokens = re.findall(r"\b[a-zA-Z0-9_\-\.\/]+\b", text.lower())
        # Add bigrams for key legal phrases (e.g., 'article 21', 'legal aid', '24 hours', 'magistrate production')
        bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
        return tokens + bigrams

    def _chunk_document(self, file_path: Path) -> List[LegalChunk]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract header metadata
        source_id = "UNKNOWN"
        title = file_path.stem
        url = "Official Legal Portal"
        authority = "Government of India"

        source_match = re.search(r"\[SOURCE_ID:\s*([^\]]+)\]", content)
        if source_match:
            source_id = source_match.group(1).strip()

        title_match = re.search(r"\[TITLE:\s*([^\]]+)\]", content)
        if title_match:
            title = title_match.group(1).strip()

        url_match = re.search(r"\[URL:\s*([^\]]+)\]", content)
        if url_match:
            url = url_match.group(1).strip()

        auth_match = re.search(r"\[AUTHORITY:\s*([^\]]+)\]", content)
        if auth_match:
            authority = auth_match.group(1).strip()

        # Clean content removing bracket headers
        clean_body = re.sub(r"\[[A-Z_]+:\s*[^\]]+\]\n*", "", content).strip()

        # Chunk by logical sections/paragraphs
        raw_paragraphs = [p.strip() for p in clean_body.split("\n\n") if len(p.strip()) > 30]
        chunks = []
        for idx, p in enumerate(raw_paragraphs):
            chunks.append(LegalChunk(p, source_id, title, url, authority, idx))
        return chunks

    def _build_index(self):
        self.chunks = []
        doc_files = list(CONSTITUTION_DIR.glob("*.txt")) + list(ARREST_DIR.glob("*.txt"))
        for doc_file in doc_files:
            self.chunks.extend(self._chunk_document(doc_file))

        if not self.chunks:
            return

        # Build vocabulary
        doc_token_lists = [self._tokenize(chunk.text) for chunk in self.chunks]
        all_tokens = set()
        for t_list in doc_token_lists:
            all_tokens.update(t_list)

        self.vocabulary = {token: idx for idx, token in enumerate(sorted(all_tokens))}
        vocab_size = len(self.vocabulary)
        num_docs = len(self.chunks)

        # Compute Document Frequencies
        df = np.zeros(vocab_size)
        for t_list in doc_token_lists:
            seen = set()
            for t in t_list:
                if t in self.vocabulary and t not in seen:
                    df[self.vocabulary[t]] += 1
                    seen.add(t)

        # Smooth IDF
        self.idf = np.log((num_docs + 1) / (df + 1)) + 1.0

        # Compute TF-IDF matrix for all chunks
        matrix = np.zeros((num_docs, vocab_size))
        for doc_idx, t_list in enumerate(doc_token_lists):
            tf_dict = {}
            for t in t_list:
                if t in self.vocabulary:
                    idx = self.vocabulary[t]
                    tf_dict[idx] = tf_dict.get(idx, 0) + 1
            for term_idx, count in tf_dict.items():
                matrix[doc_idx, term_idx] = (1 + math.log(count)) * self.idf[term_idx]

        # Normalize rows to unit length for cosine similarity
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.chunk_vectors = matrix / norms

    def retrieve(self, query: str, top_k: int = TOP_K_CHUNKS) -> Dict[str, Any]:
        """
        Retrieves top relevant legal chunks and evaluates similarity against the evidence threshold.
        """
        if not self.chunks or not query.strip():
            return {
                "chunks": [],
                "max_score": 0.0,
                "is_sufficient": False,
                "sources": [],
                "formatted_context": "No context available.",
            }

        # Vectorize query
        q_tokens = self._tokenize(query)
        q_vec = np.zeros(len(self.vocabulary))
        tf_dict = {}
        for t in q_tokens:
            if t in self.vocabulary:
                idx = self.vocabulary[t]
                tf_dict[idx] = tf_dict.get(idx, 0) + 1

        for term_idx, count in tf_dict.items():
            q_vec[term_idx] = (1 + math.log(count)) * self.idf[term_idx]

        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return {
                "chunks": [],
                "max_score": 0.0,
                "is_sufficient": False,
                "sources": [],
                "formatted_context": "No matching legal terms found.",
            }

        q_vec_norm = q_vec / q_norm

        # Cosine similarity against all chunks
        scores = np.dot(self.chunk_vectors, q_vec_norm)

        # Sort indices by score descending
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        unique_sources = {}
        max_score = float(scores[top_indices[0]]) if len(top_indices) > 0 else 0.0

        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.05:  # filter negligible noise
                chunk = self.chunks[idx]
                chunk_dict = chunk.to_dict()
                chunk_dict["score"] = round(score, 4)
                results.append(chunk_dict)

                if chunk.source_id not in unique_sources:
                    unique_sources[chunk.source_id] = {
                        "id": chunk.source_id,
                        "title": chunk.title,
                        "url": chunk.url,
                        "authority": chunk.authority,
                    }

        is_sufficient = max_score >= self.threshold

        # Format context string for LLM prompt
        context_parts = []
        for i, res in enumerate(results, 1):
            context_parts.append(
                f"[Document {i} - Source: {res['title']} | Score: {res['score']}]\n{res['text']}"
            )
        formatted_context = "\n\n".join(context_parts) if context_parts else "No relevant legal context found."

        return {
            "chunks": results,
            "max_score": round(max_score, 4),
            "is_sufficient": is_sufficient,
            "sources": list(unique_sources.values()),
            "formatted_context": formatted_context,
        }


# Singleton instance for quick import
_global_retriever = None


def get_retriever() -> HybridRetriever:
    global _global_retriever
    if _global_retriever is None:
        _global_retriever = HybridRetriever()
    return _global_retriever
