from unittest.mock import MagicMock, patch

from langchain_core.documents import Document


@patch("parking_assistant.rag.retriever.load_index")
def test_retrieve_returns_results(mock_load_index):
    mock_index = MagicMock()
    mock_index.similarity_search.return_value = [
        Document(page_content="Hourly rate: $3 per hour."),
        Document(page_content="Daily maximum: $25."),
    ]
    mock_load_index.return_value = mock_index

    from parking_assistant.rag.retriever import retrieve

    results = retrieve("parking rates")
    assert len(results) == 2
    assert "Hourly rate" in results[0]
    mock_index.similarity_search.assert_called_once_with("parking rates", k=3)


@patch("parking_assistant.rag.retriever.load_index")
def test_retrieve_empty_query(mock_load_index):
    from parking_assistant.rag.retriever import retrieve

    results = retrieve("")
    assert results == []
    mock_load_index.assert_not_called()


@patch("parking_assistant.rag.retriever.load_index")
def test_retrieve_with_custom_limit(mock_load_index):
    mock_index = MagicMock()
    mock_index.similarity_search.return_value = [
        Document(page_content="Result 1"),
    ]
    mock_load_index.return_value = mock_index

    from parking_assistant.rag.retriever import retrieve

    results = retrieve("hours", limit=1)
    assert len(results) == 1
    mock_index.similarity_search.assert_called_once_with("hours", k=1)
