"""LLM Client — lightweight DeepSeek API wrapper via OpenAI-compatible API.

Uses only the ``requests`` standard library replacement (or built-in
``urllib``).  The API key is read from the ``DEEPSEEK_API_KEY``
environment variable — never hard-coded.

Usage::

    client = LLMClient()
    answer = client.ask("What is Ring AllReduce?")
"""

import json
import os
import urllib.request
import urllib.error


class LLMClient:
    """Minimal OpenAI-compatible chat-completion client for DeepSeek."""

    BASE_URL = "https://api.deepseek.com/v1/chat/completions"
    MODEL    = "deepseek-chat"

    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if base_url is not None:
            self.BASE_URL = base_url
        if model is not None:
            self.MODEL = model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ask(self, prompt, system_prompt=None):
        """Send a chat-completion request and return the model's text reply.

        Parameters
        ----------
        prompt : str
            The user message.
        system_prompt : str or None
            Optional system-level instruction.

        Returns
        -------
        str — the model's text answer.

        Raises
        ------
        ValueError
            If ``DEEPSEEK_API_KEY`` is not set.
        RuntimeError
            On HTTP or API-level errors.
        """
        if not self.api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY environment variable is not set.\n"
                "  export DEEPSEEK_API_KEY=sk-..."
            )
        
        print("\n[LLM] Calling DeepSeek...")
        print(f"[LLM] Model: {self.MODEL}")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": self.MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 512,
        }).encode("utf-8")

        req = urllib.request.Request(
            self.BASE_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(
                f"[LLM] HTTP Status: {resp.status}"
                )

                data = json.loads(
                    resp.read().decode("utf-8")
                )

                print(
                    "[LLM] Response received."
                )
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"DeepSeek API HTTP {e.code}: {e.reason}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"DeepSeek API connection error: {e.reason}"
            ) from e

        # Extract the first choice's message content.
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(
                "DeepSeek API returned no choices."
            )

        answer = choices[0]["message"]["content"]

        print(
            f"[LLM] Reply length: {len(answer)} chars"
        )

        return answer
