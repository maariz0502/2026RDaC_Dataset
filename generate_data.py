# Script for generating file paths to each image/label.
import os
import json

# Define where your images are
DIRS = {
    "train": "images/train",
    "val":   "images/val"
}

# Supported image extensions
EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')

data = { "train": [], "val": [] }

print("Scanning directories...")

for dataset_type, folder_path in DIRS.items():
    if not os.path.exists(folder_path):
        print(f"Warning: {folder_path} not found.")
        continue
        
    # List all files in the directory
    files = sorted(os.listdir(folder_path))
    
    # Filter only images
    for f in files:
        if f.lower().endswith(EXTS):
            data[dataset_type].append(f)
            
    print(f"Found {len(data[dataset_type])} images in {dataset_type}")

# Write to a JavaScript file
output_content = f"const GALLERY_DATA = {json.dumps(data, indent=2)};"

with open("gallery_data.js", "w") as f:
    f.write(output_content)

print("\nSuccess! Created 'gallery_data.js'.")