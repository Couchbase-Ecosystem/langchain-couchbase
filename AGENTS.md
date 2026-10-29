# AGENTS.md

Instructions for automated agents (and humans) maintaining `langchain-couchbase`.
CONTRIBUTING.md has the full contributor guide; this file covers the rules and
gotchas for dependency, CI, release, and integration-validation work.

## Toolchain

- Package manager is **Poetry** with a committed `poetry.lock`. Do not switch to
  uv, pip-tools, or another tool.
- `poetry.lock` is written by Poetry 2.x (`lock-version = "2.1"`). The CI
  workflows pin the same Poetry version (`POETRY_VERSION` in
  `.github/workflows/*.yml`); keep them in step when you upgrade Poetry locally.
- Supported Python: `>=3.11,<4.0`. CI runs lint/unit/compile jobs on 3.11, 3.12, 3.13, and 3.14.

## Dependency policy

- The `couchbase` Python SDK range (`>=4.4.0,<5.0.0`) is **intentionally broad**
  so users can stay on any currently supported 4.x SDK. Do not narrow it during
  routine dependency updates. Change it only with an explicit compatibility
  rationale and integration-test evidence at the new lower bound.
- Routine refresh: `poetry update --with dev,test,typing,lint,codespell` (stays
  inside the declared ranges), then `poetry show --outdated --top-level` to find
  caret-blocked bumps. Bump dev/test tooling ranges only when lint and tests stay
  green.
- `langchain-core` / `langchain-classic` minimums are user-facing; raise them
  only when the code needs a newer API.

## Validation

```bash
poetry install --with dev,test_integration,typing,test,lint
make lint                 # ruff check + ruff format --diff + mypy (package and tests)
make test                 # unit tests, network disabled
poetry run pytest -m compile tests/integration_tests   # import/compile check
make integration_tests    # needs a live Couchbase target, see below
```

The unit suite is small; the integration suite (44 tests) is the real
regression gate for dependency changes, so run it whenever dependencies change.

### Integration tests against a local Couchbase

1. Start Couchbase Server **8.0+** (Query vector indexes need 8.0) with the Data,
   Query, Index, and Search services. To keep Server 7.6 coverage, also run the
   Search vector store, cache, and chat-history tests against 7.6.x;
   `test_query_vector_store.py` needs 8.0.
2. Create bucket `langchain`, scope `langchain`, and collections `vector_docs`,
   `cache_docs`, `semantic_cache_docs`, `chat_messages`.
3. Create the two Search indexes from `tests/fixtures/*.json`: replace the
   `<<BUCKET_NAME>>`/`<<SCOPE_NAME>>`/`<<COLLECTION_NAME>>`/`<<INDEX_NAME>>`
   placeholders, drop `uuid`/`sourceUUID`, and `PUT` them to
   `/api/bucket/langchain/scope/langchain/index/<name>` on port 8094.
   Use `langchain_vector_index` (on `vector_docs`) and `langchain_cache_index`
   (on `semantic_cache_docs`).
4. Export the `COUCHBASE_*` variables listed in CONTRIBUTING.md and run
   `make integration_tests`.

If host port 11210 is taken, run Couchbase without published ports and run the
tests in a container that shares its network
(`docker run --network container:<couchbase-container> ...`) so
`couchbase://localhost` works.

The tests use fixed `sleep`s for index consistency, so on a cold cluster the
first run can flake (seen on `test_memory_with_message_store`). Re-run before
treating a single failure as a regression.

## CI

- `CI` (`check_diffs.yml`): lint, unit tests, and integration-test compile on
  every PR and push to `main`.
- `Integration tests` (`_integration_test.yml`): runs on PRs and nightly against
  the team's Capella cluster, using repository variables and the
  `COUCHBASE_PASSWORD` secret. GitHub disables the nightly schedule after 60 days
  without commits; re-enable it in the Actions tab when that happens.
- `Build and Deploy Sphinx Docs`: builds on PRs, and deploys to GitHub Pages on
  push to `main`.

## Releases

Releases are **manual workflow dispatches**: `release` (`_release.yml`) is run
from `main` by a maintainer. It builds the package, publishes to TestPyPI, runs
pre-release checks (including integration tests), publishes to PyPI through
trusted publishing, then creates the `langchain-couchbase==<version>` tag and
GitHub release. The version comes from `pyproject.toml` (`poetry version
patch|minor|major`).

Agents must **not** dispatch the release workflow, create tags or GitHub
releases, publish to PyPI, or deploy docs without explicit maintainer approval.
Merging to `main` publishes nothing except the docs site.
