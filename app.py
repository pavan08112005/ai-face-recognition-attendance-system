from flask import Flask, jsonify, request, render_template, Response
from database import get_students, get_attendance
from waitress import serve

import sqlite3
import subprocess
import sys
import csv
import io
import os
from datetime import datetime
from functools import wraps


app = Flask(__name__)
import secrets

ADMIN_PASSWORD = os.environ.get("ATTENDANCE_ADMIN_PASSWORD")


def require_admin():
    def decorator(view_function):
        @wraps(view_function)
        def wrapped(*args, **kwargs):
            password = request.headers.get(
                "X-Admin-Password", ""
            )

            if not ADMIN_PASSWORD:
                return jsonify({
                    "message": "Admin password is not configured."
                }), 503

            if not secrets.compare_digest(
                password, ADMIN_PASSWORD
            ):
                return jsonify({
                    "message": "Unauthorized. Admin password required."
                }), 401

            return view_function(*args, **kwargs)

        return wrapped
    return decorator

# Project folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# DASHBOARD API
# ==========================================

@app.route("/api/dashboard")
def dashboard():

    students = get_students()
    attendance = get_attendance()

    today = datetime.now().strftime("%Y-%m-%d")

    total_students = len(students)

    # Database attendance records are tuples:
    # (student_id, name, date, time, session)

    today_records = [
        record
        for record in attendance
        if record[2] == today
    ]

    present_today = len(
        set(
            record[0]
            for record in today_records
        )
    )

    absent_today = max(
        total_students - present_today,
        0
    )

    percentage = (
        (present_today / total_students) * 100
        if total_students > 0
        else 0
    )

    return jsonify({
        "total_students": total_students,
        "present_today": present_today,
        "absent_today": absent_today,
        "attendance_percentage": round(
            percentage,
            1
        )
    })


# ==========================================
# STUDENTS API
# ==========================================

@app.route("/api/students")
def students():

    db_path = os.path.join(
        BASE_DIR,
        "attendance.db"
    )

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT student_id, name, created_at
        FROM students
        ORDER BY name
    """)

    rows = cursor.fetchall()

    conn.close()

    result = []

    for row in rows:

        result.append({
            "student_id": row[0],
            "name": row[1],
            "created_at": row[2]
        })

    return jsonify(result)


# ==========================================
# ATTENDANCE API
# ==========================================

@app.route("/api/attendance")
def attendance():

    records = get_attendance()

    result = []

    for record in records:

        result.append({
            "student_id": record[0],
            "name": record[1],
            "date": record[2],
            "time": record[3],
            "session": record[4]
        })

    return jsonify(result)


# ==========================================
# REGISTER STUDENT
# ==========================================
@app.route("/api/register", methods=["POST"])
@require_admin()
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Invalid request data."
        }), 400

    student_id = data.get(
        "student_id",
        ""
    ).strip()

    name = data.get(
        "name",
        ""
    ).strip()

    if not student_id or not name:

        return jsonify({
            "message":
            "Student ID and Name are required."
        }), 400

    try:

        register_script = os.path.join(
            BASE_DIR,
            "register_student.py"
        )

        subprocess.Popen([
            sys.executable,
            register_script,
            student_id,
            name
        ])

        return jsonify({
            "message":
            "Face registration started. "
            "Complete the camera registration."
        })

    except Exception as error:

        return jsonify({
            "message":
            f"Could not start registration: {error}"
        }), 500


# ==========================================
# START LIVE ATTENDANCE
# ==========================================

@app.route(
    "/api/start-attendance",
    methods=["POST"]
)
def start_attendance():

    try:

        attendance_script = os.path.join(
            BASE_DIR,
            "attendance_system.py"
        )

        subprocess.Popen([
            sys.executable,
            attendance_script
        ])

        return jsonify({
            "message":
            "Automatic attendance started. "
            "Camera window opened."
        })

    except Exception as error:

        return jsonify({
            "message":
            f"Could not start attendance: {error}"
        }), 500


# ==========================================
# EXPORT CSV
# ==========================================

@app.route("/api/export")
def export_csv():

    records = get_attendance()

    output = io.StringIO()

    writer = csv.writer(output)

    # CSV header
    writer.writerow([
        "Student ID",
        "Name",
        "Date",
        "Time",
        "Session"
    ])

    # Database records are tuples
    for record in records:

        writer.writerow([
            record[0],
            record[1],
            record[2],
            record[3],
            record[4]
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; "
                "filename=attendance_records.csv"
        }
    )


# ==========================================
# START FLASK SERVER
# ==========================================

if __name__ == "__main__":

    print("")
    print("================================")
    print("FACE ATTENDANCE WEB SYSTEM")
    print("================================")
    print("Server: http://127.0.0.1:5001")
    print("")

    serve(
        app,
        host="127.0.0.1",
        port=5001
    )