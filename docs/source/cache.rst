Couchbase Cache
==============

LangChain provides two powerful caching mechanisms integrated with Couchbase:

1. ``CouchbaseCache``: A standard key-value cache that stores exact LLM prompt-response pairs
2. ``CouchbaseSemanticCache``: An advanced semantic cache that matches similar prompts using vector similarity

These caching systems can dramatically reduce costs, improve application performance, and enhance user experience by avoiding redundant API calls to language models.

Benefits of LLM Caching
----------------------

Implementing LLM caching provides several key advantages:

* **Cost Reduction**: Minimize expensive API calls to commercial LLM providers
* **Latency Improvement**: Deliver faster responses for previously seen queries
* **Consistency**: Ensure consistent responses for identical or similar queries
* **Reliability**: Reduce dependency on external API availability
* **Scalability**: Handle higher volumes of requests without proportional cost increases

Standard Cache Implementation
---------------------------

The ``CouchbaseCache`` class provides a straightforward key-value caching mechanism that uses exact matching to identify cached responses.

How It Works
~~~~~~~~~~~

1. When a prompt is sent to an LLM, the cache generates a hash of the prompt and all relevant parameters (temperature, model, etc.)
2. This hash is used as a lookup key in the Couchbase collection
3. If a matching entry is found, the cached response is returned without calling the LLM
4. If no match is found, the LLM is called and the response is stored in the cache for future use

Example Usage
~~~~~~~~~~~~

Here's a complete example showing how to set up and use the standard cache:

.. code-block:: python

    from datetime import timedelta
    from langchain.globals import set_llm_cache
    from langchain_openai import OpenAI
    from couchbase.auth import PasswordAuthenticator
    from couchbase.cluster import Cluster
    from couchbase.options import ClusterOptions
    from langchain_couchbase.cache import CouchbaseCache

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

    # Initialize cache with a 1-day TTL
    cache = CouchbaseCache(
        cluster=cluster,
        bucket_name="langchain_bucket", 
        scope_name="_default", 
        collection_name="cache",
        ttl=timedelta(days=1)
    )

    # Set as the global LLM cache
    set_llm_cache(cache)

    # The LLM will now use the cache
    llm = OpenAI(temperature=0)
    
    # First call will hit the API and cache the result
    print("First call (not cached):")
    result1 = llm.invoke("What is the capital of France?")
    print(result1)
    
    # Second call with the same prompt will use the cached result
    print("\nSecond call (cached):")
    result2 = llm.invoke("What is the capital of France?")
    print(result2)
    
    # Different prompt will not use cache
    print("\nDifferent prompt (not cached):")
    result3 = llm.invoke("What is the capital of Italy?")
    print(result3)
    
    # Same prompt with different parameters will not use cache
    print("\nSame prompt, different temperature (not cached):")
    llm_different_temp = OpenAI(temperature=0.7)
    result4 = llm_different_temp.invoke("What is the capital of France?")
    print(result4)

Configuration Options
~~~~~~~~~~~~~~~~~~~

The ``CouchbaseCache`` class accepts several parameters:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``cluster``
     - A connected Couchbase Cluster object
   * - ``bucket_name``
     - Name of the bucket to store cache entries
   * - ``scope_name``
     - Name of the scope within the bucket (default: "_default")
   * - ``collection_name``
     - Name of the collection within the scope (default: "_default")
   * - ``ttl``
     - Optional time-to-live for cache entries (as timedelta)

Semantic Cache Implementation
---------------------------

The ``CouchbaseSemanticCache`` provides an intelligent caching mechanism that can match semantically similar prompts, not just identical ones. This is particularly valuable for natural language interactions where users might ask the same question in slightly different ways.

How It Works
~~~~~~~~~~~

1. When a prompt is sent to an LLM, the cache converts it to an embedding using the provided embedding model
2. This embedding is used to perform a vector similarity search in Couchbase
3. If a semantically similar prompt is found (above the specified similarity threshold), its cached response is returned
4. If no similar prompt is found, the LLM is called and the response is cached alongside the prompt embedding

Prerequisites
~~~~~~~~~~~

The semantic cache requires:

1. A properly configured vector index in Couchbase (similar to the one used for the vector store)
2. An embedding model to convert prompts to vector representations

Example Usage
~~~~~~~~~~~~

Here's a complete example showing how to set up and use the semantic cache:

.. code-block:: python

    from datetime import timedelta
    from langchain.globals import set_llm_cache
    from langchain_openai import OpenAI, OpenAIEmbeddings
    from couchbase.auth import PasswordAuthenticator
    from couchbase.cluster import Cluster
    from couchbase.options import ClusterOptions
    from langchain_couchbase.cache import CouchbaseSemanticCache

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

    # Initialize embeddings
    embeddings = OpenAIEmbeddings()

    # Initialize semantic cache with a similarity threshold
    semantic_cache = CouchbaseSemanticCache(
        cluster=cluster,
        embedding=embeddings,
        bucket_name="langchain_bucket",
        scope_name="_default", 
        collection_name="semantic_cache",
        index_name="semantic_cache_index",
        score_threshold=0.85,  # Only use cache if similarity is above this threshold
        ttl=timedelta(days=7)
    )

    # Set as the global LLM cache
    set_llm_cache(semantic_cache)

    # The LLM will now use the semantic cache
    llm = OpenAI(temperature=0)
    
    # First call will hit the API and cache the result
    print("First call (not cached):")
    result1 = llm.invoke("What is the capital of France?")
    print(result1)
    
    # This similar prompt will use the cached result if similarity is above threshold
    print("\nSimilar prompt (should be cached):")
    result2 = llm.invoke("Could you tell me the capital city of France?")
    print(result2)
    
    # Different prompt will not use cache
    print("\nDifferent prompt (not cached):")
    result3 = llm.invoke("What is the capital of Italy?")
    print(result3)

Creating the Index for Semantic Cache
----------------------------------

The semantic cache requires a vector index in Couchbase. Here's an example of how to create it:

.. code-block:: sql

    CREATE SEARCH INDEX semantic_cache_index 
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

Configuration Options
~~~~~~~~~~~~~~~~~~~

The ``CouchbaseSemanticCache`` accepts several parameters:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``cluster``
     - A connected Couchbase Cluster object
   * - ``embedding``
     - LangChain embedding function for creating embeddings
   * - ``bucket_name``
     - Name of the bucket to store cache entries
   * - ``scope_name``
     - Name of the scope within the bucket (default: "_default")
   * - ``collection_name``
     - Name of the collection within the scope (default: "_default")
   * - ``index_name``
     - Name of the vector search index
   * - ``score_threshold``
     - Minimum similarity score (0-1) to consider a match (default: 0.8)
   * - ``embedding_key``
     - Field name to store embeddings (default: "embedding")
   * - ``ttl``
     - Optional time-to-live for cache entries (as timedelta)

Cache Management
---------------

Both cache implementations provide methods for managing the cache:

Clearing the Cache
~~~~~~~~~~~~~~~~

To empty the cache:

.. code-block:: python

    # Clear the standard cache
    cache.clear()
    
    # Clear the semantic cache
    semantic_cache.clear()

Selective Updates
~~~~~~~~~~~~~~

You can manually add or update specific entries:

.. code-block:: python

    # For standard cache
    # This is rarely needed as the cache auto-populates
    from langchain_core.outputs import Generation
    
    prompt = "What is the meaning of life?"
    llm_string = "my-llm-model"
    generations = [Generation(text="42")]
    
    cache.update(prompt, llm_string, generations)

Inspecting Cache Contents
~~~~~~~~~~~~~~~~~~~~~~~

You can inspect cache contents using Couchbase's query capabilities:

.. code-block:: sql

    -- For standard cache
    SELECT * FROM your_bucket.your_scope.your_collection LIMIT 10;
    
    -- For semantic cache
    SELECT text, metadata FROM your_bucket.your_scope.your_collection LIMIT 10;

Best Practices
------------

For optimal caching performance and utility:

1. **Set Appropriate TTL**: Choose a time-to-live that balances freshness with caching benefits
   
2. **Monitor Cache Size**: Very large caches may impact Couchbase performance; consider periodic pruning
   
3. **Tune Semantic Threshold**: For semantic caching, experiment with the score_threshold to balance precision vs. recall
   
4. **Cache Per Context**: For multi-tenant applications, consider separate cache collections for different users or contexts
   
5. **Handle Versioning**: If your application changes LLM providers or models, clear or version your cache accordingly

API Reference
-----------

.. autoclass:: langchain_couchbase.cache.CouchbaseCache
   :members:
   :inherited-members:
   :exclude-members: _check_bucket_exists, _check_scope_and_collection_exists, _generate_key

.. autoclass:: langchain_couchbase.cache.CouchbaseSemanticCache
   :members: 
   :inherited-members:
   :exclude-members: _check_bucket_exists, _check_scope_and_collection_exists, _check_index_exists 