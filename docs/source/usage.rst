.. _usage:

Usage
=====

``langchain-couchbase`` provides several components to integrate Couchbase with LangChain:

Vector Store
-----------

Use Couchbase as a vector store for your embeddings:

.. code-block:: python

    from langchain.embeddings import OpenAIEmbeddings
    from langchain_couchbase.vectorstores import CouchbaseVectorStore
    
    embeddings = OpenAIEmbeddings()
    
    vectorstore = CouchbaseVectorStore(
        connection_string="couchbase://localhost",
        username="Administrator",
        password="password",
        bucket_name="vector_bucket",
        scope_name="_default",
        collection_name="vector_collection",
        embedding=embeddings
    )
    
    # Add documents
    texts = ["Couchbase is a NoSQL database", "LangChain is a framework for LLM applications"]
    vectorstore.add_texts(texts)
    
    # Search
    query = "What is Couchbase?"
    docs = vectorstore.similarity_search(query)

Cache
-----

Use Couchbase as a cache for LLM responses:

.. code-block:: python

    from langchain.cache import BaseCache
    from langchain_couchbase.cache import CouchbaseCache
    from langchain.globals import set_llm_cache
    
    # Setup cache
    cache = CouchbaseCache(
        connection_string="couchbase://localhost",
        username="Administrator",
        password="password",
        bucket_name="langchain",
        scope_name="_default", 
        collection_name="llm_cache"
    )
    
    # Set as global cache
    set_llm_cache(cache)

Chat Message History
-------------------

Store chat history in Couchbase:

.. code-block:: python

    from langchain_couchbase.chat_message_histories import CouchbaseChatMessageHistory
    
    message_history = CouchbaseChatMessageHistory(
        connection_string="couchbase://localhost",
        username="Administrator",
        password="password",
        bucket_name="langchain",
        scope_name="_default",
        collection_name="chat_history",
        session_id="user-123"
    )
    
    # Add messages
    message_history.add_user_message("Hello!")
    message_history.add_ai_message("Hi there! How can I help you today?")
    
    # Get messages
    messages = message_history.messages 