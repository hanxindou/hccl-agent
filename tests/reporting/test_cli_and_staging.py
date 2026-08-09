from __future__ import annotations

from pathlib import Path

import pytest

from tools.report_cli import build_command, describe_command, parser
from tools.reporting.evidence_reader import CHART_ROOT, CLAIM_LEDGER, DATA_LEDGER, REPORT_ROOT, STAGE_ROOT, sha256
from tools.reporting.final_evidence import _official_commits, create_final_evidence
from tools.reporting.schemas import CHART_FILES, REPORT_FILES
from tools.reporting.staging import MARKER, build_stage, verify_stage


def _generated_hashes() -> dict[str, str]:
    paths = [DATA_LEDGER, CLAIM_LEDGER]
    paths.extend(REPORT_ROOT / name for name in REPORT_FILES)
    paths.extend(CHART_ROOT / name for name in CHART_FILES)
    return {str(path): sha256(path) for path in paths}


def test_describe_is_read_only() -> None:
    before = _generated_hashes()
    result = describe_command()
    assert result["status"] == "PASS"
    assert result["read_only"] is True
    assert result["real_device_api_executed"] is False
    assert result["runtime_api_calls"] == []
    assert _generated_hashes() == before


def test_build_is_deterministic() -> None:
    before = _generated_hashes()
    result = build_command()
    assert result["status"] == "PASS"
    assert result["performance_benchmark_executed"] is False
    assert result["real_device_api_executed"] is False
    assert _generated_hashes() == before


@pytest.mark.parametrize("command", ("build", "verify", "describe", "stage", "verify-stage"))
def test_cli_accepts_expected_commands(command: str) -> None:
    assert parser().parse_args([command]).command == command


def test_stage_build_and_verify() -> None:
    result = build_stage()
    assert result["status"] == "PASS"
    assert result["official_assets_included"] is False
    assert result["controlled_competition_doc_included"] is False
    assert result["private_logs_included"] is False
    assert result["real_device_api_executed"] is False
    assert result["runtime_api_calls"] == []
    assert (STAGE_ROOT / MARKER).is_file()
    assert verify_stage()["status"] == "PASS"


def test_stage_contains_report_tests_and_tooling() -> None:
    assert (STAGE_ROOT / "tools/report_cli.py").is_file()
    assert (STAGE_ROOT / "tests/reporting/test_report_suite.py").is_file()
    assert (STAGE_ROOT / "docs/submission/reports/README.md").is_file()


def test_final_evidence_rejects_out_of_scope_path() -> None:
    with pytest.raises(RuntimeError, match="one new g3_c_\\*"):
        create_final_evidence(str(Path("dist/not-evidence")))


def test_official_commit_manifest_mapping() -> None:
    manifest = {
        "official_repositories": {
            "hcomm": {"commit": "hcomm-commit"},
            "hccl": {"commit": "hccl-commit"},
        }
    }
    assert _official_commits(manifest) == {"hcomm": "hcomm-commit", "hccl": "hccl-commit"}
