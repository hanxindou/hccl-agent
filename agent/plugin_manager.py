"""Plugin Manager — Agent-facing wrapper around the HCCL plugin bridge.

Combines the raw ctypes bridge (plugin/hccl_bridge.py) with the algorithm
name parser (agent/plugin_capability.py) to produce a structured
capability report that the Agent can consume directly.
"""

from plugin.hccl_bridge import HCCLBridge
from agent.plugin_capability import parse_algorithm_list, map_algorithm_name


class PluginManager:

    def __init__(self):
        self.bridge = HCCLBridge()

    def discover(self):
        """Query the HCCL plugin for its version and supported algorithms.

        Returns
        -------
        dict
            {
                "version": "0.1.0-prototype",
                "algorithms": ["Ring AllReduce", "Butterfly", ...],
                "raw_algorithms": "RingAllReduce,Butterfly,...",
                "library_path": "/.../libhccl_plugin.so",
            }
        """
        version = self.bridge.get_version()
        raw = self.bridge.get_algorithms()
        compact_list = parse_algorithm_list(raw)
        display_list = [map_algorithm_name(a) for a in compact_list]

        return {
            "version": version,
            "algorithms": display_list,
            "raw_algorithms": raw,
            "library_path": self.bridge.lib_path,
        }
