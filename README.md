# langchain-couchbase

This package contains the LangChain integration with Couchbase

## Installation

```bash
pip install -U langchain-couchbase
```

## Vector Store

`CouchbaseVectorStore` class enables the usage of Couchbase for Vector Search.

```python
from langchain_couchbase import CouchbaseSearchVectorStore
```

To use this in an application:

```python
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

vector_store = CouchbaseSearchVectorStore(
    cluster=cluster,
    bucket_name=BUCKET_NAME,
    scope_name=SCOPE_NAME,
    collection_name=COLLECTION_NAME,
    embedding=my_embeddings,
    index_name=SEARCH_INDEX_NAME,
)
```

See a [usage example](https://python.langchain.com/docs/integrations/vectorstores/couchbase/)

## LLM Caches

### CouchbaseCache

Use Couchbase as a cache for prompts and responses.

See a [usage example](https://python.langchain.com/docs/integrations/llm_caching/#couchbase-caches).

To import this cache:

```python
from langchain_couchbase.cache import CouchbaseCache
```

To use this cache with your LLMs:

```python
from langchain_core.globals import set_llm_cache

cluster = couchbase_cluster_connection_object

set_llm_cache(
    CouchbaseCache(
        cluster=cluster,
        bucket_name=BUCKET_NAME,
        scope_name=SCOPE_NAME,
        collection_name=COLLECTION_NAME,
    )
)
```

### CouchbaseSemanticCache

Semantic caching allows users to retrieve cached prompts based on the semantic similarity between the user input and previously cached inputs. Under the hood it uses Couchbase as both a cache and a vectorstore. The `CouchbaseSemanticCache` needs a Search Index defined to work. Please look at the usage example on how to set up the index.

See a [usage example](https://python.langchain.com/docs/integrations/llm_caching/#couchbase-caches).

To import this cache:

```python
from langchain_couchbase.cache import CouchbaseSemanticCache
```

To use this cache with your LLMs:

```python
from langchain_core.globals import set_llm_cache

# use any embedding provider...

from langchain_openai.Embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
cluster = couchbase_cluster_connection_object

set_llm_cache(
    CouchbaseSemanticCache(
        cluster=cluster,
        embedding = embeddings,
        bucket_name=BUCKET_NAME,
        scope_name=SCOPE_NAME,
        collection_name=COLLECTION_NAME,
        index_name=INDEX_NAME,
    )
)
```

## Chat Message History

Use Couchbase as the storage for your chat messages.

See a [usage example](https://python.langchain.com/docs/integrations/memory/couchbase_chat_message_history/).

To use the chat message history in your applications:

```python
from langchain_couchbase.chat_message_histories import CouchbaseChatMessageHistory

message_history = CouchbaseChatMessageHistory(
    cluster=cluster,
    bucket_name=BUCKET_NAME,
    scope_name=SCOPE_NAME,
    collection_name=COLLECTION_NAME,
    session_id="test-session",
)

message_history.add_user_message("hi!")
```
