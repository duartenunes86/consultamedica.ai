"""Evaluation orchestration — benchmark the system against MedQA / PubMedQA."""

import asyncio
import json
import logging
import random

from datasets import load_dataset

from app.agents.consensus import build_consensus
from app.agents.diagnosis import DiagnosisAgent
from app.agents.drug_interaction import DrugInteractionAgent
from app.agents.treatment import TreatmentAgent
from app.agents.triage import TriageAgent
from app.eval.judge import judge_medqa_answer, judge_pubmedqa_answer
from app.eval.schemas import BenchmarkConfig, BenchmarkResult, QuestionResult
from app.rag.vector_store import format_rag_context, query_medical_knowledge

logger = logging.getLogger(__name__)


async def _run_consultation(message: str) -> dict:
    """Run the full agent pipeline on a message. Returns consensus result dict."""
    rag_docs = query_medical_knowledge(message)
    rag_context, citations = format_rag_context(rag_docs)

    context = {
        "medical_history": [],
        "current_medications": [],
        "rag_context": rag_context,
        "drug_info": "",
    }

    triage_result, diagnosis_result, treatment_result, drug_result = await asyncio.gather(
        TriageAgent().analyze(message, context),
        DiagnosisAgent().analyze(message, context),
        TreatmentAgent().analyze(message, context),
        DrugInteractionAgent().analyze(message, context),
    )

    consensus = await build_consensus(
        triage=triage_result,
        diagnosis=diagnosis_result,
        treatment=treatment_result,
        drug_interactions=drug_result,
        citations=citations,
    )

    return consensus


async def _evaluate_medqa_question(item: dict) -> QuestionResult:
    """Evaluate a single MedQA question."""
    question = item["question"]
    options = item["options"]
    answer_idx = item["answer_idx"]
    correct_text = options[answer_idx]

    consensus = await _run_consultation(question)

    judge_result = await judge_medqa_answer(
        question=question,
        options=options,
        correct_answer_idx=answer_idx,
        system_analysis=consensus.summary,
    )

    return QuestionResult(
        question=question,
        ground_truth=f"{answer_idx}. {correct_text}",
        system_answer=judge_result.get("extracted_answer", "?"),
        is_correct=judge_result.get("is_correct", False),
        judge_reasoning=judge_result.get("reasoning", ""),
        confidence=consensus.confidence,
        urgency=consensus.urgency.value,
    )


async def _evaluate_pubmedqa_question(item: dict) -> QuestionResult:
    """Evaluate a single PubMedQA question."""
    question = item["question"]
    correct_answer = item.get("final_decision", "")

    consensus = await _run_consultation(question)

    judge_result = await judge_pubmedqa_answer(
        question=question,
        correct_answer=correct_answer,
        system_analysis=consensus.summary,
    )

    return QuestionResult(
        question=question,
        ground_truth=correct_answer,
        system_answer=judge_result.get("extracted_answer", "?"),
        is_correct=judge_result.get("is_correct", False),
        judge_reasoning=judge_result.get("reasoning", ""),
        confidence=consensus.confidence,
        urgency=consensus.urgency.value,
    )


def _compute_metrics(results: list[QuestionResult], dataset: str) -> BenchmarkResult:
    """Compute aggregate metrics from per-question results."""
    n = len(results)
    correct = [r for r in results if r.is_correct]
    incorrect = [r for r in results if not r.is_correct]

    accuracy = len(correct) / n if n else 0.0
    avg_confidence = sum(r.confidence for r in results) / n if n else 0.0
    avg_correct_conf = sum(r.confidence for r in correct) / len(correct) if correct else 0.0
    avg_incorrect_conf = sum(r.confidence for r in incorrect) / len(incorrect) if incorrect else 0.0

    # False emergency rate: questions marked emergency/urgent that are routine medical knowledge questions
    emergency_count = sum(1 for r in results if r.urgency in ("emergency", "urgent"))
    false_emergency_rate = emergency_count / n if n else 0.0

    return BenchmarkResult(
        dataset=dataset,
        num_questions=n,
        accuracy=round(accuracy, 4),
        avg_confidence=round(avg_confidence, 4),
        avg_correct_confidence=round(avg_correct_conf, 4),
        avg_incorrect_confidence=round(avg_incorrect_conf, 4),
        false_emergency_rate=round(false_emergency_rate, 4),
        results=results,
    )


async def run_benchmark(config: BenchmarkConfig) -> BenchmarkResult:
    """Run a full benchmark evaluation."""
    logger.info(f"Starting benchmark: dataset={config.dataset}, n={config.num_questions}, seed={config.seed}")

    rng = random.Random(config.seed)

    if config.dataset == "medqa":
        ds = load_dataset("GBaker/MedQA-USMLE-4-options", split="test")
        indices = rng.sample(range(len(ds)), min(config.num_questions, len(ds)))
        samples = ds.select(indices)

        results = []
        for i, item in enumerate(samples):
            logger.info(f"[{i+1}/{len(samples)}] Evaluating MedQA question...")
            result = await _evaluate_medqa_question(item)
            results.append(result)

    elif config.dataset == "pubmedqa":
        ds = load_dataset("qiaojin/PubMedQA", "pqa_labeled", split="train")
        indices = rng.sample(range(len(ds)), min(config.num_questions, len(ds)))
        samples = ds.select(indices)

        results = []
        for i, item in enumerate(samples):
            logger.info(f"[{i+1}/{len(samples)}] Evaluating PubMedQA question...")
            result = await _evaluate_pubmedqa_question(item)
            results.append(result)

    else:
        raise ValueError(f"Unknown dataset: {config.dataset}")

    return _compute_metrics(results, config.dataset)
