# Dynamic schedule replanning

The replan contract accepts degradation, link-down, recovery, rank removal, no-path, and topology-change events. It records the prior and resulting topology/schedule hashes, route decision, correctness, memory bound, and event outcome. Five frozen cases replan successfully; the no-alternate-path case remains the explicit `EXPECTED_NO_PATH_FAILURE` and never silently falls back.

These are deterministic simulator events. They do not establish real communicator recovery, real fault switching, or device-runtime failover latency.
