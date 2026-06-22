"""Policy Engine — experience-driven algorithm ranking.

Blends simulated scores with historical win rates so the Agent favours
algorithms that have proven themselves in similar past scenarios.
"""


class PolicyEngine:

    SIM_WEIGHT   = 0.7   # simulation score contribution
    HISTORY_WEIGHT = 0.3 # historical win-rate contribution

    @staticmethod
    def calculate_win_rates(historical_stats):
        """Convert per-algorithm stats into win-rate proportions.

        Win rate = count(algo) / total_count.  Algorithms that appear
        more often in successful past runs get a higher rate.

        Parameters
        ----------
        historical_stats : dict
            {"Mesh": {"count": 12, ...}, "Ring AllReduce": {"count": 5, ...}}

        Returns
        -------
        dict  {"Mesh": 0.71, "Ring AllReduce": 0.29, ...}
        """
        if not historical_stats:
            return {}

        total = sum(s["count"] for s in historical_stats.values())
        if total == 0:
            return {}

        return {
            algo: round(s["count"] / total, 4)
            for algo, s in historical_stats.items()
        }

    @classmethod
    def rank_algorithms(cls, simulation_scores, win_rates):
        """Blend simulation scores with historical win rates.

        Parameters
        ----------
        simulation_scores : dict
            {"Ring AllReduce": 82.0, "Butterfly": 86.0, ...}
        win_rates : dict
            {"Ring AllReduce": 0.20, "Butterfly": 0.35, ...}

        Returns
        -------
        list of (algorithm, final_score)  sorted descending.
        """
        results = []
        for algo, sim in simulation_scores.items():
            wr = win_rates.get(algo, 0.0)
            final = sim * cls.SIM_WEIGHT + wr * 100.0 * cls.HISTORY_WEIGHT
            results.append((algo, round(final, 2)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results
