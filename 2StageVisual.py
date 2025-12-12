import os
import cv2
from ultralytics import YOLO
from dotenv import load_dotenv

# 1. Load the variables from .env
load_dotenv() 

# 2. Get the paths (with default backups if the env var is missing)
MODEL_GROUP_PATH = os.getenv("MODEL_GROUP_PATH", "weights/default_groups.pt")
MODEL_LIGHT_PATH = os.getenv("MODEL_LIGHT_PATH", "weights/default_lights.pt")
VIDEO_PATH = os.getenv("VIDEO_PATH", "input.mp4")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "output.mp4")
TARGET_W, TARGET_H = 1280, 720      # The resolution that the video will be resized

def process_video():
    # 1. Load Models
    print("Loading models...")
    model_group = YOLO(MODEL_GROUP_PATH)
    model_light = YOLO(MODEL_LIGHT_PATH)

    # 2. Open Video
    cap = cv2.VideoCapture(VIDEO_PATH)
    
    # We get the original FPS, but we set our own Target Width/Height
    fps = cap.get(cv2.CAP_PROP_FPS)

    # 3. Setup Video Writer (Use target size, not original size)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (TARGET_W, TARGET_H))

    print(f"Processing video frames (Resizing to {TARGET_W}x{TARGET_H})...")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (TARGET_W, TARGET_H))

        # Update width/height variables for safety checks later in the loop
        width, height = TARGET_W, TARGET_H

        # ==========================================
        # STAGE 1: Detect Traffic Light Groups
        # ==========================================
        # Run inference on the resized frame
        group_results = model_group.predict(frame, conf=0.4, verbose=False, device=0)

        # We need to draw on a copy or the original frame
        visualized_frame = frame.copy()

        for result in group_results:
            boxes = result.boxes
            for box in boxes:
                # Get Group Coordinates (Global)
                gx1, gy1, gx2, gy2 = box.xyxy[0].cpu().numpy().astype(int)
                conf_group = float(box.conf[0])
                
                # Safety check: Ensure coordinates are within new frame bounds
                gx1, gy1 = max(0, gx1), max(0, gy1)
                gx2, gy2 = min(width, gx2), min(height, gy2)

                # Draw the GROUP Box (Cyan)
                cv2.rectangle(visualized_frame, (gx1, gy1), (gx2, gy2), (255, 255, 0), 2)
                cv2.putText(visualized_frame, f"group {conf_group:.2f}", (gx1, gy1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

                # ==========================================
                # STAGE 2: Detect Individual Lights
                # ==========================================
                # Crop the image to the group area
                group_crop = frame[gy1:gy2, gx1:gx2]

                # Skip if crop is empty or too small
                if group_crop.size == 0 or group_crop.shape[0] < 10 or group_crop.shape[1] < 10:
                    continue

                # Run inference on the CROP
                light_results = model_light.predict(group_crop, conf=0.25, verbose=False, device=0)

                for light_res in light_results:
                    for light_box in light_res.boxes:
                        # Get Light Coordinates (LOCAL to the crop)
                        lx1, ly1, lx2, ly2 = light_box.xyxy[0].cpu().numpy().astype(int)
                        
                        # Get Class ID, Label, and Confidence
                        cls_id = int(light_box.cls[0])
                        label_name = model_light.names[cls_id]
                        conf_light = float(light_box.conf[0])
                        
                        # Convert Local Crop Coords -> Global Frame Coords
                        global_lx1 = lx1 + gx1
                        global_ly1 = ly1 + gy1
                        global_lx2 = lx2 + gx1
                        global_ly2 = ly2 + gy1

                        # Determine Color based on label and shorten label_name
                        color = (255, 255, 255) # Default White
                        if 'red' in label_name.lower(): 
                            color = (0, 0, 255)
                            label_name='red'
                        elif 'green' in label_name.lower(): 
                            color = (0, 255, 0)
                            label_name='green'
                        elif 'yellow' in label_name.lower(): 
                            color = (0, 255, 255)
                            label_name='yellow'

                        # Draw the LIGHT Box
                        # CHANGED: Thickness is 2 (matches group)
                        cv2.rectangle(visualized_frame, (global_lx1, global_ly1), (global_lx2, global_ly2), color, 2)
                        
                        # CHANGED: Added Text Label with Confidence for the light
                        # We print it slightly above the light box
                        label_text = f"{label_name} {conf_light:.2f}"
                        cv2.putText(visualized_frame, label_text, (global_lx1, global_ly1 - 5), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Write resized frame to video
        out.write(visualized_frame)
        
        # Show detection in window (press q to quit)
        cv2.imshow('2-Stage Detection', visualized_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Done! Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    process_video()