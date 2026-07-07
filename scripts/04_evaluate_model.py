#!/usr/bin/env python
"""Evaluate a saved model on a feature table."""

from __future__ import annotations

import argparse

import pandas as pd

from rppg_stress.evaluation import classification_metrics, summarize_by_subject
from rppg_stress.ml import evaluate_loso_from_feature_table, load_model_bundle, predict_from_features
from rppg_stress.utils import load_config, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True, help="Feature CSV")
    parser.add_argument("--model", default=None, help="Saved joblib model")
    parser.add_argument("--output", required=True, help="Output JSON metrics")
    parser.add_argument("--loso", action="store_true", help="Run Leave-One-Subject-Out evaluation instead of saved-model evaluation")
    parser.add_argument("--config", default="config/default.yaml", help="YAML config path for --loso")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.features)
    if "label" not in df.columns:
        raise ValueError("Feature CSV must contain a label column for evaluation")
    if args.loso:
        config = load_config(args.config)
        metrics = evaluate_loso_from_feature_table(df, config)
        save_json(metrics, args.output)
        print(f"Saved LOSO evaluation: {args.output}")
        print(f"Accuracy: {metrics.get('accuracy'):.4f} | F1 macro: {metrics.get('f1_macro'):.4f}")
        return

    if args.model is None:
        raise ValueError("--model is required unless --loso is used")
    bundle = load_model_bundle(args.model)
    y_pred, y_score = predict_from_features(bundle, df)
    y_true = df["label"].astype(int).to_numpy()
    metrics = classification_metrics(y_true, y_pred, y_score)
    if "subject_id" in df.columns:
        metrics.update(summarize_by_subject(df["subject_id"].astype(str), y_true, y_pred))
    save_json(metrics, args.output)
    print(f"Saved evaluation: {args.output}")
    print(f"Accuracy: {metrics.get('accuracy'):.4f} | F1 macro: {metrics.get('f1_macro'):.4f}")


if __name__ == "__main__":
    main()
