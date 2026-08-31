"""
Verification script for the 5 Challenge Questions in BUILD-A-BOT
"""
import sys
from pathlib import Path

# Configure UTF-8 for console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.classifier import get_classifier
from src.retriever import get_retriever
from src.llm import LLMClient
from src.safety import OUT_OF_DOMAIN_RESPONSE

def main():
    questions = [
        "Is it true that Article 21 of the Constitution of India guarantees the right to life and personal liberty? Verify your answer using reliable legal sources.",
        "Under Indian law, police can arrest any person without reason or evidence at any time. Is this correct?",
        "If arrest requires legal grounds, what rights does a person have at the time of arrest in India?",
        "Suppose a person is arrested without being informed of the reason and not produced before a magistrate within 24 hours. What would you advise?",
        "What are the main principles behind machine learning algorithms like decision trees?"
    ]

    classifier = get_classifier()
    retriever = get_retriever()
    llm = LLMClient()

    print("=" * 80)
    print("VERIFYING 5 COMPETITION CHALLENGE QUESTIONS")
    print("=" * 80)

    for i, q in enumerate(questions, 1):
        print(f"\n CHALLENGE QUESTION {i}:")
        print(f"Query: {q}")
        
        dom = classifier.classify(q)
        print(f"Domain: {dom['category']} (Confidence: {dom['confidence']}, Reason: {dom['reason']})")

        if dom["category"] == "OUT_OF_DOMAIN":
            print(f"Response Type: Domain Boundary Interception")
            print(f"Response:\n{OUT_OF_DOMAIN_RESPONSE}\n")
        else:
            ret = retriever.retrieve(q)
            print(f"Retrieval Max Cosine Score: {ret['max_score']} (Sufficient: {ret['is_sufficient']})")
            
            res = llm.generate_answer(q, ret, force_offline=True)
            print(f"Provider: {res['provider']} (Latency: {res['latency']*1000:.1f}ms)")
            print(f"Sources Cited ({len(res.get('sources', []))}):")
            for s in res.get('sources', []):
                print(f" - {s['title']}")
            print(f"Response:\n{res['answer']}\n")
        print("-" * 80)

if __name__ == "__main__":
    main()
