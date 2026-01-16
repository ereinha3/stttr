"""Image search and selection utilities for the worker."""

from __future__ import annotations

import hashlib
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

from .settings import OPENSERP_BASE_URL
from .summary import build_selection_prompt

DEFAULT_IMAGE_DIR = "images"


@dataclass
class ImageCandidate:
    title: str
    url: str
    source: str
    thumbnail: Optional[str]
    snippet: Optional[str]


async def search_images(
    query: str,
    *,
    num_results: int = 5,
    base_url: Optional[str] = None,
) -> List[ImageCandidate]:
    resolved_base = base_url or OPENSERP_BASE_URL
    endpoint = resolved_base.rstrip("/") + "/mega/image"

    params = {"text": query, "limit": num_results}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, params=params)
        response.raise_for_status()
        payload = response.json()
    except (httpx.ConnectError, httpx.HTTPStatusError, httpx.TimeoutException) as e:
        # Image search is optional - return empty list if service unavailable
        import logging
        logging.getLogger(__name__).warning("Image search unavailable: %s", e)
        return []

    results: List[ImageCandidate] = []
    for item in payload[:num_results]:
        results.append(
            ImageCandidate(
                title=item.get("title", ""),
                url=item.get("image", ""),
                source=item.get("url", ""),
                thumbnail=item.get("thumbnail"),
                snippet=item.get("description"),
            )
        )

    return results


async def score_images_with_llm(
    *,
    section: Dict[str, Any],
    candidates: List[ImageCandidate],
    llm_client,
    model: str,
) -> Optional[ImageCandidate]:
    if not candidates:
        return None

    messages = build_selection_prompt(section, candidates)
    decision = await llm_client.complete(messages, model=model, temperature=0.0)
    decision = decision.strip().upper()
    if decision == "NONE":
        return None

    try:
        index = int(decision.split()[0])
    except ValueError:
        return None

    if 0 <= index < len(candidates):
        return candidates[index]
    return None


async def download_image(
    url: str,
    *,
    dest_dir: str = DEFAULT_IMAGE_DIR,
    timeout: float = 20.0,
) -> Tuple[str, Optional[str]]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme for image download: {url}")

    destination = Path(dest_dir)
    destination.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url)
    response.raise_for_status()

    content_type = response.headers.get("content-type")
    extension = None
    if content_type:
        extension = mimetypes.guess_extension(content_type.split(";")[0].strip())
    if not extension:
        extension = Path(parsed.path).suffix or ".jpg"

    filename = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24] + extension
    file_path = destination / filename
    file_path.write_bytes(response.content)

    return str(file_path), content_type


async def suggest_images_for_sections(
    sections: List[Dict[str, Any]],
    *,
    num_results: int = 5,
    base_url: Optional[str] = None,
    download: bool = False,
    image_dir: str = DEFAULT_IMAGE_DIR,
    llm_client,
    model: str,
) -> List[Dict[str, Any]]:
    enriched_sections: List[Dict[str, Any]] = []

    for section in sections:
        query = f"{section.get('title', '')} {section.get('summary', '')}".strip()
        candidates = await search_images(query, num_results=num_results, base_url=base_url)
        chosen = await score_images_with_llm(
            section=section,
            candidates=candidates,
            llm_client=llm_client,
            model=model,
        )
        section_copy = {**section}
        if chosen:
            payload: Dict[str, Any] = {
                "title": chosen.title,
                "url": chosen.url,
                "source": chosen.source,
                "thumbnail": chosen.thumbnail,
            }
            if download:
                try:
                    local_path, content_type = await download_image(chosen.url, dest_dir=image_dir)
                    payload.update({"local_path": local_path, "content_type": content_type})
                except Exception as exc:
                    payload["download_error"] = str(exc)
            section_copy["image"] = payload
        enriched_sections.append(section_copy)

    return enriched_sections


__all__ = [
    "ImageCandidate",
    "search_images",
    "score_images_with_llm",
    "download_image",
    "suggest_images_for_sections",
]

