import cv2
import numpy as np

from face_engine import FaceEngine
from database import initialize_database, get_students


# ---------------------------------------
# Find the best matching registered face
# ---------------------------------------
def find_best_match(query_embedding, students):

    best_student = None
    best_score = -1.0

    for student in students:

        stored_embedding = student["embedding"]

        score = float(
            np.dot(query_embedding, stored_embedding)
        )

        if score > best_score:
            best_score = score
            best_student = student

    return best_student, best_score


def main():

    initialize_database()

    students = get_students()

    if not students:
        print("No students registered.")
        print("Run: python register_student.py")
        return

    print(f"{len(students)} student(s) loaded.")

    engine = FaceEngine()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open camera.")
        return

    # Initial threshold
    CONFIDENCE_THRESHOLD = 0.45

    print("\nRecognition started.")
    print("Press Q to quit.")

    while True:

        ret, frame = camera.read()

        if not ret:
            continue

        faces = engine.detect_faces(frame)

        for face in faces:

            embedding = engine.get_embedding(face)

            if embedding is None:
                continue

            student, score = find_best_match(
                embedding,
                students
            )

            x1, y1, x2, y2 = face.bbox.astype(int)

            if student and score >= CONFIDENCE_THRESHOLD:

                label = (
                    f"{student['name']} "
                    f"({score:.2f})"
                )

                text_color = (0, 255, 0)

            else:

                label = f"Unknown ({score:.2f})"

                text_color = (0, 0, 255)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                text_color,
                2
            )

            cv2.putText(
                frame,
                label,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                text_color,
                2
            )

        cv2.imshow(
            "Face Recognition",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()