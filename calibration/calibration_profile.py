"""Calibration Profile — versioned, traceable simulation parameters."""

import json
from typing import Any, Dict


class CalibrationProfile:
    """All key simulator parameters in one versioned profile."""

    def __init__(
        self,
        version: str = "v1",
        author: str = "hccl-agent",
        description: str = "",
        algorithm_efficiency: Dict[str, float] | None = None,
        contention_coefficients: Dict[str, float] | None = None,
        latency_scale: float = 30.0,
        bandwidth_weight: float = 0.4,
        latency_weight: float = 0.6,
        overlap_factor_default: float = 0.0,
        mesh_effective_steps_coeff: float = 0.15,
        hardware_tier: str = "medium",
    ) -> None:
        self.version = version
        self.author = author
        self.description = description
        self.algorithm_efficiency = algorithm_efficiency or {
            "Ring AllReduce": 0.90, "Butterfly": 0.85, "Mesh": 0.88,
            "NHR": 0.93, "Fat-Tree": 0.95, "PairWise": 0.82,
        }
        self.contention_coefficients = contention_coefficients or {
            "Mesh": 0.12, "Fat-Tree": 0.04,
        }
        self.latency_scale = latency_scale
        self.bandwidth_weight = bandwidth_weight
        self.latency_weight = latency_weight
        self.overlap_factor_default = overlap_factor_default
        self.mesh_effective_steps_coeff = mesh_effective_steps_coeff
        self.hardware_tier = hardware_tier

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "algorithm_efficiency": self.algorithm_efficiency,
            "contention_coefficients": self.contention_coefficients,
            "latency_scale": self.latency_scale,
            "bandwidth_weight": self.bandwidth_weight,
            "latency_weight": self.latency_weight,
            "overlap_factor_default": self.overlap_factor_default,
            "mesh_effective_steps_coeff": self.mesh_effective_steps_coeff,
            "hardware_tier": self.hardware_tier,
        }

    def to_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "CalibrationProfile":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            version=data.get("version", "v1"),
            author=data.get("author", "hccl-agent"),
            description=data.get("description", ""),
            algorithm_efficiency=data.get("algorithm_efficiency"),
            contention_coefficients=data.get("contention_coefficients"),
            latency_scale=data.get("latency_scale", 30.0),
            bandwidth_weight=data.get("bandwidth_weight", 0.4),
            latency_weight=data.get("latency_weight", 0.6),
            overlap_factor_default=data.get("overlap_factor_default", 0.0),
            mesh_effective_steps_coeff=data.get("mesh_effective_steps_coeff", 0.15),
            hardware_tier=data.get("hardware_tier", "medium"),
        )
