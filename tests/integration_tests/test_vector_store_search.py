"""Test Couchbase Vector Store search functionality with edge cases"""

import os
import time
from typing import Any
from datetime import timedelta

import pytest
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions

from langchain_couchbase import CouchbaseVectorStore
from tests.utils import ConsistentFakeEmbeddings

# Environment variables
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
    auth = PasswordAuthenticator(USERNAME, PASSWORD)
    options = ClusterOptions(auth)
    cluster = Cluster(CONNECTION_STRING, options)
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
class TestCouchbaseVectorStoreSearch:
    """Test suite for vector store search edge cases"""
    
    @classmethod
    def setup_method(self) -> None:
        """Setup method to clean the collection before each test"""
        cluster = get_cluster()
        delete_documents(cluster, BUCKET_NAME, SCOPE_NAME, COLLECTION_NAME)

    def setup_vector_store(self, cluster: Any) -> CouchbaseVectorStore:
        """Helper to set up vector store with test document"""
        vector_store = CouchbaseVectorStore(
            cluster=cluster,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            embedding=ConsistentFakeEmbeddings(),
            index_name=INDEX_NAME,
        )
        
        # Add test document
        texts = ["This is a test document about vector search"]
        metadatas = [{"source": "test_blog"}]
        vector_store.add_texts(texts, metadatas=metadatas)
        
        # Wait for indexing
        time.sleep(SLEEP_DURATION)
        return vector_store

    def test_normal_search(self, cluster: Any) -> None:
        """Test normal search functionality"""
        vector_store = self.setup_vector_store(cluster)
        results = vector_store.similarity_search(
            "test document",
            k=1
        )
        assert len(results) > 0
        assert "test document" in results[0].page_content

    def test_null_fields_search_nonexistent_field(self, cluster: Any) -> None:
        """Test search with non-existent field"""
        vector_store = self.setup_vector_store(cluster)
        with pytest.raises(Exception) as exc_info:
            vector_store.similarity_search(
                k=1000,
                query="",
                search_options={
                    "query": {"field": "nonexistent_field", "match": "any_value"}
                }
            )
        assert exc_info.type in (ValueError, AttributeError)

    def test_null_fields_search_original_issue(self, cluster: Any) -> None:
        """Test original issue reproduction"""
        vector_store = self.setup_vector_store(cluster)
        with pytest.raises(Exception) as exc_info:
            vector_store.similarity_search(
                k=1000,
                query="",
                search_options={
                    "query": {"field": "metadata.source", "match": "lilian_weng_blog"},
                    "fields": ["nonexistent_field"]
                }
            )
        assert exc_info.type in (ValueError, AttributeError)

    def test_null_fields_search_empty_fields(self, cluster: Any) -> None:
        """Test search with empty fields list"""
        vector_store = self.setup_vector_store(cluster)
        with pytest.raises(Exception) as exc_info:
            vector_store.similarity_search(
                k=1000,
                query="",
                search_options={
                    "fields": []
                }
            )
        assert exc_info.type in (ValueError, AttributeError)

    def test_custom_search_options(self, cluster: Any) -> None:
        """Test search with custom search options"""
        vector_store = self.setup_vector_store(cluster)
        results = vector_store.similarity_search(
            k=1,
            query="test",
            search_options={
                "query": {"field": "metadata.source", "match": "test_blog"}
            }
        )
        assert len(results) > 0
        assert results[0].metadata["source"] == "test_blog" 