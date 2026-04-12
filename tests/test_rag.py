from unittest.mock import MagicMock, patch


def _make_mock_object(content):
    obj = MagicMock()
    obj.properties = {"content": content}
    return obj


@patch("parking_assistant.rag.retriever.get_client")
@patch("parking_assistant.rag.retriever.get_collection")
def test_retrieve_returns_results(mock_get_collection, mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_collection = MagicMock()
    mock_response = MagicMock()
    mock_response.objects = [
        _make_mock_object("Hourly rate: $3 per hour."),
        _make_mock_object("Daily maximum: $25."),
    ]
    mock_collection.query.near_text.return_value = mock_response
    mock_get_collection.return_value = mock_collection

    from parking_assistant.rag.retriever import retrieve

    results = retrieve("parking rates")
    assert len(results) == 2
    assert "Hourly rate" in results[0]
    mock_collection.query.near_text.assert_called_once_with(query="parking rates", limit=3)


@patch("parking_assistant.rag.retriever.get_client")
@patch("parking_assistant.rag.retriever.get_collection")
def test_retrieve_empty_query(mock_get_collection, mock_get_client):
    from parking_assistant.rag.retriever import retrieve

    results = retrieve("")
    assert results == []
    mock_get_client.assert_not_called()


@patch("parking_assistant.rag.retriever.get_client")
@patch("parking_assistant.rag.retriever.get_collection")
def test_retrieve_with_custom_limit(mock_get_collection, mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_collection = MagicMock()
    mock_response = MagicMock()
    mock_response.objects = [_make_mock_object("Result 1")]
    mock_collection.query.near_text.return_value = mock_response
    mock_get_collection.return_value = mock_collection

    from parking_assistant.rag.retriever import retrieve

    results = retrieve("hours", limit=1)
    assert len(results) == 1
    mock_collection.query.near_text.assert_called_once_with(query="hours", limit=1)
