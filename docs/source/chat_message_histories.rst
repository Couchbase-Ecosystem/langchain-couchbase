Couchbase Chat Message History
==========================

The ``CouchbaseChatMessageHistory`` class provides a robust and scalable solution for storing, managing, and retrieving conversation history between users and AI systems using Couchbase as the persistence layer.

Overview
--------

In conversational AI applications, maintaining history between interactions is essential for creating natural, contextual experiences. The ``CouchbaseChatMessageHistory`` class implements LangChain's ``BaseChatMessageHistory`` interface, enabling your application to:

* Store messages from both human users and AI systems
* Retrieve complete conversation histories
* Organize conversations by session
* Set automatic expiration for old conversations
* Scale to support large numbers of concurrent users

By leveraging Couchbase's document model and indexing capabilities, this implementation provides excellent performance even with extensive chat histories.

Architecture
-----------

The ``CouchbaseChatMessageHistory`` stores each message as a separate document in a Couchbase collection, with fields for:

* Session ID: To group messages by conversation
* Message content: The actual message including role (human/AI) and content
* Timestamp: For ordering messages chronologically
* Additional metadata: Optional metadata can be attached to messages

This design allows for efficient retrieval and querying of conversation history across different dimensions.

Getting Started
--------------

To use the ``CouchbaseChatMessageHistory``, you need to first establish a connection to your Couchbase cluster:

.. code-block:: python

    from datetime import timedelta
    from couchbase.auth import PasswordAuthenticator
    from couchbase.cluster import Cluster
    from couchbase.options import ClusterOptions
    from langchain_couchbase.chat_message_histories import CouchbaseChatMessageHistory

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

    # Initialize chat message history with session ID
    message_history = CouchbaseChatMessageHistory(
        cluster=cluster,
        bucket_name="langchain_bucket",
        scope_name="_default",
        collection_name="chat_history",
        session_id="user123",  # Unique identifier for this conversation
        create_index=True,     # Create an index for efficient retrieval
        ttl=timedelta(days=30) # Messages expire after 30 days
    )

Configuration Parameters
----------------------

The ``CouchbaseChatMessageHistory`` constructor accepts several parameters for customization:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Description
   * - ``cluster``
     - A connected Couchbase Cluster object
   * - ``bucket_name``
     - Name of the bucket to store messages
   * - ``scope_name``
     - Name of the scope within the bucket (default: "_default")
   * - ``collection_name``
     - Name of the collection within the scope to store messages
   * - ``session_id``
     - Unique identifier for the conversation session
   * - ``session_id_key``
     - Field name for storing the session ID (default: "session_id")
   * - ``message_key``
     - Field name for storing message content (default: "message")
   * - ``create_index``
     - Whether to create an index for efficient retrieval (default: True)
   * - ``ttl``
     - Optional time-to-live for messages as a timedelta

Adding Messages
-------------

The primary way to add messages is through the ``add_message`` method, which accepts any LangChain message type:

.. code-block:: python

    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    # Add a system message (instructions)
    message_history.add_message(SystemMessage(content="You are a helpful assistant."))
    
    # Add messages from the human user
    message_history.add_message(HumanMessage(content="Hello, how are you?"))
    
    # Add responses from the AI
    message_history.add_message(AIMessage(content="I'm doing well, thank you for asking!"))

    # Add a message with additional metadata
    message_history.add_message(
        HumanMessage(
            content="Can you help me with a task?",
            additional_kwargs={"metadata": {"user_info": "premium_tier"}}
        )
    )

You can also add multiple messages at once with the ``add_messages`` method:

.. code-block:: python

    # Add multiple messages in sequence
    messages = [
        HumanMessage(content="What can you help me with today?"),
        AIMessage(content="I can help with a variety of tasks. What would you like assistance with?")
    ]
    message_history.add_messages(messages)

Internally, each message is stored as a separate document in the Couchbase collection, with:
- The session ID to group messages by conversation
- The current timestamp for chronological ordering
- The serialized message content including role and text

Retrieving Messages
----------------

To retrieve all messages for the current session:

.. code-block:: python

    # Get all messages in this session
    all_messages = message_history.messages
    
    # Display messages in order
    for message in all_messages:
        if isinstance(message, HumanMessage):
            print(f"Human: {message.content}")
        elif isinstance(message, AIMessage):
            print(f"AI: {message.content}")
        elif isinstance(message, SystemMessage):
            print(f"System: {message.content}")

Behind the scenes, the implementation:
1. Queries Couchbase for all documents matching the current session_id
2. Orders messages by timestamp to maintain conversation flow
3. Deserializes each document back into the appropriate LangChain message type

Clearing Messages
--------------

To remove all messages for a specific session:

.. code-block:: python

    # Clear all messages for this session
    message_history.clear()

This operation removes all documents with the matching session_id from the collection.

Using with LangChain Chains and Agents
------------------------------------

The chat message history integrates seamlessly with LangChain's conversation components:

.. code-block:: python

    from langchain_openai import ChatOpenAI
    from langchain.chains import ConversationChain
    from langchain.memory import ConversationBufferMemory

    # Create a memory instance with the Couchbase message history
    memory = ConversationBufferMemory(
        chat_memory=message_history,
        return_messages=True
    )

    # Create a conversation chain with the memory
    conversation = ConversationChain(
        llm=ChatOpenAI(),
        memory=memory,
        verbose=True
    )

    # The conversation will now persist across sessions
    response = conversation.invoke("Hello, my name is Alice")
    print(response)
    
    # Later interactions will have access to the history
    response = conversation.invoke("What's my name?")
    print(response)  # The AI should remember the name "Alice"

This enables building stateful, context-aware applications that can continue conversations across multiple interactions or sessions.

Multi-User Management
-------------------

For applications supporting multiple users, create separate instances for each user:

.. code-block:: python

    # Create chat histories for different users
    def get_user_chat_history(user_id):
        return CouchbaseChatMessageHistory(
            cluster=cluster,
            bucket_name="langchain_bucket",
            scope_name="_default",
            collection_name="chat_history",
            session_id=user_id
        )
    
    # Usage example
    alice_history = get_user_chat_history("alice_user_id")
    bob_history = get_user_chat_history("bob_user_id")
    
    # Each user's conversations are kept separate
    alice_history.add_message(HumanMessage(content="Hello, I'm Alice"))
    bob_history.add_message(HumanMessage(content="Hi there, Bob here"))

The same collection can efficiently store conversations for thousands or millions of users, with queries only retrieving messages for the specific session_id.

Database Schema and Indexing
--------------------------

When the ``create_index`` parameter is set to ``True`` (the default), the implementation automatically creates a compound index on:

1. The session_id field - for quick lookup of conversations
2. The timestamp field - for chronological ordering
3. The message field - for efficient retrieval of message content

This index greatly improves query performance, especially for longer conversation histories.

The index is created with this SQL statement (executed internally):

.. code-block:: sql

    CREATE INDEX LANGCHAIN_CHAT_HISTORY IF NOT EXISTS 
    ON collection_name(session_id_key, ts_key, message_key)

Message Expiration
----------------

To automatically expire old conversations, provide a ``ttl`` parameter:

.. code-block:: python

    # Messages will be automatically deleted after 7 days
    message_history = CouchbaseChatMessageHistory(
        cluster=cluster,
        bucket_name="langchain_bucket",
        scope_name="_default",
        collection_name="chat_history",
        session_id="user123",
        ttl=timedelta(days=7)  # Set message expiration time
    )

Couchbase's TTL (Time-To-Live) feature will automatically remove documents after the specified duration, helping manage database size and comply with data retention policies.

Performance Considerations
------------------------

For optimal performance with ``CouchbaseChatMessageHistory``:

1. **Indexing**: Always enable the ``create_index`` option for production use

2. **Batch Operations**: For loading historical data, batch message additions when possible

3. **Session Granularity**: Choose appropriate session_id values:
   - Too broad (e.g., one session per user) may lead to very large conversation histories
   - Too granular (e.g., new session per interaction) loses conversational context

4. **TTL Management**: Set appropriate TTL values to balance history retention with database size

5. **Production Scaling**: For high-volume applications, consider:
   - Separate Couchbase bucket or scope for chat histories
   - Additional indices for specialized queries
   - Monitoring document count and size

API Reference
-----------

.. autoclass:: langchain_couchbase.chat_message_histories.CouchbaseChatMessageHistory
   :members:
   :inherited-members:
   :exclude-members: _check_bucket_exists, _check_scope_and_collection_exists 