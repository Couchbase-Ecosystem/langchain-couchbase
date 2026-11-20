"""Open and validate the Couchbase collection that a component stores data in."""

from __future__ import annotations

from typing import NamedTuple

from couchbase.bucket import Bucket
from couchbase.cluster import Cluster
from couchbase.collection import Collection
from couchbase.scope import Scope


class CollectionHandles(NamedTuple):
    """SDK handles for a validated bucket, scope, and collection."""

    bucket: Bucket
    scope: Scope
    collection: Collection


def open_collection(
    cluster: Cluster, bucket_name: str, scope_name: str, collection_name: str
) -> CollectionHandles:
    """Return handles for an existing bucket, scope, and collection.

    Every Couchbase-backed component (vector stores, caches, chat history) calls
    this once at construction so they all fail the same way on bad input.

    Raises:
        ValueError: if ``cluster`` is not a ``couchbase.cluster.Cluster``, the
            bucket does not exist, the handles cannot be opened, or the scope or
            collection is missing from the bucket.
    """
    if not isinstance(cluster, Cluster):
        raise ValueError(
            f"cluster should be an instance of couchbase.Cluster, got {type(cluster)}"
        )

    try:
        cluster.buckets().get_bucket(bucket_name)
    except Exception:
        raise ValueError(
            f"Bucket {bucket_name} does not exist. "
            " Please create the bucket before searching."
        ) from None

    try:
        bucket = cluster.bucket(bucket_name)
        scope = bucket.scope(scope_name)
        collection = scope.collection(collection_name)
    except Exception as e:
        raise ValueError(
            "Error connecting to couchbase. "
            "Please check the connection and credentials."
        ) from e

    scope_collections = {
        scope_spec.name: {c.name for c in scope_spec.collections}
        for scope_spec in bucket.collections().get_all_scopes()
    }
    if scope_name not in scope_collections:
        raise ValueError(
            f"Scope {scope_name} not found in Couchbase bucket {bucket_name}"
        )
    if collection_name not in scope_collections[scope_name]:
        raise ValueError(
            f"Collection {collection_name} not found in scope "
            f"{scope_name} in Couchbase bucket {bucket_name}"
        )

    return CollectionHandles(bucket, scope, collection)
