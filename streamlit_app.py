import streamlit as st
import pandas as pd
import sqlite3
import subprocess
import sys
from datetime import datetime

DB_NAME = "attendance.db"


# ==============================
# DATABASE
# ==============================

def get_connection():
    return sqlite3.connect(DB_NAME)


def get_students():
    conn = get_connection()

    data = pd.read_sql_query(
        """
        SELECT student_id, name, created_at
        FROM students
        ORDER BY name
        """,
        conn
    )

    conn.close()
    return data


def get_attendance():
    conn = get_connection()

    data = pd.read_sql_query(
        """
        SELECT student_id, name, date, time, session
        FROM attendance
        ORDER BY date DESC, time DESC
        """,
        conn
    )

    conn.close()
    return data


# ==============================
# PAGE
# ==============================

st.set_page_config(
    page_title="Face Attendance System",
    page_icon="📸",
    layout="wide"
)


# ==============================
# HEADER
# ==============================

st.title("📸 Face-Based Attendance System")

st.caption(
    "AI-powered attendance using InsightFace / ArcFace"
)

st.divider()


# ==============================
# DATA
# ==============================

students = get_students()
attendance = get_attendance()

today = datetime.now().strftime("%Y-%m-%d")

if not attendance.empty:
    today_attendance = attendance[
        attendance["date"] == today
    ]
else:
    today_attendance = attendance


total_students = len(students)

if not today_attendance.empty:
    present_today = today_attendance[
        "student_id"
    ].nunique()
else:
    present_today = 0


absent_today = max(
    total_students - present_today,
    0
)


attendance_percentage = (
    present_today / total_students * 100
    if total_students > 0
    else 0
)


# ==============================
# SIDEBAR
# ==============================

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Module",
    [
        "📊 Dashboard",
        "👨‍🎓 Students",
        "➕ Register Student",
        "📷 Live Attendance",
        "📋 Attendance Records"
    ]
)


# ==============================
# DASHBOARD
# ==============================

if page == "📊 Dashboard":

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "👨‍🎓 Total Students",
            total_students
        )

    with col2:
        st.metric(
            "✅ Present Today",
            present_today
        )

    with col3:
        st.metric(
            "❌ Absent Today",
            absent_today
        )

    with col4:
        st.metric(
            "📊 Attendance",
            f"{attendance_percentage:.1f}%"
        )

    st.divider()

    st.subheader("Today's Attendance")

    if today_attendance.empty:

        st.info(
            "No attendance recorded today."
        )

    else:

        st.dataframe(
            today_attendance,
            use_container_width=True,
            hide_index=True
        )


# ==============================
# STUDENTS
# ==============================

elif page == "👨‍🎓 Students":

    st.header("👨‍🎓 Registered Students")

    if students.empty:

        st.warning(
            "No students registered."
        )

    else:

        st.dataframe(
            students,
            use_container_width=True,
            hide_index=True
        )

        st.success(
            f"{len(students)} student(s) registered."
        )


# ==============================
# REGISTER STUDENT
# ==============================

elif page == "➕ Register Student":

    st.header("➕ Register New Student")

    st.write(
        "Register a student's face using "
        "InsightFace / ArcFace."
    )

    student_id = st.text_input(
        "Student ID",
        placeholder="Example: is413"
    )

    student_name = st.text_input(
        "Student Name",
        placeholder="Example: Rahul"
    )

    st.info(
        "Enter the details and start registration. "
        "The webcam will open in a separate window."
    )

    if st.button(
        "📷 Start Face Registration",
        type="primary"
    ):

        if not student_id or not student_name:

            st.error(
                "Please enter Student ID and Student Name."
            )

        else:

            try:

                # Open the registration program
                # in a separate terminal window.
                subprocess.Popen(
                    [
                        "cmd",
                        "/k",
                        sys.executable,
                        "register_student.py"
                    ]
                )

                st.success(
                    "Registration program started. "
                    "Complete the webcam registration."
                )

            except Exception as e:

                st.error(
                    f"Could not start registration: {e}"
                )


# ==============================
# LIVE ATTENDANCE
# ==============================

elif page == "📷 Live Attendance":

    st.header("📷 Live Attendance")

    st.write(
        "Start real-time face recognition "
        "and automatic attendance."
    )

    st.warning(
        "The webcam will open in a separate window."
    )

    if st.button(
        "▶ Start Automatic Attendance",
        type="primary"
    ):

        try:

            subprocess.Popen(
                [
                    "cmd",
                    "/k",
                    sys.executable,
                    "attendance_system.py"
                ]
            )

            st.success(
                "Automatic attendance started."
            )

        except Exception as e:

            st.error(
                f"Could not start attendance: {e}"
            )


# ==============================
# ATTENDANCE RECORDS
# ==============================

elif page == "📋 Attendance Records":

    st.header("📋 Attendance Records")

    if attendance.empty:

        st.info(
            "No attendance records available."
        )

    else:

        st.dataframe(
            attendance,
            use_container_width=True,
            hide_index=True
        )

        csv = attendance.to_csv(
            index=False
        )

        st.download_button(
            "📥 Download Attendance CSV",
            csv,
            "attendance_report.csv",
            "text/csv"
        )

        st.success(
            f"Total attendance records: {len(attendance)}"
        )


# ==============================
# FOOTER
# ==============================

st.divider()

st.caption(
    "Face-Based Attendance System | "
    "InsightFace • ArcFace • OpenCV • SQLite"
)