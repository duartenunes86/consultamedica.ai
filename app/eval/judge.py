"""Claude-based answer scoring using tool_use for structured output."""

import anthropic

from app.config import get_settings


async def judge_medqa_answer(
    question: str,
    options: dict[str, str],
    correct_answer_idx: str,
    system_analysis: str,
) -> dict:
    """Judge whether the system's analysis matches the correct MedQA answer.

    Returns: {is_correct: bool, extracted_answer: str, reasoning: str}
    """
    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    correct_text = options[correct_answer_idx]
    option_lines = "\n".join(f"  {k}. {v}" for k, v in options.items())

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=(
            "You are a medical exam grader. You read an AI system's medical analysis "
            "and determine if it effectively identifies the correct answer to a USMLE-style question. "
            "The system does NOT directly pick an option letter — you must infer from its analysis "
            "which answer it most aligns with."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"QUESTION: {question}\n\n"
                f"OPTIONS:\n{option_lines}\n\n"
                f"CORRECT ANSWER: {correct_answer_idx}. {correct_text}\n\n"
                f"SYSTEM ANALYSIS:\n{system_analysis}\n\n"
                "Grade the system's analysis using the grading_result tool."
            ),
        }],
        tools=[{
            "name": "grading_result",
            "description": "Return the grading result for this medical question",
            "input_schema": {
                "type": "object",
                "properties": {
                    "is_correct": {
                        "type": "boolean",
                        "description": "Whether the system's analysis aligns with the correct answer",
                    },
                    "extracted_answer": {
                        "type": "string",
                        "description": "The answer option (A/B/C/D) the system's analysis most aligns with",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why the grading was assigned",
                    },
                },
                "required": ["is_correct", "extracted_answer", "reasoning"],
            },
        }],
        tool_choice={"type": "tool", "name": "grading_result"},
    )

    for block in response.content:
        if block.type == "tool_use":
            return block.input

    return {"is_correct": False, "extracted_answer": "?", "reasoning": "Judge failed to produce output"}


async def judge_pubmedqa_answer(
    question: str,
    correct_answer: str,
    system_analysis: str,
) -> dict:
    """Judge whether the system's analysis matches the correct PubMedQA answer (yes/no/maybe).

    Returns: {is_correct: bool, extracted_answer: str, reasoning: str}
    """
    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=(
            "You are a medical research grader. You read an AI system's analysis of a PubMedQA question "
            "and determine if the system's conclusion matches the correct answer (yes/no/maybe)."
        ),
        messages=[{
            "role": "user",
            "content": (
                f"QUESTION: {question}\n\n"
                f"CORRECT ANSWER: {correct_answer}\n\n"
                f"SYSTEM ANALYSIS:\n{system_analysis}\n\n"
                "Grade the system's analysis using the grading_result tool."
            ),
        }],
        tools=[{
            "name": "grading_result",
            "description": "Return the grading result for this PubMedQA question",
            "input_schema": {
                "type": "object",
                "properties": {
                    "is_correct": {
                        "type": "boolean",
                        "description": "Whether the system's conclusion matches the correct answer",
                    },
                    "extracted_answer": {
                        "type": "string",
                        "enum": ["yes", "no", "maybe"],
                        "description": "The answer the system's analysis most aligns with",
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why the grading was assigned",
                    },
                },
                "required": ["is_correct", "extracted_answer", "reasoning"],
            },
        }],
        tool_choice={"type": "tool", "name": "grading_result"},
    )

    for block in response.content:
        if block.type == "tool_use":
            return block.input

    return {"is_correct": False, "extracted_answer": "?", "reasoning": "Judge failed to produce output"}
