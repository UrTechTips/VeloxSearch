import math
from typing import List, Optional
from app.services.inverted_index import InvertedIndex as II

class BM25:
    def __init__(self, index: II, k: Optional[float] = 1.2, b: Optional[float] = 0.75):
        """BM25 Scoring Algorithm Implementation

        Args:
            index (II): Inverted Index instance
            k (Optional[float], optional): BM25 k parameter. Defaults to 1.2.
            b (Optional[float], optional): BM25 b parameter. Defaults to 0.75.

        Methods:
            compute_bm25(query_tokens): Compute BM25 Scores for all documents in the index
            search(query_tokens, top_k): Search Top K Documents based on BM25 Scores
        """
        self.k = k
        self.b = b
        self.index = index

        self.avg_doc_length = self.index.get_average_doc_length()
        self.idf = {}

    def _compute_idf(self, token: str) -> float:
        """Compute IDF Value

        Args:
            doc_id (str): Document ID
            token (str): token

        Returns:
            float: idf value
        """
        N = self.index.get_total_docs() # Total number of documents
        documents = self.index.get_index().get(token, [])
        nt = len(documents) if documents else 0 # No. of documents containing the term

        IDF = math.log(1 + (N - nt + 0.5) / (nt + 0.5))
        return IDF
    
    def _compute_tf(self, term_freq: int, doc_length: int, avg_doc_length: float) -> float:
        """Compute the Term Frequency Value

        Args:
            term_freq (int): _description_
            doc_length (int): _description_
            avg_doc_length (float): _description_

        Returns:
            float: _description_
        """
        if avg_doc_length == 0 or doc_length == 0:
            return 0.0
        denominator = term_freq + self.k * (1 - self.b + self.b * (doc_length / avg_doc_length))
        if denominator == 0:
            return 0.0
        tf = (term_freq) / denominator
        return tf

    def _compute_bm25_per_document(self, doc_id: str, query_tokens: List[str]) -> float:
        """Compute the BM25 Score for input tokens

        Args:
            doc_id (str): Document ID
            query_tokens (List[str]): Query Tokens

        Returns:
            float: BM25 Score
        """
        doc_length = self.index.get_doc_length(doc_id)
        score = 0
        for token in query_tokens:
            term_freq = self.index.get_term_frequencies(token).get(doc_id, 0)

            tf = self._compute_tf(term_freq, doc_length, self.avg_doc_length)  
            idf = self.idf[token]
            score += tf * idf
            
        return score
    
    def compute_bm25(self, query_tokens: List[str]) -> List[dict]:
        """Compute BM25 Scores for all documents in the index

        Args:
            query_tokens (List[str]): Query Tokens

        Returns:
            List[dict]: List of documents with their BM25 scores
        """
        for token in query_tokens:
            if token not in self.idf.keys():
                self.idf[token] = self._compute_idf(token)
        
        results = []
        for doc_id in self.index.get_doc_lengths().keys():
            score = self._compute_bm25_per_document(doc_id, query_tokens)
            results.append({
                "id": doc_id,
                "score": score
            })
        results.sort(key=lambda x: x['score'], reverse=True)
        return self._normalize_scores(results)

    def search(self, query_tokens: List[str], top_k: int) -> List[dict[str, float]]:
        """Search Top K Documents based on BM25 Scores

        Args:
            query_tokens (List[str]): Query Tokens
            top_k (int): Number of top results to return

        Returns:
            List[dict]: List of top K documents with their BM25 scores
        """
        if not query_tokens:
            return []

        valid_tokens = [
            t for t in query_tokens
            if self.index.term_exists(t)
        ]

        if not valid_tokens:
            return []

        bm25_scores = self.compute_bm25(query_tokens)
        return bm25_scores[:top_k]

    def _normalize_scores(self, scores: List[dict]) -> List[dict]:
        """Normalize BM25 Scores

        Args:
            scores (List[dict]): List of documents with their BM25 scores
        """
        if not scores:
            return scores

        max_score = max(score['score'] for score in scores)
        min_score = min(score['score'] for score in scores)

        for score in scores:
            if max_score - min_score == 0:
                score['score'] = 0.0
            else:
                score['score'] = (score['score'] - min_score) / (max_score - min_score)
        return scores