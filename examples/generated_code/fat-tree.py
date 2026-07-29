"""Generated example artifact for Fat-Tree AllReduce.

This file is intentionally a syntax-valid Python sketch produced by the
Agent code-generation prototype. It is not a CANN/HCCL implementation and
is not submitted as a real collective communication algorithm.
"""


class FatTreeExample:

    def execute(self):
        self.leaf_aggregation()
        self.core_aggregation()
        self.broadcast()

    def leaf_aggregation(self):
        """Sketch: intra-group sum."""

    def core_aggregation(self):
        """Sketch: inter-group leader sum."""

    def broadcast(self):
        """Sketch: global result to all leaves."""
