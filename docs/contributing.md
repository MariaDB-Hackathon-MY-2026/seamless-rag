# Contributing

Contributions to Seamless-RAG are welcome. This guide covers the development setup and workflow.

## Development Setup

```bash
git clone https://github.com/SunflowersLwtech/seamless-rag.git
cd seamless-rag

conda create -n seamless-rag python=3.12 -y
conda activate seamless-rag
pip install -e ".[dev,mariadb,embeddings]"
```

## Running Tests

```bash
# Quick check (stops on first failure)
make test-quick

# All unit tests
make test-unit

# TOON spec conformance (166 official fixtures)
make test-spec

# Hypothesis property-based tests
make test-props

# Everything except integration
make test-all

# Full suite including integration (requires Docker)
docker compose -f docker-compose.test.yml up -d
make test-full
```

## Code Style

The project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
make lint          # check
ruff format .      # auto-format
```

## Pull Request Guidelines

1. Create a feature branch from `main`
2. Write tests for new functionality
3. Run `make test-all` and ensure it passes
4. Keep commits focused -- one logical change per commit
5. Use conventional commit messages: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`

## Project Structure

```
src/seamless_rag/       # Main package
tests/
  unit/                 # Unit tests
  integration/          # Integration tests (need Docker)
  fixtures/toon_spec/   # Official TOON v3 test fixtures (read-only)
eval/                   # Evaluation harness (read-only)
docs/                   # Documentation (MkDocs Material)
```

## Adding a Provider

To add a new embedding or LLM provider:

1. Create a new module in `src/seamless_rag/providers/` or `src/seamless_rag/llm/`
2. Implement the `EmbeddingProvider` or `LLMProvider` protocol
3. Register it in the corresponding factory module
4. Add tests in `tests/unit/`
5. Document it in `docs/providers.md`
