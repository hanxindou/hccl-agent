"""Tests for RetryPolicy."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from simulator.retry_policy import RetryPolicy


class TestRetryPolicy(unittest.TestCase):

    def test_success_first_attempt(self):
        rp = RetryPolicy(max_retry=3)
        r = rp.execute_with_retry(lambda: 42)
        self.assertTrue(r["success"])
        self.assertEqual(r["attempts"], 1)
        self.assertEqual(r["result"], 42)

    def test_retry_then_success(self):
        attempts = [0]

        def flaky():
            attempts[0] += 1
            if attempts[0] < 3:
                raise RuntimeError("fail")
            return "ok"

        rp = RetryPolicy(max_retry=3, initial_delay_ms=0)
        r = rp.execute_with_retry(flaky)
        self.assertTrue(r["success"])
        self.assertEqual(r["attempts"], 3)

    def test_max_retry_exceeded(self):
        rp = RetryPolicy(max_retry=2, initial_delay_ms=0)
        r = rp.execute_with_retry(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        self.assertFalse(r["success"])
        self.assertEqual(r["attempts"], 2)


if __name__ == "__main__":
    unittest.main()
