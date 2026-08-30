"""
Diagnostic script — run from D:\\Chat_Bot with:
    python diagnose_retriever.py

Imports the REAL src.retriever and src.config from your project and reports
exactly what got indexed, so we can see ground truth instead of guessing.
"""
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import KNOWLEDGE_BASE_DIR, METADATA_DIR
from src.retriever import HybridRetriever

print(f"KNOWLEDGE_BASE_DIR = {KNOWLEDGE_BASE_DIR}")
print(f"  exists: {KNOWLEDGE_BASE_DIR.exists()}")
print()

print("All .txt files found under knowledge_base/ (recursive):")
all_txt = sorted(KNOWLEDGE_BASE_DIR.rglob("*.txt"))
if not all_txt:
    print("  ** NONE FOUND ** — this is the bug. Check the files actually")
    print("  live under knowledge_base/<folder>/*.txt on disk.")
for f in all_txt:
    rel = f.relative_to(KNOWLEDGE_BASE_DIR)
    size = f.stat().st_size
    print(f"  {rel}  ({size} bytes)")
print()

print("Building retriever index (this is exactly what the app does)...")
r = HybridRetriever()
print(f"Total chunks indexed: {len(r.chunks)}")
print()

print("Chunks per source_id:")
counts = Counter(c.source_id for c in r.chunks)
for source_id, n in sorted(counts.items()):
    print(f"  {source_id}: {n} chunk(s)")
print()

# Flag any file that produced zero chunks
indexed_files = set()
for c in r.chunks:
    pass  # LegalChunk doesn't store file path, so we cross-check by source_id below

print("Checking for consumer/cyber/employment/domestic/tenancy content specifically:")
target_ids = [c.source_id for c in r.chunks if c.source_id.startswith((
    "CPA", "ECOM", "IT-ACT", "DPDP", "POSH", "LABOUR", "PWDVA", "MAINTENANCE",
    "RERA", "MODEL-TENANCY"
))]
if not target_ids:
    print("  ** ZERO chunks from any new-domain source_id **")
    print("  This means either the files weren't found, or _chunk_document()")
    print("  produced no valid paragraphs (e.g. body <30 chars, or headers")
    print("  weren't parsed correctly, or content is all on one line with no")
    print("  blank-line paragraph breaks).")
else:
    print(f"  Found {len(target_ids)} chunk(s): {Counter(target_ids)}")
print()

print("Test query: 'What does the Consumer Protection Act 2019 say about unfair trade practices?'")
result = r.retrieve("What does the Consumer Protection Act 2019 say about unfair trade practices?")
print(f"  max_score: {result['max_score']}  is_sufficient: {result['is_sufficient']}")
for chunk in result["chunks"]:
    print(f"  -> {chunk['source_id']} (score={chunk['score']}): {chunk['text'][:80]}...")