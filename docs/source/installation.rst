Installation and Setup
===================

This section provides comprehensive instructions for installing the ``langchain-couchbase`` package and setting up the necessary Couchbase environment.

Package Installation
-------------------

You can install ``langchain-couchbase`` using pip:

.. code-block:: bash

    pip install langchain-couchbase

For development or the latest features, you can install directly from the GitHub repository:

.. code-block:: bash

    pip install git+https://github.com/langchain-ai/langchain-couchbase.git

Dependencies
-----------

The ``langchain-couchbase`` package has the following core dependencies:

* ``langchain-core>=0.1.0``: Core LangChain components
* ``couchbase>=4.1.0``: Couchbase Python SDK

These dependencies will be automatically installed when installing the package through pip.

Optional Dependencies
-------------------

Depending on which embeddings and language models you want to use, you may need to install additional packages:

* For OpenAI embeddings and models:

  .. code-block:: bash

      pip install langchain-openai

* For HuggingFace embeddings and models:

  .. code-block:: bash

      pip install langchain-huggingface

* For other providers, install the appropriate packages. See the `LangChain documentation <https://python.langchain.com/docs/get_started/installation>`_ for details.

Couchbase Server Setup
---------------------

To use the LangChain Couchbase integrations, you'll need a running Couchbase server. Here are the main options:

Local Installation
~~~~~~~~~~~~~~~~

To install Couchbase Server locally:

1. Download the Couchbase Server Community or Enterprise Edition from the `Couchbase website <https://www.couchbase.com/downloads/>`_.
2. Follow the installation instructions for your operating system.
3. Access the Couchbase Web Console at ``http://localhost:8091`` to complete the setup.

Docker Deployment
~~~~~~~~~~~~~~~

You can quickly deploy Couchbase using Docker:

.. code-block:: bash

    docker run -d --name couchbase -p 8091-8096:8091-8096 -p 11210-11211:11210-11211 couchbase:latest

Then access the Couchbase Web Console at ``http://localhost:8091`` and follow the setup wizard.

Couchbase Cloud
~~~~~~~~~~~~~

For production environments, consider using `Couchbase Capella <https://cloud.couchbase.com/>`_, a fully managed Database-as-a-Service:

1. Create an account on Couchbase Capella
2. Deploy a new cluster
3. Configure access credentials and network security
4. Use the provided connection string in your application

Bucket, Scope, and Collection Creation
-------------------------------------

After setting up Couchbase Server, you'll need to create the database structures:

1. **Create a Bucket**: A bucket is a logical grouping of data items
   
   * From the Couchbase Web Console, navigate to "Buckets" and click "Add Bucket"
   * Name your bucket (e.g., "langchain")
   * Configure memory and other settings according to your needs
   * Click "Add Bucket" to create it

2. **Create Scopes and Collections**: Within each bucket, you can organize data into scopes and collections
   
   * Navigate to your bucket and click on "Scopes & Collections"
   * By default, a bucket has a "_default" scope with a "_default" collection
   * For larger applications, you might want to create separate collections for vector stores, caches, and chat histories

Vector Search Index Setup
-----------------------

For the ``CouchbaseVectorStore`` and ``CouchbaseSemanticCache`` components, you'll need to create vector search indices:

1. From the Couchbase Web Console, navigate to "Search" and click "Add Index"
2. Name your index (e.g., "vector_index")
3. Select the bucket, scope, and collection
4. Choose "Custom" mapping type
5. Enter a vector search mapping similar to:

.. code-block:: json

    {
      "type": "fulltext-index",
      "sourceType": "gocbcore",
      "planParams": {
        "indexPartitions": 6
      },
      "params": {
        "mapping": {
          "types": {
            "your_collection": {
              "enabled": true,
              "dynamic": true,
              "properties": {
                "embedding": {
                  "enabled": true,
                  "dynamic": false,
                  "fields": [
                    {
                      "name": "embedding",
                      "type": "vector",
                      "dims": 1536,
                      "similarity": "dot_product",
                      "index": true
                    }
                  ]
                }
              }
            }
          }
        }
      }
    }

Be sure to adjust the ``dims`` parameter to match your embedding model's dimensions (e.g., 1536 for OpenAI's text-embedding-ada-002).

Connection Configuration
----------------------

When connecting to Couchbase from your Python application, you'll need:

1. **Connection String**: The address of your Couchbase server(s)
2. **Credentials**: Username and password with appropriate permissions
3. **TLS Configuration**: For secure connections (especially with Couchbase Cloud)

Here's a basic connection setup:

.. code-block:: python

    from datetime import timedelta
    from couchbase.auth import PasswordAuthenticator
    from couchbase.cluster import Cluster
    from couchbase.options import ClusterOptions, ClusterTimeoutOptions

    # Connection parameters
    connection_string = "couchbase://localhost"  # Or your cluster address
    username = "Administrator"
    password = "password"

    # Authentication
    auth = PasswordAuthenticator(username, password)
    
    # Options with timeouts for better error handling
    timeout_opts = ClusterTimeoutOptions(
        kv_timeout=timedelta(seconds=10),
        query_timeout=timedelta(seconds=60)
    )
    options = ClusterOptions(auth, timeout_options=timeout_opts)
    
    # Connect to the cluster
    cluster = Cluster(connection_string, options)
    
    # Wait for the cluster to be ready
    cluster.wait_until_ready(timedelta(seconds=5))

For Couchbase Cloud deployments, you'll need to include TLS configuration and the proper connection string from your cluster information.

Environment Variable Management
-----------------------------

For security, it's recommended to store connection credentials in environment variables rather than hardcoding them:

.. code-block:: python

    import os
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get credentials from environment
    connection_string = os.getenv("COUCHBASE_CONNECTION_STRING")
    username = os.getenv("COUCHBASE_USERNAME")
    password = os.getenv("COUCHBASE_PASSWORD")

Create a ``.env`` file in your project root:

.. code-block:: text

    COUCHBASE_CONNECTION_STRING=couchbase://localhost
    COUCHBASE_USERNAME=Administrator
    COUCHBASE_PASSWORD=your_secure_password

Permission Requirements
---------------------

The Couchbase user account used by your application needs specific permissions:

* For basic operations: Query, Read, Write permissions on the relevant buckets
* For index creation: Data Reader, Index Manager, and Query Manager roles
* For production: Create a dedicated user with minimal required permissions

Troubleshooting
-------------

Common installation issues:

1. **Connection Problems**:
   
   * Verify Couchbase server is running
   * Check connection string format
   * Ensure network connectivity (especially with cloud deployments)
   * Verify credentials are correct

2. **Index Creation Failures**:
   
   * Ensure the user has index management permissions
   * Verify the bucket, scope, and collection exist
   * Check vector dimension size matches your embedding model

3. **Library Conflicts**:
   
   * If encountering dependency conflicts, consider using a virtual environment
   * Make sure Couchbase Python SDK version is compatible with your server version

Next Steps
---------

After completing the installation and setup, proceed to:

1. The :doc:`vectorstores` section to learn about storing and retrieving embeddings
2. The :doc:`cache` section for implementing LLM response caching
3. The :doc:`chat_message_histories` section for managing conversation history 