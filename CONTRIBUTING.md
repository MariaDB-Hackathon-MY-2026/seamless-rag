# Contributing to Seamless-RAG

Thank you for your interest in contributing to Seamless-RAG.

## Development Setup

```bash
git clone https://github.com/MariaDB-Hackathon-MY-2026/seamless-rag.git
cd seamless-rag
conda create -n seamless-rag python=3.12 -y
conda activate seamless-rag
pip install -e ".[dev,mariadb,embeddings,gemini,openai]"

# Start MariaDB
docker compose up -d
```

### Troubleshooting: editable install + Python 3.14 + sandboxed shells

If `pip install -e .` succeeds but `import seamless_rag` then fails with
`ModuleNotFoundError`, you may have hit this combination:

- **Python 3.14** ships a stricter `site.py` that ignores any `.pth` file
  carrying the macOS `UF_HIDDEN` filesystem flag (run with `python -v`
  and you'll see `Skipping hidden .pth file`).
- **Sandboxed shells** — the Bash tool exposed by some AI coding agents,
  certain CI runners, some macOS app sandboxes — set `UF_HIDDEN` on
  every file they create under `site-packages/`, including the editable-
  install `.pth` that Hatchling drops there.
- The result is an editable install that's invisible to the importer.

Two fixes, pick whichever fits your workflow:

```bash
# A. clear the hidden flag so site.py picks the .pth back up (one-shot)
chflags nohidden .venv/lib/python3.14/site-packages/*.pth

# B. bypass site.py entirely and put the source on PYTHONPATH (per-shell)
export PYTHONPATH="$PWD/src:${PYTHONPATH}"
```

Pinning Python to 3.12 / 3.13 sidesteps it — the `UF_HIDDEN` skip
behaviour is only enforced from 3.14 onward.

## Running Tests

```bash
make test-all         # lint + unit + spec (no Docker needed)
make test-full        # all suites including integration
make score            # quality dashboard
```

## Adding a Custom Provider

### Embedding Provider

Implement the `EmbeddingProvider` protocol:

```python
class MyProvider:
    @property
    def dimensions(self) -> int:
        return 768

    def embed(self, text: str) -> list[float]:
        return my_api.embed(text)

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        return [self.embed(t) for t in texts]
```

Register in `src/seamless_rag/providers/factory.py`.

### LLM Provider

Implement the `LLMProvider` protocol:

```python
class MyLLM:
    def generate(self, prompt: str, context: str) -> str:
        return my_api.generate(prompt, context)
```

Register in `src/seamless_rag/llm/factory.py`.

## Code Style

- Enforced by `ruff` (line length 100)
- Type hints on all public functions
- `typing.Protocol` for interfaces
- Tests required for new features

## Pull Request Process

1. Fork and create a feature branch
2. Write tests for new functionality
3. Run `make test-all` and ensure it passes
4. Submit a PR with a clear description

## License

By contributing, you agree that your contributions will be licensed under the Apache-2.0 License.
