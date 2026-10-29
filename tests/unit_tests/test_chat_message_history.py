"""Unit tests for CouchbaseChatMessageHistory error handling."""

from datetime import timedelta
from types import SimpleNamespace
from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest
from couchbase.cluster import Cluster
from couchbase.exceptions import AmbiguousTimeoutException
from couchbase.result import MultiMutationResult
from langchain_core.messages import AIMessage, HumanMessage, message_to_dict

from langchain_couchbase.chat_message_histories import CouchbaseChatMessageHistory

BUCKET = "bucket"
SCOPE = "scope"
COLLECTION = "collection"


def _make_history(ttl: Optional[timedelta] = None) -> CouchbaseChatMessageHistory:
    cluster = MagicMock(spec=Cluster)
    collection_spec = SimpleNamespace(name=COLLECTION)
    scope_spec = SimpleNamespace(name=SCOPE, collections=[collection_spec])
    bucket = cluster.bucket.return_value
    bucket.collections.return_value.get_all_scopes.return_value = [scope_spec]
    return CouchbaseChatMessageHistory(
        cluster=cluster,
        bucket_name=BUCKET,
        scope_name=SCOPE,
        collection_name=COLLECTION,
        session_id="session",
        create_index=False,
        ttl=ttl,
    )


def _multi_result(raw_result: Dict[str, Any]) -> MultiMutationResult:
    """Build a MultiMutationResult the way the SDK does for insert_multi.

    The SDK default for multi operations is return_exceptions=True, so failed
    keys are returned in the result instead of being raised.
    """
    return MultiMutationResult(
        SimpleNamespace(raw_result=raw_result), return_exceptions=True
    )


def _failed_multi_result(keys: Any) -> MultiMutationResult:
    raw: Dict[str, Any] = {"all_okay": False}
    for key in keys:
        raw[key] = AmbiguousTimeoutException("timed out")
    return _multi_result(raw)


def test_failed_multi_result_control() -> None:
    result = _failed_multi_result(["k1"])
    assert result.all_ok is False
    assert isinstance(result.exceptions["k1"], AmbiguousTimeoutException)


@pytest.mark.parametrize("ttl", [None, timedelta(minutes=5)])
def test_add_messages_raises_on_failed_write(ttl: Optional[timedelta]) -> None:
    history = _make_history(ttl=ttl)
    collection = history._collection
    collection.insert_multi.side_effect = lambda batch, **kwargs: _failed_multi_result(
        batch.keys()
    )

    with pytest.raises(ValueError, match="Failed to add messages") as exc_info:
        history.add_messages([HumanMessage(content="hi"), AIMessage(content="hey")])

    assert isinstance(exc_info.value.__cause__, AmbiguousTimeoutException)
    collection.insert_multi.assert_called_once()


def test_add_messages_succeeds_when_all_ok() -> None:
    history = _make_history()
    history._collection.insert_multi.side_effect = lambda batch, **kwargs: (
        _multi_result({"all_okay": True})
    )

    history.add_messages([HumanMessage(content="hi")])

    history._collection.insert_multi.assert_called_once()


def test_add_messages_raises_when_sdk_raises() -> None:
    history = _make_history()
    history._collection.insert_multi.side_effect = AmbiguousTimeoutException("boom")

    with pytest.raises(AmbiguousTimeoutException):
        history.add_messages([HumanMessage(content="hi")])


def test_add_messages_stops_after_failed_batch() -> None:
    history = _make_history()
    history._collection.insert_multi.side_effect = lambda batch, **kwargs: (
        _failed_multi_result(batch.keys())
    )

    with pytest.raises(ValueError):
        history.add_messages([HumanMessage(content=str(i)) for i in range(150)])

    history._collection.insert_multi.assert_called_once()


def test_add_message_raises_on_failed_write() -> None:
    history = _make_history()
    history._collection.insert.side_effect = AmbiguousTimeoutException("boom")

    with pytest.raises(AmbiguousTimeoutException):
        history.add_message(HumanMessage(content="hi"))


def test_add_message_succeeds() -> None:
    history = _make_history()

    history.add_message(HumanMessage(content="hi"))

    history._collection.insert.assert_called_once()


def test_messages_raises_on_failed_read() -> None:
    history = _make_history()
    history._scope.query.side_effect = AmbiguousTimeoutException("boom")

    with pytest.raises(AmbiguousTimeoutException):
        history.messages


def test_messages_raises_when_iterating_result_fails() -> None:
    history = _make_history()
    query_result = MagicMock()
    query_result.__iter__.side_effect = AmbiguousTimeoutException("boom")
    history._scope.query.return_value = query_result

    with pytest.raises(AmbiguousTimeoutException):
        history.messages


def test_messages_returns_rows() -> None:
    history = _make_history()
    stored = HumanMessage(content="hi")
    history._scope.query.return_value = iter([{"message": message_to_dict(stored)}])

    assert history.messages == [stored]


def test_messages_returns_empty_for_new_conversation() -> None:
    history = _make_history()
    history._scope.query.return_value = iter([])

    assert history.messages == []


def test_clear_raises_on_failed_delete() -> None:
    history = _make_history()
    history._scope.query.return_value.execute.side_effect = AmbiguousTimeoutException(
        "boom"
    )

    with pytest.raises(AmbiguousTimeoutException):
        history.clear()


def test_clear_succeeds() -> None:
    history = _make_history()

    history.clear()

    history._scope.query.return_value.execute.assert_called_once()
