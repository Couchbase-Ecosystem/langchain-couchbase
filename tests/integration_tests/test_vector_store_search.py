"""Integration tests for CouchbaseVectorStore search functionality.

This test suite verifies the integration between Langchain, Couchbase, and OpenAI
by testing various vector search scenarios including:
- Normal vector similarity search
- Error handling for null fields in search results
- Custom search options with field filtering

Requirements:
- Running Couchbase server with vector search capability
- OpenAI API key configured in environment
- Proper vector search index configuration
"""

from datetime import timedelta
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from langchain_couchbase import CouchbaseVectorStore

# Load environment variables
load_dotenv()

# Couchbase connection settings
COUCHBASE_CONNECTION_STRING = os.getenv("COUCHBASE_CONNECTION_STRING", "couchbase://localhost")
DB_USERNAME = os.getenv("DB_USERNAME", "Administrator")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# Vector store settings
BUCKET_NAME = os.getenv("BUCKET_NAME", "test_bucket")
SCOPE_NAME = os.getenv("SCOPE_NAME", "test_scope")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "test_collection")
SEARCH_INDEX_NAME = os.getenv("SEARCH_INDEX_NAME", "test_vector_index")

def test_normal_search(vector_store):
    """Test normal search functionality"""
    print("\nTesting normal search...")
    try:
        results = vector_store.similarity_search(
            "test document",
            k=1
        )
        print("Search results:", results)
    except Exception as e:
        print(f"Error in normal search: {e}")

def test_null_fields_search(vector_store):
    """Test search with conditions that should return null fields"""
    print("\nTesting search with null fields (exact issue scenario)...")
    try:
        # Test 1: Search with non-existent field
        print("Test 1: Searching with non-existent field...")
        results = vector_store.similarity_search(
            k=1000,
            query="",
            search_options={
                "query": {"field": "nonexistent_field", "match": "any_value"}
            }
        )
        print("Search results:", results)
    except ValueError as e:
        print(f"Test 1 - Expected ValueError caught: {e}")
    except AttributeError as e:
        print(f"Test 1 - AttributeError caught (this is the issue we're fixing): {e}")
    except Exception as e:
        print(f"Test 1 - Unexpected error: {type(e).__name__}: {e}")

    try:
        # Test 2: Original issue reproduction
        print("\nTest 2: Original issue reproduction...")
        results = vector_store.similarity_search(
            k=1000,
            query="",
            search_options={
                "query": {"field": "metadata.source", "match": "lilian_weng_blog"},
                "fields": ["nonexistent_field"]  # Request field that doesn't exist
            }
        )
        print("Search results:", results)
    except ValueError as e:
        print(f"Test 2 - Expected ValueError caught: {e}")
    except AttributeError as e:
        print(f"Test 2 - AttributeError caught (this is the issue we're fixing): {e}")
    except Exception as e:
        print(f"Test 2 - Unexpected error: {type(e).__name__}: {e}")

    try:
        # Test 3: Force null fields by requesting no stored fields
        print("\nTest 3: Force null fields by requesting no stored fields...")
        results = vector_store.similarity_search(
            k=1000,
            query="",
            search_options={
                "fields": []  # Request no fields to be returned
            }
        )
        print("Search results:", results)
    except ValueError as e:
        print(f"Test 3 - Expected ValueError caught: {e}")
    except AttributeError as e:
        print(f"Test 3 - AttributeError caught (this is the issue we're fixing): {e}")
    except Exception as e:
        print(f"Test 3 - Unexpected error: {type(e).__name__}: {e}")

def test_custom_search_options(vector_store):
    """Test search with custom search options"""
    print("\nTesting search with custom options...")
    try:
        results = vector_store.similarity_search(
            k=1,
            query="test",
            search_options={
                "query": {"field": "metadata.source", "match": "lilian_weng_blog"}
            }
        )
        print("Search results:", results)
    except Exception as e:
        print(f"Error in custom search: {e}")

def main():
    try:
        print("Using configuration:")
        print(f"Connection String: {COUCHBASE_CONNECTION_STRING}")
        print(f"Bucket: {BUCKET_NAME}")
        print(f"Scope: {SCOPE_NAME}")
        print(f"Collection: {COLLECTION_NAME}")
        print(f"Search Index: {SEARCH_INDEX_NAME}")
        
        # Set up Couchbase connection
        auth = PasswordAuthenticator(DB_USERNAME, DB_PASSWORD)
        options = ClusterOptions(auth)
        cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)
        
        # Wait until cluster is ready
        cluster.wait_until_ready(timedelta(seconds=5))
        
        # Initialize embeddings
        embeddings = OpenAIEmbeddings()
        
        # Initialize vector store
        vector_store = CouchbaseVectorStore(
            cluster=cluster,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
            index_name=SEARCH_INDEX_NAME,
        )
        
        # Add test document with specific metadata
        texts = [
            "This is a test document about vector search",
        ]
        metadatas = [
            {"source": "test_blog"}  # Different source than what we'll search for
        ]
        
        # Add documents to vector store
        vector_store.add_texts(texts, metadatas=metadatas)
        
        # Run different test scenarios
        test_normal_search(vector_store)
        test_null_fields_search(vector_store)
        test_custom_search_options(vector_store)
        
    except Exception as e:
        print(f"Setup error: {e}")

if __name__ == "__main__":
    main() 