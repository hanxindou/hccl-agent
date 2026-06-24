"""Replanning Skill — choose an alternative algorithm when reflection
indicates a re-plan is needed, or when topology changes force replanning."""


class ReplanningSkill:

    @staticmethod
    def choose_alternative(current_algorithm, ranking,
                           topology_changed=False):
        """Pick highest-ranked algorithm differing from *current*.

        When *topology_changed* is True, skips the current algorithm
        unconditionally (force replan).  Otherwise returns first
        alternative in ranking order.
        """
        if not ranking:
            return current_algorithm

        if topology_changed:
            for algo, _ in ranking:
                if algo != current_algorithm:
                    return algo
            return current_algorithm

        for algo, _ in ranking:
            if algo != current_algorithm:
                return algo

        return current_algorithm
