# --- tracking.py ---
import uuid
import os
import cv2
class PeopleTracker:
    def __init__(self):
        self.threshold = 30  # seconds
        self.tracker = self.init_tracker()

    def init_tracker(self):
        # Initialize a simple tracker (e.g. SORT, DeepSort, etc.)
        return cv2.TrackerKCF_create()

    def track(self, frame):
        # Dummy tracking logic (replace with real one)
        return 

    def save_violation_image(self, frame, pid):
        path = f"violations/{pid}_{uuid.uuid4()}.jpg"
        os.makedirs("violations", exist_ok=True)
        cv2.imwrite(path, frame)
        return path
