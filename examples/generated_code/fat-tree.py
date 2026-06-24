# Generated algorithm skeleton for Fat-Tree
# Primitive: AllReduce

class Fat-Tree:

    def execute(self):
        leaf_aggregation()  # Leaf aggregation — intra-group sum
        core_aggregation()  # Core aggregation — inter-group leader sum
        broadcast()  # Broadcast — global result to all leaves

