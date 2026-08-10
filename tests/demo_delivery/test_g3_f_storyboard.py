from __future__ import annotations

from tools.demo_delivery.common import DELIVERY_ROOT, read_json
from tools.demo_delivery.storyboard import ALLOWED_VISUAL_TYPES, validate_storyboard


def test_storyboard_scene_and_reference_contract_passes() -> None:
    result = validate_storyboard()
    assert result["status"] == "PASS", result["errors"]
    assert result["sentinel"] == "G3_F_STORYBOARD_OK"
    assert result["scene_count"] == result["mapped_asset_count"] == 11
    assert result["recording_status"] == "PLANNED_NOT_RECORDED"
    assert result["video_binary_created"] is False


def test_risky_scenes_keep_visible_truth_badges_and_fallbacks() -> None:
    scenes = read_json(DELIVERY_ROOT / "storyboard.json")["scenes"]
    assert all(row["visual_type"] in ALLOWED_VISUAL_TYPES for row in scenes)
    assert all(row["truth_badge"] for row in scenes)
    assert all(row["limitations"] for row in scenes)
    assert all(row["forbidden_interpretations"] for row in scenes)
    assert all(row["fallback_visual"] for row in scenes)
    badges = {badge for row in scenes for badge in row["truth_badge"]}
    assert {
        "SIMULATED_ONLY", "LOGICAL_MODEL_SCALE", "OFFLINE_REPLAY",
        "DIRECT_COMPILE_LINK_ONLY", "REAL_DEVICE_NOT_EXECUTED",
    } <= badges


def test_privacy_and_recording_files_do_not_claim_media_exists() -> None:
    storyboard = read_json(DELIVERY_ROOT / "storyboard.json")
    assert storyboard["recording_status"] == "PLANNED_NOT_RECORDED"
    assert storyboard["video_binary_created"] is False
    privacy = (DELIVERY_ROOT / "recording_privacy_checklist.md").read_text(encoding="utf-8")
    assert "API-key" in privacy
    assert "user-specific Windows path" in privacy
    assert "edited to change a result" in privacy
    assert not list(DELIVERY_ROOT.rglob("*.mp4"))
    assert not list(DELIVERY_ROOT.rglob("*.mov"))
