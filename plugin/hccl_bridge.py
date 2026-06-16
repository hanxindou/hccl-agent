"""HCCL Plugin Bridge — Python ↔ libhccl_plugin.so via ctypes.

Provides a thin wrapper around the HCCL plugin shared library so the
Python Agent can query plugin metadata (version, supported algorithms)
without any Ascend SDK dependency.

Usage::

    bridge = HCCLBridge()
    print(bridge.get_version())       # "0.1.0-prototype"
    print(bridge.get_algorithms())    # "RingAllReduce,Butterfly,..."
"""

import ctypes
import os


class HCCLBridge:
    """Load libhccl_plugin.so and expose its plugin-discovery functions."""

    def __init__(self, lib_path=None):
        """
        Parameters
        ----------
        lib_path : str or None
            Path to libhccl_plugin.so.  When None the bridge searches
            for the library at the default build location relative to
            this source file.
        """
        if lib_path is None:
            lib_path = self._find_library()

        if not os.path.exists(lib_path):
            raise FileNotFoundError(
                f"HCCL plugin library not found: {lib_path}\n"
                f"Build it first:\n"
                f"  cd hcccl && mkdir -p build && cd build\n"
                f"  cmake .. && make"
            )

        self.lib_path = lib_path
        self._lib = None

    # ------------------------------------------------------------------
    # Library loading
    # ------------------------------------------------------------------

    def load_library(self):
        """Load the shared library (idempotent — loads once)."""
        if self._lib is not None:
            return

        self._lib = ctypes.CDLL(self.lib_path)

        # ---- hcclPluginGetVersion: () -> const char* ----
        self._lib.hcclPluginGetVersion.argtypes = []
        self._lib.hcclPluginGetVersion.restype = ctypes.c_char_p

        # ---- hcclPluginGetAlgorithms: () -> const char* ----
        self._lib.hcclPluginGetAlgorithms.argtypes = []
        self._lib.hcclPluginGetAlgorithms.restype = ctypes.c_char_p

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
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _find_library():
        """Locate the default build output of the HCCL plugin."""
        # Search relative to this file: plugin/ → ../hcccl/build/
        candidate = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "hcccl",
            "build",
            "libhccl_plugin.so",
        )
        return os.path.normpath(candidate)
