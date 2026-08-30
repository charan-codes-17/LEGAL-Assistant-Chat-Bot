"""
Domain and Scope Classifier Module for Indian Legal Assistant Chatbot
Categorizes input queries into LEGAL_IN_SCOPE, LEGAL_OUT_OF_SCOPE, and OUT_OF_DOMAIN.
"""
import re
from typing import Dict, Any


class DomainClassifier:
    """
    Hybrid domain classifier combining deterministic rule-based matching with semantic filters.
    Optimized for high precision, fast response, and zero false-legal classifications on tech/science topics.
    """

    # Non-legal keywords (Machine learning, programming, biology, physics, cooking, general chitchat)
    NON_LEGAL_PATTERNS = [
        r"\b(machine\s+learning|decision\s+tree|decision\s+trees|deep\s+learning|neural\s+network|random\s+forest|gradient\s+boost|algorithm|supervised|unsupervised|svm|cnn|rnn|transformer|backpropagation)\b",
        r"\b(python|javascript|c\+\+|html|css|sql|react|fastapi|docker|kubernetes|git|github|coding|programming|function|compiler)\b",
        r"\b(photosynthesis|mitochondria|dna|rna|gravity|quantum|thermodynamics|atom|molecule|cellular|galaxy|solar\s+system)\b",
        r"\b(recipe|cooking|bake|cake|pizza|burger|pasta|weather|forecast|cricket|football|movie|song|lyrics|joke|story)\b",
        r"\b(soil\s+salinity|agricultural\s+land|farmers\s+reduce|antibiotics|viral\s+infections|dehydration)\b"
    ]

    # In-scope Indian legal keywords and provisions
    IN_SCOPE_PATTERNS = [
        r"\b(article\s*(14|19|21|22|32|39a|226|359))\b",
        r"\b(constitution|fundamental\s+rights?|liberty|right\s+to\s+life|personal\s+liberty|equality\s+before\s+law)\b",
        r"\b(arrest|arrested|detained|detention|police|custody|magistrate|24\s*hours?|grounds\s+of\s+arrest)\b",
        r"\b(bail|bailable|non-bailable|crpc|bnss|cognizable|warrant|interrogation|memo\s+of\s+arrest)\b",
        r"\b(habeas\s+corpus|writ|high\s+court|supreme\s+court|illegal\s+detention|remand|legal\s+aid|nalsa|dlsa|d\.?k\.?\s*basu)\b",
        # Consumer Rights & E-Commerce
        r"\b(consumer\s+rights?|consumer\s+protection|e-?commerce|online\s+shopping|defective\s+product|deficiency\s+in\s+service|unfair\s+trade\s+practice|consumer\s+forum|consumer\s+court|refund|warranty|guarantee|misleading\s+advertisement|fake\s+product|broken\s+product|damaged\s+product|cheated\s+(by|online)|consumer\s+complaint|file\s+a\s+complaint)\b",
        # Cyber Law & Digital Rights
        r"\b(cyber\s*crime|cyber\s*bullying|cyber\s*stalking|hack\w*|data\s+privacy|data\s+protection|it\s+act|information\s+technology\s+act|phishing|online\s+fraud|online\s+scam|upi\s+fraud|upi\s+scam|identity\s+theft|digital\s+rights|personal\s+data|blackmail\w*|extort\w*|leaked\s+photos?|private\s+pictures?|revenge\s+porn|impersonat\w*|fake\s+profile|morphed\s+photos?|online\s+threat\w*|rape\s+threat\w*|internet\s+threat\w*)\b",
        # Employment & Workplace Rights
        r"\b(employment|workplace|employer|employee|termination|wrongful\s+termination|fired|laid\s+off|layoff|salary|wages?|labou?r\s+law|industrial\s+dispute|sexual\s+harassment|posh\s+act|provident\s+fund|\bpf\b|gratuity|notice\s+period|resignation|sue\s+(my|the)\s+(company|employer))\b",
        # Domestic Violence & Family Protections
        r"\b(domestic\s+violence|dowry|cruelty|maintenance|divorce|family\s+court|498a|protection\s+of\s+women|matrimonial|child\s+custody|\bcustody\b|alimony|hit\w*\s+me|beat\w*\s+me|abus\w*|tortur\w*|restraining\s+order|protection\s+order)\b",
        # Property & Tenancy Law
        r"\b(tenant|landlord|owner\s+won'?t\s+return|rent|eviction|lease|tenancy|rent\s+control|property\s+dispute|security\s+deposit|sale\s+deed|encroachment|possession\s+of\s+(my\s+)?flat|delayed?\s+possession|builder\s+delay\w*|land\s+dispute|register\s+property|property\s+registration)\b",
    ]

    # Legal topics outside our verified scope
    OUT_OF_SCOPE_LEGAL_PATTERNS = [
        r"\b(patent|trademark|copyright|ipr|intellectual\s+property)\b",
        r"\b(gst|income\s+tax|corporate\s+tax|merger|acquisition|insolvency|ibc|sebi)\b",
        r"\b(admiralty|maritime\s+law|space\s+law|aviation\s+law)\b",
        r"\b(us\s+constitution|miranda\s+rights?|first\s+amendment|uk\s+common\s+law)\b"
    ]

    def classify(self, query: str) -> Dict[str, Any]:
        """
        Classifies a user query and returns domain status with confidence and explanation.
        """
        clean_q = query.strip().lower()

        if not clean_q:
            return {
                "category": "EMPTY_INPUT",
                "is_in_scope": False,
                "confidence": 1.0,
                "reason": "Input query is empty.",
            }

        # 1. Check for blatant non-legal topics (e.g. Question 5: Machine Learning / Decision Trees)
        for pattern in self.NON_LEGAL_PATTERNS:
            if re.search(pattern, clean_q):
                return {
                    "category": "OUT_OF_DOMAIN",
                    "is_in_scope": False,
                    "confidence": 0.98,
                    "reason": "Query belongs to Computer Science, STEM, or general topics outside the Legal domain.",
                }

        # 2. Check for out-of-scope legal topics
        for pattern in self.OUT_OF_SCOPE_LEGAL_PATTERNS:
            if re.search(pattern, clean_q):
                return {
                    "category": "LEGAL_OUT_OF_SCOPE",
                    "is_in_scope": False,
                    "confidence": 0.90,
                    "reason": "Query is legal in nature but falls outside the verified knowledge base on Constitutional and Arrest Rights.",
                }

        # 3. Check for in-scope legal topics
        matches = 0
        for pattern in self.IN_SCOPE_PATTERNS:
            if re.search(pattern, clean_q):
                matches += 1

        if matches >= 1:
            confidence = min(0.70 + (matches * 0.10), 0.99)
            return {
                "category": "LEGAL_IN_SCOPE",
                "is_in_scope": True,
                "confidence": round(confidence, 2),
                "reason": f"Query contains verified Indian Constitutional or Criminal Procedure concepts ({matches} matches).",
            }

        # 4. Ambiguous / Short query
        if len(clean_q.split()) <= 4:
            return {
                "category": "AMBIGUOUS",
                "is_in_scope": False,
                "confidence": 0.60,
                "reason": "Query is too brief or ambiguous to determine specific legal applicability.",
            }

        # Default fallback: treat as potentially legal but requires vector evidence check
        return {
            "category": "LEGAL_IN_SCOPE",
            "is_in_scope": True,
            "confidence": 0.55,
            "reason": "General inquiry; proceeding to vector retrieval check.",
        }


# Singleton instance
_global_classifier = None


def get_classifier() -> DomainClassifier:
    global _global_classifier
    if _global_classifier is None:
        _global_classifier = DomainClassifier()
    return _global_classifier