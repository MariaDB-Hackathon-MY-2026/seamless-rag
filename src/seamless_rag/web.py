"""Gradio Web UI — visual interface for Seamless-RAG.

Launch: seamless-rag web  OR  python -m seamless_rag.web
"""
from __future__ import annotations

import json
import logging
import traceback

import gradio as gr

logger = logging.getLogger(__name__)

# ── Backend helpers ──────────────────────────────────────────

_rag = None


def _get_rag():
    global _rag
    if _rag is None:
        from seamless_rag.core import SeamlessRAG
        _rag = SeamlessRAG()
    return _rag


def _get_benchmark():
    from seamless_rag.benchmark.compare import TokenBenchmark
    return TokenBenchmark()


# ── Handler: Init DB ─────────────────────────────────────────

def handle_init_db():
    try:
        rag = _get_rag()
        rag.init()
        return "Schema initialized successfully (documents + chunks tables created)."
    except Exception as e:
        return f"Error: {e}"


# ── Handler: Ingest Text ─────────────────────────────────────

def handle_ingest(title: str, text_content: str):
    if not title.strip():
        return "Please enter a document title."
    if not text_content.strip():
        return "Please enter text content."
    try:
        rag = _get_rag()
        chunks = [p.strip() for p in text_content.split("\n\n") if p.strip()]
        if not chunks:
            chunks = [text_content.strip()]
        doc_id = rag.ingest(title.strip(), chunks)
        return f"Ingested '{title}' as document #{doc_id} with {len(chunks)} chunks."
    except Exception as e:
        return f"Error: {e}"


# ── Handler: Embed Table ─────────────────────────────────────

def handle_embed(table: str, column: str, batch_size: int):
    try:
        rag = _get_rag()
        result = rag.embed_table(
            table or "chunks", text_column=column or "content",
            batch_size=batch_size,
        )
        e, f, t = result["embedded"], result["failed"], result["total"]
        return f"Embedded: {e}, Failed: {f}, Total: {t}"
    except Exception as e:
        return f"Error: {e}"


# ── Handler: RAG Ask ─────────────────────────────────────────

def handle_ask(question: str, top_k: int):
    if not question.strip():
        return "", "", "", "", "", ""
    try:
        rag = _get_rag()
        r = rag.ask(question.strip(), top_k=int(top_k))

        answer = r.answer if r.answer else "(No LLM configured — showing retrieval only)"

        savings_text = (
            f"JSON: {r.json_tokens} tokens (${r.json_cost_usd:.6f})\n"
            f"TOON: {r.toon_tokens} tokens (${r.toon_cost_usd:.6f})\n"
            f"Savings: {r.savings_pct:.1f}% (${r.savings_cost_usd:.6f}/query)\n"
            f"At 1K queries/day: ${r.savings_cost_usd * 1000 * 30:.2f}/month saved"
        )

        sources_text = ""
        for i, src in enumerate(r.sources, 1):
            content = src.get("content", str(src))
            dist = src.get("distance", "?")
            sources_text += f"#{i} (distance: {dist}): {content[:120]}...\n\n"

        return answer, r.context_toon, r.context_json, savings_text, sources_text, f"{r.savings_pct:.1f}%"
    except Exception as e:
        err = f"Error: {e}\n{traceback.format_exc()}"
        return err, "", "", "", "", ""


# ── Handler: Export SQL ──────────────────────────────────────

def handle_export(sql: str):
    if not sql.strip():
        return "Please enter a SELECT query."
    try:
        rag = _get_rag()
        toon = rag.export(sql.strip())
        return toon
    except Exception as e:
        return f"Error: {e}"


# ── Handler: Benchmark ───────────────────────────────────────

def handle_benchmark(rows: int, cols: int):
    try:
        from seamless_rag.toon.encoder import encode_tabular
        bench = _get_benchmark()
        data = [
            {"id": i, **{f"f{c}": f"val_{i}_{c}" for c in range(1, int(cols))}, "score": round(0.99 - i * 0.01, 2)}
            for i in range(1, int(rows) + 1)
        ]
        r = bench.compare(data)
        toon_out = encode_tabular(data)

        preview = "\n".join(toon_out.split("\n")[:6])
        if int(rows) > 5:
            preview += f"\n  ... ({int(rows) - 5} more rows)"

        stats = (
            f"Rows: {int(rows)}, Columns: {int(cols)}\n\n"
            f"JSON: {r.json_tokens} tokens, {r.json_bytes} bytes (${r.json_cost_usd:.6f})\n"
            f"TOON: {r.toon_tokens} tokens, {r.toon_bytes} bytes (${r.toon_cost_usd:.6f})\n\n"
            f"Token savings: {r.savings_pct:.1f}%\n"
            f"Cost savings: ${r.savings_cost_usd:.6f}/query\n\n"
            f"At 1K queries/day:  ${r.savings_cost_usd * 1000 * 30:.2f}/month\n"
            f"At 10K queries/day: ${r.savings_cost_usd * 10000 * 30:.2f}/month"
        )
        return preview, stats, f"{r.savings_pct:.1f}%"
    except Exception as e:
        return f"Error: {e}", "", ""


# ── Handler: JSON → TOON ─────────────────────────────────────

def handle_json_to_toon(json_input: str):
    if not json_input.strip():
        return "Paste JSON array of objects above.", ""
    try:
        from seamless_rag.toon.encoder import encode_tabular
        data = json.loads(json_input)
        if not isinstance(data, list):
            return "Input must be a JSON array of objects.", ""
        toon = encode_tabular(data)
        bench = _get_benchmark()
        r = bench.compare(data)
        stats = f"JSON: {r.json_tokens} tok → TOON: {r.toon_tokens} tok | Savings: {r.savings_pct:.1f}%"
        return toon, stats
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}", ""
    except Exception as e:
        return f"Error: {e}", ""


# ── Handler: Status ──────────────────────────────────────────

def handle_status():
    from seamless_rag.config import Settings
    try:
        s = Settings()
        lines = [
            "=== Connection ===",
            f"Host: {s.mariadb_host}:{s.mariadb_port}",
            f"Database: {s.mariadb_database}",
            f"User: {s.mariadb_user}",
            "",
            "=== Embedding ===",
            f"Provider: {s.embedding_provider}",
            f"Model: {s.embedding_model}",
            f"Dimensions: {s.embedding_dimensions}",
            f"API Key: {'***' + s.embedding_api_key[-4:] if s.embedding_api_key else '(none)'}",
            "",
            "=== LLM ===",
            f"Provider: {s.llm_provider}",
            f"Model: {s.llm_model}",
            f"API Key: {'***' + s.llm_api_key[-4:] if s.llm_api_key else '(none)'}",
            f"OpenAI Key: {'***' + s.openai_api_key[-4:] if s.openai_api_key else '(none)'}",
        ]

        # Test DB connection
        try:
            rag = _get_rag()
            rag._store._cursor().execute("SELECT 1")
            lines.insert(0, "MariaDB: CONNECTED\n")
        except Exception as e:
            lines.insert(0, f"MariaDB: DISCONNECTED ({e})\n")

        return "\n".join(lines)
    except Exception as e:
        return f"Error loading settings: {e}"


# ── Build UI ─────────────────────────────────────────────────

THEME = gr.themes.Base(
    primary_hue=gr.themes.Color(
        c50="#f0fdf4", c100="#dcfce7", c200="#bbf7d0", c300="#86efac",
        c400="#4ade80", c500="#22c55e", c600="#16a34a", c700="#15803d",
        c800="#166534", c900="#14532d", c950="#052e16",
    ),
    font=["IBM Plex Sans", "system-ui", "sans-serif"],
    font_mono=["IBM Plex Mono", "monospace"],
)

CSS = """
.main-title { text-align: center; margin-bottom: 0; }
.main-title h1 { font-size: 1.8rem; font-weight: 700; color: #166534; }
.main-title p { color: #6b7280; font-size: 0.9rem; }
.savings-badge { font-size: 2rem; font-weight: 800; color: #16a34a;
                 text-align: center; padding: 1rem; }
footer { display: none !important; }
"""


def create_app() -> gr.Blocks:
    with gr.Blocks(theme=THEME, css=CSS, title="Seamless-RAG") as app:

        # ── Header ──
        gr.HTML(
            '<div class="main-title">'
            "<h1>Seamless-RAG</h1>"
            "<p>TOON-Native Auto-Embedding &amp; RAG Toolkit for MariaDB</p>"
            "</div>"
        )

        with gr.Tabs():

            # ══════════ Tab 1: RAG Query ══════════
            with gr.Tab("RAG Query", id="rag"):
                gr.Markdown("Ask a question — retrieves context from MariaDB, formats as TOON, generates answer.")
                with gr.Row():
                    with gr.Column(scale=3):
                        ask_input = gr.Textbox(
                            label="Question",
                            placeholder="What are the effects of climate change on ecosystems?",
                            lines=2,
                        )
                    with gr.Column(scale=1):
                        ask_topk = gr.Slider(1, 20, value=5, step=1, label="Top-K results")
                ask_btn = gr.Button("Ask", variant="primary", size="lg")

                ask_answer = gr.Textbox(label="Answer", lines=4, interactive=False)

                with gr.Row():
                    ask_savings_badge = gr.Textbox(label="Token Savings", interactive=False, elem_classes=["savings-badge"])
                    ask_savings = gr.Textbox(label="Cost Comparison", lines=5, interactive=False)

                with gr.Accordion("Context: TOON vs JSON", open=False), gr.Row():
                    ask_toon = gr.Code(label="TOON Context", language=None, interactive=False)
                    ask_json = gr.Code(label="JSON Context", language="json", interactive=False)

                with gr.Accordion("Source Documents", open=False):
                    ask_sources = gr.Textbox(label="Retrieved Sources", lines=6, interactive=False)

                ask_btn.click(
                    fn=handle_ask,
                    inputs=[ask_input, ask_topk],
                    outputs=[ask_answer, ask_toon, ask_json, ask_savings, ask_sources, ask_savings_badge],
                )

            # ══════════ Tab 2: Benchmark ══════════
            with gr.Tab("Benchmark", id="bench"):
                gr.Markdown("Run token benchmark: compare JSON vs TOON on generated sample data.")
                with gr.Row():
                    bench_rows = gr.Slider(5, 500, value=50, step=5, label="Rows")
                    bench_cols = gr.Slider(2, 16, value=6, step=1, label="Columns")
                bench_btn = gr.Button("Run Benchmark", variant="primary")

                bench_savings_badge = gr.Textbox(label="Savings", interactive=False, elem_classes=["savings-badge"])

                with gr.Row():
                    bench_preview = gr.Code(label="TOON Output (preview)", language=None, interactive=False)
                    bench_stats = gr.Textbox(label="Statistics", lines=10, interactive=False)

                bench_btn.click(
                    fn=handle_benchmark,
                    inputs=[bench_rows, bench_cols],
                    outputs=[bench_preview, bench_stats, bench_savings_badge],
                )

            # ══════════ Tab 3: JSON → TOON ══════════
            with gr.Tab("JSON → TOON", id="convert"):
                gr.Markdown("Paste any JSON array of objects to convert to TOON tabular format.")
                json_input = gr.Code(
                    label="JSON Input",
                    language="json",
                    value='[\n  {"id": 1, "name": "Ada", "score": 95},\n  {"id": 2, "name": "Bob", "score": 87},\n  {"id": 3, "name": "Eve", "score": 91}\n]',
                    lines=8,
                )
                convert_btn = gr.Button("Convert to TOON", variant="primary")
                toon_output = gr.Code(label="TOON Output", language=None, interactive=False)
                convert_stats = gr.Textbox(label="Token Comparison", interactive=False)

                convert_btn.click(
                    fn=handle_json_to_toon,
                    inputs=[json_input],
                    outputs=[toon_output, convert_stats],
                )

            # ══════════ Tab 4: Data ══════════
            with gr.Tab("Data", id="data"):
                gr.Markdown("Manage data: initialize schema, ingest documents, embed tables.")

                with gr.Accordion("Initialize Database", open=True):
                    init_btn = gr.Button("Initialize Schema", variant="primary")
                    init_output = gr.Textbox(label="Result", interactive=False)
                    init_btn.click(fn=handle_init_db, outputs=[init_output])

                with gr.Accordion("Ingest Document", open=True):
                    with gr.Row():
                        ingest_title = gr.Textbox(label="Document Title", placeholder="My Research Paper")
                    ingest_text = gr.Textbox(
                        label="Text Content (separate chunks with blank lines)",
                        placeholder="First paragraph...\n\nSecond paragraph...",
                        lines=6,
                    )
                    ingest_btn = gr.Button("Ingest", variant="primary")
                    ingest_output = gr.Textbox(label="Result", interactive=False)
                    ingest_btn.click(
                        fn=handle_ingest,
                        inputs=[ingest_title, ingest_text],
                        outputs=[ingest_output],
                    )

                with gr.Accordion("Embed Table", open=False):
                    with gr.Row():
                        embed_table = gr.Textbox(label="Table", value="chunks")
                        embed_col = gr.Textbox(label="Text Column", value="content")
                        embed_batch = gr.Slider(8, 256, value=64, step=8, label="Batch Size")
                    embed_btn = gr.Button("Embed", variant="primary")
                    embed_output = gr.Textbox(label="Result", interactive=False)
                    embed_btn.click(
                        fn=handle_embed,
                        inputs=[embed_table, embed_col, embed_batch],
                        outputs=[embed_output],
                    )

            # ══════════ Tab 5: SQL Export ══════════
            with gr.Tab("SQL Export", id="export"):
                gr.Markdown("Run a SELECT query against MariaDB and export results as TOON.")
                sql_input = gr.Code(
                    label="SQL Query (SELECT only)",
                    language="sql",
                    value="SELECT id, content, embedding IS NOT NULL AS has_embedding FROM chunks LIMIT 10",
                    lines=3,
                )
                export_btn = gr.Button("Export as TOON", variant="primary")
                export_output = gr.Code(label="TOON Output", language=None, interactive=False)
                export_btn.click(fn=handle_export, inputs=[sql_input], outputs=[export_output])

            # ══════════ Tab 6: Status ══════════
            with gr.Tab("Status", id="status"):
                gr.Markdown("System status: MariaDB connection, provider configuration.")
                status_btn = gr.Button("Refresh Status", variant="secondary")
                status_output = gr.Textbox(label="System Status", lines=18, interactive=False)
                status_btn.click(fn=handle_status, outputs=[status_output])

    return app


# ── Entry point ──────────────────────────────────────────────

def main():
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)


if __name__ == "__main__":
    main()
