from __future__ import annotations

from tools.demo_delivery.finalize import (
    EXPECTED_EVIDENCE_FILES, FINAL_SENTINELS, content_audits,
    old_authority_immutability, staging_validation,
)


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
    result = staging_validation()
    assert result["status"] == "PASS"
    assert result["g3_f_demo_video_delivery"] == "PASS"
    assert result["g3_f_demo_asset_count"] >= 20
