from app.rag.embeddings import get_collection


def query_medical_knowledge(query: str, n_results: int = 5) -> list[dict]:
    """Query the medical knowledge vector store for relevant context."""
    collection = get_collection()
    if collection is None or collection.count() == 0:
        return []

    results = collection.query(query_texts=[query], n_results=min(n_results, collection.count()))

    documents = []
    for i, doc in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
        distance = results["distances"][0][i] if results["distances"] else None
        documents.append({
            "text": doc,
            "source": metadata.get("source", "unknown"),
            "relevance": 1 - distance if distance is not None else 0,
        })
    return documents


def format_rag_context(documents: list[dict]) -> tuple[str, list[str]]:
    """Format retrieved documents into a context string and citations list."""
    if not documents:
        return "", []

    context_parts = []
    citations = []
    for doc in documents:
        context_parts.append(doc["text"])
        source = doc.get("source", "unknown")
        if source not in citations:
            citations.append(source)

    return "\n\n---\n\n".join(context_parts), citations
