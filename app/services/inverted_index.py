import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from app.services.tokenizer import tokenize_lexical as tokenize
from app.services.dataset import Dataset

logger = logging.getLogger(__name__)

class InvertedIndex:
    """Inverted Index implementation for efficient search and retrieval of documents based on token occurrences.

    Attributes:
        dataset (Dataset): The dataset for which the index is built.
        path (str): The file path where the index is stored.
        index (Dict[str, Dict[str, int]]): The inverted index mapping tokens to document IDs and term frequencies.
        doc_lengths (Dict[int, int]): A mapping of document IDs to their token lengths.
        total_docs (int): The total number of documents indexed.
    """
    def __init__(self, dataset: Dataset = None, path: str = None) -> None:
        """Generate Inverted Index for the given dataset."""
        self.dataset = dataset
        self.dataset_id = dataset.dataset_id
        self.path = path if path is not None else f"data/{self.dataset_id}/"
        self.index: Dict[str, Dict[str, int]] = {}
        self.doc_lengths: Dict[int, int] = {}
        self.total_docs: int = 0

    def index_exists(self) -> bool:
        """Check if the inverted index files exist.

        Returns:
            bool: True if both index files exist, False otherwise.
        """
        filepath_index = os.path.join(self.path, "inverted_index.json")
        filepath_doc_lengths = os.path.join(self.path, "doc_lengths.json")
        return os.path.exists(filepath_index) and os.path.exists(filepath_doc_lengths)

    def _process_document(self, document: Dict[str, Any]) -> tuple[int, List[str]]:
        """Process a single document to extract tokens.

        Args:
            document (dict): Document data.

        Returns:
            tuple: Document ID and list of tokens.
        """
        doc_id = str(document["id"])
        searchable_fields = self.dataset.get_searchable_fields()

        tokens = []
        for field in searchable_fields:
            field_content = document.get(field, "")
            if field_content:
                tokens.extend(tokenize(field_content))

        return doc_id, tokens

    def build_index(self):
        """Build complete index from dataset. And save the index.

        Args:
            dataset (List[Dict[str, Any]]): The dataset to build the index from.
        """
        for document in self.dataset.get_documents():
            self.add_document(document)
        self.save_index()

    def add_document(self, document: Dict[str, Any]):
        """Add a single document to the inverted index. And save the index.

        Args:
            document (Dict[str, Any]): The document to add to the index.
        """
        doc_id, tokens = self._process_document(document)
        self.doc_lengths[doc_id] = len(tokens)
        self.total_docs = len(self.doc_lengths)

        self._add_document_tokens(doc_id, tokens)
        # self.save_index()

    def _add_document_tokens(self, doc_id: str, tokens: List[str]):
        """Add tokens of a document to the inverted index.

        Args:
            doc_id (str): The ID of the document.
            tokens (List[str]): The list of tokens extracted from the document.
        """
        tf_map = {}
        for token in tokens:
            tf_map[token] = tf_map.get(token, 0) + 1

        for token, tf in tf_map.items():
            if token not in self.index:
                self.index[token] = {}

            self.index[token][doc_id] = tf

    def save_index(self) -> bool:
        """Save the inverted index file to data storage.

        Returns:
            bool: True if the index was saved successfully, False otherwise.
        """
        try:
            Path(self.path).mkdir(parents=True, exist_ok=True)
            filepath_index = os.path.join(self.path, "inverted_index.json")
            filepath_doc_lengths = os.path.join(self.path, "doc_lengths.json")
            path_index = Path(filepath_index)
            path_doc_lengths = Path(filepath_doc_lengths)

            with path_index.open("w", encoding="utf-8") as f:
                json.dump(self.index, f, ensure_ascii=False, indent=4)
            with path_doc_lengths.open("w", encoding="utf-8") as f:
                json.dump({
                    "doc_lengths": self.doc_lengths,
                    "total_docs": self.total_docs
                }, f, ensure_ascii=False, indent=4)
            return True
        except IOError as e:
            logger.error(f"Failed to save index to {self.path}: {e}")
            return False

    def open_index(self) -> bool:
        """Load an inverted index from a file.
        
        Returns:
            bool: True if the index was loaded successfully, False otherwise.
        """
        try:
            filepath_index = os.path.join(self.path, "inverted_index.json")
            filepath_doc_lengths = os.path.join(self.path, "doc_lengths.json")

            with open(filepath_index, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.index = data if data else {}
            with open(filepath_doc_lengths, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.doc_lengths = data.get("doc_lengths", {})
                self.total_docs = data.get("total_docs", len(self.doc_lengths)) # Load or fallback
            return True
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load index from {self.path}: {e}")
            return False
        
    def index_exists(self) -> bool:
        """Check if the inverted index files exist.

        Returns:
            bool: True if both index files exist, False otherwise.
        """
        filepath_index = os.path.join(self.path, "inverted_index.json")
        filepath_doc_lengths = os.path.join(self.path, "doc_lengths.json")
        return os.path.exists(filepath_index) and os.path.exists(filepath_doc_lengths)

    def clear_index(self) -> None:
        """Clear the current inverted index and document lengths."""
        self.index = {}
        self.doc_lengths = {}
        self.total_docs = 0
        self.avg_doc_length = 0.0

        try:
            os.remove(os.path.join(self.path, "inverted_index.json")) if os.path.exists(os.path.join(self.path, "inverted_index.json")) else None
            os.remove(os.path.join(self.path, "doc_lengths.json")) if os.path.exists(os.path.join(self.path, "doc_lengths.json")) else None
            os.rmdir(self.path) if os.path.exists(self.path) and not os.listdir(self.path) else None
        except IOError as e:
            logger.error(f"Error clearing index files: {e}")
        
    def get_index(self):
        """Return the inverted index."""
        return self.index

    def get_doc_lengths(self):
        """Return the documents lengths
        """
        return self.doc_lengths

    def get_doc_length(self, doc_id):
        """Return precomputed token length of the document."""
        return self.doc_lengths.get(doc_id, 0)

    def get_total_docs(self):
        """Return total number of indexed documents."""
        return self.total_docs
    
    def get_average_doc_length(self) -> float:
        """Return average document length across all indexed documents."""
        if not self.doc_lengths:
            logger.warning("Document lengths are empty, cannot compute average document length.")
            return 0.0
        return sum(self.doc_lengths.values()) / len(self.doc_lengths)

    
    def get_term_frequencies(self, token: str) -> Dict[str, int]:
        """Return term frequencies for a given token across documents.

        Args:
            token (str): The token to look up.

        Returns:
            Dict[str, int]: A dictionary mapping document IDs to term frequencies.
        """
        postings = self.index.get(token, {})
        return postings

    def term_exists(self, token: str) -> bool:
        """Check if a term exists in the inverted index.

        Args:
            token (str): The token to check.
        
        Returns:
            bool: True if the term exists, False otherwise.
        """
        return token in self.index