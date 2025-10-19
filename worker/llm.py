"""Client for interacting with a vLLM-hosted chat completion API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx


class VLLMClient:
    def __init__(
        self,
        base_url: str,
        *,
        api_key: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        model: str,
        temperature: float = 0.2,
    ) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


__all__ = ["VLLMClient"]

