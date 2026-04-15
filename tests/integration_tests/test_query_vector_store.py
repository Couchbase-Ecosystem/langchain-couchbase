"""Test Couchbase Query Vector Store functionality"""

import os
import time
from typing import Any, Optional

import pytest
from langchain_core.documents import Document

from langchain_couchbase import CouchbaseQueryVectorStore
from langchain_couchbase.vectorstores import DistanceStrategy, IndexType
from tests.utils import (
    ConsistentFakeEmbeddings,
)

CONNECTION_STRING = os.getenv("COUCHBASE_CONNECTION_STRING", "")
BUCKET_NAME = os.getenv("COUCHBASE_BUCKET_NAME", "")
SCOPE_NAME = os.getenv("COUCHBASE_SCOPE_NAME", "")
COLLECTION_NAME = os.getenv("COUCHBASE_COLLECTION_NAME", "")
USERNAME = os.getenv("COUCHBASE_USERNAME", "")
PASSWORD = os.getenv("COUCHBASE_PASSWORD", "")
SLEEP_DURATION = 2


def set_all_env_vars() -> bool:
    """Check if all the environment variables are set."""
    return all(
        [
            CONNECTION_STRING,
            BUCKET_NAME,
            SCOPE_NAME,
            COLLECTION_NAME,
            USERNAME,
            PASSWORD,
        ]
    )


def check_capella() -> bool:
    """Check if the connection string is for Couchbase Capella."""
    return "cloud.couchbase.com" in CONNECTION_STRING.lower()


def get_cluster() -> Any:
    """Get a couchbase cluster object"""
    from datetime import timedelta

    from couchbase.auth import PasswordAuthenticator
    from couchbase.cluster import Cluster
    from couchbase.options import ClusterOptions

    auth = PasswordAuthenticator(USERNAME, PASSWORD)
    options = ClusterOptions(auth)
    options.apply_profile("wan_development")
    connect_string = CONNECTION_STRING
    cluster = Cluster(connect_string, options)

    # Wait until the cluster is ready for use.
    cluster.wait_until_ready(timedelta(seconds=5))

    return cluster


@pytest.fixture()
def cluster() -> Any:
    """Get a couchbase cluster object"""
    return get_cluster()


def delete_documents(
    cluster: Any, bucket_name: str, scope_name: str, collection_name: str
) -> None:
    """Delete all the documents in the collection"""
    query = f"DELETE FROM `{bucket_name}`.`{scope_name}`.`{collection_name}`"
    cluster.query(query).execute()


def fetch_documents_by_ids(
    cluster: Any,
    bucket_name: str,
    scope_name: str,
    collection_name: str,
    ids: list[str],
) -> dict[str, dict[str, Any]]:
    keys = ", ".join([f'"{doc_id}"' for doc_id in ids])
    query = (
        f"SELECT META().id AS id, `{collection_name}`.* "
        f"FROM `{bucket_name}`.`{scope_name}`.`{collection_name}` "
        f"USE KEYS [{keys}]"
    )
    rows = cluster.query(query).execute()
    return {row["id"]: row for row in rows}


def get_index(cluster: Any, index_name: str) -> Optional[dict]:
    """Return index dict if exists, otherwise None."""
    query = f"SELECT * FROM system:indexes WHERE name = '{index_name}'"
    rows = cluster.query(query).execute()
    if len(rows) == 0:
        return None
    return rows[0]["indexes"]


def delete_index(
    cluster: Any,
    bucket_name: str,
    scope_name: str,
    collection_name: str,
    index_name: str,
) -> None:
    """Drop the given index from the specified collection."""
    query = f"DROP INDEX `{index_name}` on {bucket_name}.{scope_name}.{collection_name}"
    cluster.query(query).execute()


@pytest.mark.skipif(
    not set_all_env_vars(), reason="Missing Couchbase environment variables"
)
class TestCouchbaseQueryVectorStore:
    @classmethod
    def setup_method(self) -> None:
        cluster = get_cluster()
        # Delete all the documents in the collection
        delete_documents(cluster, BUCKET_NAME, SCOPE_NAME, COLLECTION_NAME)

    def test_from_documents(self, cluster: Any) -> None:
        """Test end to end search using a list of documents."""

        documents = [
            Document(page_content="foo", metadata={"page": 1}),
            Document(page_content="bar", metadata={"page": 2}),
            Document(page_content="baz", metadata={"page": 3}),
        ]

        vectorstore = CouchbaseQueryVectorStore.from_documents(
            documents,
            ConsistentFakeEmbeddings(),
            cluster=cluster,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("baz", k=3)
        assert any(
            doc.page_content == "baz" and doc.metadata.get("page") == 3
            for doc in output
        )

    def test_from_texts(self, cluster: Any) -> None:
        """Test end to end search using a list of texts."""

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        vectorstore = CouchbaseQueryVectorStore.from_texts(
            texts,
            ConsistentFakeEmbeddings(),
            cluster=cluster,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("foo", k=3)
        assert len(output) >= 1
        assert any(doc.page_content == "foo" for doc in output)

    def test_from_texts_with_metadatas(self, cluster: Any) -> None:
        """Test end to end search using a list of texts and metadatas."""

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseQueryVectorStore.from_texts(
            texts,
            ConsistentFakeEmbeddings(),
            metadatas=metadatas,
            cluster=cluster,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("baz", k=3)
        assert any(
            doc.page_content == "baz" and doc.metadata.get("c") == 3 for doc in output
        )

    def test_add_texts_with_ids_and_metadatas(self, cluster: Any) -> None:
        """Test end to end search by adding a list of texts, ids and metadatas."""

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        ids = ["a", "b", "c"]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        results = vectorstore.add_texts(
            texts,
            ids=ids,
            metadatas=metadatas,
        )
        assert results == ids

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        stored_docs = fetch_documents_by_ids(
            cluster, BUCKET_NAME, SCOPE_NAME, COLLECTION_NAME, ids
        )
        assert "a" in stored_docs
        assert stored_docs["a"]["text"] == "foo"
        assert stored_docs["a"]["metadata"]["a"] == 1

    def test_delete_texts_with_ids(self, cluster: Any) -> None:
        """Test deletion of documents by ids."""
        texts = [
            "foo",
            "bar",
            "baz",
        ]

        ids = ["a", "b", "c"]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        results = vectorstore.add_texts(
            texts,
            ids=ids,
            metadatas=metadatas,
        )
        assert results == ids
        assert vectorstore.delete(ids)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("foo", k=1)
        assert len(output) == 0

    def test_similarity_search_with_scores(self, cluster: Any) -> None:
        """Test similarity search with scores."""

        texts = ["foo", "bar", "baz"]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        vectorstore.add_texts(texts, metadatas=metadatas)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search_with_score("foo", k=2)

        assert len(output) == 2
        assert any(
            doc.page_content == "foo" and doc.metadata.get("a") == 1
            for doc, _ in output
        )
        # revisit sorting of scores based on similarity metric
        # assert output[0][1] > output[1][1]

    def test_similarity_search_by_vector(self, cluster: Any) -> None:
        """Test similarity search by vector."""

        texts = ["foo", "bar", "baz"]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        vectorstore.add_texts(texts, metadatas=metadatas)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        vector = ConsistentFakeEmbeddings().embed_query("foo")
        vector_output = vectorstore.similarity_search_by_vector(vector, k=3)
        assert any(doc.page_content == "foo" for doc in vector_output)

        similarity_output = vectorstore.similarity_search("foo", k=3)
        assert any(doc.page_content == "foo" for doc in similarity_output)

    def test_output_fields(self, cluster: Any) -> None:
        """Test that output fields are set correctly."""

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        metadatas = [{"page": 1, "a": 1}, {"page": 2, "b": 2}, {"page": 3, "c": 3}]

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        ids = vectorstore.add_texts(texts, metadatas)
        assert len(ids) == len(texts)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("foo", k=3, fields=["metadata.page"])
        assert any(
            doc.page_content == "foo"
            and doc.metadata.get("page") == 1
            and "a" not in doc.metadata
            for doc in output
        )

    def test_hybrid_search(self, cluster: Any) -> None:
        """Test hybrid search."""

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        metadatas = [
            {"section": "index"},
            {"section": "glossary"},
            {"section": "appendix"},
        ]

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        vectorstore.add_texts(texts, metadatas=metadatas)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        result, score = vectorstore.similarity_search_with_score("foo", k=3)[0]

        # Wait for the documents to be indexed for hybrid search
        time.sleep(SLEEP_DURATION)

        hybrid_result, hybrid_score = vectorstore.similarity_search_with_score(
            "foo",
            k=1,
            where_str="metadata.section = 'index'",
        )[0]

        assert hybrid_result.page_content == "foo"
        assert hybrid_result.metadata["section"] == "index"
        assert isinstance(score, (int, float))
        assert isinstance(hybrid_score, (int, float))

    def test_id_in_results(self, cluster: Any) -> None:
        """Test that the id is returned in the result documents."""

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        ids = vectorstore.add_texts(texts, metadatas=metadatas)
        assert len(ids) == len(texts)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("foo", k=3)
        assert all(doc.id is not None for doc in output)

    def test_composite_index_creation(self, cluster: Any) -> None:
        """Test composite index creation."""

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        # Add some documents to the vector store
        vectorstore.add_texts(["foo", "bar", "baz"])

        # Create the index
        index_description = "IVF1,SQ8"
        index_name = "composite_test_index"
        try:
            delete_index(cluster, BUCKET_NAME, SCOPE_NAME, COLLECTION_NAME, index_name)
            time.sleep(SLEEP_DURATION)
        except Exception:
            pass
        vectorstore.create_index(
            IndexType.COMPOSITE,
            index_name=index_name,
            index_description=index_description,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        # Wait for the index to be created
        time.sleep(SLEEP_DURATION)

        # Check if the index is created
        index = get_index(cluster, index_name)
        assert index is not None
        assert index["name"] == "composite_test_index"
        assert index["using"] == "gsi"
        assert index["with"]["description"] == index_description
        assert index["with"]["dimension"] == 10  # ConsistentFakeEmbeddings default
        assert f"`{vectorstore._embedding_key}` VECTOR" in index["index_key"]
        assert f"`{vectorstore._text_key}`" in index["index_key"]

        # Test the index
        output = vectorstore.similarity_search("foo", k=3)
        assert any(doc.page_content == "foo" for doc in output)

        # Delete the index
        delete_index(
            cluster,
            BUCKET_NAME,
            SCOPE_NAME,
            COLLECTION_NAME,
            index_name,
        )
        time.sleep(SLEEP_DURATION)

        # Check if the index is deleted
        assert get_index(cluster, index_name) is None

    def test_hyperscale_index_creation(self, cluster: Any) -> None:
        """Test Hyperscale index creation."""

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        # Add some documents to the vector store
        vectorstore.add_texts(["foo", "bar", "baz"])

        # Create the index
        index_description = "IVF1,SQ8"
        index_name = "hyperscale_test_index"
        try:
            delete_index(cluster, BUCKET_NAME, SCOPE_NAME, COLLECTION_NAME, index_name)
            time.sleep(SLEEP_DURATION)
        except Exception:
            pass
        vectorstore.create_index(
            IndexType.HYPERSCALE,
            index_name=index_name,
            index_description=index_description,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        # Wait for the index to be created
        time.sleep(SLEEP_DURATION)

        # Check if the index is created
        index = get_index(cluster, index_name)
        assert index is not None
        assert index["name"] == "hyperscale_test_index"
        assert index["using"] == "gsi"
        assert index["with"]["description"] == index_description
        assert index["with"]["dimension"] == 10  # ConsistentFakeEmbeddings default
        assert f"`{vectorstore._embedding_key}` VECTOR" in index["index_key"]
        assert f"`{vectorstore._text_key}`" not in index["index_key"]

        # Test the index
        output = vectorstore.similarity_search("bar", k=3)
        assert any(doc.page_content == "bar" for doc in output)

        # Delete the index
        delete_index(
            cluster,
            BUCKET_NAME,
            SCOPE_NAME,
            COLLECTION_NAME,
            index_name,
        )

        # Check if the index is deleted
        assert get_index(cluster, index_name) is None

    def test_composite_index_creation_with_custom_parameters(
        self, cluster: Any
    ) -> None:
        """Test composite index creation with custom parameters."""

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        # Add some documents to the vector store
        vectorstore.add_documents(
            [
                Document(page_content="foo", metadata={"text": "a"}),
                Document(page_content="bar", metadata={"text": "b"}),
                Document(page_content="baz", metadata={"text": "c"}),
            ]
        )

        # Create the index
        index_description = "IVF1,SQ8"
        index_name = "langchain_composite_query_index_custom"
        nprobes = 2
        trainlist = 2
        default_dimension = 10  # ConsistentFakeEmbeddings default
        vector_field = "embedding"
        indexing_fields = ["metadata.text"]

        try:
            delete_index(cluster, BUCKET_NAME, SCOPE_NAME, COLLECTION_NAME, index_name)
            time.sleep(SLEEP_DURATION)
        except Exception:
            pass

        vectorstore.create_index(
            IndexType.COMPOSITE,
            index_description=index_description,
            distance_metric=DistanceStrategy.EUCLIDEAN,
            index_name=index_name,
            index_scan_nprobes=nprobes,
            index_trainlist=trainlist,
            vector_field=vector_field,
            vector_dimension=default_dimension,
            fields=indexing_fields,
        )

        # Wait for the index to be created
        time.sleep(SLEEP_DURATION)

        # Check if the index is created
        index = get_index(cluster, index_name)
        # import pdb; pdb.set_trace()
        assert index is not None
        assert index["name"] == index_name
        assert index["using"] == "gsi"
        assert index["with"]["description"] == index_description
        assert index["with"]["dimension"] == default_dimension
        assert index["with"]["scan_nprobes"] == nprobes
        assert index["with"]["train_list"] == trainlist
        assert f"`{vector_field}` VECTOR" in index["index_key"]
        assert f"`{vectorstore._text_key}`" in index["index_key"]
        assert "(`metadata`.`text`)" in index["index_key"]

        # Test the index
        output = vectorstore.similarity_search("foo", k=3)
        assert any(
            doc.page_content == "foo" and doc.metadata.get("text") == "a"
            for doc in output
        )

        # Delete the index
        delete_index(cluster, BUCKET_NAME, SCOPE_NAME, COLLECTION_NAME, index_name)
        time.sleep(SLEEP_DURATION)

        # Check if the index is deleted
        assert get_index(cluster, index_name) is None

    def test_hyperscale_index_creation_with_custom_parameters(
        self, cluster: Any
    ) -> None:
        """Test Hyperscale index creation with custom parameters."""

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.EUCLIDEAN,
        )

        # Add some documents to the vector store
        vectorstore.add_documents(
            [
                Document(page_content="foo", metadata={"text": "a"}),
                Document(page_content="bar", metadata={"text": "b"}),
                Document(page_content="baz", metadata={"text": "c"}),
            ]
        )

        # Create the index
        index_description = "IVF1,SQ8"
        index_name = "langchain_hyperscale_query_index_custom"
        nprobes = 2
        trainlist = 2
        default_dimension = 10  # ConsistentFakeEmbeddings default
        vector_field = "embedding"
        indexing_fields = ["metadata.text"]

        try:
            delete_index(cluster, BUCKET_NAME, SCOPE_NAME, COLLECTION_NAME, index_name)
            time.sleep(SLEEP_DURATION)
        except Exception:
            pass

        vectorstore.create_index(
            IndexType.HYPERSCALE,
            index_description=index_description,
            distance_metric=DistanceStrategy.EUCLIDEAN,
            index_name=index_name,
            index_scan_nprobes=nprobes,
            index_trainlist=trainlist,
            vector_field=vector_field,
            vector_dimension=default_dimension,
            fields=indexing_fields,
        )

        # Wait for the index to be created
        time.sleep(SLEEP_DURATION)

        # Check if the index is created
        index = get_index(cluster, index_name)
        assert index is not None
        assert index["name"] == index_name
        assert index["using"] == "gsi"
        assert index["with"]["description"] == index_description
        assert index["with"]["dimension"] == default_dimension
        assert index["with"]["scan_nprobes"] == nprobes
        assert index["with"]["train_list"] == trainlist
        assert f"`{vector_field}` VECTOR" in index["index_key"]
        assert f"`{vectorstore._text_key}`" not in index["index_key"]

        # Test the index
        output = vectorstore.similarity_search("foo", k=3)
        assert any(
            doc.page_content == "foo" and doc.metadata.get("text") == "a"
            for doc in output
        )

        # Delete the index
        delete_index(cluster, BUCKET_NAME, SCOPE_NAME, COLLECTION_NAME, index_name)
        time.sleep(SLEEP_DURATION)

        # Check if the index is deleted
        assert get_index(cluster, index_name) is None

    def test_custom_text_key_with_hyphen(self, cluster: Any) -> None:
        """Test that field names with hyphens work correctly.

        This test verifies that using hyphenated field names like 'text-to-embed'
        for text_key and 'text-embedding' for embedding_key work correctly.
        Field names with special characters need proper escaping in N1QL queries.
        """
        texts = [
            "foo",
            "bar",
            "baz",
        ]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        # Use hyphenated field names
        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.COSINE,
            text_key="text-to-embed",
            embedding_key="text-embedding",
        )

        ids = vectorstore.add_texts(texts, metadatas=metadatas)
        assert len(ids) == len(texts)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        # Test similarity search with hyphenated field names
        output = vectorstore.similarity_search("foo", k=3)
        assert any(
            doc.page_content == "foo" and doc.metadata.get("a") == 1 for doc in output
        )

    def test_from_texts_with_hyphenated_field_names(self, cluster: Any) -> None:
        """Test from_texts class method with hyphenated field names."""
        texts = [
            "foo",
            "bar",
            "baz",
        ]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseQueryVectorStore.from_texts(
            texts,
            ConsistentFakeEmbeddings(),
            metadatas=metadatas,
            cluster=cluster,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.COSINE,
            text_key="text-to-embed",
            embedding_key="text-embedding",
        )

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("baz", k=3)
        assert any(
            doc.page_content == "baz" and doc.metadata.get("c") == 3 for doc in output
        )

    def test_hybrid_search_with_hyphenated_field_names(self, cluster: Any) -> None:
        """Test hybrid search with hyphenated field names."""
        texts = [
            "foo",
            "bar",
            "baz",
        ]

        metadatas = [
            {"section-1": "index"},
            {"section-1": "glossary"},
            {"section-1": "appendix"},
        ]

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            distance_metric=DistanceStrategy.COSINE,
            text_key="text-to-embed",
            embedding_key="text-embedding",
        )

        vectorstore.add_texts(texts, metadatas=metadatas)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        result, score = vectorstore.similarity_search_with_score("foo", k=3)[0]

        # Wait for the documents to be indexed for hybrid search
        time.sleep(SLEEP_DURATION)

        hybrid_result, hybrid_score = vectorstore.similarity_search_with_score(
            "foo",
            k=1,
            where_str="`metadata`.`section-1` = 'index'",
        )[0]

        assert hybrid_result.page_content == "foo"
        assert hybrid_result.metadata["section-1"] == "index"
        assert isinstance(score, (int, float))
        assert isinstance(hybrid_score, (int, float))
