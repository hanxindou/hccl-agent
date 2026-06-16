"""Agent Prompt Engine — loads, fills, and logs Prompt templates.

Reads prompt templates from prompts/*.txt, substitutes runtime parameters
into {placeholders}, and logs every filled prompt so the Agent generation
process is fully traceable — satisfying the competition's requirement for
Prompt call records.
"""

import json
import os
import time
from datetime import datetime


class AgentPromptEngine:
    """Load prompt templates, fill placeholders, log the result."""

    def __init__(self, prompts_dir=None):
        if prompts_dir is None:
            prompts_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "prompts",
            )
        self.prompts_dir = prompts_dir
        self.log_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "logs",
        )
        os.makedirs(self.log_dir, exist_ok=True)

        self.prompt_log_path = os.path.join(
            self.log_dir, "prompt_calls.jsonl"
        )

    # ------------------------------------------------------------------
    # Template loading
    # ------------------------------------------------------------------

    def load_template(self, template_name):
        """Load a raw template file.

        Parameters
        ----------
        template_name : str
            Filename under prompts/, e.g. 'algorithm_prompt.txt'.

        Returns
        -------
        str — the raw template text with {placeholders} intact.
        """
        path = os.path.join(self.prompts_dir, template_name)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Prompt template not found: {path}"
            )
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # ------------------------------------------------------------------
    # Parameter filling
    # ------------------------------------------------------------------

    def fill_template(self, template_text, params):
        """Substitute {key} placeholders with values from *params* dict.

        Missing keys are left as-is (not replaced) so they are visible
        in the log.
        """
        # Use safe format_map that leaves missing keys untouched.
        class SafeDict(dict):
            def __missing__(self, key):
                return "{" + key + "}"

        return template_text.format_map(SafeDict(params))

    def build_algorithm_selection_prompt(self, params):
        """Fill the algorithm-selection prompt (section 1 of the prompt
        file).

        Expected params keys:
            primitive, nodes, message_size, topology,
            bandwidth_gbps, latency_ms, device_type
        """
        template = self._extract_section(
            "algorithm_prompt.txt",
            "## 1. 算法选择 Prompt",
            "---",
        )
        if template is None:
            # Fallback: use the whole file for now.
            template = self.load_template("algorithm_prompt.txt")

        filled = self.fill_template(template, params)
        self._log_prompt_call("algorithm_selection", params, filled)
        return filled

    def build_code_generation_prompt(self, params):
        """Fill the code-generation prompt (section 2).

        Expected params keys:
            algorithm, primitive, nodes, message_size,
            topology, precision
        """
        template = self._extract_section(
            "algorithm_prompt.txt",
            "## 2. 代码生成 Prompt",
            "---",
        )
        if template is None:
            template = self.load_template("algorithm_prompt.txt")

        filled = self.fill_template(template, params)
        self._log_prompt_call("code_generation", params, filled)
        return filled

    def build_test_generation_prompt(self, params):
        """Fill the test-generation prompt (section 3)."""
        template = self._extract_section(
            "algorithm_prompt.txt",
            "## 3. 测试用例生成 Prompt",
            "---",
        )
        if template is None:
            template = self.load_template("algorithm_prompt.txt")

        filled = self.fill_template(template, params)
        self._log_prompt_call("test_generation", params, filled)
        return filled

    def build_performance_analysis_prompt(self, params):
        """Fill the performance-analysis prompt (section 4)."""
        template = self._extract_section(
            "algorithm_prompt.txt",
            "## 4. 性能分析 Prompt",
            "---",
        )
        if template is None:
            template = self.load_template("algorithm_prompt.txt")

        filled = self.fill_template(template, params)
        self._log_prompt_call("performance_analysis", params, filled)
        return filled

    def build_reliability_prompt(self, params):
        """Fill the reliability prompt (section 5)."""
        template = self._extract_section(
            "algorithm_prompt.txt",
            "## 5. 可靠性机制生成 Prompt",
            "---",
        )
        if template is None:
            template = self.load_template("algorithm_prompt.txt")

        filled = self.fill_template(template, params)
        self._log_prompt_call("reliability", params, filled)
        return filled

    # ------------------------------------------------------------------
    # Section extraction helper
    # ------------------------------------------------------------------

    def _extract_section(self, template_name, start_marker, end_marker):
        """Extract a section between *start_marker* and *end_marker*.

        Returns the text between them (excluding the markers), or None
        if the markers aren't found.
        """
        try:
            raw = self.load_template(template_name)
        except FileNotFoundError:
            return None

        start_idx = raw.find(start_marker)
        if start_idx == -1:
            return None
        start_idx += len(start_marker)
        # Skip the newline after marker.
        if raw[start_idx:start_idx + 1] == "\n":
            start_idx += 1

        end_idx = raw.find(end_marker, start_idx)
        if end_idx == -1:
            # Take everything until EOF.
            section = raw[start_idx:]
        else:
            section = raw[start_idx:end_idx]

        return section.strip()

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_prompt_call(self, prompt_type, params, filled_prompt):
        """Record a prompt call to logs/prompt_calls.jsonl."""
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "unix_time": time.time(),
            "prompt_type": prompt_type,
            "parameters": params,
            "filled_prompt": filled_prompt,
        }
        with open(self.prompt_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_call_count(self):
        """Return the number of logged prompt calls."""
        if not os.path.exists(self.prompt_log_path):
            return 0
        count = 0
        with open(self.prompt_log_path, "r", encoding="utf-8") as f:
            for _ in f:
                count += 1
        return count
