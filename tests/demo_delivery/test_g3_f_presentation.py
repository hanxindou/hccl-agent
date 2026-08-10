from __future__ import annotations

from tools.demo_delivery.common import DELIVERY_ROOT, read_json
from tools.demo_delivery.presentation import validate_presentation


def test_narration_subtitle_and_flow_contracts_pass() -> None:
    result = validate_presentation()
    assert result["status"] == "PASS", result["errors"]
    assert result["narration_count"] == result["subtitle_count"] == 11
    assert result["flow_profiles"] == ["SHORT", "STANDARD", "TECHNICAL"]
    assert result["sentinels"] == [
        "G3_F_NARRATION_OK", "G3_F_SUBTITLE_SOURCE_OK", "G3_F_PRESENTATION_FLOW_OK",
    ]


def test_high_risk_narration_retains_claim_boundaries() -> None:
    rows = {row["scene_id"]: row for row in read_json(DELIVERY_ROOT / "narration_source.json")["segments"]}
    assert "frozen simulated benchmark" in rows["SCENE-04"]["text_or_localization_source"]
    assert "not a real Ascend/NPU measurement" in rows["SCENE-04"]["text_or_localization_source"]
    assert "logical model-scale" in rows["SCENE-06"]["text_or_localization_source"]
    assert "compile/link-only" in rows["SCENE-08"]["text_or_localization_source"]
    assert "No ACL/HCCL runtime" in rows["SCENE-08"]["text_or_localization_source"]
    assert "not presented as original historical" in rows["SCENE-05"]["text_or_localization_source"]


def test_localization_timeline_voice_and_ppt_remain_unresolved() -> None:
    narration = read_json(DELIVERY_ROOT / "narration_source.json")
    subtitles = read_json(DELIVERY_ROOT / "subtitle_source.json")
    presentation = read_json(DELIVERY_ROOT / "presentation_flow.json")
    localization = read_json(DELIVERY_ROOT / "localization_status.json")
    assert narration["language_status"] == "USER_ACTION_REQUIRED"
    assert narration["voiceover_created"] is False
    assert subtitles["timeline_status"] == "ANCHORS_ONLY_PENDING_UA_F_001"
    assert subtitles["srt_vtt_created"] is False
    assert presentation["ppt_created"] is False
    assert localization["audio_created"] is False
    assert not list(DELIVERY_ROOT.rglob("*.srt"))
    assert not list(DELIVERY_ROOT.rglob("*.vtt"))
    assert not list(DELIVERY_ROOT.rglob("*.mp3"))


def test_truth_badges_are_on_screen_not_narration_only() -> None:
    registry = read_json(DELIVERY_ROOT / "on_screen_truth_badges.json")
    assert registry["narration_only_mitigation_allowed"] is False
    assert {row["badge_id"] for row in registry["badges"]} == {
        "SIMULATED_ONLY", "HOST_VALIDATED", "LOGICAL_MODEL_SCALE",
        "DIRECT_COMPILE_LINK_ONLY", "REAL_DEVICE_NOT_EXECUTED", "OFFLINE_REPLAY",
    }
