"""
Safety, Compliance, and Citation Verification Module for Indian Legal Assistant Chatbot
Applies legal disclaimers, crisis escalation, and verifies citations against retrieved metadata.
"""
from typing import List, Dict, Any

STANDARD_LEGAL_DISCLAIMER = (
    " **Legal Disclaimer**: This response provides general legal information based on verified Indian "
    "statutes and constitutional provisions retrieved by this system. It does not constitute formal legal "
    "advice or attorney-client representation. For specific legal emergencies, please consult a qualified "
    "advocate or contact your District Legal Services Authority (DLSA)."
)

OUT_OF_DOMAIN_RESPONSE = (
    " **Domain Boundary Notice**\n\n"
    "Your query appears to be outside LUMA’s **legal domain**.\n\n"
    "I am **LUMA**, an AI assistant specialized strictly in **Laws , Articles , Rights , Rules and Regulations**.\n\n"
    "You can ask me about:\n \n"
    "**Constitutional rights**, **arrest & detention**, **consumer protection**, **cyber law & privacy**, **workplace rights (POSH)**, **tenancy & property**, and **family law**\n\n"
)

OUT_OF_SCOPE_LEGAL_RESPONSE = (
    " **Knowledge Base Limitation**\n\n"
    "While your question appears to be related to law, it falls outside my verified knowledge base (which is focused on "
    "Indian Constitutional Rights, Fundamental Freedoms, and Arrest/Detention Safeguards under CrPC/BNSS).\n\n"
    "I am restricted from answering untested areas of law (such as Corporate Tax, Patents, or Foreign Law) to ensure 100% "
    "verifiable accuracy without hallucination."
)

INSUFFICIENT_EVIDENCE_RESPONSE = (
    " **Insufficient Evidence in Verified Knowledge Base**\n\n"
    "I could not locate sufficient verified legal evidence in my indexed knowledge base to answer this query factually. "
    "To prevent hallucinating non-existent laws, acts, or constitutional provisions (such as fabricated article numbers or fictional acts), "
    "I cannot provide an unverified response.\n\n"
    " *Please check the official Constitution of India or India Code repository (https://indiacode.nic.in).* "
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
    Appends structured citation metadata to the generated response.

    Sources are wrapped in an HTML <details>/<summary> accordion that is
    collapsed by default ("📑 View Sources") and expands smoothly on click.
    Streamlit renders this correctly when st.markdown(..., unsafe_allow_html=True)
    is used in app.py.

    NOTE: The standard legal disclaimer is intentionally no longer appended
    per-message here — it is shown once as a fixed caption beneath the chat
    input. `include_disclaimer` is kept in the signature so existing call
    sites in llm.py don't need to change; the argument is now a no-op.
    """
    parts = [answer.strip()]

    if sources:
        # Build the inner source list as HTML list items
        items_html = ""
        for idx, src in enumerate(sources, 1):
            title = src.get("title", "Unknown Source")
            authority = src.get("authority", "Government of India")
            url = src.get("url", "#")
            url_label = src.get("url", "Official Document")
            items_html += (
                f"<li style='margin-bottom:10px;'>"
                f"<strong>{idx}. {title}</strong><br>"
                f"<span style='color:#a0a0a0;font-size:0.88rem;'>"
                f"Authority: {authority}</span><br>"
                f"<a href='{url}' target='_blank' "
                f"style='color:#60a5fa;font-size:0.88rem;text-decoration:none;'>"
                f"🔗 {url_label}</a>"
                f"</li>"
            )

        accordion_html = f"""
<details style="margin-top:18px;">
  <summary style="
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      list-style: none;
      padding: 6px 14px;
      border-radius: 7px;
      border: 1px solid rgba(255,255,255,0.12);
      background: #111214;
      color: #f5f5f5;
      font-size: 0.85rem;
      font-weight: 600;
      user-select: none;
      transition: background 0.15s, border-color 0.15s;
  "
  onmouseover="this.style.borderColor='#3b82f6';this.style.background='#16181d';"
  onmouseout="this.style.borderColor='rgba(255,255,255,0.12)';this.style.background='#111214';"
  >
     View Sources <span style="color:#8a8a8a;font-weight:400;">({len(sources)} cited)</span>
  </summary>
  <div style="
      margin-top: 12px;
      padding: 14px 16px;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,0.08);
      background: #0c0c0d;
  ">
    <p style="margin:0 0 10px 0;font-size:0.8rem;color:#8a8a8a;letter-spacing:0.04em;text-transform:uppercase;">
      Verified Sources Cited
    </p>
    <ol style="margin:0;padding-left:18px;color:#e0e0e0;font-size:0.9rem;line-height:1.7;">
      {items_html}
    </ol>
  </div>
</details>"""

        parts.append(accordion_html)

    return "\n".join(parts)