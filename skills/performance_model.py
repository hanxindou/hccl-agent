class PerformanceModel:

    def calculate_score(
        self,
        latency,
        bandwidth
    ):

        score = (
            bandwidth * 0.7
            -
            latency * 0.3
        )

        return round(score, 2)