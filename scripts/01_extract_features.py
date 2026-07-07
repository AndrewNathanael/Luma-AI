#!/usr/bin/env python
"""Extract rPPG and PRV/HRV features from manifest videos."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from rppg_stress.dataset import process_manifest_to_features
from rppg_stress.utils import ensure_parent, load_config, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="CSV with subject_id, video_path, condition")
    parser.add_argument("--output", required=True, help="Output feature CSV")
    parser.add_argument("--config", default="config/default.yaml", help="YAML config path")
    parser.add_argument("--strict", action="store_true", help="Stop at first failed video")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    features = process_manifest_to_features(args.manifest, config=config, strict=args.strict)

    out_path = ensure_parent(args.output)
    features.to_csv(out_path, index=False)
    print(f"Wrote features: {out_path} shape={features.shape}")

    errors = features.attrs.get("errors", [])
    if errors:
        err_path = Path(str(out_path) + ".errors.json")
        save_json({"errors": errors}, err_path)
        print(f"Some videos failed. Error log: {err_path}")


if __name__ == "__main__":
    main()
