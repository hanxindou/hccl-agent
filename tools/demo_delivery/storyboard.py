"""G3-F-C evidence-safe storyboard and screen-recording plan."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .common import DELIVERY_ROOT, ROOT, read_json, sha256_file, write_json, write_text


STORYBOARD = DELIVERY_ROOT / "storyboard.json"
ALLOWED_VISUAL_TYPES = {
    "LIVE_TERMINAL", "REGISTERED_FIGURE", "ARCHITECTURE_DIAGRAM",
    "TEXT_CARD", "DEMO_OUTPUT", "REFERENCE_SCREEN_CAPTURE",
}


def _scene(
    scene_id: str, sequence: int, section: str, purpose: str, visual_type: str,
    *, asset: str | None = None, figures: list[str] | None = None,
    demo_steps: list[str] | None = None, badges: list[str], claims: list[str] | None = None,
    metrics: list[str] | None = None, traces: list[str] | None = None,
    innovations: list[str] | None = None, limitations: list[str], forbidden: list[str],
    fallback: str,
) -> dict[str, Any]:
    return {
        "scene_id": scene_id, "sequence": sequence, "section": section, "purpose": purpose,
        "target_duration": "PRODUCTION_BUDGET_PENDING_UA_F_001",
        "visual_type": visual_type, "visual_asset": asset,
        "figure_ref": figures or [], "demo_step_ref": demo_steps or [],
        "screen_action": "present the registered asset or bounded final command summary; do not scroll raw logs",
        "camera_or_crop": "repository-neutral crop; retain figure ID, truth badge, and limitations",
        "overlay_text": badges,
        "truth_badge": badges,
        "narration_ref": f"NARR-{sequence:02d}", "subtitle_ref": f"SUB-{sequence:02d}",
        "claim_refs": claims or [], "metric_refs": metrics or [], "trace_refs": traces or [],
        "innovation_refs": innovations or [],
        "transition": "CUT_WITH_TRUTH_BADGE_RETAINED",
        "limitations": limitations, "forbidden_interpretations": forbidden,
        "fallback_visual": fallback, "recording_status": "PLANNED_NOT_RECORDED",
    }


def _scenes() -> list[dict[str, Any]]:
    return [
        _scene(
            "SCENE-01", 1, "Problem", "Frame the collective-optimization and evidence-delivery problem",
            "TEXT_CARD", badges=["EVIDENCE_SCOPE_DECLARED"], innovations=["INNOV-01"],
            limitations=["project value is bounded by frozen evidence"],
            forbidden=["do not claim SOTA, first, or production hardware validation"], fallback="TEXT-CARD-PROBLEM",
        ),
        _scene(
            "SCENE-02", 2, "System architecture", "Show execution, simulation, Agent, and readiness layers",
            "ARCHITECTURE_DIAGRAM", asset="docs/submission/visualization/assets/diagrams/fig-01-system-execution-and-validation-architecture.svg",
            figures=["FIG-01"], badges=["LAYERED_TRUTH_BOUNDARY"], claims=["C-ABI-001", "C-DIRECT-001"],
            innovations=["INNOV-05"], limitations=["layers have different evidence identities"],
            forbidden=["do not depict every layer as real-device executed"], fallback="FIG-01",
        ),
        _scene(
            "SCENE-03", 3, "Why static selection is insufficient", "Explain schedule/topology-aware choice",
            "ARCHITECTURE_DIAGRAM", asset="docs/submission/visualization/assets/diagrams/fig-02-schedule-ir-and-topology-aware-optimization-pipeline.svg",
            figures=["FIG-02"], badges=["SIMULATED_ONLY"], innovations=["INNOV-02"],
            limitations=["selection evidence uses a frozen analytical simulator"],
            forbidden=["do not present modeled selection as measured device tuning"], fallback="FIG-02",
        ),
        _scene(
            "SCENE-04", 4, "Schedule and topology optimization", "Present the frozen 18/0/0 result and 45.59% simulated improvement",
            "REGISTERED_FIGURE", asset="docs/submission/visualization/assets/charts/fig-04-18-wins-0-ties-0-losses.svg",
            figures=["FIG-03", "FIG-04"], badges=["SIMULATED_ONLY"], claims=["C-PERF-001", "C-PERF-002"],
            metrics=["g3b2.performance.weighted_geomean_improvement_percent", "g3b2.outcomes.wins", "g3b2.outcomes.ties", "g3b2.outcomes.losses"], innovations=["INNOV-02"],
            limitations=["45.59283008% raw / 45.59% display is frozen simulated evidence"],
            forbidden=["do not call this real Ascend performance improvement"], fallback="FIG-04",
        ),
        _scene(
            "SCENE-05", 5, "Agent-assisted decision loop", "Replay proposal, deterministic evaluation, reflection, replanning, and selection",
            "LIVE_TERMINAL", figures=["FIG-08"], demo_steps=["DEMO-AGENT-REPLAY"], badges=["OFFLINE_REPLAY"],
            traces=["g3-b2-optimization-authoritative-round1"], innovations=["INNOV-01"],
            limitations=["replay is not original historical execution", "human governance remains disclosed"],
            forbidden=["do not claim a fully autonomous historical run"], fallback="FALLBACK-AGENT-REPLAY",
        ),
        _scene(
            "SCENE-06", 6, "Frozen simulated evidence", "Show logical scale trends with visible model boundary",
            "REGISTERED_FIGURE", asset="docs/submission/visualization/assets/charts/fig-05-logical-scale-trend.svg",
            figures=["FIG-05"], badges=["SIMULATED_ONLY", "LOGICAL_MODEL_SCALE"], claims=["C-SCALE-001"],
            limitations=["1024 ranks is logical/model scale"],
            forbidden=["do not call logical ranks a 1024-card measured cluster"], fallback="FIG-05",
        ),
        _scene(
            "SCENE-07", 7, "Sparse and reliability", "Separate host sparse/integrity/retry evidence from simulator backpressure",
            "REGISTERED_FIGURE", asset="docs/submission/visualization/assets/charts/fig-07-integrity-retry-and-backpressure-layers.svg",
            figures=["FIG-06", "FIG-07"], badges=["HOST_VALIDATED", "SIMULATED_BACKPRESSURE"],
            claims=["C-SPARSE-001", "C-CRC-001", "C-RETRY-001", "C-BP-001"], innovations=["INNOV-03", "INNOV-04"],
            limitations=["sparse wire bytes are modeled", "backpressure is simulator-only", "no NIC/HCCL hardware reliability validation"],
            forbidden=["do not present modeled bytes as NIC traffic or backpressure as host runtime execution"], fallback="FIG-07",
        ),
        _scene(
            "SCENE-08", 8, "Direct readiness boundary", "Explain the official ACL/HCCL production source path without executing it",
            "ARCHITECTURE_DIAGRAM", asset="docs/submission/visualization/assets/diagrams/fig-10-direct-readiness-validation-ladder.svg",
            figures=["FIG-10"], demo_steps=["DEMO-SUBMISSION-DESCRIBE"],
            badges=["DIRECT_COMPILE_LINK_ONLY", "REAL_DEVICE_NOT_EXECUTED"], claims=["C-DIRECT-001", "C-DIRECT-002"],
            innovations=["INNOV-05"], limitations=["17 official call expressions are compile/link-only readiness", "runtime execution remains absent"],
            forbidden=["do not animate the Direct path as an executed collective"], fallback="FIG-10",
        ),
        _scene(
            "SCENE-09", 9, "Offline reproducibility and live demo", "Execute the project-owned CPU_SIM path and verify figures offline",
            "LIVE_TERMINAL", demo_steps=["DEMO-CPU-SIM", "DEMO-VISUAL-VERIFY"],
            badges=["HOST_VALIDATED", "REAL_DEVICE_NOT_EXECUTED"], claims=["C-ABI-001"], innovations=["INNOV-05"],
            limitations=["CPU_SIM host execution only", "visual verification does not rerun benchmarks"],
            forbidden=["do not label CPU_SIM as Ascend/NPU execution"], fallback="FALLBACK-CPU-SIM",
        ),
        _scene(
            "SCENE-10", 10, "Limitations", "Make all execution and evidence boundaries explicit before the closing claim",
            "ARCHITECTURE_DIAGRAM", asset="docs/submission/visualization/assets/diagrams/fig-12-truth-and-evidence-boundary-matrix.svg",
            figures=["FIG-12"], badges=["REAL_DEVICE_NOT_EXECUTED"], claims=["C-DIRECT-002"],
            limitations=["real-device acceptance remains HARDWARE_BLOCKED", "no ACL/HCCL runtime was executed"],
            forbidden=["do not use a green hardware PASS or imply device acceptance"], fallback="FIG-12",
        ),
        _scene(
            "SCENE-11", 11, "Competition value", "Close with evidence-backed engineering value and reproducibility",
            "REGISTERED_FIGURE", asset="docs/submission/visualization/assets/charts/fig-13-algorithm-and-topology-coverage.svg",
            figures=["FIG-13"], badges=["EVIDENCE_BACKED", "REAL_DEVICE_NOT_EXECUTED"], innovations=["INNOV-01", "INNOV-02", "INNOV-03", "INNOV-04", "INNOV-05"],
            limitations=["competition innovation wording is project-scoped, not a global novelty claim"],
            forbidden=["do not claim industry first, leading, or SOTA"], fallback="FIG-13",
        ),
    ]


def build_storyboard() -> dict[str, Any]:
    scenes = _scenes()
    storyboard = {
        "schema_version": "g3-f-storyboard-v1", "status": "PASS", "recording_status": "PLANNED_NOT_RECORDED",
        "scene_count": len(scenes), "story_order_authority": "docs/submission/visualization/figure_story_map.md",
        "scenes": scenes, "video_binary_created": False, "runtime_api_calls": [],
    }
    write_json(STORYBOARD, storyboard)
    asset_rows = []
    for scene in scenes:
        source = scene["visual_asset"]
        if source:
            path = ROOT / source
            asset_rows.append({
                "scene_id": scene["scene_id"], "asset": source, "sha256": sha256_file(path),
                "figure_refs": scene["figure_ref"], "source": "PROJECT_GENERATED_G3_E_ASSET",
                "license_status": "PROJECT_ASSET_PENDING_UA_B_001", "remote_dependency": False,
            })
        else:
            asset_rows.append({
                "scene_id": scene["scene_id"], "asset": scene["fallback_visual"], "sha256": None,
                "figure_refs": scene["figure_ref"], "source": "DEMO_OR_TEXT_CONTRACT",
                "license_status": "PROJECT_GENERATED", "remote_dependency": False,
            })
    write_json(DELIVERY_ROOT / "scene_asset_map.json", {
        "schema_version": "g3-f-scene-asset-map-v1", "status": "PASS", "assets": asset_rows,
        "external_assets": [], "controlled_logos": [],
    })
    rows = ["# G3-F Storyboard", "", "No screen recording or video binary has been created.", ""]
    for scene in scenes:
        rows.extend([
            f"## {scene['scene_id']} — {scene['section']}", "", scene["purpose"], "",
            f"- Visual: `{scene['visual_type']}` / `{scene['visual_asset'] or scene['demo_step_ref']}`",
            f"- Truth badge: `{', '.join(scene['truth_badge'])}`",
            f"- Fallback: `{scene['fallback_visual']}`",
            f"- Limitations: {'; '.join(scene['limitations'])}", "",
        ])
    write_text(DELIVERY_ROOT / "storyboard.md", "\n".join(rows))
    write_text(DELIVERY_ROOT / "screen_recording_plan.md", """# Screen-Recording Plan

Record only the bounded final outputs named in `demo_manifest.json`. Use a command-local sanitized prompt and a repository-neutral crop. Keep figure IDs, truth badges, and limitations visible. Never show API keys, credentials, personal paths, notifications, browser sessions, private logs, controlled materials, or unrelated desktop content.

The recording specification remains resolution-independent until UA-F-001 is resolved. Use vector-first registered G3-E assets. Do not create or imply an Ascend/NPU execution scene. Every required live scene has a frozen validated fallback that is explicitly labeled as prerecorded output.
""")
    write_text(DELIVERY_ROOT / "recording_privacy_checklist.md", """# Recording Privacy Checklist

- [ ] External API-key variables are absent.
- [ ] No Git/GitHub credentials, email, browser account, notification, or personal filename is visible.
- [ ] No user-specific Windows path or private `/home` path is visible.
- [ ] The prompt is command-local and repository-neutral; global shell configuration is unchanged.
- [ ] Only registered project assets are shown; no controlled logo, private font, or unlicensed media is present.
- [ ] Truth badges, figure IDs, limitations, and final command status remain visible after crop.
- [ ] No screenshot or terminal output has been edited to change a result.
- [ ] Raw logs, temporary files, editor history, and unrelated desktop content are excluded.
""")
    write_text(DELIVERY_ROOT / "recording_fallback_map.md", """# Recording Fallback Map

| Live scene | Fallback | Required identity |
| --- | --- | --- |
| SCENE-05 Agent replay | FALLBACK-AGENT-REPLAY | PRERECORDED_DETERMINISTIC_OUTPUT |
| SCENE-09 CPU_SIM | FALLBACK-CPU-SIM | PRERECORDED_DETERMINISTIC_OUTPUT |
| SCENE-09 figure verification | FALLBACK-VISUAL-VERIFY | FROZEN_VALIDATED_OUTPUT |

Fallbacks retain the same claim refs, truth badges, and limitations. They never impersonate a currently running command.
""")
    return validate_storyboard()


def _ids(path: Path, collection: str, key: str) -> set[str]:
    return {str(row[key]) for row in read_json(path)[collection]}


def validate_storyboard() -> dict[str, Any]:
    errors: list[str] = []
    required = [
        "storyboard.json", "storyboard.md", "screen_recording_plan.md", "scene_asset_map.json",
        "recording_privacy_checklist.md", "recording_fallback_map.md",
    ]
    for name in required:
        if not (DELIVERY_ROOT / name).is_file():
            errors.append(f"missing artifact: {name}")
    if errors:
        return {"schema_version": "g3-f-storyboard-validation-v1", "status": "FAIL", "errors": errors}
    payload = read_json(STORYBOARD)
    scenes = payload.get("scenes", [])
    figures = _ids(ROOT / "docs/submission/visualization/chart_registry.json", "figures", "figure_id")
    claims = _ids(ROOT / "docs/submission/report_claim_ledger.json", "claims", "claim_id")
    metrics = _ids(ROOT / "docs/submission/report_data_ledger.json", "metrics", "metric_id")
    traces = _ids(ROOT / "docs/submission/agent_delivery/trace_index.json", "traces", "trace_id")
    innovations = _ids(ROOT / "docs/submission/visualization/innovation_map.json", "innovations", "innovation_id")
    demo_steps = {row["step_id"] for row in read_json(DELIVERY_ROOT / "demo_manifest.json")["steps"]}
    if [row.get("sequence") for row in scenes] != list(range(1, len(scenes) + 1)):
        errors.append("scene sequence is not contiguous")
    if len({row.get("scene_id") for row in scenes}) != len(scenes):
        errors.append("duplicate scene ID")
    for row in scenes:
        scene_id = row.get("scene_id")
        if row.get("visual_type") not in ALLOWED_VISUAL_TYPES:
            errors.append(f"invalid visual type: {scene_id}")
        for name, values, allowed in (
            ("figure", row.get("figure_ref", []), figures), ("claim", row.get("claim_refs", []), claims),
            ("metric", row.get("metric_refs", []), metrics), ("trace", row.get("trace_refs", []), traces),
            ("innovation", row.get("innovation_refs", []), innovations), ("demo", row.get("demo_step_ref", []), demo_steps),
        ):
            missing = sorted(set(values) - allowed)
            if missing:
                errors.append(f"unresolved {name} refs in {scene_id}: {missing}")
        asset = row.get("visual_asset")
        if asset and not (ROOT / asset).is_file():
            errors.append(f"missing visual asset: {asset}")
        if not row.get("purpose") or not row.get("truth_badge") or not row.get("limitations") or not row.get("forbidden_interpretations"):
            errors.append(f"incomplete truth contract: {scene_id}")
        if not row.get("fallback_visual"):
            errors.append(f"fallback missing: {scene_id}")
    all_badges = {badge for row in scenes for badge in row.get("truth_badge", [])}
    for required_badge in ("SIMULATED_ONLY", "LOGICAL_MODEL_SCALE", "OFFLINE_REPLAY", "DIRECT_COMPILE_LINK_ONLY", "REAL_DEVICE_NOT_EXECUTED"):
        if required_badge not in all_badges:
            errors.append(f"required truth badge missing: {required_badge}")
    canonical = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if STORYBOARD.read_text(encoding="utf-8") != canonical:
        errors.append("storyboard serialization is not canonical")
    secret_patterns = [r"C:\\Users\\", r"/home/[A-Za-z0-9._-]+/", r"ghp_[A-Za-z0-9]+", r"sk-[A-Za-z0-9]+"]
    for path in (DELIVERY_ROOT / name for name in required):
        text = path.read_text(encoding="utf-8", errors="replace")
        if str(ROOT) in text or any(re.search(pattern, text) for pattern in secret_patterns):
            errors.append(f"privacy/path finding: {path.name}")
    return {
        "schema_version": "g3-f-storyboard-validation-v1", "status": "PASS" if not errors else "FAIL",
        "errors": errors, "scene_count": len(scenes), "mapped_asset_count": len(read_json(DELIVERY_ROOT / "scene_asset_map.json")["assets"]),
        "recording_status": payload.get("recording_status"), "privacy_findings": [],
        "video_binary_created": False, "sentinel": "G3_F_STORYBOARD_OK" if not errors else None,
    }
