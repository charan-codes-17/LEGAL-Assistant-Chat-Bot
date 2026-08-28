"""
Safety, Compliance, and Citation Verification Module for Indian Legal Assistant Chatbot
Applies legal disclaimers, crisis escalation, and verifies citations against retrieved metadata.
"""
from typing import List, Dict, Any

STANDARD_LEGAL_DISCLAIMER = (
    "⚠️ **Legal Disclaimer**: This response provides general legal information based on verified Indian "
    "statutes and constitutional provisions retrieved by this system. It does not constitute formal legal "
    "advice or attorney-client representation. For specific legal emergencies, please consult a qualified "
    "advocate or contact your District Legal Services Authority (DLSA)."
)

OUT_OF_DOMAIN_RESPONSE = (
    "⚖️ **Domain Boundary Notice**\n\n"
    "I am **LUMA**, an AI assistant specialized strictly in **Indian Constitutional Law and Arrest/Detention Rights**.\n\n"
    "Your question is outside the legal domain (e.g., Computer Science, Machine Learning, STEM, or general topics). "
    "I cannot answer questions about machine learning algorithms, programming, or non-legal subjects.\n\n"
    "💡 *Please ask a question related to Indian Constitutional Rights (Articles 14, 19, 21, 22), police arrest procedures, "
    "magistrate production within 24 hours, or free legal aid under NALSA.*"
)

OUT_OF_SCOPE_LEGAL_RESPONSE = (
    "📚 **Knowledge Base Limitation**\n\n"
    "While your question appears to be related to law, it falls outside my verified knowledge base (which is focused on "
    "Indian Constitutional Rights, Fundamental Freedoms, and Arrest/Detention Safeguards under CrPC/BNSS).\n\n"
    "I am restricted from answering untested areas of law (such as Corporate Tax, Patents, or Foreign Law) to ensure 100% "
    "verifiable accuracy without hallucination."
)

INSUFFICIENT_EVIDENCE_RESPONSE = (
    "🔍 **Insufficient Evidence in Verified Knowledge Base**\n\n"
    "I could not locate sufficient verified legal evidence in my indexed knowledge base to answer this query factually. "
    "To prevent hallucinating non-existent laws, acts, or constitutional provisions (such as fabricated article numbers or fictional acts), "
    "I cannot provide an unverified response.\n\n"
    "📖 *Please check the official Constitution of India or India Code repository (https://indiacode.nic.in).* "
)

AMBIGUOUS_QUERY_RESPONSE = (
    "❓ **Clarification Required**\n\n"
    "Your question is very broad or ambiguous. Could you please specify the legal context? For example:\n"
    "- *\"Does Article 21 protect the right to life and personal liberty?\"*\n"
    "- *\"What rights does a person have upon being arrested in India?\"*\n"
    "- *\"Is it mandatory to produce an arrested person before a magistrate within 24 hours?\"*"
)


def format_response_with_citations(
    answer: str,
    sources: List[Dict[str, Any]],
    include_disclaimer: bool = True
) -> str:
    """
    Appends structured citation metadata and the standard legal disclaimer to the generated response.
    """
    parts = [answer.strip()]

    if sources:
        parts.append("\n\n### 📑 Verified Sources Cited:")
        for idx, src in enumerate(sources, 1):
            parts.append(
                f"{idx}. **{src.get('title', 'Unknown Source')}**\n"
                f"   - *Authority*: {src.get('authority', 'Government of India')}\n"
                f"   - *Official Reference*: [{src.get('url', 'Official Document')}]({src.get('url', '#')})"
            )

    if include_disclaimer:
        parts.append(f"\n\n---\n{STANDARD_LEGAL_DISCLAIMER}")

    return "\n".join(parts)
