"""Test Couchbase Vector Store functionality"""

import os
import time
from typing import Any

import pytest
from langchain_core.documents import Document

from langchain_couchbase import (
    CouchbaseSearchVectorStore,
)
from tests.utils import ConsistentFakeEmbeddings

CONNECTION_STRING = os.getenv("COUCHBASE_CONNECTION_STRING", "")
BUCKET_NAME = os.getenv("COUCHBASE_BUCKET_NAME", "")
SCOPE_NAME = os.getenv("COUCHBASE_SCOPE_NAME", "")
COLLECTION_NAME = os.getenv("COUCHBASE_COLLECTION_NAME", "")
USERNAME = os.getenv("COUCHBASE_USERNAME", "")
PASSWORD = os.getenv("COUCHBASE_PASSWORD", "")
INDEX_NAME = os.getenv("COUCHBASE_INDEX_NAME", "")
SLEEP_DURATION = 1


def set_all_env_vars() -> bool:
    return all(
        [
            CONNECTION_STRING,
            BUCKET_NAME,
            SCOPE_NAME,
            COLLECTION_NAME,
            USERNAME,
            PASSWORD,
            INDEX_NAME,
        ]
    )


def get_cluster() -> Any:
    """Get a couchbase cluster object"""
    from datetime import timedelta

    from couchbase.auth import PasswordAuthenticator
    from couchbase.cluster import Cluster
    from couchbase.options import ClusterOptions

    auth = PasswordAuthenticator(USERNAME, PASSWORD)
    options = ClusterOptions(auth)
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


@pytest.mark.skipif(
    not set_all_env_vars(), reason="Missing Couchbase environment variables"
)
class TestCouchbaseSearchVectorStore:
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

        vectorstore = CouchbaseSearchVectorStore.from_documents(
            documents,
            ConsistentFakeEmbeddings(),
            cluster=cluster,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            index_name=INDEX_NAME,
        )

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("baz", k=1)
        assert output[0].page_content == "baz"
        assert output[0].metadata["page"] == 3

    def test_from_texts(self, cluster: Any) -> None:
        """Test end to end search using a list of texts."""

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        vectorstore = CouchbaseSearchVectorStore.from_texts(
            texts,
            ConsistentFakeEmbeddings(),
            cluster=cluster,
            index_name=INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
        )

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("foo", k=1)
        assert len(output) == 1
        assert output[0].page_content == "foo"

    def test_from_texts_with_metadatas(self, cluster: Any) -> None:
        """Test end to end search using a list of texts and metadatas."""

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseSearchVectorStore.from_texts(
            texts,
            ConsistentFakeEmbeddings(),
            metadatas=metadatas,
            cluster=cluster,
            index_name=INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
        )

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("baz", k=1)
        assert output[0].page_content == "baz"
        assert output[0].metadata["c"] == 3

    def test_add_texts_with_ids_and_metadatas(self, cluster: Any) -> None:
        """Test end to end search by adding a list of texts, ids and metadatas."""

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        ids = ["a", "b", "c"]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseSearchVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            index_name=INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
        )

        results = vectorstore.add_texts(
            texts,
            ids=ids,
            metadatas=metadatas,
        )
        assert results == ids

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("foo", k=1)
        assert output[0].id == "a"
        assert output[0].page_content == "foo"
        assert output[0].metadata["a"] == 1

    def test_delete_texts_with_ids(self, cluster: Any) -> None:
        """Test deletion of documents by ids."""
        texts = [
            "foo",
            "bar",
            "baz",
        ]

        ids = ["a", "b", "c"]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseSearchVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            index_name=INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
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

        vectorstore = CouchbaseSearchVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            index_name=INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
        )

        vectorstore.add_texts(texts, metadatas=metadatas)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search_with_score("foo", k=2)

        assert len(output) == 2
        assert output[0][0].page_content == "foo"

        # check if the scores are sorted
        assert output[0][0].metadata["a"] == 1
        assert output[0][1] > output[1][1]

    def test_similarity_search_by_vector(self, cluster: Any) -> None:
        """Test similarity search by vector."""

        texts = ["foo", "bar", "baz"]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseSearchVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            index_name=INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
        )

        vectorstore.add_texts(texts, metadatas=metadatas)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        vector = ConsistentFakeEmbeddings().embed_query("foo")
        vector_output = vectorstore.similarity_search_by_vector(vector, k=1)

        assert vector_output[0].page_content == "foo"

        similarity_output = vectorstore.similarity_search("foo", k=1)

        assert similarity_output == vector_output

    def test_output_fields(self, cluster: Any) -> None:
        """Test that output fields are set correctly."""

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        metadatas = [{"page": 1, "a": 1}, {"page": 2, "b": 2}, {"page": 3, "c": 3}]

        vectorstore = CouchbaseSearchVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            index_name=INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
        )

        ids = vectorstore.add_texts(texts, metadatas)
        assert len(ids) == len(texts)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("foo", k=1, fields=["metadata.page"])
        assert output[0].page_content == "foo"
        assert output[0].metadata["page"] == 1
        assert "a" not in output[0].metadata

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

        vectorstore = CouchbaseSearchVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            index_name=INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
        )

        vectorstore.add_texts(texts, metadatas=metadatas)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        result, score = vectorstore.similarity_search_with_score("foo", k=1)[0]

        # Wait for the documents to be indexed for hybrid search
        time.sleep(SLEEP_DURATION)

        hybrid_result, hybrid_score = vectorstore.similarity_search_with_score(
            "foo",
            k=1,
            search_options={"query": {"match": "index", "field": "metadata.section"}},
        )[0]

        assert result == hybrid_result
        assert score <= hybrid_score

    def test_id_in_results(self, cluster: Any) -> None:
        """Test that the id is returned in the result documents."""

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        vectorstore = CouchbaseSearchVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            index_name=INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
        )

        ids = vectorstore.add_texts(texts, metadatas=metadatas)
        assert len(ids) == len(texts)

        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)

        output = vectorstore.similarity_search("foo", k=1)
        assert output[0].id == ids[0]

    def test_search_index_without_fields(self, cluster: Any) -> None:
        """Test that the right error is raised if the search index
        does not contain the required fields."""
        from couchbase.management.search import SearchIndex

        texts = [
            "foo",
            "bar",
            "baz",
        ]

        metadatas = [{"a": 1}, {"b": 2}, {"c": 3}]

        # Create a search index without the required fields
        scope_index_manager = (
            cluster.bucket(BUCKET_NAME).scope(SCOPE_NAME).search_indexes()
        )
        INVALID_INDEX_NAME = "langchain-vs-testing-invalid-index"

        index_definition = {
            "type": "fulltext-index",
            "name": INVALID_INDEX_NAME,
            "sourceType": "gocbcore",
            "sourceName": BUCKET_NAME,
            "planParams": {"maxPartitionsPerPIndex": 1024, "indexPartitions": 1},
            "params": {
                "doc_config": {
                    "docid_prefix_delim": "",
                    "docid_regexp": "",
                    "mode": "scope.collection.type_field",
                    "type_field": "type",
                },
                "mapping": {
                    "analysis": {},
                    "default_analyzer": "standard",
                    "default_datetime_parser": "dateTimeOptional",
                    "default_field": "_all",
                    "default_mapping": {"dynamic": False, "enabled": False},
                    "default_type": "_default",
                    "docvalues_dynamic": False,
                    "index_dynamic": True,
                    "store_dynamic": True,
                    "type_field": "_type",
                    "types": {
                        "langchain.testing": {
                            "dynamic": False,
                            "enabled": True,
                            "properties": {
                                "embedding": {
                                    "dynamic": False,
                                    "enabled": True,
                                    "fields": [
                                        {
                                            "dims": 10,
                                            "index": True,
                                            "name": "embedding",
                                            "similarity": "l2_norm",
                                            "type": "vector",
                                            "vector_index_optimized_for": "recall",
                                        }
                                    ],
                                },
                            },
                        }
                    },
                },
                "store": {"indexType": "scorch", "segmentVersion": 16},
            },
            "sourceParams": {},
        }

        # Create the search index without text and metadata fields
        scope_index_manager.upsert_index(SearchIndex.from_json(index_definition))

        # Create the vector store with the invalid search index
        invalid_index_vs = CouchbaseSearchVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            index_name=INVALID_INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
        )

        ids = invalid_index_vs.add_texts(texts, metadatas=metadatas)
        assert len(ids) == len(texts)
        # Wait for the documents to be indexed
        time.sleep(SLEEP_DURATION)
        with pytest.raises(
            ValueError,
            match=("Search results do not contain the fields from the document."),
        ):
            output = invalid_index_vs.similarity_search("foo", k=1)

        # Drop the invalid search index
        scope_index_manager.drop_index(INVALID_INDEX_NAME)

        # Test the search index with the required fields reusing the same collection
        vectorstore = CouchbaseSearchVectorStore(
            cluster=cluster,
            embedding=ConsistentFakeEmbeddings(),
            index_name=INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
        )

        output = vectorstore.similarity_search("foo", k=1)
        assert output[0].id == ids[0]

    def test_retriever(self, cluster: Any) -> None:
        """Test the SearchVectorStore as a retriever."""
        texts = ["foo", "bar", "baz"]
        vectorstore = CouchbaseSearchVectorStore.from_texts(
            texts=texts,
            embedding=ConsistentFakeEmbeddings(),
            cluster=cluster,
            index_name=INDEX_NAME,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
        )

        # Create the retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
        docs = retriever.invoke("foo")

        assert len(docs) == 1

        assert docs[0].page_content == "foo"
