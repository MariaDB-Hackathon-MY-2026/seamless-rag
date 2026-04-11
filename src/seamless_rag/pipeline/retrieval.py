"""Retrieval strategies — deterministic algorithms that don't need LLM judgment.

These sit between raw vector search and the final result:
  search() → [MMR / rerank] → results

Algorithms implemented:
- MMR (Maximal Marginal Relevance) — Carbonell & Goldstein 1998
  Standard algorithm used by LangChain, LlamaIndex, and most RAG frameworks.

Agent decides WHEN to use these. The algorithms themselves are fixed:
give parameters, get results. No judgment needed.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from seamless_rag.providers.protocol import EmbeddingProvider

logger = logging.getLogger(__name__)


def _cosine_similarity_matrix(
    query: np.ndarray, docs: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute cosine similarities: query-to-docs and docs-to-docs.

    Returns:
        (query_sims, doc_sim_matrix) — shapes (n,) and (n, n).
    """
    # Normalize
    query_norm = query / (np.linalg.norm(query) + 1e-10)
    norms = np.linalg.norm(docs, axis=1, keepdims=True) + 1e-10
    docs_norm = docs / norms

    query_sims = docs_norm @ query_norm  # (n,)
    doc_sims = docs_norm @ docs_norm.T   # (n, n)
    return query_sims, doc_sims


def mmr(
    query_vec: list[float],
    candidates: list[dict],
    candidate_vecs: list[list[float]],
    k: int = 5,
    lambda_mult: float = 0.5,
) -> list[dict]:
    """Maximal Marginal Relevance — balance relevance and diversity.

    Algorithm: Carbonell & Goldstein, "The Use of MMR, Diversity-Based
    Reranking for Reordering Documents and Producing Summaries", 1998.

    This is the standard MMR implementation used across the industry
    (LangChain, LlamaIndex, Haystack all use the same formula).

    Greedy selection: each step picks the candidate most relevant to the
    query but least similar to already-selected results.

    Args:
        query_vec: The query embedding vector.
        candidates: Search results (list of dicts).
        candidate_vecs: Embedding vectors for each candidate (same order).
        k: Number of results to return.
        lambda_mult: Trade-off — 1.0 = pure relevance, 0.0 = pure diversity.
            Default 0.5 balances both equally.

    Returns:
        Reordered subset of candidates maximizing diversity.
    """
    if len(candidates) <= k:
        return candidates

    q = np.array(query_vec, dtype=np.float32)
    docs = np.array(candidate_vecs, dtype=np.float32)
    query_sims, doc_sims = _cosine_similarity_matrix(q, docs)

    selected: list[int] = []
    remaining = set(range(len(candidates)))

    for _ in range(k):
        best_score = -np.inf
        best_idx = -1

        for idx in remaining:
            relevance = float(query_sims[idx])

            max_sim = float(np.max(doc_sims[idx, selected])) if selected else 0.0

            score = lambda_mult * relevance - (1 - lambda_mult) * max_sim

            if score > best_score:
                best_score = score
                best_idx = idx

        if best_idx >= 0:
            selected.append(best_idx)
            remaining.discard(best_idx)

    return [candidates[i] for i in selected]


def mmr_search(
    provider: EmbeddingProvider,
    storage: object,
    table: str,
    question: str,
    top_k: int = 5,
    fetch_k: int = 20,
    lambda_mult: float = 0.5,
    where: str = "",
) -> list[dict]:
    """Convenience: vector search + MMR in one call.

    Fetches fetch_k candidates via vector search, then applies MMR
    to select the top_k most diverse results.
    """
    query_vec = provider.embed(question)

    candidates = storage.search(
        table, query_vec, top_k=fetch_k, where=where,
    )

    if len(candidates) <= top_k:
        return candidates

    # Re-embed candidates for MMR diversity calculation
    # Use 'content' if present (default chunks table), otherwise concatenate all text values
    def _candidate_text(c: dict) -> str:
        if "content" in c:
            return c["content"]
        # For custom tables: join all non-numeric, non-id string values
        parts = [str(v) for k, v in c.items()
                 if k not in ("id", "distance", "embedding") and v is not None]
        return " — ".join(parts) if parts else str(c)

    texts = [_candidate_text(c) for c in candidates]
    candidate_vecs = provider.embed_batch(texts)

    return mmr(query_vec, candidates, candidate_vecs, k=top_k, lambda_mult=lambda_mult)
