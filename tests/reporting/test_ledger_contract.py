from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.reporting.evidence_reader import (
    DATA_LEDGER,
    G3_B2_ROOT,
    G3_B3_ROOT,
    ROOT,
    read_json,
    resolve_pointer,
    sha256,
    verify_sha256sums,
)
from tools.reporting.schemas import METRIC_FIELDS, PROHIBITED_TRUTH_LABELS, TRUTH_LABELS


@pytest.fixture(scope="module")
def ledger() -> dict:
    return read_json(DATA_LEDGER)


@pytest.fixture(scope="module")
def metrics(ledger: dict) -> dict[str, dict]:
    return {row["metric_id"]: row for row in ledger["metrics"]}


def test_ledger_schema_and_count(ledger: dict) -> None:
    assert ledger["schema_version"] == "g3-c-report-data-ledger-v1"
    assert ledger["metric_count"] == len(ledger["metrics"])
    assert ledger["metric_count"] >= 57


def test_metric_ids_are_unique(ledger: dict) -> None:
    ids = [row["metric_id"] for row in ledger["metrics"]]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("field", METRIC_FIELDS)
def test_every_metric_has_required_field(ledger: dict, field: str) -> None:
    assert all(field in row for row in ledger["metrics"]), field


def test_metric_truth_labels_are_allowlisted(ledger: dict) -> None:
    labels = {row["truth_label"] for row in ledger["metrics"]}
    assert labels <= TRUTH_LABELS
    assert not labels & PROHIBITED_TRUTH_LABELS


def test_metric_sources_are_repo_relative_and_content_addressed(ledger: dict) -> None:
    for row in ledger["metrics"]:
        source = Path(row["source_path"])
        assert not source.is_absolute()
        path = ROOT / source
        assert path.is_file(), row["metric_id"]
        assert sha256(path) == row["source_sha256"], row["metric_id"]


def test_json_pointers_resolve(ledger: dict) -> None:
    cache: dict[str, object] = {}
    for row in ledger["metrics"]:
        source = row["source_path"]
        cache.setdefault(source, json.loads((ROOT / source).read_text(encoding="utf-8")))
        resolve_pointer(cache[source], row["source_json_pointer"])


@pytest.mark.parametrize(
    ("metric_id", "expected"),
    (
        ("g3b2.performance.weighted_geomean_improvement_percent", 45.59283008),
        ("g3b2.outcomes.wins", 18),
        ("g3b2.outcomes.ties", 0),
        ("g3b2.outcomes.losses", 0),
        ("g3b3.direct.official_call_expression_count", 17),
        ("g3b3.direct.runtime_execution", False),
        ("g3b3.native.exported_symbol_count", 19),
        ("g3b3.regression.ctest_passed", 14),
        ("g3b3.regression.ctest_failed", 0),
        ("g3b3.regression.python_passed", 93),
        ("g3b3.agent.proposal_records", 20),
        ("g3b3.agent.evaluation_records", 20),
        ("g3b3.agent.reflection_records", 20),
        ("g3b3.gates.int8_quantization", "DEFERRED_BY_PRECISION_GATE"),
        ("g3b3.gates.pairwise", "SKIPPED_BY_VALUE_GATE"),
    ),
)
def test_frozen_authoritative_metric_values(metrics: dict[str, dict], metric_id: str, expected: object) -> None:
    assert metrics[metric_id]["value"] == expected


def test_g3_b2_frozen_evidence_integrity() -> None:
    result = verify_sha256sums(G3_B2_ROOT)
    assert result["status"] == "PASS"
    assert result["sha256sums_sha256"] == "99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483"


def test_g3_b3_frozen_evidence_integrity() -> None:
    result = verify_sha256sums(G3_B3_ROOT)
    assert result["status"] == "PASS"
    assert result["sha256sums_sha256"] == "45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754"


def test_no_runtime_api_calls_are_reported(ledger: dict) -> None:
    runtime_values = [row["runtime_api_calls"] for row in ledger["metrics"] if row["runtime_api_calls"] is not None]
    assert all(value == [] for value in runtime_values)
