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

# Create sidebar
sidebar = st.sidebar
sidebar.title("Tracked People")
sidebar.markdown("**Current IDs and Duration:**")

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

            # Check for violations and update sidebar
            violation_ids = set()
            sidebar_text = ""
            
            for pid, times in id_times.items():
                duration = times["last_seen"] - times["enter"]
                status = "🔴 Violation" if duration > tracker.threshold else "🟢 Normal"
                sidebar_text += f"ID {pid}: {duration:.1f}s - {status}\n"
                
                if duration > tracker.threshold:  # 120 seconds
                    violation_ids.add(pid)
                    image_path = tracker.save_violation_image(filename, frame, pid)
                    document_id = mongo_client.save_violation(filename, detections)
                    postgres_client.log_id(
                        pid,
                        datetime.datetime.fromtimestamp(times["enter"]),
                        datetime.datetime.fromtimestamp(times["last_seen"]),
                        filename,
                        document_id
                    )

            # Update sidebar
            sidebar.text_area("Current Tracking", value=sidebar_text, height=300, disabled=True, key=f"tracking_status_{frame_count}")

            # Draw annotations and update display
            annotated_frame = draw_boxes(frame, detections, len(ids_in_scene), violation_ids)
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
