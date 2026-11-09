"""
Recommendations Page — Library AI Agent
IBM Granite-powered book recommendations and summarizations for ANY topic or book.
Students can type any subject, topic, book title, or course name and get:
  - AI-ranked top 5 recommendations from the full 75-book catalog
  - Personalised explanation for each recommendation
  - On-demand IBM Granite book summaries
  - Subject-wise browsing with AI overview
"""

import streamlit as st
from services.database import BookDB, StudentDB, ReservationDB, WaitlistDB, seed_database
from services.granite_service import (
    recommend_by_topic,
    summarize_book,
    generate_recommendations,
)

seed_database()

st.set_page_config(
    page_title="Recommendations · Library AI",
    page_icon="⭐",
    layout="wide",
)

# ── Subject metadata ───────────────────────────────────────────────────────────
SUBJECT_META = {
    "Computer Science":       {"icon": "💻", "color": "#0f62fe", "desc": "Programming, algorithms, databases, networks, OS"},
    "Artificial Intelligence":{"icon": "🤖", "color": "#8a3ffc", "desc": "ML, deep learning, NLP, reinforcement learning, AI theory"},
    "Data Science":           {"icon": "📊", "color": "#009d9a", "desc": "Data analysis, visualisation, pandas, statistics, ML pipelines"},
    "Mathematics":            {"icon": "📐", "color": "#ff832b", "desc": "Calculus, linear algebra, discrete math, statistics, abstract algebra"},
    "Physics":                {"icon": "⚛️",  "color": "#da1e28", "desc": "Mechanics, electromagnetism, quantum mechanics, modern physics"},
    "Economics":              {"icon": "📈", "color": "#24a148", "desc": "Micro/macroeconomics, behavioural economics, finance, theory"},
    "Business":               {"icon": "💼", "color": "#f1c21b", "desc": "Strategy, marketing, accounting, entrepreneurship, leadership"},
    "Engineering":            {"icon": "⚙️",  "color": "#6ea6ff", "desc": "Mechanical, electrical, thermodynamics, signal processing"},
    "Chemistry":              {"icon": "🧪", "color": "#ee538b", "desc": "General, organic, physical, analytical chemistry, biochemistry"},
    "Biology":                {"icon": "🧬", "color": "#42be65", "desc": "Cell biology, genetics, evolution, neuroscience, ecology"},
    "Psychology":             {"icon": "🧠", "color": "#be95ff", "desc": "Cognitive, social, clinical psychology, behavioural science"},
    "Medicine":               {"icon": "🏥", "color": "#fa4d56", "desc": "Anatomy, pathology, physiology, internal medicine, public health"},
    "Law":                    {"icon": "⚖️",  "color": "#bdd9ff", "desc": "Constitutional, contract, tort, international law"},
    "Environmental Science":  {"icon": "🌿", "color": "#a7f0ba", "desc": "Ecology, climate change, sustainability, renewable energy"},
    "History":                {"icon": "📜", "color": "#d2a106", "desc": "World history, ancient civilisations, modern history, anthropology"},
    "Literature":             {"icon": "📝", "color": "#ff7eb6", "desc": "Creative writing, literary theory, anthologies, writing craft"},
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg", width=80)
    st.markdown("## 📚 Library AI Agent")
    st.caption("Powered by **IBM Granite** · watsonx.ai")
    st.divider()

    students = StudentDB.all()
    student_names = ["— No profile —"] + [f"{s['name']} ({s['major']})" for s in students]
    student_ids  = [None] + [s["id"] for s in students]

    current_idx = 0
    if st.session_state.get("current_student_id"):
        try:
            current_idx = student_ids.index(st.session_state.current_student_id)
        except ValueError:
            current_idx = 0

    sel = st.selectbox(
        "👤 Active Profile", range(len(student_names)),
        format_func=lambda i: student_names[i], index=current_idx, key="rec_profile",
    )
    st.session_state.current_student_id = student_ids[sel]

    if st.session_state.current_student_id:
        s = StudentDB.get(st.session_state.current_student_id)
        if s:
            st.success(f"✅ **{s['name']}**")
            st.caption(f"{s['major']} · Year {s.get('year',1)}")

    st.divider()
    st.markdown("### 🏷️ Browse by Subject")
    subjects = BookDB.subjects()
    for subj in subjects:
        meta = SUBJECT_META.get(subj, {"icon": "📚"})
        if st.button(f"{meta['icon']} {subj}", key=f"nav_{subj}", use_container_width=True):
            st.session_state.selected_subject = subj
            st.session_state.rec_mode = "subject"
            st.rerun()

# ── Student context ────────────────────────────────────────────────────────────
student = None
if st.session_state.get("current_student_id"):
    student = StudentDB.get(st.session_state.current_student_id)

# ── Session state defaults ─────────────────────────────────────────────────────
if "rec_mode"        not in st.session_state: st.session_state.rec_mode = "topic"
if "selected_subject" not in st.session_state: st.session_state.selected_subject = None
if "rec_results"     not in st.session_state: st.session_state.rec_results = None
if "last_topic"      not in st.session_state: st.session_state.last_topic = ""
if "summary_cache"   not in st.session_state: st.session_state.summary_cache = {}

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("# ⭐ AI Book Recommendations")
st.caption(
    "Type **any topic, subject, book title or course name** and IBM Granite will recommend "
    "the best books from our full catalog — with personalised explanations and on-demand summaries."
)
st.divider()

# ── Mode tabs ─────────────────────────────────────────────────────────────────
tab_topic, tab_subject, tab_personal = st.tabs([
    "🔍 Topic / Book Search",
    "🏷️ Browse by Subject",
    "👤 My Personalised Picks",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Free-text topic search + IBM Granite recommendations + summaries
# ══════════════════════════════════════════════════════════════════════════════
with tab_topic:
    st.markdown("### 🔍 What do you want to learn about?")
    st.caption(
        "Enter anything: a topic (*machine learning*), a book title (*Clean Code*), "
        "a course (*Operating Systems*), a concept (*quantum entanglement*), "
        "or even a career goal (*become a data scientist*)."
    )

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        topic_input = st.text_input(
            "Your topic or book",
            placeholder="e.g.  neural networks,  contract law,  history of Rome,  Python for beginners…",
            label_visibility="collapsed",
            key="topic_input_field",
        )
    with col_btn:
        search_clicked = st.button("🔍 Find Books", type="primary", use_container_width=True)

    # Quick example chips
    st.caption("**Quick examples →**")
    chip_cols = st.columns(6)
    examples = [
        "machine learning", "quantum mechanics", "contract law",
        "data visualisation", "evolution and genetics", "financial accounting",
    ]
    for i, ex in enumerate(examples):
        with chip_cols[i]:
            if st.button(ex, key=f"chip_{ex}", use_container_width=True):
                st.session_state.last_topic = ex
                search_clicked = True
                topic_input = ex

    # Trigger search
    if search_clicked and (topic_input or st.session_state.last_topic):
        query = topic_input.strip() or st.session_state.last_topic
        st.session_state.last_topic = query

        with st.spinner(f"🤖 IBM Granite is finding the best books for **\"{query}\"**…"):
            all_books = BookDB.all()
            result = recommend_by_topic(query, all_books, student)
            st.session_state.rec_results = result
            st.session_state.rec_topic  = query

    # Display results
    if st.session_state.rec_results:
        result = st.session_state.rec_results
        topic  = st.session_state.get("rec_topic", "")

        st.divider()
        st.markdown(f"### 📚 IBM Granite Recommendations for: *\"{topic}\"*")

        # Topic summary from Granite
        if result.get("topic_summary"):
            st.info(f"🤖 **IBM Granite:** {result['topic_summary']}")

        recs = result.get("recommendations", [])
        if not recs:
            st.warning("No matching books found. Try a different topic or keyword.")
        else:
            for rec in recs:
                book = rec.get("book")
                if not book:
                    continue

                avail = book.get("availableCopies", 0)
                meta  = SUBJECT_META.get(book.get("subject",""), {"icon": "📚", "color": "#888"})
                avail_badge = "🟢 Available" if avail > 2 else ("🟡 Limited" if avail > 0 else "🔴 Unavailable")

                with st.container(border=True):
                    # ── Book header row ──
                    h1, h2, h3 = st.columns([1, 5, 2])
                    with h1:
                        st.markdown(
                            f"<div style='font-size:2.8rem;text-align:center;padding:8px 0'>"
                            f"#{rec['rank']}</div>",
                            unsafe_allow_html=True,
                        )
                    with h2:
                        st.markdown(f"### {meta['icon']} {book['title']}")
                        st.caption(f"**{book['author']}**  ·  {book.get('subject','')}  ·  "
                                   f"{book.get('edition','')} {book.get('year','')}  ·  "
                                   f"⭐ {book.get('rating','?')}  ·  "
                                   f"📤 {book.get('borrowedCount',0)} borrows")
                        st.caption(f"{avail_badge}  ·  {avail}/{book.get('totalCopies','?')} copies")
                    with h3:
                        level = book.get("level","")
                        level_map = {"beginner":"🟢 Beginner","intermediate":"🟡 Intermediate","advanced":"🔴 Advanced"}
                        st.markdown(f"**Level:** {level_map.get(level, level)}")
                        st.markdown(f"**Category:** {book.get('category','')}")

                    st.divider()

                    # ── Granite's personalised "why" ──
                    st.markdown("**🤖 Why IBM Granite recommends this:**")
                    st.success(rec.get("why", "Relevant to your query."))
                    if rec.get("best_for"):
                        st.caption(f"👥 **Best for:** {rec['best_for']}")

                    # ── Tags ──
                    if book.get("tags"):
                        st.caption("🏷️ " + "  ·  ".join(book["tags"][:6]))

                    # ── Actions row ──
                    a1, a2, a3, a4 = st.columns(4)
                    with a1:
                        sum_key = f"summ_{book['id']}"
                        if st.button("📖 AI Summary", key=f"sumbtn_{book['id']}", use_container_width=True):
                            if sum_key not in st.session_state.summary_cache:
                                with st.spinner("Generating summary with IBM Granite…"):
                                    summary = summarize_book(
                                        book["title"], book["author"],
                                        book.get("description",""), book.get("tags",[])
                                    )
                                    st.session_state.summary_cache[sum_key] = summary
                            st.session_state[f"show_sum_{book['id']}"] = True

                    with a2:
                        if avail > 0 and student:
                            if st.button("📌 Reserve", key=f"res_t_{book['id']}", use_container_width=True, type="primary"):
                                if ReservationDB.has_active(student["id"], book["id"]):
                                    st.toast("⚠️ Already reserved!", icon="⚠️")
                                else:
                                    BookDB.decrement_available(book["id"])
                                    ReservationDB.create(student["id"], book["id"], book["title"], student["name"])
                                    st.toast(f"✅ Reserved '{book['title']}'!", icon="✅")
                                    st.rerun()
                        elif avail == 0 and student:
                            if st.button("📋 Waitlist", key=f"wl_t_{book['id']}", use_container_width=True):
                                if WaitlistDB.is_on_waitlist(book["id"], student["id"]):
                                    st.toast("Already on waitlist!", icon="⚠️")
                                else:
                                    entry = WaitlistDB.join(book["id"], student["id"])
                                    st.toast(f"📋 Joined waitlist #{entry['position']}", icon="📋")

                    with a3:
                        st.caption(f"📚 {book.get('subject','')}")
                    with a4:
                        if not student:
                            st.caption("Select profile to reserve")

                    # ── Expandable AI summary ──
                    if st.session_state.get(f"show_sum_{book['id']}") and sum_key in st.session_state.summary_cache:
                        with st.expander("📖 IBM Granite Book Summary", expanded=True):
                            st.markdown(st.session_state.summary_cache[sum_key])
                            if st.button("✕ Hide summary", key=f"hidesumm_{book['id']}"):
                                st.session_state[f"show_sum_{book['id']}"] = False
                                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Browse by Subject with per-subject AI overview + books
# ══════════════════════════════════════════════════════════════════════════════
with tab_subject:
    st.markdown("### 🏷️ Browse All Subjects")

    subjects = BookDB.subjects()
    all_books = BookDB.all()

    # Subject grid
    subject_cols = st.columns(4)
    for i, subj in enumerate(subjects):
        meta  = SUBJECT_META.get(subj, {"icon": "📚", "color": "#888", "desc": ""})
        count = len([b for b in all_books if b.get("subject") == subj])
        with subject_cols[i % 4]:
            with st.container(border=True):
                st.markdown(f"### {meta['icon']} {subj}")
                st.caption(f"{count} books")
                st.caption(meta.get("desc",""))
                if st.button(f"View {subj}", key=f"view_{subj}", use_container_width=True, type="primary"):
                    st.session_state.selected_subject = subj
                    st.rerun()

    # ── Selected subject detail ────────────────────────────────────────────────
    sel_subj = st.session_state.get("selected_subject")
    if sel_subj:
        st.divider()
        meta = SUBJECT_META.get(sel_subj, {"icon": "📚", "color": "#0f62fe"})
        st.markdown(f"## {meta['icon']} {sel_subj}")

        subject_books = BookDB.get_by_subject(sel_subj)
        if not subject_books:
            st.info(f"No books found for {sel_subj}.")
        else:
            # IBM Granite subject overview
            overview_key = f"subj_overview_{sel_subj}"
            if overview_key not in st.session_state.summary_cache:
                if st.button(f"🤖 Generate IBM Granite Overview for {sel_subj}", type="primary"):
                    with st.spinner(f"IBM Granite generating {sel_subj} overview…"):
                        from services.granite_service import chat_with_granite
                        overview = chat_with_granite(
                            "You are an expert academic librarian. Write a 3-paragraph academic overview of this subject: "
                            "what it covers, why it matters, key sub-fields, and what students will gain from studying it.",
                            f"Subject: {sel_subj}\nAvailable books: {', '.join(b['title'] for b in subject_books[:8])}",
                            max_tokens=400, temperature=0.5,
                        )
                        st.session_state.summary_cache[overview_key] = overview
                        st.rerun()
            else:
                with st.container(border=True):
                    st.markdown("**🤖 IBM Granite — Subject Overview:**")
                    st.markdown(st.session_state.summary_cache[overview_key])

            # Sort options
            sort_col, _ = st.columns([2, 4])
            with sort_col:
                sort_opt = st.selectbox("Sort by", ["Most Popular","Highest Rated","A→Z","Level: Easy first"],
                                        key=f"sort_{sel_subj}")

            if sort_opt == "Most Popular":
                subject_books = sorted(subject_books, key=lambda b: b.get("borrowedCount",0), reverse=True)
            elif sort_opt == "Highest Rated":
                subject_books = sorted(subject_books, key=lambda b: b.get("rating",0), reverse=True)
            elif sort_opt == "A→Z":
                subject_books = sorted(subject_books, key=lambda b: b.get("title","").lower())
            else:
                level_order = {"beginner":0,"intermediate":1,"advanced":2}
                subject_books = sorted(subject_books, key=lambda b: level_order.get(b.get("level",""),1))

            st.caption(f"Showing {len(subject_books)} books in **{sel_subj}**")

            for book in subject_books:
                avail = book.get("availableCopies",0)
                avail_icon = "🟢" if avail > 2 else ("🟡" if avail > 0 else "🔴")
                level_map = {"beginner":"🟢 Beginner","intermediate":"🟡 Intermediate","advanced":"🔴 Advanced"}

                with st.expander(
                    f"{'📗' if avail>0 else '📕'} **{book['title']}**  ·  {book['author']}  "
                    f"·  {avail_icon} {avail} avail  ·  ⭐ {book.get('rating','?')}",
                    expanded=False,
                ):
                    d1, d2 = st.columns([3,1])
                    with d1:
                        st.write(book.get("description",""))
                        if book.get("tags"):
                            st.caption("🏷️ " + "  ·  ".join(book["tags"][:6]))

                    with d2:
                        st.markdown(f"**Level:** {level_map.get(book.get('level',''),'?')}")
                        st.markdown(f"**Category:** {book.get('category','')}")
                        st.markdown(f"**Edition:** {book.get('edition','')} ({book.get('year','')})")
                        if book.get("isbn"):
                            st.caption(f"ISBN: {book['isbn']}")
                        st.metric("Available", f"{avail}/{book.get('totalCopies',avail)}")
                        st.metric("Borrows", f"📤 {book.get('borrowedCount',0)}")

                    btn1, btn2, btn3 = st.columns(3)
                    with btn1:
                        sum_key = f"summ_{book['id']}"
                        if st.button("📖 AI Summary", key=f"subj_sum_{book['id']}", use_container_width=True):
                            if sum_key not in st.session_state.summary_cache:
                                with st.spinner("IBM Granite generating summary…"):
                                    st.session_state.summary_cache[sum_key] = summarize_book(
                                        book["title"], book["author"],
                                        book.get("description",""), book.get("tags",[])
                                    )
                            st.session_state[f"show_subj_sum_{book['id']}"] = True

                    with btn2:
                        if avail > 0 and student:
                            if st.button("📌 Reserve", key=f"subj_res_{book['id']}", use_container_width=True, type="primary"):
                                if ReservationDB.has_active(student["id"], book["id"]):
                                    st.toast("⚠️ Already reserved!")
                                else:
                                    BookDB.decrement_available(book["id"])
                                    ReservationDB.create(student["id"], book["id"], book["title"], student["name"])
                                    st.toast(f"✅ Reserved!", icon="✅")
                                    st.rerun()
                        elif avail == 0 and student:
                            if st.button("📋 Waitlist", key=f"subj_wl_{book['id']}", use_container_width=True):
                                if not WaitlistDB.is_on_waitlist(book["id"], student["id"]):
                                    entry = WaitlistDB.join(book["id"], student["id"])
                                    st.toast(f"📋 Position #{entry['position']}", icon="📋")

                    with btn3:
                        wl_count = len(WaitlistDB.for_book(book["id"]))
                        if wl_count:
                            st.caption(f"⏳ {wl_count} on waitlist")

                    if st.session_state.get(f"show_subj_sum_{book['id']}") and sum_key in st.session_state.summary_cache:
                        st.divider()
                        st.markdown("**📖 IBM Granite Summary:**")
                        st.info(st.session_state.summary_cache[sum_key])
                        if st.button("✕ Hide", key=f"hide_subj_{book['id']}"):
                            st.session_state[f"show_subj_sum_{book['id']}"] = False
                            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Personalised picks using full student profile
# ══════════════════════════════════════════════════════════════════════════════
with tab_personal:
    st.markdown("### 👤 Your Personalised IBM Granite Picks")

    if not student:
        st.warning("👆 Select your student profile from the sidebar to get personalised recommendations.")
        st.stop()

    st.info(
        f"**Profile:** {student['name']}  ·  {student.get('major','')}  ·  Year {student.get('year',1)}\n\n"
        f"**Courses:** {', '.join(student.get('currentCourses',[]) or ['None'])}\n\n"
        f"**Interests:** {', '.join(student.get('interests',[]) or ['None'])}"
    )

    # Optional extra query
    personal_query = st.text_input(
        "Optionally refine your recommendation (leave blank for general picks):",
        placeholder="e.g. I want to prepare for my algorithms exam, or I'm interested in AI ethics",
        key="personal_query",
    )

    if st.button("🤖 Get My IBM Granite Picks", type="primary", use_container_width=False):
        query = personal_query.strip() or f"{student.get('major','')} {' '.join(student.get('currentCourses',[]))}"
        with st.spinner("IBM Granite is curating your personalised picks…"):
            all_books = BookDB.all()
            result = recommend_by_topic(query, all_books, student)
            st.session_state.personal_rec_results = result
            st.session_state.personal_rec_query = query

    if "personal_rec_results" in st.session_state:
        result = st.session_state.personal_rec_results
        st.divider()

        if result.get("topic_summary"):
            st.markdown(f"**🤖 IBM Granite says:** {result['topic_summary']}")

        recs = result.get("recommendations", [])
        if not recs:
            st.info("No specific matches found. Try a more specific query above.")
        else:
            st.markdown(f"### Top {len(recs)} Picks for You")
            for rec in recs:
                book = rec.get("book")
                if not book:
                    continue

                avail = book.get("availableCopies", 0)
                meta  = SUBJECT_META.get(book.get("subject",""), {"icon":"📚"})
                level_map = {"beginner":"🟢","intermediate":"🟡","advanced":"🔴"}

                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"**#{rec['rank']} {meta['icon']} {book['title']}**")
                        st.caption(f"{book['author']}  ·  {book.get('subject','')}  ·  "
                                   f"{level_map.get(book.get('level',''),'?')} {book.get('level','').title()}  ·  "
                                   f"⭐ {book.get('rating','?')}")
                        st.markdown(f"*{rec.get('why', '')}*")
                        if rec.get("best_for"):
                            st.caption(f"👥 {rec['best_for']}")
                    with c2:
                        st.metric("Avail.", f"{avail}/{book.get('totalCopies','?')}")
                        sum_key = f"summ_{book['id']}"
                        if st.button("📖", key=f"pers_sum_{book['id']}", help="AI Summary", use_container_width=True):
                            if sum_key not in st.session_state.summary_cache:
                                with st.spinner("Summarising…"):
                                    st.session_state.summary_cache[sum_key] = summarize_book(
                                        book["title"], book["author"],
                                        book.get("description",""), book.get("tags",[])
                                    )
                            st.session_state[f"show_pers_sum_{book['id']}"] = True

                        if avail > 0:
                            if st.button("📌", key=f"pers_res_{book['id']}", help="Reserve", use_container_width=True):
                                if not ReservationDB.has_active(student["id"], book["id"]):
                                    BookDB.decrement_available(book["id"])
                                    ReservationDB.create(student["id"], book["id"], book["title"], student["name"])
                                    st.toast(f"✅ Reserved!", icon="✅")
                                    st.rerun()
                        else:
                            if st.button("📋", key=f"pers_wl_{book['id']}", help="Waitlist", use_container_width=True):
                                if not WaitlistDB.is_on_waitlist(book["id"], student["id"]):
                                    entry = WaitlistDB.join(book["id"], student["id"])
                                    st.toast(f"📋 #{entry['position']}", icon="📋")

                    if st.session_state.get(f"show_pers_sum_{book['id']}") and sum_key in st.session_state.summary_cache:
                        st.divider()
                        st.markdown("**📖 IBM Granite Book Summary:**")
                        st.info(st.session_state.summary_cache[sum_key])

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#888; font-size:0.85rem;'>"
    "Library AI Agent · All recommendations and summaries powered by "
    "<strong>IBM Granite</strong> on <strong>watsonx.ai</strong> (IBM Cloud Lite)"
    "</p>",
    unsafe_allow_html=True,
)
