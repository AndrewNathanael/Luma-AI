#!/usr/bin/env python
"""Create a starter manifest CSV by scanning a video directory."""

from __future__ import annotations

import argparse

from rppg_stress.dataset import make_manifest_from_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Root folder containing videos")
    parser.add_argument("--output", required=True, help="Output manifest CSV")
    parser.add_argument("--pattern", default="*.mp4", help="Glob pattern, e.g. '*.mp4' or '*.avi'")
    parser.add_argument(
        "--dataset",
        default="auto",
        choices=["auto", "generic", "ubfc_phys"],
        help="Manifest discovery mode. auto detects UBFC-Phys when possible.",
    )
    parser.add_argument("--strict", action="store_true", help="Fail if UBFC-Phys task videos are missing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = make_manifest_from_directory(
        args.root,
        args.output,
        pattern=args.pattern,
        dataset=args.dataset,
        strict=args.strict,
    )
    print(f"Wrote manifest with {len(df)} rows to {args.output}")
    missing = df.attrs.get("missing_videos", [])
    if missing:
        print(f"Warning: {len(missing)} expected UBFC-Phys task videos were missing.")
    print("Review condition labels before training.")


if __name__ == "__main__":
    main()
