"""Deterministic, evidence-derived SVG rendering for G3-E-B."""

from __future__ import annotations

import math
import re
from html import escape
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from .authority import TRUTH_IDENTITIES
from .common import CLAIM_LEDGER, DATA_LEDGER, OUTPUT_ROOT, ROOT, load_json, relative, sha256_file, write_json, write_text


ASSET_ROOT = OUTPUT_ROOT / "assets"
MAIN_FIGURES = {"FIG-01", "FIG-02", "FIG-03", "FIG-04", "FIG-06", "FIG-07", "FIG-08", "FIG-10", "FIG-12", "FIG-13"}
SUPPORTING_FIGURES = {"FIG-05", "FIG-09", "FIG-11"}
CHART_FIGURES = {"FIG-03", "FIG-04", "FIG-05", "FIG-06", "FIG-07", "FIG-11", "FIG-13"}
DIAGRAM_STEPS = {
    "FIG-01": ["Competition goal", "Agent / Prompt", "Schedule IR", "CPU_SIM + simulator", "Direct readiness", "Real device: blocked"],
    "FIG-02": ["Topology + workload", "Proposal", "Schedule IR v2", "Selector + cost model", "Deterministic evaluation", "Evidence-backed decision"],
    "FIG-08": ["Human goal / constraints", "Agent proposal", "Deterministic evaluation", "Reflection / replanning", "Human-governed gate", "Frozen evidence mapping"],
    "FIG-09": ["Feature proposal", "Evidence gate", "Implemented", "INT8: deferred", "PairWise: skipped", "Frozen decision record"],
    "FIG-10": ["Official declarations", "17 source call expressions", "Compile + link", "Readiness artifact", "Runtime execution absent", "Real-device acceptance blocked"],
    "FIG-12": ["Host executed", "Simulator modeled", "Direct readiness", "Real device not executed"],
}


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:64]


def _svg_open(title: str, desc: str, truths: list[str]) -> list[str]:
    badge = " · ".join(truths)
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img" aria-labelledby="title desc">',
        f"  <title id=\"title\">{escape(title)}</title>",
        f"  <desc id=\"desc\">{escape(desc)}</desc>",
        "  <defs>",
        "    <style>text{font-family:Arial,'Noto Sans',sans-serif;fill:#152238}.title{font-size:34px;font-weight:700}.sub{font-size:17px;fill:#53657a}.label{font-size:16px}.small{font-size:13px;fill:#53657a}.value{font-size:15px;font-weight:700}.node{fill:#f6f8fb;stroke:#9aabc0;stroke-width:2}.primary{fill:#1769aa}.secondary{fill:#3da58a}.warning{fill:#d9852b}.blocked{fill:#c74c4c}.grid{stroke:#d8e0ea;stroke-width:1}.arrow{stroke:#63768c;stroke-width:2;fill:none}.badge{fill:#e8eef5;stroke:#b9c7d7}.badgeText{font-size:12px;font-weight:700}</style>",
        "    <marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"8\" refY=\"5\" markerWidth=\"7\" markerHeight=\"7\" orient=\"auto-start-reverse\"><path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#63768c\"/></marker>",
        "  </defs>",
        "  <rect width=\"1280\" height=\"720\" fill=\"#ffffff\"/>",
        "  <rect x=\"0\" y=\"0\" width=\"14\" height=\"720\" fill=\"#1769aa\"/>",
        f"  <text class=\"title\" x=\"54\" y=\"64\">{escape(title)}</text>",
        "  <text class=\"sub\" x=\"54\" y=\"94\">Evidence-derived · offline deterministic SVG</text>",
        f"  <rect class=\"badge\" x=\"54\" y=\"112\" width=\"{min(1130, max(230, len(badge) * 8 + 32))}\" height=\"28\" rx=\"14\"/>",
        f"  <text class=\"badgeText\" x=\"70\" y=\"131\">{escape(badge)}</text>",
    ]


def _svg_close(source_label: str) -> list[str]:
    return [
        "  <line class=\"grid\" x1=\"54\" y1=\"665\" x2=\"1226\" y2=\"665\"/>",
        f"  <text class=\"small\" x=\"54\" y=\"691\">Source: {escape(source_label[:145])}</text>",
        "</svg>",
    ]


def _render_flow(title: str, desc: str, truths: list[str], steps: list[str], source_label: str) -> str:
    parts = _svg_open(title, desc, truths)
    if len(steps) <= 4:
        width, gap, x0 = 245, 38, 72
    else:
        width, gap, x0 = 165, 30, 54
    for index, step in enumerate(steps):
        x = x0 + index * (width + gap)
        if index:
            parts.append(f'  <line class="arrow" x1="{x-gap+4}" y1="350" x2="{x-8}" y2="350" marker-end="url(#arrow)"/>')
        klass = "blocked" if "blocked" in step.lower() or "absent" in step.lower() else "node"
        parts.append(f'  <rect class="{klass}" x="{x}" y="280" width="{width}" height="140" rx="14"/>')
        words, lines, line = step.split(), [], ""
        for word in words:
            if len(line) + len(word) + 1 > 20:
                lines.append(line); line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            lines.append(line)
        for row, text in enumerate(lines[:4]):
            fill = "#ffffff" if klass == "blocked" else "#152238"
            parts.append(f'  <text class="label" x="{x + width/2:.1f}" y="{330 + row*24}" text-anchor="middle" fill="{fill}">{escape(text)}</text>')
    parts.extend(_svg_close(source_label))
    return "\n".join(parts) + "\n"


def _short_metric(metric_id: str) -> str:
    bits = metric_id.split(".")
    return (".".join(bits[-2:]) if len(bits) > 2 else metric_id).replace("_", " ")


def _numeric_rows(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for payload in payloads for row in payload.get("series", []) if isinstance(row.get("value"), (int, float)) and not isinstance(row.get("value"), bool)]


def _render_metric_bars(title: str, desc: str, truths: list[str], payloads: list[dict[str, Any]], source_label: str) -> str:
    rows = _numeric_rows(payloads)
    if len(rows) > 14:
        rows = rows[::max(1, len(rows) // 14)][:14]
    parts = _svg_open(title, desc, truths)
    values = [abs(float(row["value"])) for row in rows]
    positive = [value for value in values if value > 0]
    use_log = bool(positive and max(positive) / min(positive) > 100)
    scaled = [(math.log10(value + 1) if use_log else value) for value in values]
    maximum = max(scaled, default=1) or 1
    parts.append(f'  <text class="small" x="930" y="160">Scale: {"log10(value + 1)" if use_log else "linear from zero"}</text>')
    for index, (row, scale) in enumerate(zip(rows, scaled)):
        y = 184 + index * 31
        width = 650 * scale / maximum
        parts.append(f'  <text class="small" x="54" y="{y+18}">{escape(_short_metric(row["metric_id"]))}</text>')
        parts.append(f'  <rect x="310" y="{y+5}" width="650" height="17" fill="#edf1f6" rx="4"/>')
        parts.append(f'  <rect class="primary" x="310" y="{y+5}" width="{max(2, width):.1f}" height="17" rx="4"/>')
        parts.append(f'  <text class="value" x="980" y="{y+19}">{escape(str(row["display_value"]))} {escape(str(row["unit"]))}</text>')
    parts.extend(_svg_close(source_label))
    return "\n".join(parts) + "\n"


def _render_latency(title: str, desc: str, truths: list[str], payload: dict[str, Any], source_label: str) -> str:
    by_id = {row["metric_id"]: row for row in payload["series"]}
    scenarios = sorted({item.split(".")[2] for item in by_id if item.endswith("baseline_p50_us")})
    improvements = []
    for scenario in scenarios:
        baseline = float(by_id[f"g3b2.scenario.{scenario}.baseline_p50_us"]["value"])
        candidate = float(by_id[f"g3b2.scenario.{scenario}.candidate_p50_us"]["value"])
        improvements.append((scenario.upper(), 100.0 * (baseline - candidate) / baseline))
    parts = _svg_open(title, desc, truths)
    parts.append('  <text class="small" x="54" y="170">P50 modeled latency reduction by frozen scenario (%) · zero baseline</text>')
    for index, (scenario, value) in enumerate(improvements):
        x, height = 70 + index * 63, max(2, value * 6.5)
        parts.append(f'  <rect class="secondary" x="{x}" y="{600-height:.1f}" width="38" height="{height:.1f}" rx="3"/>')
        parts.append(f'  <text class="small" x="{x+19}" y="625" text-anchor="middle">{scenario}</text>')
        parts.append(f'  <text class="small" x="{x+19}" y="{590-height:.1f}" text-anchor="middle">{value:.1f}</text>')
    parts.append('  <line class="grid" x1="54" y1="600" x2="1226" y2="600"/>')
    parts.extend(_svg_close(source_label))
    return "\n".join(parts) + "\n"


def _render_outcome(title: str, desc: str, truths: list[str], payload: dict[str, Any], ledger: dict[str, Any], source_label: str) -> str:
    rows = {row["metric_id"]: row for row in payload["series"]}
    scenarios = sorted({item.split(".")[2] for item in rows if item.endswith("baseline_p50_us")})
    wins = sum(float(rows[f"g3b2.scenario.{scenario}.candidate_p50_us"]["value"]) < float(rows[f"g3b2.scenario.{scenario}.baseline_p50_us"]["value"]) for scenario in scenarios)
    ties = sum(float(rows[f"g3b2.scenario.{scenario}.candidate_p50_us"]["value"]) == float(rows[f"g3b2.scenario.{scenario}.baseline_p50_us"]["value"]) for scenario in scenarios)
    losses = len(scenarios) - wins - ties
    weighted = next(row for row in ledger["metrics"] if row["metric_id"].endswith("weighted_geomean_improvement_percent"))
    parts = _svg_open(title, desc, truths)
    for index, (label, value, klass) in enumerate([("WINS", wins, "primary"), ("TIES", ties, "warning"), ("LOSSES", losses, "blocked")]):
        x = 85 + index * 300
        parts.append(f'  <rect class="node" x="{x}" y="235" width="250" height="220" rx="18"/>')
        parts.append(f'  <circle class="{klass}" cx="{x+125}" cy="315" r="44"/>')
        parts.append(f'  <text x="{x+125}" y="329" text-anchor="middle" font-size="38" font-weight="700" fill="#ffffff">{value}</text>')
        parts.append(f'  <text class="label" x="{x+125}" y="400" text-anchor="middle">{label}</text>')
    parts.append('  <rect class="node" x="985" y="235" width="220" height="220" rx="18"/>')
    parts.append(f'  <text x="1095" y="325" text-anchor="middle" font-size="34" font-weight="700">{escape(weighted["display_value"])}%</text>')
    parts.append('  <text class="small" x="1095" y="374" text-anchor="middle">weighted modeled</text>')
    parts.append('  <text class="small" x="1095" y="396" text-anchor="middle">improvement</text>')
    parts.append('  <text class="small" x="640" y="530" text-anchor="middle">Frozen simulated scenarios only · not real Ascend/NPU performance</text>')
    parts.extend(_svg_close(source_label))
    return "\n".join(parts) + "\n"


def _payloads(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    return [load_json(ROOT / source) for source in candidate["data_sources"] if source.startswith("docs/submission/report_chart_data/")]


def _caption(candidate: dict[str, Any], classification: str) -> str:
    return f"{candidate['title']}. {candidate['purpose']} Truth: {', '.join(candidate['truth_identity'])}. Limits: {'; '.join(candidate['limitations'])}. Classification: {classification}."


def build_charts() -> dict[str, Any]:
    candidates = load_json(OUTPUT_ROOT / "chart_candidate_inventory.json")["candidates"]
    ledger = load_json(DATA_LEDGER)
    claim_ids = {row["claim_id"] for row in load_json(CLAIM_LEDGER)["claims"]}
    selected = [row for row in candidates if row["figure_id"] in MAIN_FIGURES | SUPPORTING_FIGURES]
    records: list[dict[str, Any]] = []
    for candidate in selected:
        figure_id = candidate["figure_id"]
        classification = "MAIN" if figure_id in MAIN_FIGURES else "SUPPORTING"
        kind = "charts" if figure_id in CHART_FIGURES else "diagrams"
        path = ASSET_ROOT / kind / f"{figure_id.lower()}-{_slug(candidate['title'])}.svg"
        payloads, source_label = _payloads(candidate), ", ".join(candidate["data_sources"])
        desc = _caption(candidate, classification)
        if figure_id == "FIG-03":
            svg = _render_latency(candidate["title"], desc, candidate["truth_identity"], payloads[0], source_label)
        elif figure_id == "FIG-04":
            svg = _render_outcome(candidate["title"], desc, candidate["truth_identity"], payloads[0], ledger, source_label)
        elif figure_id in DIAGRAM_STEPS:
            svg = _render_flow(candidate["title"], desc, candidate["truth_identity"], DIAGRAM_STEPS[figure_id], source_label)
        else:
            svg = _render_metric_bars(candidate["title"], desc, candidate["truth_identity"], payloads, source_label)
        write_text(path, svg)
        metric_ids = sorted({metric for payload in payloads for metric in payload.get("metric_refs", [])})
        records.append({
            "figure_id": figure_id, "title": candidate["title"], "classification": classification,
            "asset_path": relative(path), "asset_sha256": sha256_file(path), "format": "SVG", "canonical": True,
            "width": 1280, "height": 720, "source_paths": candidate["data_sources"],
            "source_sha256": {source: sha256_file(ROOT / source) for source in candidate["data_sources"]},
            "metric_ids": metric_ids, "claim_refs": candidate["claim_refs"], "truth_identity": candidate["truth_identity"],
            "caption": desc, "alt_text": desc, "limitations": candidate["limitations"],
            "forbidden_interpretations": ["real-device result"] if "REAL_DEVICE_NOT_EXECUTED" in candidate["truth_identity"] else [],
            "all_claim_refs_resolve": all(claim in claim_ids for claim in candidate["claim_refs"]),
        })
    registry = {
        "schema_version": "g3-e-chart-registry-v1", "status": "DETERMINISTIC_SVG_ASSETS_BUILT",
        "renderer": "Python stdlib self-contained SVG", "canonical_format": "SVG",
        "png_policy": "NOT_GENERATED_NO_DETERMINISTIC_DEPENDENCY_REQUIRED", "asset_count": len(records),
        "main_figure_count": sum(row["classification"] == "MAIN" for row in records),
        "supporting_figure_count": sum(row["classification"] == "SUPPORTING" for row in records), "figures": records,
    }
    write_json(OUTPUT_ROOT / "chart_registry.json", registry)
    lines = ["# G3-E Figure Index", "", "All assets are canonical, self-contained, deterministic SVG files derived from frozen authorities.", "", "| ID | Class | Title | Truth identity | Asset |", "|---|---|---|---|---|"]
    for row in records:
        lines.append(f"| {row['figure_id']} | {row['classification']} | {row['title']} | {', '.join(row['truth_identity'])} | `{row['asset_path']}` |")
    write_text(OUTPUT_ROOT / "figure_index.md", "\n".join(lines) + "\n")
    return validate_charts()


def validate_charts() -> dict[str, Any]:
    errors: list[str] = []
    registry = load_json(OUTPUT_ROOT / "chart_registry.json")
    claims = {row["claim_id"] for row in load_json(CLAIM_LEDGER)["claims"]}
    metrics = {row["metric_id"] for row in load_json(DATA_LEDGER)["metrics"]}
    if (registry.get("asset_count"), registry.get("main_figure_count"), registry.get("supporting_figure_count")) != (13, 10, 3):
        errors.append("asset classification/count mismatch")
    hashes: list[str] = []
    for row in registry.get("figures", []):
        path = ROOT / row["asset_path"]
        if not path.is_file():
            errors.append(f"missing asset: {row['figure_id']}"); continue
        if sha256_file(path) != row["asset_sha256"]:
            errors.append(f"asset hash mismatch: {row['figure_id']}")
        hashes.append(sha256_file(path))
        try:
            tags = [element.tag.rsplit("}", 1)[-1] for element in ElementTree.parse(path).getroot().iter()]
            if "title" not in tags or "desc" not in tags:
                errors.append(f"missing accessible text: {row['figure_id']}")
        except ElementTree.ParseError as exc:
            errors.append(f"invalid SVG: {row['figure_id']} {exc}")
        text = path.read_text(encoding="utf-8")
        external_check = text.replace("http://www.w3.org/2000/svg", "")
        if "http://" in external_check or "https://" in external_check:
            errors.append(f"external asset reference: {row['figure_id']}")
        if not set(row.get("claim_refs", ())) <= claims:
            errors.append(f"unknown claim mapping: {row['figure_id']}")
        if not set(row.get("metric_ids", ())) <= metrics:
            errors.append(f"unknown metric mapping: {row['figure_id']}")
        if not set(row.get("truth_identity", ())) <= set(TRUTH_IDENTITIES):
            errors.append(f"unknown truth identity: {row['figure_id']}")
        for source, digest in row.get("source_sha256", {}).items():
            if not (ROOT / source).is_file() or sha256_file(ROOT / source) != digest:
                errors.append(f"source hash mismatch: {row['figure_id']} {source}")
    return {
        "schema_version": "g3-e-chart-suite-validation-v1", "status": "PASS" if not errors else "FAIL", "errors": errors,
        "asset_count": registry.get("asset_count"), "main_figure_count": registry.get("main_figure_count"),
        "supporting_figure_count": registry.get("supporting_figure_count"), "unique_asset_hash_count": len(set(hashes)),
        "canonical_format": registry.get("canonical_format"), "png_generated": False, "network_access": False,
        "benchmark_rerun": False, "runtime_api_calls": [], "sentinel": "G3_E_CHART_SUITE_OK" if not errors else None,
    }
