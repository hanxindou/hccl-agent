import json
import os


class ConfigSkill:

    REQUIRED_FIELDS = [
        "cluster_name",
        "device_type",
    ]

    DEFAULTS = {
        "cluster_name": "Ascend-Cluster",
        "nodes": 8,
        "topology": "Full Mesh",
        "device_type": "Ascend910A",
        "memory_gb": 64,
        "available_algorithms": [
            "Ring AllReduce",
            "Butterfly",
            "Mesh",
        ],
        "links": [
            {
                "type": "HCCS",
                "bandwidth_gbps": 100,
                "latency_ms": 0.002,
                "ber": 1e-12,
                "duplex": "full",
            },
        ],
        "numa": {
            "nodes_per_socket": 4,
            "sockets": 2,
        },
        "hbm": {
            "capacity_gb": 64,
            "bandwidth_gbps": 1200,
        },
        "ub": {
            "capacity_kb": 192,
        },
    }

    def __init__(self, config_path=None):
        if config_path is None:
            self.config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "config",
                "cluster.json",
            )
        else:
            self.config_path = config_path

    def load_cluster_info(self):
        """Load, validate, and normalize cluster configuration.

        Normalization extracts the primary intra-server link (HCCS)
        bandwidth and latency to top-level keys for backward
        compatibility with the simulator.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Cluster config not found: {self.config_path}"
            )

        with open(self.config_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        config = dict(self.DEFAULTS)
        config.update(raw)

        for field in self.REQUIRED_FIELDS:
            value = config.get(field)
            if value is None or value == "":
                raise ValueError(
                    f"Cluster config missing required field: {field}"
                )

        # Normalize: extract primary link params to top level so the
        # simulator can use bandwidth_gbps / latency_ms without parsing
        # the links array.
        links = config.get("links", [])
        if links and "bandwidth_gbps" not in config:
            primary = links[0]
            config["bandwidth_gbps"] = primary.get("bandwidth_gbps", 100)
            config["latency_ms"] = primary.get("latency_ms", 0.002)

        return config

    def get_link_by_type(self, link_type):
        """Return the first link dict matching *link_type* (e.g. 'HCCS')."""
        config = self.load_cluster_info()
        for link in config.get("links", []):
            if link.get("type") == link_type:
                return dict(link)
        return None
