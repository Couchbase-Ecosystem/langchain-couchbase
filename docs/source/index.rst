LangChain Couchbase Documentation
================================

``langchain-couchbase`` is a comprehensive integration package that enables seamless interactions between LangChain and `Couchbase <https://www.couchbase.com/>`_, a distributed NoSQL database platform.

Why Use Couchbase with LangChain?
---------------------------------

Couchbase offers several advantages for LangChain applications:

* **Vector Search**: Couchbase provides built-in vector search capabilities, allowing for efficient similarity searches over embeddings.
* **Document Storage**: As a JSON document database, Couchbase is ideal for storing and retrieving structured data like chat messages and LLM responses.
* **Scalability**: Built for distributed environments, Couchbase can scale horizontally to handle growing data volumes.
* **Performance**: In-memory caching combined with disk persistence delivers high throughput and low latency.
* **Durability**: Multi-node replication ensures data durability and high availability.

Key Integrations
---------------

This package provides the following integrations with LangChain:

* **Vector Stores**: The ``CouchbaseVectorStore`` class enables storing, managing, and querying document embeddings for semantic search and retrieval.
* **Caching Mechanisms**: Both standard (``CouchbaseCache``) and semantic (``CouchbaseSemanticCache``) caching options help reduce LLM API costs and improve response times by reusing previous results.
* **Chat Message History**: The ``CouchbaseChatMessageHistory`` class provides persistent storage for conversation history in chat applications.

Usage Scenarios
--------------

The Couchbase integrations are particularly valuable for:

* **Production LLM Applications**: When moving from prototypes to production, Couchbase provides the reliability and performance needed for business-critical applications.
* **Multi-User Systems**: Applications supporting many concurrent users benefit from Couchbase's distributed architecture.
* **Enterprise Deployments**: Organizations with existing Couchbase infrastructure can integrate LangChain applications with their data platform.
* **High-Volume Retrieval Augmented Generation (RAG)**: Efficient vector search, combined with JSON document storage, enables sophisticated RAG applications at scale.

Getting Started
--------------

To get started with the LangChain Couchbase integrations:

1. Install the package: ``pip install langchain-couchbase``
2. Set up a Couchbase cluster or use Couchbase Cloud
3. Create appropriate buckets, scopes, and collections
4. Follow the integration-specific guides in this documentation

Repository: `GitHub Repository <https://github.com/langchain-ai/langchain-couchbase>`_

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   installation
   vectorstores
   cache
   chat_message_histories
   api_reference

Prerequisites
------------

To use these integrations, you'll need:

* Python 3.8 or later
* A Couchbase server (version 7.0 or later recommended)
* Appropriate credentials for your Couchbase cluster

For the vector store functionality, you'll also need a compatible embedding provider, such as:

* OpenAI embeddings (via ``langchain-openai``)
* Hugging Face embeddings (via ``langchain-huggingface``) 
* Any other embedding model supported by LangChain

Contributing
-----------

Contributions to this integration are welcome! To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For more details, see the `contributing guidelines <https://github.com/langchain-ai/langchain-couchbase/blob/main/CONTRIBUTING.md>`_.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 