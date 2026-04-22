"""Shared utility functions for langchain-couchbase."""

from datetime import timedelta
from typing import Any, Optional

from couchbase.cluster import Cluster


def check_bucket_exists(cluster: Cluster, bucket_name: str) -> bool:
    """Check if the bucket exists in the linked Couchbase cluster.

    Args:
        cluster: Couchbase cluster object with active connection.
        bucket_name: Name of the bucket to check.

    Returns:
        True if the bucket exists, False otherwise.
    """
    bucket_manager = cluster.buckets()
    try:
        bucket_manager.get_bucket(bucket_name)
        return True
    except Exception:
        return False


def check_scope_and_collection_exists(
    bucket: Any,
    scope_name: str,
    collection_name: str,
    bucket_name: str,
) -> bool:
    """Check if the scope and collection exists in the linked Couchbase bucket.

    Uses early-exit pattern for better performance on large clusters.

    Args:
        bucket: Couchbase bucket object.
        scope_name: Name of the scope to check.
        collection_name: Name of the collection to check.
        bucket_name: Name of the bucket (for error messages).

    Returns:
        True if both scope and collection exist.

    Raises:
        ValueError: If scope or collection is not found.
    """
    for scope in bucket.collections().get_all_scopes():
        if scope.name == scope_name:
            if collection_name in [c.name for c in scope.collections]:
                return True
            raise ValueError(
                f"Collection {collection_name} not found in scope "
                f"{scope_name} in Couchbase bucket {bucket_name}"
            )

    raise ValueError(
        f"Scope {scope_name} not found in Couchbase bucket {bucket_name}"
    )


def validate_ttl(ttl: Optional[timedelta]) -> None:
    """Validate the time to live value.

    Args:
        ttl: Time to live as a timedelta.

    Raises:
        ValueError: If ttl is not a timedelta or is not greater than 0.
    """
    if not isinstance(ttl, timedelta):
        raise ValueError(f"ttl should be of type timedelta but was {type(ttl)}.")
    if ttl <= timedelta(seconds=0):
        raise ValueError(
            f"ttl must be greater than 0 but was {ttl.total_seconds()} seconds."
        )
