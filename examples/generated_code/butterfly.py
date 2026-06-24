# Generated algorithm skeleton for Butterfly
# Primitive: AllReduce

class Butterfly:

    def execute(self):
        pairwise_exchange_at_distance=1_(nearest_neighbour)()  # Pairwise exchange at distance=1 (nearest neighbour)
        recursive_doubling_at_distance=2,4,8…_up_to_n/2()  # Recursive doubling at distance=2,4,8… up to N/2
        final_broadcast()  # Final broadcast — all ranks hold global result

