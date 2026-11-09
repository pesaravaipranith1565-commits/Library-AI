"""
Catalog Page — Library AI Agent
Browse, search and filter all books; reserve or join waitlists
"""

import streamlit as st
from services.database import BookDB, StudentDB, ReservationDB, WaitlistDB, seed_database

seed_database()

st.set_page_config(page_title="Catalog · Library AI", page_icon="📖", layout="wide")

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
        format_func=lambda i: student_names[i], index=current_idx, key="cat_profile",
    )
    st.session_state.current_student_id = student_ids[selected_idx]

    if st.session_state.current_student_id:
        s = StudentDB.get(st.session_state.current_student_id)
        if s:
            st.success(f"✅ **{s['name']}**")
            st.caption(f"{s['major']} · Year {s.get('year',1)}")

# ── Student context ────────────────────────────────────────────────────────────
student = None
if st.session_state.get("current_student_id"):
    student = StudentDB.get(st.session_state.current_student_id)

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("# 📖 Library Catalog")

# ── Filter bar ────────────────────────────────────────────────────────────────
col_search, col_subj, col_sort, col_avail = st.columns([3, 2, 2, 1])
with col_search:
    search = st.text_input("🔍 Search title, author, topic…", placeholder="e.g. machine learning, Cormen, SQL")
with col_subj:
    all_subjects = ["All subjects"] + BookDB.subjects()
    subject_filter = st.selectbox("📂 Subject", all_subjects)
with col_sort:
    sort_by = st.selectbox("↕️ Sort", ["Default", "Most Popular", "Highest Rated", "A → Z"])
with col_avail:
    available_only = st.checkbox("Available only", value=False)

st.divider()

# ── Load & filter books ────────────────────────────────────────────────────────
subj = "" if subject_filter == "All subjects" else subject_filter
books = BookDB.all(search=search, subject=subj, available_only=available_only)

if sort_by == "Most Popular":
    books = sorted(books, key=lambda b: b.get("borrowedCount", 0), reverse=True)
elif sort_by == "Highest Rated":
    books = sorted(books, key=lambda b: b.get("rating", 0), reverse=True)
elif sort_by == "A → Z":
    books = sorted(books, key=lambda b: b.get("title", "").lower())

st.caption(f"Showing **{len(books)}** book(s)")

if not books:
    st.info("No books found. Try adjusting your search or filters.")
    st.stop()

# ── Book cards ─────────────────────────────────────────────────────────────────
def render_book_card(book: dict, idx: int):
    avail = book.get("availableCopies", 0)
    total = book.get("totalCopies", avail)
    badge = "🟢 Available" if avail > 2 else ("🟡 Limited" if avail > 0 else "🔴 Unavailable")

    with st.expander(
        f"{'📗' if avail > 0 else '📕'} **{book['title']}**  —  _{book['author']}_  ·  {badge}",
        expanded=False,
    ):
        c1, c2 = st.columns([3, 1])
        with c1:
            if book.get("description"):
                st.write(book["description"])
            tags = [book.get("subject", ""), book.get("category", ""), book.get("level", "")]
            tags = [t for t in tags if t]
            if tags:
                st.caption("🏷️ " + "  ·  ".join(tags))
            if book.get("tags"):
                st.caption("🔖 " + ", ".join(book["tags"][:6]))
        with c2:
            st.metric("Available", f"{avail} / {total}")
            if book.get("rating"):
                st.metric("Rating", f"⭐ {book['rating']}")
            if book.get("borrowedCount") is not None:
                st.metric("Borrows", f"📤 {book['borrowedCount']}")
            if book.get("year"):
                st.caption(f"📅 {book.get('edition','')} edition · {book['year']}")
            if book.get("isbn"):
                st.caption(f"📘 ISBN: {book['isbn']}")

        # Action buttons
        if student:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if avail > 0:
                    if st.button("📌 Reserve", key=f"res_{book['id']}_{idx}", use_container_width=True, type="primary"):
                        if ReservationDB.has_active(student["id"], book["id"]):
                            st.warning("You already have an active reservation for this book.")
                        else:
                            if BookDB.decrement_available(book["id"]):
                                ReservationDB.create(student["id"], book["id"], book["title"], student["name"])
                                StudentDB.add_to_history(student["id"], book["id"])
                                st.success(f"✅ Reserved **\"{book['title']}\"**! Due in 14 days.")
                                st.rerun()
                            else:
                                st.error("Book became unavailable. Please refresh.")
                else:
                    if st.button("📋 Join Waitlist", key=f"wl_{book['id']}_{idx}", use_container_width=True):
                        if WaitlistDB.is_on_waitlist(book["id"], student["id"]):
                            pos = WaitlistDB.position(book["id"], student["id"])
                            st.info(f"You are already on the waitlist at position #{pos}")
                        else:
                            entry = WaitlistDB.join(book["id"], student["id"])
                            st.success(f"📋 Added to waitlist at position **#{entry['position']}**")
                            st.rerun()
            with btn_col2:
                wl = WaitlistDB.for_book(book["id"])
                if wl:
                    st.caption(f"⏳ {len(wl)} on waitlist")
        else:
            st.info("Select a student profile in the sidebar to reserve books.")


for i, book in enumerate(books):
    render_book_card(book, i)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#888; font-size:0.85rem;'>"
    "Library AI Agent · Powered by <strong>IBM Granite</strong> on watsonx.ai</p>",
    unsafe_allow_html=True,
)
