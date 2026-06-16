import argparse

from agent.hccl_agent import HCCLAgent


def parse_args():
    # CLI arguments make experiments reproducible while keeping interactive input available.
    parser = argparse.ArgumentParser(
        description="Run the HCCL Agent communication algorithm demo."
    )
    parser.add_argument(
        "--nodes",
        type=int,
        help="Number of NPU nodes/cards in this experiment."
    )
    parser.add_argument(
        "--message-size",
        type=int,
        help="Message size in MB."
    )
    parser.add_argument(
        "--primitive",
        default="AllReduce",
        help="Collective primitive: AllReduce, AllGather, or ReduceScatter."
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # If CLI values are not provided, fall back to beginner-friendly prompts.
    nodes = args.nodes
    if nodes is None:
        nodes = int(input("Nodes: "))

    message_size = args.message_size
    if message_size is None:
        message_size = int(input("Message size (MB): "))

    agent = HCCLAgent()

    output = agent.run(
        nodes,
        message_size,
        args.primitive
    )
    print()

    print("Cluster Info")

    print(
        output["cluster"]["cluster_name"]
    )

    print(
        output["cluster"]["device_type"]
    )

    print(
        output["cluster"]["bandwidth_gbps"],
        "Gbps"
    )

    print()

    print(
        "Primitive:",
        output["primitive"]
    )

    print(
        "Topology:",
        output["topology"]
    )

    print()

    print(
        "Recommended algorithm:",
        output["algorithm"]
    )

    print()

    print(
        "Reason:",
        output["reason"]
    )

    print()

    print("LLM Reasoning")

    print(
        output.get("reasoning")
    )

    print()
    print("Simulation Result")

    print(
        "Latency:",
        output["result"]["latency"],
        "ms"
    )

    print(
        "Bandwidth:",
        output["result"]["bandwidth"],
        "GB/s"
    )

    print(
        "Score:",
        output["result"]["score"]
    )

    print()
    print("Agent Optimization Result")

    print(
        "Best algorithm:",
        output["best_algorithm"]
    )

    print(
        "Best result:",
        output["best_result"]
    )

    print()

    print("Communication Strategy")

    for step in (
        output["strategy"]["steps"]
    ):

        print(step)

    print()
    print("Algorithm Score Ranking")

    for algo, score in (
        output["ranking"]
    ):

        print(
            algo,
            "->",
            score
        )


if __name__ == "__main__":
    main()
