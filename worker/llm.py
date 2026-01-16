"""Client for interacting with OpenAI-compatible chat completion APIs.

Supports: OpenAI, Groq, Together, vLLM, and any OpenAI-compatible endpoint.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified client for OpenAI-compatible LLM APIs."""
    
    def __init__(
        self,
        base_url: str,
        *,
        api_key: Optional[str] = None,
        timeout: float = 120.0,
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
        max_tokens: Optional[int] = 4096,
    ) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        logger.info("Sending request to %s with model %s", self.base_url, model)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
            )
        
        if response.status_code != 200:
            logger.error("LLM request failed: %s - %s", response.status_code, response.text[:500])
            response.raise_for_status()
            
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        logger.info("Received response with %d characters", len(content))
        return content


# Alias for backward compatibility
VLLMClient = LLMClient


def create_client_from_env() -> LLMClient:
    """Create an LLM client from environment variables."""
    from worker.settings import LLM_API_KEY, LLM_BASE_URL
    
    return LLMClient(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
    )


__all__ = ["LLMClient", "VLLMClient", "create_client_from_env"]

