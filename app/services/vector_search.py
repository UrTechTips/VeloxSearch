import os
import time
import threading
import hnswlib
from pathlib import Path
from typing import List, Dict, Optional, Any
from sentence_transformers import SentenceTransformer
from app.services.dataset import Dataset

# TODO: Optimized initialization, Check if Searching needs optimization.

class VectorSearch:
    _shared_model: Optional[SentenceTransformer] = None
    _model_lock = threading.Lock()

    def __init__(self, dataset: Dataset, vector_terms: Optional[List[str]] = None, path: Optional[str] = None):
        """Initialize the VectorSearch with dataset ID and vector terms.

        Args:
            dataset_id (str): The dataset identifier.
            vector_terms (Optional[List[str]], optional): List of terms to vectorize. Defaults to None.
            path (Optional[str], optional): The path to the dataset directory. Defaults to None.
        """
        self.dataset_id: str = dataset.dataset_id
        self.dataset = dataset
        self.vector_terms: List[str] = vector_terms if vector_terms is not None else []
        self.path = path if path is not None else f"data/{self.dataset_id}/"

        start_time = time.perf_counter()
        self.model = self._get_or_create_model()
        model_time = time.perf_counter()
        print(f"Model ready in {model_time - start_time:.2f} seconds.")
        self.dimensions = 384
        self.index: hnswlib.Index = hnswlib.Index(space='cosine', dim=self.dimensions)
        index_time = time.perf_counter()
        print(f"Index initialized in {index_time - model_time:.2f} seconds.")

        self.id_map: Dict[str, int] = {}
        self.reverse_id_map: Dict[int, str] = {}
        self.next_internal_id: int = 1

    @classmethod
    def _get_or_create_model(cls) -> SentenceTransformer:
        # Use double-checked locking to avoid duplicate model loads under concurrency.
        if cls._shared_model is None:
            with cls._model_lock:
                if cls._shared_model is None:
                    cls._shared_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        return cls._shared_model

    @classmethod
    def preload_model(cls) -> None:
        """Eagerly load the embedding model once during app startup."""
        cls._get_or_create_model()

    def build_index(self, batch_size: Optional[int] = 32) -> hnswlib.Index:
        """Build HNSWLib index from dataset. And save the index.

        Args:
            dataset (List[Dict]): Dataset to build the index from.
            batch_size (int, optional): Number of documents to process in each batch. Defaults to
        """
        self.index.init_index(max_elements=len(self.dataset.get_documents()), ef_construction=200, M=16)

        for i, document in enumerate(self.dataset.get_documents()):
            doc_id = str(document["id"])
            self.id_map[doc_id] = self.next_internal_id
            self.reverse_id_map[self.next_internal_id] = doc_id
            self.next_internal_id += 1

        text = []
        ids = []

        for doc in self.dataset.get_documents():
            vector_text = " ".join(str(doc.get(term, "")) for term in self.vector_terms)
            text.append(vector_text)
            ids.append(self.id_map[str(doc["id"])])

        vectors = self.model.encode(text, batch_size=batch_size, normalize_embeddings=True)
        self.index.add_items(vectors, ids=ids)
        self.save_index()
    
    def add_document(self, doc_id: str, document: Dict) -> None:
        """Add a single document to the HNSWLib index. And save the index.

        Args:
            document (Dict): Document to add to the index.
        """
        self.id_map[doc_id] = self.next_internal_id
        self.reverse_id_map[self.next_internal_id] = doc_id
        self.next_internal_id += 1

        self.index.resize_index(self.index.get_max_elements() + 1)

        vector_text = " ".join(str(document.get(term, "")) for term in self.vector_terms)
        vector = self.model.encode(vector_text, normalize_embeddings=True)
        self.index.add_items(vector, ids=[self.id_map[doc_id] ])
        self.save_index()

    def search(self, query_text: str, top_k: Optional[int] = 10) -> List[str]:
        """Search the HNSWLib index for similar vectors.

        Args:
            query_text (str): Text to search for.
            top_k (int, optional): Number of top results to return. Defaults to 5.
        
        Returns:
            List[str]: List of document IDs for the top_k similar vectors.
        """
        top_k = min(top_k, self.index.get_current_count())
        query_vector = self.model.encode(query_text, normalize_embeddings=True)
        labels, distances = self.index.knn_query(query_vector, k=top_k)
        
        return [
            {"id": self.reverse_id_map[i], "vector_score": float(1 - d)}
            for i, d in zip(labels[0], distances[0])
        ]


    def save_index(self) -> bool:
        """Save the HNSWLib index to disk.

        Returns:
            bool: True if save was successful, False otherwise.
        """
        try:
            Path(self.path).mkdir(parents=True, exist_ok=True)
            path_index = os.path.join(self.path, "vector_index.bin")
            path_idmap = os.path.join(self.path, "id_map.json")
            with open(path_idmap, 'w') as f:
                import json
                json.dump(self.id_map, f)
            self.index.save_index(path_index)
            return True
        except IOError as e:
            print(f"Error saving vector index: {e}")
            return False

    def load_index(self) -> bool:
        """Load the HNSWLib index from disk.

        Returns:
            bool: True if load was successful, False otherwise.
        """
        try:
            path_index = os.path.join(self.path, "vector_index.bin")
            path_idmap = os.path.join(self.path, "id_map.json")
            with open(path_idmap, 'r') as f:
                import json
                self.id_map = json.load(f)
                self.reverse_id_map = {v: k for k, v in self.id_map.items()}
                self.next_internal_id = max(self.reverse_id_map.keys()) + 1
            self.index.load_index(path_index)
            return True
        except IOError as e:
            print(f"Error loading vector index: {e}")
            return False
        
    def index_exists(self) -> bool:
        """Check if the index files exist on disk.

        Returns:
            bool: True if index files exist, False otherwise.
        """
        path_index = os.path.join(self.path, "vector_index.bin")
        path_idmap = os.path.join(self.path, "id_map.json")
        return os.path.exists(path_index) and os.path.exists(path_idmap)

    def clear_index(self) -> None:
        """Clear the current index in memory safely."""
        # Explicitly reset references
        self.index = None

        # Recreate a brand-new index
        self.index = hnswlib.Index(space="cosine", dim=self.dimensions)

        self.id_map.clear()
        self.reverse_id_map.clear()
        self.next_internal_id = 1

        self._delete_index_files()


    def _delete_index_files(self) -> None:
        """Delete the index files from disk.
        """
        path_index = os.path.join(self.path, "vector_index.bin")
        path_idmap = os.path.join(self.path, "id_map.json")
        try:
            if os.path.exists(path_index):
                os.remove(path_index)
            if os.path.exists(path_idmap):
                os.remove(path_idmap)
            if os.path.exists(self.path) and not os.listdir(self.path):
                os.rmdir(self.path)
        except IOError as e:
            print(f"Error deleting vector index files: {e}")