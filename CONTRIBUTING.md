# Contributing to LangChain Couchbase

Thank you for your interest in contributing to LangChain Couchbase! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Setting up your development environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/langchain-couchbase.git
   cd langchain-couchbase
   ```
3. Install the package in development mode:
   ```bash
   pip install -e .
   ```
4. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

### Setting up Couchbase

To run tests and examples, you need a running Couchbase instance. You can:

1. Install Couchbase Server locally
2. Use Docker:
   ```bash
   docker run -d --name couchbase -p 8091-8096:8091-8096 -p 11210-11211:11210-11211 couchbase:latest
   ```

Set up environment variables for testing:
```bash
export COUCHBASE_CONNECTION_STRING=couchbase://localhost
export COUCHBASE_USERNAME=Administrator
export COUCHBASE_PASSWORD=password
```

## Development Workflow

1. Create a branch for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes:
   - Write your code
   - Add or update tests as necessary
   - Update documentation if applicable

3. Run tests locally:
   ```bash
   pytest
   ```

4. Follow code style guidelines:
   - Use Black for code formatting:
     ```bash
     black langchain_couchbase tests
     ```
   - Run linting:
     ```bash
     flake8 langchain_couchbase tests
     ```

5. Commit your changes:
   - Use clear, descriptive commit messages
   - Include the issue number in your commit message if applicable

6. Push your branch to GitHub:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Create a Pull Request (PR):
   - Fill out the PR template
   - Link any relevant issues
   - Request review

## Pull Request Process

1. Ensure your PR includes tests for any new functionality
2. Update documentation, including docstrings and examples
3. Make sure all tests are passing
4. Your PR will be reviewed by project maintainers, who may request changes
5. After approval, a maintainer will merge your PR

## Testing

- All new features and bug fixes should include tests
- Run the entire test suite before submitting your PR:
  ```bash
  pytest
  ```
- For integration tests that require Couchbase:
  ```bash
  pytest tests/integration_tests
  ```

## Documentation

When adding or updating features, please update the documentation:

1. Update docstrings for public classes and methods
2. Update relevant .rst files in the docs/ directory
3. Add examples for new features

Generate documentation locally:
```bash
cd docs
make html
```

## Release Process

Releases are handled by the project maintainers. The general process is:

1. Update version in pyproject.toml
2. Update CHANGELOG.md
3. Create a release tag
4. GitHub Actions will build and publish to PyPI

## Contact

If you have questions or need help, please:
- Open an issue on GitHub
- Join the LangChain Discord server
- Reach out to the maintainers

Thank you for contributing to LangChain Couchbase! 