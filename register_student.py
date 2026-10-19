import cv2
import numpy as np
import sys

from face_engine import FaceEngine
from database import initialize_database, save_student


def register_student(student_id=None, name=None):

    initialize_database()

    # If ID and name were not provided from the website,
    # ask for them in the terminal.
    if not student_id:
        student_id = input("Enter Student ID: ").strip()

    if not name:
        name = input("Enter Student Name: ").strip()

    if not student_id or not name:
        print("Student ID and Name are required.")
        return

    engine = FaceEngine()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open camera.")
        return

    print("\n================================")
    print("STUDENT FACE REGISTRATION")
    print("================================")
    print("Student ID:", student_id)
    print("Name:", name)
    print("")
    print("Look at the camera.")
    print("Move your face slightly left and right.")
    print("Press Q to cancel.\n")

    embeddings = []

    while len(embeddings) < 10:

        ret, frame = camera.read()

        if not ret:
            continue

        faces = engine.detect_faces(frame)

        
        if len(faces) == 1:

            face = faces[0]

            quality_ok, quality_message = (
                engine.assess_face_quality(frame, face)
            )

            if not quality_ok:
                cv2.putText(
                    frame,
                    quality_message,
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 165, 255),
                    2
                )
            else:
                embedding = engine.get_embedding(face)

                if embedding is not None:
                    embeddings.append(embedding)

                    x1, y1, x2, y2 = face.bbox.astype(int)

                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        f"Capturing {len(embeddings)}/10",
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )


            if embedding is not None:

                embeddings.append(embedding)

                x1, y1, x2, y2 = face.bbox.astype(int)

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"Capturing {len(embeddings)}/10",
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

        elif len(faces) > 1:

            cv2.putText(
                frame,
                "Only ONE face should be visible",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        else:

            cv2.putText(
                frame,
                "Face not detected",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        cv2.imshow("Student Registration", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    if len(embeddings) < 5:

        print(
            "Registration cancelled. "
            "Not enough face samples."
        )

        return

    # Average multiple embeddings
    final_embedding = np.mean(
        np.array(embeddings),
        axis=0
    )

    # Normalize final embedding
    final_embedding = (
        final_embedding /
        np.linalg.norm(final_embedding)
    )

    save_student(
        student_id,
        name,
        final_embedding
    )

    print("\n================================")
    print("Student registered successfully!")
    print("Student ID:", student_id)
    print("Name:", name)
    print("Embedding size:", len(final_embedding))
    print("================================")


if __name__ == "__main__":

    # Website mode:
    # python register_student.py is412 rahul

    if len(sys.argv) >= 3:

        student_id = sys.argv[1]
        name = " ".join(sys.argv[2:])

        register_student(
            student_id,
            name
        )

    # Terminal mode:
    # python register_student.py

    else:

        register_student()