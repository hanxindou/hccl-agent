"""HCCL Compatibility Layer — standard collective communication API.

Wraps the Simulator behind HCCL-standard function signatures
(HcclCommInit, HcclAllReduce, HcclAllGather, HcclReduceScatter)
so the Agent can interact through a recognised interface without
depending on real Ascend hardware.
"""

from typing import Any, Dict, List, Optional, Tuple

from plugin.execution_engine import (
    HCCL_BF16,
    HCCL_FP16,
    HCCL_FP32,
    HCCL_MAX,
    HCCL_MIN,
    HCCL_PROD,
    HCCL_SUM,
    ExecutionEngine,
    roundtrip_dtype_value,
)

HCCL_SUCCESS: int = 0

_REDUCE_OP_NAMES = {
    HCCL_SUM: "SUM",
    HCCL_PROD: "PROD",
    HCCL_MAX: "MAX",
    HCCL_MIN: "MIN",
}

_SUPPORTED_DTYPES = {HCCL_FP32, HCCL_FP16, HCCL_BF16}


def _normalize_dtype(data_type: int) -> int:
    if data_type in _SUPPORTED_DTYPES:
        return data_type
    raise ValueError(f"unsupported dtype: {data_type}")


def _quantize_input_values(values: List[float], data_type: int) -> List[float]:
    data_type = _normalize_dtype(data_type)
    return [roundtrip_dtype_value(float(value), data_type) for value in values]


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


def HcclAllGatherReference(
    send_data: List[List[float]],
    data_type: int = HCCL_FP32,
) -> List[List[float]]:
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
        roundtrip_dtype_value(float(element), data_type)
        for src_rank in send_data
        for element in src_rank
    ]
    return [list(expected_for_one_rank) for _ in send_data]


def HcclAllGatherCpuData(
    send_data: List[List[float]],
    algorithm: str = "Wrapper",
    data_type: int = HCCL_FP32,
    engine: Optional[ExecutionEngine] = None,
) -> Dict[str, Any]:
    """Execute AllGather through the C CPU_SIM plugin data path."""
    runner = engine or ExecutionEngine()
    result = runner.execute_allgather(
        send_data, algorithm=algorithm, data_type=data_type,
    )
    if result["status"] == "success":
        result["reference"] = HcclAllGatherReference(send_data, data_type=data_type)
    return result


def _normalize_reduce_op(op: int) -> int:
    if op in _REDUCE_OP_NAMES:
        return op
    raise ValueError(f"unsupported ReduceOp: {op}")


def _apply_reduce(values: List[float], op: int) -> float:
    op = _normalize_reduce_op(op)
    if op == HCCL_SUM:
        result = 0.0
        for value in values:
            result += float(value)
        return result
    if op == HCCL_PROD:
        result = 1.0
        for value in values:
            result *= float(value)
        return result
    if op == HCCL_MAX:
        result = float(values[0])
        for value in values[1:]:
            candidate = float(value)
            if candidate > result:
                result = candidate
        return result
    if op == HCCL_MIN:
        result = float(values[0])
        for value in values[1:]:
            candidate = float(value)
            if candidate < result:
                result = candidate
        return result
    raise ValueError(f"unsupported ReduceOp: {op}")


def HcclAllReduceReference(
    input_data: List[float],
    op: int = HCCL_SUM,
    data_type: int = HCCL_FP32,
) -> List[float]:
    """Return the FP32 CPU_SIM AllReduce reference for one scalar per rank."""
    if not input_data:
        return []
    values = _quantize_input_values(input_data, data_type)
    reduced = _apply_reduce(values, op)
    reduced = roundtrip_dtype_value(reduced, data_type)
    return [reduced for _ in input_data]


def HcclAllReduceCpuData(
    input_data: List[float],
    algorithm: str = "Wrapper",
    op: int = HCCL_SUM,
    data_type: int = HCCL_FP32,
    engine: Optional[ExecutionEngine] = None,
) -> Dict[str, Any]:
    """Execute AllReduce through the C CPU_SIM plugin data path."""
    runner = engine or ExecutionEngine()
    result = runner.execute_allreduce_data(
        input_data, algorithm=algorithm, op=op, data_type=data_type,
    )
    if result["status"] == "success":
        result["reference"] = HcclAllReduceReference(
            input_data, op=op, data_type=data_type,
        )
    return result


def HcclReduceScatterReference(
    send_data: List[List[List[float]]],
    op: int = HCCL_SUM,
    data_type: int = HCCL_FP32,
) -> List[List[float]]:
    """Return the CPU_SIM ReduceScatter FP32 reference.

    Input layout is [N][N][C], indexed as send[src][dst][element].
    Output layout is [N][C], one reduced shard per dst rank.
    """
    if not send_data:
        return []
    rank_count = len(send_data)
    if any(len(src_row) != rank_count for src_row in send_data):
        raise ValueError("send_data must have shape [N][N][C]")
    recv_count = len(send_data[0][0])
    if recv_count == 0:
        raise ValueError("recv_count must be greater than zero")
    for src_row in send_data:
        for shard in src_row:
            if len(shard) != recv_count:
                raise ValueError("all shards must have the same length")

    return [
        [
            roundtrip_dtype_value(
                _apply_reduce(
                    _quantize_input_values(
                        [float(send_data[src][dst][elem]) for src in range(rank_count)],
                        data_type,
                    ),
                    op,
                ),
                data_type,
            )
            for elem in range(recv_count)
        ]
        for dst in range(rank_count)
    ]


def HcclReduceScatterCpuData(
    send_data: List[List[List[float]]],
    op: int = HCCL_SUM,
    data_type: int = HCCL_FP32,
    engine: Optional[ExecutionEngine] = None,
) -> Dict[str, Any]:
    """Execute ReduceScatter through the C CPU_SIM plugin data path."""
    runner = engine or ExecutionEngine()
    result = runner.execute_reducescatter(send_data, data_type=data_type, op=op)
    if result["status"] == "success":
        result["reference"] = HcclReduceScatterReference(
            send_data, op=op, data_type=data_type,
        )
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
