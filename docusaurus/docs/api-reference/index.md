# LangChain Couchbase API Reference

This document provides a comprehensive reference for the `langchain-couchbase` package, which integrates LangChain with Couchbase.

## Installation

```bash
pip install -U langchain-couchbase
```

## Table of Contents

- [CouchbaseVectorStore](#couchbasevectorstore)
- [CouchbaseCache](#couchbasecache)
- [CouchbaseSemanticCache](#couchbasesemanticcache)
- [CouchbaseChatMessageHistory](#couchbasechatmessagehistory)

---

## CouchbaseVectorStore

`CouchbaseVectorStore` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/vectorstores.py#L26-L173)) enables the usage of Couchbase for Vector Search.

### Import

```python
from langchain_couchbase import CouchbaseVectorStore
```

### Constructor Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| cluster | Cluster | Yes | - | Couchbase cluster object with active connection |
| bucket_name | str | Yes | - | Name of bucket to store documents in |
| scope_name | str | Yes | - | Name of scope in the bucket to store documents in |
| collection_name | str | Yes | - | Name of collection in the scope to store documents in |
| embedding | Embeddings | Yes | - | Embedding function to use |
| index_name | str | Yes | - | Name of the Search index to use |
| text_key | str | No | "text" | Key in document to use as text |
| embedding_key | str | No | "embedding" | Key in document to use for the embeddings |
| scoped_index | bool | No | True | Specify whether the index is a scoped index |

### Key Methods

#### `add_texts` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/vectorstores.py#L342-L415))

Add texts to the vector store.

```python
def add_texts(
    self,
    texts: Iterable[str],
    metadatas: Optional[List[dict]] = None,
    ids: Optional[List[str]] = None,
    batch_size: Optional[int] = None,
    **kwargs: Any,
) -> List[str]
```

#### `similarity_search` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/vectorstores.py#L471-L499))

Return documents most similar to the query.

```python
def similarity_search(
    self,
    query: str,
    k: int = 4,
    search_options: Optional[Dict[str, Any]] = {},
    **kwargs: Any,
) -> List[Document]
```

#### `similarity_search_with_score` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/vectorstores.py#L577-L605))

Return documents most similar to the query with their scores.

```python
def similarity_search_with_score(
    self,
    query: str,
    k: int = 4,
    search_options: Optional[Dict[str, Any]] = {},
    **kwargs: Any,
) -> List[Tuple[Document, float]]
```

#### `delete` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/vectorstores.py#L415-L432))

Delete documents from the vector store by IDs.

```python
def delete(self, ids: Optional[List[str]] = None, **kwargs: Any) -> Optional[bool]
```

### Usage Example

```python
import getpass
from datetime import timedelta
from langchain_openai import OpenAIEmbeddings
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from langchain_couchbase import CouchbaseVectorStore

# Constants for the connection
COUCHBASE_CONNECTION_STRING = getpass.getpass("Enter the connection string for the Couchbase cluster: ")
DB_USERNAME = getpass.getpass("Enter the username for the Couchbase cluster: ")
DB_PASSWORD = getpass.getpass("Enter the password for the Couchbase cluster: ")
BUCKET_NAME = "langchain_bucket"
SCOPE_NAME = "_default"
COLLECTION_NAME = "default"
SEARCH_INDEX_NAME = "langchain-test-index"

# Create Couchbase connection object
auth = PasswordAuthenticator(DB_USERNAME, DB_PASSWORD)
options = ClusterOptions(auth)
cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)

# Wait until the cluster is ready for use.
cluster.wait_until_ready(timedelta(seconds=5))

# Initialize embeddings
embeddings = OpenAIEmbeddings()

# Create vector store
vector_store = CouchbaseVectorStore(
    cluster=cluster,
    bucket_name=BUCKET_NAME,
    scope_name=SCOPE_NAME,
    collection_name=COLLECTION_NAME,
    embedding=embeddings,
    index_name=SEARCH_INDEX_NAME,
)

# Add documents
from langchain_core.documents import Document
document_1 = Document(page_content="foo", metadata={"baz": "bar"})
document_2 = Document(page_content="thud", metadata={"bar": "baz"})
vector_store.add_documents([document_1, document_2])

# Search
results = vector_store.similarity_search("thud", k=1)
for doc in results:
    print(f"* {doc.page_content} [{doc.metadata}]")

# Search with score
results = vector_store.similarity_search_with_score("thud", k=1)
for doc, score in results:
    print(f"* [SIM={score:3f}] {doc.page_content} [{doc.metadata}]")
```

---

## CouchbaseCache

`CouchbaseCache` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/cache.py#L101-L147)) allows using Couchbase as a cache for prompts and responses.

### Import

```python
from langchain_couchbase.cache import CouchbaseCache
```

### Constructor Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| cluster | Cluster | Yes | - | Couchbase cluster object with active connection |
| bucket_name | str | Yes | - | Name of the bucket to store documents in |
| scope_name | str | Yes | - | Name of the scope in bucket to store documents in |
| collection_name | str | Yes | - | Name of the collection in the scope to store documents in |
| ttl | Optional[timedelta] | No | None | Time to live for the document in the cache |

### Key Methods

#### `lookup` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/cache.py#L208-L221))

Look up from cache based on prompt and llm_string.

```python
def lookup(self, prompt: str, llm_string: str) -> Optional[RETURN_VAL_TYPE]
```

#### `update` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/cache.py#L222-L241))

Update cache based on prompt and llm_string.

```python
def update(self, prompt: str, llm_string: str, return_val: RETURN_VAL_TYPE) -> None
```

#### `clear` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/cache.py#L242-L252))

Clear the cache.

```python
def clear(self, **kwargs: Any) -> None
```

### Usage Example

```python
from datetime import timedelta
from langchain_core.globals import set_llm_cache
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from langchain_couchbase.cache import CouchbaseCache

# Create Couchbase connection object
auth = PasswordAuthenticator(DB_USERNAME, DB_PASSWORD)
options = ClusterOptions(auth)
cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)

# Wait until the cluster is ready for use.
cluster.wait_until_ready(timedelta(seconds=5))

# Set up the cache
set_llm_cache(
    CouchbaseCache(
        cluster=cluster,
        bucket_name=BUCKET_NAME,
        scope_name=SCOPE_NAME,
        collection_name=COLLECTION_NAME,
    )
)

# Now any LLM calls will use the cache
from langchain_openai import OpenAI
llm = OpenAI(temperature=0)
# First call will be executed and cached
result1 = llm.invoke("What is the capital of France?")
# Second call with the same prompt will be retrieved from cache
result2 = llm.invoke("What is the capital of France?")
```

---

## CouchbaseSemanticCache

`CouchbaseSemanticCache` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/cache.py#L255-L337)) allows retrieving cached prompts based on the semantic similarity between the user input and previously cached inputs.

### Import

```python
from langchain_couchbase.cache import CouchbaseSemanticCache
```

### Constructor Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| cluster | Cluster | Yes | - | Couchbase cluster object with active connection |
| embedding | Embeddings | Yes | - | Embedding model to use |
| bucket_name | str | Yes | - | Name of the bucket to store documents in |
| scope_name | str | Yes | - | Name of the scope in bucket to store documents in |
| collection_name | str | Yes | - | Name of the collection in the scope to store documents in |
| index_name | str | Yes | - | Name of the Search index to use |
| score_threshold | Optional[float] | No | None | Score threshold to use for filtering results |
| ttl | Optional[timedelta] | No | None | Time to live for the document in the cache |

### Key Methods

#### `lookup` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/cache.py#L338-L359))

Look up from cache based on the semantic similarity of the prompt.

```python
def lookup(self, prompt: str, llm_string: str) -> Optional[RETURN_VAL_TYPE]
```

#### `update` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/cache.py#L360-L375))

Update cache based on the prompt and llm_string.

```python
def update(self, prompt: str, llm_string: str, return_val: RETURN_VAL_TYPE) -> None
```

#### `clear` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/cache.py#L376-L386))

Clear the cache.

```python
def clear(self, **kwargs: Any) -> None
```

### Usage Example

```python
from datetime import timedelta
from langchain_core.globals import set_llm_cache
from langchain_openai import OpenAIEmbeddings
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from langchain_couchbase.cache import CouchbaseSemanticCache

# Create Couchbase connection object
auth = PasswordAuthenticator(DB_USERNAME, DB_PASSWORD)
options = ClusterOptions(auth)
cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)

# Wait until the cluster is ready for use.
cluster.wait_until_ready(timedelta(seconds=5))

# Initialize embeddings
embeddings = OpenAIEmbeddings()

# Set up the semantic cache
set_llm_cache(
    CouchbaseSemanticCache(
        cluster=cluster,
        embedding=embeddings,
        bucket_name=BUCKET_NAME,
        scope_name=SCOPE_NAME,
        collection_name=COLLECTION_NAME,
        index_name=INDEX_NAME,
    )
)

# Now any LLM calls will use the semantic cache
from langchain_openai import OpenAI
llm = OpenAI(temperature=0)
# First call will be executed and cached
result1 = llm.invoke("What is the capital of France?")
# Second call with a semantically similar prompt will be retrieved from cache
result2 = llm.invoke("Tell me the capital city of France")
```

---

## CouchbaseChatMessageHistory

`CouchbaseChatMessageHistory` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/chat_message_histories.py#L36-L95)) allows using Couchbase as the storage for chat messages.

### Import

```python
from langchain_couchbase.chat_message_histories import CouchbaseChatMessageHistory
```

### Constructor Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| cluster | Cluster | Yes | - | Couchbase cluster object with active connection |
| bucket_name | str | Yes | - | Name of the bucket to store documents in |
| scope_name | str | Yes | - | Name of the scope in bucket to store documents in |
| collection_name | str | Yes | - | Name of the collection in the scope to store documents in |
| session_id | str | Yes | - | Value for the session used to associate messages from a single chat session |
| session_id_key | str | No | "session_id" | Name of the field to use for the session id |
| message_key | str | No | "message" | Name of the field to use for the messages |
| create_index | bool | No | True | Create an index if True |
| ttl | Optional[timedelta] | No | None | Time to live for the documents in the collection |

### Key Methods

#### `add_message` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/chat_message_histories.py#L170-L200))

Add a message to the chat history.

```python
def add_message(self, message: BaseMessage) -> None
```

#### `add_messages` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/chat_message_histories.py#L201-L231))

Add multiple messages to the chat history in a batched manner.

```python
def add_messages(self, messages: Sequence[BaseMessage]) -> None
```

#### `clear` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/chat_message_histories.py#L232-L244))

Clear the chat history.

```python
def clear(self) -> None
```

#### `messages` ([source](https://github.com/Couchbase-Ecosystem/langchain-couchbase/blob/main/langchain_couchbase/chat_message_histories.py#L244-L266)) (property)

Get all messages in the chat history associated with the session_id.

```python
@property
def messages(self) -> List[BaseMessage]
```

### Usage Example

```python
from datetime import timedelta
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from langchain_couchbase.chat_message_histories import CouchbaseChatMessageHistory

# Create Couchbase connection object
auth = PasswordAuthenticator(DB_USERNAME, DB_PASSWORD)
options = ClusterOptions(auth)
cluster = Cluster(COUCHBASE_CONNECTION_STRING, options)

# Wait until the cluster is ready for use.
cluster.wait_until_ready(timedelta(seconds=5))

# Create chat message history
message_history = CouchbaseChatMessageHistory(
    cluster=cluster,
    bucket_name=BUCKET_NAME,
    scope_name=SCOPE_NAME,
    collection_name=COLLECTION_NAME,
    session_id="test-session",
)

# Create memory with the message history
memory = ConversationBufferMemory(
    memory_key="chat_history",
    chat_memory=message_history,
    return_messages=True
)

# Add messages
message_history.add_user_message("Hello, how are you?")
message_history.add_ai_message("I'm doing well, thank you for asking!")

# Add multiple messages at once
messages = [
    HumanMessage(content="What can you help me with today?"),
    AIMessage(content="I can help you with a variety of tasks. What do you need assistance with?")
]
message_history.add_messages(messages)

# Retrieve all messages
all_messages = message_history.messages
for message in all_messages:
    print(f"{message.type}: {message.content}")

# Clear the history
message_history.clear()
```