import json
import os
import glob
import numpy as np

# We are running this locally, so everything is in the current directory (".")
input_dir = "."
output_file = "transforms.json"

print("Fixing the OpenCV -> OpenGL coordinate system mismatch...")

# Load the files directly from the current folder
with open("intrinsic.json", "r") as f:
    intrinsics = json.load(f)
with open("poses.json", "r") as f:
    poses = json.load(f)

camera_matrix = intrinsics["camera_matrix"]

transforms = {
    "fl_x": camera_matrix[0][0],
    "fl_y": camera_matrix[1][1],
    "cx": camera_matrix[0][2],
    "cy": camera_matrix[1][2],
    "w": intrinsics["image_width"],
    "h": intrinsics["image_height"],
    "camera_model": "OPENCV",
    "frames": []
}

# Find all images in the local images/ folder
image_files = sorted(glob.glob(os.path.join(input_dir, "images", "frame_*.png")))

for img_path in image_files:
    filename = os.path.basename(img_path)
    idx_str = str(int(filename.replace("frame_", "").replace(".png", "")))

    if idx_str in poses:
        # Load the raw OpenCV 4x4 matrix
        pose = np.array(poses[idx_str])
        
        # THE FIX: Convert OpenCV (Right-Down-Forward) to OpenGL (Right-Up-Backward)
        # We do this by negating the Y and Z axis column vectors
        pose[:, 1:3] *= -1.0
        
        transforms["frames"].append({
            "file_path": f"images/{filename}",
            "transform_matrix": pose.tolist()
        })

# Overwrite the transforms.json
with open(output_file, "w") as f:
    json.dump(transforms, f, indent=4)

print(f"✅ Fixed! Saved {len(transforms['frames'])} frames with corrected camera orientations.")
