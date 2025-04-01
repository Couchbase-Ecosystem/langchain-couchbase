.. langchain-couchbase documentation master file, created by
   sphinx-quickstart on Thu Mar 27 22:25:59 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

langchain-couchbase
===================

**Couchbase integrations for LangChain**

.. image:: https://img.shields.io/pypi/v/langchain-couchbase.svg
   :target: https://pypi.org/project/langchain-couchbase/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/langchain-couchbase.svg
   :target: https://pypi.org/project/langchain-couchbase/
   :alt: Python Versions

langchain-couchbase provides integrations for using Couchbase with LangChain. This package contains the following modules:

* **Vector Stores**: Store and search embeddings in Couchbase
* **Memory**: Chat message history backed by Couchbase
* **Cache**: LLM cache using Couchbase

Installation
------------

.. code-block:: bash

   pip install langchain-couchbase

Quick Start
-----------

Here's a simple example of using Couchbase as a vector store:

.. code-block:: python

   from langchain_couchbase import CouchbaseVectorStore
   from langchain_core.embeddings import FakeEmbeddings

   # Create a vector store
   vectorstore = CouchbaseVectorStore(
       connection_string="couchbase://localhost",
       username="Administrator",
       password="password",
       bucket_name="vector_store",
       scope_name="_default",
       collection_name="embeddings",
       embedding=FakeEmbeddings(size=1536)
   )

   # Add documents
   vectorstore.add_texts(["Hello world", "Bye bye", "Hello there"])

   # Perform similarity search
   result = vectorstore.similarity_search("Hello", k=1)
   print(result)

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules


Project Links
-------------

* `GitHub <https://github.com/langchain-ai/langchain-couchbase>`_
* `PyPI <https://pypi.org/project/langchain-couchbase/>`_
* `LangChain Documentation <https://python.langchain.com>`_

