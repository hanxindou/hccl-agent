"""Auto-Tuning Skill — search parameter space for optimal communication config."""

from typing import Any, Dict, List, Tuple


class AutoTuningSkill:
    """Grid-search over chunk_size, pipeline_depth, and overlap_factor."""

    @staticmethod
    def generate_parameter_space() -> Dict[str, List[float]]:
        """Return the searchable parameter ranges."""
        return {
            "chunk_size_mb":   [1, 2, 4, 8, 16],
            "pipeline_depth":  [1, 2, 4],
            "overlap_factor":  [0.0, 0.25, 0.5],
        }

    @staticmethod
    def enumerate_configurations(
        param_space: Dict[str, List[float]] | None = None,
    ) -> List[Dict[str, float]]:
        """Generate the Cartesian product of all parameter values."""
        if param_space is None:
            param_space = AutoTuningSkill.generate_parameter_space()
        keys = list(param_space.keys())
        values = list(param_space.values())
        configs: List[Dict[str, float]] = []

        def _recurse(idx: int, current: Dict[str, float]) -> None:
            if idx == len(keys):
                configs.append(dict(current))
                return
            for v in values[idx]:
                current[keys[idx]] = v
                _recurse(idx + 1, current)

        _recurse(0, {})
        return configs

    @staticmethod
    def evaluate_configuration(
        config: Dict[str, float],
        algorithm: str,
        topology: str,
        nodes: int,
        message_size_mb: float = 128.0,
        base_score: float = 0.0,
    ) -> float:
        """Compute a tuning-adjusted score for a given parameter config.

        Deterministic rules — no randomness.

        Parameters
        ----------
        config : dict  — keys: chunk_size_mb, pipeline_depth, overlap_factor
        algorithm : str
        topology : str
        nodes : int
        message_size_mb : float
        base_score : float  — score from the Simulator (0-100)

        Returns
        -------
        float  — adjusted score.
        """
        score = float(base_score)
        chunk = config.get("chunk_size_mb", 4)
        depth = config.get("pipeline_depth", 2)
        overlap = config.get("overlap_factor", 0.0)

        # Chunk size adjustment.
        if chunk == 1:
            score *= 0.85   # too small → latency penalty
        elif chunk == 2:
            score *= 0.95
        elif chunk == 4:
            score *= 1.0    # optimal
        elif chunk == 8:
            score *= 0.97   # slight bandwidth penalty
        elif chunk == 16:
            score *= 0.90   # bandwidth penalty

        # Pipeline depth bonus.
        if depth == 2:
            score *= 1.03
        elif depth == 4:
            score *= 1.05

        # Overlap factor bonus (compute-communication overlap).
        if overlap > 0:
            score *= 1.0 + overlap * 0.1  # up to +5% at overlap=0.5

        return round(min(score, 100.0), 2)

    @staticmethod
    def grid_search(
        algorithm: str,
        topology: str,
        nodes: int,
        message_size_mb: float = 128.0,
        base_score: float = 0.0,
        top_k: int = 5,
        param_space: Dict[str, List[float]] | None = None,
    ) -> Dict[str, Any]:
        """Exhaustive grid search for the best parameter configuration.

        Returns
        -------
        dict
            best_config, best_score, top_k, evaluated_configs count.
        """
        if param_space is None:
            param_space = AutoTuningSkill.generate_parameter_space()

        configs = AutoTuningSkill.enumerate_configurations(param_space)
        results: List[Tuple[float, Dict[str, float]]] = []

        for cfg in configs:
            s = AutoTuningSkill.evaluate_configuration(
                cfg, algorithm, topology, nodes, message_size_mb, base_score,
            )
            results.append((s, cfg))

        results.sort(key=lambda x: x[0], reverse=True)
        best_score, best_config = results[0]

        return {
            "best_config": best_config,
            "best_score": best_score,
            "top_k": [
                {"score": s, "config": c} for s, c in results[:top_k]
            ],
            "evaluated_configs": len(configs),
        }
