from __future__ import annotations

import shutil
from pathlib import Path

from tools.submission_cli import core as submission_core
from tools.demo_delivery.finalize import (
    EXPECTED_EVIDENCE_FILES, FINAL_SENTINELS, build_staging, content_audits,
    old_authority_immutability, staging_validation,
)


def _remove_test_owned_generated_path(path: Path) -> None:
    if not path.exists():
        return
    submission_core._assert_generated_target(path)
    marker = path / submission_core.MARKER
    if not marker.is_file():
        raise AssertionError(f"refusing to remove unmarked generated path: {path}")
    shutil.rmtree(path)


def _clean_staging_integration_outputs() -> None:
    for path in (
        submission_core.DEFAULT_STAGE,
        submission_core.INSTALL_ROOT / "quick",
        submission_core.BUILD_ROOT / "quick",
    ):
        _remove_test_owned_generated_path(path)


def test_old_authority_is_unchanged_from_origin_main() -> None:
    result = old_authority_immutability()
    assert result["status"] == "PASS", result["errors"]
    assert result["old_authority_modified"] is False
    assert result["files_checked"] > 50
    assert all(row["status"] == "PASS" for row in result["frozen_evidence_roots"].values())


def test_demo_assets_are_portable_private_and_secret_free() -> None:
    asset, privacy, secret = content_audits()
    assert asset["status"] == "PASS", asset["findings"]
    assert privacy["status"] == "PASS", privacy["findings"]
    assert secret["status"] == "PASS", secret["findings"]
    assert asset["reference_video_created"] is False


def test_final_evidence_contract_and_sentinels_are_complete() -> None:
    assert len(EXPECTED_EVIDENCE_FILES) == len(set(EXPECTED_EVIDENCE_FILES))
    assert EXPECTED_EVIDENCE_FILES[-1] == "SHA256SUMS"
    assert FINAL_SENTINELS[-1] == "G3_F_COMPETITION_DEMO_VIDEO_OK"
    assert {
        "G3_F_DEMO_AUTHORITY_OK", "G3_F_OFFLINE_DEMO_OK", "G3_F_DEMO_FALLBACK_OK",
        "G3_F_STORYBOARD_OK", "G3_F_NARRATION_OK", "G3_F_SUBTITLE_SOURCE_OK",
        "G3_F_PRESENTATION_FLOW_OK", "G3_F_CLAIM_BOUNDARIES_OK", "G3_F_PRIVACY_OK",
        "G3_F_ASSET_PORTABILITY_OK", "G3_F_STAGING_OK", "G3_F_COMPETITION_DEMO_VIDEO_OK",
    } == set(FINAL_SENTINELS)


def test_existing_staging_covers_g3_f_after_stage_is_built() -> None:
    _clean_staging_integration_outputs()
    assert not submission_core.DEFAULT_STAGE.exists()
    assert not (submission_core.INSTALL_ROOT / "quick").exists()
    assert not (submission_core.BUILD_ROOT / "quick").exists()
    try:
        quick_args = submission_core.build_parser().parse_args(["quick"])
        quick = submission_core.quick_command(quick_args, persist=False)
        assert quick["status"] == "PASS"
        assert quick["expensive_simulator_evidence_regenerated"] is False
        assert quick["real_device_api_executed"] is False
        assert quick["runtime_api_calls"] == []

        built = build_staging()
        assert built["status"] == "PASS"

        result = staging_validation()
        assert result["status"] == "PASS"
        assert result["g3_f_demo_video_delivery"] == "PASS"
        assert result["g3_f_demo_asset_count"] >= 20
    finally:
        _clean_staging_integration_outputs()
