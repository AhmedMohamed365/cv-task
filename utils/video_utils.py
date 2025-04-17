import cv2
import numpy as np

def get_video_frames(video_path):
    """Generator function to yield frames from a video file."""
    cap = cv2.VideoCapture(video_path)
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            yield frame
    finally:
        cap.release()

def draw_boxes(frame, detections, people_count=None, violation_ids=None):
    """Draw bounding boxes and labels on the frame."""
    annotated_frame = frame.copy()
    violation_ids = violation_ids or set()
    
    # Draw people count if provided
    if people_count is not None:
        cv2.putText(
            annotated_frame,
            f"People in ROI: {people_count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
    
    # Draw detection boxes
    for det in detections:
        x1, y1, x2, y2 = map(int, det['bbox'])
        track_id = det['id']
        conf = det.get('conf', 1.0)
        
        # Set color based on violation status
        if track_id in violation_ids:
            color = [0, 0, 255]  # Red for violations
        else:
            color = np.random.RandomState(track_id).randint(0, 255, size=3).tolist()
        
        # Draw bounding box
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw label background
        cv2.rectangle(annotated_frame, (x1, y1 - 30), (x1 + 130, y1), color, -1)
        
        # Add ID and confidence text
        cv2.putText(
            annotated_frame,
            f"ID: {track_id} - {conf:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            2
        )
    
    return annotated_frame