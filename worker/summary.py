"""RunPod worker specific summarisation helpers."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def extract_json_from_response(response: str) -> str:
    """Extract JSON from LLM response that may contain markdown or extra text."""
    # Try to find JSON in code blocks first
    code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
    if code_block_match:
        return code_block_match.group(1)
    
    # Try to find raw JSON object
    json_match = re.search(r'(\{[\s\S]*\})', response)
    if json_match:
        return json_match.group(1)
    
    return response


def parse_summary_response(response: str) -> Dict[str, Any]:
    """Parse LLM response into summary dict, with fallbacks."""
    try:
        extracted = extract_json_from_response(response)
        return json.loads(extracted)
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse LLM JSON response: %s", e)
        # Return a fallback structure
        return {
            "title": "Summary",
            "overview": response[:500] if len(response) > 500 else response,
            "sections": [{"title": "Content", "summary": response, "key_points": []}],
            "glossary": [],
            "follow_up_questions": [],
        }


UNDERSTANDING_LEVELS = {
    0: {
        "name": "Complete Novice",
        "description": "User has zero background in this topic",
        "guidance": (
            "The user is a COMPLETE NOVICE with NO prior knowledge. You MUST:\n"
            "- Define EVERY technical term and acronym, no matter how basic\n"
            "- Provide extensive background context before diving into details\n"
            "- Use real-world analogies and simple examples for every concept\n"
            "- Explain WHY things matter, not just what they are\n"
            "- Include a 'Prerequisites' section with foundational knowledge\n"
            "- Add many glossary entries (10+ terms)\n"
            "- Keep language simple and accessible"
        ),
    },
    1: {
        "name": "Beginner",
        "description": "User has minimal familiarity with the domain",
        "guidance": (
            "The user is a BEGINNER with minimal knowledge. You MUST:\n"
            "- Define most technical terms and all acronyms\n"
            "- Provide background context for complex concepts\n"
            "- Use analogies for abstract ideas\n"
            "- Explain the significance of key points\n"
            "- Include substantial glossary (6-10 terms)"
        ),
    },
    2: {
        "name": "Basic Understanding",
        "description": "User knows fundamentals but lacks depth",
        "guidance": (
            "The user has BASIC understanding of fundamentals. You should:\n"
            "- Define specialized terms and uncommon acronyms\n"
            "- Provide context for advanced concepts\n"
            "- Connect new information to foundational knowledge\n"
            "- Include moderate glossary (4-6 terms)"
        ),
    },
    3: {
        "name": "Intermediate",
        "description": "User has working knowledge of the topic",
        "guidance": (
            "The user has INTERMEDIATE knowledge. You should:\n"
            "- Define only niche or emerging terms\n"
            "- Focus on key takeaways and insights\n"
            "- Highlight what's novel or noteworthy\n"
            "- Include brief glossary (2-4 terms) for specialized terminology"
        ),
    },
    4: {
        "name": "Advanced",
        "description": "User is well-versed in this area",
        "guidance": (
            "The user has ADVANCED knowledge. You should:\n"
            "- Skip basic explanations entirely\n"
            "- Focus on technical details and implications\n"
            "- Highlight cutting-edge or controversial points\n"
            "- Minimal glossary (0-2 terms) only for highly specialized terms"
        ),
    },
    5: {
        "name": "Expert",
        "description": "User is an expert seeking quick reference",
        "guidance": (
            "The user is an EXPERT. You should:\n"
            "- Provide concise, dense summaries\n"
            "- Focus on data points, specifications, and actionable insights\n"
            "- No explanations of standard concepts\n"
            "- No glossary unless truly novel terminology\n"
            "- Prioritize brevity and precision"
        ),
    },
}


def build_summary_prompt(
    transcript: str,
    *,
    understanding_level: int,
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    applied_context = context or {}
    
    # Clamp understanding level to valid range
    level = max(0, min(5, understanding_level))
    level_info = UNDERSTANDING_LEVELS[level]
    
    guidance = (
        f"User's self-rated understanding: {level}/5 ({level_info['name']})\n"
        f"This means: {level_info['description']}\n\n"
        f"CRITICAL INSTRUCTIONS based on this level:\n{level_info['guidance']}"
    )

    json_schema = '''{
  "title": "string - concise title for this content",
  "overview": "string - 2-3 sentence overview",
  "sections": [
    {
      "title": "string - section title",
      "summary": "string - section summary",
      "key_points": ["string - key point 1", "string - key point 2"]
    }
  ],
  "glossary": [
    {"term": "string - technical term", "definition": "string - explanation"}
  ],
  "follow_up_questions": ["string - suggested question for deeper learning"]
}'''

    return [
        {
            "role": "system",
            "content": (
                "You are an expert technical note-taker. Given a transcript, craft a modular summary "
                "with clear sections, expand acronyms, explain jargon, and vary depth based on the "
                "listener's self-rated understanding (1=novice, 5=expert). "
                "IMPORTANT: Respond ONLY with valid JSON, no markdown, no explanation."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Understanding level: {understanding_level}/5\n"
                f"Guidance: {guidance}\n\n"
                f"Context: {json.dumps(applied_context)}\n\n"
                f"Transcript:\n{transcript[:8000]}\n\n"
                f"Respond with ONLY this JSON structure (no markdown, no ```json blocks):\n{json_schema}"
            ),
        },
    ]


def build_selection_prompt(section: Dict[str, Any], candidates: List[Any]) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an editorial assistant selecting images for a technical summary. Choose at most one "
                "image per section. Prefer images that visually reinforce the section's key ideas. If none are "
                "suitable, respond with 'NONE'."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Section Title: {section.get('title')}\n"
                f"Section Summary: {section.get('summary')}\n"
                f"Key Points: {section.get('key_points')}\n"
                "Candidates:\n"
                + "\n".join(
                    f"[{idx}] title={cand.title} url={cand.url} source={cand.source} snippet={cand.snippet}"
                    for idx, cand in enumerate(candidates)
                )
                + "\nRespond with the index of the best candidate or 'NONE'."
            ),
        },
    ]


def build_pending_result(summary_json: str, enriched_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary_data = json.loads(summary_json)
    summary_data["sections"] = enriched_sections
    return summary_data


async def summarise_with_vllm(
    transcript: str,
    *,
    understanding_level: int,
    context: Optional[Dict[str, Any]],
    model: str,
    llm_client,
) -> str:
    messages = build_summary_prompt(transcript, understanding_level=understanding_level, context=context)
    return await llm_client.complete(messages, model=model)


__all__ = [
    "build_summary_prompt",
    "build_selection_prompt",
    "extract_json_from_response",
    "parse_summary_response",
    "summarise_with_vllm",
]

