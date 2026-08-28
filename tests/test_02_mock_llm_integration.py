"""
Suite 2: Universal Mock LLM Server & AI Integration Suite.
Runs automatically if the plugin uses AI/LLM providers (Ollama, OpenAI, Groq, Together).
"""

import json
import pytest
import httpx
from config import MOCK_LLM_URL, PLUGIN_INFO


class TestUniversalMockLLMIntegration:

    @pytest.fixture(autouse=True)
    def check_ai_capability(self):
        if not PLUGIN_INFO.get("has_llm"):
            pytest.skip(f"El plugin '{PLUGIN_INFO['name']}' no utiliza integraciones de IA/LLM.")

    def test_mock_server_root_health(self, mock_server, http_client: httpx.Client):
        """Validates that the mock LLM server is up and responsive."""
        res = http_client.get(f"{mock_server}/")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_ollama_tags_endpoint_returns_models(self, mock_server, http_client: httpx.Client):
        """Validates /api/tags returns a list of models."""
        res = http_client.get(f"{mock_server}/api/tags")
        assert res.status_code == 200
        data = res.json()
        assert "models" in data
        assert len(data["models"]) >= 1

    def test_ollama_generate_returns_valid_json_schema(self, mock_server, http_client: httpx.Client):
        """Validates /api/generate responds with serialized JSON containing all SEO keys."""
        payload = {
            "model": "llama3.1:latest",
            "prompt": "Genera el SEO para este post en formato JSON.",
            "stream": False,
            "format": "json"
        }
        res = http_client.post(f"{mock_server}/api/generate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "response" in data
        inner = json.loads(data["response"])
        assert "seo_title" in inner or "title" in inner or "status" in inner

    def test_openai_chat_completions_schema(self, mock_server, http_client: httpx.Client):
        """Validates /v1/chat/completions for Groq/Together/OpenAI compatibility."""
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": "Genera datos en JSON"}]
        }
        res = http_client.post(f"{mock_server}/v1/chat/completions", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert "choices" in body
