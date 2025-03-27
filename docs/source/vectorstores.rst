Couchbase Vector Stores
====================

The ``CouchbaseVectorStore`` class provides a comprehensive integration between LangChain and Couchbase's vector search capabilities, enabling efficient storage and retrieval of embeddings for semantic search applications.

Overview
--------

Couchbase's vector search feature allows applications to search across multi-dimensional vector embeddings, making it ideal for:

* Semantic search across document collections
* Recommendation systems based on similarity
* Image or audio similarity search
* Natural language processing applications
* Retrieval augmented generation (RAG) systems

The ``CouchbaseVectorStore`` implementation in this package enables developers to leverage these capabilities while maintaining a consistent interface with other LangChain vector stores.

Vector Index Requirements
-----------------------

Before using the ``CouchbaseVectorStore``, you must set up a Couchbase Search index with vector search capabilities. 

Here's an example of creating a vector search index through the Couchbase UI or using N1QL:

.. code-block:: sql

    CREATE SEARCH INDEX langchain_vector_index 
    ON your_bucket.your_scope.your_collection
    WITH {
      "type": "fulltext-index",
      "sourceType": "gocbcore",
      "planParams": {
        "indexPartitions": 6
      },
      "params": {
        "mapping": {
          "types": {
            "your_collection": {
              "enabled": true,
              "dynamic": true,
              "properties": {
                "embedding": {
                  "enabled": true,
                  "dynamic": false,
                  "fields": [
                    {
                      "name": "embedding",
                      "type": "vector",
                      "dims": 1536,
                      "similarity": "dot_product",
                      "index": true
                    }
                  ]
                }
              }
            }
          }
        }
      }
    }

.. note::
   The ``dims`` parameter should match the dimension of your embedding model (1536 for OpenAI text-embedding-ada-002, but will vary based on your model).

Getting Started
--------------

To use the ``CouchbaseVectorStore``, you need to first establish a connection to your Couchbase cluster:

.. code-block:: python

    from datetime import timedelta
    from langchain_openai import OpenAIEmbeddings
    from couchbase.auth import PasswordAuthenticator
    from couchbase.cluster import Cluster
    from couchbase.options import ClusterOptions
    from langchain_couchbase.vectorstores import CouchbaseVectorStore

    # Set up connection to Couchbase
    COUCHBASE_CONNECTION_STRING = "couchbase://localhost"
    DB_USERNAME = "Administrator"
    DB_PASSWORD = "password"

    # Authenticate and connect to the cluster
    auth = PasswordAuthenticator(DB_USERNAME, DB_PASSWORD)
    options = ClusterOptions(auth)
    cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)

    # Wait until the cluster is ready for use
    cluster.wait_until_ready(timedelta(seconds=5))

    # Initialize embeddings provider
    embeddings = OpenAIEmbeddings()

    # Initialize vector store
    vector_store = CouchbaseVectorStore(
        cluster=cluster,
        bucket_name="langchain_bucket",
        scope_name="_default",
        collection_name="default",
        embedding=embeddings,
        index_name="langchain-vector-index",
        text_key="text",               # Field name for document text
        embedding_key="embedding",     # Field name for vector embeddings
        metadata_key="metadata",       # Field name for metadata
    )

Key Parameters
-------------

The ``CouchbaseVectorStore`` constructor accepts several parameters for customization:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``cluster``
     - A connected Couchbase Cluster object
   * - ``bucket_name``
     - Name of the bucket to store documents in
   * - ``scope_name``
     - Name of the scope in the bucket (default: "_default")
   * - ``collection_name``
     - Name of the collection in the scope (default: "_default")
   * - ``embedding``
     - LangChain embedding function for creating embeddings
   * - ``index_name``
     - Name of the Couchbase Search index to use
   * - ``text_key``
     - Field name for storing document content (default: "text")
   * - ``embedding_key``
     - Field name for storing embeddings (default: "embedding")
   * - ``metadata_key``
     - Field name for storing metadata (default: "metadata")
   * - ``batch_size``
     - Batch size for writing documents (default: 100)

Adding Documents
---------------

You can add documents to the vector store using the ``add_documents`` or ``add_texts`` methods:

.. code-block:: python

    from langchain_core.documents import Document

    # Add documents with metadata
    document_1 = Document(page_content="sample document text", metadata={"source": "file1.txt"})
    document_2 = Document(page_content="different document content", metadata={"source": "file2.txt"})
    documents = [document_1, document_2]
    
    # Add with explicit IDs
    ids = ["doc1", "doc2"]
    vector_store.add_documents(documents=documents, ids=ids)
    
    # Or add just texts
    texts = ["sample text 1", "sample text 2"]
    metadatas = [{"source": "text1"}, {"source": "text2"}]
    vector_store.add_texts(texts=texts, metadatas=metadatas)

Behind the scenes, this process:

1. Generates embeddings for each document using the provided embedding function
2. Creates a Couchbase document with the text, embedding, and metadata
3. Stores the document in the specified collection with the provided ID (or generates a UUID if no ID is provided)

Similarity Search
---------------

Perform similarity searches to find documents semantically similar to a query:

.. code-block:: python

    # Basic similarity search
    results = vector_store.similarity_search(query="sample document", k=2)
    for doc in results:
        print(f"Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}")
        print("---")
    
    # Similarity search with score
    results_with_score = vector_store.similarity_search_with_score(query="sample document", k=2)
    for doc, score in results_with_score:
        print(f"Score: {score}")
        print(f"Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}")
        print("---")

The search process:

1. Converts the query text into an embedding using the embedding function
2. Uses Couchbase vector search to find the most similar embeddings
3. Returns the matching documents, along with similarity scores when requested

Filtering Searches
----------------

You can filter search results based on metadata:

.. code-block:: python

    # Filter by metadata field
    filter_dict = {"source": "file1.txt"}
    
    filtered_results = vector_store.similarity_search(
        query="sample document",
        k=2,
        filter=filter_dict
    )

The ``filter`` parameter accepts a dictionary where the keys are metadata field names and the values are the expected values. This filtering happens within Couchbase's search engine, so it's efficient for large collections.

Deleting Documents
----------------

You can delete documents from the vector store:

.. code-block:: python

    # Delete documents by IDs
    vector_store.delete(ids=["doc1", "doc2"])

Advanced Usage: Hybrid Search
---------------------------

Couchbase supports hybrid search, combining keyword and vector search. While not directly exposed in the API, you can use this capability by creating a combined index and customizing your search queries:

.. code-block:: python

    from couchbase.search import SearchOptions
    from couchbase.vector_search import VectorSearch, VectorQuery
    
    # This example shows a custom search combining text and vector search
    # Requires setting up the proper index in Couchbase
    
    # Get embedding for query
    query_embedding = embeddings.embed_query("hybrid search example")
    
    # Create vector search component
    vector_search = VectorSearch(
        VectorQuery(
            field_name=vector_store._embedding_key,
            vector=query_embedding,
            k=10
        )
    )
    
    # Configure search options with vector search
    options = SearchOptions(
        vector_search=vector_search,
        limit=5
    )
    
    # Execute search - this is a basic example, customize as needed
    query = "sample"  # Text query
    search_results = vector_store._scope.search(
        vector_store._index_name, 
        query,
        options
    )
    
    # Process results (implementation would depend on your needs)

Using as a Retriever
------------------

The vector store can be used directly as a retriever:

.. code-block:: python

    # Create a retriever with default settings
    retriever = vector_store.as_retriever()
    
    # Create a retriever with custom settings
    retriever = vector_store.as_retriever(
        search_type="mmr",  # Maximum Marginal Relevance
        search_kwargs={"k": 5, "fetch_k": 10, "lambda_mult": 0.5},
    )
    
    # Use the retriever
    results = retriever.invoke("sample query")

Using the retriever makes it easy to integrate the vector store with LangChain chains and agents.

Performance Considerations
------------------------

For optimal performance with the ``CouchbaseVectorStore``:

1. **Batch Inserts**: Use batch operations when adding many documents with the ``add_documents`` or ``add_texts`` methods.

2. **Index Design**: Configure your vector index with appropriate parameters for your use case. Consider:
   - Vector dimensions matching your embedding model
   - Similarity metric (dot_product, euclidean, cosine)
   - Number of index partitions for large collections

3. **Connection Pooling**: Reuse the Couchbase Cluster object across operations rather than creating new connections.

4. **Filtering Strategy**: When using filters, ensure your index design properly supports the filtering fields.

5. **Document Size**: Consider the size of your documents; very large documents may impact performance.

API Reference
-----------

.. autoclass:: langchain_couchbase.vectorstores.CouchbaseVectorStore
   :members:
   :inherited-members:
   :exclude-members: _format_metadata, _check_bucket_exists, _check_scope_and_collection_exists, _check_index_exists 