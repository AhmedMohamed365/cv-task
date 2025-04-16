# --- mongo_client.py ---

from pymongo import MongoClient

class MongoClientWrapper:
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017")
        self.db = self.client["tracking"]

    def save_violation(self, pid, image_path, timestamp):
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        self.db.violations.insert_one({
            "pid": pid,
            "timestamp": timestamp,
            "image": image_bytes
        })