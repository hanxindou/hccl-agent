"""G3-B3 feature-completion contracts and host-only implementations."""

from .contracts import (
    AGENT_PROPOSAL_VERSION,
    SCHEDULE_IR_VERSION,
    canonical_hash,
    upgrade_dense_schedule_v2,
    validate_agent_proposal_v2,
    validate_schedule_v2,
)

__all__ = [
    "AGENT_PROPOSAL_VERSION",
    "SCHEDULE_IR_VERSION",
    "canonical_hash",
    "upgrade_dense_schedule_v2",
    "validate_agent_proposal_v2",
    "validate_schedule_v2",
]
