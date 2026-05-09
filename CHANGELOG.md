# Changelog

All notable changes to Seamless-RAG are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.5] - 2026-05-09

First tag-driven release through the new `release.yml` GitHub Actions
pipeline. No code changes versus 0.1.4 — this version exists to verify
the full publish path end-to-end (verify tag matches pyproject → build
→ twine check → PyPI upload via `PYPI_API_TOKEN` secret → GitHub
Release with notes auto-extracted from this changelog).

If you're already on 0.1.4 there is no functional reason to upgrade.

## [0.1.4] - 2026-05-09

### Fixed

- **Chunker now handles structured / non-prose input.** `seamless-rag ingest`
  previously used a sentence-only splitter, so any text without `.!?` (TSV,
  CSV, log, code, JSON-lines) was returned as a single giant chunk and
  `--chunk-size` was silently ignored. The chunker is now recursive:
  sentences → newlines → fixed character windows, the standard pattern used
  by LangChain and llama-index. Locked in by 6 regression tests in
  `tests/unit/test_cli.py::TestChunkText`.
- **`seamless-rag init` no longer requires the embedding provider package.**
  It used to load the configured embedder just to read its dimension; now
  reads `EMBEDDING_DIMENSIONS` from settings (default 384). Means
  `pip install seamless-rag[mariadb]` is enough for `init` and `schema` —
  no need to also install ~500 MB of PyTorch.
- **LLM provider failures are no longer swallowed.** When `LLM_PROVIDER=gemini`
  but the `google-genai` SDK is missing, `seamless-rag ask` used to print
  retrieval context and exit 0 with no answer. Now the underlying
  `ImportError` propagates with an actionable install hint
  (`pip install "seamless-rag[gemini]"`) and the CLI exits non-zero.

### Changed

- **Single source of truth for `__version__`.** Reads from
  `importlib.metadata` so it cannot desync from `pyproject.toml`. Bumping
  the package version now requires changing exactly one file.
- **All optional-extra import sites raise actionable `ImportError`.** When
  the relevant SDK is missing, `gemini`/`openai`/`sentence-transformers`
  imports now raise a self-contained message that names the right
  `pip install seamless-rag[<extra>]` plus alternative providers — same
  pattern that already shipped for the `mariadb` C-extension driver.

### Added

- **`.github/workflows/release.yml`.** Pushing a `v*.*.*` tag now drives
  the full release: verify tag matches `pyproject.toml`, build sdist +
  wheel, `twine check`, upload to PyPI (token-based today, with a
  documented OIDC migration path), and create the matching GitHub
  Release with notes pulled from this changelog. No more manual
  `python -m build && twine upload`.

## [0.1.3] - 2026-05-09

### Added
- Friendly `ImportError` for the `mariadb` Python driver so users without
  Connector/C see actionable install hints instead of a raw
  `ModuleNotFoundError`.

### Fixed
- `Settings(extra="ignore")` so non-Seamless-RAG entries in `.env`
  (e.g. `TWINE_PASSWORD`) don't break startup.
- Lazy import of `SeamlessRAG` from the package root so bare
  `import seamless_rag` works without the optional `[mariadb]` extra.

## [0.1.2] - 2026-05-09

First publishable PyPI release.

### Added
- Vertex AI Express Mode auto-detection: API keys with the `AQ.` prefix
  route through Vertex AI; `AIza…` keys keep using Google AI Studio. No
  separate flag.
- Full PyPI metadata (keywords, classifiers, project URLs) for
  discoverability under MariaDB ecosystem listings.
- README "One-Line Agent Setup" section + `Install.md` for AI coding
  agents (DeerFlow-style bootstrap doc).
- Public agent skills under `skills/public/` (`seamless-rag` and
  `text-to-sql`).

### Fixed
- `mariadb` driver moved back to optional `[mariadb]` extra (it's a
  C-extension that needs system headers; making it required broke
  `pip install seamless-rag` on machines without Connector/C).

## [0.1.0] - 2026-05-08

Initial development release. **Do not use** — `pip install seamless-rag`
fails because of the import-time `mariadb` C-extension dependency. Fixed
in 0.1.2 / 0.1.3.

[Unreleased]: https://github.com/MariaDB-Hackathon-MY-2026/seamless-rag/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/MariaDB-Hackathon-MY-2026/seamless-rag/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/MariaDB-Hackathon-MY-2026/seamless-rag/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/MariaDB-Hackathon-MY-2026/seamless-rag/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/MariaDB-Hackathon-MY-2026/seamless-rag/releases/tag/v0.1.2
[0.1.0]: https://github.com/MariaDB-Hackathon-MY-2026/seamless-rag/releases/tag/v0.1.0
