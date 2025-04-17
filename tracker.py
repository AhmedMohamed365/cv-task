import cv2
import numpy as np
from ultralytics import YOLO
import os
from pathlib import Path
import datetime

class PeopleTracker:
    def __init__(self, model_path='yolo12m.pt', tracker_config='utils/custom-botsort.yaml'):
        self.model = YOLO(model_path)
        self.tracker_config = tracker_config
        self.threshold = 20  # 20 seconds
        self.track_colors = {}
        self.output_dir = 'outputs'
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs('violations', exist_ok=True)

    def init_video_writer(self, input_video_path):
        cap = cv2.VideoCapture(input_video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        output_path = os.path.join(
            self.output_dir,
            f"{Path(input_video_path).stem}_tracked.mp4"
        )
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        return writer, cap, output_path

    def get_track_color(self, track_id):
        if track_id not in self.track_colors:
            self.track_colors[track_id] = (
                int(np.random.randint(0, 255)),
                int(np.random.randint(0, 255)),
                int(np.random.randint(0, 255))
            )
        return self.track_colors[track_id]

    def annotate_frame(self, frame, detections):
        annotated_frame = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            track_id = det['id']
            conf = det['conf']
            color = self.get_track_color(track_id)
            
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

    def save_violation_image(self, video_name, frame, pid):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(f"violations/{video_name}", exist_ok=True)
        path = f"violations/{video_name}/{pid}_{timestamp}.jpg"
        cv2.imwrite(path, frame)
        return path

    def track(self, frame):
        results = self.model.track(
            frame,
            persist=True,
            classes=0,  # person class
            conf=0.3,
            iou=0.5,
            tracker=self.tracker_config,
            agnostic_nms=True
        )
        
        detections = []
        if results[0].boxes is not None and hasattr(results[0].boxes, 'id'):
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
            confidences = results[0].boxes.conf.cpu().numpy()
            
            for box, track_id, conf in zip(boxes, track_ids, confidences):
                detections.append({
                    'id': int(track_id),
                    'bbox': box.tolist(),
                    'conf': float(conf)
                })
        
        return detections