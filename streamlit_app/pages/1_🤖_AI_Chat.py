"""
AI Chat Page — Library AI Agent
Conversational interface powered by IBM Granite on watsonx.ai
"""

import streamlit as st
from services.database import BookDB, StudentDB, ReservationDB, WaitlistDB, ChatDB, seed_database
from services.granite_service import understand_query, generate_recommendations, generate_agent_response, analyze_syllabus

seed_database()

st.set_page_config(page_title="AI Chat · Library AI", page_icon="🤖", layout="wide")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg", width=80)
    st.markdown("## 📚 Library AI Agent")
    st.caption("Powered by **IBM Granite** · watsonx.ai")
    st.divider()

    students = StudentDB.all()
    student_names = ["— Select your profile —"] + [f"{s['name']} ({s['major']})" for s in students]
    student_ids = [None] + [s["id"] for s in students]

    current_idx = 0
    if st.session_state.get("current_student_id"):
        try:
            current_idx = student_ids.index(st.session_state.current_student_id)
        except ValueError:
            current_idx = 0

    selected_idx = st.selectbox(
        "👤 Active Profile", range(len(student_names)),
        format_func=lambda i: student_names[i], index=current_idx, key="chat_profile",
    )
    st.session_state.current_student_id = student_ids[selected_idx]

    if st.session_state.current_student_id:
        s = StudentDB.get(st.session_state.current_student_id)
        if s:
            st.success(f"✅ **{s['name']}**")
            st.caption(f"{s['major']} · Year {s.get('year',1)}")

    st.divider()
    st.markdown("### 💡 Quick Prompts")
    quick_prompts = [
        "Recommend books for my major",
        "Find machine learning books",
        "Is Introduction to Algorithms available?",
        "I want to reserve Clean Code",
        "Find books for my current syllabus",
        "What are the most popular books?",
        "I need beginner Python books",
    ]
    for prompt in quick_prompts:
        if st.button(f"💬 {prompt}", key=f"qp_{prompt}", use_container_width=True):
            st.session_state.pending_message = prompt

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

# ── Init session state ─────────────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "pending_message" not in st.session_state:
    st.session_state.pending_message = None
if "syllabus_mode" not in st.session_state:
    st.session_state.syllabus_mode = False

student = None
if st.session_state.get("current_student_id"):
    student = StudentDB.get(st.session_state.current_student_id)

# ── Welcome message ────────────────────────────────────────────────────────────
if not st.session_state.chat_messages:
    greeting = f"Hello{', ' + student['name'].split()[0] if student else ''}! 👋\n\n"
    greeting += "I'm your **Library AI Agent**, powered by **IBM Granite** on watsonx.ai.\n\n"
    greeting += "I can help you:\n"
    greeting += "- 🔍 Find books by topic, course, or keyword\n"
    greeting += "- ⭐ Get personalised recommendations\n"
    greeting += "- 📊 Check real-time book availability\n"
    greeting += "- 📌 Reserve books or join waitlists\n"
    greeting += "- 🎓 Find resources for your syllabus\n\n"
    greeting += "What are you looking for today?"
    st.session_state.chat_messages.append({"role": "assistant", "content": greeting, "books": []})

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("# 🤖 AI Library Agent")
st.caption("Ask anything about books, availability, or get personalised recommendations · IBM Granite NLP")
st.divider()

# ── Chat display ───────────────────────────────────────────────────────────────
chat_container = st.container()

with chat_container:
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

            # Show book cards if present
            if msg.get("books"):
                books = msg["books"][:6]
                cols = st.columns(min(len(books), 3))
                for i, book in enumerate(books):
                    avail = book.get("availableCopies", 0)
                    badge = "🟢" if avail > 2 else ("🟡" if avail == 1 else ("🔴" if avail == 0 else "🟡"))
                    with cols[i % 3]:
                        with st.container(border=True):
                            st.markdown(f"**{book['title'][:40]}{'…' if len(book['title'])>40 else ''}**")
                            st.caption(f"{book['author'][:35]}")
                            st.caption(f"{badge} {avail} available · ⭐ {book.get('rating','?')}")
                            if book.get("subject"):
                                st.caption(f"🏷️ {book['subject']}")
                            # Reserve / Waitlist button
                            if student:
                                btn_label = "📌 Reserve" if avail > 0 else "📋 Waitlist"
                                btn_key = f"chat_btn_{book['id']}_{id(msg)}"
                                if st.button(btn_label, key=btn_key, use_container_width=True):
                                    _sid = student["id"]
                                    if avail > 0:
                                        if ReservationDB.has_active(_sid, book["id"]):
                                            st.toast("⚠️ Already reserved!", icon="⚠️")
                                        else:
                                            BookDB.decrement_available(book["id"])
                                            ReservationDB.create(_sid, book["id"], book["title"], student["name"])
                                            StudentDB.add_to_history(_sid, book["id"])
                                            st.toast(f"✅ Reserved '{book['title']}'!", icon="✅")
                                    else:
                                        if WaitlistDB.is_on_waitlist(book["id"], _sid):
                                            st.toast("⚠️ Already on waitlist!", icon="⚠️")
                                        else:
                                            entry = WaitlistDB.join(book["id"], _sid)
                                            st.toast(f"📋 Joined waitlist at position #{entry['position']}", icon="📋")

            # Show NLP debug if present
            if msg.get("understanding") and st.session_state.get("show_debug"):
                with st.expander("🔍 NLP Understanding"):
                    u = msg["understanding"]
                    st.json(u)


# ── Syllabus mode toggle ───────────────────────────────────────────────────────
col_syl, col_dbg = st.columns([1, 1])
with col_syl:
    if st.button("📄 Analyze Syllabus" if not st.session_state.syllabus_mode else "❌ Cancel Syllabus Mode",
                 use_container_width=True):
        st.session_state.syllabus_mode = not st.session_state.syllabus_mode
        st.rerun()
with col_dbg:
    st.session_state.show_debug = st.toggle("🔍 Show NLP debug")


# ── Input handling ─────────────────────────────────────────────────────────────
def process_message(user_input: str):
    """Core message processing: NLP → intent routing → response."""
    st.session_state.chat_messages.append({"role": "user", "content": user_input, "books": []})

    with st.spinner("🤖 IBM Granite is thinking..."):
        # Step 1: NLP understanding
        understanding = understand_query(user_input, student)
        intent = understanding.get("intent", "search_book")
        keywords = understanding.get("keywords", [user_input])
        subject = understanding.get("subject", user_input)
        book_title = understanding.get("bookTitle")

        response_text = ""
        response_books = []

        # Step 2: Route by intent
        if intent == "search_book":
            books = BookDB.semantic_search(keywords + [subject])
            if books:
                response_text = f"I found **{len(books)}** book(s) matching your query about **\"{subject}\"**. Here are the top results:"
                response_books = books[:6]
            else:
                response_text = f"I couldn't find books specifically about **\"{subject}\"**. Here are our most popular titles:"
                response_books = BookDB.popular(6)

        elif intent == "get_recommendation":
            if not student:
                response_text = "To give you personalised recommendations, please select your student profile from the sidebar first!"
            else:
                all_books = BookDB.all()
                response_text = generate_recommendations(student, all_books, subject)
                kws = (student.get("interests", []) or []) + (student.get("currentCourses", []) or [])
                response_books = BookDB.semantic_search(kws)[:6]

        elif intent == "check_availability":
            search_term = book_title or subject
            books = BookDB.semantic_search([search_term] + keywords)
            if not books:
                response_text = f"I couldn't find **\"{search_term}\"** in our catalog. Try searching by a different title or keyword."
            else:
                book = books[0]
                avail = book.get("availableCopies", 0)
                if avail > 0:
                    response_text = f"✅ **Good news!** *\"{book['title']}\"* by {book['author']} is **available** — {avail} of {book.get('totalCopies',avail)} copies are currently free."
                else:
                    wl = WaitlistDB.for_book(book["id"])
                    response_text = f"📋 *\"{book['title']}\"* is **fully borrowed** (all {book.get('totalCopies','?')} copies out). There are **{len(wl)}** people on the waitlist. Would you like to join?"
                response_books = books[:4]

        elif intent == "reserve_book":
            search_term = book_title or subject
            books = BookDB.semantic_search([search_term] + keywords)
            if books and student:
                book = books[0]
                avail = book.get("availableCopies", 0)
                response_text = (
                    f"*\"{book['title']}\"* is **available**! Use the Reserve button below to complete your reservation."
                    if avail > 0 else
                    f"*\"{book['title']}\"* is **fully borrowed** right now. You can join the waitlist and be notified when it returns!"
                )
                response_books = books[:3]
            elif not student:
                response_text = "Please select your student profile from the sidebar before making a reservation."
            else:
                response_text = f"I couldn't find a book titled **\"{search_term}\"**. Try searching the Catalog page directly."

        elif intent == "join_waitlist":
            search_term = book_title or subject
            books = BookDB.semantic_search([search_term] + keywords)
            if books:
                book = books[0]
                wl = WaitlistDB.for_book(book["id"])
                est_days = len(wl) * 14
                response_text = f"The waitlist for *\"{book['title']}\"* has **{len(wl)}** student(s) — estimated wait is about **{est_days} days**. Use the Waitlist button below."
                response_books = books[:2]
            else:
                response_text = "Please specify which book you'd like to join the waitlist for."

        elif intent == "get_syllabus_books":
            if student and student.get("currentCourses"):
                kws = student.get("currentCourses", [])
                books = BookDB.semantic_search(kws)
                response_text = f"Based on your courses (**{', '.join(kws)}**), here are the books most relevant to your syllabus:"
                response_books = books[:8]
            else:
                response_text = "Please add your current courses to your student profile, or use the **📄 Analyze Syllabus** button to paste your course syllabus text directly!"

        else:  # general_help
            ctx = {}
            if student:
                ctx = {"Student name": student["name"], "Major": student.get("major"), "Courses": ", ".join(student.get("currentCourses", []))}
            response_text = generate_agent_response(user_input, ctx) or "I'm here to help! What would you like to know?"
            response_books = BookDB.popular(4)

        # Save to DB
        if student:
            ChatDB.save(student["id"], "user", user_input)
            ChatDB.save(student["id"], "assistant", response_text, {"intent": intent})

        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response_text,
            "books": response_books,
            "understanding": understanding,
        })


def process_syllabus(text: str):
    """Process pasted syllabus and find matching books."""
    st.session_state.chat_messages.append({
        "role": "user",
        "content": f"📄 **Syllabus Analysis Request**\n\n_{text[:200]}..._",
        "books": [],
    })

    with st.spinner("🔍 IBM Granite analysing syllabus..."):
        analysis = analyze_syllabus(text)
        all_mentioned = (analysis.get("required", []) or []) + (analysis.get("recommended", []) or [])
        catalog_books = []
        for m in all_mentioned:
            found = BookDB.semantic_search([m.get("title", ""), m.get("author", "")])
            if found:
                catalog_books.append(found[0])

        topic_books = BookDB.semantic_search(analysis.get("topics", []))
        all_books = catalog_books + [b for b in topic_books if b["id"] not in {x["id"] for x in catalog_books}]

        n_req = len(analysis.get("required", []))
        n_rec = len(analysis.get("recommended", []))
        topics_str = ", ".join(analysis.get("topics", [])[:5]) or "N/A"

        response_text = (
            f"📚 **Syllabus Analysis Complete!**\n\n"
            f"Found **{n_req}** required and **{n_rec}** recommended books.\n\n"
            f"**Topics covered:** {topics_str}\n\n"
            f"Here are the matching books in our catalog:"
        )

        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response_text,
            "books": all_books[:6],
        })
        st.session_state.syllabus_mode = False


# ── Handle pending quick-prompt message ───────────────────────────────────────
if st.session_state.pending_message:
    msg = st.session_state.pending_message
    st.session_state.pending_message = None
    process_message(msg)
    st.rerun()

# ── Syllabus input ─────────────────────────────────────────────────────────────
if st.session_state.syllabus_mode:
    st.info("📄 **Syllabus mode** — paste your course syllabus below")
    syl_text = st.text_area("Paste syllabus text here:", height=160, placeholder="Course: CS301 — Algorithms\nRequired: Introduction to Algorithms by Cormen...")
    if st.button("🔍 Analyse Syllabus", type="primary"):
        if syl_text.strip():
            process_syllabus(syl_text.strip())
            st.rerun()
        else:
            st.warning("Please paste your syllabus text first.")

# ── Chat input ─────────────────────────────────────────────────────────────────
else:
    user_msg = st.chat_input("Ask me anything — find books, check availability, get recommendations...")
    if user_msg:
        process_message(user_msg)
        st.rerun()
