from flask import Flask, jsonify, request, render_template, Response
from database import (
    get_students,
    get_attendance,
    get_connection,
    initialize_database,
    mark_attendance,
)

from face_engine import FaceEngine
from attendance_system import find_best_match
import cv2
import numpy as np
import threading
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
initialize_database()
# Initialize the face recognition engine once.
face_engine = None
face_engine_lock = threading.Lock()
face_inference_lock = threading.Lock()

def get_face_engine():
    global face_engine

    if face_engine is None:
        with face_engine_lock:
            if face_engine is None:
                face_engine = FaceEngine()

    return face_engine
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
    conn = get_connection()
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


@app.route("/api/recognize-frame", methods=["POST"])
def recognize_frame():

    # Keep the rest of your existing recognition code below this point.


    if "frame" not in request.files:
        return jsonify({
            "success": False,
            "message": "No camera frame received."
        }), 400

    uploaded_frame = request.files["frame"]

    # Reject empty or excessively large frames.
    frame_bytes = uploaded_frame.read(2 * 1024 * 1024 + 1)

    if not frame_bytes or len(frame_bytes) > 2 * 1024 * 1024:
        return jsonify({
            "success": False,
            "message": "Invalid or oversized camera frame."
        }), 400

    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({
            "success": False,
            "message": "Could not read the camera frame."
        }), 400

    try:
        engine = get_face_engine()

        with face_inference_lock:
            faces = engine.detect_faces(frame)

            if len(faces) != 1:
                return jsonify({
                    "success": False,
                    "message": (
                        "No face detected."
                        if len(faces) == 0
                        else "Please ensure only one face is visible."
                    )
                }), 200

            face = faces[0]

            quality_ok, quality_message = engine.assess_face_quality(
                frame, face
            )

            if not quality_ok:
                return jsonify({
                    "success": False,
                    "message": quality_message
                }), 200

            embedding = engine.get_embedding(face)

        if embedding is None:
            return jsonify({
                "success": False,
                "message": "Could not generate a face embedding."
            }), 200

        students_list = get_students()

        if not students_list:
            return jsonify({
                "success": False,
                "message": "No students are registered yet."
            }), 200

        best_student, best_score, second_best_score = find_best_match(
            embedding, students_list
        )

        if (
            best_student is None
            or best_score < 0.45
            or best_score - second_best_score < 0.05
        ):
            return jsonify({
                "success": False,
                "message": "Face not confidently matched."
            }), 200

        marked = mark_attendance(
            best_student["student_id"],
            best_student["name"],
            session="classroom"
        )

        return jsonify({
            "success": True,
            "recognized": True,
            "student_id": best_student["student_id"],
            "name": best_student["name"],
            "confidence": round(float(best_score), 3),
            "attendance_marked": marked,
            "message": (
                "Attendance marked successfully."
                if marked
                else "Attendance was already marked for this session."
            )
        }), 200

    except Exception:
        app.logger.exception("Face recognition failed")
        return jsonify({
            "success": False,
            "message": "Recognition failed. Check the server logs."
        }), 500

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