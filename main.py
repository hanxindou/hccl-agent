import argparse
import json
import shlex
import sys

from agent.hccl_agent import HCCLAgent
from plugin.hccl_vm_backend import (
    Backend,
    load_hccl_vm_config,
)
from plugin.hccl_vm_env import HcclVmEnvironment
from plugin.hccl_vm_evidence import archive_official_evidence
from plugin.hccl_vm_runner import (
    HcclVmRunner,
    OfficialAllReduceRequest,
)


def _add_backend_options(parser, *, default_backend=None):
    parser.add_argument(
        "--backend",
        choices=[backend.value for backend in Backend],
        default=default_backend,
        help="Execution backend. CPU_SIM remains the default for normal runs.",
    )
    parser.add_argument(
        "--config",
        dest="hccl_vm_config",
        help="Path to an HCCL-VM JSON configuration file.",
    )
    parser.add_argument("--wsl-distro")
    parser.add_argument("--cann-path")
    parser.add_argument("--hccl-vm-install-dir")
    parser.add_argument("--hccl-test-bin")
    parser.add_argument("--hcomm-source-dir")
    parser.add_argument("--hccl-source-dir")
    parser.add_argument("--topology")
    parser.add_argument("--mock-comm")
    parser.add_argument("--expansion-mode")
    parser.add_argument("--evidence-root")
    parser.add_argument("--timeout-seconds", type=int)


def _add_official_collective_options(parser):
    parser.add_argument("--primitive", default="AllReduce")
    parser.add_argument("--nodes", type=int, default=2)
    parser.add_argument("--dtype", default="int32")
    parser.add_argument("--op", default="sum")
    parser.add_argument("--elements", type=int, default=16)


def parse_args(argv=None):
    # CLI arguments make experiments reproducible while keeping interactive input available.
    parser = argparse.ArgumentParser(
        description="Run the HCCL Agent communication algorithm demo."
    )
    parser.set_defaults(command="run")
    _add_backend_options(parser)
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

    subparsers = parser.add_subparsers(dest="command")

    diagnose_parser = subparsers.add_parser(
        "diagnose",
        help="Inspect the external official HCCL-VM validation environment.",
    )
    _add_backend_options(
        diagnose_parser,
        default_backend=Backend.ASCEND_HCCL_VM.value,
    )

    dry_run_parser = subparsers.add_parser(
        "dry-run",
        help="Print the official validation execution plan without running it.",
    )
    _add_backend_options(
        dry_run_parser,
        default_backend=Backend.ASCEND_HCCL_VM.value,
    )
    _add_official_collective_options(dry_run_parser)

    verify_parser = subparsers.add_parser(
        "verify-official",
        help="Run the external official HCCL-VM validation workflow.",
    )
    _add_backend_options(
        verify_parser,
        default_backend=Backend.ASCEND_HCCL_VM.value,
    )
    _add_official_collective_options(verify_parser)

    args = parser.parse_args(argv)
    if args.command is None:
        args.command = "run"
    return args


def _config_from_args(args):
    overrides = {
        "backend": args.backend,
        "wsl_distro": args.wsl_distro,
        "cann_path": args.cann_path,
        "hccl_vm_install_dir": args.hccl_vm_install_dir,
        "hccl_test_bin": args.hccl_test_bin,
        "hcomm_source_dir": args.hcomm_source_dir,
        "hccl_source_dir": args.hccl_source_dir,
        "topology": args.topology,
        "mock_comm": args.mock_comm,
        "expansion_mode": args.expansion_mode,
        "evidence_root": args.evidence_root,
        "timeout_seconds": args.timeout_seconds,
    }
    return load_hccl_vm_config(
        args.hccl_vm_config,
        overrides=overrides,
    )


def main():
    args = parse_args()
    config = _config_from_args(args)

    if args.command != "run":
        _run_official_command(args, config)
        return

    if config.backend != Backend.CPU_SIM.value:
        raise SystemExit(
            "ASCEND_HCCL_VM is an external validation backend; "
            "use diagnose, dry-run, or verify-official."
        )

    _run_cpu_sim(args)


def _run_official_command(args, config):
    if args.command == "diagnose":
        report = HcclVmEnvironment(config).diagnose()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if report["status"] != "OK":
            raise SystemExit(2)
        return

    if args.command == "dry-run":
        try:
            request = _official_request_from_args(args)
            report = HcclVmRunner(config).dry_run(request)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    if args.command == "verify-official":
        try:
            request = _official_request_from_args(args)
            outcome = HcclVmRunner(config).verify(request)
            evidence = archive_official_evidence(
                outcome,
                request,
                config,
                command=shlex.join([sys.executable, *sys.argv]),
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        report = outcome.to_public_dict()
        report["evidence_dir"] = str(evidence.directory)
        report["evidence_sha256"] = evidence.checksum_file_sha256
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if not report.get("passed", False):
            raise SystemExit(2)
        return

    # No other official commands are currently supported.
    print(json.dumps(
        {
            "command": args.command,
            "selected_backend": config.backend,
            "status": "NOT_IMPLEMENTED",
        },
        indent=2,
    ))
    raise SystemExit(
        f"{args.command} is configured but not implemented yet"
    )


def _official_request_from_args(args):
    return OfficialAllReduceRequest(
        primitive=args.primitive,
        rank_count=args.nodes,
        dtype=args.dtype,
        reduce_op=args.op,
        elements=args.elements,
    )


def _run_cpu_sim(args):

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
