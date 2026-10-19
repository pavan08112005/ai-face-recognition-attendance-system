import cv2
import numpy as np
from insightface.app import FaceAnalysis


class FaceEngine:
    def __init__(self):
        print("Loading InsightFace model...")

        self.app = FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"]
        )

        self.app.prepare(
            ctx_id=0,
            det_size=(640, 640)
        )

        print("InsightFace model loaded successfully.")

    def detect_faces(self, frame):
        """
        Detect all faces in a camera frame.
        Returns InsightFace face objects.
        """
        return self.app.get(frame)

    def get_embedding(self, face):
        """
        Return normalized ArcFace embedding.
        """
        embedding = face.embedding

        norm = np.linalg.norm(embedding)

        if norm == 0:
            return None

        return embedding / norm

    def compare_faces(self, embedding1, embedding2):
        """
        Calculate cosine similarity between two face embeddings.
        """
        return float(np.dot(embedding1, embedding2))
    
    
    def get_head_position(self, face):
        """Return normalized horizontal nose position for testing."""
        landmarks = getattr(face, "landmark_2d_106", None)

        if landmarks is None or len(landmarks) <= 54:
            return None

        x1, y1, x2, y2 = face.bbox.astype(float)
        face_width = x2 - x1

        if face_width <= 0:
            return None

        # Landmark 54 is a candidate point; verify visually before
        # relying on it for movement detection.
        candidate_x = float(landmarks[54][0])
        return (candidate_x - x1) / face_width


    
    def assess_face_quality(self, frame, face):
        """Basic face-size, blur and brightness screening."""
        height, width = frame.shape[:2]
        x1, y1, x2, y2 = face.bbox.astype(int)

        x1 = max(0, min(x1, width))
        x2 = max(0, min(x2, width))
        y1 = max(0, min(y1, height))
        y2 = max(0, min(y2, height))

        if x2 <= x1 or y2 <= y1:
            return False, "Invalid face region"

        if (x2 - x1) < 80 or (y2 - y1) < 80:
            return False, "Move closer"

        roi = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        blur_score = cv2.Laplacian(
            gray, cv2.CV_64F
        ).var()

        brightness = float(np.mean(gray))

        if blur_score < 20:
            return False, "Image blurry"

        if brightness < 25:
            return False, "Too dark"

        if brightness > 230:
            return False, "Too bright"

        return True, "Quality OK"



if __name__ == "__main__":
    print("Starting Face Engine Test...")

    engine = FaceEngine()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open camera.")
        exit()

    print("Camera started.")
    print("Press Q to quit.")

    while True:
        ret, frame = camera.read()

        if not ret:
            print("ERROR: Could not read camera frame.")
            break

        faces = engine.detect_faces(frame)

        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)

            embedding = engine.get_embedding(face)
            head_position = engine.get_head_position(face)
            print("Head position:", head_position)

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Face detected | Embedding: {len(embedding)}D",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        cv2.imshow("InsightFace Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    print("Face Engine Test Completed.")