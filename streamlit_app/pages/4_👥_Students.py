"""
Students Page — Library AI Agent
Create and manage student profiles
"""

import streamlit as st
from services.database import StudentDB, BookDB, ReservationDB, seed_database

seed_database()

st.set_page_config(page_title="Students · Library AI", page_icon="👥", layout="wide")

MAJORS = [
    "Computer Science", "Data Science", "Artificial Intelligence",
    "Mathematics", "Physics", "Electrical Engineering",
    "Business Administration", "Economics", "Information Technology", "Other",
]

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg", width=80)
    st.markdown("## 📚 Library AI Agent")
    st.caption("Powered by **IBM Granite** · watsonx.ai")
    st.divider()

    students_sidebar = StudentDB.all()
    student_names = ["— Select your profile —"] + [f"{s['name']} ({s['major']})" for s in students_sidebar]
    student_ids = [None] + [s["id"] for s in students_sidebar]

    current_idx = 0
    if st.session_state.get("current_student_id"):
        try:
            current_idx = student_ids.index(st.session_state.current_student_id)
        except ValueError:
            current_idx = 0

    selected_idx = st.selectbox(
        "👤 Active Profile", range(len(student_names)),
        format_func=lambda i: student_names[i], index=current_idx, key="stu_profile",
    )
    st.session_state.current_student_id = student_ids[selected_idx]

    if st.session_state.current_student_id:
        s = StudentDB.get(st.session_state.current_student_id)
        if s:
            st.success(f"✅ **{s['name']}**")

# ── Page ───────────────────────────────────────────────────────────────────────
st.markdown("# 👥 Student Profiles")
st.caption("Create a profile for personalised AI book recommendations. Select a profile to set it as active.")
st.divider()

# ── Existing students grid ─────────────────────────────────────────────────────
students = StudentDB.all()
if students:
    st.markdown(f"### Registered Students ({len(students)})")
    cols = st.columns(3)
    for i, s in enumerate(students):
        is_active = s["id"] == st.session_state.get("current_student_id")
        active_res = ReservationDB.active_for_student(s["id"])
        with cols[i % 3]:
            with st.container(border=True):
                # Header row
                hcol1, hcol2 = st.columns([3, 1])
                with hcol1:
                    st.markdown(f"### {s['name']}")
                with hcol2:
                    if is_active:
                        st.success("Active")

                st.caption(f"🎓 {s.get('major','?')} · Year {s.get('year',1)}")
                if s.get("studentId"):
                    st.caption(f"🆔 {s['studentId']}")
                if s.get("currentCourses"):
                    st.caption("📚 " + ", ".join(s["currentCourses"][:3]))
                if s.get("interests"):
                    st.caption("💡 " + ", ".join(s["interests"][:3]))
                st.caption(f"📌 {len(active_res)} active reservation(s)")

                # Activate button
                if not is_active:
                    if st.button(f"✅ Select Profile", key=f"sel_{s['id']}", use_container_width=True, type="primary"):
                        st.session_state.current_student_id = s["id"]
                        st.success(f"Profile set to {s['name']}")
                        st.rerun()
                else:
                    if st.button("🚪 Deselect", key=f"desel_{s['id']}", use_container_width=True):
                        st.session_state.current_student_id = None
                        st.rerun()

    st.divider()

# ── Create new profile form ────────────────────────────────────────────────────
st.markdown("### ➕ Create New Profile")

with st.form("new_student_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *", placeholder="Jane Smith")
        email = st.text_input("Email *", placeholder="jane@university.edu")
        student_id_val = st.text_input("Student ID", placeholder="STU12345")
    with col2:
        major = st.selectbox("Major", MAJORS)
        year = st.selectbox("Academic Year", [1, 2, 3, 4, 5], format_func=lambda y: f"Year {y}")

    courses_raw = st.text_input(
        "Current Courses",
        placeholder="Algorithms, Database Systems, Operating Systems",
        help="Comma-separated list of your current courses"
    )
    interests_raw = st.text_input(
        "Study Interests",
        placeholder="machine learning, web development, data visualization",
        help="Comma-separated list — used by AI for better recommendations"
    )

    submitted = st.form_submit_button("✅ Create Profile", type="primary", use_container_width=True)

    if submitted:
        if not name.strip() or not email.strip():
            st.error("Name and email are required.")
        elif StudentDB.get_by_email(email.strip()):
            st.error(f"A student with email **{email}** already exists.")
        else:
            courses = [c.strip() for c in courses_raw.split(",") if c.strip()]
            interests = [x.strip() for x in interests_raw.split(",") if x.strip()]
            student = StudentDB.create({
                "name": name.strip(),
                "email": email.strip(),
                "studentId": student_id_val.strip(),
                "major": major,
                "year": year,
                "currentCourses": courses,
                "interests": interests,
            })
            st.session_state.current_student_id = student["id"]
            st.success(f"🎉 Profile created for **{student['name']}**! Profile set as active.")
            st.rerun()

# ── Reading history section ────────────────────────────────────────────────────
if st.session_state.get("current_student_id"):
    active_student = StudentDB.get(st.session_state.current_student_id)
    if active_student and active_student.get("readingHistory"):
        st.divider()
        st.markdown(f"### 📚 {active_student['name']}'s Reading History")
        history_books = [BookDB.get(bid) for bid in active_student["readingHistory"] if BookDB.get(bid)]
        if history_books:
            h_cols = st.columns(4)
            for i, book in enumerate(history_books[-8:]):
                with h_cols[i % 4]:
                    with st.container(border=True):
                        st.caption(f"**{book['title'][:35]}**")
                        st.caption(book["author"][:30])
        else:
            st.caption("No reading history yet.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#888; font-size:0.85rem;'>"
    "Library AI Agent · Powered by <strong>IBM Granite</strong> on watsonx.ai</p>",
    unsafe_allow_html=True,
)
