"""Calibration Registry — manage multiple named profiles."""

import os
from typing import Dict, List

from calibration.calibration_profile import CalibrationProfile


class CalibrationRegistry:
    """Register, load, and switch between calibration profiles."""

    def __init__(self, profiles_dir: str | None = None) -> None:
        if profiles_dir is None:
            profiles_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "default_profiles",
            )
        self.profiles_dir = profiles_dir
        self._profiles: Dict[str, CalibrationProfile] = {}
        self._current_name: str = "competition_v1"
        self._auto_load()

    def _auto_load(self) -> None:
        if os.path.isdir(self.profiles_dir):
            for fname in os.listdir(self.profiles_dir):
                if fname.endswith(".json"):
                    name = fname.replace(".json", "")
                    path = os.path.join(self.profiles_dir, fname)
                    try:
                        self._profiles[name] = CalibrationProfile.from_json(path)
                    except Exception:
                        continue
        # Always ensure a default profile exists.
        if not self._profiles:
            default = CalibrationProfile(
                version="v1", author="hccl-agent",
                description="Default calibration profile (auto-generated).",
            )
            self._profiles["competition_v1"] = default

    def register_profile(self, name: str, profile: CalibrationProfile) -> None:
        self._profiles[name] = profile

    def load_profile(self, name: str) -> CalibrationProfile:
        if name not in self._profiles:
            raise KeyError(f"Profile '{name}' not found. Available: {self.list_profiles()}")
        self._current_name = name
        return self._profiles[name]

    def current_profile(self) -> CalibrationProfile:
        return self._profiles.get(
            self._current_name,
            next(iter(self._profiles.values())),
        )

    def list_profiles(self) -> List[str]:
        return sorted(self._profiles.keys())


# Global singleton.
_registry: CalibrationRegistry | None = None


def get_registry() -> CalibrationRegistry:
    global _registry
    if _registry is None:
        _registry = CalibrationRegistry()
    return _registry
