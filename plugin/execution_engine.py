"""Execution Engine — run HCCL algorithms via ctypes.

Loads libhccl_plugin.so and calls the C implementation of ring_allreduce
on real (CPU-simulated) data.  This is the first link that closes the
loop from Agent decision to actual computation.

Usage::

    engine = ExecutionEngine()
    result = engine.execute_algorithm("Ring AllReduce", [1.0, 2.0, 3.0, 4.0])
    # → {"algorithm": "Ring AllReduce", "status": "success",
    #    "result": [10.0, 10.0, 10.0, 10.0]}
"""

import ctypes
import os

# ---- C enum constants (must match hccl_comm.h) ----

HCCL_SUCCESS = 0
HCCL_ERR_INVALID_ARG   = -1
HCCL_ERR_NOT_SUPPORTED = -6

HCCL_FP32 = 0
HCCL_SUM  = 0

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


class ExecutionEngine:
    """Execute a named HCCL algorithm on the given input data."""

    def __init__(self, lib_path=None):
        if lib_path is None:
            lib_path = self._find_library()

        if not os.path.exists(lib_path):
            raise FileNotFoundError(
                f"HCCL plugin library not found: {lib_path}"
            )

        self.lib_path = lib_path
        self._lib = None

    # ------------------------------------------------------------------
    # Library loading & ctypes bindings
    # ------------------------------------------------------------------

    def load_library(self):
        if self._lib is not None:
            return

        lib = ctypes.CDLL(self.lib_path)

        # -- hcclCommInit --
        lib.hcclCommInit.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),   # hcclComm_t*  (out)
            ctypes.c_int32,                    # num_devices
            ctypes.POINTER(ctypes.c_int32),    # device_ids*
        ]
        lib.hcclCommInit.restype = ctypes.c_int

        # -- hcclCommDestroy --
        lib.hcclCommDestroy.argtypes = [ctypes.c_void_p]
        lib.hcclCommDestroy.restype = ctypes.c_int

        # -- hcclSetRank --
        lib.hcclSetRank.argtypes = [
            ctypes.c_void_p,   # hcclComm_t
            ctypes.c_int32,    # rank
        ]
        lib.hcclSetRank.restype = ctypes.c_int

        # -- ring_allreduce --
        lib.ring_allreduce.argtypes = [
            ctypes.POINTER(ctypes.c_float),   # send_buf
            ctypes.POINTER(ctypes.c_float),   # recv_buf
            ctypes.c_size_t,                  # count
            ctypes.c_int,                     # data_type
            ctypes.c_int,                     # op
            ctypes.c_void_p,                  # comm
        ]
        lib.ring_allreduce.restype = ctypes.c_int

        # -- butterfly_allreduce --
        lib.butterfly_allreduce.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_size_t,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        lib.butterfly_allreduce.restype = ctypes.c_int

        # -- nhr_allreduce --
        lib.nhr_allreduce.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_size_t,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        lib.nhr_allreduce.restype = ctypes.c_int

        # -- mesh_allreduce --
        lib.mesh_allreduce.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_size_t,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        lib.mesh_allreduce.restype = ctypes.c_int

        # -- fattree_allreduce --
        lib.fattree_allreduce.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_size_t,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        lib.fattree_allreduce.restype = ctypes.c_int

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
        candidate = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "hcccl",
            "build",
            "libhccl_plugin.so",
        )
        return os.path.normpath(candidate)
