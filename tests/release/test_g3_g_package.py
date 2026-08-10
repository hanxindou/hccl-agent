import json
import stat
import zipfile
from pathlib import Path

from tools.release_audit.package import (
    FIXED_ZIP_TIME,
    MARKER,
    _write_deterministic_zip,
    validate_archive,
    validate_release_metadata,
)


def test_tracked_release_metadata_is_complete_and_honest():
    result = validate_release_metadata()
    assert result["status"] == "PASS"
    assert result["sentinels"] == ["G3_G_FINAL_STAGING_OK", "G3_G_RELEASE_CANDIDATE_OK"]


def test_release_manifest_has_exact_required_source_mapping():
    manifest = json.loads(Path("docs/submission/release/release_manifest.json").read_text(encoding="utf-8"))
    assert manifest["file_count"] == len(manifest["entries"])
    assert manifest["total_size"] == sum(row["size"] for row in manifest["entries"])
    assert all(row["required"] and row["source"] != "UNKNOWN_SOURCE" for row in manifest["entries"])
    assert manifest["final_submission_authorization"] == "USER_ACTION_REQUIRED"
    assert manifest["final_submission_archive_status"] == "NOT_AUTHORIZED"


def test_deterministic_archive_and_safe_metadata(tmp_path):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / MARKER).write_text("owned\n", encoding="utf-8")
    (candidate / "payload/scripts").mkdir(parents=True)
    (candidate / "payload/data.txt").write_text("payload\n", encoding="utf-8")
    (candidate / "payload/scripts/check.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    first, second = tmp_path / "one.zip", tmp_path / "two.zip"
    assert _write_deterministic_zip(candidate, first) == _write_deterministic_zip(candidate, second)
    result = validate_archive(first, candidate)
    assert result["status"] == "PASS"
    with zipfile.ZipFile(first) as archive:
        assert [row.filename for row in archive.infolist()] == sorted(row.filename for row in archive.infolist())
        for row in archive.infolist():
            assert row.date_time == FIXED_ZIP_TIME
            expected = 0o755 if row.filename.endswith("check.sh") else 0o644
            assert stat.S_IMODE(row.external_attr >> 16) == expected


def test_archive_contract_never_claims_final_submission_authorization():
    contract = json.loads(Path("docs/submission/release/archive_contract.json").read_text(encoding="utf-8"))
    assert contract["artifact_identity"] == "RELEASE_CANDIDATE_ARCHIVE"
    assert contract["final_submission_archive"] is False
    assert contract["final_submission_archive_status"] == "NOT_AUTHORIZED"
