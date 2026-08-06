from __future__ import annotations

from dataclasses import replace
import unittest
from unittest.mock import patch

from core.config import load_settings, require_llm_credentials
from retrieval.llm import build_llm


class LLMTests(unittest.TestCase):
    def test_build_llm_supports_groq_openai_compatible_endpoint(self) -> None:
        settings = replace(
            load_settings(),
            llm_provider="groq",
            model_name="openai/gpt-oss-20b",
            groq_api_key="test-groq-key",
            groq_base_url="https://api.groq.com/openai/v1",
        )

        require_llm_credentials(settings)

        with patch("retrieval.llm.ChatOpenAI", return_value="groq-client") as mock_chat_openai:
            llm = build_llm(settings, temperature=0.2)

        self.assertEqual(llm, "groq-client")
        mock_chat_openai.assert_called_once_with(
            model="openai/gpt-oss-20b",
            api_key="test-groq-key",
            base_url="https://api.groq.com/openai/v1",
            temperature=0.2,
        )


if __name__ == "__main__":
    unittest.main()
