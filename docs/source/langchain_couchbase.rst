This page contains the complete API reference for the ``langchain-couchbase`` package. 
For usage examples and tutorials, see the :doc:`usage` page.

The package provides three main components:

* **Vector Stores** - Store and search document embeddings in Couchbase
   - Couchbase Query Vector Store (Hyperscale and Composite Vector Indexes)
   - Couchbase Search Vector Store (Search Vector Index)
* **Caching** - Cache LLM responses and enable semantic caching
* **Chat Message History** - Store conversation history in Couchbase

Vector Stores
-------------

Couchbase Query Vector Store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. Note::
   This vector store uses the Query and Index service to store and search document embeddings. It supports two types of vector indexes:
   
   * **Hyperscale Vector Index** - Optimized for pure vector searches on large datasets (billions of documents). Best for content discovery, recommendations, and applications requiring high accuracy with low memory footprint.
   
   * **Composite Vector Index** - Combines a Global Secondary Index (GSI) with a vector column. Ideal for searches combining vector similarity with scalar filters where scalars filter out large portions of the dataset.
   
   For guidance on choosing the right index type, see `Choose the Right Vector Index <https://docs.couchbase.com/cloud/vector-index/use-vector-indexes.html>`_.
   
   This vector store is available in Couchbase Server versions 8.0 and above.

.. automodule:: langchain_couchbase.vectorstores.query_vector_store
   :members:
   :show-inheritance:
   :undoc-members:

Couchbase Search Vector Store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. Note::
   This vector store uses Search Vector Indexes to store and search document embeddings. Search Vector Indexes combine a Couchbase Search index with a vector column, allowing hybrid searches that combine vector searches with Full-Text Search (FTS) and geospatial searches. This vector store is available in Couchbase Server versions 7.6 and above.

.. automodule:: langchain_couchbase.vectorstores.search_vector_store
   :members:
   :show-inheritance:
   :undoc-members:

Couchbase Vector Store
~~~~~~~~~~~~~~~~~~~~~~

.. warning::
   This class is deprecated since version 0.3.0 and will be removed in version 1.0.0.
   Use :class:`CouchbaseSearchVectorStore` instead.

.. automodule:: langchain_couchbase.vectorstores.vectorstores
   :members:
   :show-inheritance:
   :undoc-members:


Base Vector Store
~~~~~~~~~~~~~~~~~

.. automodule:: langchain_couchbase.vectorstores.base_vector_store
   :members:
   :show-inheritance:
   :undoc-members:

Caching
-------

.. automodule:: langchain_couchbase.cache
   :members:
   :show-inheritance:
   :undoc-members:

Chat Message History
--------------------

Couchbase Chat Message History
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: langchain_couchbase.chat_message_histories
   :members:
   :show-inheritance:
   :undoc-members:

Package Overview
----------------

.. automodule:: langchain_couchbase
   :members:
   :show-inheritance:
   :undoc-members:
