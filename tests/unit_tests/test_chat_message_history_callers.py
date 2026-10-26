"""Caller-level failure tests for CouchbaseChatMessageHistory.

These drive the history through the real LangChain callers
(``ConversationBufferMemory``, ``aget_messages`` and
``RunnableWithMessageHistory``) against an in-memory fake collection, with
failures injected. Contributed by @ericdelorefice in #44 / #45.
"""

import logging
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest
from couchbase.cluster import Cluster
from couchbase.exceptions import AmbiguousTimeoutException
from couchbase.result import MultiMutationResult
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain_couchbase.chat_message_histories import CouchbaseChatMessageHistory

BUCKET = "bucket"
SCOPE = "scope"
COLLECTION = "collection"


class FakeStore:
    """Just enough of a collection and scope for the chat history."""

    def __init__(self) -> None:
        self.docs: Dict[str, Dict[str, Any]] = {}
        self.fail_writes = False
        self.fail_reads = False

    def insert(self, key: str, value: Dict[str, Any], **kwargs: Any) -> None:
        if self.fail_writes:
            raise AmbiguousTimeoutException("injected: insert timed out")
        self.docs[key] = value

    def insert_multi(
        self, batch: Dict[str, Dict[str, Any]], **kwargs: Any
    ) -> MultiMutationResult:
        # Built the way the SDK builds it with the default
        # return_exceptions=True: failures are returned, not raised.
        raw: Dict[str, Any] = {"all_okay": not self.fail_writes}
        if self.fail_writes:
            for key in batch:
                raw[key] = AmbiguousTimeoutException("injected: insert timed out")
        else:
            self.docs.update(batch)
        return MultiMutationResult(
            SimpleNamespace(raw_result=raw), return_exceptions=True
        )

    def query(self, statement: str, **params: Any) -> Any:
        if statement.lstrip().upper().startswith("SELECT"):
            if self.fail_reads:
                raise AmbiguousTimeoutException("injected: query timed out")
            rows = [
                d for d in self.docs.values() if d["session_id"] == params["session_id"]
            ]
            rows.sort(key=lambda d: d["ts"])
            return [{"message": d["message"]} for d in rows]
        return MagicMock()


def _echo(messages: List[BaseMessage]) -> AIMessage:
    return AIMessage(content=f"seen {len(messages)}")


def _make_history(store: FakeStore, session_id: str = "s1") -> Any:
    cluster = MagicMock(spec=Cluster)
    bucket = cluster.bucket.return_value
    scope = bucket.scope.return_value
    scope.collection.return_value = store
    scope.query.side_effect = store.query
    scope_spec = SimpleNamespace(
        name=SCOPE, collections=[SimpleNamespace(name=COLLECTION)]
    )
    bucket.collections.return_value.get_all_scopes.return_value = [scope_spec]
    return CouchbaseChatMessageHistory(
        cluster=cluster,
        bucket_name=BUCKET,
        scope_name=SCOPE,
        collection_name=COLLECTION,
        session_id=session_id,
        create_index=False,
    )


def test_classic_memory_save_context_reports_a_failed_write() -> None:
    store = FakeStore()
    memory = ConversationBufferMemory(chat_memory=_make_history(store))
    store.fail_writes = True

    with pytest.raises(ValueError, match="Failed to add messages"):
        memory.save_context({"input": "my name is Eric"}, {"output": "noted"})


async def test_async_read_does_not_turn_a_failed_read_into_an_empty_history() -> None:
    store = FakeStore()
    history = _make_history(store)
    history.add_message(HumanMessage(content="hi"))
    store.fail_reads = True

    with pytest.raises(AmbiguousTimeoutException):
        await history.aget_messages()


def test_runnable_with_history_failed_turn_leaves_a_trace(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """RunnableWithMessageHistory writes the turn from an on_end listener, and
    langchain_core logs listener errors instead of raising them. The most the
    history can do for this caller is make the failure reach that log."""
    store = FakeStore()
    history = _make_history(store)
    chain = RunnableWithMessageHistory(
        RunnableLambda(_echo), lambda session_id: history
    )
    store.fail_writes = True

    with caplog.at_level(logging.DEBUG):
        out = chain.invoke(
            [HumanMessage(content="my name is Eric")],
            config={"configurable": {"session_id": "s1"}},
        )
    store.fail_writes = False

    assert out.content == "seen 1"
    assert history.messages == []
    assert any("Failed to add messages" in r.getMessage() for r in caplog.records), (
        caplog.text
    )


def test_runnable_with_history_healthy_two_turns() -> None:
    store = FakeStore()
    history = _make_history(store)
    chain = RunnableWithMessageHistory(RunnableLambda(_echo), lambda sid: history)
    config: Any = {"configurable": {"session_id": "s1"}}
    chain.invoke([HumanMessage(content="turn 1")], config=config)
    out = chain.invoke([HumanMessage(content="turn 2")], config=config)

    assert out.content == "seen 3"
    assert len(history.messages) == 4


def test_other_sessions_not_mixed_in() -> None:
    store = FakeStore()
    _make_history(store, session_id="a").add_message(HumanMessage(content="for a"))

    assert _make_history(store, session_id="b").messages == []
