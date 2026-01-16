import logging
from typing import List, Dict, Any, Optional

_reranker_model = None

def _get_reranker_model():
    global _reranker_model
    if _reranker_model is None:
        from sentence_transformers import CrossEncoder
        from .config import RERANKER_MODEL
        logging.info(f"Loading reranker model: {RERANKER_MODEL}")
        _reranker_model = CrossEncoder(RERANKER_MODEL)
        logging.info("Reranker model loaded successfully")
    return _reranker_model

def rerank_documents(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: Optional[int] = None
) -> List[Dict[str, Any]]:
    from .config import RERANKER_TOP_K

    if not documents:
        return documents

    if top_k is None:
        top_k = RERANKER_TOP_K

    model = _get_reranker_model()

    pairs = [(query, doc.get('content', '')) for doc in documents]

    scores = model.predict(pairs)

    scored_docs = []
    for doc, score in zip(documents, scores):
        doc_copy = doc.copy()
        doc_copy['rerank_score'] = float(score)
        scored_docs.append(doc_copy)

    scored_docs.sort(key=lambda x: x['rerank_score'], reverse=True)

    return scored_docs[:top_k] if top_k else scored_docs

def clear_model_cache():
    global _reranker_model
    _reranker_model = None
