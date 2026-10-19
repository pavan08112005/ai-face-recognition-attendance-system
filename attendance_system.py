
import cv2
import numpy as np
import time
from datetime import datetime

from face_engine import FaceEngine
from database import (
    initialize_database,
    get_students,
    mark_attendance
)

CONFIDENCE_THRESHOLD = 0.45
SESSION_NAME = "classroom"
HEAD_MOVEMENT_THRESHOLD = 0.08
CHALLENGE_TIMEOUT = 12


def find_best_match(query_embedding, students):
    best_student = None
    best_score = -1.0
    second_best_score = -1.0

    for student in students:
        stored_embedding = student["embedding"]
        score = float(np.dot(query_embedding, stored_embedding))

        if score > best_score:
            second_best_score = best_score
            best_score = score
            best_student = student
        elif score > second_best_score:
            second_best_score = score

    return best_student, best_score, second_best_score


def main():
    initialize_database()
    students = get_students()

    if not students:
        print("No students registered.")
        return

    print(f"{len(students)} student(s) loaded.")
    engine = FaceEngine()
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open camera.")
        return

    print("\n================================")
    print("AUTOMATIC ATTENDANCE SYSTEM")
    print("================================")
    print("Challenge: look straight, turn your head, then return.")
    print("Press Q to quit.")

    # Per-student challenge progress.
    challenges = {}
    last_marked = set()

    try:
        while True:
            ret, frame = camera.read()
            if not ret:
                continue

            faces = engine.detect_faces(frame)

            # Avoid running a challenge when multiple faces are visible.
            if len(faces) != 1:
                if len(faces) > 1:
                    cv2.putText(
                        frame, "Only one face should be visible",
                        (20, 35), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 165, 255), 2
                    )
                cv2.imshow("Automatic Attendance", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue

            face = faces[0]
            x1, y1, x2, y2 = face.bbox.astype(int)

            quality_ok, quality_message = (
                engine.assess_face_quality(frame, face)
            )

            label = quality_message
            color = (0, 165, 255)

            if quality_ok:
                embedding = engine.get_embedding(face)

                if embedding is not None:
                    student, score, second_score = find_best_match(
                        embedding, students
                    )
                    print(
    f"Best match: {student['name'] if student else 'None'} | "
    f"Best score: {score:.3f} | "
    f"Second score: {second_score:.3f} | "
    f"Margin: {score - second_score:.3f}"
)

                    confident = (
                        student is not None
                        and score >= CONFIDENCE_THRESHOLD
                        and (score - second_score) >= 0.05
                    )

                    if not confident:
                        label = f"Unknown / uncertain | {score:.2f}"
                        color = (0, 0, 255)
                    else:
                        student_id = student["student_id"]
                        name = student["name"]
                        today = datetime.now().strftime("%Y-%m-%d")
                        attendance_key = f"{student_id}_{today}"

                        if attendance_key in last_marked:
                            label = f"{name} | Already processed"
                            color = (255, 200, 0)

                        else:
                            position = engine.get_head_position(face)

                            if position is None:
                                label = f"{name} | Face landmark unavailable"
                            else:
                                state = challenges.get(student_id)

                                if state is None or time.time() - state["start"] > CHALLENGE_TIMEOUT:
                                    challenges[student_id] = {
                                        "start": time.time(),
                                        "center": position,
                                        "turned": False,
                                        "samples": 0,
                                        "sum": 0.0
                                    }
                                    state = challenges[student_id]
                                    label = f"{name}: Look straight"
                                else:
                                    state["samples"] += 1
                                    state["sum"] += position
                                    average_position = (
                                        state["sum"] / state["samples"]
                                    )
                                    movement = abs(
                                        position - state["center"]
                                    )

                                    if not state["turned"]:
                                        if movement >= HEAD_MOVEMENT_THRESHOLD:
                                            state["turned"] = True
                                            label = f"{name}: Turn detected, return to center"
                                        else:
                                            label = f"{name}: Turn your head left or right"
                                    else:
                                        if movement <= HEAD_MOVEMENT_THRESHOLD / 2:
                                            marked = mark_attendance(
                                                student_id,
                                                name,
                                                SESSION_NAME
                                            )
                                            print(f"DEBUG: mark_attendance returned {marked}")
                                            last_marked.add(attendance_key)
                                            challenges.pop(student_id, None)
                                            if marked:
                                                  label = f"{name}: Attendance marked"
                                                  print(f"Attendance marked for {name}")
                                                  color = (0, 255, 0)
                                            else:
                                                  label = f"{name}: Already marked today"
                                                  print(f"Attendance already exists for {name}")
                                                  color = (255, 200, 0)
                                        else:
                                            label = f"{name}: Return to center"

                                    if student_id in challenges:
                                        color = (255, 200, 0)

            cv2.rectangle(
                frame, (x1, y1), (x2, y2), color, 2
            )
            cv2.putText(
                frame, label,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
            )

            cv2.imshow("Automatic Attendance", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    print("\nAttendance session ended.")


if __name__ == "__main__":
    main()
