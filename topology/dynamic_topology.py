"""Dynamic Topology Manager — apply events and rebuild graphs."""

from typing import Any, Dict, List, Optional, Tuple

from topology.topology_events import TopologyEvent
from topology.graph_builder import TopologyGraphBuilder, CommunicationGraph
from hardware.profile import HardwareProfile


class DynamicTopologyManager:
    """Track and apply topology mutations over time."""

    def __init__(
        self,
        num_nodes: int,
        num_gpus_per_node: int = 8,
        profile: HardwareProfile | None = None,
        mode: str = "SINGLE_NODE",
    ) -> None:
        self.initial_nodes = num_nodes
        self.gpus_per_node = num_gpus_per_node
        self.profile = profile or HardwareProfile.tier_medium()
        self.mode = mode
        self._version: int = 0
        self._events: List[TopologyEvent] = []
        self._current_nodes: int = num_nodes

        self.graph, self.meta = TopologyGraphBuilder.build(
            num_nodes, num_gpus_per_node, self.profile, mode,
        )

    # ------------------------------------------------------------------
    # Event management
    # ------------------------------------------------------------------

    def apply_event(self, event: TopologyEvent) -> None:
        """Record and apply a topology event."""
        self._events.append(event)
        self._version += 1

        if event.event_type == "NodeJoin":
            self._current_nodes += 1
        elif event.event_type == "NodeLeave":
            self._current_nodes = max(1, self._current_nodes - 1)

        # Rebuild graph after mutation.
        self.graph, self.meta = self._rebuild()

    def apply_events(self, events: List[TopologyEvent]) -> None:
        """Apply a batch of events (single rebuild at end)."""
        for e in events:
            self._events.append(e)
            self._version += 1
            if e.event_type == "NodeJoin":
                self._current_nodes += 1
            elif e.event_type == "NodeLeave":
                self._current_nodes = max(1, self._current_nodes - 1)
        self.graph, self.meta = self._rebuild()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def current_version(self) -> int:
        return self._version

    def event_history(self) -> List[TopologyEvent]:
        return list(self._events)

    def current_node_count(self) -> int:
        return self._current_nodes

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _rebuild(self) -> Tuple[CommunicationGraph, Dict[str, Any]]:
        mode = self.mode
        if self._current_nodes <= 8:
            mode = "SINGLE_NODE"
        elif self._current_nodes <= 64:
            mode = "MULTI_NODE"
        return TopologyGraphBuilder.build(
            self._current_nodes, self.gpus_per_node, self.profile, mode,
        )
