import logging
import re
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi

def tokenize(text: str) -> List[str]:
    tokens = re.findall(r'\w+', text.lower())
    return tokens

def build_bm25_index(documents: Dict[str, Any]) -> Tuple[BM25Okapi, List[str]]:
    corpus = []
    doc_keys = []

    for key, doc in documents.items():
        content = doc.get('content', '') if isinstance(doc, dict) else doc
        tokens = tokenize(content)
        corpus.append(tokens)
        doc_keys.append(key)

    if not corpus:
        return None, []

    bm25 = BM25Okapi(corpus)
    return bm25, doc_keys

def bm25_search(
    query: str,
    bm25_index: BM25Okapi,
    doc_keys: List[str],
    top_k: int = 100
) -> List[Tuple[str, float]]:
    if bm25_index is None:
        return []

    query_tokens = tokenize(query)
    scores = bm25_index.get_scores(query_tokens)

    results = [(key, float(score)) for key, score in zip(doc_keys, scores)]
    results.sort(key=lambda x: x[1], reverse=True)

    return results[:top_k]

def reciprocal_rank_fusion(
    semantic_results: List[Tuple[str, float]],
    bm25_results: List[Tuple[str, float]],
    semantic_weight: float = 0.7,
    bm25_weight: float = 0.3,
    k: int = 60
) -> List[Tuple[str, float]]:
    fused_scores = {}

    for rank, (key, _) in enumerate(semantic_results, 1):
        rrf_score = semantic_weight * (1.0 / (k + rank))
        fused_scores[key] = fused_scores.get(key, 0) + rrf_score

    for rank, (key, _) in enumerate(bm25_results, 1):
        rrf_score = bm25_weight * (1.0 / (k + rank))
        fused_scores[key] = fused_scores.get(key, 0) + rrf_score

    results = [(key, score) for key, score in fused_scores.items()]
    results.sort(key=lambda x: x[1], reverse=True)

    return results

def hybrid_search(
    query: str,
    query_embedding: List[float],
    embeddings: Dict[str, Any],
    semantic_weight: float = 0.7,
    bm25_weight: float = 0.3,
    top_k: int = 100
) -> List[Tuple[str, float]]:
    from sklearn.metrics.pairwise import cosine_similarity
    from .config import SIMILARITY_THRESHOLD

    semantic_results = []
    for key, data in embeddings.items():
        similarity = cosine_similarity([query_embedding], [data['embedding']])[0][0]
        if similarity >= SIMILARITY_THRESHOLD:
            semantic_results.append((key, float(similarity)))
    semantic_results.sort(key=lambda x: x[1], reverse=True)

    bm25_index, doc_keys = build_bm25_index(embeddings)
    bm25_results = bm25_search(query, bm25_index, doc_keys, top_k=top_k * 2)

    fused = reciprocal_rank_fusion(
        semantic_results[:top_k * 2],
        bm25_results,
        semantic_weight=semantic_weight,
        bm25_weight=bm25_weight
    )

    return fused[:top_k]
