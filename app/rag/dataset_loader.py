"""Download and ingest MedQA / PubMedQA datasets into the RAG knowledge base."""

import logging

from datasets import load_dataset

from app.rag.ingest import ingest_text

logger = logging.getLogger(__name__)


def _format_medqa_doc(item: dict) -> str:
    """Format a MedQA item as a self-contained knowledge document."""
    question = item["question"]
    options = item["options"]
    answer_idx = item["answer_idx"]
    answer_text = options[answer_idx]

    option_lines = "\n".join(f"  {k}. {v}" for k, v in options.items())

    return (
        f"USMLE-STYLE MEDICAL QUESTION AND ANSWER\n\n"
        f"Question: {question}\n\n"
        f"Options:\n{option_lines}\n\n"
        f"Correct Answer: {answer_idx}. {answer_text}"
    )


def _format_pubmedqa_abstract(item: dict) -> str:
    """Format PubMedQA context as a standalone medical knowledge document."""
    contexts = item.get("context", {})
    labels = contexts.get("labels", [])
    meshes = contexts.get("meshes", [])
    texts = contexts.get("contexts", [])

    parts = []
    if meshes:
        parts.append(f"MeSH Terms: {', '.join(meshes)}")

    for label, text in zip(labels, texts):
        parts.append(f"[{label}] {text}")

    return "MEDICAL RESEARCH ABSTRACT\n\n" + "\n\n".join(parts) if parts else ""


def _format_pubmedqa_qa(item: dict) -> str:
    """Format PubMedQA as a full Q&A document with explanation."""
    question = item["question"]
    final_decision = item.get("final_decision", "")
    long_answer = item.get("long_answer", "")

    return (
        f"MEDICAL RESEARCH Q&A\n\n"
        f"Question: {question}\n\n"
        f"Answer: {final_decision}\n\n"
        f"Explanation: {long_answer}"
    )


def load_medqa(limit: int | None = None) -> int:
    """Download and ingest MedQA (USMLE 4-options) into RAG. Returns chunks ingested."""
    logger.info("Loading MedQA dataset from HuggingFace...")
    ds = load_dataset("GBaker/MedQA-USMLE-4-options", split="train")

    if limit is not None:
        ds = ds.select(range(min(limit, len(ds))))

    total_chunks = 0
    for item in ds:
        doc = _format_medqa_doc(item)
        total_chunks += ingest_text(doc, source="medqa")

    logger.info(f"MedQA: ingested {len(ds)} items ({total_chunks} chunks)")
    return total_chunks


def load_pubmedqa(limit: int | None = None) -> int:
    """Download and ingest PubMedQA (pqa_labeled) into RAG. Returns chunks ingested."""
    logger.info("Loading PubMedQA dataset from HuggingFace...")
    ds = load_dataset("qiaojin/PubMedQA", "pqa_labeled", split="train")

    if limit is not None:
        ds = ds.select(range(min(limit, len(ds))))

    total_chunks = 0
    for item in ds:
        # Ingest abstract as standalone medical knowledge
        abstract_doc = _format_pubmedqa_abstract(item)
        if abstract_doc:
            total_chunks += ingest_text(abstract_doc, source="pubmedqa_abstract")

        # Ingest full Q&A with explanation
        qa_doc = _format_pubmedqa_qa(item)
        total_chunks += ingest_text(qa_doc, source="pubmedqa_qa")

    logger.info(f"PubMedQA: ingested {len(ds)} items ({total_chunks} chunks)")
    return total_chunks


def load_dataset_into_rag(dataset: str, limit: int | None = None) -> dict:
    """Load a dataset (medqa, pubmedqa, or all) into the RAG knowledge base."""
    results = {}

    if dataset in ("medqa", "all"):
        results["medqa_chunks"] = load_medqa(limit)

    if dataset in ("pubmedqa", "all"):
        results["pubmedqa_chunks"] = load_pubmedqa(limit)

    results["total_chunks"] = sum(results.values())
    return results
