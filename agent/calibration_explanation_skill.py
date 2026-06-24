"""Calibration Explanation Skill — explain parameter provenance and impact."""

from typing import Any, Dict


class CalibrationExplanationSkill:
    """Generate human-readable explanation of calibration parameters."""

    @staticmethod
    def explain(profile: Any) -> Dict[str, Any]:
        d = profile.to_dict() if hasattr(profile, "to_dict") else profile
        return {
            "profile_version": d.get("version", "N/A"),
            "author": d.get("author", "N/A"),
            "description": d.get("description", ""),
            "parameter_count": (
                len(d.get("algorithm_efficiency", {}))
                + len(d.get("contention_coefficients", {})) + 6
            ),
            "parameter_summary": {
                "Algorithm Efficiency": (
                    "Reflects how effectively each algorithm utilises "
                    "available link bandwidth (0-1 scale)."
                ),
                "Contention Coefficients": (
                    "Controls how bandwidth degrades under concurrent "
                    "peer-to-peer communication."
                ),
                "Latency Scale": (
                    "Smooth-decay parameter: at latency=SCALE, "
                    "latency sub-score = 50."
                ),
                "Bandwidth/Latency Weights": (
                    "Relative importance of bandwidth vs latency "
                    "in the final composite score."
                ),
            },
        }
