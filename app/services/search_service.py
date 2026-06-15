from typing import List, Dict, Self
from app.utils.redis_utils import publish_status

from app.services.bm25 import BM25
from app.services.ranker import Ranker
from app.services.dataset import Dataset
from app.services.indexer import Indexer
from app.services.vector_search import VectorSearch
from app.services.inverted_index import InvertedIndex


class SearchService:
    def __init__(self, dataset_id: str, path: str = None) -> None:
        """Initialize the SearchService.

        Args:
            dataset_id (str): The dataset identifier.
            path (str, optional): The path to the dataset directory. Defaults to None.
        """
        self.dataset_id = dataset_id
        self.path = path if path else f"data/{dataset_id}/"

        self.dataset = Dataset(dataset_id, path=self.path)
        self.indexer = Indexer(self.dataset, path=self.path)
        self.inverted_index = None
        self.vector_search = None

        self.bm25 = None
        self.ranker = None

    def is_indexed(self) -> bool:
        """Check if the dataset has already been indexed.

        Returns:
            bool: True if indexed, False otherwise.
        """
        return self.indexer.is_indexed()

    def index(self) -> Self:
        """Index the dataset using both BM25 and Vector Search.

        Args:
            dataset (List[Dict]): The dataset to be indexed.

        Returns:
            Self: The instance of the SearchService.
        """
        # self.dataset.save_dataset(dataset)
        self.indexer.build_index()
        publish_status(dataset_id=self.dataset_id, message="Indexing completed.", progress=100)

        self.inverted_index = self.indexer.get_inverted_index()
        self.vector_search = self.indexer.get_vector_search()

        self.bm25 = BM25(self.inverted_index)
        self.ranker = Ranker(self.dataset_id, self.bm25, self.vector_search)
        return self

    def add_documents(self, documents: List[Dict]) -> Self:
        """Add new documents to the existing dataset and update the indexes.

        Args:
            documents (List[Dict]): The new documents to be added.
        
        Returns:
            Self: The instance of the SearchService.
        """
        for document in documents:
            # The indexer is responsible for adding the document to the dataset and updating indexes.
            self.indexer.add_document(document)
            self.indexer.save_index() # TODO: Add tests for this method

        self.inverted_index = self.indexer.get_inverted_index()
        self.vector_search = self.indexer.get_vector_search()

        self.bm25 = BM25(self.inverted_index)
        self.ranker = Ranker(self.dataset_id, self.bm25, self.vector_search)
        return self

    def load(self) -> Self:
        """Load the necessary components for the search service.

        Returns:
            Self: The instance of the SearchService.
        """
        self.dataset.load_dataset()
        self.indexer.load_index()
        self.inverted_index = self.indexer.get_inverted_index()
        self.vector_search = self.indexer.get_vector_search()

        self.bm25 = BM25(self.inverted_index)
        self.ranker = Ranker(self.dataset_id, self.bm25, self.vector_search)
        return self
    
    def search(self, query: str, top_k: int = 5) -> Dict[str, List[Dict]]:
        """Perform a search using both BM25 and Vector Search.

        Args:
            query (str): The search query.
            top_k (int, optional): Number of top results to return. Defaults to 5.
        Returns:
            List[Dict]: A dictionary containing results from both search methods.
        """
        results = self.ranker.rank(query, k=top_k)
        res = []
        for i in results:
            doc_id = i['id']
            data = self.dataset.get_document(doc_id)
            res.append(data)

        return {"results": res, "meta": results}