"""Evaluation helpers for stress classification and rPPG experiments."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics(
    y_true: Iterable[int],
    y_pred: Iterable[int],
    y_score: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    y_true = np.asarray(list(y_true))
    y_pred = np.asarray(list(y_pred))
    labels = sorted(np.unique(np.concatenate([y_true, y_pred])).tolist())

    out: Dict[str, Any] = {
        "n_samples": int(len(y_true)),
        "labels": labels,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "precision_weighted": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall_weighted": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "classification_report": classification_report(y_true, y_pred, zero_division=0, output_dict=True),
    }

    if y_score is not None and len(labels) == 2:
        try:
            if y_score.ndim == 2 and y_score.shape[1] >= 2:
                score = y_score[:, 1]
            else:
                score = np.asarray(y_score).ravel()
            out["roc_auc"] = float(roc_auc_score(y_true, score))
        except Exception:
            out["roc_auc"] = None

    return out


def summarize_by_subject(subject_ids: Iterable[str], y_true: Iterable[int], y_pred: Iterable[int]) -> Dict[str, Any]:
    subject_ids = np.asarray(list(subject_ids), dtype=str)
    y_true = np.asarray(list(y_true))
    y_pred = np.asarray(list(y_pred))
    rows = []
    for subject in sorted(np.unique(subject_ids)):
        mask = subject_ids == subject
        rows.append(
            {
                "subject_id": str(subject),
                "n_samples": int(mask.sum()),
                "accuracy": float(accuracy_score(y_true[mask], y_pred[mask])),
                "f1_macro": float(f1_score(y_true[mask], y_pred[mask], average="macro", zero_division=0)),
            }
        )
    return {"subjects": rows}
