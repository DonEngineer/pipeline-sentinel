"""Chat model client backed by Ollama."""

from __future__ import annotations

from langchain_ollama import ChatOllama


class OllamaChat:
    """Thin wrapper over ChatOllama with a simple ``invoke(prompt) -> str`` interface."""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self.model = model
        self.base_url = base_url
        self._client = ChatOllama(model=model, base_url=base_url)

    def invoke(self, prompt: str) -> str:
        """Send a prompt; return the model's text response."""
        return str(self._client.invoke(prompt).content)
