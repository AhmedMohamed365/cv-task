# --- mongo_client.py ---

from pymongo import MongoClient

class MongoClientWrapper:
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["tracking"]

    def save_violation(self, frame_id, detections):
        try:
            result = self.db.violations.insert_one({
                "frame_id": frame_id,
                "detections": detections,
            })
            return result.inserted_id
        except Exception as e:
            print(f"Error saving violation to MongoDB: {str(e)}")
            raise

        