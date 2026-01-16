"""Vision processing module for image analysis and OCR.

Analyzes images using:
1. Tesseract OCR for text extraction
2. LLM for content understanding and description
3. Image metadata extraction
"""

from __future__ import annotations

import base64
import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image
import pytesseract

from worker.llm import LLMClient
from worker.settings import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

logger = logging.getLogger(__name__)


@dataclass
class ImageAnalysis:
    """Result of analyzing an image."""
    
    path: str
    filename: str
    hash: str
    width: int
    height: int
    format: str
    ocr_text: str
    description: str
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0
    is_slide: bool = False
    is_diagram: bool = False
    is_photo: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


def compute_image_hash(image_path: Path) -> str:
    """Compute SHA256 hash of image file."""
    return hashlib.sha256(image_path.read_bytes()).hexdigest()[:16]


def extract_ocr_text(image_path: Path) -> str:
    """Extract text from image using Tesseract OCR."""
    try:
        image = Image.open(image_path)
        # Use Tesseract with English language
        text = pytesseract.image_to_string(image, lang='eng')
        return text.strip()
    except Exception as e:
        logger.warning("OCR extraction failed for %s: %s", image_path, e)
        return ""


def get_image_metadata(image_path: Path) -> Dict[str, Any]:
    """Extract image metadata (dimensions, format, etc.)."""
    try:
        with Image.open(image_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format or "unknown",
                "mode": img.mode,
                "has_transparency": img.mode in ("RGBA", "LA", "P"),
            }
    except Exception as e:
        logger.warning("Failed to get metadata for %s: %s", image_path, e)
        return {"width": 0, "height": 0, "format": "unknown", "mode": "unknown"}


def build_image_analysis_prompt(
    ocr_text: str,
    metadata: Dict[str, Any],
    context: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Build prompt for LLM to analyze image based on OCR and metadata."""
    
    context_info = f"\nContext: {context}" if context else ""
    
    return [
        {
            "role": "system",
            "content": (
                "You are an image analysis assistant. Based on the OCR text extracted from an image "
                "and its metadata, provide a structured analysis. Determine if this is a slide, diagram, "
                "or photo, and extract key information. Respond with JSON only."
            ),
        },
        {
            "role": "user", 
            "content": (
                f"Analyze this image based on extracted text and metadata.{context_info}\n\n"
                f"Image dimensions: {metadata.get('width')}x{metadata.get('height')}\n"
                f"Format: {metadata.get('format')}\n\n"
                f"OCR Text:\n{ocr_text[:3000] if ocr_text else '(No text detected)'}\n\n"
                "Respond with JSON:\n"
                '{"description": "one paragraph describing the image content", '
                '"keywords": ["keyword1", "keyword2", ...], '
                '"is_slide": true/false, '
                '"is_diagram": true/false, '
                '"is_photo": true/false, '
                '"main_topic": "primary topic or subject", '
                '"confidence": 0.0-1.0}'
            ),
        },
    ]


async def analyze_image(
    image_path: Path,
    *,
    llm_client: Optional[LLMClient] = None,
    context: Optional[str] = None,
) -> ImageAnalysis:
    """Analyze a single image using OCR and LLM.
    
    Args:
        image_path: Path to the image file
        llm_client: Optional LLM client (creates one if not provided)
        context: Optional context about what the image might contain
        
    Returns:
        ImageAnalysis with extracted information
    """
    image_path = Path(image_path)
    
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Extract basic metadata
    metadata = get_image_metadata(image_path)
    image_hash = compute_image_hash(image_path)
    
    # Extract OCR text
    ocr_text = extract_ocr_text(image_path)
    
    # Use LLM to analyze
    if llm_client is None:
        llm_client = LLMClient(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    
    try:
        messages = build_image_analysis_prompt(ocr_text, metadata, context)
        response = await llm_client.complete(messages, model=LLM_MODEL)
        
        # Parse LLM response
        import json
        from worker.summary import extract_json_from_response
        
        try:
            analysis_data = json.loads(extract_json_from_response(response))
        except json.JSONDecodeError:
            analysis_data = {}
        
        return ImageAnalysis(
            path=str(image_path),
            filename=image_path.name,
            hash=image_hash,
            width=metadata.get("width", 0),
            height=metadata.get("height", 0),
            format=metadata.get("format", "unknown"),
            ocr_text=ocr_text,
            description=analysis_data.get("description", "Image content"),
            keywords=analysis_data.get("keywords", []),
            confidence=float(analysis_data.get("confidence", 0.5)),
            is_slide=bool(analysis_data.get("is_slide", False)),
            is_diagram=bool(analysis_data.get("is_diagram", False)),
            is_photo=bool(analysis_data.get("is_photo", False)),
            metadata=metadata,
        )
        
    except Exception as e:
        logger.warning("LLM analysis failed for %s: %s", image_path, e)
        # Return basic analysis without LLM
        return ImageAnalysis(
            path=str(image_path),
            filename=image_path.name,
            hash=image_hash,
            width=metadata.get("width", 0),
            height=metadata.get("height", 0),
            format=metadata.get("format", "unknown"),
            ocr_text=ocr_text,
            description=f"Image: {image_path.name}",
            keywords=[],
            confidence=0.3,
            is_slide=bool(ocr_text),  # If has text, likely a slide
            is_diagram=False,
            is_photo=not bool(ocr_text),
            metadata=metadata,
        )


async def analyze_images(
    image_paths: List[Path],
    *,
    llm_client: Optional[LLMClient] = None,
    context: Optional[str] = None,
) -> List[ImageAnalysis]:
    """Analyze multiple images.
    
    Args:
        image_paths: List of paths to image files
        llm_client: Optional shared LLM client
        context: Optional context about the images
        
    Returns:
        List of ImageAnalysis results
    """
    if llm_client is None:
        llm_client = LLMClient(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    
    results = []
    for path in image_paths:
        try:
            analysis = await analyze_image(path, llm_client=llm_client, context=context)
            results.append(analysis)
        except Exception as e:
            logger.error("Failed to analyze image %s: %s", path, e)
    
    return results


__all__ = [
    "ImageAnalysis",
    "analyze_image",
    "analyze_images",
    "extract_ocr_text",
    "get_image_metadata",
]

