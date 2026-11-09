"""
Reservations Page — Library AI Agent
View active reservations, waitlists, and history
"""

import streamlit as st
from services.database import BookDB, StudentDB, ReservationDB, WaitlistDB, seed_database
from datetime import datetime

seed_database()

st.set_page_config(page_title="Reservations · Library AI", page_icon="📋", layout="wide")

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
        format_func=lambda i: student_names[i], index=current_idx, key="res_profile",
    )
    st.session_state.current_student_id = student_ids[selected_idx]

    if st.session_state.current_student_id:
        s = StudentDB.get(st.session_state.current_student_id)
        if s:
            st.success(f"✅ **{s['name']}**")
            st.caption(f"{s['major']} · Year {s.get('year',1)}")

# ── Guard: no profile selected ─────────────────────────────────────────────────
student = None
if st.session_state.get("current_student_id"):
    student = StudentDB.get(st.session_state.current_student_id)

st.markdown("# 📋 My Reservations")

if not student:
    st.warning("👆 Please select your student profile from the sidebar to view reservations.")
    st.stop()

st.caption(f"Viewing reservations for **{student['name']}** · {student['major']} · Year {student.get('year',1)}")
st.divider()

# ── Load data ──────────────────────────────────────────────────────────────────
all_res = ReservationDB.all_for_student(student["id"])
active_res = [r for r in all_res if r.get("status") == "active"]
history_res = [r for r in all_res if r.get("status") != "active"]
waitlist_entries = WaitlistDB.for_student(student["id"])

# ── Summary metrics ────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("📌 Active Reservations", len(active_res))
with c2:
    st.metric("⏳ Waitlists", len(waitlist_entries))
with c3:
    st.metric("📜 History", len(history_res))

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_active, tab_waitlist, tab_history = st.tabs([
    f"📌 Active ({len(active_res)})",
    f"⏳ Waitlists ({len(waitlist_entries)})",
    f"📜 History ({len(history_res)})",
])

# ── Active Reservations ────────────────────────────────────────────────────────
with tab_active:
    if not active_res:
        st.info("No active reservations. Browse the **📖 Catalog** to reserve a book!")
    else:
        for r in active_res:
            book = BookDB.get(r["bookId"])
            reserved_date = r.get("reservedAt", "")[:10]
            due_date = r.get("dueDate", "")[:10]

            # Check if overdue
            overdue = False
            if due_date:
                try:
                    overdue = datetime.fromisoformat(r["dueDate"]) < datetime.utcnow()
                except Exception:
                    pass

            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.markdown(f"**{book['title'] if book else r.get('bookTitle','Unknown')}**")
                    if book:
                        st.caption(f"by {book['author']} · {book.get('subject','')}")
                    st.caption(f"Reserved: {reserved_date}")
                with col2:
                    if overdue:
                        st.error(f"⚠️ OVERDUE · Due: {due_date}")
                    else:
                        st.info(f"📅 Due: **{due_date}**")
                with col3:
                    if st.button("❌ Cancel", key=f"cancel_{r['id']}", use_container_width=True):
                        ReservationDB.cancel(r["id"])
                        BookDB.increment_available(r["bookId"])
                        st.success("Reservation cancelled. Copy returned to shelf.")
                        st.rerun()

# ── Waitlists ──────────────────────────────────────────────────────────────────
with tab_waitlist:
    if not waitlist_entries:
        st.info("You are not on any waitlists. Join a waitlist from the **📖 Catalog** for unavailable books.")
    else:
        for entry in waitlist_entries:
            book = BookDB.get(entry["bookId"])
            joined_date = entry.get("joinedAt", "")[:10]
            est_wait = entry.get("position", 1) * 14

            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.markdown(f"**{book['title'] if book else 'Unknown Book'}**")
                    if book:
                        st.caption(f"by {book['author']}")
                    st.caption(f"Joined: {joined_date}")
                with col2:
                    st.metric("Queue Position", f"#{entry.get('position', '?')}")
                    st.caption(f"~{est_wait} days estimated")
                with col3:
                    if st.button("🚪 Leave", key=f"leave_{entry['id']}", use_container_width=True):
                        WaitlistDB.leave(entry["bookId"], student["id"])
                        st.success("Removed from waitlist.")
                        st.rerun()

# ── History ────────────────────────────────────────────────────────────────────
with tab_history:
    if not history_res:
        st.info("No reservation history yet.")
    else:
        for r in history_res:
            book = BookDB.get(r["bookId"])
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{book['title'] if book else r.get('bookTitle','Unknown')}**")
                    if book:
                        st.caption(f"by {book['author']}")
                with col2:
                    status = r.get("status", "unknown")
                    if status == "cancelled":
                        st.error("🚫 Cancelled")
                    else:
                        st.success("✅ Returned")
                    reserved_date = r.get("reservedAt", "")[:10]
                    st.caption(f"{reserved_date}")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#888; font-size:0.85rem;'>"
    "Library AI Agent · Powered by <strong>IBM Granite</strong> on watsonx.ai</p>",
    unsafe_allow_html=True,
)
