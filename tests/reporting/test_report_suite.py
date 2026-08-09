from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

import pytest

from tools.reporting.evidence_reader import CHART_ROOT, REPORT_ROOT, ROOT, read_json
from tools.reporting.report_verifier import verify_all
from tools.reporting.schemas import CHART_FILES, REPORT_FILES, REPORT_REQUIRED_HEADINGS


FORMAL_REPORTS = tuple(name for name in REPORT_FILES if name[:2].isdigit())


@pytest.mark.parametrize("filename", REPORT_FILES)
def test_report_file_exists(filename: str) -> None:
    assert (REPORT_ROOT / filename).is_file()


@pytest.mark.parametrize("filename", FORMAL_REPORTS)
def test_formal_report_has_uniform_contract(filename: str) -> None:
    text = (REPORT_ROOT / filename).read_text(encoding="utf-8")
    assert "Report Status: `FINAL_EVIDENCE_DERIVED`" in text
    assert "Real-device Validated: `false`" in text
    assert "Runtime API Executed: `false`" in text
    assert all(heading in text for heading in REPORT_REQUIRED_HEADINGS)


@pytest.mark.parametrize("filename", CHART_FILES)
def test_chart_data_is_ledger_derived(filename: str) -> None:
    payload = read_json(CHART_ROOT / filename)
    assert payload["schema_version"] == "g3-c-chart-data-v1"
    assert payload["derived_from"] == "docs/submission/report_data_ledger.json"
    assert payload["truth_label"]


def test_report_verifier_passes() -> None:
    result = verify_all(persist=False)
    assert result["status"] == "PASS"
    assert result["frozen_evidence_changes"] == []
    assert result["real_device_api_executed"] is False
    assert result["runtime_api_calls"] == []


def test_report_numeric_markers_reference_ledger() -> None:
    ledger_ids = {row["metric_id"] for row in read_json(ROOT / "docs/submission/report_data_ledger.json")["metrics"]}
    markers: set[str] = set()
    for filename in FORMAL_REPORTS:
        markers.update(re.findall(r"<!-- metric:([^ ]+) -->", (REPORT_ROOT / filename).read_text(encoding="utf-8")))
    assert markers
    assert markers <= ledger_ids


def test_all_markdown_links_are_relative_and_resolve() -> None:
    for report in REPORT_ROOT.glob("*.md"):
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", report.read_text(encoding="utf-8")):
            pure = PurePosixPath(target)
            assert not pure.is_absolute()
            assert (report.parent / Path(*pure.parts)).resolve().is_file(), (report.name, target)


def test_report_suite_has_no_private_absolute_paths() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in REPORT_ROOT.glob("*.md"))
    assert "C:\\Users\\" not in text
    assert "/home/" not in text
    assert "/mnt/" not in text


def test_performance_claim_keeps_simulator_identity() -> None:
    text = (REPORT_ROOT / "06_simulator_performance_and_scale_report.md").read_text(encoding="utf-8")
    assert "45.59283008" in text
    assert "SIMULATED_ONLY" in text
    assert "1024 logical ranks" in text
    assert "physical devices" in text


def test_direct_report_keeps_compile_link_boundary() -> None:
    text = (REPORT_ROOT / "10_direct_compile_link_readiness_appendix.md").read_text(encoding="utf-8")
    assert "DIRECT_COMPILE_LINK_ONLY" in text
    assert "actual call expression present != runtime API executed" in text
    assert "runtime_api_calls=[]" in text


def test_sparse_report_separates_modeled_wire_from_measurement() -> None:
    text = (REPORT_ROOT / "05_sparse_communication_and_wire_accounting_report.md").read_text(encoding="utf-8")
    assert "modeled_wire_bytes != physically measured NIC bytes" in text
    assert "dense fallback" in text.lower()
