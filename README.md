```markdown
# Metric-Semantic 3D Reconstruction of a Desktop Scene

This repository contains a complete 2D-to-3D robotics perception pipeline designed to spatially localize and measure physical I/O ports in a metric 3D space. The project was submitted as part of the **CP260-2026: Robotics Perception** course at the **Indian Institute of Science (IISc)**.

## Project Objective
The goal is to generate 6-DoF Oriented Bounding Boxes (OBBs) for 8 distinct entities on a PC tower rear panel using a sparse set of 16 images. The pipeline achieves zero-shot detection without manually annotated 3D ground truth, bridging the gap between 2D Vision-Language Models and true 3D spatial geometry.

## Technical Architecture
The system employs a dual-pipeline approach:
1. **Coordinate Frame Alignment:** Automated pre-processing to resolve OpenCV (Right-Down-Forward) and OpenGL (Right-Up-Backward) extrinsic matrix disparities.
2. **3D Reconstruction:** Utilizes **3D Gaussian Splatting (3DGS)** via Nerfstudio (`splatfacto`) to create a high-fidelity point cloud.
3. **2D Semantic Segmentation:** Uses **GroundingDINO** and **SAM** with a multi-caption aliasing strategy to achieve 100% detection recall across 16 frames.
4. **Spatial Anchoring:** Implements **First-Surface Voxel Anchoring** to snap 3D centers to the physical faceplate of the hardware, eliminating "X-Ray" depth penetration into background walls.
5. **OBB Fitting:** Applies **PCA-aligned Interquartile Range (IQR)** filtering to determine the precise 3D rotation ($SO(3)$) and extents to maximize 2D Polygonal Intersection over Union (IoU).

## Key Performance Metrics
- **VGA Center Error:** 4.32 cm (Passes <15.0 cm threshold)
- **VGA Extent Error:** 0.04 mm
- **Entity Coverage:** 8/8 (2 Baseline + 6 Bonus)
- **Collisions:** Zero spatial overlaps detected

---

## Repository Structure
```text
📁 rp_project/
├── 📄 .gitignore              # Ignores large model weights and data zips
├── 📄 README.md               # Project overview and reproduction instructions
├── 📁 data/
│   ├── 📄 intrinsic.json      # Raw camera intrinsics
│   ├── 📄 poses.json          # Raw OpenCV camera poses
│   └── 📄 transforms.json     # Generated: Aligned OpenGL poses for Nerfstudio
├── 📁 docs/
│   ├── 📄 report.pdf          # Final LaTeX Technical Report
│   └── 📄 3d_verification.png # Generated 3D cluster validation plot
├── 📁 src/
│   ├── 📄 format_data.py      # Pose alignment script (OpenCV -> OpenGL)
│   └── 📄 main_pipeline.ipynb # Master notebook for 3DGS training and OBB detection
└── 📄 FINAL_SUBMISSION.json   # Output: Validated OBB coordinates for all 8 entities
```

---

## Reproduction Guide

The following steps outline how to run the entire pipeline from raw data to the final 3D visualization. Ensure you have a CUDA-enabled GPU. 

*(Note: The master notebook is designed to be run in a Kaggle or Colab environment with T4/P100 GPUs).*

### 1. Environment Setup
Install the core dependencies:
```bash
pip install torch torchvision
pip install nerfstudio
ns-install-cli
pip install plyfile matplotlib
```

### 2. Data Alignment (OpenCV to OpenGL)
The raw dataset provides camera poses in OpenCV format. Nerfstudio requires OpenGL. Run the formatting script to generate the `transforms.json` file.
```bash
python src/format_data.py
```
*Expected Output: `✅ Fixed! Saved 16 frames with corrected camera orientations.`*

### 3. Train 3D Gaussian Splatting
Run the training sequence using the Nerfstudio CLI. We disable internal pose normalization to preserve the metric coordinate frame.
```bash
ns-train splatfacto \
  --output-dir outputs \
  --max-num-iterations 30000 \
  --pipeline.model.camera-optimizer.mode off \
  --optimizers.means.optimizer.lr 0.0016 \
  --optimizers.scales.optimizer.lr 0.005 \
  nerfstudio-data \
  --data data/ \
  --orientation-method none \
  --center-method none \
  --auto-scale-poses False
```

### 4. Export the Point Cloud
Once training is complete, export the 3D Gaussian cloud as a `.ply` file.
```bash
# Locate your generated config.yml in the outputs/ directory
ns-export gaussian-splat --load-config outputs/.../config.yml --output-dir exports/
```

### 5. Run Semantic 3D OBB Detection
Open and execute the `src/main_pipeline.ipynb` notebook.
This notebook will:
1. Load GroundingDINO and SAM weights.
2. Filter the `.ply` file by opacity (σ > 0.05).
3. Cast 3D Ray-Cones from the 2D bounding boxes.
4. Execute **First-Surface Voxel Anchoring** and **PCA OBB fitting**.
5. Save the results to `FINAL_SUBMISSION.json`.

### 6. Verify Geometry
The final cell in `main_pipeline.ipynb` will generate a 3D scatter plot of the predicted OBB centers against the camera poses and the Ground Truth VGA anchor. 
This plot (`docs/3d_verification.png`) visually confirms that the First-Surface anchor successfully prevented background ray-penetration (the "X-Ray Bug") and correctly localized background objects (e.g., the keyboard).
```
