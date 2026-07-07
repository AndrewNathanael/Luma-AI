# rPPG Stress Estimation Project

![rPPG UI Preview](ui_preview.png)

Academic pipeline for estimating physiological stress from facial videos using remote photoplethysmography (rPPG).

## System Flowchart

```mermaid
graph TD
    A[Face Video] --> B(Facial ROI Detection)
    B --> C(ROI RGB Time Series)
    C --> D{rPPG Algorithms: GREEN/CHROM/POS}
    D --> E[BVP, HR, and PRV/HRV Features]
    E --> F((Subject-independent Stress Classification))
    F --> G[Evaluation & Real-time Demo]
```

## Key Features
* **Non-invasive Vital Extraction:** Extracts Heart Rate (HR) and Pulse Rate Variability (PRV/HRV) directly from facial video feeds using remote photoplethysmography (rPPG).
* **Multiple rPPG Algorithms:** Supports various state-of-the-art rPPG extraction methods including GREEN, CHROM, and POS for optimal Blood Volume Pulse (BVP) estimation.
* **Real-time Live Dashboard:** Features a FastAPI and React (Vite) powered dashboard that streams webcam video, displaying live physiological metrics and real-time stress classification.
* **Subject-Independent Machine Learning:** Uses a robust Random Forest model trained on the UBFC-Phys dataset to predict stress states reliably across different, unseen individuals.
* **Comprehensive ML Pipeline:** Includes full scripts for dataset manifest generation, feature extraction, model training, and Leave-One-Subject-Out (LOSO) cross-validation evaluation.

## 1. Installation

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

For development and tests:

```bash
pip install -e ".[dev]"
pytest
```

## 2. Full-Stack Dashboard Scaffold

This project now includes a Vite React frontend and FastAPI backend scaffold.

Backend:

```bash
uvicorn backend.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Default URLs:

```text
FastAPI: http://localhost:8000
API docs: http://localhost:8000/docs
React:   http://localhost:5173
```

## 3. UBFC-Phys Dataset

UBFC-Phys contains 56 participants in folders named `s1` through `s56`. Each subject folder contains three task videos named:

```text
s1/
  vid_s1_T1.avi    # rest
  vid_s1_T2.avi    # speech
  vid_s1_T3.avi    # arithmetic
  bvp_s1_T1.csv    # contact BVP, 64 Hz
  eda_s1_T1.csv    # EDA, 4 Hz
  info_s1.txt
  selfReportedAnx_s1.csv
```

The recommended first binary stress setup is:

```text
T1 / rest        -> 0, low or non-stress
T2 / speech      -> 1, stress
T3 / arithmetic  -> 1, stress
```

Download UBFC-Phys from the official dataUBFC or IEEE DataPort record, extract the subject archives, and keep the subject folders under one root, for example:

```text
data/UBFC-Phys/
  s1/
  s2/
  ...
  s56/
```

Create a manifest automatically:

```bash
python scripts/00_make_manifest.py \
  --root data/UBFC-Phys \
  --output data/ubfc_phys_manifest.csv \
  --dataset ubfc_phys \
  --strict
```

`--dataset auto` also detects UBFC-Phys when the `s<number>` folders and `vid_s<number>_T1/T2/T3.avi` files are present. The generated CSV uses the common manifest format:

```csv
subject_id,video_path,condition,task,dataset
s1,/absolute/path/to/data/UBFC-Phys/s1/vid_s1_T1.avi,rest,T1,UBFC-Phys
s1,/absolute/path/to/data/UBFC-Phys/s1/vid_s1_T2.avi,speech,T2,UBFC-Phys
s1,/absolute/path/to/data/UBFC-Phys/s1/vid_s1_T3.avi,arithmetic,T3,UBFC-Phys
```

Dataset reference: R. Meziati Sabour, Y. Benezeth, P. De Oliveira, J. Chappe, F. Yang, "UBFC-Phys: A Multimodal Database For Psychophysiological Studies Of Social Stress", IEEE Transactions on Affective Computing, 2021. Official record: https://search-data.ubfc.fr/FR-18008901306731-2022-05-05_UBFC-Phys-A-Multimodal-Dataset-For.html

## 4. Feature Extraction

```bash
python scripts/01_extract_features.py \
  --manifest data/ubfc_phys_manifest.csv \
  --output data/features_pos.csv \
  --config config/default.yaml
```

The output contains HR, PRV/HRV, signal-quality features, `label`, `subject_id`, `condition`, and video metadata.

## 5. Training

```bash
python scripts/02_train_stress_classifier.py \
  --features data/features_pos.csv \
  --model-out models/stress_model.joblib \
  --metrics-out results/train_metrics.json \
  --feature-importance-out results/feature_importance_random_forest.csv \
  --config config/default.yaml
```

The default training mode is a subject-independent train/validation/test split. Subjects are disjoint across all three sets. Validation metrics are computed from a model fitted on train subjects only; final held-out test metrics are computed from a model fitted on train plus validation subjects.

Relevant config:

```yaml
training:
  model: random_forest
  validation: subject_split
  validation_size: 0.2
  test_size: 0.2
  random_state: 42
```

For Random Forest, feature importance is exported as a ranked CSV with `feature`, `importance`, and `importance_normalized`.

## 6. Leave-One-Subject-Out Evaluation

Run LOSO from the training script by setting `training.validation: loso`, or run it directly from a feature table:

```bash
python scripts/04_evaluate_model.py \
  --features data/features_pos.csv \
  --output results/loso_metrics.json \
  --loso \
  --config config/default.yaml
```

The LOSO output includes aggregate metrics, per-subject metrics, and fold records with the left-out subject for each fold.

## 7. Saved Model Evaluation

```bash
python scripts/04_evaluate_model.py \
  --features data/features_pos.csv \
  --model models/stress_model.joblib \
  --output results/evaluation.json
```

Use this for a separate held-out feature table. Avoid evaluating a saved model on the same subjects used to train it unless you are checking software plumbing.

## 8. Real-Time Webcam Demo

```bash
python scripts/03_realtime_demo.py \
  --model models/stress_model.joblib \
  --config config/default.yaml
```

The demo displays heart rate, estimated stress class, confidence, signal quality, and face-detection rate.

## 9. Academic Notes

- This project estimates physiological stress correlates; it is not a psychological or medical diagnosis.
- Use subject-independent validation or LOSO for academic reporting.
- Report the rPPG method, ROI backend, window size, split seed, subject IDs per split, and any excluded videos.
- Do not rely on HR alone. Prefer PRV/HRV features such as SDNN, RMSSD, pNN50, LF, HF, LF/HF, and signal-quality measures.
- When possible, compare video-derived BVP with contact BVP/PPG/ECG/EDA references.

## 10. Project Structure

```text
rppg_stress_project/
  backend/
    main.py
    api/
    schemas/
    services/
  config/default.yaml
  data/manifest_example.csv
  frontend/
    package.json
    src/
  requirements.txt
  pyproject.toml
  scripts/
    00_make_manifest.py
    01_extract_features.py
    02_train_stress_classifier.py
    03_realtime_demo.py
    04_evaluate_model.py
  src/rppg_stress/
    dataset.py
    evaluation.py
    features.py
    ml.py
    roi.py
    rppg_algorithms.py
    signal_processing.py
    utils.py
    video_io.py
  tests/
```
