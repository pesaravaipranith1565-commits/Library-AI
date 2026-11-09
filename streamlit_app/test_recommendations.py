"""Quick test for the new summarize_book and recommend_by_topic functions"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database import BookDB, StudentDB, seed_database
from services.granite_service import summarize_book, recommend_by_topic

seed_database()
all_books = BookDB.all()
student = StudentDB.get_by_email("alex.johnson@university.edu")

print("=" * 60)
print("Testing IBM Granite: summarize_book + recommend_by_topic")
print("=" * 60)

# ── Test 1: Book summarization ─────────────────────────────────────────────
print("\n[TEST 1] summarize_book — Introduction to Algorithms")
book = all_books[0]
print(f"  Input: {book['title']} by {book['author']}")
summary = summarize_book(
    book["title"], book["author"],
    book.get("description", ""), book.get("tags", [])
)
assert len(summary) > 30, f"Summary too short: {len(summary)}"
print(f"  Output ({len(summary)} chars):")
print("  " + summary[:250].replace("\n", "\n  "))
print("  PASS")

# ── Test 2: Recommend by topic — CS / AI ─────────────────────────────────
print("\n[TEST 2] recommend_by_topic — 'machine learning neural networks'")
result = recommend_by_topic("machine learning and neural networks", all_books, student)
print(f"  Topic summary: {result.get('topic_summary','')[:100]}")
recs = result.get("recommendations", [])
assert len(recs) >= 3, f"Too few recs: {len(recs)}"
print(f"  Recommendations: {len(recs)}")
for r in recs:
    b = r.get("book")
    title = b["title"] if b else "?"
    why = r.get("why", "")[:80]
    print(f"    #{r['rank']} {title} — {why}")
print("  PASS")

# ── Test 3: Recommend by topic — History ─────────────────────────────────
print("\n[TEST 3] recommend_by_topic — 'history of ancient civilisations'")
result2 = recommend_by_topic("history of ancient civilisations", all_books)
recs2 = result2.get("recommendations", [])
assert len(recs2) >= 3, f"Too few recs: {len(recs2)}"
print(f"  Recommendations: {len(recs2)}")
for r in recs2:
    b = r.get("book")
    title = b["title"] if b else "?"
    subj  = b.get("subject", "") if b else ""
    print(f"    #{r['rank']} {title} [{subj}]")
print("  PASS")

# ── Test 4: Recommend by topic — Law ──────────────────────────────────────
print("\n[TEST 4] recommend_by_topic — 'contract law and legal obligations'")
result3 = recommend_by_topic("contract law and legal obligations", all_books)
recs3 = result3.get("recommendations", [])
assert len(recs3) >= 1, f"Too few recs: {len(recs3)}"
print(f"  Recommendations: {len(recs3)}")
for r in recs3:
    b = r.get("book")
    title = b["title"] if b else "?"
    print(f"    #{r['rank']} {title}")
print("  PASS")

# ── Test 5: Recommend by topic — Psychology ──────────────────────────────
print("\n[TEST 5] recommend_by_topic — 'cognitive biases and decision making'")
result4 = recommend_by_topic("cognitive biases and decision making", all_books)
recs4 = result4.get("recommendations", [])
assert len(recs4) >= 2
print(f"  Recommendations: {len(recs4)}")
for r in recs4:
    b = r.get("book")
    title = b["title"] if b else "?"
    print(f"    #{r['rank']} {title}")
print("  PASS")

print("\n" + "=" * 60)
print("ALL TESTS PASSED — IBM Granite recommendations + summaries OK")
print("=" * 60)
