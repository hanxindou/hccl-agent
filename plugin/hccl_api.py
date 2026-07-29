"""HCCL Compatibility Layer — standard collective communication API.

Wraps the Simulator behind HCCL-standard function signatures
(HcclCommInit, HcclAllReduce, HcclAllGather, HcclReduceScatter)
so the Agent can interact through a recognised interface without
depending on real Ascend hardware.
"""

from typing import Any, Dict, List, Optional, Tuple

from plugin.execution_engine import ExecutionEngine

HCCL_SUCCESS: int = 0


class HcclComm:
    """Simulated HCCL communicator."""

    def __init__(self) -> None:
        self.rank: int = 0
        self.rank_size: int = 0
        self.topology: str = ""


def HcclCommInitClusterInfo(
    cluster_info: Dict[str, Any],
    rank: int,
) -> Tuple[int, HcclComm]:
    """Create a communicator from cluster configuration.

    Parameters
    ----------
    cluster_info : dict
        Loaded from config/cluster.json.
    rank : int
        Rank ID within the communicator.

    Returns
    -------
    (HCCL_SUCCESS, HcclComm)
    """
    comm = HcclComm()
    comm.rank = rank
    comm.rank_size = cluster_info.get("nodes", 1)
    comm.topology = cluster_info.get("topology", "Full Mesh")
    return HCCL_SUCCESS, comm


def _simulate(
    primitive: str,
    algorithm: str,
    comm: HcclComm,
    message_size_mb: float = 128.0,
    graph=None,
    profile=None,
) -> Dict[str, Any]:
    """Internal helper: run the Simulator (graph-first, fallback to flat)."""
    from simulator.simulator import Simulator

    sim = Simulator()
    if graph is not None:
        result = sim.simulate_with_graph(
            graph=graph,
            primitive=primitive,
            algorithm=algorithm,
            message_size_mb=message_size_mb,
            profile=profile,
        )
    else:
        result = sim.simulate_collective(
            primitive=primitive,
            algorithm=algorithm,
            topology=comm.topology,
            nodes=comm.rank_size,
            message_size_mb=message_size_mb,
        )
    result["status"] = "SUCCESS"
    result["primitive"] = primitive
    return result


def HcclAllReduce(
    send_buf: Optional[List[float]],
    recv_buf: Optional[List[float]],
    count: int,
    data_type: str,
    op: str,
    comm: HcclComm,
    algorithm: str = "Ring AllReduce",
) -> Dict[str, Any]:
    """HCCL AllReduce — simulated via the performance model."""
    return _simulate("AllReduce", algorithm, comm)


def HcclAllGather(
    send_buf: Optional[List[float]],
    recv_buf: Optional[List[float]],
    send_count: int,
    data_type: str,
    comm: HcclComm,
    algorithm: str = "Mesh",
) -> Dict[str, Any]:
    """HCCL AllGather — simulated via the performance model."""
    return _simulate("AllGather", algorithm, comm)


def HcclAllGatherReference(send_data: List[List[float]]) -> List[List[float]]:
    """Return the C1 CPU_SIM AllGather reference result.

    Input layout is [N][C]. Each destination rank receives the same
    flattened source-rank-ordered vector [N*C].
    """
    if not send_data:
        return []
    count = len(send_data[0])
    if count == 0 or any(len(row) != count for row in send_data):
        raise ValueError("send_data must be a non-empty rectangular matrix")

    expected_for_one_rank = [
        float(element)
        for src_rank in send_data
        for element in src_rank
    ]
    return [list(expected_for_one_rank) for _ in send_data]


def HcclAllGatherCpuData(
    send_data: List[List[float]],
    algorithm: str = "Wrapper",
    engine: Optional[ExecutionEngine] = None,
) -> Dict[str, Any]:
    """Execute AllGather through the C CPU_SIM plugin data path."""
    runner = engine or ExecutionEngine()
    result = runner.execute_allgather(send_data, algorithm=algorithm)
    if result["status"] == "success":
        result["reference"] = HcclAllGatherReference(send_data)
    return result


def HcclReduceScatter(
    send_buf: Optional[List[float]],
    recv_buf: Optional[List[float]],
    recv_count: int,
    data_type: str,
    op: str,
    comm: HcclComm,
    algorithm: str = "Ring AllReduce",
) -> Dict[str, Any]:
    """HCCL ReduceScatter — simulated via the performance model."""
    return _simulate("ReduceScatter", algorithm, comm)
