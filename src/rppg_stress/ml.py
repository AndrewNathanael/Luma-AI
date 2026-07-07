"""Machine-learning utilities for stress classification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit, LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .evaluation import classification_metrics, summarize_by_subject
from .features import feature_columns
from .utils import deep_get, ensure_parent


@dataclass
class ModelBundle:
    model: Pipeline
    feature_columns: list[str]
    model_name: str
    labels: list[int]


def build_classifier(model_name: str, random_state: int = 42) -> Pipeline:
    """Build sklearn pipeline with imputation, scaling, and classifier."""
    model_name = model_name.lower().strip()
    if model_name == "logistic_regression":
        clf = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=random_state)
    elif model_name == "svm":
        clf = SVC(kernel="rbf", class_weight="balanced", probability=True, random_state=random_state)
    elif model_name == "random_forest":
        clf = RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=random_state,
            n_jobs=-1,
        )
    else:
        raise ValueError("model must be logistic_regression, svm, or random_forest")

    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", clf),
        ]
    )


def train_from_feature_table(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[ModelBundle, Dict[str, Any]]:
    """Train classifier using subject-independent split or LOSO validation."""
    df = df.copy()
    df = df.dropna(axis=0, subset=["label", "subject_id"])
    cols = model_feature_columns(df, config)
    if not cols:
        raise ValueError("No numeric feature columns found for training")

    X = df[cols]
    y = df["label"].astype(int).to_numpy()
    groups = df["subject_id"].astype(str).to_numpy()

    model_name = str(deep_get(config, "training.model", "random_forest"))
    validation = str(deep_get(config, "training.validation", "subject_split")).lower().strip()
    random_state = int(deep_get(config, "training.random_state", 42))
    model = build_classifier(model_name, random_state=random_state)

    metrics: Dict[str, Any]
    if validation == "loso":
        metrics = leave_one_subject_out_validation(model, X, y, groups)
        # Fit final model on all data after CV estimates.
        model.fit(X, y)
    elif validation == "subject_split":
        test_size = float(deep_get(config, "training.test_size", 0.2))
        validation_size = float(deep_get(config, "training.validation_size", 0.2))
        model, metrics = _subject_split_validation(
            model=model,
            X=X,
            y=y,
            groups=groups,
            validation_size=validation_size,
            test_size=test_size,
            random_state=random_state,
        )
    else:
        raise ValueError("training.validation must be subject_split or loso")

    bundle = ModelBundle(
        model=model,
        feature_columns=cols,
        model_name=model_name,
        labels=sorted(np.unique(y).astype(int).tolist()),
    )
    metrics["feature_columns"] = cols
    metrics["excluded_features"] = configured_excluded_features(config)
    metrics["model_name"] = model_name
    metrics["validation"] = validation
    return bundle, metrics


def configured_excluded_features(config: Dict[str, Any]) -> list[str]:
    """Return configured model-input exclusions as normalized column names."""
    values = deep_get(config, "training.exclude_features", []) or []
    if isinstance(values, str):
        values = [values]
    return sorted({str(value).strip() for value in values if str(value).strip()})


def model_feature_columns(df: pd.DataFrame, config: Dict[str, Any]) -> list[str]:
    """Return model features after applying configured exclusions."""
    excluded = set(configured_excluded_features(config))
    return [column for column in feature_columns(df) if column not in excluded]


def _subject_split_validation(
    model: Pipeline,
    X: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    validation_size: float,
    test_size: float,
    random_state: int,
) -> Tuple[Pipeline, Dict[str, Any]]:
    split = make_subject_independent_splits(
        groups=groups,
        validation_size=validation_size,
        test_size=test_size,
        random_state=random_state,
    )
    train_idx = split["train"]
    validation_idx = split["validation"]
    test_idx = split["test"]

    validation_model = clone(model)
    validation_model.fit(X.iloc[train_idx], y[train_idx])
    validation_pred = validation_model.predict(X.iloc[validation_idx])
    validation_score = _predict_score(validation_model, X.iloc[validation_idx])
    validation_metrics = classification_metrics(y[validation_idx], validation_pred, validation_score)
    validation_metrics.update(summarize_by_subject(groups[validation_idx], y[validation_idx], validation_pred))

    final_train_idx = np.concatenate([train_idx, validation_idx])
    final_model = clone(model)
    final_model.fit(X.iloc[final_train_idx], y[final_train_idx])
    test_pred = final_model.predict(X.iloc[test_idx])
    test_score = _predict_score(final_model, X.iloc[test_idx])
    test_metrics = classification_metrics(y[test_idx], test_pred, test_score)
    test_metrics.update(summarize_by_subject(groups[test_idx], y[test_idx], test_pred))

    split_summary = _split_summary(groups, train_idx, validation_idx, test_idx)
    metrics: Dict[str, Any] = {
        "split": split_summary,
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "accuracy": test_metrics.get("accuracy"),
        "f1_macro": test_metrics.get("f1_macro"),
        "precision_macro": test_metrics.get("precision_macro"),
        "recall_macro": test_metrics.get("recall_macro"),
    }
    metrics.update(split_summary)
    return final_model, metrics


def make_subject_independent_splits(
    groups: np.ndarray,
    validation_size: float = 0.2,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Dict[str, np.ndarray]:
    """Return row indices for subject-disjoint train, validation, and test sets."""
    groups = np.asarray(groups, dtype=str)
    unique_subjects = np.unique(groups)
    if len(unique_subjects) < 3:
        raise ValueError("Subject-independent train/validation/test split requires at least 3 subjects")
    if not 0.0 < test_size < 1.0:
        raise ValueError("test_size must be between 0 and 1")
    if not 0.0 < validation_size < 1.0:
        raise ValueError("validation_size must be between 0 and 1")
    if validation_size + test_size >= 1.0:
        raise ValueError("validation_size + test_size must be less than 1")

    row_positions = np.arange(len(groups))
    test_splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_validation_idx, test_idx = next(test_splitter.split(row_positions, groups=groups))

    relative_validation_size = validation_size / (1.0 - test_size)
    validation_splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=relative_validation_size,
        random_state=random_state + 1,
    )
    train_local_idx, validation_local_idx = next(
        validation_splitter.split(
            row_positions[train_validation_idx],
            groups=groups[train_validation_idx],
        )
    )
    train_idx = train_validation_idx[train_local_idx]
    validation_idx = train_validation_idx[validation_local_idx]
    _validate_disjoint_subjects(groups, train_idx, validation_idx, test_idx)
    return {
        "train": np.sort(train_idx),
        "validation": np.sort(validation_idx),
        "test": np.sort(test_idx),
    }


def leave_one_subject_out_validation(
    model: Pipeline,
    X: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
) -> Dict[str, Any]:
    """Evaluate a model with Leave-One-Subject-Out cross-validation."""
    logo = LeaveOneGroupOut()
    y_pred = np.empty_like(y, dtype=int)
    folds = []

    for fold_idx, (train_idx, test_idx) in enumerate(logo.split(X, y, groups=groups), start=1):
        fold_model = clone(model)
        fold_model.fit(X.iloc[train_idx], y[train_idx])
        fold_pred = fold_model.predict(X.iloc[test_idx]).astype(int)
        y_pred[test_idx] = fold_pred
        fold_metrics = classification_metrics(y[test_idx], fold_pred)
        left_out_subject = str(np.unique(groups[test_idx])[0])
        folds.append(
            {
                "fold": int(fold_idx),
                "left_out_subject": left_out_subject,
                "train_subjects": sorted(np.unique(groups[train_idx]).tolist()),
                "n_train_samples": int(len(train_idx)),
                "n_test_samples": int(len(test_idx)),
                "metrics": fold_metrics,
            }
        )

    metrics = classification_metrics(y, y_pred)
    metrics.update(summarize_by_subject(groups, y, y_pred))
    metrics["folds"] = folds
    metrics["n_subjects"] = int(len(np.unique(groups)))
    return metrics


def evaluate_loso_from_feature_table(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Run Leave-One-Subject-Out evaluation directly from a feature table."""
    df = df.copy()
    df = df.dropna(axis=0, subset=["label", "subject_id"])
    cols = model_feature_columns(df, config)
    if not cols:
        raise ValueError("No numeric feature columns found for LOSO evaluation")

    X = df[cols]
    y = df["label"].astype(int).to_numpy()
    groups = df["subject_id"].astype(str).to_numpy()
    model_name = str(deep_get(config, "training.model", "random_forest"))
    random_state = int(deep_get(config, "training.random_state", 42))
    model = build_classifier(model_name, random_state=random_state)
    metrics = leave_one_subject_out_validation(model, X, y, groups)
    metrics["feature_columns"] = cols
    metrics["excluded_features"] = configured_excluded_features(config)
    metrics["model_name"] = model_name
    metrics["validation"] = "loso"
    return metrics


def _split_summary(
    groups: np.ndarray,
    train_idx: np.ndarray,
    validation_idx: np.ndarray,
    test_idx: np.ndarray,
) -> Dict[str, Any]:
    train_subjects = sorted(np.unique(groups[train_idx]).tolist())
    validation_subjects = sorted(np.unique(groups[validation_idx]).tolist())
    test_subjects = sorted(np.unique(groups[test_idx]).tolist())
    return {
        "train_subjects": train_subjects,
        "validation_subjects": validation_subjects,
        "test_subjects": test_subjects,
        "n_train_samples": int(len(train_idx)),
        "n_validation_samples": int(len(validation_idx)),
        "n_test_samples": int(len(test_idx)),
        "n_train_subjects": int(len(train_subjects)),
        "n_validation_subjects": int(len(validation_subjects)),
        "n_test_subjects": int(len(test_subjects)),
        "n_final_train_samples": int(len(train_idx) + len(validation_idx)),
    }


def _validate_disjoint_subjects(
    groups: np.ndarray,
    train_idx: np.ndarray,
    validation_idx: np.ndarray,
    test_idx: np.ndarray,
) -> None:
    train_subjects = set(groups[train_idx])
    validation_subjects = set(groups[validation_idx])
    test_subjects = set(groups[test_idx])
    if train_subjects & validation_subjects or train_subjects & test_subjects or validation_subjects & test_subjects:
        raise RuntimeError("Subject split leaked subjects across train, validation, and test sets")


def _predict_score(model: Pipeline, X: pd.DataFrame) -> np.ndarray | None:
    try:
        if hasattr(model, "predict_proba"):
            return model.predict_proba(X)
        if hasattr(model, "decision_function"):
            return model.decision_function(X)
    except Exception:
        return None
    return None


def save_model_bundle(bundle: ModelBundle, path: str) -> None:
    path = ensure_parent(path)
    joblib.dump(
        {
            "model": bundle.model,
            "feature_columns": bundle.feature_columns,
            "model_name": bundle.model_name,
            "labels": bundle.labels,
        },
        path,
    )


def load_model_bundle(path: str) -> ModelBundle:
    data = joblib.load(path)
    return ModelBundle(
        model=data["model"],
        feature_columns=list(data["feature_columns"]),
        model_name=str(data.get("model_name", "unknown")),
        labels=list(data.get("labels", [])),
    )


def predict_from_features(bundle: ModelBundle, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray | None]:
    missing = [c for c in bundle.feature_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Feature table is missing columns required by model: {missing}")
    X = df[bundle.feature_columns]
    y_pred = bundle.model.predict(X)
    y_score = _predict_score(bundle.model, X)
    return y_pred, y_score


def random_forest_feature_importance(bundle: ModelBundle) -> pd.DataFrame:
    """Return sorted feature importances for a fitted Random Forest bundle."""
    classifier = bundle.model.named_steps.get("classifier")
    if not isinstance(classifier, RandomForestClassifier):
        raise ValueError("Feature importance export is only available for random_forest models")
    if not hasattr(classifier, "feature_importances_"):
        raise ValueError("Random Forest model is not fitted")

    importance = np.asarray(classifier.feature_importances_, dtype=float)
    if len(importance) != len(bundle.feature_columns):
        raise ValueError("Feature importance length does not match feature columns")
    out = pd.DataFrame(
        {
            "feature": bundle.feature_columns,
            "importance": importance,
        }
    )
    total = float(out["importance"].sum())
    out["importance_normalized"] = out["importance"] / total if total > 0 else 0.0
    out = out.sort_values("importance", ascending=False).reset_index(drop=True)
    out.insert(0, "rank", np.arange(1, len(out) + 1))
    return out


def save_random_forest_feature_importance(bundle: ModelBundle, path: str | Path) -> pd.DataFrame:
    """Save Random Forest feature importances to CSV and return the table."""
    out = random_forest_feature_importance(bundle)
    path = ensure_parent(path)
    out.to_csv(path, index=False)
    return out
