"""Execution Engine - run HCCL algorithms via ctypes.

Loads the HCCL plugin shared library and calls the C implementation of
the current CPU-simulated AllReduce algorithms.

Usage::

    engine = ExecutionEngine()
    result = engine.execute_algorithm("Ring AllReduce", [1.0, 2.0, 3.0, 4.0])
    # → {"algorithm": "Ring AllReduce", "status": "success",
    #    "result": [10.0, 10.0, 10.0, 10.0]}
"""

import ctypes
import struct

from plugin.hccl_bridge import configure_ctypes_signatures, resolve_library_path

# ---- C enum constants (must match hccl_comm.h) ----

HCCL_SUCCESS = 0
HCCL_ERR_INVALID_ARG   = -1
HCCL_ERR_NOT_SUPPORTED = -6

HCCL_FP32 = 0
HCCL_FP16 = 1
HCCL_BF16 = 2
HCCL_SUM  = 0
HCCL_PROD = 1
HCCL_MAX  = 2
HCCL_MIN  = 3

# ---- Algorithm name mapping (Agent display name → internal key) ----

_ALGO_TABLE = {
    "Ring AllReduce": "ring",
    "Butterfly":      "butterfly",
    "Mesh":           "mesh",
    "NHR":            "nhr",
    "Fat-Tree":       "fattree",
    "PairWise":       "pairwise",
}

_IMPLEMENTED = {"ring", "butterfly", "nhr", "mesh", "fattree"}


def _float_to_bits(value):
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def _bits_to_float(bits):
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def float_to_bf16_bits(value):
    bits = _float_to_bits(value)
    if (bits & 0x7F800000) == 0x7F800000 and (bits & 0x007FFFFF):
        return ((bits >> 16) | 0x0040) & 0xFFFF
    bits = (bits + 0x7FFF + ((bits >> 16) & 1)) & 0xFFFFFFFF
    return (bits >> 16) & 0xFFFF


def bf16_bits_to_float(value):
    return _bits_to_float((int(value) & 0xFFFF) << 16)


def float_to_fp16_bits(value):
    bits = _float_to_bits(value)
    sign = (bits >> 16) & 0x8000
    raw_exp = (bits >> 23) & 0xFF
    mant = bits & 0x007FFFFF
    exp = int(raw_exp) - 127 + 15

    if raw_exp == 0xFF:
        if mant == 0:
            return sign | 0x7C00
        return sign | 0x7C00 | (mant >> 13) | 0x0001
    if exp <= 0:
        if exp < -10:
            return sign
        mant = (mant | 0x00800000) >> (1 - exp)
        return sign | ((mant + 0x00001000) >> 13)
    if exp >= 31:
        return sign | 0x7C00

    mant += 0x00001000
    if mant & 0x00800000:
        mant = 0
        exp += 1
        if exp >= 31:
            return sign | 0x7C00
    return sign | (exp << 10) | (mant >> 13)


def fp16_bits_to_float(value):
    half = int(value) & 0xFFFF
    sign = (half & 0x8000) << 16
    exp = (half >> 10) & 0x1F
    mant = half & 0x03FF

    if exp == 0:
        if mant == 0:
            bits = sign
        else:
            shift = 0
            while (mant & 0x0400) == 0:
                mant <<= 1
                shift += 1
            mant &= 0x03FF
            bits = sign | ((127 - 15 - shift) << 23) | (mant << 13)
    elif exp == 0x1F:
        bits = sign | 0x7F800000 | (mant << 13)
        if mant:
            bits |= 0x00000001
    else:
        bits = sign | ((exp + (127 - 15)) << 23) | (mant << 13)

    return _bits_to_float(bits)


def roundtrip_dtype_value(value, data_type):
    if data_type == HCCL_FP16:
        return fp16_bits_to_float(float_to_fp16_bits(value))
    if data_type == HCCL_BF16:
        return bf16_bits_to_float(float_to_bf16_bits(value))
    return float(value)


def _make_input_array(values, data_type):
    if data_type == HCCL_FP16:
        return (ctypes.c_uint16 * len(values))(
            *[float_to_fp16_bits(value) for value in values]
        )
    if data_type == HCCL_BF16:
        return (ctypes.c_uint16 * len(values))(
            *[float_to_bf16_bits(value) for value in values]
        )
    return (ctypes.c_float * len(values))(*[float(value) for value in values])


def _make_output_array(length, data_type):
    if data_type in {HCCL_FP16, HCCL_BF16}:
        return (ctypes.c_uint16 * length)()
    return (ctypes.c_float * length)()


def _read_output_value(buffer, index, data_type):
    if data_type == HCCL_FP16:
        return fp16_bits_to_float(buffer[index])
    if data_type == HCCL_BF16:
        return bf16_bits_to_float(buffer[index])
    return float(buffer[index])


class ExecutionEngine:
    """Execute a named HCCL algorithm on the given input data."""

    def __init__(self, library_path=None, lib_path=None):
        resolved, source, attempts = resolve_library_path(library_path, lib_path)
        self.lib_path = resolved
        self.library_path = resolved
        self.library_source = source
        self.checked_paths = attempts
        self._lib = None

    # ------------------------------------------------------------------
    # Library loading & ctypes bindings
    # ------------------------------------------------------------------

    def load_library(self):
        if self._lib is not None:
            return

        lib = ctypes.CDLL(self.lib_path)
        configure_ctypes_signatures(
            lib, self.lib_path, self.checked_paths,
            include_algorithm_symbols=True,
        )

        self._lib = lib

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_algorithm(self, algorithm_name, input_data):
        """Run *algorithm_name* on *input_data*.

        Parameters
        ----------
        algorithm_name : str
            Agent display name, e.g. "Ring AllReduce".
        input_data : list[float]
            One float per rank, e.g. [1.0, 2.0, 3.0, 4.0].

        Returns
        -------
        dict with keys "algorithm", "status", "result".
        """
        algo_key = _ALGO_TABLE.get(algorithm_name)
        if algo_key is None:
            return {
                "algorithm": algorithm_name,
                "status": "unknown_algorithm",
                "result": None,
            }

        if algo_key not in _IMPLEMENTED:
            return {
                "algorithm": algorithm_name,
                "status": "not_implemented",
                "result": None,
            }

        if not input_data:
            return {
                "algorithm": algorithm_name,
                "status": "invalid_input",
                "result": None,
            }

        if algo_key == "ring":
            return self._execute_ring_allreduce(input_data)
        elif algo_key == "butterfly":
            return self._execute_butterfly(input_data)
        elif algo_key == "nhr":
            return self._execute_nhr(input_data)
        elif algo_key == "mesh":
            return self._execute_mesh(input_data)
        elif algo_key == "fattree":
            return self._execute_fattree(input_data)

        return {
            "algorithm": algorithm_name,
            "status": "not_implemented",
            "result": None,
        }

    def execute_allgather(self, send_data, algorithm="Wrapper",
                          data_type=HCCL_FP32):
        """Run CPU_SIM AllGather on a rectangular rank-by-element matrix.

        send_data uses the C1 CPU_SIM input layout [N][C]. The returned
        result uses [N][N*C], one flattened gathered vector per dst rank.
        """
        if not send_data:
            return {
                "primitive": "AllGather",
                "algorithm": algorithm,
                "status": "invalid_input",
                "return_code": HCCL_ERR_INVALID_ARG,
                "result": None,
            }
        count = len(send_data[0])
        if count == 0 or any(len(row) != count for row in send_data):
            return {
                "primitive": "AllGather",
                "algorithm": algorithm,
                "status": "invalid_input",
                "return_code": HCCL_ERR_INVALID_ARG,
                "result": None,
            }

        self.load_library()
        lib = self._lib
        n = len(send_data)
        flat_input = [float(value) for row in send_data for value in row]
        send = _make_input_array(flat_input, data_type)
        recv = _make_output_array(n * n * count, data_type)

        comm = ctypes.c_void_p()
        device_ids = (ctypes.c_int32 * n)(*range(n))
        rc = lib.hcclCommInit(ctypes.byref(comm), n, device_ids)
        if rc != HCCL_SUCCESS:
            return {
                "primitive": "AllGather",
                "algorithm": algorithm,
                "status": "comm_init_failed",
                "return_code": rc,
                "result": None,
            }

        try:
            normalized = algorithm.lower()
            if normalized in {"wrapper", "hcclallgather", "standard"}:
                call = lib.hcclAllGather
            elif normalized in {"ring", "ring allgather"}:
                call = lib.ring_allgather
            elif normalized in {"butterfly", "butterfly allgather"}:
                call = lib.butterfly_allgather
            else:
                return {
                    "primitive": "AllGather",
                    "algorithm": algorithm,
                    "status": "unknown_algorithm",
                    "return_code": HCCL_ERR_NOT_SUPPORTED,
                    "result": None,
                }

            rc = call(send, recv, count, data_type, comm)
            if rc != HCCL_SUCCESS:
                return {
                    "primitive": "AllGather",
                    "algorithm": algorithm,
                    "status": "not_supported" if rc == HCCL_ERR_NOT_SUPPORTED else "error",
                    "return_code": rc,
                    "result": None,
                }

            rows = []
            row_len = n * count
            for dst in range(n):
                offset = dst * row_len
                rows.append([
                    round(_read_output_value(recv, offset + idx, data_type), 6)
                    for idx in range(row_len)
                ])
        finally:
            lib.hcclCommDestroy(comm)

        return {
            "primitive": "AllGather",
            "algorithm": algorithm,
            "status": "success",
            "return_code": rc,
            "result": rows,
        }

    def execute_reducescatter(self, send_data, data_type=HCCL_FP32,
                              op=HCCL_SUM):
        """Run CPU_SIM ReduceScatter on [N][N][C] FP32 data."""
        if not send_data:
            return {
                "primitive": "ReduceScatter",
                "algorithm": "Mesh",
                "status": "invalid_input",
                "return_code": HCCL_ERR_INVALID_ARG,
                "result": None,
            }
        n = len(send_data)
        if any(len(src_row) != n for src_row in send_data):
            return {
                "primitive": "ReduceScatter",
                "algorithm": "Mesh",
                "status": "invalid_input",
                "return_code": HCCL_ERR_INVALID_ARG,
                "result": None,
            }
        count = len(send_data[0][0]) if n else 0
        if count == 0:
            return {
                "primitive": "ReduceScatter",
                "algorithm": "Mesh",
                "status": "invalid_input",
                "return_code": HCCL_ERR_INVALID_ARG,
                "result": None,
            }
        for src_row in send_data:
            for shard in src_row:
                if len(shard) != count:
                    return {
                        "primitive": "ReduceScatter",
                        "algorithm": "Mesh",
                        "status": "invalid_input",
                        "return_code": HCCL_ERR_INVALID_ARG,
                        "result": None,
                    }

        self.load_library()
        lib = self._lib
        flat_input = [
            float(value)
            for src_row in send_data
            for shard in src_row
            for value in shard
        ]
        send = _make_input_array(flat_input, data_type)
        recv = _make_output_array(n * count, data_type)

        comm = ctypes.c_void_p()
        device_ids = (ctypes.c_int32 * n)(*range(n))
        rc = lib.hcclCommInit(ctypes.byref(comm), n, device_ids)
        if rc != HCCL_SUCCESS:
            return {
                "primitive": "ReduceScatter",
                "algorithm": "Mesh",
                "status": "comm_init_failed",
                "return_code": rc,
                "result": None,
            }

        try:
            rc = lib.hcclReduceScatter(send, recv, count, data_type, op, comm)
            if rc != HCCL_SUCCESS:
                return {
                    "primitive": "ReduceScatter",
                    "algorithm": "Mesh",
                    "status": "not_supported" if rc == HCCL_ERR_NOT_SUPPORTED else "error",
                    "return_code": rc,
                    "result": None,
                }

            rows = []
            for dst in range(n):
                offset = dst * count
                rows.append([
                    round(_read_output_value(recv, offset + elem, data_type), 6)
                    for elem in range(count)
                ])
        finally:
            lib.hcclCommDestroy(comm)

        return {
            "primitive": "ReduceScatter",
            "algorithm": "Mesh",
            "status": "success",
            "return_code": rc,
            "result": rows,
        }

    def execute_allreduce_data(self, input_data, algorithm="Ring", op=HCCL_SUM,
                               data_type=HCCL_FP32):
        """Run CPU_SIM FP32 AllReduce over one scalar per rank."""
        if not input_data:
            return {
                "primitive": "AllReduce",
                "algorithm": algorithm,
                "status": "invalid_input",
                "return_code": HCCL_ERR_INVALID_ARG,
                "result": None,
            }

        self.load_library()
        lib = self._lib
        n = len(input_data)
        comm = ctypes.c_void_p()
        device_ids = (ctypes.c_int32 * n)(*range(n))
        rc = lib.hcclCommInit(ctypes.byref(comm), n, device_ids)
        if rc != HCCL_SUCCESS:
            return {
                "primitive": "AllReduce",
                "algorithm": algorithm,
                "status": "comm_init_failed",
                "return_code": rc,
                "result": None,
            }

        try:
            normalized = algorithm.lower()
            if normalized in {"wrapper", "hcclallreduce", "standard"}:
                call = lib.hcclAllReduce
            elif normalized in {"ring", "ring allreduce"}:
                call = lib.ring_allreduce
            elif normalized in {"butterfly", "butterfly allreduce"}:
                call = lib.butterfly_allreduce
            elif normalized in {"mesh", "mesh allreduce"}:
                call = lib.mesh_allreduce
            elif normalized in {"nhr", "nhr allreduce"}:
                call = lib.nhr_allreduce
            elif normalized in {"fattree", "fat-tree", "fat-tree allreduce"}:
                call = lib.fattree_allreduce
            else:
                return {
                    "primitive": "AllReduce",
                    "algorithm": algorithm,
                    "status": "unknown_algorithm",
                    "return_code": HCCL_ERR_NOT_SUPPORTED,
                    "result": None,
                }

            for rank, value in enumerate(input_data):
                lib.hcclSetRank(comm, rank)
                send = _make_input_array([value], data_type)
                recv = _make_output_array(1, data_type)
                call(send, recv, 1, data_type, op, comm)

            results = []
            for rank, value in enumerate(input_data):
                lib.hcclSetRank(comm, rank)
                send = _make_input_array([value], data_type)
                recv = _make_output_array(1, data_type)
                rc = call(send, recv, 1, data_type, op, comm)
                if rc != HCCL_SUCCESS:
                    return {
                        "primitive": "AllReduce",
                        "algorithm": algorithm,
                        "status": "not_supported" if rc == HCCL_ERR_NOT_SUPPORTED else "error",
                        "return_code": rc,
                        "result": None,
                    }
                results.append(round(_read_output_value(recv, 0, data_type), 6))
        finally:
            lib.hcclCommDestroy(comm)

        return {
            "primitive": "AllReduce",
            "algorithm": algorithm,
            "status": "success",
            "return_code": rc,
            "result": results,
        }

    # ------------------------------------------------------------------
    # Ring AllReduce execution
    # ------------------------------------------------------------------

    def _execute_ring_allreduce(self, input_data):
        """Run Ring AllReduce(SUM) on *input_data*.

        Two-pass pattern (matching test_ring.c):
          Pass 1 — submit each rank's value
          Pass 2 — retrieve per-rank results
        """
        self.load_library()
        lib = self._lib
        N = len(input_data)

        # -- create communicator --
        comm = ctypes.c_void_p()
        device_ids = (ctypes.c_int32 * N)(*range(N))
        rc = lib.hcclCommInit(
            ctypes.byref(comm), N, device_ids
        )
        if rc != HCCL_SUCCESS:
            return {
                "algorithm": "Ring AllReduce",
                "status": "comm_init_failed",
                "result": None,
            }

        try:
            send = ctypes.c_float()
            recv = ctypes.c_float()

            # Pass 1 — submit all values.
            for rank in range(N):
                lib.hcclSetRank(comm, rank)
                send.value = input_data[rank]
                lib.ring_allreduce(
                    ctypes.byref(send), ctypes.byref(recv),
                    1, HCCL_FP32, HCCL_SUM, comm,
                )

            # Pass 2 — retrieve all results.
            results = []
            for rank in range(N):
                lib.hcclSetRank(comm, rank)
                send.value = input_data[rank]
                lib.ring_allreduce(
                    ctypes.byref(send), ctypes.byref(recv),
                    1, HCCL_FP32, HCCL_SUM, comm,
                )
                results.append(round(recv.value, 6))

        finally:
            lib.hcclCommDestroy(comm)

        return {
            "algorithm": "Ring AllReduce",
            "status": "success",
            "result": results,
        }

    # ------------------------------------------------------------------
    # Butterfly execution
    # ------------------------------------------------------------------

    def _execute_butterfly(self, input_data):
        """Run Butterfly AllReduce(SUM) on *input_data*."""
        self.load_library()
        lib = self._lib
        N = len(input_data)

        comm = ctypes.c_void_p()
        device_ids = (ctypes.c_int32 * N)(*range(N))
        rc = lib.hcclCommInit(ctypes.byref(comm), N, device_ids)
        if rc != HCCL_SUCCESS:
            return {
                "algorithm": "Butterfly",
                "status": "comm_init_failed",
                "result": None,
            }

        try:
            send = ctypes.c_float()
            recv = ctypes.c_float()

            for rank in range(N):
                lib.hcclSetRank(comm, rank)
                send.value = input_data[rank]
                lib.butterfly_allreduce(
                    ctypes.byref(send), ctypes.byref(recv),
                    1, HCCL_FP32, HCCL_SUM, comm,
                )

            results = []
            for rank in range(N):
                lib.hcclSetRank(comm, rank)
                send.value = input_data[rank]
                lib.butterfly_allreduce(
                    ctypes.byref(send), ctypes.byref(recv),
                    1, HCCL_FP32, HCCL_SUM, comm,
                )
                results.append(round(recv.value, 6))

        finally:
            lib.hcclCommDestroy(comm)

        return {
            "algorithm": "Butterfly",
            "status": "success",
            "result": results,
        }

    # ------------------------------------------------------------------
    # NHR execution
    # ------------------------------------------------------------------

    def _execute_nhr(self, input_data):
        self.load_library()
        lib = self._lib
        N = len(input_data)

        comm = ctypes.c_void_p()
        device_ids = (ctypes.c_int32 * N)(*range(N))
        rc = lib.hcclCommInit(ctypes.byref(comm), N, device_ids)
        if rc != HCCL_SUCCESS:
            return {"algorithm": "NHR", "status": "comm_init_failed", "result": None}

        try:
            send = ctypes.c_float()
            recv = ctypes.c_float()
            for rank in range(N):
                lib.hcclSetRank(comm, rank)
                send.value = input_data[rank]
                lib.nhr_allreduce(ctypes.byref(send), ctypes.byref(recv),
                                  1, HCCL_FP32, HCCL_SUM, comm)
            results = []
            for rank in range(N):
                lib.hcclSetRank(comm, rank)
                send.value = input_data[rank]
                lib.nhr_allreduce(ctypes.byref(send), ctypes.byref(recv),
                                  1, HCCL_FP32, HCCL_SUM, comm)
                results.append(round(recv.value, 6))
        finally:
            lib.hcclCommDestroy(comm)

        return {"algorithm": "NHR", "status": "success", "result": results}

    # ------------------------------------------------------------------
    # Mesh execution
    # ------------------------------------------------------------------

    def _execute_mesh(self, input_data):
        self.load_library()
        lib = self._lib
        N = len(input_data)

        comm = ctypes.c_void_p()
        device_ids = (ctypes.c_int32 * N)(*range(N))
        rc = lib.hcclCommInit(ctypes.byref(comm), N, device_ids)
        if rc != HCCL_SUCCESS:
            return {"algorithm": "Mesh", "status": "comm_init_failed", "result": None}

        try:
            send = ctypes.c_float()
            recv = ctypes.c_float()
            for rank in range(N):
                lib.hcclSetRank(comm, rank)
                send.value = input_data[rank]
                lib.mesh_allreduce(ctypes.byref(send), ctypes.byref(recv),
                                   1, HCCL_FP32, HCCL_SUM, comm)
            results = []
            for rank in range(N):
                lib.hcclSetRank(comm, rank)
                send.value = input_data[rank]
                lib.mesh_allreduce(ctypes.byref(send), ctypes.byref(recv),
                                   1, HCCL_FP32, HCCL_SUM, comm)
                results.append(round(recv.value, 6))
        finally:
            lib.hcclCommDestroy(comm)

        return {"algorithm": "Mesh", "status": "success", "result": results}

    # ------------------------------------------------------------------
    # Fat-Tree execution
    # ------------------------------------------------------------------

    def _execute_fattree(self, input_data):
        self.load_library()
        lib = self._lib
        N = len(input_data)

        comm = ctypes.c_void_p()
        device_ids = (ctypes.c_int32 * N)(*range(N))
        rc = lib.hcclCommInit(ctypes.byref(comm), N, device_ids)
        if rc != HCCL_SUCCESS:
            return {"algorithm": "Fat-Tree", "status": "comm_init_failed", "result": None}

        try:
            send = ctypes.c_float()
            recv = ctypes.c_float()
            for rank in range(N):
                lib.hcclSetRank(comm, rank)
                send.value = input_data[rank]
                lib.fattree_allreduce(ctypes.byref(send), ctypes.byref(recv),
                                      1, HCCL_FP32, HCCL_SUM, comm)
            results = []
            for rank in range(N):
                lib.hcclSetRank(comm, rank)
                send.value = input_data[rank]
                lib.fattree_allreduce(ctypes.byref(send), ctypes.byref(recv),
                                      1, HCCL_FP32, HCCL_SUM, comm)
                results.append(round(recv.value, 6))
        finally:
            lib.hcclCommDestroy(comm)

        return {"algorithm": "Fat-Tree", "status": "success", "result": results}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _find_library():
        path, _, _ = resolve_library_path()
        return path
