from __future__ import annotations

import subprocess

import pytest

from tools.reporting import evidence_reader, report_verifier


def _install_ref_map(monkeypatch: pytest.MonkeyPatch, available: set[str]) -> list[str]:
    attempted: list[str] = []

    def fake_git(*args: str) -> str:
        assert args[:2] == ("rev-parse", "--verify")
        candidate = args[2].removesuffix("^{commit}")
        attempted.append(candidate)
        if candidate in available:
            return "a" * 40
        raise subprocess.CalledProcessError(128, ["git", *args])

    monkeypatch.setattr(evidence_reader, "git", fake_git)
    return attempted


def test_resolver_uses_local_main(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    attempted = _install_ref_map(monkeypatch, {"refs/heads/main", "main"})
    assert evidence_reader.resolve_reporting_base_ref() == "refs/heads/main"
    assert attempted == ["refs/heads/main"]


def test_resolver_falls_back_to_origin_main(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    attempted = _install_ref_map(monkeypatch, {"refs/remotes/origin/main", "origin/main"})
    assert evidence_reader.resolve_reporting_base_ref() == "refs/remotes/origin/main"
    assert attempted == ["refs/heads/main", "main", "refs/remotes/origin/main"]


def test_github_main_prefers_remote_tracking_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    attempted = _install_ref_map(monkeypatch, {"refs/remotes/origin/main", "refs/heads/main"})
    assert evidence_reader.resolve_reporting_base_ref() == "refs/remotes/origin/main"
    assert attempted == ["refs/remotes/origin/main"]


def test_github_non_main_base_is_resolved(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_BASE_REF", "release/next")
    attempted = _install_ref_map(monkeypatch, {"refs/remotes/origin/release/next", "refs/heads/main"})
    assert evidence_reader.resolve_reporting_base_ref() == "refs/remotes/origin/release/next"
    assert attempted == ["refs/remotes/origin/release/next"]


def test_missing_github_ref_falls_back_to_local_main(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_BASE_REF", "missing")
    attempted = _install_ref_map(monkeypatch, {"refs/heads/main"})
    assert evidence_reader.resolve_reporting_base_ref() == "refs/heads/main"
    assert attempted == ["refs/remotes/origin/missing", "origin/missing", "refs/heads/main"]


def test_missing_all_refs_raises_stable_reporting_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_BASE_REF", "missing")
    _install_ref_map(monkeypatch, set())
    with pytest.raises(RuntimeError) as caught:
        evidence_reader.resolve_reporting_base_ref()
    message = str(caught.value)
    assert "reporting base ref cannot be resolved" in message
    assert "refs/remotes/origin/missing" in message
    assert "GITHUB_BASE_REF='missing'" in message
    assert "complete Git history" in message
    assert "CalledProcessError" not in message
    assert "exit status 128" not in message


def test_source_commit_falls_back_to_resolved_ref(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(evidence_reader, "resolve_reporting_base_ref", lambda: "origin/release")
    monkeypatch.setattr(evidence_reader, "git", lambda *args: calls.append(args) or "b" * 40)
    assert evidence_reader.source_commit(tmp_path / "unavailable.json") == "b" * 40
    assert calls == [("merge-base", "HEAD", "origin/release")]


def test_source_commit_prefers_frozen_g3_c_authority(tmp_path) -> None:
    source = tmp_path / "source_commit.json"
    source.write_text('{"source_commit":"' + "c" * 40 + '"}\n', encoding="utf-8")
    assert evidence_reader.source_commit(source) == "c" * 40


def test_report_verifier_diff_uses_shared_resolver(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(report_verifier, "resolve_reporting_base_ref", lambda: "origin/release")
    monkeypatch.setattr(report_verifier, "git", lambda *args: calls.append(args) or "one\\file\ntwo/file\n")
    assert report_verifier._git_diff_from_base() == ["one/file", "two/file"]
    assert calls == [("diff", "--name-only", "origin/release")]


def test_resolver_only_performs_read_only_ref_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    attempted = _install_ref_map(monkeypatch, {"refs/remotes/origin/main"})
    assert evidence_reader.resolve_reporting_base_ref() == "refs/remotes/origin/main"
    assert attempted == ["refs/heads/main", "main", "refs/remotes/origin/main"]
