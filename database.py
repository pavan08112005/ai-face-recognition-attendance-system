import sqlite3
import numpy as np
from datetime import datetime


DB_NAME = "attendance.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            embedding BLOB NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            session TEXT NOT NULL,
            UNIQUE(student_id, date, session)
        )
    """)

    conn.commit()
    conn.close()


def save_student(student_id, name, embedding):
    conn = get_connection()
    cursor = conn.cursor()

    embedding_blob = embedding.astype(np.float32).tobytes()

    cursor.execute("""
        INSERT OR REPLACE INTO students
        (student_id, name, embedding, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        student_id,
        name,
        embedding_blob,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT student_id, name, embedding
        FROM students
    """)

    rows = cursor.fetchall()
    conn.close()

    students = []

    for student_id, name, embedding_blob in rows:

        embedding = np.frombuffer(
            embedding_blob,
            dtype=np.float32
        )

        students.append({
            "student_id": student_id,
            "name": name,
            "embedding": embedding
        })

    return students

def mark_attendance(student_id, name, session="default"):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    try:
        cursor.execute("""
            INSERT INTO attendance
            (student_id, name, date, time, session)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, name, date, time, session))

        conn.commit()
        print(f"Attendance marked: {name} | {date} {time}")
        return True

    except sqlite3.IntegrityError as error:
        print(f"Attendance not inserted: {error}")
        return False

    except sqlite3.Error as error:
        print(f"Database error: {error}")
        return False

    finally:
        conn.close()

def get_attendance():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT student_id, name, date, time, session
        FROM attendance
        ORDER BY date DESC, time DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


if __name__ == "__main__":

    initialize_database()

    print("Database initialized successfully.")

    students = get_students()

    print(f"Students registered: {len(students)}")

    attendance = get_attendance()

    print(f"Attendance records: {len(attendance)}")
    
def delete_student(student_id):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM students WHERE student_id = ?",
            (student_id,)
        )

        deleted = cursor.rowcount
        conn.commit()

        return deleted > 0

    finally:
        conn.close()
