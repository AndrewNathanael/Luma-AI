from __future__ import annotations

from rppg_stress.dataset import make_manifest_from_directory, make_ubfc_phys_manifest


def test_make_ubfc_phys_manifest_detects_subject_tasks(tmp_path):
    subject_dir = tmp_path / "s1"
    subject_dir.mkdir()
    for task in ("T1", "T2", "T3"):
        (subject_dir / f"vid_s1_{task}.avi").write_bytes(b"")

    manifest = make_ubfc_phys_manifest(tmp_path)

    assert manifest["subject_id"].tolist() == ["s1", "s1", "s1"]
    assert manifest["task"].tolist() == ["T1", "T2", "T3"]
    assert manifest["condition"].tolist() == ["rest", "speech", "arithmetic"]


def test_make_manifest_auto_detects_ubfc_phys(tmp_path):
    subject_dir = tmp_path / "s2"
    subject_dir.mkdir()
    (subject_dir / "vid_s2_T1.avi").write_bytes(b"")

    output = tmp_path / "manifest.csv"
    manifest = make_manifest_from_directory(tmp_path, output, dataset="auto")

    assert output.exists()
    assert manifest.loc[0, "subject_id"] == "s2"
    assert manifest.loc[0, "condition"] == "rest"
    assert manifest.attrs["missing_videos"]
