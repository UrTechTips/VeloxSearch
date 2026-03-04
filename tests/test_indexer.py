import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.indexer import Indexer
from app.services.dataset import Dataset

@pytest.fixture
def mock_dataset():
    dataset = Mock()
    dataset.get_documents.return_value = [
        {"id": "1", "text": "sample document", "doc_id": "1"},
        {"id": "2", "text": "another document", "doc_id": "2"}
    ]
    dataset.get_vector_terms.return_value = ["sample", "document", "another"]
    return dataset


@pytest.fixture
def mock_indexer(mock_dataset):
    with patch('app.services.indexer.Dataset') as mock_dataset_class, \
         patch('app.services.indexer.InvertedIndex') as mock_inv_idx, \
         patch('app.services.indexer.VectorSearch') as mock_vec_search:
        
        mock_dataset_class.return_value.load_dataset.return_value = mock_dataset
        mock_dataset_class.dataset_id = "test_dataset"
        indexer = Indexer(mock_dataset_class, path="test_path/")
        indexer.inverted_index = mock_inv_idx.return_value
        indexer.vector_search = mock_vec_search.return_value
        
        yield indexer


def test_indexer_initialization(mock_indexer):
    assert mock_indexer.dataset_id == "test_dataset"
    assert mock_indexer.path == "test_path/"


def test_build_index(mock_indexer):
    with patch('os.makedirs'):
        result = mock_indexer.build_index()
        
        mock_indexer.inverted_index.build_index.assert_called_once()
        mock_indexer.vector_search.build_index.assert_called_once()
        assert result == mock_indexer


def test_add_document_valid(mock_indexer):
    document = {"id": "3", "text": "new document"}
    
    mock_indexer.add_document(document)
    
    mock_indexer.dataset.add_document.assert_called_once_with(document)
    mock_indexer.inverted_index.add_document.assert_called_once_with(document)
    mock_indexer.vector_search.add_document.assert_called_once_with("3", document)


def test_add_document_missing_id(mock_indexer):
    document = {"text": "document without id"}
    
    with pytest.raises(ValueError, match="Document must contain an 'id' field"):
        mock_indexer.add_document(document)


def test_rebuild_index(mock_indexer):
    with patch('os.path.exists', return_value=True), \
         patch('shutil.rmtree'):
        mock_indexer.rebuild_index()
        
        mock_indexer.inverted_index.build_index.assert_called_once()
        mock_indexer.vector_search.build_index.assert_called_once()


def test_load_index_success(mock_indexer):
    mock_indexer.inverted_index.index_exists.return_value = True
    mock_indexer.vector_search.index_exists.return_value = True
    
    mock_indexer.load_index()
    
    mock_indexer.inverted_index.open_index.assert_called_once()
    mock_indexer.vector_search.load_index.assert_called_once()


def test_load_index_missing_inverted(mock_indexer):
    mock_indexer.inverted_index.index_exists.return_value = False
    
    with pytest.raises(FileNotFoundError, match="Inverted index not found"):
        mock_indexer.load_index()


def test_load_index_missing_vector(mock_indexer):
    mock_indexer.inverted_index.index_exists.return_value = True
    mock_indexer.vector_search.index_exists.return_value = False
    
    with pytest.raises(FileNotFoundError, match="Vector index not found"):
        mock_indexer.load_index()