import streamlit as st
from db import get_connection
from datetime import date
import mysql.connector

def manage_teachers():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch subjects and classes
    cursor.execute("SELECT s_id, s_name FROM subjects")
    subjects = cursor.fetchall()

    cursor.execute("SELECT c_id, c_name FROM classes")
    classes = cursor.fetchall()

    # Fetch existing teachers
    cursor.execute("SELECT * FROM teachers")
    teachers = cursor.fetchall()

    teacher_names = {t['t_name']: t['t_id'] for t in teachers}
    teacher_selected = st.selectbox("Select Teacher to View/Edit or Add New",
                                    ["-- Add New --"] + list(teacher_names.keys()))

    # Handle new teacher addition
    if teacher_selected == "-- Add New --":
        new_name = st.text_input("Enter Teacher Name")
        if st.button("Add Teacher") and new_name:
            cursor.execute("INSERT INTO teachers (t_name) VALUES (%s)", (new_name,))
            conn.commit()
            st.session_state.teacher_added = True
            st.rerun()

        if st.session_state.get("teacher_added"):
            st.success("✅ Teacher added successfully.")
            del st.session_state["teacher_added"]

    else:
        teacher_id = teacher_names[teacher_selected]
        st.markdown(f"**Editing Teacher:** {teacher_selected}")

        # Subject/Class assignment form
        with st.form("assign_subject_class"):
            subject = st.selectbox("Select Subject", [f"{s['s_id']} - {s['s_name']}" for s in subjects])
            class_selected = st.selectbox("Select Class", [f"{c['c_id']} - {c['c_name']}" for c in classes])
            submit_btn = st.form_submit_button("Assign")

            if submit_btn:
                sub_id = subject.split(" - ")[0]
                class_id = class_selected.split(" - ")[0]
                try:
                    cursor.execute("""
                        INSERT INTO teacher_subject_class (teacher_id, subject_id, class_id)
                        VALUES (%s, %s, %s)
                    """, (teacher_id, sub_id, class_id))
                    conn.commit()
                    st.success("📘 Subject-Class assigned.")
                    st.rerun()
                except mysql.connector.errors.IntegrityError as e:
                    if "unique_subject_class" in str(e):
                        st.warning("⚠️ This subject is already assigned to a teacher for this class.")
                    else:
                        st.error(f"❌ An error occurred: {e}")

        # Show current assignments
        cursor.execute("""
            SELECT tsc.id, s.s_name, c.c_name 
            FROM teacher_subject_class tsc
            JOIN subjects s ON s.s_id = tsc.subject_id
            JOIN classes c ON c.c_id = tsc.class_id
            WHERE tsc.teacher_id = %s
        """, (teacher_id,))
        rows = cursor.fetchall()

        st.markdown("### Assigned Subjects & Classes:")
        for row in rows:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📘 {row['s_name']} – Class {row['c_name']}")
            with col2:
                if st.button("🗑️", key=f"del_{row['id']}"):
                    cursor.execute("DELETE FROM teacher_subject_class WHERE id = %s", (row['id'],))
                    conn.commit()
                    st.success("🗑️ Assignment deleted.")
                    st.rerun()

        # Delete teacher
        if st.button("❌ Delete This Teacher"):
            cursor.execute("DELETE FROM teacher_subject_class WHERE teacher_id = %s", (teacher_id,))
            cursor.execute("DELETE FROM teachers WHERE t_id = %s", (teacher_id,))
            conn.commit()
            st.success("❌ Teacher deleted.")
            st.rerun()

    conn.close()


def manage_class_timetable():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch class and subject options
    cursor.execute("SELECT c_id, c_name FROM classes")
    classes = cursor.fetchall()

    cursor.execute("SELECT s_id, s_name FROM subjects")
    subjects = cursor.fetchall()

    class_option = st.selectbox("Select Class", [f"{c['c_id']} - {c['c_name']}" for c in classes])
    day_option = st.selectbox("Select Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
    class_id = int(class_option.split(" - ")[0])

    # View existing timetable for this class and day
    st.markdown("### Current Timetable")
    cursor.execute("""
        SELECT ct.id, ct.period, s.s_name
        FROM class_timetable ct
        JOIN subjects s ON ct.subject_id = s.s_id
        WHERE ct.class_id = %s AND ct.day = %s
        ORDER BY ct.period
    """, (class_id, day_option))
    timetable = cursor.fetchall()

    for entry in timetable:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.write(f"Period {entry['period']}: 📘 {entry['s_name']}")
        with col2:
            if st.button("🗑️", key=f"del_tt_{entry['id']}"):
                cursor.execute("DELETE FROM class_timetable WHERE id = %s", (entry['id'],))
                conn.commit()
                st.success("Deleted from timetable.")
                st.rerun()

    st.markdown("### Add/Update Period")
    with st.form("add_timetable_entry"):
        period = st.selectbox("Select Period", list(range(1, 9)))
        subject = st.selectbox("Select Subject", [f"{s['s_id']} - {s['s_name']}" for s in subjects])
        submit = st.form_submit_button("Save/Update")

        if submit:
            subject_id = subject.split(" - ")[0]

            # Check if this period already has a subject
            cursor.execute("""
                SELECT id FROM class_timetable 
                WHERE class_id = %s AND day = %s AND period = %s
            """, (class_id, day_option, period))
            existing = cursor.fetchone()

            if existing:
                # Update the existing subject
                cursor.execute("""
                    UPDATE class_timetable SET subject_id = %s
                    WHERE id = %s
                """, (subject_id, existing['id']))
            else:
                # Insert new row
                cursor.execute("""
                    INSERT INTO class_timetable (class_id, subject_id, day, period)
                    VALUES (%s, %s, %s, %s)
                """, (class_id, subject_id, day_option, period))

            conn.commit()
            st.success("Timetable updated.")
            st.rerun()

    conn.close()


def mark_teacher_attendance():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get today's date
    today = date.today()

    # Fetch all teachers
    cursor.execute("SELECT t_id, t_name FROM teachers ORDER BY t_name")
    teachers = cursor.fetchall()

    # Fetch already marked attendance for today
    cursor.execute("SELECT teacher_id, status FROM teacher_attendence WHERE date = %s", (today,))
    attendance_records = {row['teacher_id']: row['status'] for row in cursor.fetchall()}

    st.write(f"Date: {today.strftime('%A, %d %B %Y')}")
    st.markdown("### Mark attendance for each teacher:")

    with st.form("attendance_form"):
        selections = {}
        for teacher in teachers:
            current_status = attendance_records.get(teacher['t_id'], 'Present')  # Default to Present
            selections[teacher['t_id']] = st.radio(
                label=teacher['t_name'],
                options=["Present", "Absent"],
                index=0 if current_status == "Present" else 1,
                horizontal=True,
                key=f"status_{teacher['t_id']}"
            )

        submitted = st.form_submit_button("Save Attendance")

        if submitted:
            for teacher_id, status in selections.items():
                if teacher_id in attendance_records:
                    # Update if already marked
                    cursor.execute("""
                        UPDATE teacher_attendence
                        SET status = %s
                        WHERE teacher_id = %s AND date = %s
                    """, (status, teacher_id, today))
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO teacher_attendence (teacher_id, date, status)
                        VALUES (%s, %s, %s)
                    """, (teacher_id, today, status))
            conn.commit()
            st.success("✅ Attendance saved successfully.")
            st.rerun()

    conn.close()


def view_timetables():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    option = st.radio("View by", ["Teacher", "Class"], horizontal=True)

    if option == "Teacher":
        cursor.execute("SELECT t_id, t_name FROM teachers")
        teachers = cursor.fetchall()

        teacher_map = {t["t_name"]: t["t_id"] for t in teachers}
        selected_teacher = st.selectbox("Select Teacher", list(teacher_map.keys()))

        if selected_teacher:
            t_id = teacher_map[selected_teacher]
            query = """
                SELECT c.c_name as class_name, s.s_name as subject_name, ct.day, ct.period
                FROM class_timetable ct
                JOIN teacher_subject_class tsc ON ct.class_id = tsc.class_id AND ct.subject_id = tsc.subject_id
                JOIN classes c ON c.c_id = ct.class_id
                JOIN subjects s ON s.s_id = ct.subject_id
                WHERE tsc.teacher_id = %s
                ORDER BY FIELD(ct.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'), ct.period
            """
            cursor.execute(query, (t_id,))
            rows = cursor.fetchall()

            st.markdown(f"### Timetable for **{selected_teacher}**")
            if rows:
                for row in rows:
                    st.write(f"📚 {row['subject_name']} – Class {row['class_name']} | {row['day']} Period {row['period']}")
            else:
                st.info("No timetable data found for this teacher.")

    elif option == "Class":
        cursor.execute("SELECT c_id, c_name FROM classes")
        classes = cursor.fetchall()

        class_map = {c["c_name"]: c["c_id"] for c in classes}
        selected_class = st.selectbox("Select Class", list(class_map.keys()))

        if selected_class:
            c_id = class_map[selected_class]
            query = """
                SELECT s.s_name as subject_name, ct.day, ct.period, t.t_name as teacher_name
                FROM class_timetable ct
                JOIN teacher_subject_class tsc ON ct.class_id = tsc.class_id AND ct.subject_id = tsc.subject_id
                JOIN subjects s ON s.s_id = ct.subject_id
                JOIN teachers t ON t.t_id = tsc.teacher_id
                WHERE ct.class_id = %s
                ORDER BY FIELD(ct.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'), ct.period
            """
            cursor.execute(query, (c_id,))
            rows = cursor.fetchall()

            st.markdown(f"### Timetable for **Class {selected_class}**")
            if rows:
                for row in rows:
                    st.write(f"📘 {row['subject_name']} – {row['day']} Period {row['period']} | Teacher: {row['teacher_name']}")
            else:
                st.info("No timetable data found for this class.")

    cursor.close()
    conn.close()


def find_substitutions():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Step 1: Get absent teachers
    cursor.execute("""
        SELECT DISTINCT t.t_id, t.t_name 
        FROM teacher_attendence ta
        JOIN teachers t ON ta.teacher_id = t.t_id
        WHERE ta.status = 'Absent' AND ta.date = CURDATE()
    """)
    absentees = cursor.fetchall()

    if not absentees:
        st.success("✅ All teachers are present today!")
        conn.close()
        return

    selected_teacher = st.selectbox("Select Absent Teacher", [t["t_name"] for t in absentees])
    selected_teacher_id = next(t["t_id"] for t in absentees if t["t_name"] == selected_teacher)

    # Step 2: Get the classes the absent teacher was supposed to take today
    cursor.execute("""
        SELECT ct.class_id, c.c_name, ct.subject_id, s.s_name, ct.day, ct.period
        FROM class_timetable ct
        JOIN teacher_subject_class tsc ON tsc.class_id = ct.class_id AND tsc.subject_id = ct.subject_id
        JOIN classes c ON c.c_id = ct.class_id
        JOIN subjects s ON s.s_id = ct.subject_id
        WHERE tsc.teacher_id = %s AND ct.day = DAYNAME(CURDATE())
        ORDER BY ct.period
    """, (selected_teacher_id,))
    missed_classes = cursor.fetchall()

    if not missed_classes:
        st.info("This teacher had no scheduled periods today.")
        conn.close()
        return

    st.markdown("### Missed Periods:")
    for row in missed_classes:
        st.markdown(f"📘 {row['s_name']} – Class {row['c_name']} | Period {row['period']}")

    st.markdown("---")
    st.markdown("### Suggested Substitutes:")

    # Step 3: For each missed class, find substitute teachers who are free at that period
    for row in missed_classes:
        period = row["period"]
        class_name = row["c_name"]
        subject_name = row["s_name"]

        cursor.execute("""
            SELECT t.t_id, t.t_name
            FROM teachers t
            WHERE t.t_id NOT IN (
                SELECT tsc.teacher_id
                FROM teacher_subject_class tsc
                JOIN class_timetable ct ON tsc.class_id = ct.class_id AND tsc.subject_id = ct.subject_id
                WHERE ct.day = DAYNAME(CURDATE()) AND ct.period = %s
            )
            AND t.t_id != %s
            AND t.t_id NOT IN (
                SELECT teacher_id FROM teacher_attendence 
                WHERE date = CURDATE() AND status = 'Absent')
        """, (period, selected_teacher_id))

        free_teachers = cursor.fetchall()
        st.write(f"**{subject_name} – Class {class_name} (Period {period})**")

        if free_teachers:
            for ft in free_teachers:
                st.write(f"🔄 {ft['t_name']} is available")
        else:
            st.warning("⚠️ No available substitute found for this period.")

    cursor.close()
    conn.close()


def manage_classes():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Show existing classes
    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()

    st.markdown("### 📚 Existing Classes")
    for c in classes:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"{c['c_id']}: {c['c_name']}")
        with col2:
            if st.button("🗑️", key=f"del_{c['c_id']}"):
                cursor.execute("DELETE FROM classes WHERE c_id = %s", (c['c_id'],))
                conn.commit()
                st.success(f"Deleted class: {c['c_name']}")
                st.rerun()

    st.markdown("### ➕ Add New Class")
    new_class_id = st.text_input("Class ID (e.g., C101)")
    new_class_name = st.text_input("Class Name")

    if st.button("Add Class") and new_class_id and new_class_name:
        try:
            cursor.execute("INSERT INTO classes (c_id, c_name) VALUES (%s, %s)", (new_class_id, new_class_name))
            conn.commit()
            st.success(f"Class '{new_class_name}' added with ID {new_class_id}.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    conn.close()

def manage_subjects():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Show existing subjects
    cursor.execute("SELECT * FROM subjects")
    subjects = cursor.fetchall()

    st.markdown("### Current Subjects")
    for subj in subjects:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.write(f"{subj['s_id']}: {subj['s_name']}")
        with col2:
            if st.button("🗑️", key=f"del_{subj['s_id']}"):
                cursor.execute("DELETE FROM subjects WHERE s_id = %s", (subj['s_id'],))
                conn.commit()
                st.success(f"Subject '{subj['s_name']}' removed.")
                st.rerun()

    # Add new subject
    st.markdown("### ➕ Add New Subject")
    new_subject_id = st.text_input("Enter Subject ID (e.g., S101)")
    new_subject_name = st.text_input("Enter Subject Name")

    if st.button("Add Subject") and new_subject_id and new_subject_name:
        try:
            cursor.execute("INSERT INTO subjects (s_id, s_name) VALUES (%s, %s)", (new_subject_id, new_subject_name))
            conn.commit()
            st.success(f"Subject '{new_subject_name}' added successfully with ID {new_subject_id}.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    conn.close()