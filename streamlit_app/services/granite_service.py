"""
IBM watsonx.ai Granite Service (Python)
Uses ibm-watsonx-ai SDK with ibm/granite-4-h-small model
"""

import os
import json
import re
import streamlit as st
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.foundation_models.schema import TextChatParameters

# ── Singleton client ───────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_granite_model():
    """Lazy-load and cache the IBM Granite model instance."""
    api_key = st.secrets.get("WATSONX_API_KEY", os.getenv("WATSONX_API_KEY", ""))
    project_id = st.secrets.get("WATSONX_PROJECT_ID", os.getenv("WATSONX_PROJECT_ID", ""))
    url = st.secrets.get("WATSONX_URL", os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"))
    model_id = st.secrets.get("GRANITE_MODEL_ID", os.getenv("GRANITE_MODEL_ID", "ibm/granite-4-h-small"))

    if not api_key or not project_id:
        raise ValueError("IBM watsonx.ai credentials missing. Set WATSONX_API_KEY and WATSONX_PROJECT_ID in .streamlit/secrets.toml")

    creds = Credentials(url=url, api_key=api_key)
    return ModelInference(model_id=model_id, credentials=creds, project_id=project_id)


def chat_with_granite(system_prompt: str, user_prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """Send a chat request to IBM Granite and return the response text."""
    try:
        model = get_granite_model()
        params = TextChatParameters(max_tokens=max_tokens, temperature=temperature)
        response = model.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            params=params,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        st.error(f"IBM Granite error: {e}")
        return ""


# ── NLP Intent Understanding ───────────────────────────────────────────────────

VALID_INTENTS = [
    "search_book", "get_recommendation", "check_availability",
    "reserve_book", "join_waitlist", "get_syllabus_books", "general_help",
]

def understand_query(query: str, student: dict | None = None) -> dict:
    """
    Use IBM Granite to parse a student query and extract intent + keywords.
    Returns a dict with intent, keywords, subject, bookTitle, author, level, summary.
    """
    system_prompt = (
        "You are a Library AI Assistant. Analyze the student query and extract structured information. "
        "Respond ONLY with valid JSON — no explanation, no markdown fences."
    )

    context_lines = []
    if student:
        if student.get("major"):
            context_lines.append(f"Student major: {student['major']}")
        if student.get("year"):
            context_lines.append(f"Academic year: Year {student['year']}")
        if student.get("currentCourses"):
            context_lines.append(f"Current courses: {', '.join(student['currentCourses'])}")

    user_prompt = f"""Student query: "{query}"
{chr(10).join(context_lines)}

Return ONLY this JSON (fill every field):
{{
  "intent": "one of: search_book | get_recommendation | check_availability | reserve_book | join_waitlist | get_syllabus_books | general_help",
  "keywords": ["key", "search", "terms"],
  "subject": "main subject or topic",
  "bookTitle": "specific book title if mentioned, else null",
  "author": "specific author if mentioned, else null",
  "course": "specific course if mentioned, else null",
  "level": "beginner or intermediate or advanced or null",
  "summary": "one sentence description of what the student needs"
}}"""

    try:
        text = chat_with_granite(system_prompt, user_prompt, max_tokens=300, temperature=0.1)
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            parsed = json.loads(json_match.group())
            if parsed.get("intent") not in VALID_INTENTS:
                parsed["intent"] = "search_book"
            return parsed
    except Exception as e:
        pass  # fall through to fallback

    # Fallback: keyword extraction
    words = [w for w in re.split(r'\s+', query.lower()) if len(w) > 3]
    return {
        "intent": "search_book",
        "keywords": words,
        "subject": query,
        "bookTitle": None,
        "author": None,
        "course": None,
        "level": None,
        "summary": query,
    }


# ── Personalized Recommendations ──────────────────────────────────────────────

def generate_recommendations(student: dict, books: list, query_context: str = "") -> str:
    """Generate AI-powered book recommendations for a student."""
    book_list = "\n".join(
        f'- "{b["title"]}" by {b["author"]} [{b["subject"]}] '
        f'(Available: {"Yes" if b.get("availableCopies", 0) > 0 else "No"})'
        for b in books[:20]
    )

    system_prompt = (
        "You are an expert academic librarian AI. Recommend the most suitable books for this student. "
        "Be specific, helpful, and concise. Format your response with numbered recommendations."
    )

    user_prompt = f"""Student Profile:
- Name: {student.get('name', 'Student')}
- Major: {student.get('major', 'Unknown')}
- Year: Year {student.get('year', 1)}
- Current courses: {', '.join(student.get('currentCourses', [])) or 'Not specified'}
- Study interests: {', '.join(student.get('interests', [])) or 'Not specified'}
{f"- Specific request: {query_context}" if query_context else ""}

Available books in library:
{book_list}

Provide 3-5 personalized book recommendations with brief reasons why each book suits this student."""

    result = chat_with_granite(system_prompt, user_prompt, max_tokens=600, temperature=0.6)
    return result or "Unable to generate recommendations at this time. Please browse the catalog."


# ── Conversational Response ────────────────────────────────────────────────────

def generate_agent_response(user_message: str, context: dict | None = None) -> str:
    """Generate a friendly library agent response."""
    system_prompt = (
        "You are a friendly, knowledgeable Library AI Agent at a university library. "
        "Help students find books, check availability, make reservations, and get academic recommendations. "
        "Be concise, helpful, and encouraging. Keep responses under 150 words."
    )

    context_str = ""
    if context:
        lines = [f"{k}: {v}" for k, v in context.items() if v]
        context_str = "\n".join(lines) + "\n\n" if lines else ""

    user_prompt = f"{context_str}Student: {user_message}"
    result = chat_with_granite(system_prompt, user_prompt, max_tokens=250, temperature=0.7)
    return result or "I'm here to help you find the perfect learning resources! What are you looking for?"


# ── Syllabus Analysis ─────────────────────────────────────────────────────────

def analyze_syllabus(syllabus_text: str) -> dict:
    """Extract required/recommended books from syllabus text."""
    system_prompt = (
        "You are a Library AI that extracts book references from course syllabi. "
        "Respond ONLY with valid JSON — no markdown fences, no extra text."
    )

    user_prompt = f"""Extract all book references from this syllabus text and return ONLY this JSON:
{{
  "required": [{{"title": "...", "author": "...", "isbn": "..."}}],
  "recommended": [{{"title": "...", "author": "...", "isbn": "..."}}],
  "topics": ["topic1", "topic2"]
}}

Syllabus text:
{syllabus_text[:2000]}"""

    try:
        text = chat_with_granite(system_prompt, user_prompt, max_tokens=400, temperature=0.1)
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass
    return {"required": [], "recommended": [], "topics": []}


# ── Book Summarization ────────────────────────────────────────────────────────

def summarize_book(title: str, author: str, description: str = "", tags: list = None) -> str:
    """
    Use IBM Granite to generate a rich academic summary of a book.
    Covers: what the book is about, who it's for, key topics, and why it matters.
    """
    system_prompt = (
        "You are an expert academic librarian. Write a concise, informative book summary "
        "for university students. Cover: what the book is about, the key topics or chapters, "
        "who it is best suited for (level/major), and why it is valuable. "
        "Keep it under 200 words. Be clear and direct."
    )

    tag_str = ", ".join(tags or [])
    user_prompt = (
        f"Book: \"{title}\" by {author}\n"
        + (f"Description: {description}\n" if description else "")
        + (f"Topics/Tags: {tag_str}\n" if tag_str else "")
        + "\nWrite a rich academic summary for a student deciding whether to read this book."
    )

    result = chat_with_granite(system_prompt, user_prompt, max_tokens=280, temperature=0.5)
    return result or f'"{title}" by {author} — {description}'


# ── Topic-based Recommendations ───────────────────────────────────────────────

def _normalize_title(t: str) -> str:
    """Strip punctuation/extra spaces for fuzzy title matching."""
    return re.sub(r'[^a-z0-9 ]', '', t.lower()).strip()


def recommend_by_topic(topic: str, catalog_books: list, student: dict | None = None) -> dict:
    """
    Given a free-text topic/query entered by the student, use IBM Granite to:
    1. Pre-filter the catalog to the most relevant ~30 books via keyword scoring.
    2. Ask Granite to rank and explain the top 5 from that filtered list.
    3. Return a structured result with ranked matches + AI commentary.
    """
    # ── Step 1: keyword-score every book against the topic ────────────────
    topic_words = [w.lower() for w in re.split(r'\W+', topic) if len(w) > 2]

    def relevance_score(book: dict) -> int:
        text = " ".join([
            book.get("title", ""), book.get("author", ""),
            book.get("subject", ""), book.get("category", ""),
            book.get("description", ""),
            " ".join(book.get("tags", [])),
        ]).lower()
        return sum(1 for w in topic_words if w in text)

    scored = sorted(catalog_books, key=relevance_score, reverse=True)
    # Take top 30 by keyword relevance; always keep at least 20 even if score=0
    top_relevant = [b for b in scored[:30] if relevance_score(b) > 0] or scored[:20]

    # Add student-major books if not already included
    if student and student.get("major"):
        major_books = [b for b in catalog_books if student["major"].lower() in b.get("subject","").lower()]
        for mb in major_books[:5]:
            if mb not in top_relevant:
                top_relevant.append(mb)

    working_catalog = top_relevant[:35]

    # ── Step 2: Build the catalog string Granite will reason over ─────────
    catalog_lines = []
    for i, b in enumerate(working_catalog, 1):
        catalog_lines.append(
            f"{i}. \"{b['title']}\" by {b['author']} "
            f"[{b['subject']} | {b.get('level','?')} | ⭐{b.get('rating','?')}] "
            f"— {b.get('description','')[:90]}"
        )
    catalog_str = "\n".join(catalog_lines)

    student_ctx = ""
    if student:
        student_ctx = (
            f"\nStudent profile:\n"
            f"- Major: {student.get('major', 'Not specified')}\n"
            f"- Year: Year {student.get('year', 1)}\n"
            f"- Current courses: {', '.join(student.get('currentCourses', [])) or 'None'}\n"
            f"- Interests: {', '.join(student.get('interests', [])) or 'None'}\n"
        )

    system_prompt = (
        "You are an expert academic librarian AI powered by IBM Granite. "
        "Your job is to recommend the most relevant books from a library catalog "
        "based on a student's topic or query. Respond ONLY with valid JSON — no markdown, no extra text."
    )

    user_prompt = f"""Student query / topic: "{topic}"
{student_ctx}
Library catalog (numbered):
{catalog_str}

Return ONLY this JSON with exactly 5 recommendations (use catalog numbers):
{{
  "topic_summary": "2-sentence explanation of this topic and why it matters academically",
  "recommendations": [
    {{
      "rank": 1,
      "catalog_number": <number from the list>,
      "title": "exact title",
      "author": "exact author",
      "why": "2–3 sentence personalised reason why this book matches the query and student profile",
      "best_for": "who this book is best for (e.g. beginners, CS majors, advanced readers)"
    }}
  ]
}}"""

    try:
        raw = chat_with_granite(system_prompt, user_prompt, max_tokens=900, temperature=0.3)
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            parsed = json.loads(json_match.group())
            enriched = []
            for rec in parsed.get("recommendations", []):
                book_obj = None
                # 1. Try catalog index number (Granite provides it) — indexes into working_catalog
                idx = rec.get("catalog_number", 0)
                if 1 <= idx <= len(working_catalog):
                    book_obj = working_catalog[idx - 1]
                # 2. Normalised exact title match in working catalog then full catalog
                if not book_obj:
                    rec_norm = _normalize_title(rec.get("title", ""))
                    book_obj = next(
                        (b for b in working_catalog if _normalize_title(b["title"]) == rec_norm),
                        None,
                    ) or next(
                        (b for b in catalog_books if _normalize_title(b["title"]) == rec_norm),
                        None,
                    )
                # 3. Partial normalised title match (first 30 chars)
                if not book_obj and rec.get("title"):
                    rec_norm = _normalize_title(rec.get("title", ""))
                    book_obj = next(
                        (b for b in catalog_books if rec_norm[:30] in _normalize_title(b["title"])),
                        None,
                    ) or next(
                        (b for b in catalog_books if _normalize_title(b["title"])[:30] in rec_norm),
                        None,
                    )
                rec["book"] = book_obj
                if book_obj:  # only include recs that resolved to a real book
                    enriched.append(rec)
            # Re-number after filtering
            for i, r in enumerate(enriched, 1):
                r["rank"] = i
            parsed["recommendations"] = enriched[:5]
            if enriched:
                return parsed
    except Exception as e:
        pass

    # Fallback: keyword-based match with generic message
    words = [w for w in re.split(r'\W+', topic.lower()) if len(w) > 3]
    fallback_books = [
        b for b in catalog_books
        if any(w in (b.get("title", "") + " " + b.get("description", "") + " " + " ".join(b.get("tags", []))).lower() for w in words)
    ][:5]
    return {
        "topic_summary": f"Books related to '{topic}' from the library catalog.",
        "recommendations": [
            {"rank": i + 1, "title": b["title"], "author": b["author"],
             "why": b.get("description", ""), "best_for": b.get("level", "all levels"), "book": b}
            for i, b in enumerate(fallback_books)
        ],
    }
