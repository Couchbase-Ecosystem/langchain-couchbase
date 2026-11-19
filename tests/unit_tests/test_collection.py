"""Unit tests for the shared bucket/scope/collection validation seam."""

from types import SimpleNamespace
from typing import Any, List, Tuple
from unittest.mock import MagicMock

import pytest
from couchbase.cluster import Cluster
from langchain_core.embeddings import FakeEmbeddings

from langchain_couchbase._collection import open_collection
from langchain_couchbase.cache import CouchbaseCache
from langchain_couchbase.chat_message_histories import CouchbaseChatMessageHistory
from langchain_couchbase.vectorstores import CouchbaseQueryVectorStore, DistanceStrategy

BUCKET = "bucket"
SCOPE = "scope"
COLLECTION = "collection"


def _cluster(scopes: List[Tuple[str, List[str]]]) -> Any:
    cluster = MagicMock(spec=Cluster)
    cluster.bucket.return_value.collections.return_value.get_all_scopes.return_value = [  # noqa: E501
        SimpleNamespace(
            name=scope, collections=[SimpleNamespace(name=c) for c in collections]
        )
        for scope, collections in scopes
    ]
    return cluster


def test_returns_handles_for_existing_collection() -> None:
    cluster = _cluster([("other", []), (SCOPE, ["x", COLLECTION])])

    handles = open_collection(cluster, BUCKET, SCOPE, COLLECTION)

    cluster.buckets.return_value.get_bucket.assert_called_once_with(BUCKET)
    bucket = cluster.bucket.return_value
    assert handles.bucket is bucket
    assert handles.scope is bucket.scope.return_value
    assert handles.collection is bucket.scope.return_value.collection.return_value
    bucket.scope.assert_called_once_with(SCOPE)
    bucket.scope.return_value.collection.assert_called_once_with(COLLECTION)


def test_rejects_non_cluster() -> None:
    with pytest.raises(ValueError, match="instance of couchbase.Cluster"):
        open_collection(object(), BUCKET, SCOPE, COLLECTION)  # type: ignore[arg-type]


def test_missing_bucket() -> None:
    cluster = _cluster([(SCOPE, [COLLECTION])])
    cluster.buckets.return_value.get_bucket.side_effect = Exception("not found")

    with pytest.raises(ValueError, match=f"Bucket {BUCKET} does not exist"):
        open_collection(cluster, BUCKET, SCOPE, COLLECTION)
    cluster.bucket.assert_not_called()


def test_connection_error_is_chained() -> None:
    cluster = _cluster([(SCOPE, [COLLECTION])])
    cause = RuntimeError("boom")
    cluster.bucket.side_effect = cause

    with pytest.raises(ValueError, match="Error connecting to couchbase") as info:
        open_collection(cluster, BUCKET, SCOPE, COLLECTION)
    assert info.value.__cause__ is cause


def test_missing_scope() -> None:
    cluster = _cluster([("other", [COLLECTION])])

    with pytest.raises(ValueError, match=f"Scope {SCOPE} not found"):
        open_collection(cluster, BUCKET, SCOPE, COLLECTION)


def test_missing_collection_in_scope() -> None:
    # The collection exists, but in a different scope.
    cluster = _cluster([(SCOPE, ["x"]), ("other", [COLLECTION])])

    with pytest.raises(ValueError, match=f"Collection {COLLECTION} not found"):
        open_collection(cluster, BUCKET, SCOPE, COLLECTION)


@pytest.mark.parametrize(
    "build",
    [
        lambda cluster: CouchbaseCache(cluster, BUCKET, SCOPE, COLLECTION),
        lambda cluster: CouchbaseChatMessageHistory(
            cluster=cluster,
            bucket_name=BUCKET,
            scope_name=SCOPE,
            collection_name=COLLECTION,
            session_id="s",
            create_index=False,
        ),
        lambda cluster: CouchbaseQueryVectorStore(
            cluster=cluster,
            bucket_name=BUCKET,
            scope_name=SCOPE,
            collection_name=COLLECTION,
            embedding=FakeEmbeddings(size=4),
            distance_metric=DistanceStrategy.COSINE,
        ),
    ],
    ids=["cache", "chat_history", "vector_store"],
)
def test_components_share_the_validation(build: Any) -> None:
    good = _cluster([(SCOPE, [COLLECTION])])
    component = build(good)
    assert component._collection is (
        good.bucket.return_value.scope.return_value.collection.return_value
    )

    with pytest.raises(ValueError, match=f"Collection {COLLECTION} not found"):
        build(_cluster([(SCOPE, [])]))
