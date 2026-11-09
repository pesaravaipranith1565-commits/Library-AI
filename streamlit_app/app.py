"""
Library AI Agent — Streamlit Application
Main entry point (Dashboard page)
Powered by IBM Granite on watsonx.ai (IBM Cloud Lite)
"""

import streamlit as st
from services.database import seed_database, BookDB, StudentDB, ReservationDB

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="Library AI Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "Library AI Agent — Powered by IBM Granite on watsonx.ai",
    },
)

# ── Bootstrap DB on first run ──────────────────────────────────────────────────
seed_database()

# ── Session state defaults ─────────────────────────────────────────────────────
if "current_student_id" not in st.session_state:
    st.session_state.current_student_id = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ── Sidebar — profile selector ─────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg", width=80)
    st.markdown("## 📚 Library AI Agent")
    st.caption("Powered by **IBM Granite** · watsonx.ai")
    st.divider()

    students = StudentDB.all()
    student_names = ["— Select your profile —"] + [f"{s['name']} ({s['major']})" for s in students]
    student_ids = [None] + [s["id"] for s in students]

    current_idx = 0
    if st.session_state.current_student_id:
        try:
            current_idx = student_ids.index(st.session_state.current_student_id)
        except ValueError:
            current_idx = 0

    selected_idx = st.selectbox(
        "👤 Active Profile",
        range(len(student_names)),
        format_func=lambda i: student_names[i],
        index=current_idx,
        key="profile_selector",
    )
    st.session_state.current_student_id = student_ids[selected_idx]

    if st.session_state.current_student_id:
        s = next((x for x in students if x["id"] == st.session_state.current_student_id), None)
        if s:
            st.success(f"✅ Active: **{s['name']}**")
            st.caption(f"📖 {s['major']} · Year {s.get('year', 1)}")
            if s.get("currentCourses"):
                st.caption(f"📚 {', '.join(s['currentCourses'][:2])}")
    else:
        st.info("Select a profile for personalized AI recommendations")

    st.divider()
    st.caption("🗄️ IBM Cloud Lite")
    st.caption("🤖 IBM Granite · `ibm/granite-4-h-small`")

# ── Dashboard content ──────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align:center; padding: 12px 0 4px 0;">
    <h1 style="font-size:2.4rem; font-weight:800; margin-bottom:4px;">📚 Library AI Agent</h1>
    <p style="color:#6c757d; font-size:1.05rem;">
        Intelligent academic library assistant powered by <strong>IBM Granite</strong> on <strong>watsonx.ai</strong>
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Stats row ──────────────────────────────────────────────────────────────────
all_books = BookDB.all()
available_books = [b for b in all_books if b.get("availableCopies", 0) > 0]
subjects = BookDB.subjects()
all_students = StudentDB.all()

current_student = None
my_reservations = []
if st.session_state.current_student_id:
    current_student = StudentDB.get(st.session_state.current_student_id)
    my_reservations = ReservationDB.active_for_student(st.session_state.current_student_id)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📚 Total Books", len(all_books))
with col2:
    st.metric("✅ Available Now", len(available_books))
with col3:
    st.metric("🎓 Subjects", len(subjects))
with col4:
    if current_student:
        st.metric("📌 My Reservations", len(my_reservations))
    else:
        st.metric("👥 Students", len(all_students))

st.divider()

# ── Welcome / hero ─────────────────────────────────────────────────────────────
if current_student:
    st.markdown(f"### 👋 Welcome back, **{current_student['name'].split()[0]}**!")
    st.write(f"You are logged in as a **Year {current_student.get('year',1)} {current_student['major']}** student.")

    if my_reservations:
        st.markdown("#### 📌 Your Active Reservations")
        for r in my_reservations[:3]:
            book = BookDB.get(r["bookId"])
            due = r.get("dueDate", "")[:10]
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{book['title'] if book else r.get('bookTitle','?')}**")
                    if book:
                        st.caption(f"by {book['author']}")
                with c2:
                    st.caption(f"Due: **{due}**")
else:
    st.info("👆 Select your student profile in the sidebar to get personalised AI recommendations, track reservations, and more.")

# ── Popular books ──────────────────────────────────────────────────────────────
st.markdown("### 🔥 Most Popular Books")
popular = BookDB.popular(8)

cols = st.columns(4)
for i, book in enumerate(popular[:8]):
    avail = book.get("availableCopies", 0)
    badge = "🟢" if avail > 2 else ("🟡" if avail > 0 else "🔴")
    with cols[i % 4]:
        with st.container(border=True):
            st.markdown(f"**{book['title'][:35]}{'…' if len(book['title'])>35 else ''}**")
            st.caption(f"{book['author'][:30]}")
            st.caption(f"{badge} {avail} available · ⭐ {book.get('rating','?')}")
            st.caption(f"📤 {book.get('borrowedCount',0)} borrows")

st.divider()

# ── Feature cards ──────────────────────────────────────────────────────────────
st.markdown("### ✨ What can Library AI Agent do?")

features = [
    ("🔍", "Semantic Search", "Ask in plain English — IBM Granite NLP understands your intent"),
    ("⭐", "Personalised Picks", "AI recommendations tailored to your major, courses & interests"),
    ("📊", "Real-time Availability", "Check all copies instantly — reserve or join the waitlist"),
    ("📋", "Smart Reservations", "One-click reservations with 14-day due dates & waitlist tracking"),
    ("🎓", "Syllabus Analysis", "Paste a syllabus — AI finds every book in the catalog"),
    ("🤖", "IBM Granite Powered", "Enterprise LLM on IBM watsonx.ai (IBM Cloud Lite)"),
]

f_cols = st.columns(3)
for i, (icon, title, desc) in enumerate(features):
    with f_cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"### {icon} {title}")
            st.caption(desc)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#888; font-size:0.85rem;'>"
    "Library AI Agent · Powered by <strong>IBM Granite</strong> on watsonx.ai · IBM Cloud Lite"
    "</p>",
    unsafe_allow_html=True,
)
