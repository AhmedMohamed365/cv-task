import streamlit as st
import os
import cv2
import uuid
import datetime
from tracker import PeopleTracker
from utils.mongo_client import MongoClientWrapper
from utils.postgres_client import PostgresClient
from utils.video_utils import draw_boxes, get_video_frames

# Initialize services
tracker = PeopleTracker()
mongo_client = MongoClientWrapper()
postgres_client = PostgresClient()

UPLOAD_DIR = "videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="People Tracking App", layout="wide")
st.title("🚀 Smart People Tracking and Violation Detection")

# Upload video
uploaded_file = st.file_uploader("Upload a video", type=["mp4", "avi"])

if uploaded_file:
    # Generate unique filename and save video
    filename = f"{uuid.uuid4()}.mp4"
    video_path = os.path.join(UPLOAD_DIR, filename)
    with open(video_path, "wb") as f:
        f.write(uploaded_file.read())
    st.success(f"Video saved to {video_path}")

    # Initialize video writer
    writer, cap, output_path = tracker.init_video_writer(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    # Create placeholders for display
    frame_display = st.empty()
    status_text = st.empty()

    # Initialize tracking variables
    id_times = {}
    frame_count = 0
    
    try:
        for frame in get_video_frames(video_path):
            frame_count += 1
            timestamp = frame_count / fps
            
            # Process frame and get detections
            detections = tracker.track(frame)
            ids_in_scene = []

            # Update tracking information
            for det in detections:
                pid = det["id"]
                ids_in_scene.append(pid)

                if pid not in id_times:
                    id_times[pid] = {"enter": timestamp, "last_seen": timestamp}
                else:
                    id_times[pid]["last_seen"] = timestamp

            # Check for violations (2 minutes threshold)
            for pid, times in id_times.items():
                duration = times["last_seen"] - times["enter"]
                if duration > tracker.threshold:  # 120 seconds
                    image_path = tracker.save_violation_image(filename, frame, pid)
                    mongo_client.save_violation(pid, image_path, timestamp)
                    postgres_client.log_id(
                        pid,
                        datetime.datetime.fromtimestamp(times["enter"]),
                        datetime.datetime.fromtimestamp(times["last_seen"]),
                        filename
                    )

            # Draw annotations and update display
            annotated_frame = draw_boxes(frame, detections, len(ids_in_scene))
            writer.write(annotated_frame)
            frame_display.image(annotated_frame, channels="BGR")
            
            # Update status
            status_text.text(f"Processing frame {frame_count} - {len(ids_in_scene)} people in scene")
            
    except Exception as e:
        st.error(f"Error processing video: {str(e)}")
    finally:
        # Clean up
        writer.release()
        cap.release()
        
    st.success("Video processing complete! Output saved to: " + output_path)

# # --- tracking.py ---

# class PeopleTracker:
#     def __init__(self):
#         self.threshold = 30  # seconds
#         self.tracker = self.init_tracker()

#     def init_tracker(self):
#         # Initialize a simple tracker (e.g. SORT, DeepSort, etc.)
#         import cv2
#         return cv2.TrackerKCF_create()

#     def track(self, frame):
#         # Dummy tracking logic (replace with real one)
#         return [{"id": 1, "bbox": [100, 100, 50, 100]}]

#     def save_violation_image(self, frame, pid):
#         path = f"violations/{pid}_{uuid.uuid4()}.jpg"
#         os.makedirs("violations", exist_ok=True)
#         cv2.imwrite(path, frame)
#         return path

# # --- mongo_client.py ---

# from pymongo import MongoClient

# class MongoClientWrapper:
#     def __init__(self):
#         self.client = MongoClient("mongodb://localhost:27017")
#         self.db = self.client["tracking"]

#     def save_violation(self, pid, image_path, timestamp):
#         with open(image_path, "rb") as f:
#             image_bytes = f.read()
#         self.db.violations.insert_one({
#             "pid": pid,
#             "timestamp": timestamp,
#             "image": image_bytes
#         })

# # --- postgres_client.py ---

# import psycopg2

# class PostgresClient:
#     def __init__(self):
#         self.conn = psycopg2.connect(
#             dbname="tracking_db",
#             user="postgres",
#             password="postgres",
#             host="localhost",
#             port="5432"
#         )
#         self.cursor = self.conn.cursor()
#         self.create_table()

#     def create_table(self):
#         self.cursor.execute('''CREATE TABLE IF NOT EXISTS tracking (
#             id SERIAL PRIMARY KEY,
#             person_id INT,
#             enter_time FLOAT,
#             exit_time FLOAT,
#             video_name TEXT
#         );''')
#         self.conn.commit()

#     def log_id(self, pid, enter_time, exit_time, video_name):
#         self.cursor.execute(
#             "INSERT INTO tracking (person_id, enter_time, exit_time, video_name) VALUES (%s, %s, %s, %s)",
#             (pid, enter_time, exit_time, video_name)
#         )
#         self.conn.commit()

# # --- video_utils.py ---

# import cv2

# def get_video_frames(video_path):
#     cap = cv2.VideoCapture(video_path)
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret:
#             break
#         yield frame
#     cap.release()

# def draw_boxes(frame, detections):
#     for det in detections:
#         x, y, w, h = det["bbox"]
#         cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
#         cv2.putText(frame, f"ID: {det['id']}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
#     return frame
