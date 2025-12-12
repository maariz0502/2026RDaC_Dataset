import os
import cv2
from ultralytics import YOLO
from dotenv import load_dotenv # Import this

# 1. Load the variables from .env
load_dotenv() 

# 2. Get the paths (with default backups if the env var is missing)
MODEL_GROUP_PATH = os.getenv("MODEL_GROUP_PATH", "weights/default_groups.pt")
MODEL_LIGHT_PATH = os.getenv("MODEL_LIGHT_PATH", "weights/default_lights.pt")
VIDEO_PATH = os.getenv("VIDEO_PATH", "input.mp4")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "output.mp4")

def process_video():
    # 1. Load Models
    print("Loading models...")
    model_group = YOLO(MODEL_GROUP_PATH)
    model_light = YOLO(MODEL_LIGHT_PATH)

    # 2. Open Video
    cap = cv2.VideoCapture(VIDEO_PATH)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)

    # 3. Setup Video Writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (width, height))

    print("Processing video frames...")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # ==========================================
        # STAGE 1: Detect Traffic Light Groups
        # ==========================================
        # Run inference on the full frame
        group_results = model_group.predict(frame, conf=0.4, verbose=False)

        # We need to draw on a copy or the original frame
        visualized_frame = frame.copy()

        for result in group_results:
            boxes = result.boxes
            for box in boxes:
                # Get Group Coordinates (Global)
                gx1, gy1, gx2, gy2 = box.xyxy[0].cpu().numpy().astype(int)
                conf_group = float(box.conf[0])
                
                # Safety check: Ensure coordinates are within frame bounds
                gx1, gy1 = max(0, gx1), max(0, gy1)
                gx2, gy2 = min(width, gx2), min(height, gy2)

                # Draw the GROUP Box (Cyan)
                cv2.rectangle(visualized_frame, (gx1, gy1), (gx2, gy2), (255, 255, 0), 3)
                cv2.putText(visualized_frame, f"GROUP {conf_group:.2f}", (gx1, gy1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                # ==========================================
                # STAGE 2: Detect Individual Lights
                # ==========================================
                # Crop the image to the group area
                group_crop = frame[gy1:gy2, gx1:gx2]

                # Skip if crop is empty or too small
                if group_crop.size == 0 or group_crop.shape[0] < 10 or group_crop.shape[1] < 10:
                    continue

                # Run inference on the CROP
                light_results = model_light.predict(group_crop, conf=0.25, verbose=False)

                for light_res in light_results:
                    for light_box in light_res.boxes:
                        # Get Light Coordinates (LOCAL to the crop)
                        lx1, ly1, lx2, ly2 = light_box.xyxy[0].cpu().numpy().astype(int)
                        
                        # Get Class ID and Label (e.g., 0=Red, 1=Green)
                        cls_id = int(light_box.cls[0])
                        label_name = model_light.names[cls_id]
                        
                        # --- THE CRITICAL MATH ---
                        # Convert Local Crop Coords -> Global Frame Coords
                        global_lx1 = lx1 + gx1
                        global_ly1 = ly1 + gy1
                        global_lx2 = lx2 + gx1
                        global_ly2 = ly2 + gy1

                        # Determine Color based on label
                        color = (255, 255, 255) # Default White
                        if 'red' in label_name.lower(): color = (0, 0, 255)
                        elif 'green' in label_name.lower(): color = (0, 255, 0)
                        elif 'yellow' in label_name.lower(): color = (0, 255, 255)

                        # Draw the LIGHT Box
                        cv2.rectangle(visualized_frame, (global_lx1, global_ly1), (global_lx2, global_ly2), color, 2)
                        
                        # (Optional) Draw Link Line connecting Light to Group Label
                        # cv2.line(visualized_frame, (gx1, gy1), (global_lx1, global_ly1), color, 1)

        # Write frame to video
        out.write(visualized_frame)
        
        # Optional: Show detection in window (press q to quit)
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