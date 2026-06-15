# Integration
import os
import shutil
from typing import Dict, Self
from app.services.dataset import Dataset
from app.services.vector_search import VectorSearch
from app.services.inverted_index import InvertedIndex
from app.utils.redis_utils import publish_status

class Indexer:
    def __init__(self, dataset: Dataset, path: str = None) -> None:
        """Initialize the Indexer.

        Args:
            dataset_id (str): The dataset identifier.
            path (str, optional): The path to the dataset directory. Defaults to None.
        """
        self.dataset_id = dataset.dataset_id
        self.path = path if path else f"data/{self.dataset_id}/"
        self.dataset = dataset

        self.inverted_index = InvertedIndex(self.dataset, path=self.path)
        self.vector_search = VectorSearch(self.dataset, self.dataset.get_vector_terms(), path=self.path)

    def is_indexed(self) -> bool:
        """Check if the dataset has already been indexed.

        Returns:
            bool: True if indexed, False otherwise.
        """
        return self.inverted_index.index_exists() and self.vector_search.index_exists()
    
    def build_index(self) -> Self:
        """Build the index for the dataset. And save it to disk.

        Returns:
            Self: The current Indexer instance.
        """
        os.makedirs(self.path, exist_ok=True)

        dataset = self.dataset.get_documents()
        publish_status(dataset_id=self.dataset_id, message="Building inverted index...", progress=0)
        self.inverted_index.build_index()
        publish_status(dataset_id=self.dataset_id, message="Building vector index...", progress=50)
        self.vector_search.build_index()
        
        return self

    def add_document(self, document: Dict) -> None:
        """Add a document to the dataset.

        Args:
            document (Dict): The document to add.

        Raises:
            ValueError: If the document does not contain an 'id' field.
        """
        document_id = document.get("id")
        if document_id is None:
            raise ValueError("Document must contain an 'id' field")
        self.dataset.add_document(document)
        self.inverted_index.add_document(document)
        self.vector_search.add_document(document_id, document)

    def rebuild_index(self) -> None:
        """ Rebuild the index for the dataset.
        """
        documents = self.dataset.get_documents()

        self.inverted_index.clear_index()
        self.vector_search.clear_index()

        self.inverted_index.build_index()
        self.vector_search.build_index()

    def load_index(self) -> None:
        """Load the index for the dataset.

        Raises:
            FileNotFoundError: If the index files do not exist.
        """
        if not self.inverted_index.index_exists():
            raise FileNotFoundError("Inverted index not found")

        if not self.vector_search.index_exists():
            raise FileNotFoundError("Vector index not found")
        
        self.inverted_index.open_index()
        self.vector_search.load_index()

    def save_index(self) -> None:
        """Save the index for the dataset.
        """
        self.inverted_index.save_index()
        self.vector_search.save_index()

    def get_inverted_index(self) -> InvertedIndex:
        """Get the inverted index.

        Returns:
            InvertedIndex: The inverted index instance.
        """
        return self.inverted_index
    
    def get_vector_search(self) -> VectorSearch:
        """Get the vector search instance.

        Returns:
            VectorSearch: The vector search instance.
        """
        return self.vector_search