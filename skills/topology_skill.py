class TopologySkill:

    def analyze(
        self,
        nodes
    ):

        if nodes <= 8:
            return "Full Mesh"

        elif nodes <= 64:
            return "Ring"

        else:
            return "Fat Tree"