"""Replanning Skill — choose an alternative algorithm when reflection
indicates a re-plan is needed."""


class ReplanningSkill:

    @staticmethod
    def choose_alternative(current_algorithm, ranking):
        """Pick the highest-ranked algorithm that differs from *current*.

        Parameters
        ----------
        current_algorithm : str
            The algorithm that was just executed.
        ranking : list of (algorithm, score)  sorted descending.

        Returns
        -------
        str — the alternative algorithm, or *current_algorithm* if no
              alternative exists.
        """
        if not ranking:
            return current_algorithm

        for algo, _ in ranking:
            if algo != current_algorithm:
                return algo

        return current_algorithm
