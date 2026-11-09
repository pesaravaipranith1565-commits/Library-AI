"""End-to-end test for Streamlit app services"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database import seed_database, BookDB, StudentDB, ReservationDB, WaitlistDB
from services.granite_service import understand_query, generate_agent_response, generate_recommendations, analyze_syllabus

def test_database():
    seed_database()
    books = BookDB.all()
    students = StudentDB.all()
    assert len(books) >= 75, f"Expected >=75 books, got {len(books)}"
    assert len(students) >= 3, f"Expected >=3 students, got {len(students)}"
    subjects = list({b["subject"] for b in books})
    assert len(subjects) >= 14, f"Expected >=14 subjects, got {len(subjects)}"
    print(f"  DB: {len(books)} books, {len(subjects)} subjects, {len(students)} students - PASS")

    # Search
    py_books = BookDB.all(search="python")
    assert len(py_books) >= 1, "Python search failed"
    print(f"  Search 'python': {len(py_books)} result(s) - PASS")

    # Subject filter
    cs_books = BookDB.all(subject="Computer Science")
    assert len(cs_books) >= 5
    print(f"  Subject filter 'Computer Science': {len(cs_books)} books - PASS")

    # Available filter
    avail = BookDB.all(available_only=True)
    assert all(b["availableCopies"] > 0 for b in avail)
    print(f"  Available filter: {len(avail)} available books - PASS")

    # Semantic search
    ml_books = BookDB.semantic_search(["machine learning", "deep learning"])
    assert len(ml_books) >= 1
    print(f"  Semantic search: {len(ml_books)} ML books - PASS")

    # Popular
    popular = BookDB.popular(5)
    assert len(popular) == 5
    print(f"  Popular books: top={popular[0]['title'][:30]} - PASS")

    # Student by email
    alex = StudentDB.get_by_email("alex.johnson@university.edu")
    assert alex is not None
    print(f"  Get student by email: {alex['name']} - PASS")

    return alex

def test_reservations(student):
    books = BookDB.all(available_only=True)
    book = books[0]
    
    # Create reservation
    before_avail = book["availableCopies"]
    ok = BookDB.decrement_available(book["id"])
    assert ok, "decrement_available failed"
    res = ReservationDB.create(student["id"], book["id"], book["title"], student["name"])
    assert res["status"] == "active"
    print(f"  Reservation created: '{book['title'][:30]}' - PASS")

    # Has active check
    assert ReservationDB.has_active(student["id"], book["id"])
    print(f"  has_active check - PASS")

    # Active list
    active = ReservationDB.active_for_student(student["id"])
    assert len(active) >= 1
    print(f"  Active reservations: {len(active)} - PASS")

    # Cancel
    ReservationDB.cancel(res["id"])
    BookDB.increment_available(book["id"])
    after_avail = BookDB.get(book["id"])["availableCopies"]
    assert after_avail == before_avail, f"Copy count not restored: {before_avail} -> {after_avail}"
    print(f"  Cancel + copy restore: {before_avail} -> {after_avail} - PASS")

    return book

def test_waitlist(student, book):
    # Find an unavailable book
    unavail_books = [b for b in BookDB.all() if b["availableCopies"] == 0]
    if not unavail_books:
        print("  Waitlist: no unavailable books, skipping")
        return
    
    ubook = unavail_books[0]
    entry = WaitlistDB.join(ubook["id"], student["id"])
    assert entry["position"] >= 1
    print(f"  Joined waitlist: pos #{entry['position']} for '{ubook['title'][:30]}' - PASS")

    assert WaitlistDB.is_on_waitlist(ubook["id"], student["id"])
    print(f"  is_on_waitlist check - PASS")

    WaitlistDB.leave(ubook["id"], student["id"])
    assert not WaitlistDB.is_on_waitlist(ubook["id"], student["id"])
    print(f"  Leave waitlist - PASS")

def test_granite_nlp():
    print("\n  Testing IBM Granite NLP...")
    
    # Test 1: search_book intent
    r = understand_query("I need books about machine learning")
    assert r["intent"] in ["search_book", "get_recommendation"], f"Bad intent: {r['intent']}"
    print(f"  NLP search_book: intent={r['intent']}, subject={r['subject']} - PASS")

    # Test 2: availability
    r2 = understand_query("Is Introduction to Algorithms available?")
    assert r2["intent"] == "check_availability", f"Expected check_availability, got {r2['intent']}"
    print(f"  NLP check_availability: bookTitle={r2.get('bookTitle')} - PASS")

    # Test 3: recommendation with profile
    r3 = understand_query("Recommend books for my courses", {"major": "Data Science", "year": 2, "currentCourses": ["ML", "Stats"]})
    assert r3["intent"] in ["get_recommendation", "search_book"]
    print(f"  NLP recommendation: intent={r3['intent']} - PASS")

    # Test 4: agent response
    resp = generate_agent_response("What is the best book for learning Python?", {"major": "Computer Science"})
    assert len(resp) > 10, "Empty agent response"
    print(f"  Agent response: '{resp[:60]}...' - PASS")

    # Test 5: recommendations
    student = StudentDB.get_by_email("maria.garcia@university.edu")
    books = BookDB.all()
    rec = generate_recommendations(student, books, "data analysis")
    assert len(rec) > 20
    print(f"  Recommendations: '{rec[:60]}...' - PASS")

    # Test 6: syllabus analysis
    syllabus = """
    CS401 - Machine Learning
    Required: Hands-On Machine Learning by Aurélien Géron
    Recommended: Deep Learning by Goodfellow
    Topics: neural networks, gradient descent, supervised learning
    """
    analysis = analyze_syllabus(syllabus)
    assert isinstance(analysis, dict)
    assert "required" in analysis
    print(f"  Syllabus analysis: {len(analysis.get('required',[]))} required, topics={analysis.get('topics',[])} - PASS")

if __name__ == "__main__":
    print("=" * 60)
    print("Library AI Agent — Streamlit End-to-End Test")
    print("=" * 60)

    print("\n📦 Testing Database Layer...")
    student = test_database()

    print("\n📌 Testing Reservations & Waitlists...")
    book = test_reservations(student)
    test_waitlist(student, book)

    print("\n🤖 Testing IBM Granite (watsonx.ai)...")
    test_granite_nlp()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nRun the Streamlit app with:")
    print("  cd streamlit_app && streamlit run app.py")
