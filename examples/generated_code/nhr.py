# Generated algorithm skeleton for NHR
# Primitive: AllReduce

class NHR:

    def execute(self):
        group_local_ring_reduce_(group_size=4)()  # Group-local ring reduce (group_size=4)
        leader_ring_reduce_across_groups()  # Leader ring reduce across groups
        group_broadcast()  # Group broadcast — leaders distribute to members

