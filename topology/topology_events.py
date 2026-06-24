"""Topology Event types for dynamic cluster changes."""

from typing import Any, Dict


class TopologyEvent:
    """A single topology mutation event."""

    VALID_TYPES = {
        "NodeJoin", "NodeLeave", "LinkAdd",
        "LinkRemove", "LinkFailure", "LinkRecovery",
    }

    def __init__(
        self,
        event_type: str,
        node_id: int = -1,
        src: int = -1,
        dst: int = -1,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        if event_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid event type: {event_type}. "
                f"Valid: {sorted(self.VALID_TYPES)}"
            )
        self.event_type = event_type
        self.node_id = node_id
        self.src = src
        self.dst = dst
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return (
            f"TopologyEvent({self.event_type}, node={self.node_id}, "
            f"link={self.src}->{self.dst})"
        )
