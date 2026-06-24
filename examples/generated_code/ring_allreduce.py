# Generated algorithm skeleton for Ring AllReduce
# Primitive: AllReduce

class RingAllReduce:

    def execute(self):
        reducescatter()  # ReduceScatter — each rank splits data, circulates chunks along ring
        ring_exchange()  # Ring Exchange — partial sums propagate through pipeline
        allgather()  # AllGather — fully reduced chunks circulate to all ranks

