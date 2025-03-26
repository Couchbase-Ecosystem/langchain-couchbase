# LangChain Couchbase API Reference

This repository contains the API reference documentation for the [langchain-couchbase](https://github.com/Couchbase-Ecosystem/langchain-couchbase/) package.

## Overview

The `langchain-couchbase` package provides integration between LangChain and Couchbase, offering the following components:

- **CouchbaseVectorStore**: Use Couchbase for vector search and retrieval
- **CouchbaseCache**: Use Couchbase as a cache for LLM prompts and responses
- **CouchbaseSemanticCache**: Semantic caching for LLM prompts using Couchbase
- **CouchbaseChatMessageHistory**: Store chat message history in Couchbase

## Documentation

The API reference documentation is available at: [Visit Docs Here](https://couchbase-examples.github.io/langchain-couchbase-api-reference/)

## Local Development

To build and preview the documentation locally:

1. Install MkDocs and the Material theme:
   ```bash
   pip install mkdocs-material
   ```

2. Build the documentation:
   ```bash
   mkdocs build
   ```

3. Serve the documentation locally:
   ```bash
   mkdocs serve
   ```

4. Open your browser to http://localhost:8000

## Deployment

The documentation is automatically deployed to GitHub Pages when changes are pushed to the main branch, using the GitHub Actions workflow defined in `.github/workflows/deploy-docs.yml`.