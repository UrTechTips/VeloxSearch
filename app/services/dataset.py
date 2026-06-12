import os
import json
from typing import List, Dict, Optional, Self
from genson import SchemaBuilder

class Dataset:
    """A class to manage datasets, including loading, saving, and adding documents.
    The dataset is stored as a JSON file, and the configuration is also stored in a separate JSON file.

    Methods:
        save_dataset(data: List[Dict]) -> Self: Save the dataset to a JSON file.
        load_dataset() -> Self: Load the dataset from a JSON file.
        add_document(document: Dict, document_id: Optional[str] = None) -> None: Add a document to the dataset.
        get_searchable_fields() -> List[str]: Get the searchable fields from the dataset configuration.
        get_vector_terms() -> List[str]: Get the vector terms from the dataset configuration.
        get_documents() -> List[Dict]: Get all documents from the dataset.
        get_document(document_id: str) -> Optional[Dict]: Get a document by its ID.
    """
    def __init__(self, dataset_id: str, config: Dict = None, path: Optional[str] = None):
        """Initialize the Dataset instance.

        Args:
            dataset_id (str): The ID of the dataset.
            config (Dict, optional): The configuration for the dataset. Defaults to None.
            path (Optional[str], optional): The path where the dataset is stored. Defaults to None.
        """
        self.dataset_id = dataset_id
        self.config = config

        self.path = path if path is not None else f"data/{self.dataset_id}/"
        # TODO: To make a better implementation, Instead of checking if the path exists, we can check if the a status flag exists in a database.
        if os.path.exists(self.path):
            self.load_dataset()

    def save_dataset(self, data: List[Dict]) -> Self:
        """Save the dataset to a JSON file.

        Args:
            data (List[Dict]): The dataset to save.

        Returns:
            Dataset: The current Dataset instance.
        """
        os.makedirs(self.path, exist_ok=True)
        file_path = os.path.join(self.path, "dataset.json")
        config_path = os.path.join(self.path, "config.json")
        with open(file_path, "w") as f:
            json.dump(data, f)
        with open(config_path, "w") as f:
            json.dump(self.config, f)
        return self

    def save_config(self, config: Dict) -> Self:
        """Save the dataset configuration to a JSON file.

        Args:
            config (Dict): The configuration to save.

        Returns:
            Dataset: The current Dataset instance.
        """
        self.config = config
        os.makedirs(self.path, exist_ok=True)
        config_path = os.path.join(self.path, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f)
        return self
    
    def load_dataset(self) -> Self:
        """Load the dataset from a JSON file.

        Returns:
            Dataset: The loaded dataset.
        """
        file_path = os.path.join(self.path, "dataset.json")
        config_path = os.path.join(self.path, "config.json")
        with open(file_path, "r") as f:
            data = json.load(f)
        with open(config_path, "r") as f:
            self.config = json.load(f)
        return data
    
    def add_document(self, document: Dict, document_id: Optional[str] = None) -> None:
        """Add a document to the dataset.

        Args:
            document (Dict): The document to add.
            document_id (Optional[str], optional): The ID of the document. Defaults to None.
        """
        file_path = os.path.join(self.path, "dataset.json")
        with open(file_path, "r") as f:
            data = json.load(f)
        data.append(document)
        with open(file_path, "w") as f:
            json.dump(data, f)

    def get_searchable_fields(self) -> List[str]:
        """Get the searchable fields from the dataset configuration.

        Returns:
            List[str]: The list of searchable fields.
        """
        if self.config and "searchable_fields" in self.config:
            return self.config["searchable_fields"]
        return []
    
    def get_vector_terms(self) -> List[str]:
        """Get the vector terms from the dataset configuration.

        Returns:
            List[str]: The list of vector terms.
        """
        if self.config and "vector_terms" in self.config:
            return self.config["vector_terms"]
        return []
    
    def get_documents(self) -> List[Dict]:
        """Get all documents from the dataset.

        Returns:
            List[Dict]: The list of documents.
        """
        file_path = os.path.join(self.path, "dataset.json")
        with open(file_path, "r") as f:
            data = json.load(f)
        return data

    def get_document(self, document_id: str) -> Optional[Dict]:
        """Get a document by its ID.

        Args:
            document_id (str): The ID of the document.

        Returns:
            Optional[Dict]: The document if found, else None.
        """
        documents = self.get_documents()
        for doc in documents:
            if str(doc.get(self.config.get("id_field"))) == str(document_id):
                return doc
        return None
    
    def parse_dataset(self) -> List[Dict]:
        """Parse the dataset to extract the schema and return the documents.

        Returns:
            List[Dict]: The list of parsed documents.
        """
        builder = SchemaBuilder()
        documents = self.get_documents()
        for doc in documents:
            builder.add_object(doc)
        schema = builder.to_json()
        print(schema)
        return schema

    def delete_dataset(self) -> None:
        """Delete the dataset by removing the dataset directory and its contents."""
        if os.path.exists(self.path):
            for root, dirs, files in os.walk(self.path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.path)