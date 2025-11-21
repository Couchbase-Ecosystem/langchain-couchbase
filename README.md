# langchain-couchbase

This package contains the official [LangChain](https://python.langchain.com/docs/introduction/) integration with Couchbase

The documentation and API Reference can be found on [Github Pages](https://couchbase-ecosystem.github.io/langchain-couchbase/index.html).

## Installation

```bash
pip install -U langchain-couchbase
```

## Vector Store

### CouchbaseQueryVectorStore
`CouchbaseQueryVectorStore` class enables the usage of Couchbase for Vector Search using the Query and Indexing Service. It implements two different types of vector indices:
 - [Hyperscale Vector Index](https://docs.couchbase.com/server/current/vector-index/hyperscale-vector-index.html)
 - [Composite Vector Index](https://docs.couchbase.com/server/current/vector-index/composite-vector-index.html)

> Note: CouchbaseQueryVectorStore requires Couchbase Server version 8.0 and above.

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

from langchain_couchbase import CouchbaseQueryVectorStore
from langchain_couchbase.vectorstores import DistanceStrategy

vector_store = CouchbaseQueryVectorStore(
    cluster=cluster,
    bucket_name=BUCKET_NAME,
    scope_name=SCOPE_NAME,
    collection_name=COLLECTION_NAME,
    embedding=my_embeddings,
    distance_metric=DistanceStrategy.DOT
)
```

See a [usage example](https://github.com/couchbaselabs/query-vector-search-demo)


### CouchbaseSearchVectorStore

`CouchbaseSearchVectorStore` class enables the usage of Couchbase for Vector Search using the [Search Service](https://docs.couchbase.com/server/current/vector-search/vector-search.html).

> Note: CouchbaseSearchVectorStore requires Couchbase Server version 7.6 and above.

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

from langchain_couchbase import CouchbaseSearchVectorStore

vector_store = CouchbaseSearchVectorStore(
    cluster=cluster,
    bucket_name=BUCKET_NAME,
    scope_name=SCOPE_NAME,
    collection_name=COLLECTION_NAME,
    embedding=my_embeddings,
    index_name=SEARCH_INDEX_NAME,
)
```

See a [usage example](https://github.com/couchbase-examples/hybrid-search-demo)

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

from langchain_openai import OpenAIEmbeddings

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

cluster = couchbase_cluster_connection_object

message_history = CouchbaseChatMessageHistory(
    cluster=cluster,
    bucket_name=BUCKET_NAME,
    scope_name=SCOPE_NAME,
    collection_name=COLLECTION_NAME,
    session_id="test-session",
)

message_history.add_user_message("hi!")
```

<details>
<summary><strong>Documentation</strong></summary>

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

4. Ensure the build directory exists:
```bash
mkdir -p source/build
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
<br/>
</details>


## Contributing

We welcome pull requests! The steps below are what we use locally when iterating on the project.

### Local environment

1. Install [Poetry](https://python-poetry.org/docs/#installation) if you do not already have it.
2. Clone the repository and move into the project directory:

```bash
git clone https://github.com/Couchbase-Ecosystem/langchain-couchbase.git
cd langchain-couchbase
```

3. Install the dependencies needed for development and testing:

```bash
poetry install --with test,test_integration,lint,typing
```

   The command above pulls in optional groups defined in `pyproject.toml` so you have pytest, linters, type checking, and spell checking tools available.

4. Activate the virtual environment when you want an interactive shell:

```bash
poetry shell
```

### Running tests and quality checks

- Run the fast unit-test suite (uses `pytest --disable-socket`):

```bash
make test
```

- Run the full integration tests (requires a running Couchbase cluster and the indexes defined in `tests/fixtures/`):

```bash
make integration_tests
```

- Execute an individual test file:

```bash
make test TEST_FILE=tests/path/to/test_file.py
```

- Run linting, formatting, and type checks together:

```bash
make lint
```

- Format Python files automatically:

```bash
make format
```

You can also invoke the underlying commands directly, e.g. `poetry run pytest` or `poetry run ruff check .`, if you prefer not to use `make`.

### Couchbase setup for tests

Integration tests exercise a real Couchbase cluster. To run them locally:

1. **Run Couchbase Server 8.0+** (or Capella) with the Data, Query and Search services enabled. Make sure you can connect with a user that has at least admin privileges for the bucket you will use.

2. **Create the data containers.**
   - Bucket: choose any name (e.g. `langchain`).
   - Scope: choose any name (e.g. `langchain`).
   - Collections (within the scope):
     - one for vector store tests → set `COUCHBASE_COLLECTION_NAME`.
     - one for basic cache tests → set `COUCHBASE_CACHE_COLLECTION_NAME`.
     - one for semantic cache tests → set `COUCHBASE_SEMANTIC_CACHE_COLLECTION_NAME`.
     - one for chat history tests → set `COUCHBASE_CHAT_HISTORY_COLLECTION_NAME`.

3. **Create the required Search indexes.**
   - Copy `tests/fixtures/search_index_definition_for_vector_store_testing.json` and replace the `<<SCOPE_NAME>>`, `<<COLLECTION_NAME>>`, and `<<INDEX_NAME>>` placeholders with the values you created above. Apply the definition through the Couchbase UI (FTS → Import JSON).
   - Repeat the process for `tests/fixtures/search_index_definition_for_cache_testing.json`, using a distinct `COUCHBASE_SEMANTIC_CACHE_INDEX_NAME`. (The semantic cache requires a Search index with vector fields.)

4. **Export the environment variables** before running tests. The integration suite reads the following values:

   ```bash
   export COUCHBASE_CONNECTION_STRING="couchbase://localhost"
   export COUCHBASE_USERNAME="Administrator"
   export COUCHBASE_PASSWORD="password"
   export COUCHBASE_BUCKET_NAME="langchain"
   export COUCHBASE_SCOPE_NAME="langchain"
   export COUCHBASE_COLLECTION_NAME="vector_docs"
   export COUCHBASE_INDEX_NAME="langchain_vector_index"
   export COUCHBASE_CACHE_COLLECTION_NAME="cache_docs"
   export COUCHBASE_SEMANTIC_CACHE_COLLECTION_NAME="semantic_cache_docs"
   export COUCHBASE_SEMANTIC_CACHE_INDEX_NAME="langchain_cache_index"
   export COUCHBASE_CHAT_HISTORY_COLLECTION_NAME="chat_messages"
   ```

   Adjust the values to match your cluster. You can keep the integration tests skipped until all variables are defined.

## 📢 Support Policy

We truly appreciate your interest in this project!  
This project is **community-maintained**, which means it's **not officially supported** by our support team.

If you need help, have found a bug, or want to contribute improvements, the best place to do that is right here — by [opening a GitHub issue](https://github.com/Couchbase-Ecosystem/langchain-couchbase/issues).  
Our support portal is unable to assist with requests related to this project, so we kindly ask that all inquiries stay within GitHub.

Your collaboration helps us all move forward together — thank you!
