"""Tests for LLMClient — mock-only, no real network calls."""

import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from agent.llm_client import LLMClient


class TestLLMClient(unittest.TestCase):

    def setUp(self):
        # Always provide a fake key so instantiation succeeds.
        self.client = LLMClient(api_key="sk-test")

    # ---- success case ----

    @patch("urllib.request.urlopen")
    def test_ask_returns_content(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps({
                "choices": [
                    {"message": {"content": "Recommendation: Ring AllReduce"}}
                ]
            }).encode("utf-8")
        )

        result = self.client.ask("Test prompt")
        self.assertIn("Ring AllReduce", result)

    # ---- missing API key ----

    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient(api_key="")  # explicit empty
            with self.assertRaises(ValueError):
                client.ask("prompt")

    # ---- empty response ----

    @patch("urllib.request.urlopen")
    def test_ask_empty_choices_raises(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps({"choices": []}).encode("utf-8")
        )
        with self.assertRaises(RuntimeError):
            self.client.ask("prompt")

    # ---- HTTP error ----

    @patch("urllib.request.urlopen")
    def test_ask_http_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "http://fake", 401, "Unauthorized", {}, None,
        )
        with self.assertRaises(RuntimeError):
            self.client.ask("prompt")

    # ---- URL error ----

    @patch("urllib.request.urlopen")
    def test_ask_url_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        with self.assertRaises(RuntimeError):
            self.client.ask("prompt")

    # ---- system prompt ----

    @patch("urllib.request.urlopen")
    def test_ask_with_system_prompt(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps({
                "choices": [
                    {"message": {"content": "OK"}}
                ]
            }).encode("utf-8")
        )
        result = self.client.ask("user", system_prompt="You are helpful.")
        self.assertEqual("OK", result)

    # ---- env var fallback ----

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-env"})
    @patch("urllib.request.urlopen")
    def test_reads_key_from_env(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps({
                "choices": [
                    {"message": {"content": "env works"}}
                ]
            }).encode("utf-8")
        )
        client = LLMClient()  # no explicit key
        result = client.ask("prompt")
        self.assertEqual("env works", result)


if __name__ == "__main__":
    unittest.main()
