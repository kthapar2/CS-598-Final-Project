
# CS598 DLH Final Project: Debiasing Deep Chest X-Ray Classifiers

This repository contains our final project for CS598 Deep Learning for Healthcare (Spring 2025), where we reproduce and extend the methods from the paper:

> **Marcinkevics et al. (2022)**  
> _Debiasing Deep Chest X-Ray Classifiers Using Intra- and Post-processing Methods_

## 🔬 Project Summary

We replicate debiasing techniques proposed in the original paper, focusing on intra- and post-processing strategies for fairness-aware classification of pneumonia using the MIMIC-CXR dataset.

Key methods implemented:
- **Intra-processing**: Pruning, Bias Gradient Descent/Ascent (GD/A)
- **Post-processing**: Equalized Odds, Reject Option Classification (ROC)
- **Baseline comparisons**: Random perturbations, standard (unmodified) models

Our project specifically investigates **ethnicity-based bias** (White vs Hispanic/Latino) on a binary pneumonia prediction task.

We also propose and evaluate an **extension**: pruning only a subset of fully connected layers to preserve performance while reducing bias and runtime.

## 📁 Repository Structure

```
├── chestxray_dataset.py        # Dataset loader for MIMIC-CXR
├── main_ChestXRay.py          # Entry point for training and debiasing
├── algorithms/
│   ├── pruning.py             # Pruning method
│   └── ...                    # Other debiasing implementations
├── models/
│   ├── networks_ChestXRay.py  # VGG-16 backbone model
│   └── ...
├── configs/
│   ├── mimic_cxr_ethnicity.yml
│   ├── mimic_cxr_sex.yml
│   └── ...
├── figures/                   # Output plots (EOD vs Performance)
├── results/                   # JSON summaries of results
└── README.md
```

## 📊 Results Summary

| Method        | EOD (Ours)       | BA (Ours)        |
|---------------|------------------|------------------|
| Standard      | -0.031 ± 0.034   | 0.715 ± 0.083    |
| ROC           | -0.069 ± 0.066   | 0.681 ± 0.072    |
| Equalized Odds| -0.050 (seen)    | 0.670 (seen)     |
| Pruning       | -0.048 ± 0.069   | 0.691 ± 0.069    |
| Bias GD/A     |  0.015 ± 0.036   | 0.640 ± 0.078    |

**Extension**: Partial pruning (only some FC layers)  
→ EOD: -0.071 ± 0.042, BA: 0.698 ± 0.075

## 📌 How to Run

### 1. Environment Setup

```bash
conda create -n cs598-dlh python=3.10
conda activate cs598-dlh
pip install -r requirements.txt
```

### 2. Data Preparation

- Download MIMIC-CXR v2.0.0 from PhysioNet
- Place resized 224x224 frontal images in `data/mimic-cxr`
- Update config YAML with paths and ratios

### 3. Train and Debias

```bash
python main_ChestXRay.py --config configs/mimic_cxr_ethnicity.yml
```

### 4. Analyze Results

```bash
python analyze_results.py
```

## 📹 Video Walkthrough

👉 [TODO: Insert link here]

## 📎 Report

The full writeup is included in [`Final Report.pdf`](link) and follows the CS598 DLH rubric.

## 🤝 Authors

- **Jonathan T. Bui** – jtbui2@illinois.edu  
- **Karan Thapar** – kthapar2@illinois.edu

## 📄 Citation

If you use this repo or ideas in your own work, please cite:

```
@inproceedings{marcinkevics2022debiasing,
  title={Debiasing Deep Chest X-Ray Classifiers Using Intra- and Post-processing Methods},
  author={Marcinkevics, Rihards and Ozkan, Ege and Vogt, Julia E},
  booktitle={Machine Learning for Healthcare Conference},
  year={2022}
}
```
