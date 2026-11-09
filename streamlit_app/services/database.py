"""
Library AI Agent — Database layer
JSON file-based persistence (compatible with the Node.js LowDB data format).
"""

import json
import os
import uuid
from datetime import datetime, timedelta
import streamlit as st

# ── Path resolution ────────────────────────────────────────────────────────────

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_BASE_DIR, "data", "db.json")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

_DEFAULT_DB = {"books": [], "students": [], "reservations": [], "waitlists": [], "chatHistory": []}

# ── Low-level I/O ──────────────────────────────────────────────────────────────

def _load_db() -> dict:
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all keys exist
                for k, v in _DEFAULT_DB.items():
                    data.setdefault(k, v)
                return data
        except Exception:
            pass
    return dict(_DEFAULT_DB)


def _save_db(data: dict):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Books ──────────────────────────────────────────────────────────────────────

class BookDB:
    @staticmethod
    def all(search: str = "", subject: str = "", available_only: bool = False) -> list:
        db = _load_db()
        books = db["books"]
        if search:
            q = search.lower()
            books = [
                b for b in books
                if q in b.get("title", "").lower()
                or q in b.get("author", "").lower()
                or q in b.get("subject", "").lower()
                or any(q in t.lower() for t in b.get("tags", []))
                or q in b.get("description", "").lower()
            ]
        if subject:
            books = [b for b in books if b.get("subject", "").lower() == subject.lower()]
        if available_only:
            books = [b for b in books if b.get("availableCopies", 0) > 0]
        return books

    @staticmethod
    def get(book_id: str) -> dict | None:
        return next((b for b in _load_db()["books"] if b["id"] == book_id), None)

    @staticmethod
    def subjects() -> list:
        return sorted({b["subject"] for b in _load_db()["books"] if b.get("subject")})

    @staticmethod
    def popular(limit: int = 10) -> list:
        books = _load_db()["books"]
        return sorted(books, key=lambda b: b.get("borrowedCount", 0), reverse=True)[:limit]

    @staticmethod
    def get_by_subject(subject: str) -> list:
        return [b for b in _load_db()["books"] if b.get("subject", "").lower() == subject.lower()]

    @staticmethod
    def semantic_search(keywords: list) -> list:
        if not keywords:
            return []
        db = _load_db()
        results = []
        seen = set()
        for book in db["books"]:
            text = " ".join([
                book.get("title", ""), book.get("author", ""),
                book.get("subject", ""), book.get("description", ""),
                " ".join(book.get("tags", [])),
            ]).lower()
            if any(kw.lower() in text for kw in keywords) and book["id"] not in seen:
                results.append(book)
                seen.add(book["id"])
        return results

    @staticmethod
    def decrement_available(book_id: str) -> bool:
        db = _load_db()
        for book in db["books"]:
            if book["id"] == book_id and book.get("availableCopies", 0) > 0:
                book["availableCopies"] -= 1
                book["borrowedCount"] = book.get("borrowedCount", 0) + 1
                _save_db(db)
                return True
        return False

    @staticmethod
    def increment_available(book_id: str):
        db = _load_db()
        for book in db["books"]:
            if book["id"] == book_id:
                book["availableCopies"] = min(
                    book.get("availableCopies", 0) + 1,
                    book.get("totalCopies", 1)
                )
                _save_db(db)
                return

    @staticmethod
    def create(data: dict) -> dict:
        db = _load_db()
        book = {
            "id": str(uuid.uuid4()),
            "totalCopies": data.get("totalCopies", 1),
            "availableCopies": data.get("availableCopies", data.get("totalCopies", 1)),
            "borrowedCount": data.get("borrowedCount", 0),
            "reservationCount": 0,
            "createdAt": datetime.utcnow().isoformat(),
            **data,
        }
        db["books"].append(book)
        _save_db(db)
        return book


# ── Students ───────────────────────────────────────────────────────────────────

class StudentDB:
    @staticmethod
    def all() -> list:
        return _load_db()["students"]

    @staticmethod
    def get(student_id: str) -> dict | None:
        return next((s for s in _load_db()["students"] if s["id"] == student_id), None)

    @staticmethod
    def get_by_email(email: str) -> dict | None:
        return next((s for s in _load_db()["students"] if s.get("email", "").lower() == email.lower()), None)

    @staticmethod
    def create(data: dict) -> dict:
        db = _load_db()
        student = {
            "id": str(uuid.uuid4()),
            "borrowedBooks": [],
            "reservedBooks": [],
            "waitlistBooks": [],
            "readingHistory": [],
            "preferences": data.get("preferences", {}),
            "createdAt": datetime.utcnow().isoformat(),
            **data,
            "email": data.get("email", "").lower(),
        }
        db["students"].append(student)
        _save_db(db)
        return student

    @staticmethod
    def update(student_id: str, updates: dict) -> dict | None:
        db = _load_db()
        for s in db["students"]:
            if s["id"] == student_id:
                s.update(updates)
                _save_db(db)
                return s
        return None

    @staticmethod
    def add_to_history(student_id: str, book_id: str):
        db = _load_db()
        for s in db["students"]:
            if s["id"] == student_id:
                history = s.get("readingHistory", [])
                if book_id not in history:
                    s["readingHistory"] = history + [book_id]
                _save_db(db)
                return


# ── Reservations ───────────────────────────────────────────────────────────────

class ReservationDB:
    @staticmethod
    def all_for_student(student_id: str) -> list:
        return [r for r in _load_db()["reservations"] if r["studentId"] == student_id]

    @staticmethod
    def active_for_student(student_id: str) -> list:
        return [r for r in _load_db()["reservations"]
                if r["studentId"] == student_id and r.get("status") == "active"]

    @staticmethod
    def get(reservation_id: str) -> dict | None:
        return next((r for r in _load_db()["reservations"] if r["id"] == reservation_id), None)

    @staticmethod
    def has_active(student_id: str, book_id: str) -> bool:
        return any(
            r for r in _load_db()["reservations"]
            if r["studentId"] == student_id and r["bookId"] == book_id and r.get("status") == "active"
        )

    @staticmethod
    def create(student_id: str, book_id: str, book_title: str, student_name: str) -> dict:
        db = _load_db()
        now = datetime.utcnow()
        reservation = {
            "id": str(uuid.uuid4()),
            "studentId": student_id,
            "bookId": book_id,
            "bookTitle": book_title,
            "studentName": student_name,
            "status": "active",
            "reservedAt": now.isoformat(),
            "dueDate": (now + timedelta(days=14)).isoformat(),
        }
        db["reservations"].append(reservation)
        _save_db(db)
        return reservation

    @staticmethod
    def cancel(reservation_id: str):
        db = _load_db()
        for r in db["reservations"]:
            if r["id"] == reservation_id:
                r["status"] = "cancelled"
                r["cancelledAt"] = datetime.utcnow().isoformat()
                _save_db(db)
                return


# ── Waitlists ─────────────────────────────────────────────────────────────────

class WaitlistDB:
    @staticmethod
    def for_book(book_id: str) -> list:
        entries = [e for e in _load_db()["waitlists"] if e["bookId"] == book_id]
        return sorted(entries, key=lambda e: e.get("joinedAt", ""))

    @staticmethod
    def for_student(student_id: str) -> list:
        return [e for e in _load_db()["waitlists"] if e["studentId"] == student_id]

    @staticmethod
    def is_on_waitlist(book_id: str, student_id: str) -> bool:
        return any(
            e for e in _load_db()["waitlists"]
            if e["bookId"] == book_id and e["studentId"] == student_id
        )

    @staticmethod
    def position(book_id: str, student_id: str) -> int | None:
        entry = next(
            (e for e in _load_db()["waitlists"] if e["bookId"] == book_id and e["studentId"] == student_id),
            None
        )
        return entry["position"] if entry else None

    @staticmethod
    def join(book_id: str, student_id: str) -> dict:
        if WaitlistDB.is_on_waitlist(book_id, student_id):
            entry = next(e for e in _load_db()["waitlists"] if e["bookId"] == book_id and e["studentId"] == student_id)
            return entry
        db = _load_db()
        current = WaitlistDB.for_book(book_id)
        entry = {
            "id": str(uuid.uuid4()),
            "bookId": book_id,
            "studentId": student_id,
            "position": len(current) + 1,
            "joinedAt": datetime.utcnow().isoformat(),
            "status": "waiting",
        }
        db["waitlists"].append(entry)
        _save_db(db)
        return entry

    @staticmethod
    def leave(book_id: str, student_id: str):
        db = _load_db()
        db["waitlists"] = [
            e for e in db["waitlists"]
            if not (e["bookId"] == book_id and e["studentId"] == student_id)
        ]
        # Re-number
        remaining = sorted(
            [e for e in db["waitlists"] if e["bookId"] == book_id],
            key=lambda e: e.get("joinedAt", "")
        )
        for i, e in enumerate(remaining):
            e["position"] = i + 1
        _save_db(db)


# ── Chat History ───────────────────────────────────────────────────────────────

class ChatDB:
    @staticmethod
    def get_history(student_id: str, limit: int = 30) -> list:
        history = [m for m in _load_db()["chatHistory"] if m["studentId"] == student_id]
        history.sort(key=lambda m: m.get("timestamp", ""))
        return history[-limit:]

    @staticmethod
    def save(student_id: str, role: str, content: str, metadata: dict | None = None):
        db = _load_db()
        db["chatHistory"].append({
            "id": str(uuid.uuid4()),
            "studentId": student_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        })
        _save_db(db)


# ── Seed ──────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# COMPREHENSIVE BOOK CATALOG  —  75 books across 15 academic subjects
# ─────────────────────────────────────────────────────────────────────────────
SAMPLE_BOOKS = [
    # ── Computer Science (6 books) ──────────────────────────────────────────
    {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen",
     "isbn": "978-0262033848", "subject": "Computer Science", "category": "Algorithms & Data Structures",
     "description": "The definitive reference on algorithms — covers sorting, searching, dynamic programming, graph algorithms and more.",
     "tags": ["algorithms", "data structures", "sorting", "graphs", "programming"],
     "totalCopies": 5, "availableCopies": 3, "year": 2022, "edition": "4th", "level": "intermediate", "rating": 4.8, "borrowedCount": 92},
    {"title": "Clean Code", "author": "Robert C. Martin",
     "isbn": "978-0132350884", "subject": "Computer Science", "category": "Software Engineering",
     "description": "A handbook of agile software craftsmanship — how to write code that is readable, testable and maintainable.",
     "tags": ["clean code", "software engineering", "refactoring", "best practices"],
     "totalCopies": 4, "availableCopies": 1, "year": 2008, "edition": "1st", "level": "intermediate", "rating": 4.7, "borrowedCount": 87},
    {"title": "Python Crash Course", "author": "Eric Matthes",
     "isbn": "978-1718502703", "subject": "Computer Science", "category": "Programming Languages",
     "description": "Fast-paced, thorough introduction to Python — projects include games, data visualisations and web apps.",
     "tags": ["python", "programming", "beginner", "projects", "automation"],
     "totalCopies": 8, "availableCopies": 5, "year": 2023, "edition": "3rd", "level": "beginner", "rating": 4.6, "borrowedCount": 105},
    {"title": "Database System Concepts", "author": "Abraham Silberschatz",
     "isbn": "978-1260515046", "subject": "Computer Science", "category": "Databases",
     "description": "Comprehensive introduction to database design, SQL, transactions and distributed database systems.",
     "tags": ["database", "SQL", "DBMS", "relational model", "transactions"],
     "totalCopies": 5, "availableCopies": 2, "year": 2020, "edition": "7th", "level": "intermediate", "rating": 4.5, "borrowedCount": 61},
    {"title": "Computer Networks", "author": "Andrew S. Tanenbaum",
     "isbn": "978-0132126953", "subject": "Computer Science", "category": "Networking",
     "description": "Complete guide to networking fundamentals — physical layer through application layer, TCP/IP and security.",
     "tags": ["networking", "TCP/IP", "protocols", "internet", "OSI model"],
     "totalCopies": 4, "availableCopies": 3, "year": 2021, "edition": "6th", "level": "intermediate", "rating": 4.4, "borrowedCount": 54},
    {"title": "Operating System Concepts", "author": "Abraham Silberschatz, Peter Baer Galvin",
     "isbn": "978-1119800361", "subject": "Computer Science", "category": "Operating Systems",
     "description": "The 'Dinosaur Book' — covers processes, threads, memory management, file systems and virtualisation.",
     "tags": ["operating systems", "processes", "memory", "file systems", "concurrency"],
     "totalCopies": 5, "availableCopies": 4, "year": 2021, "edition": "10th", "level": "intermediate", "rating": 4.5, "borrowedCount": 72},

    # ── Artificial Intelligence (5 books) ───────────────────────────────────
    {"title": "Artificial Intelligence: A Modern Approach", "author": "Stuart Russell & Peter Norvig",
     "isbn": "978-0137903955", "subject": "Artificial Intelligence", "category": "AI Foundations",
     "description": "The most widely used AI textbook — search, planning, knowledge representation, learning and perception.",
     "tags": ["artificial intelligence", "search algorithms", "planning", "knowledge representation"],
     "totalCopies": 6, "availableCopies": 4, "year": 2021, "edition": "4th", "level": "advanced", "rating": 4.9, "borrowedCount": 88},
    {"title": "Deep Learning", "author": "Ian Goodfellow, Yoshua Bengio & Aaron Courville",
     "isbn": "978-0262035613", "subject": "Artificial Intelligence", "category": "Deep Learning",
     "description": "Comprehensive coverage of deep learning — feedforward networks, CNNs, RNNs, autoencoders and GANs.",
     "tags": ["deep learning", "neural networks", "CNN", "RNN", "backpropagation"],
     "totalCopies": 3, "availableCopies": 0, "year": 2016, "edition": "1st", "level": "advanced", "rating": 4.7, "borrowedCount": 99},
    {"title": "Natural Language Processing with Python", "author": "Steven Bird, Ewan Klein & Edward Loper",
     "isbn": "978-0596516499", "subject": "Artificial Intelligence", "category": "NLP",
     "description": "Practical introduction to NLP using the NLTK library — tokenisation, tagging, parsing and semantics.",
     "tags": ["NLP", "natural language processing", "NLTK", "text mining", "python"],
     "totalCopies": 4, "availableCopies": 3, "year": 2019, "edition": "2nd", "level": "intermediate", "rating": 4.4, "borrowedCount": 63},
    {"title": "Reinforcement Learning: An Introduction", "author": "Richard S. Sutton & Andrew G. Barto",
     "isbn": "978-0262039246", "subject": "Artificial Intelligence", "category": "Reinforcement Learning",
     "description": "The foundational RL textbook — MDPs, temporal-difference learning, policy gradients and function approximation.",
     "tags": ["reinforcement learning", "Q-learning", "MDP", "policy gradient", "AI"],
     "totalCopies": 3, "availableCopies": 2, "year": 2018, "edition": "2nd", "level": "advanced", "rating": 4.8, "borrowedCount": 57},
    {"title": "Pattern Recognition and Machine Learning", "author": "Christopher M. Bishop",
     "isbn": "978-0387310732", "subject": "Artificial Intelligence", "category": "Machine Learning",
     "description": "Rigorous Bayesian treatment of machine learning — regression, classification, neural networks and graphical models.",
     "tags": ["pattern recognition", "Bayesian", "machine learning", "probabilistic models"],
     "totalCopies": 3, "availableCopies": 1, "year": 2006, "edition": "1st", "level": "advanced", "rating": 4.7, "borrowedCount": 48},

    # ── Data Science (5 books) ───────────────────────────────────────────────
    {"title": "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow",
     "author": "Aurélien Géron", "isbn": "978-1098125974", "subject": "Data Science", "category": "Machine Learning",
     "description": "Practical end-to-end guide: regression, classification, clustering, neural networks and deployment.",
     "tags": ["machine learning", "scikit-learn", "tensorflow", "keras", "data science"],
     "totalCopies": 4, "availableCopies": 2, "year": 2022, "edition": "3rd", "level": "intermediate", "rating": 4.8, "borrowedCount": 83},
    {"title": "The Elements of Statistical Learning", "author": "Hastie, Tibshirani & Friedman",
     "isbn": "978-0387848570", "subject": "Data Science", "category": "Statistics & ML",
     "description": "Mathematical rigour behind ML — shrinkage methods, SVMs, random forests, boosting and neural networks.",
     "tags": ["statistical learning", "SVMs", "random forests", "boosting", "regularisation"],
     "totalCopies": 3, "availableCopies": 1, "year": 2016, "edition": "2nd", "level": "advanced", "rating": 4.6, "borrowedCount": 51},
    {"title": "Python for Data Analysis", "author": "Wes McKinney",
     "isbn": "978-1098104030", "subject": "Data Science", "category": "Data Wrangling",
     "description": "Authoritative guide to pandas, NumPy and data manipulation — from the creator of pandas.",
     "tags": ["pandas", "numpy", "data analysis", "python", "data wrangling"],
     "totalCopies": 5, "availableCopies": 3, "year": 2022, "edition": "3rd", "level": "intermediate", "rating": 4.5, "borrowedCount": 77},
    {"title": "Data Science from Scratch", "author": "Joel Grus",
     "isbn": "978-1492041139", "subject": "Data Science", "category": "Foundations",
     "description": "Builds data science algorithms from the ground up using pure Python — statistics, probability and ML.",
     "tags": ["data science", "statistics", "python", "machine learning", "foundations"],
     "totalCopies": 4, "availableCopies": 2, "year": 2019, "edition": "2nd", "level": "beginner", "rating": 4.3, "borrowedCount": 64},
    {"title": "Storytelling with Data", "author": "Cole Nussbaumer Knaflic",
     "isbn": "978-1119002253", "subject": "Data Science", "category": "Data Visualisation",
     "description": "Best practices for data visualisation — choose the right chart, remove clutter, tell compelling stories.",
     "tags": ["data visualisation", "storytelling", "charts", "communication", "dashboards"],
     "totalCopies": 4, "availableCopies": 3, "year": 2015, "edition": "1st", "level": "beginner", "rating": 4.5, "borrowedCount": 69},

    # ── Mathematics (5 books) ────────────────────────────────────────────────
    {"title": "Calculus: Early Transcendentals", "author": "James Stewart",
     "isbn": "978-1285741550", "subject": "Mathematics", "category": "Calculus",
     "description": "Classic calculus — limits, derivatives, integrals, sequences and series with clear worked examples.",
     "tags": ["calculus", "derivatives", "integrals", "limits", "sequences"],
     "totalCopies": 10, "availableCopies": 7, "year": 2015, "edition": "8th", "level": "intermediate", "rating": 4.3, "borrowedCount": 110},
    {"title": "Linear Algebra and Its Applications", "author": "Gilbert Strang",
     "isbn": "978-0030105678", "subject": "Mathematics", "category": "Linear Algebra",
     "description": "Geometric intuition meets rigour — vectors, matrix factorisation, eigenvalues and singular values.",
     "tags": ["linear algebra", "matrices", "eigenvalues", "vectors", "SVD"],
     "totalCopies": 6, "availableCopies": 4, "year": 2016, "edition": "5th", "level": "intermediate", "rating": 4.7, "borrowedCount": 84},
    {"title": "Probability and Statistics for Engineers and Scientists",
     "author": "Walpole, Myers & Myers", "isbn": "978-0134115856", "subject": "Mathematics", "category": "Statistics",
     "description": "Bridge between probability theory and engineering applications — estimation, hypothesis testing, regression.",
     "tags": ["probability", "statistics", "hypothesis testing", "regression", "engineering math"],
     "totalCopies": 5, "availableCopies": 3, "year": 2016, "edition": "9th", "level": "intermediate", "rating": 4.2, "borrowedCount": 67},
    {"title": "Discrete Mathematics and Its Applications", "author": "Kenneth H. Rosen",
     "isbn": "978-0073383095", "subject": "Mathematics", "category": "Discrete Mathematics",
     "description": "Logic, sets, number theory, graph theory, combinatorics and formal languages for CS students.",
     "tags": ["discrete mathematics", "logic", "graph theory", "combinatorics", "proofs"],
     "totalCopies": 6, "availableCopies": 4, "year": 2018, "edition": "8th", "level": "intermediate", "rating": 4.4, "borrowedCount": 78},
    {"title": "Abstract Algebra", "author": "David S. Dummit & Richard M. Foote",
     "isbn": "978-0471433347", "subject": "Mathematics", "category": "Abstract Algebra",
     "description": "Thorough treatment of groups, rings, fields and modules — the essential graduate-level algebra text.",
     "tags": ["abstract algebra", "group theory", "rings", "fields", "Galois theory"],
     "totalCopies": 3, "availableCopies": 2, "year": 2003, "edition": "3rd", "level": "advanced", "rating": 4.6, "borrowedCount": 38},

    # ── Physics (5 books) ────────────────────────────────────────────────────
    {"title": "University Physics with Modern Physics", "author": "Young & Freedman",
     "isbn": "978-0135159552", "subject": "Physics", "category": "General Physics",
     "description": "Complete university physics — mechanics, waves, thermodynamics, electromagnetism and modern physics.",
     "tags": ["physics", "mechanics", "thermodynamics", "electromagnetism", "modern physics"],
     "totalCopies": 8, "availableCopies": 5, "year": 2019, "edition": "15th", "level": "intermediate", "rating": 4.4, "borrowedCount": 96},
    {"title": "Concepts of Modern Physics", "author": "Arthur Beiser",
     "isbn": "978-0072448481", "subject": "Physics", "category": "Modern Physics",
     "description": "Relativity, quantum mechanics, atomic structure, nuclear physics and particle physics explained clearly.",
     "tags": ["modern physics", "quantum mechanics", "relativity", "nuclear physics", "atomic physics"],
     "totalCopies": 5, "availableCopies": 3, "year": 2002, "edition": "6th", "level": "intermediate", "rating": 4.3, "borrowedCount": 59},
    {"title": "Introduction to Electrodynamics", "author": "David J. Griffiths",
     "isbn": "978-1108420419", "subject": "Physics", "category": "Electromagnetism",
     "description": "The definitive undergraduate electrodynamics text — fields, potentials, Maxwell's equations and waves.",
     "tags": ["electrodynamics", "Maxwell equations", "electromagnetism", "fields", "optics"],
     "totalCopies": 4, "availableCopies": 2, "year": 2017, "edition": "4th", "level": "advanced", "rating": 4.8, "borrowedCount": 44},
    {"title": "The Feynman Lectures on Physics", "author": "Richard P. Feynman",
     "isbn": "978-0465023820", "subject": "Physics", "category": "Foundational Physics",
     "description": "Feynman's legendary lecture series — profound physical insight presented in an engaging, intuitive style.",
     "tags": ["Feynman", "physics", "mechanics", "quantum mechanics", "electromagnetism"],
     "totalCopies": 4, "availableCopies": 3, "year": 2011, "edition": "Millenium", "level": "intermediate", "rating": 4.9, "borrowedCount": 82},
    {"title": "Introduction to Quantum Mechanics", "author": "David J. Griffiths",
     "isbn": "978-1107189638", "subject": "Physics", "category": "Quantum Mechanics",
     "description": "Clear, accessible introduction to quantum mechanics — wave functions, Schrödinger equation and spin.",
     "tags": ["quantum mechanics", "wave function", "Schrodinger equation", "spin", "quantum physics"],
     "totalCopies": 4, "availableCopies": 2, "year": 2018, "edition": "3rd", "level": "advanced", "rating": 4.7, "borrowedCount": 55},

    # ── Economics (5 books) ──────────────────────────────────────────────────
    {"title": "Principles of Economics", "author": "N. Gregory Mankiw",
     "isbn": "978-0357038314", "subject": "Economics", "category": "Introductory Economics",
     "description": "The most widely adopted introductory economics text — supply, demand, markets, GDP and monetary policy.",
     "tags": ["economics", "microeconomics", "macroeconomics", "supply demand", "GDP"],
     "totalCopies": 7, "availableCopies": 5, "year": 2020, "edition": "9th", "level": "beginner", "rating": 4.3, "borrowedCount": 103},
    {"title": "Microeconomic Theory", "author": "Andreu Mas-Colell, Michael Whinston & Jerry Green",
     "isbn": "978-0195073409", "subject": "Economics", "category": "Microeconomics",
     "description": "The definitive graduate microeconomics textbook — consumer theory, production, equilibrium and game theory.",
     "tags": ["microeconomics", "consumer theory", "game theory", "general equilibrium", "welfare"],
     "totalCopies": 3, "availableCopies": 2, "year": 1995, "edition": "1st", "level": "advanced", "rating": 4.5, "borrowedCount": 31},
    {"title": "Macroeconomics", "author": "N. Gregory Mankiw",
     "isbn": "978-1319105990", "subject": "Economics", "category": "Macroeconomics",
     "description": "Long-run growth, business cycles, IS-LM model, open-economy macroeconomics and policy.",
     "tags": ["macroeconomics", "GDP", "inflation", "monetary policy", "fiscal policy"],
     "totalCopies": 5, "availableCopies": 3, "year": 2019, "edition": "10th", "level": "intermediate", "rating": 4.4, "borrowedCount": 58},
    {"title": "Freakonomics", "author": "Steven D. Levitt & Stephen J. Dubner",
     "isbn": "978-0060731335", "subject": "Economics", "category": "Behavioural Economics",
     "description": "Explores the hidden side of economics — incentives, information asymmetry and unexpected correlations.",
     "tags": ["behavioural economics", "incentives", "data", "social science", "popular economics"],
     "totalCopies": 5, "availableCopies": 4, "year": 2005, "edition": "1st", "level": "beginner", "rating": 4.4, "borrowedCount": 88},
    {"title": "The Wealth of Nations", "author": "Adam Smith",
     "isbn": "978-0679783367", "subject": "Economics", "category": "Classical Economics",
     "description": "The foundational text of modern economics — division of labour, free markets and the invisible hand.",
     "tags": ["classical economics", "free market", "division of labour", "capitalism", "Adam Smith"],
     "totalCopies": 3, "availableCopies": 2, "year": 1776, "edition": "Modern", "level": "intermediate", "rating": 4.2, "borrowedCount": 29},

    # ── Business & Management (5 books) ─────────────────────────────────────
    {"title": "The Lean Startup", "author": "Eric Ries",
     "isbn": "978-0307887894", "subject": "Business", "category": "Entrepreneurship",
     "description": "Build-measure-learn cycle for startups — validated learning, MVPs and pivoting based on real data.",
     "tags": ["startup", "entrepreneurship", "MVP", "agile", "innovation", "lean"],
     "totalCopies": 3, "availableCopies": 2, "year": 2011, "edition": "1st", "level": "beginner", "rating": 4.5, "borrowedCount": 76},
    {"title": "Good to Great", "author": "Jim Collins",
     "isbn": "978-0066620992", "subject": "Business", "category": "Leadership & Strategy",
     "description": "Research-based analysis of what makes companies achieve and sustain great performance.",
     "tags": ["leadership", "strategy", "management", "corporate culture", "business growth"],
     "totalCopies": 4, "availableCopies": 3, "year": 2001, "edition": "1st", "level": "intermediate", "rating": 4.4, "borrowedCount": 65},
    {"title": "Competitive Strategy", "author": "Michael E. Porter",
     "isbn": "978-0684841489", "subject": "Business", "category": "Strategy",
     "description": "Porter's Five Forces and generic strategies framework — the most influential business strategy book.",
     "tags": ["strategy", "competitive advantage", "Porter", "five forces", "industry analysis"],
     "totalCopies": 3, "availableCopies": 2, "year": 1980, "edition": "1st", "level": "intermediate", "rating": 4.3, "borrowedCount": 47},
    {"title": "Principles of Marketing", "author": "Philip Kotler & Gary Armstrong",
     "isbn": "978-0135197158", "subject": "Business", "category": "Marketing",
     "description": "Foundation marketing text — segmentation, targeting, positioning, the 4Ps and digital marketing.",
     "tags": ["marketing", "4Ps", "segmentation", "branding", "digital marketing"],
     "totalCopies": 5, "availableCopies": 3, "year": 2020, "edition": "18th", "level": "beginner", "rating": 4.2, "borrowedCount": 71},
    {"title": "Financial Accounting", "author": "Robert Libby, Patricia Libby & Frank Hodge",
     "isbn": "978-1260247930", "subject": "Business", "category": "Accounting",
     "description": "Decision-making approach to financial accounting — balance sheets, income statements and cash flows.",
     "tags": ["accounting", "financial statements", "balance sheet", "income statement", "GAAP"],
     "totalCopies": 4, "availableCopies": 2, "year": 2020, "edition": "10th", "level": "beginner", "rating": 4.1, "borrowedCount": 52},

    # ── Engineering (5 books) ────────────────────────────────────────────────
    {"title": "Engineering Mechanics: Dynamics", "author": "J.L. Meriam & L.G. Kraige",
     "isbn": "978-1119390985", "subject": "Engineering", "category": "Mechanical Engineering",
     "description": "Kinematics and kinetics of particles and rigid bodies — force, acceleration, energy and momentum.",
     "tags": ["dynamics", "kinematics", "mechanics", "mechanical engineering", "vibrations"],
     "totalCopies": 5, "availableCopies": 3, "year": 2018, "edition": "9th", "level": "intermediate", "rating": 4.3, "borrowedCount": 58},
    {"title": "Fundamentals of Electric Circuits", "author": "Charles K. Alexander & Matthew Sadiku",
     "isbn": "978-1260226966", "subject": "Engineering", "category": "Electrical Engineering",
     "description": "Comprehensive intro to circuit analysis — Kirchhoff laws, AC/DC circuits, operational amplifiers.",
     "tags": ["circuits", "electrical engineering", "Kirchhoff", "AC DC", "op-amp"],
     "totalCopies": 5, "availableCopies": 4, "year": 2020, "edition": "7th", "level": "intermediate", "rating": 4.5, "borrowedCount": 63},
    {"title": "Shigley's Mechanical Engineering Design", "author": "Budynas & Nisbett",
     "isbn": "978-1260569995", "subject": "Engineering", "category": "Mechanical Design",
     "description": "Machine design fundamentals — static and fatigue failure, shafts, bearings, gears and joints.",
     "tags": ["mechanical design", "machine elements", "fatigue", "gears", "bearings"],
     "totalCopies": 4, "availableCopies": 2, "year": 2020, "edition": "11th", "level": "advanced", "rating": 4.4, "borrowedCount": 44},
    {"title": "Thermodynamics: An Engineering Approach", "author": "Yunus A. Cengel & Michael A. Boles",
     "isbn": "978-1260048728", "subject": "Engineering", "category": "Thermodynamics",
     "description": "Thermodynamic principles for engineering — laws of thermodynamics, cycles, refrigeration and combustion.",
     "tags": ["thermodynamics", "heat transfer", "engineering", "cycles", "entropy"],
     "totalCopies": 5, "availableCopies": 3, "year": 2019, "edition": "9th", "level": "intermediate", "rating": 4.3, "borrowedCount": 55},
    {"title": "Signals and Systems", "author": "Alan V. Oppenheim & Alan S. Willsky",
     "isbn": "978-0138147570", "subject": "Engineering", "category": "Signal Processing",
     "description": "Continuous and discrete-time signals and systems — Fourier analysis, Laplace and Z-transforms.",
     "tags": ["signals", "systems", "Fourier", "Laplace", "digital signal processing"],
     "totalCopies": 4, "availableCopies": 3, "year": 1996, "edition": "2nd", "level": "advanced", "rating": 4.5, "borrowedCount": 48},

    # ── Chemistry (5 books) ──────────────────────────────────────────────────
    {"title": "Chemistry: The Central Science", "author": "Brown, LeMay & Bursten",
     "isbn": "978-0134414232", "subject": "Chemistry", "category": "General Chemistry",
     "description": "Comprehensive general chemistry — atomic structure, bonding, reactions, equilibrium and electrochemistry.",
     "tags": ["chemistry", "atomic structure", "bonding", "reactions", "equilibrium"],
     "totalCopies": 6, "availableCopies": 4, "year": 2017, "edition": "14th", "level": "beginner", "rating": 4.3, "borrowedCount": 79},
    {"title": "Organic Chemistry", "author": "Paula Yurkanis Bruice",
     "isbn": "978-0134042282", "subject": "Chemistry", "category": "Organic Chemistry",
     "description": "Thorough treatment of organic chemistry — mechanisms, stereochemistry, spectroscopy and synthesis.",
     "tags": ["organic chemistry", "mechanisms", "stereochemistry", "synthesis", "spectroscopy"],
     "totalCopies": 5, "availableCopies": 3, "year": 2016, "edition": "8th", "level": "intermediate", "rating": 4.4, "borrowedCount": 66},
    {"title": "Physical Chemistry", "author": "Peter Atkins & Julio de Paula",
     "isbn": "978-0198700722", "subject": "Chemistry", "category": "Physical Chemistry",
     "description": "Quantum mechanics, statistical mechanics, thermodynamics and kinetics at the molecular level.",
     "tags": ["physical chemistry", "quantum chemistry", "thermodynamics", "kinetics", "spectroscopy"],
     "totalCopies": 4, "availableCopies": 2, "year": 2018, "edition": "11th", "level": "advanced", "rating": 4.5, "borrowedCount": 41},
    {"title": "Biochemistry", "author": "Jeremy M. Berg, John L. Tymoczko & Gregory J. Gatto",
     "isbn": "978-1319114657", "subject": "Chemistry", "category": "Biochemistry",
     "description": "Molecular life sciences — proteins, enzymes, metabolism, DNA replication and gene expression.",
     "tags": ["biochemistry", "proteins", "enzymes", "metabolism", "DNA"],
     "totalCopies": 5, "availableCopies": 3, "year": 2019, "edition": "9th", "level": "intermediate", "rating": 4.4, "borrowedCount": 57},
    {"title": "Analytical Chemistry", "author": "Daniel C. Harris",
     "isbn": "978-1464175633", "subject": "Chemistry", "category": "Analytical Chemistry",
     "description": "Quantitative analysis methods — titrations, chromatography, spectroscopy and electroanalytical techniques.",
     "tags": ["analytical chemistry", "titrations", "chromatography", "spectroscopy", "quantitative"],
     "totalCopies": 4, "availableCopies": 3, "year": 2015, "edition": "9th", "level": "intermediate", "rating": 4.3, "borrowedCount": 45},

    # ── Biology (5 books) ────────────────────────────────────────────────────
    {"title": "Campbell Biology", "author": "Jane B. Reece et al.",
     "isbn": "978-0135188743", "subject": "Biology", "category": "General Biology",
     "description": "The gold standard biology textbook — cell biology, genetics, evolution, ecology and physiology.",
     "tags": ["biology", "cell biology", "genetics", "evolution", "ecology"],
     "totalCopies": 7, "availableCopies": 5, "year": 2020, "edition": "12th", "level": "beginner", "rating": 4.5, "borrowedCount": 91},
    {"title": "Molecular Biology of the Cell", "author": "Alberts, Johnson, Lewis et al.",
     "isbn": "978-0393884821", "subject": "Biology", "category": "Molecular Biology",
     "description": "Comprehensive molecular cell biology — cell structure, signalling, gene expression and cell division.",
     "tags": ["molecular biology", "cell signalling", "gene expression", "mitosis", "proteins"],
     "totalCopies": 5, "availableCopies": 3, "year": 2022, "edition": "7th", "level": "intermediate", "rating": 4.6, "borrowedCount": 62},
    {"title": "Genetics: From Genes to Genomes", "author": "Leland H. Hartwell et al.",
     "isbn": "978-1259700903", "subject": "Biology", "category": "Genetics",
     "description": "Modern genetics approach — Mendelian genetics, linkage, genomics, epigenetics and systems biology.",
     "tags": ["genetics", "genomics", "Mendelian", "epigenetics", "DNA sequencing"],
     "totalCopies": 5, "availableCopies": 3, "year": 2017, "edition": "6th", "level": "intermediate", "rating": 4.3, "borrowedCount": 55},
    {"title": "Evolutionary Biology", "author": "Douglas J. Futuyma & Mark Kirkpatrick",
     "isbn": "978-1605356051", "subject": "Biology", "category": "Evolutionary Biology",
     "description": "Mechanisms of evolution — natural selection, genetic drift, speciation, phylogenetics and macroevolution.",
     "tags": ["evolution", "natural selection", "speciation", "phylogenetics", "population genetics"],
     "totalCopies": 4, "availableCopies": 3, "year": 2017, "edition": "4th", "level": "intermediate", "rating": 4.4, "borrowedCount": 43},
    {"title": "Neuroscience: Exploring the Brain", "author": "Mark F. Bear, Barry W. Connors & Michael A. Paradiso",
     "isbn": "978-1284217964", "subject": "Biology", "category": "Neuroscience",
     "description": "Accessible neuroscience — neurons, synaptic transmission, brain systems, sensation, movement and cognition.",
     "tags": ["neuroscience", "neurons", "brain", "synapses", "cognition", "nervous system"],
     "totalCopies": 4, "availableCopies": 2, "year": 2020, "edition": "4th", "level": "intermediate", "rating": 4.5, "borrowedCount": 49},

    # ── Psychology (5 books) ─────────────────────────────────────────────────
    {"title": "Psychology", "author": "David G. Myers & C. Nathan DeWall",
     "isbn": "978-1319070557", "subject": "Psychology", "category": "General Psychology",
     "description": "Engaging introduction to psychology — neuroscience, development, learning, cognition and social behaviour.",
     "tags": ["psychology", "cognitive", "social psychology", "neuroscience", "behaviour"],
     "totalCopies": 6, "availableCopies": 4, "year": 2020, "edition": "13th", "level": "beginner", "rating": 4.4, "borrowedCount": 85},
    {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman",
     "isbn": "978-0374533557", "subject": "Psychology", "category": "Cognitive Psychology",
     "description": "Kahneman's groundbreaking work on System 1 vs System 2 thinking, cognitive biases and decision-making.",
     "tags": ["cognitive biases", "decision making", "behavioral economics", "heuristics", "psychology"],
     "totalCopies": 5, "availableCopies": 3, "year": 2011, "edition": "1st", "level": "beginner", "rating": 4.7, "borrowedCount": 112},
    {"title": "Social Psychology", "author": "Elliot Aronson, Timothy D. Wilson & Samuel Sommers",
     "isbn": "978-0135576601", "subject": "Psychology", "category": "Social Psychology",
     "description": "How social context shapes thoughts, feelings and behaviour — conformity, persuasion and group dynamics.",
     "tags": ["social psychology", "conformity", "persuasion", "attitudes", "group dynamics"],
     "totalCopies": 5, "availableCopies": 3, "year": 2020, "edition": "10th", "level": "intermediate", "rating": 4.3, "borrowedCount": 67},
    {"title": "Abnormal Psychology", "author": "Ronald J. Comer & Jonathan S. Comer",
     "isbn": "978-1319194659", "subject": "Psychology", "category": "Clinical Psychology",
     "description": "Classification, causes and treatment of psychological disorders — DSM approach with case studies.",
     "tags": ["abnormal psychology", "mental disorders", "DSM", "therapy", "clinical psychology"],
     "totalCopies": 4, "availableCopies": 2, "year": 2021, "edition": "11th", "level": "intermediate", "rating": 4.2, "borrowedCount": 54},
    {"title": "The Psychology of Money", "author": "Morgan Housel",
     "isbn": "978-0857197689", "subject": "Psychology", "category": "Behavioural Finance",
     "description": "How emotions and biases shape financial decisions — wealth, greed, risk tolerance and long-term thinking.",
     "tags": ["psychology", "finance", "behavioral finance", "investing", "money"],
     "totalCopies": 4, "availableCopies": 3, "year": 2020, "edition": "1st", "level": "beginner", "rating": 4.6, "borrowedCount": 94},

    # ── Medical & Health Sciences (5 books) ─────────────────────────────────
    {"title": "Gray's Anatomy for Students", "author": "Richard L. Drake et al.",
     "isbn": "978-0323393041", "subject": "Medicine", "category": "Anatomy",
     "description": "Clinical anatomy with dissection photos — muscles, nerves, vasculature and clinical correlations.",
     "tags": ["anatomy", "medical", "muscles", "nerves", "clinical anatomy"],
     "totalCopies": 5, "availableCopies": 3, "year": 2019, "edition": "4th", "level": "intermediate", "rating": 4.6, "borrowedCount": 72},
    {"title": "Robbins & Cotran Pathologic Basis of Disease", "author": "Kumar, Abbas & Aster",
     "isbn": "978-0323531139", "subject": "Medicine", "category": "Pathology",
     "description": "The definitive pathology text — cellular responses to injury, inflammation, neoplasia and systemic disease.",
     "tags": ["pathology", "disease mechanisms", "inflammation", "neoplasia", "medical"],
     "totalCopies": 4, "availableCopies": 2, "year": 2020, "edition": "10th", "level": "advanced", "rating": 4.7, "borrowedCount": 58},
    {"title": "Harrison's Principles of Internal Medicine", "author": "Fauci, Kasper, Longo et al.",
     "isbn": "978-1260128994", "subject": "Medicine", "category": "Internal Medicine",
     "description": "The gold standard internal medicine reference — diagnosis, pathophysiology and management of all diseases.",
     "tags": ["internal medicine", "clinical medicine", "diagnosis", "treatment", "physiology"],
     "totalCopies": 4, "availableCopies": 2, "year": 2022, "edition": "21st", "level": "advanced", "rating": 4.8, "borrowedCount": 63},
    {"title": "Guyton and Hall Textbook of Medical Physiology", "author": "John E. Hall",
     "isbn": "978-0323597128", "subject": "Medicine", "category": "Physiology",
     "description": "Comprehensive medical physiology — cardiovascular, respiratory, renal, neural and endocrine systems.",
     "tags": ["physiology", "medical", "cardiovascular", "renal", "endocrine"],
     "totalCopies": 5, "availableCopies": 3, "year": 2020, "edition": "14th", "level": "intermediate", "rating": 4.6, "borrowedCount": 66},
    {"title": "Public Health: An Introduction to the Science and Practice of Population Health",
     "author": "Nicholas Freudenberg",
     "isbn": "978-1538151327", "subject": "Medicine", "category": "Public Health",
     "description": "Population health, epidemiology, social determinants, health policy and global health challenges.",
     "tags": ["public health", "epidemiology", "health policy", "prevention", "population health"],
     "totalCopies": 3, "availableCopies": 2, "year": 2021, "edition": "2nd", "level": "intermediate", "rating": 4.2, "borrowedCount": 38},

    # ── Law (5 books) ────────────────────────────────────────────────────────
    {"title": "Black's Law Dictionary", "author": "Bryan A. Garner",
     "isbn": "978-1539229759", "subject": "Law", "category": "Legal Reference",
     "description": "The definitive legal dictionary — standard reference for American legal terms and definitions.",
     "tags": ["law", "legal terms", "dictionary", "jurisprudence", "legal reference"],
     "totalCopies": 4, "availableCopies": 3, "year": 2019, "edition": "11th", "level": "beginner", "rating": 4.5, "borrowedCount": 44},
    {"title": "Constitutional Law: Cases and Materials", "author": "Kathleen Sullivan & Noah Feldman",
     "isbn": "978-1683287049", "subject": "Law", "category": "Constitutional Law",
     "description": "Foundational constitutional law casebook — judicial review, federalism, separation of powers and civil rights.",
     "tags": ["constitutional law", "judicial review", "civil rights", "federalism", "Supreme Court"],
     "totalCopies": 3, "availableCopies": 2, "year": 2019, "edition": "19th", "level": "intermediate", "rating": 4.3, "borrowedCount": 36},
    {"title": "Contract Law", "author": "Ewan McKendrick",
     "isbn": "978-1352006131", "subject": "Law", "category": "Contract Law",
     "description": "Offer, acceptance, consideration, terms, breach and remedies — comprehensive English contract law text.",
     "tags": ["contract law", "offer acceptance", "consideration", "breach", "remedies"],
     "totalCopies": 4, "availableCopies": 3, "year": 2020, "edition": "13th", "level": "intermediate", "rating": 4.2, "borrowedCount": 41},
    {"title": "Introduction to International Law", "author": "Malcolm N. Shaw",
     "isbn": "978-1108477536", "subject": "Law", "category": "International Law",
     "description": "Treaties, state sovereignty, UN system, international courts and human rights law.",
     "tags": ["international law", "treaties", "UN", "human rights", "sovereignty"],
     "totalCopies": 3, "availableCopies": 2, "year": 2021, "edition": "9th", "level": "intermediate", "rating": 4.4, "borrowedCount": 33},
    {"title": "Tort Law", "author": "Tony Weir",
     "isbn": "978-0198160250", "subject": "Law", "category": "Tort Law",
     "description": "Negligence, duty of care, causation, damages and defences — the essentials of tort law.",
     "tags": ["tort law", "negligence", "duty of care", "damages", "liability"],
     "totalCopies": 3, "availableCopies": 2, "year": 2006, "edition": "1st", "level": "intermediate", "rating": 4.1, "borrowedCount": 28},

    # ── Environmental Science (5 books) ──────────────────────────────────────
    {"title": "Environmental Science: Earth as a Living Planet", "author": "Daniel B. Botkin & Edward A. Keller",
     "isbn": "978-1119305743", "subject": "Environmental Science", "category": "General Environmental Science",
     "description": "Interdisciplinary approach to environment — ecology, climate change, biodiversity and sustainability.",
     "tags": ["environmental science", "ecology", "climate change", "biodiversity", "sustainability"],
     "totalCopies": 5, "availableCopies": 4, "year": 2018, "edition": "10th", "level": "beginner", "rating": 4.3, "borrowedCount": 61},
    {"title": "Climate Change: What Everyone Needs to Know", "author": "Joseph Romm",
     "isbn": "978-0190250171", "subject": "Environmental Science", "category": "Climate Science",
     "description": "Accessible guide to climate science — causes, impacts, projections, solutions and policy.",
     "tags": ["climate change", "global warming", "carbon emissions", "renewable energy", "policy"],
     "totalCopies": 4, "availableCopies": 3, "year": 2022, "edition": "3rd", "level": "beginner", "rating": 4.4, "borrowedCount": 74},
    {"title": "Ecology: From Individuals to Ecosystems", "author": "Michael Begon, Colin Townsend & John Harper",
     "isbn": "978-1119279310", "subject": "Environmental Science", "category": "Ecology",
     "description": "Population ecology, community ecology, ecosystems, nutrient cycling and applied ecology.",
     "tags": ["ecology", "ecosystems", "population ecology", "food webs", "conservation"],
     "totalCopies": 4, "availableCopies": 3, "year": 2021, "edition": "5th", "level": "intermediate", "rating": 4.4, "borrowedCount": 49},
    {"title": "Renewable Energy: Physics, Engineering, Environmental Impacts",
     "author": "Bent Sørensen", "isbn": "978-0128005521",
     "subject": "Environmental Science", "category": "Renewable Energy",
     "description": "Solar, wind, hydro, biomass and geothermal energy — technologies, efficiency and environmental impacts.",
     "tags": ["renewable energy", "solar", "wind", "sustainability", "energy engineering"],
     "totalCopies": 3, "availableCopies": 2, "year": 2017, "edition": "4th", "level": "advanced", "rating": 4.3, "borrowedCount": 38},
    {"title": "Silent Spring", "author": "Rachel Carson",
     "isbn": "978-0618249060", "subject": "Environmental Science", "category": "Environmental History",
     "description": "The landmark book that launched the modern environmental movement — pesticides and ecological harm.",
     "tags": ["environment", "pesticides", "ecology", "conservation", "environmental movement"],
     "totalCopies": 4, "availableCopies": 3, "year": 1962, "edition": "Anniversary", "level": "beginner", "rating": 4.6, "borrowedCount": 56},

    # ── History (5 books) ────────────────────────────────────────────────────
    {"title": "Sapiens: A Brief History of Humankind", "author": "Yuval Noah Harari",
     "isbn": "978-0062316097", "subject": "History", "category": "World History",
     "description": "Big history from the cognitive revolution through the agricultural and scientific revolutions to today.",
     "tags": ["history", "human evolution", "civilisation", "Sapiens", "anthropology"],
     "totalCopies": 6, "availableCopies": 4, "year": 2015, "edition": "1st", "level": "beginner", "rating": 4.7, "borrowedCount": 130},
    {"title": "Guns, Germs, and Steel", "author": "Jared Diamond",
     "isbn": "978-0393354324", "subject": "History", "category": "World History",
     "description": "Why some civilisations dominated others — geography, agriculture, technology and disease.",
     "tags": ["history", "civilisation", "geography", "anthropology", "Pulitzer Prize"],
     "totalCopies": 5, "availableCopies": 3, "year": 1997, "edition": "1st", "level": "beginner", "rating": 4.5, "borrowedCount": 99},
    {"title": "The History of the Ancient World", "author": "Susan Wise Bauer",
     "isbn": "978-0393059748", "subject": "History", "category": "Ancient History",
     "description": "From Sumer to Rome — ancient civilisations, empires, rulers and their interconnections.",
     "tags": ["ancient history", "Mesopotamia", "Egypt", "Rome", "civilisations"],
     "totalCopies": 4, "availableCopies": 3, "year": 2007, "edition": "1st", "level": "intermediate", "rating": 4.3, "borrowedCount": 45},
    {"title": "A People's History of the United States", "author": "Howard Zinn",
     "isbn": "978-0062397348", "subject": "History", "category": "American History",
     "description": "American history from the perspective of workers, indigenous people and marginalised groups.",
     "tags": ["American history", "social history", "civil rights", "labour movement", "politics"],
     "totalCopies": 4, "availableCopies": 2, "year": 1980, "edition": "Modern Classic", "level": "intermediate", "rating": 4.4, "borrowedCount": 71},
    {"title": "The Rise and Fall of the Third Reich", "author": "William L. Shirer",
     "isbn": "978-1451651683", "subject": "History", "category": "Modern History",
     "description": "Comprehensive account of Nazi Germany — rise of Hitler, World War II, the Holocaust and defeat.",
     "tags": ["World War II", "Nazi Germany", "Hitler", "Holocaust", "modern history"],
     "totalCopies": 3, "availableCopies": 2, "year": 1960, "edition": "Modern Classic", "level": "intermediate", "rating": 4.6, "borrowedCount": 59},

    # ── Literature & Writing (5 books) ───────────────────────────────────────
    {"title": "The Elements of Style", "author": "Strunk & White",
     "isbn": "978-0205309023", "subject": "Literature", "category": "Writing & Style",
     "description": "The classic guide to English writing style — composition rules, omit needless words and clarity.",
     "tags": ["writing", "style", "grammar", "composition", "English"],
     "totalCopies": 6, "availableCopies": 5, "year": 1959, "edition": "4th", "level": "beginner", "rating": 4.4, "borrowedCount": 82},
    {"title": "On Writing: A Memoir of the Craft", "author": "Stephen King",
     "isbn": "978-1439193631", "subject": "Literature", "category": "Creative Writing",
     "description": "Part memoir, part writing masterclass — vocabulary, dialogue, plot and the discipline of writing.",
     "tags": ["creative writing", "storytelling", "writing craft", "Stephen King", "fiction"],
     "totalCopies": 4, "availableCopies": 3, "year": 2000, "edition": "1st", "level": "beginner", "rating": 4.7, "borrowedCount": 95},
    {"title": "The Norton Anthology of English Literature", "author": "Stephen Greenblatt et al.",
     "isbn": "978-0393264531", "subject": "Literature", "category": "Literary Anthology",
     "description": "Comprehensive anthology from Beowulf to the 21st century — the essential English literature collection.",
     "tags": ["English literature", "poetry", "drama", "prose", "anthology"],
     "totalCopies": 5, "availableCopies": 3, "year": 2018, "edition": "10th", "level": "intermediate", "rating": 4.3, "borrowedCount": 47},
    {"title": "Literary Theory: An Introduction", "author": "Terry Eagleton",
     "isbn": "978-0816654512", "subject": "Literature", "category": "Literary Theory",
     "description": "Accessible guide to literary theory — phenomenology, hermeneutics, structuralism and post-structuralism.",
     "tags": ["literary theory", "structuralism", "postmodernism", "criticism", "deconstruction"],
     "totalCopies": 4, "availableCopies": 3, "year": 2008, "edition": "Anniversary", "level": "intermediate", "rating": 4.2, "borrowedCount": 37},
    {"title": "Bird by Bird: Some Instructions on Writing and Life", "author": "Anne Lamott",
     "isbn": "978-0385480017", "subject": "Literature", "category": "Creative Writing",
     "description": "Practical and encouraging writing guide — first drafts, characters, plot, writer's block and publication.",
     "tags": ["creative writing", "writing tips", "fiction", "inspiration", "craft"],
     "totalCopies": 3, "availableCopies": 2, "year": 1994, "edition": "1st", "level": "beginner", "rating": 4.6, "borrowedCount": 63},
]

SAMPLE_STUDENTS = [
    {"name": "Alex Johnson", "email": "alex.johnson@university.edu", "studentId": "STU001",
     "major": "Computer Science", "year": 3,
     "currentCourses": ["Algorithms", "Database Systems", "Operating Systems"],
     "interests": ["machine learning", "web development", "algorithms"]},
    {"name": "Maria Garcia", "email": "maria.garcia@university.edu", "studentId": "STU002",
     "major": "Data Science", "year": 2,
     "currentCourses": ["Introduction to ML", "Statistics", "Python Programming"],
     "interests": ["data analysis", "deep learning", "visualization"]},
    {"name": "James Chen", "email": "james.chen@university.edu", "studentId": "STU003",
     "major": "Physics", "year": 1,
     "currentCourses": ["Mechanics", "Calculus I", "Introduction to Programming"],
     "interests": ["quantum physics", "mathematics", "simulations"]},
]


def seed_database():
    """Populate the database with sample books and students if empty."""
    db = _load_db()
    if not db["books"]:
        for book_data in SAMPLE_BOOKS:
            BookDB.create(book_data)
    if not db["students"]:
        for student_data in SAMPLE_STUDENTS:
            StudentDB.create(student_data)
