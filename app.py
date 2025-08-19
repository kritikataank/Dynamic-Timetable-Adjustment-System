import streamlit as st
from functions import manage_teachers, manage_class_timetable, mark_teacher_attendance, view_timetables
from functions import find_substitutions, manage_classes,  manage_subjects

st.set_page_config(page_title="School Admin Dashboard", layout="wide")
st.title("🏫 School Admin Dashboard")

# Sidebar menu navigation
menu = st.sidebar.selectbox("Choose Action", [
    "Add/Edit Teachers",
    "Add/Remove Classes",
    "Add/Edit Class Timetable",
    "Mark Teacher Attendance",
    "View Timetables",
    "Find Substitutions",
    "Add/Remove Subjects"
])

# Route actions
if menu == "Add/Edit Teachers":
    st.subheader("👩‍🏫 Add or Edit Teachers")
    manage_teachers()

elif menu == "Add/Remove Classes":
    st.subheader("🏷️ Add or Remove Classes")
    manage_classes()

elif menu == "Add/Edit Class Timetable":
    st.subheader("📅 Define Class Timetable")
    manage_class_timetable()

elif menu == "Mark Teacher Attendance":
    st.subheader("📋 Mark Daily Teacher Attendance")
    mark_teacher_attendance()

elif menu == "View Timetables":
    st.subheader("🗓 View Teacher/Class Timetables")
    view_timetables()

elif menu == "Find Substitutions":
    st.subheader("🔁 View Substitution Suggestions")
    find_substitutions()

elif menu == "Add/Remove Subjects" :
    st.subheader("📚 Add or Remove Subjects")
    manage_subjects()