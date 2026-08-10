from __future__ import annotations

import json
import re

from tools.release_audit.authority import MANDATORY_ENTRY_POINTS
from tools.release_audit.common import RELEASE_ROOT


def _load(name: str) -> dict:
    return json.loads((RELEASE_ROOT / name).read_text(encoding="utf-8"))


def test_two_clean_worktree_runs_passed_full_sequence() -> None:
    runs = [_load("cold_start_run_1.json"), _load("cold_start_run_2.json")]
    assert [row["run_id"] for row in runs] == ["run-1", "run-2"]
    for row in runs:
        assert row["status"] == "PASS"
        assert row["initial_worktree_clean"] is True
        assert row["prior_build_present"] is row["prior_dist_present"] is row["prior_staging_present"] is False
        assert row["untracked_input_used"] is row["repository_local_venv_used"] is False
        assert row["local_clone_network_used"] is False
        assert len(row["steps"]) == len(MANDATORY_ENTRY_POINTS) == 14
        assert all(step["status"] == "PASS" for step in row["steps"])
        pytest_step = next(step for step in row["steps"] if step["command"][:4] == ["python", "-m", "pytest", "tests"])
        assert "1029 passed, 1 skipped" in pytest_step["output_summary"]["pytest_summary"]


def test_declared_outputs_are_bit_identical_between_runs() -> None:
    comparison = _load("cold_start_reproducibility.json")
    assert comparison["status"] == "PASS"
    assert comparison["sentinel"] == "G3_G_COLD_START_REPRODUCTION_OK"
    assert comparison["classification"] == "BIT_FOR_BIT_FOR_DECLARED_OUTPUTS"
    assert comparison["manifest_reproducible"] is True
    assert comparison["archive_reproducibility_evaluated"] is False
    assert all(row["identical"] for row in comparison["comparisons"].values())


def test_cold_start_results_preserve_offline_and_no_npu_boundaries() -> None:
    for name in ("cold_start_run_1.json", "cold_start_run_2.json"):
        row = _load(name)
        assert row["network_required"] is False
        assert row["api_keys_present"] is False
        assert row["external_llm_invoked"] is False
        assert row["real_device_api_executed"] is False
        assert row["runtime_api_calls"] == []
        assert row["benchmark_rerun"] is False


def test_portable_cold_start_transcripts_have_no_private_absolute_path() -> None:
    pattern = re.compile(r"(?i)(?:[A-Z]:\\Users\\|/home/[^/]+/|/mnt/[a-z]/Users/)")
    for name in ("cold_start_run_1.json", "cold_start_run_2.json", "cold_start_environment.json", "cold_start_summary.json"):
        assert not pattern.search((RELEASE_ROOT / name).read_text(encoding="utf-8")), name
