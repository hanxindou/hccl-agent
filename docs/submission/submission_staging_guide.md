# Submission staging guide

G3-B creates an internal, auditable staging directory, not a final release or
competition upload. The default policy includes project source, the freshly
built CPU_SIM plugin, headers, build metadata, tests, configuration examples,
CLI tools, sanitized selected-evidence summaries, and truthful placeholders.

It excludes the controlled competition DOCX, official CANN binaries, official
HCOMM/HCCL source, private logs, credentials, caches, and superseded raw
evidence. Conditional assets remain `USER_ACTION_REQUIRED`.

```text
python -m tools.submission_cli stage --clean-output --include-selected-evidence \
  --exclude-controlled-docs --exclude-official-assets
python -m tools.submission_cli verify --stage dist/submission-staging
```

The staging `MANIFEST.json` and `SHA256SUMS` cover included payloads. A
preliminary forbidden-data scan is provided, but the final license, privacy,
clean-extraction, archive, and release audit belongs to G3-G.
