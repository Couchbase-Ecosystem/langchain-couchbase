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

### Documentation

#### Generating Documentation Locally

To generate the documentation locally, follow these steps:

1. Ensure you have the project installed in your environment:
```bash
pip install -e .  # Install in development mode
```

2. Install the required documentation dependencies:
```bash
pip install sphinx sphinx-rtd-theme tomli
```

3. Navigate to the docs directory:
```bash
cd docs
```

4. Ensure the _static directory exists:
```bash
mkdir -p source/_static
```

5. Build the HTML documentation:
```bash
make html
```

6. The generated documentation will be available in the `docs/build/html` directory. You can open `index.html` in your browser to view it:
```bash
# On macOS
open build/html/index.html
# On Linux
xdg-open build/html/index.html
# On Windows
start build/html/index.html
```

#### Additional Documentation Commands

- To clean the build directory before rebuilding:
```bash
make clean html
```

- To check for broken links in the documentation:
```bash
make linkcheck
```

- To generate a PDF version of the documentation (requires LaTeX):
```bash
make latexpdf
```

- For help on available make commands:
```bash
make help
```

#### Troubleshooting

- If you encounter errors about missing modules, ensure you have installed the project in your environment.
- If Sphinx can't find your package modules, verify your `conf.py` has the correct path configuration.
- For sphinx-specific errors, refer to the [Sphinx documentation](https://www.sphinx-doc.org/).
- If you see an error about missing `tomli` module, make sure you've installed it with `pip install tomli`.


## 📢 Support Policy

We truly appreciate your interest in this project!  
This project is **community-maintained**, which means it's **not officially supported** by our support team.

If you need help, have found a bug, or want to contribute improvements, the best place to do that is right here — by [opening a GitHub issue](https://github.com/Couchbase-Ecosystem/langchain-couchbase/issues).  
Our support portal is unable to assist with requests related to this project, so we kindly ask that all inquiries stay within GitHub.

Your collaboration helps us all move forward together — thank you!
