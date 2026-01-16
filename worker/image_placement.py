"""Image placement logic for matching images to document sections.

Uses LLM to determine the best placement for each image based on:
- Image content (OCR text, description, keywords)
- Section content (title, summary, key points)
- Relevance scoring
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from worker.llm import LLMClient
from worker.settings import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
from worker.summary import extract_json_from_response
from worker.vision import ImageAnalysis

logger = logging.getLogger(__name__)


@dataclass
class ImagePlacement:
    """Represents an image placement decision."""
    
    image: ImageAnalysis
    section_index: int
    section_title: str
    relevance_score: float
    placement_reason: str


def build_placement_prompt(
    images: List[ImageAnalysis],
    sections: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """Build prompt for LLM to determine optimal image placements."""
    
    # Format images for the prompt
    images_desc = []
    for i, img in enumerate(images):
        images_desc.append(
            f"[Image {i}] {img.filename}\n"
            f"  Type: {'slide' if img.is_slide else 'diagram' if img.is_diagram else 'photo'}\n"
            f"  Description: {img.description[:200]}\n"
            f"  Keywords: {', '.join(img.keywords[:5])}\n"
            f"  OCR Text: {img.ocr_text[:150]}..." if img.ocr_text else ""
        )
    
    # Format sections for the prompt
    sections_desc = []
    for i, sec in enumerate(sections):
        key_points = sec.get("key_points", [])
        sections_desc.append(
            f"[Section {i}] {sec.get('title', 'Untitled')}\n"
            f"  Summary: {sec.get('summary', '')[:200]}\n"
            f"  Key Points: {', '.join(str(p)[:50] for p in key_points[:3])}"
        )
    
    return [
        {
            "role": "system",
            "content": (
                "You are a document layout assistant. Your task is to match images to document sections "
                "based on content relevance. Each image should be placed in the section where it best "
                "illustrates or supports the content. An image can only be placed in one section. "
                "Some images may not fit any section well - assign them relevance_score < 0.3 to exclude them. "
                "Respond with JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                "Match these images to the most relevant sections.\n\n"
                "IMAGES:\n" + "\n".join(images_desc) + "\n\n"
                "SECTIONS:\n" + "\n".join(sections_desc) + "\n\n"
                "Respond with JSON array:\n"
                '[{"image_index": 0, "section_index": 0, "relevance_score": 0.0-1.0, "reason": "why this image fits this section"}, ...]'
            ),
        },
    ]


async def determine_image_placements(
    images: List[ImageAnalysis],
    sections: List[Dict[str, Any]],
    *,
    llm_client: Optional[LLMClient] = None,
    min_relevance: float = 0.3,
) -> List[ImagePlacement]:
    """Determine optimal placement for each image in the document.
    
    Args:
        images: List of analyzed images
        sections: List of document sections
        llm_client: Optional LLM client
        min_relevance: Minimum relevance score to include an image
        
    Returns:
        List of ImagePlacement decisions
    """
    if not images or not sections:
        return []
    
    if llm_client is None:
        llm_client = LLMClient(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    
    try:
        messages = build_placement_prompt(images, sections)
        response = await llm_client.complete(messages, model=LLM_MODEL)
        
        # Parse response
        placements_data = json.loads(extract_json_from_response(response))
        
        placements = []
        for p in placements_data:
            img_idx = p.get("image_index", 0)
            sec_idx = p.get("section_index", 0)
            score = float(p.get("relevance_score", 0))
            
            if img_idx >= len(images) or sec_idx >= len(sections):
                continue
            
            if score >= min_relevance:
                placements.append(ImagePlacement(
                    image=images[img_idx],
                    section_index=sec_idx,
                    section_title=sections[sec_idx].get("title", "Untitled"),
                    relevance_score=score,
                    placement_reason=p.get("reason", ""),
                ))
        
        # Sort by section index for ordered placement
        placements.sort(key=lambda x: (x.section_index, -x.relevance_score))
        
        return placements
        
    except Exception as e:
        logger.error("Failed to determine image placements: %s", e)
        # Fallback: distribute images evenly across sections
        return fallback_placement(images, sections, min_relevance)


def fallback_placement(
    images: List[ImageAnalysis],
    sections: List[Dict[str, Any]],
    min_relevance: float = 0.3,
) -> List[ImagePlacement]:
    """Fallback placement strategy when LLM fails.
    
    Places slides in order, photos distributed across sections.
    """
    placements = []
    
    # Separate slides from photos
    slides = [img for img in images if img.is_slide]
    photos = [img for img in images if img.is_photo or img.is_diagram]
    
    # Place slides in order (assuming they follow presentation order)
    for i, img in enumerate(slides):
        sec_idx = min(i, len(sections) - 1)
        placements.append(ImagePlacement(
            image=img,
            section_index=sec_idx,
            section_title=sections[sec_idx].get("title", "Untitled"),
            relevance_score=0.5,  # Default relevance
            placement_reason="Slide placed in order",
        ))
    
    # Distribute photos across sections
    if photos and sections:
        photos_per_section = max(1, len(photos) // len(sections))
        for i, img in enumerate(photos):
            sec_idx = min(i // photos_per_section, len(sections) - 1)
            placements.append(ImagePlacement(
                image=img,
                section_index=sec_idx,
                section_title=sections[sec_idx].get("title", "Untitled"),
                relevance_score=0.4,
                placement_reason="Photo distributed across sections",
            ))
    
    return placements


def apply_placements_to_sections(
    sections: List[Dict[str, Any]],
    placements: List[ImagePlacement],
) -> List[Dict[str, Any]]:
    """Apply image placements to sections, adding image references.
    
    Args:
        sections: Original sections
        placements: Image placement decisions
        
    Returns:
        Sections with images added
    """
    # Create a copy of sections
    enriched = [dict(sec) for sec in sections]
    
    # Initialize images list for each section
    for sec in enriched:
        if "images" not in sec:
            sec["images"] = []
    
    # Add images to their assigned sections
    for placement in placements:
        if 0 <= placement.section_index < len(enriched):
            enriched[placement.section_index]["images"].append({
                "path": placement.image.path,
                "filename": placement.image.filename,
                "description": placement.image.description,
                "relevance_score": placement.relevance_score,
                "placement_reason": placement.placement_reason,
                "is_slide": placement.image.is_slide,
                "is_diagram": placement.image.is_diagram,
                "is_photo": placement.image.is_photo,
            })
    
    return enriched


__all__ = [
    "ImagePlacement",
    "determine_image_placements",
    "apply_placements_to_sections",
    "fallback_placement",
]

