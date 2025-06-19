This page contains the complete API reference for the ``langchain-couchbase`` package. 
For usage examples and tutorials, see the :doc:`usage` page.

The package provides three main components:

* **Vector Stores** - Store and search document embeddings in Couchbase
* **Caching** - Cache LLM responses and enable semantic caching
* **Chat Message History** - Store conversation history in Couchbase

Vector Stores
-------------

Couchbase Search Vector Store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
