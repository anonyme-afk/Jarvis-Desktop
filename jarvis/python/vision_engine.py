"""
Moteur de vision avancé pour JARVIS.
Sources :
- YOLOv8        : github.com/ultralytics/ultralytics
- MediaPipe     : github.com/google/mediapipe
- face_recognition : github.com/ageitgey/face_recognition
- OpenCV        : github.com/opencv/opencv
"""
import cv2
import threading
import base64
import os
import json
import time
import numpy as np
from typing import Optional, Callable

# ===== DÉTECTION D'OBJETS YOLO =====
class ObjectDetector:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO('yolov8n.pt')  # nano = léger, tourne sur vieux PC
            print("[VISION] YOLOv8 chargé")
        except ImportError:
            print("[VISION] ultralytics non installé, détection YOLO désactivée")

    def detect(self, frame) -> list:
        if not self.model:
            return []
        results = self.model(frame, verbose=False)[0]
        detections = []
        for box in results.boxes:
            label = results.names[int(box.cls[0])]
            conf  = float(box.conf[0])
            if conf > 0.5:
                detections.append({"label": label, "confidence": round(conf, 2)})
        return detections

    def describe_frame(self, frame) -> str:
        detections = self.detect(frame)
        if not detections:
            return "Rien de particulier détecté."
        items = [f"{d['label']} ({int(d['confidence']*100)}%)" for d in detections]
        return "Je vois : " + ", ".join(items)


# ===== DÉTECTION DE GESTES MEDIAPIPE =====
class GestureDetector:
    def __init__(self, on_gesture: Optional[Callable] = None):
        self.on_gesture = on_gesture
        self.mp = None
        self.hands = None
        self.face_mesh = None
        self._load()

    def _load(self):
        try:
            import mediapipe as mp
            self.mp = mp
            self.hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.7
            )
            self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True
            )
            print("[VISION] MediaPipe chargé")
        except ImportError:
            print("[VISION] mediapipe non installé")

    def process_frame(self, frame) -> dict:
        if not self.mp:
            return {}
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = {"gesture": None, "fingers_up": 0, "eye_looking": True}

        # Détection des mains
        hand_results = self.hands.process(rgb)
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                fingers = self._count_fingers(hand_landmarks)
                result["fingers_up"] = fingers
                gesture = self._classify_gesture(hand_landmarks, fingers)
                if gesture:
                    result["gesture"] = gesture
                    if self.on_gesture:
                        self.on_gesture(gesture)

        return result

    def _count_fingers(self, landmarks) -> int:
        tips = [4, 8, 12, 16, 20]
        pips = [3, 6, 10, 14, 18]
        count = 0
        lm = landmarks.landmark
        for i, (tip, pip) in enumerate(zip(tips, pips)):
            if i == 0:  # Pouce
                if lm[tip].x < lm[pip].x:
                    count += 1
            else:
                if lm[tip].y < lm[pip].y:
                    count += 1
        return count

    def _classify_gesture(self, landmarks, fingers: int) -> Optional[str]:
        if fingers == 1:
            return "index_up"        # Volume +
        elif fingers == 2:
            return "peace"           # Screenshot
        elif fingers == 5:
            return "open_hand"       # Stop / Pause
        elif fingers == 0:
            return "fist"            # Mute
        return None


# ===== RECONNAISSANCE FACIALE =====
class FaceRecognizer:
    def __init__(self):
        self.known_faces = {}
        self.owner_name = "Monsieur"
        self._load_known_faces()

    def _load_known_faces(self):
        faces_dir = os.path.join(os.path.dirname(__file__), 'faces')
        if not os.path.exists(faces_dir):
            os.makedirs(faces_dir)
            return
        try:
            import face_recognition
            for fname in os.listdir(faces_dir):
                if fname.endswith(('.jpg', '.png')):
                    img = face_recognition.load_image_file(os.path.join(faces_dir, fname))
                    encodings = face_recognition.face_encodings(img)
                    if encodings:
                        name = os.path.splitext(fname)[0]
                        self.known_faces[name] = encodings[0]
            print(f"[VISION] {len(self.known_faces)} visage(s) connu(s)")
        except ImportError:
            print("[VISION] face_recognition non installé")

    def identify(self, frame) -> Optional[str]:
        try:
            import face_recognition
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb)
            if not locations:
                return None
            encodings = face_recognition.face_encodings(rgb, locations)
            for enc in encodings:
                for name, known_enc in self.known_faces.items():
                    matches = face_recognition.compare_faces([known_enc], enc, tolerance=0.6)
                    if matches[0]:
                        return name
            return "inconnu"
        except:
            return None


# ===== SURVEILLANCE CONTINUE (thread de fond) =====
class VisionSurveillance:
    def __init__(self, callback: Callable):
        self.callback = callback
        self.running = False
        self.camera_index = 0
        self.detector = ObjectDetector()
        self.gesture_detector = GestureDetector(
            on_gesture=lambda g: self.callback("gesture", g)
        )
        self.face_recognizer = FaceRecognizer()
        self._last_face_check = 0
        self._last_person_seen = None

    def start(self):
        self.running = True
        threading.Thread(target=self._surveillance_loop, daemon=True).start()
        print("[VISION] Surveillance démarrée")

    def stop(self):
        self.running = False

    def _surveillance_loop(self):
        cap = cv2.VideoCapture(self.camera_index)
        frame_count = 0
        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            frame_count += 1

            # Gestes : chaque frame
            gesture_data = self.gesture_detector.process_frame(frame)

            # Détection objets : toutes les 30 frames
            if frame_count % 30 == 0:
                detections = self.detector.detect(frame)
                phone_detected = any(d['label'] == 'cell phone' for d in detections)
                if phone_detected:
                    self.callback("phone_detected", None)

            # Reconnaissance faciale : toutes les 90 frames
            if frame_count % 90 == 0:
                name = self.face_recognizer.identify(frame)
                if name and name != self._last_person_seen:
                    self._last_person_seen = name
                    self.callback("face_recognized", name)

            # Détecter intrusion (personne inconnue)
            if frame_count % 150 == 0:
                name = self.face_recognizer.identify(frame)
                if name == "inconnu":
                    self.callback("intruder_detected", None)

            time.sleep(0.033)  # ~30 FPS max
        cap.release()


vision_surveillance = None

def get_frame_b64(camera_index=0) -> Optional[str]:
    cap = cv2.VideoCapture(camera_index)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    _, buf = cv2.imencode('.jpg', frame)
    return base64.b64encode(buf.tobytes()).decode()
