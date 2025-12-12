import os
import json

# --- CONFIGURATION ---
BASE_DIR = "inference"
CATEGORIES = ["Normal", "Snow", "Rain"]
# The specific subfolder structure inside each category
SUB_PATH = os.path.join("overall", "previews") 
OUTPUT_FILE = "gallery_data.js"
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
# ---------------------

def generate_gallery_data():
    """
    Scans inference/{category}/overall/previews and generates a JS file.
    """
    data = {}

    print(f"Scanning '{BASE_DIR}' folder structure...")

    for category in CATEGORIES:
        # Construct the full path: inference/normal/overall/previews
        folder_path = os.path.join(BASE_DIR, category, SUB_PATH)
        images_list = []

        if os.path.exists(folder_path):
            # Get all files in the directory
            files = os.listdir(folder_path)
            
            # Filter for images and sort them alphabetically
            images_list = [
                f for f in files 
                if f.lower().endswith(ALLOWED_EXTENSIONS)
            ]
            images_list.sort()
            
            print(f"  - Found {len(images_list)} images in '{category}'")
            print(f"    (Path: {folder_path})")
        else:
            print(f"  ! Warning: Folder not found: {folder_path}")
        
        # Add to the dictionary
        data[category] = images_list

    # Generate the JavaScript file content
    js_content = f"const GALLERY_DATA = {json.dumps(data, indent=4)};"

    try:
        with open(OUTPUT_FILE, "w") as f:
            f.write(js_content)
        print(f"\nSuccess! Generated '{OUTPUT_FILE}'")
    except Exception as e:
        print(f"\nError writing file: {e}")

if __name__ == "__main__":
    generate_gallery_data()