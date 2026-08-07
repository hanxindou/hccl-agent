# G3-B2 Agent trace contract

This directory separates the development agent (Codex), the repository runtime agent (`hccl-agent`), and the user. Records are append-only after their phase commit and use the frozen prompt registry and trace schema. All performance values are simulator-only; no ACL/HCCL runtime or real device is invoked.

Phase A freezes the contract and therefore contains no optimization proposal. Later phases add canonical records under `runs/`, `proposals/`, `evaluations/`, and `reflections/`.
