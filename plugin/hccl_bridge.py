"""HCCL Plugin Bridge - Python ctypes access to the HCCL plugin library.

Provides a thin wrapper around the HCCL plugin shared library so the
Python Agent can query plugin metadata (version, supported algorithms)
and standard CPU-simulated wrapper symbols without any Ascend SDK
dependency.

Usage::

    bridge = HCCLBridge()
    print(bridge.get_version())       # "0.1.0-prototype"
    print(bridge.get_algorithms())    # "RingAllReduce,Butterfly,..."
"""

import ctypes
import os
import platform
from pathlib import Path


HCCL_SUCCESS = 0
HCCL_ERR_INVALID_ARG = -1
HCCL_ERR_NOT_SUPPORTED = -6

HCCL_FP32 = 0
HCCL_SUM = 0


def _platform_library_name(platform_name=None):
    name = (platform_name or platform.system()).lower()
    if name.startswith("win"):
        return "hccl_plugin.dll"
    return "libhccl_plugin.so"


def default_library_candidates(platform_name=None):
    """Return project-local default dynamic-library candidates."""
    root = Path(__file__).resolve().parents[1]
    lib_name = _platform_library_name(platform_name)
    build_dir = root / "hcccl" / "build"

    if lib_name.endswith(".dll"):
        candidates = [
            build_dir / "Release" / lib_name,
            build_dir / "Debug" / lib_name,
            build_dir / lib_name,
        ]
    else:
        candidates = [
            build_dir / lib_name,
            build_dir / "Release" / lib_name,
            build_dir / "Debug" / lib_name,
        ]

    return [str(path) for path in candidates]


def resolve_library_path(library_path=None, lib_path=None):
    """Resolve a plugin library path with B1-defined precedence."""
    attempts = []
    platform_name = platform.system()
    explicit_path = library_path if library_path is not None else lib_path

    if explicit_path:
        path = os.path.normpath(os.fspath(explicit_path))
        attempts.append(path)
        if not os.path.exists(path):
            raise FileNotFoundError(
                "HCCL plugin library not found from constructor path "
                f"on {platform_name}: {path}; attempted paths: {attempts}"
            )
        return path, "library_path", attempts

    env_path = os.environ.get("HCCL_PLUGIN_PATH")
    if env_path:
        path = os.path.normpath(env_path)
        attempts.append(path)
        if not os.path.exists(path):
            raise FileNotFoundError(
                "HCCL plugin library not found from HCCL_PLUGIN_PATH "
                f"on {platform_name}: {path}; attempted paths: {attempts}"
            )
        return path, "HCCL_PLUGIN_PATH", attempts

    candidates = [os.path.normpath(p) for p in default_library_candidates()]
    attempts.extend(candidates)
    for path in candidates:
        if os.path.exists(path):
            return path, "default", attempts

    raise FileNotFoundError(
        "HCCL plugin library not found in default candidates "
        f"on {platform_name}; attempted paths: {attempts}"
    )


def _bind(lib, name, argtypes, restype, lib_path, attempts):
    try:
        func = getattr(lib, name)
    except AttributeError as exc:
        raise AttributeError(
            f"HCCL plugin library missing required symbol '{name}' "
            f"on {platform.system()}: {lib_path}; attempted paths: {attempts}"
        ) from exc
    func.argtypes = argtypes
    func.restype = restype


def configure_ctypes_signatures(lib, lib_path, attempts=None,
                                include_algorithm_symbols=False):
    """Configure explicit ctypes ABI signatures for loaded symbols."""
    attempts = attempts or [lib_path]

    _bind(lib, "hcclPluginGetVersion", [], ctypes.c_char_p, lib_path, attempts)
    _bind(lib, "hcclPluginGetAlgorithms", [], ctypes.c_char_p, lib_path, attempts)

    _bind(
        lib,
        "hcclCommInit",
        [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int32,
         ctypes.POINTER(ctypes.c_int32)],
        ctypes.c_int,
        lib_path,
        attempts,
    )
    _bind(lib, "hcclCommDestroy", [ctypes.c_void_p], ctypes.c_int,
          lib_path, attempts)
    _bind(lib, "hcclSetRank", [ctypes.c_void_p, ctypes.c_int32],
          ctypes.c_int, lib_path, attempts)
    _bind(lib, "hcclGetTopology",
          [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
          ctypes.c_int, lib_path, attempts)

    _bind(lib, "hcclAllReduce",
          [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
           ctypes.c_int, ctypes.c_int, ctypes.c_void_p],
          ctypes.c_int, lib_path, attempts)
    _bind(lib, "hcclAllGather",
          [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
           ctypes.c_int, ctypes.c_void_p],
          ctypes.c_int, lib_path, attempts)
    _bind(lib, "hcclReduceScatter",
          [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
           ctypes.c_int, ctypes.c_int, ctypes.c_void_p],
          ctypes.c_int, lib_path, attempts)
    _bind(lib, "hcclBroadcast",
          [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
           ctypes.c_int, ctypes.c_int32, ctypes.c_void_p],
          ctypes.c_int, lib_path, attempts)

    if include_algorithm_symbols:
        for name in [
            "ring_allreduce",
            "butterfly_allreduce",
            "nhr_allreduce",
            "mesh_allreduce",
            "fattree_allreduce",
        ]:
            _bind(lib, name,
                  [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                   ctypes.c_int, ctypes.c_int, ctypes.c_void_p],
                  ctypes.c_int, lib_path, attempts)


class HCCLBridge:
    """Load the HCCL plugin and expose discovery plus wrapper functions."""

    def __init__(self, library_path=None, lib_path=None):
        """
        Parameters
        ----------
        library_path : str or None
            Explicit path to hccl_plugin.dll or libhccl_plugin.so.
        lib_path : str or None
            Backward-compatible alias for library_path.
        """
        resolved, source, attempts = resolve_library_path(library_path, lib_path)

        self.lib_path = resolved
        self.library_path = resolved
        self.library_source = source
        self.checked_paths = attempts
        self._lib = None

    # ------------------------------------------------------------------
    # Library loading
    # ------------------------------------------------------------------

    def load_library(self):
        """Load the shared library. Repeated calls are safe."""
        if self._lib is not None:
            return

        try:
            lib = ctypes.CDLL(self.lib_path)
        except OSError as exc:
            raise OSError(
                f"Unable to load HCCL plugin library on {platform.system()}: "
                f"{self.lib_path}; attempted paths: {self.checked_paths}; "
                f"original error: {exc}"
            ) from exc

        configure_ctypes_signatures(lib, self.lib_path, self.checked_paths)
        self._lib = lib

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_version(self):
        """Return the plugin version string, e.g. "0.1.0-prototype"."""
        self.load_library()
        result = self._lib.hcclPluginGetVersion()
        return result.decode("utf-8") if result else ""

    def get_algorithms(self):
        """Return the comma-separated algorithm list, e.g.
        "RingAllReduce,Butterfly,Mesh,NHR,FatTree"."""
        self.load_library()
        result = self._lib.hcclPluginGetAlgorithms()
        return result.decode("utf-8") if result else ""

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_library():
        """Backward-compatible helper returning the resolved default path."""
        path, _, _ = resolve_library_path()
        return path

    @staticmethod
    def default_library_candidates(platform_name=None):
        return default_library_candidates(platform_name)
