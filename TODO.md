# Seamless-RAG — TODO

> Updated: 2026-04-11
> Status: 520/522 tests passing (99.6%)
> Codex Grade: A (95.85/100)

---

## MariaDB 生态 — 已完成 ✓

All features required for a complete MariaDB vector toolkit are implemented.

### Core Engine ✓
- [x] TOON v3 encoder — 774 lines, 166/166 spec conformance
- [x] Token benchmark — tiktoken cl100k_base, GPT-4o cost calculation
- [x] RAG pipeline — search → TOON → LLM → benchmark observation layer
- [x] MMR diversity selection (Carbonell & Goldstein 1998, numpy)
- [x] Filter + vector hybrid search (`WHERE` clause + VEC_DISTANCE)
- [x] CTE context windowing (neighboring chunks)

### Embedding Providers ✓
- [x] SentenceTransformers — local, free, 384d (default)
- [x] Gemini — google-genai SDK, 768d, MRL dimension control
- [x] OpenAI — openai SDK, 3072d
- [x] Ollama — REST API, nomic-embed-text 768d
- [x] Factory with foreign model auto-correction

### LLM Providers ✓
- [x] Ollama — local REST, qwen3:8b (default)
- [x] Gemini — gemini-2.5-flash
- [x] OpenAI — gpt-4o
- [x] Factory with foreign model auto-correction

### Storage ✓
- [x] MariaDB VectorStore — VECTOR columns, HNSW index
- [x] Connection pool (mariadb.ConnectionPool, size=5)
- [x] Version check (>= 11.7.2)
- [x] SQL injection protection (regex + identifier validation)
- [x] Context manager support
- [x] `executemany` batch operations

### CLI (9 commands) ✓
- [x] init — create schema with VECTOR + HNSW
- [x] embed — bulk-embed existing rows (core workflow)
- [x] watch — auto-embed new inserts (Rich live display)
- [x] ask — RAG query with --where, --mmr, --context-window
- [x] export — SQL SELECT → TOON
- [x] benchmark — JSON vs TOON comparison
- [x] web — Gradio web UI (6 tabs)
- [x] demo — end-to-end with sample data
- [x] ingest — convenience file loader
- [x] Global options: --host/--port/--provider/--model/--log-level

### Protocols ✓
- [x] EmbeddingProvider (runtime_checkable)
- [x] LLMProvider (runtime_checkable)
- [x] VectorStore (runtime_checkable)

### Testing ✓
- [x] 520/522 tests (99.6%)
- [x] TOON spec: 166/166 (100%)
- [x] Unit: 329/330 (99.7%)
- [x] Integration: 17/17 (100%)
- [x] Property-based (Hypothesis): 11/12

### Docs & Deployment ✓
- [x] README.md — thin-layer positioning, honest token savings
- [x] MkDocs Material site — 7 pages, GitHub Pages deployed
- [x] CONTRIBUTING.md
- [x] JUDGES_TESTING_GUIDE.md
- [x] Docker Compose (MariaDB 11.8)
- [x] Dockerfile
- [x] Apache-2.0 LICENSE
- [x] Agent skill (seamless-rag)

---

## 未来方向 — 解耦 & 分发

> 以下是从 hackathon 项目进化为开源生态工具的路线图。
> 按优先级排序。

### P0 — 分发基础设施（开源项目的生命线）
- [ ] PyPI 发布 — `pip install seamless-rag` 能直接安装
- [ ] GitHub Actions CI — PR 自动跑 `make test-all`，绿色 badge
- [ ] Issue templates — bug report / feature request / question
- [ ] PR template — checklist (tests pass, lint clean, docs updated)

### P1 — TOON 解耦（最大增长杠杆）
- [ ] 提取 `toon-format` 为独立包 — 零依赖，纯 Python
  - `pip install toon-format`
  - 支持 `list[dict]` / pandas DataFrame / CSV 输入
  - 独立 README、独立 PyPI、独立仓库
  - 这是项目真正的差异化，不应被 MariaDB 绑定
- [ ] TOON decoder — 目前只有 encoder，缺 `decode(toon_str) → list[dict]`
- [ ] TOON CLI — `toon encode data.json` / `toon decode data.toon`

### P2 — 零基础设施试用（降低 onboard 门槛）
- [ ] SQLite 向量后端 — sqlite-vec 或内存后端
  - 让用户 `pip install seamless-rag && seamless-rag demo` 零 Docker 体验
- [ ] In-memory VectorStore — 用于测试和快速原型
- [ ] `seamless-rag quickstart` 命令 — 自动检测可用后端

### P3 — LLM 质量验证（补全 token 节省叙事）
- [ ] LLM 理解力对比测试 — 同一问题、同一数据：
  - JSON context vs TOON context vs Markdown table context
  - 用 GPT-4o + Gemini 各跑 50 题，对比答案质量
  - 发布结果到 README（有数据支撑才有说服力）
- [ ] Few-shot TOON prompt — 教 LLM 读 TOON 的最优 system prompt
- [ ] TOON 作为 tool output format — agent 工具描述里声明返回格式

### P4 — 生态集成
- [ ] LangChain Retriever 适配器 — `SeamlessRAGRetriever`
- [ ] LlamaIndex VectorStore 适配器
- [ ] MCP Server — 暴露为 Model Context Protocol 工具
- [ ] pandas 集成 — `df.to_toon()` / `toon.read_toon()`

### P5 — 高级检索
- [ ] Rerank — 集成 cross-encoder (e.g. ms-marco-MiniLM)
- [ ] Hybrid search — BM25 + vector 融合
- [ ] 异步支持 — `async embed()`, `async ask()`
- [ ] Streaming LLM 输出 — 逐 token 返回

### P6 — 品牌 & 社区
- [ ] 改名考虑 — "seamless-rag" 太通用，"toon-db"/"mariadb-rag" 更可搜
- [ ] Demo video (2-4 min) — 终端录屏 + 配音
- [ ] Blog post — "为什么结构化数据不该用 JSON 喂给 LLM"
- [ ] MariaDB 官方生态提交 — mariadb.org ecosystem page
- [ ] Conference talk proposal — MariaDB Server Fest / PyCon
