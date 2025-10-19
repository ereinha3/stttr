"""RunPod worker specific summarisation helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import json


def build_summary_prompt(
    transcript: str,
    *,
    understanding_level: int,
    context: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    applied_context = context or {}
    guidance = (
        "The user rated their understanding at {level}/5. "
        "If <=2, include extensive explanations, define acronyms, and add "
        "real-world analogies. If 3, provide moderate enrichment with key "
        "clarifications. If >=4, keep enrichment light and focus on formatted "
        "bullet summaries, call out only non-intuitive terms."
    ).format(level=understanding_level)

    instructions = (
        "Produce JSON with: overview, sections[], glossary[]. "
        "Each sections[] item must have title, summary, key_points[]. "
        "glossary[] should expand acronyms or niche terms with explanations. "
        "Add optional follow_up_questions[] if knowledge gaps remain. "
        "Respect combined length under 1200 tokens."
    )

    return [
        {
            "role": "system",
            "content": (
                "You are an expert technical note-taker. Given a transcript, craft a modular summary "
                "with clear sections, expand acronyms, explain jargon, and vary depth based on the "
                "listener's self-rated understanding (1=novice, 5=expert)."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Context: {applied_context}\n\n"
                f"Guidance: {guidance}\n\n"
                "Transcript:\n" + transcript
            ),
        },
        {"role": "assistant", "content": instructions},
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
    "summarise_with_vllm",
]

