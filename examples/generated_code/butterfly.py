"""Generated example artifact for Butterfly AllReduce.

This file is intentionally a syntax-valid Python sketch produced by the
Agent code-generation prototype. It is not a CANN/HCCL implementation and
is not submitted as a real collective communication algorithm.
"""


class ButterflyExample:

    def execute(self):
        self.pairwise_exchange_distance_1()
        self.recursive_doubling()
        self.final_broadcast()

    def pairwise_exchange_distance_1(self):
        """Sketch: pairwise exchange at distance=1."""

    def recursive_doubling(self):
        """Sketch: exchange at distance=2,4,8 up to N/2."""

    def final_broadcast(self):
        """Sketch: all ranks hold the global result."""
