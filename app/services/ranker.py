from typing import List, Dict, TypedDict
from app.services.bm25 import BM25
from app.services.vector_search import VectorSearch
from app.services.tokenizer import tokenize_lexical

class RankerResult(TypedDict):
    doc_id: str
    combined_score: float
    bm25_score: float
    vector_score: float

class Ranker:
    def __init__(self, dataset_id: str, bm25: BM25, vector_search: VectorSearch, W_b: float = 1.0, W_v: float = 1.0) -> None:
        """Initialize the Ranker.

        Args:
            dataset_id (str): The dataset identifier.
            bm25 (BM25): The BM25 instance.
            vector_search (VectorSearch): The VectorSearch instance.
            W_b (float, optional): Weight for BM25 scores. Defaults to 1.0.
            W_v (float, optional): Weight for Vector Search scores. Defaults to 1.0.
        """
        self.dataset_id = dataset_id
        self.bm25 = bm25
        self.vector_search = vector_search

        self.W_b = W_b
        self.W_v = W_v

    def rank(self, query: str, k: int) -> List[RankerResult]:
        """Rank documents based on a combination of BM25 and Vector Search scores.

        Args:
            query (str): The search query.
            k (int): Number of top results to return.
        Returns:
            List[Dict]: A list of ranked document ids with their scores.
        """
        query_tokens = tokenize_lexical(query)

        bm25_results = self.bm25.search(query_tokens, top_k=3 * k)
        vector_results = self.vector_search.search(query, top_k=k)

        bm25_scores = {res["id"]: res["score"] for res in bm25_results}
        vector_scores = {res["id"]: res["vector_score"] for res in vector_results}

        candidate_doc_ids = set(bm25_scores) | set(vector_scores)

        if not candidate_doc_ids:
            return []

        results = []
        for doc_id in sorted(candidate_doc_ids):
            bm25_score = bm25_scores.get(doc_id, 0.0)
            vector_score = vector_scores.get(doc_id, 0.0)

            combined_score = (
                self.W_b * bm25_score +
                self.W_v * vector_score
            )

            results.append({
                "id": doc_id,
                "combined_score": combined_score,
                "bm25_score": bm25_score,
                "vector_score": vector_score
            })

        # Deterministic ordering for score ties across different Python processes.
        results.sort(
            key=lambda x: (
                -x["combined_score"],
                -x["bm25_score"],
                -x["vector_score"],
                str(x["id"]),
            )
        )
        return results[:k]