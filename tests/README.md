# Testing the Proxy Provider

This directory contains tests for the Proxy Provider package.

## Running Tests

To run the tests, you need to have pytest installed. If you're using Poetry, you can install it with:

```bash
poetry install
```

Then, you can run the tests with:

```bash
poetry run pytest
```

Or, if you're not using Poetry:

```bash
pytest
```

## Adding New Tests

When adding new tests, follow these guidelines:

1. Create a new test file with the prefix `test_` (e.g., `test_my_module.py`)
2. Create test classes with the prefix `Test` (e.g., `TestMyClass`)
3. Create test methods with the prefix `test_` (e.g., `test_my_function`)
4. Use fixtures for setup and teardown
5. Write clear docstrings for test classes and methods
6. Use descriptive assertion messages

## Test Data

The tests use temporary files and mock data to avoid modifying the actual data files. This ensures that the tests are isolated and repeatable.