# Seamless-RAG — Architecture Decisions

> Log of key design decisions. Updated as decisions are made during development.

## ADR-001: Facade Pattern for Public API (2026-04-11)

**Decision:** Add `SeamlessRAG` class in `core.py` as the single entry point.

**Context:** Judge Directive 1 requires a "pip-installable toolkit other developers can use."
A facade class provides a clean API: `rag = SeamlessRAG(...); rag.ask(...)`.

**Alternatives considered:** Flat module functions, factory pattern.

---

## ADR-002: VectorStore Protocol Abstraction (2026-04-11)

**Decision:** Abstract all MariaDB vector operations behind a `VectorStore` Protocol.

**Context:** Both RAG engine and Watch mode need vector operations. Without abstraction,
SQL would be duplicated. The Protocol also enables in-memory mocks for CI.

---

## ADR-003: Token Benchmark as RAG Observation Layer (2026-04-11)

**Decision:** Embed token comparison into RAG engine, not as a standalone module.

**Context:** Judge Directive 2 requires "live token comparison with every ask."
Making benchmark an observation layer (not a peer module) means every query
automatically produces comparison data.

---

## ADR-004: Polling over Binlog for Watch Mode (2026-04-11)

**Decision:** Use polling (MAX(id) high-water mark) instead of MariaDB binlog.

**Context:** Binlog requires SUPER privilege and adds deployment complexity.
Polling is simpler, works with any MariaDB setup, and is sufficient for demo.
Added checkpoint + retry for reliability (Judge Directive 3).
