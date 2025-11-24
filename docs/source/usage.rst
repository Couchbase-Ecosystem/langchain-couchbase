.. _usage:

Usage
=====

``langchain-couchbase`` is the official Couchbase integration for `LangChain <https://python.langchain.com/>`_.

Vector Stores
------------
Use Couchbase as a vector store for your documents:

Couchbase Query Vector Store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Query vector store uses the Query and Index service to store and search document embeddings. It supports two types of vector indexes:

* **Hyperscale Vector Index** - Optimized for pure vector searches on large datasets (billions of documents). Best for content discovery, recommendations, and applications requiring high accuracy with low memory footprint. Hyperscale Vector indexes compare vectors and scalar values simultaneously.

* **Composite Vector Index** - Combines a Global Secondary Index (GSI) with a vector column. Ideal for searches combining vector similarity with scalar filters where scalars filter out large portions of the dataset. Composite Vector indexes apply scalar filters first, then perform vector searches on the filtered results.

For guidance on choosing the right index type, see `Choose the Right Vector Index <https://docs.couchbase.com/cloud/vector-index/use-vector-indexes.html>`_.

For more information on the indexes, see `Hyperscale Vector Index documentation <https://docs.couchbase.com/server/current/vector-index/hyperscale-vector-index.html>`_ or `Composite Vector Index documentation <https://docs.couchbase.com/server/current/vector-index/composite-vector-index.html>`_.

.. Note::
    This vector store is available in Couchbase Server versions 8.0 and above.

See a `complete query vector store usage example <https://github.com/couchbaselabs/query-vector-search-demo>`_.

.. code-block:: python

        import getpass

        # Constants for the connection
        COUCHBASE_CONNECTION_STRING = getpass.getpass(
            "Enter the connection string for the Couchbase cluster: "
        )
        DB_USERNAME = getpass.getpass("Enter the username for the Couchbase cluster: ")
        DB_PASSWORD = getpass.getpass("Enter the password for the Couchbase cluster: ")

        # Create Couchbase connection object
        from datetime import timedelta

        from couchbase.auth import PasswordAuthenticator
        from couchbase.cluster import Cluster
        from couchbase.options import ClusterOptions

        auth = PasswordAuthenticator(DB_USERNAME, DB_PASSWORD)
        options = ClusterOptions(auth)
        cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)

        # Wait until the cluster is ready for use.
        cluster.wait_until_ready(timedelta(seconds=5))

        from langchain_couchbase import CouchbaseQueryVectorStore
        from langchain_couchbase.vectorstores import DistanceStrategy

        vectorstore = CouchbaseQueryVectorStore(
            cluster=cluster,
            bucket_name=BUCKET_NAME,
            scope_name=SCOPE_NAME,
            collection_name=COLLECTION_NAME,
            embedding=my_embeddings,
            distance_metric=DistanceStrategy.COSINE,
        )
        
        # Add documents
        texts = ["Couchbase is a NoSQL database", "LangChain is a framework for LLM applications"]
        vectorstore.add_texts(texts)
        
        # Search
        query = "What is Couchbase?"
        docs = vectorstore.similarity_search(query)


Couchbase Search Vector Store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Search vector store uses Search Vector Indexes to store and search document embeddings. Search Vector Indexes combine a Couchbase Search index with a vector column, allowing hybrid searches that combine vector searches with Full-Text Search (FTS) and geospatial searches.

For more information on Search Vector Indexes, see the `Couchbase Search Vector Index documentation <https://docs.couchbase.com/server/current/vector-search/vector-search.html>`_.

.. Note::
   This vector store is available in Couchbase Server versions 7.6 and above.


See a `complete search vector store usage example <https://python.langchain.com/docs/integrations/vectorstores/couchbase/>`_.

.. code-block:: python

    import getpass

    # Constants for the connection
    COUCHBASE_CONNECTION_STRING = getpass.getpass(
        "Enter the connection string for the Couchbase cluster: "
    )
    DB_USERNAME = getpass.getpass("Enter the username for the Couchbase cluster: ")
    DB_PASSWORD = getpass.getpass("Enter the password for the Couchbase cluster: ")

    # Create Couchbase connection object
    from datetime import timedelta

    from couchbase.auth import PasswordAuthenticator
    from couchbase.cluster import Cluster
    from couchbase.options import ClusterOptions

    auth = PasswordAuthenticator(DB_USERNAME, DB_PASSWORD)
    options = ClusterOptions(auth)
    cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)

    # Wait until the cluster is ready for use.
    cluster.wait_until_ready(timedelta(seconds=5))

    from langchain_couchbase import CouchbaseSearchVectorStore

    vector_store = CouchbaseSearchVectorStore(
        cluster=cluster,
        bucket_name=BUCKET_NAME,
        scope_name=SCOPE_NAME,
        collection_name=COLLECTION_NAME,
        embedding=my_embeddings,
        index_name=SEARCH_INDEX_NAME,
    )
    
    # Add documents
    texts = ["Couchbase is a NoSQL database", "LangChain is a framework for LLM applications"]
    vector_store.add_texts(texts)
    
    # Search
    query = "What is Couchbase?"
    docs = vector_store.similarity_search(query)

Cache
-----
Use Couchbase as a cache for LLM responses:

See a `complete cache usage example <https://python.langchain.com/docs/integrations/llm_caching/#couchbase-caches>`_.

.. code-block:: python

    from langchain_couchbase.cache import CouchbaseCache
    from langchain_core.globals import set_llm_cache

    cluster = couchbase_cluster_connection_object

    cache = CouchbaseCache(
        cluster=cluster,
        bucket_name=BUCKET_NAME,
        scope_name=SCOPE_NAME,
        collection_name=COLLECTION_NAME,
    )

    set_llm_cache(cache)

Semantic Cache
--------------

Semantic caching allows users to retrieve cached prompts based on the semantic similarity between the user input and previously cached inputs. 
Under the hood it uses Couchbase as both a cache and a vectorstore. The `CouchbaseSemanticCache` needs a Search Index defined to work. 
Please look at the usage example on how to set up the index.

See a `complete semantic cache usage example <https://python.langchain.com/docs/integrations/llm_caching/#couchbase-caches>`_.

.. code-block:: python

    from langchain_couchbase.cache import CouchbaseSemanticCache
    from langchain_core.globals import set_llm_cache
    from langchain_openai import OpenAIEmbeddings

    # use any embedding provider...
    embeddings = OpenAIEmbeddings()

    # Setup cache
    cluster = couchbase_cluster_connection_object

    cache = CouchbaseSemanticCache(
                cluster=cluster,
                embedding=embeddings,
                bucket_name=BUCKET_NAME,
                scope_name=SCOPE_NAME,
                collection_name=COLLECTION_NAME,
                index_name=INDEX_NAME,
        )

    # Set as global cache
    set_llm_cache(cache)


Chat Message History
--------------------

Use Couchbase as the storage for your chat messages.

See a `complete chat message history usage example <https://python.langchain.com/docs/integrations/memory/couchbase_chat_message_history/>`_.

.. code-block:: python

    from langchain_couchbase.chat_message_histories import CouchbaseChatMessageHistory
    
    message_history = CouchbaseChatMessageHistory(
        cluster=cluster,
        bucket_name=BUCKET_NAME,
        scope_name=SCOPE_NAME,
        collection_name=COLLECTION_NAME,
        session_id="test-session",
    )
    
    # Add messages
    message_history.add_user_message("Hello!")
    message_history.add_ai_message("Hi there! How can I help you today?")
    
    # Get messages
    messages = message_history.messages 