"""Retry Policy — execute operations with exponential backoff."""

import time
from typing import Any, Callable, Dict


class RetryPolicy:
    """Wrap a callable with retry logic."""

    def __init__(
        self,
        max_retry: int = 3,
        backoff_factor: float = 2.0,
        initial_delay_ms: float = 1.0,
    ) -> None:
        self.max_retry = max_retry
        self.backoff_factor = backoff_factor
        self.initial_delay_ms = initial_delay_ms

    def execute_with_retry(
        self, func: Callable[[], Any],
    ) -> Dict[str, Any]:
        """Call *func*, retrying on exception.

        Returns
        -------
        dict  {"success": bool, "attempts": int, "result": Any}
        """
        delay = self.initial_delay_ms / 1000.0
        for attempt in range(1, self.max_retry + 1):
            try:
                result = func()
                return {"success": True, "attempts": attempt, "result": result}
            except Exception:
                if attempt < self.max_retry:
                    time.sleep(delay)
                    delay *= self.backoff_factor
        return {"success": False, "attempts": self.max_retry, "result": None}
