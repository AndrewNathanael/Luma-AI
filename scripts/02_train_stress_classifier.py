#!/usr/bin/env python
"""Train a stress classifier from extracted features."""

from __future__ import annotations

import argparse

import pandas as pd

from rppg_stress.ml import save_model_bundle, save_random_forest_feature_importance, train_from_feature_table
from rppg_stress.utils import deep_get, load_config, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True, help="Feature CSV created by 01_extract_features.py")
    parser.add_argument("--model-out", required=True, help="Output joblib model path")
    parser.add_argument("--metrics-out", required=True, help="Output JSON metrics path")
    parser.add_argument("--feature-importance-out", default=None, help="Output CSV for Random Forest importances")
    parser.add_argument("--config", default="config/default.yaml", help="YAML config path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print("[1/5] Loading configuration and feature table...")
    config = load_config(args.config)
    df = pd.read_csv(args.features)
    print(f"      Features: {args.features}")
    print(f"      Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    if "subject_id" in df.columns:
        subjects = sorted(df["subject_id"].astype(str).unique().tolist())
        print(f"      Subjects ({len(subjects)}): {', '.join(subjects)}")
    if "condition" in df.columns:
        print(f"      Conditions: {df['condition'].value_counts().to_dict()}")
    if "label" in df.columns:
        print(f"      Labels: {df['label'].value_counts().to_dict()}")

    print("[2/5] Training model and running validation...")
    bundle, metrics = train_from_feature_table(df, config)

    print("[3/5] Subject split summary...")
    for key in ("train_subjects", "validation_subjects", "test_subjects"):
        if key in metrics:
            print(f"      {key}: {metrics[key]}")
    for key in ("n_train_samples", "n_validation_samples", "n_test_samples"):
        if key in metrics:
            print(f"      {key}: {metrics[key]}")

    print("[4/5] Saving model and metrics...")
    save_model_bundle(bundle, args.model_out)
    save_json(metrics, args.metrics_out)
    feature_importance_out = args.feature_importance_out or deep_get(config, "training.feature_importance_out", None)
    if feature_importance_out:
        try:
            print("[5/5] Exporting Random Forest feature importance...")
            save_random_forest_feature_importance(bundle, feature_importance_out)
            print(f"Saved feature importance: {feature_importance_out}")
        except ValueError as exc:
            print(f"Skipped feature importance export: {exc}")
    else:
        print("[5/5] Feature importance export not requested.")
    print(f"Saved model: {args.model_out}")
    print(f"Saved metrics: {args.metrics_out}")
    print(f"Accuracy: {metrics.get('accuracy'):.4f} | F1 macro: {metrics.get('f1_macro'):.4f}")


if __name__ == "__main__":
    main()
