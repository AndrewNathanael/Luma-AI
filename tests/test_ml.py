from __future__ import annotations

import numpy as np
import pandas as pd

from rppg_stress.ml import (
    evaluate_loso_from_feature_table,
    make_subject_independent_splits,
    model_feature_columns,
    random_forest_feature_importance,
    train_from_feature_table,
)


def _feature_table(n_subjects: int = 6) -> pd.DataFrame:
    rows = []
    for subject_idx in range(n_subjects):
        subject_id = f"s{subject_idx + 1}"
        for label in (0, 1):
            rows.append(
                {
                    "subject_id": subject_id,
                    "video_path": f"{subject_id}_{label}.avi",
                    "condition": "rest" if label == 0 else "speech",
                    "label": label,
                    "mean_hr_bpm": 60.0 + label * 10.0 + subject_idx,
                    "rmssd_ms": 40.0 - label * 5.0 + subject_idx,
                    "snr_proxy": 0.8,
                }
            )
    return pd.DataFrame(rows)


def test_subject_independent_splits_have_no_subject_overlap():
    df = _feature_table()
    groups = df["subject_id"].to_numpy()

    split = make_subject_independent_splits(groups, validation_size=0.2, test_size=0.2, random_state=7)

    subject_sets = [
        set(groups[split["train"]]),
        set(groups[split["validation"]]),
        set(groups[split["test"]]),
    ]
    assert subject_sets[0].isdisjoint(subject_sets[1])
    assert subject_sets[0].isdisjoint(subject_sets[2])
    assert subject_sets[1].isdisjoint(subject_sets[2])


def test_train_exports_random_forest_importance():
    df = _feature_table()
    config = {
        "training": {
            "model": "random_forest",
            "validation": "subject_split",
            "validation_size": 0.2,
            "test_size": 0.2,
            "random_state": 3,
        }
    }

    bundle, metrics = train_from_feature_table(df, config)
    importance = random_forest_feature_importance(bundle)

    assert metrics["test_metrics"]["n_samples"] == metrics["n_test_samples"]
    assert set(metrics["train_subjects"]).isdisjoint(metrics["test_subjects"])
    assert importance["importance"].notna().all()
    assert importance["rank"].tolist() == list(np.arange(1, len(importance) + 1))


def test_loso_evaluation_reports_one_fold_per_subject():
    df = _feature_table(n_subjects=4)
    config = {"training": {"model": "random_forest", "random_state": 5}}

    metrics = evaluate_loso_from_feature_table(df, config)

    assert metrics["validation"] == "loso"
    assert metrics["n_subjects"] == 4
    assert len(metrics["folds"]) == 4


def test_model_feature_columns_excludes_configured_features():
    df = _feature_table(n_subjects=4)
    config = {"training": {"exclude_features": ["snr_proxy"]}}

    cols = model_feature_columns(df, config)

    assert "snr_proxy" not in cols
    assert "mean_hr_bpm" in cols
