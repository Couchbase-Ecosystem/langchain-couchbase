# Contributing to langchain-couchbase

Thank you for your interest in contributing to langchain-couchbase! This document provides guidelines and instructions for contributing to the project.

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report, please check the [existing issues](https://github.com/Couchbase-Ecosystem/langchain-couchbase/issues) to ensure it hasn't already been reported.

When creating a bug report, please include:

- **Clear title and description** of the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs **actual behavior**
- **Environment details**: Python version, Couchbase version, package version

### Contributing Code

We welcome contributions of all kinds! Here are some areas where contributions are especially valuable:

- Bug fixes
- New features
- Performance improvements
- Documentation improvements
- Test coverage improvements
- Code refactoring

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management
- Git

### Initial Setup

1. **Clone the repository:**

```bash
git clone https://github.com/Couchbase-Ecosystem/langchain-couchbase.git
cd langchain-couchbase
```

2. **Install dependencies:**

```bash
poetry install --with test,lint
```

This installs all development dependencies including pytest, linters, type checkers, and other tools defined in `pyproject.toml`.

3. **Activate the virtual environment:**

```bash
poetry shell
```

## Development Workflow

1. **Create a branch** for your changes:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

2. **Make your changes**

3. **Write or update tests** for your changes

4. **Run tests and quality checks** locally (see [Testing](#testing))

5. **Commit your changes** with clear, descriptive commit messages

6. **Push to your fork:**

```bash
git push origin feature/your-feature-name
```

7. **Create a Pull Request** on GitHub

### Versioning

We follow [Semantic Versioning](https://semver.org/) rules. When updating the version, use Poetry's built-in versioning command:

```bash
# Bump patch version (0.0.x) - for bug fixes
poetry version patch

# Bump minor version (0.x.0) - for new features (backwards compatible)
poetry version minor

# Bump major version (x.0.0) - for breaking changes
poetry version major

# Or set a specific version
poetry version 1.2.3
```

**Version guidelines:**
- **Patch** (0.0.x): Bug fixes and minor improvements that don't change the API
- **Minor** (0.x.0): New features that are backwards compatible
- **Major** (x.0.0): Breaking changes that require users to update their code

### Formatting

We use `ruff` for formatting and linting. Before committing, format your code:

```bash
make format
```

### Linting

Run linting checks:

```bash
make lint
```

This runs:
- `ruff check` for code quality
- `mypy` for type checking

## Testing

### Unit Tests

Run the fast unit-test suite (uses `pytest --disable-socket` to prevent accidental network calls):

```bash
make test
```

Run a specific test file:

```bash
make test TEST_FILE=tests/path/to/test_file.py
```

### Integration Tests

Integration tests require a running Couchbase cluster. See [Couchbase Setup for Tests](#couchbase-setup-for-tests) below.

Run integration tests:

```bash
make integration_tests
```

### Couchbase Setup for Tests

Integration tests exercise a real Couchbase cluster. To run them locally:

1. **Run Couchbase Server 8.0+** (or Capella) with the Data, Query and Search services enabled. Make sure you can connect with a user that has at least read/write access to the bucket and permissions to create/manage indexes. (Admin privileges are recommended for simplicity, but not strictly required if you manually create all collections and indexes beforehand.)

2. **Create the data containers:**
   - Bucket: choose any name (e.g. `langchain`)
   - Scope: choose any name (e.g. `langchain`)
   - Collections (within the scope):
     - one for vector store tests → set `COUCHBASE_COLLECTION_NAME`
     - one for basic cache tests → set `COUCHBASE_CACHE_COLLECTION_NAME`
     - one for semantic cache tests → set `COUCHBASE_SEMANTIC_CACHE_COLLECTION_NAME`
     - one for chat history tests → set `COUCHBASE_CHAT_HISTORY_COLLECTION_NAME`

3. **Create the required Search indexes:**
   - Copy `tests/fixtures/search_index_definition_for_vector_store_testing.json` and replace the `<<SCOPE_NAME>>`, `<<COLLECTION_NAME>>`, and `<<INDEX_NAME>>` placeholders with the values you created above. Apply the definition through the Couchbase UI (Search → Import JSON).
   - Repeat the process for `tests/fixtures/search_index_definition_for_cache_testing.json`, using a distinct `COUCHBASE_SEMANTIC_CACHE_INDEX_NAME`. (The semantic cache requires a Search index with vector fields.)

4. **Export the environment variables** before running tests:

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