"""Gradio Web UI — Seamless-RAG.

Design philosophy: Polanyi's Tacit Dimension.
"We can know more than we can tell."

The interface lets you FEEL the difference between JSON and TOON
rather than just reading numbers. Focal awareness on your question
and answer; subsidiary awareness on format efficiency; tacit
understanding of the vector search mechanics underneath.

Launch: seamless-rag web  OR  python -m seamless_rag.web
"""
from __future__ import annotations

import json
import logging

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


def _safe_error(e: Exception) -> str:
    logger.exception("Request failed: %s", type(e).__name__)
    return "Request failed. Check server logs for details."


# ── Handlers ─────────────────────────────────────────────────

def handle_ask(question: str, top_k: int):
    if not question.strip():
        return "", "", "", "", "", ""
    try:
        rag = _get_rag()
        r = rag.ask(question.strip(), top_k=int(top_k))

        answer = r.answer if r.answer else "(No LLM configured — retrieval only)"

        # Subsidiary: savings felt as a quiet ratio, not a shout
        savings = (
            f"JSON {r.json_tokens} tok → TOON {r.toon_tokens} tok\n"
            f"{r.savings_pct:.1f}% fewer tokens  ·  "
            f"${r.savings_cost_usd:.5f}/query saved"
        )

        sources = ""
        for i, src in enumerate(r.sources, 1):
            content = src.get("content", "")
            if not content:
                # Custom table: show all non-meta fields
                content = " · ".join(
                    str(v) for k, v in src.items()
                    if k not in ("id", "distance", "embedding") and v is not None
                )
            dist = src.get("distance", "?")
            sources += f"#{i}  dist={dist:.4f}\n{content[:150]}\n\n"

        return answer, r.context_toon, r.context_json, savings, sources, f"{r.savings_pct:.1f}%"
    except Exception as e:
        return _safe_error(e), "", "", "", "", ""


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
            f"Rows: {int(rows)},  Columns: {int(cols)}\n\n"
            f"JSON   {r.json_tokens:>5} tokens   {r.json_bytes:>5} bytes\n"
            f"TOON   {r.toon_tokens:>5} tokens   {r.toon_bytes:>5} bytes\n\n"
            f"Savings  {r.savings_pct:.1f}%  ·  ${r.savings_cost_usd:.5f}/query\n\n"
            f"At 1K queries/day   ${r.savings_cost_usd * 1000 * 30:>8.2f}/month\n"
            f"At 10K queries/day  ${r.savings_cost_usd * 10000 * 30:>8.2f}/month"
        )
        return preview, stats, f"{r.savings_pct:.1f}%"
    except Exception as e:
        return _safe_error(e), "", ""


def handle_json_to_toon(json_input: str):
    if not json_input.strip():
        return "Paste a JSON array above.", ""
    try:
        from seamless_rag.toon.encoder import encode_tabular
        data = json.loads(json_input)
        if not isinstance(data, list):
            return "Input must be a JSON array of objects.", ""
        toon = encode_tabular(data)
        bench = _get_benchmark()
        r = bench.compare(data)
        stats = f"JSON {r.json_tokens} tok  →  TOON {r.toon_tokens} tok  ·  {r.savings_pct:.1f}% saved"
        return toon, stats
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}", ""
    except Exception as e:
        return _safe_error(e), ""


def handle_export(sql: str):
    if not sql.strip():
        return "Enter a SELECT query."
    try:
        rag = _get_rag()
        return rag.export(sql.strip())
    except Exception as e:
        return _safe_error(e)


def handle_init_db():
    try:
        _get_rag().init()
        return "Schema ready — documents + chunks tables created."
    except Exception as e:
        return _safe_error(e)


def handle_ingest(title: str, text_content: str):
    if not title.strip():
        return "Provide a document title."
    if not text_content.strip():
        return "Enter text content."
    try:
        rag = _get_rag()
        chunks = [p.strip() for p in text_content.split("\n\n") if p.strip()]
        if not chunks:
            chunks = [text_content.strip()]
        doc_id = rag.ingest(title.strip(), chunks)
        return f"'{title}' → document #{doc_id}, {len(chunks)} chunks."
    except Exception as e:
        return _safe_error(e)


def handle_embed(table: str, column: str, batch_size: int):
    try:
        rag = _get_rag()
        text_col: str | list[str] = column or "content"
        if isinstance(text_col, str) and "," in text_col:
            text_col = [c.strip() for c in text_col.split(",") if c.strip()]
        result = rag.embed_table(table or "chunks", text_column=text_col, batch_size=batch_size)
        e, f, t = result["embedded"], result["failed"], result["total"]
        return f"Embedded {e}  ·  Failed {f}  ·  Total {t}"
    except Exception as e:
        return _safe_error(e)


def handle_status():
    from seamless_rag.config import Settings
    try:
        s = Settings()

        # Test DB connection
        db_status = "DISCONNECTED"
        try:
            rag = _get_rag()
            with rag._store._get_conn() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT 1")
                finally:
                    cursor.close()
            db_status = "CONNECTED"
        except Exception:
            pass

        return (
            f"MariaDB: {db_status}\n\n"
            f"Connection\n"
            f"  {s.mariadb_host}:{s.mariadb_port} / {s.mariadb_database}\n\n"
            f"Embedding\n"
            f"  {s.embedding_provider} · {s.embedding_model} · {s.embedding_dimensions}d\n"
            f"  API key: {'configured' if s.embedding_api_key else '—'}\n\n"
            f"LLM\n"
            f"  {s.llm_provider} · {s.llm_model}\n"
            f"  API key: {'configured' if s.llm_api_key else '—'}"
        )
    except Exception:
        logger.exception("Status check failed")
        return "Error loading settings."


# ── Theme: MariaDB palette + Polanyi principles ─────────────
#
# MariaDB brand: deep teal #003545, seal brown #C0A27A
# Polanyi: warmth (personal knowledge), depth (tacit dimension),
#          quiet confidence (subsidiary awareness)

THEME = gr.themes.Base(
    primary_hue=gr.themes.Color(
        c50="#f0f7fa", c100="#d6eaf0", c200="#aed5e2", c300="#7dbdd1",
        c400="#4da3bf", c500="#1a7a94", c600="#0d6070", c700="#094d5a",
        c800="#003545", c900="#002a38", c950="#001d27",
    ),
    secondary_hue=gr.themes.Color(
        c50="#faf6f0", c100="#f0e8d8", c200="#e2d1b3", c300="#d4ba8e",
        c400="#c0a27a", c500="#a88a62", c600="#8d7050", c700="#725a3e",
        c800="#5a462f", c900="#433322", c950="#2e2318",
    ),
    neutral_hue=gr.themes.Color(
        c50="#f8f7f5", c100="#f0eeea", c200="#e2dfda", c300="#ccc7bf",
        c400="#b0a99e", c500="#8a8279", c600="#6b6358", c700="#524b42",
        c800="#3a342d", c900="#252119", c950="#171410",
    ),
    font=["IBM Plex Sans", "system-ui", "sans-serif"],
    font_mono=["IBM Plex Mono", "Menlo", "monospace"],
)

# Polanyi CSS: the interface should feel like a well-worn research notebook.
# Focal elements are warm and present; subsidiary elements recede but remain.
CSS = """
/* ── Layout: breathing room for indwelling ── */
.gradio-container { max-width: 960px !important; }
footer { display: none !important; }

/* ── Header: quiet authority ── */
.polanyi-header {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    border-bottom: 2px solid #c0a27a;
    margin-bottom: 0.5rem;
}
.polanyi-header h1 {
    font-size: 1.6rem;
    font-weight: 700;
    color: #003545;
    letter-spacing: 0.02em;
    margin: 0;
}
.polanyi-header .subtitle {
    color: #8a8279;
    font-size: 0.82rem;
    margin-top: 0.25rem;
    font-style: italic;
}

/* ── Focal: the answer draws the eye ── */
.focal-answer textarea {
    font-size: 1.05rem !important;
    line-height: 1.6 !important;
    color: #252119 !important;
    background: #faf6f0 !important;
    border-left: 3px solid #003545 !important;
    padding-left: 1rem !important;
}

/* ── Subsidiary: savings bar — felt, not stared at ── */
.savings-quiet textarea {
    font-size: 0.85rem !important;
    color: #6b6358 !important;
    background: transparent !important;
    border: none !important;
}
.savings-pill textarea {
    text-align: center !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #003545 !important;
    background: linear-gradient(135deg, #d6eaf0 0%, #f0e8d8 100%) !important;
    border: 1px solid #aed5e2 !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
}

/* ── Tacit: code blocks feel like notebook margins ── */
.gradio-code textarea, .gradio-code pre {
    font-size: 0.82rem !important;
    background: #f8f7f5 !important;
}

/* ── Tabs: understated navigation ── */
.tab-nav button {
    font-size: 0.85rem !important;
    color: #6b6358 !important;
}
.tab-nav button.selected {
    color: #003545 !important;
    border-bottom-color: #c0a27a !important;
}

/* ── Buttons: warm action ── */
button.primary {
    background: #003545 !important;
    border: none !important;
    color: #f0e8d8 !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
}
button.primary:hover {
    background: #094d5a !important;
}
button.secondary {
    background: #c0a27a !important;
    border: none !important;
    color: #252119 !important;
}

/* ── Polanyi epigraph ── */
.polanyi-quote {
    text-align: center;
    padding: 0.6rem 0;
    font-size: 0.75rem;
    color: #b0a99e;
    font-style: italic;
    border-top: 1px solid #e2dfda;
    margin-top: 1rem;
}
"""


def create_app() -> gr.Blocks:
    with gr.Blocks(theme=THEME, css=CSS, title="Seamless-RAG") as app:

        # ── Header: quiet authority, not shouting ──
        gr.HTML(
            '<div class="polanyi-header">'
            "<h1>Seamless-RAG</h1>"
            '<div class="subtitle">'
            "Vector Search &amp; TOON Format for MariaDB"
            "</div></div>"
        )

        with gr.Tabs():

            # ═══════ Ask — the focal experience ═══════
            with gr.Tab("Ask", id="rag"):
                gr.Markdown(
                    "*Ask a question. Context is retrieved from MariaDB, "
                    "compressed into TOON format, and interpreted by the LLM.*"
                )
                with gr.Row():
                    with gr.Column(scale=4):
                        ask_input = gr.Textbox(
                            label="Question",
                            placeholder="What are the effects of climate change on ecosystems?",
                            lines=2,
                        )
                    with gr.Column(scale=1):
                        ask_topk = gr.Slider(1, 20, value=5, step=1, label="Depth")
                ask_btn = gr.Button("Ask", variant="primary", size="lg")

                # Focal: the answer
                ask_answer = gr.Textbox(
                    label="Answer",
                    lines=4, interactive=False,
                    elem_classes=["focal-answer"],
                )

                # Subsidiary: savings — present but not dominant
                with gr.Row():
                    ask_savings_pill = gr.Textbox(
                        label="Token Compression",
                        interactive=False, elem_classes=["savings-pill"],
                    )
                    ask_savings = gr.Textbox(
                        label="", lines=3, interactive=False,
                        elem_classes=["savings-quiet"],
                    )

                # Tacit: the raw formats, for those who want to dwell deeper
                with gr.Accordion("Context: TOON vs JSON", open=False), gr.Row():
                    ask_toon = gr.Code(label="TOON", language=None, interactive=False)
                    ask_json = gr.Code(label="JSON", language="json", interactive=False)

                with gr.Accordion("Sources", open=False):
                    ask_sources = gr.Textbox(label="Retrieved", lines=6, interactive=False)

                ask_btn.click(
                    fn=handle_ask,
                    inputs=[ask_input, ask_topk],
                    outputs=[ask_answer, ask_toon, ask_json, ask_savings, ask_sources, ask_savings_pill],
                )

            # ═══════ Benchmark — the experiment ═══════
            with gr.Tab("Benchmark", id="bench"):
                gr.Markdown("*Adjust rows and columns. Feel how the savings change.*")
                with gr.Row():
                    bench_rows = gr.Slider(5, 500, value=50, step=5, label="Rows")
                    bench_cols = gr.Slider(2, 16, value=6, step=1, label="Columns")
                bench_btn = gr.Button("Run", variant="primary")

                bench_pill = gr.Textbox(
                    label="Token Compression",
                    interactive=False, elem_classes=["savings-pill"],
                )
                with gr.Row():
                    bench_preview = gr.Code(label="TOON Output", language=None, interactive=False)
                    bench_stats = gr.Textbox(label="Statistics", lines=10, interactive=False)

                bench_btn.click(
                    fn=handle_benchmark,
                    inputs=[bench_rows, bench_cols],
                    outputs=[bench_preview, bench_stats, bench_pill],
                )

            # ═══════ Convert — the direct experience ═══════
            with gr.Tab("JSON → TOON", id="convert"):
                gr.Markdown("*Paste JSON. See TOON. Feel the difference.*")
                json_input = gr.Code(
                    label="JSON",
                    language="json",
                    value=(
                        '[\n'
                        '  {"id": 1, "name": "Ada Lovelace", "field": "Computing", "year": 1843},\n'
                        '  {"id": 2, "name": "Michael Polanyi", "field": "Philosophy", "year": 1966},\n'
                        '  {"id": 3, "name": "Marie Curie", "field": "Physics", "year": 1903}\n'
                        ']'
                    ),
                    lines=7,
                )
                convert_btn = gr.Button("Convert", variant="primary")
                toon_output = gr.Code(label="TOON", language=None, interactive=False)
                convert_stats = gr.Textbox(
                    label="", interactive=False,
                    elem_classes=["savings-quiet"],
                )
                convert_btn.click(
                    fn=handle_json_to_toon,
                    inputs=[json_input],
                    outputs=[toon_output, convert_stats],
                )

            # ═══════ Export — SQL to TOON bridge ═══════
            with gr.Tab("SQL Export", id="export"):
                gr.Markdown("*Run any SELECT. Results come back as TOON.*")
                sql_input = gr.Code(
                    label="SQL (SELECT only)",
                    language="sql",
                    value="SELECT id, content, embedding IS NOT NULL AS has_embedding FROM chunks LIMIT 10",
                    lines=3,
                )
                export_btn = gr.Button("Export", variant="primary")
                export_output = gr.Code(label="TOON Output", language=None, interactive=False)
                export_btn.click(fn=handle_export, inputs=[sql_input], outputs=[export_output])

            # ═══════ Data — quiet infrastructure ═══════
            with gr.Tab("Data", id="data"):
                gr.Markdown("*Initialize, ingest, embed. The substrate for search.*")

                with gr.Accordion("Schema", open=True):
                    init_btn = gr.Button("Initialize", variant="secondary")
                    init_out = gr.Textbox(label="", interactive=False, elem_classes=["savings-quiet"])
                    init_btn.click(fn=handle_init_db, outputs=[init_out])

                with gr.Accordion("Ingest", open=True):
                    ingest_title = gr.Textbox(label="Title", placeholder="Document name")
                    ingest_text = gr.Textbox(
                        label="Text (blank lines separate chunks)",
                        placeholder="First paragraph...\n\nSecond paragraph...",
                        lines=5,
                    )
                    ingest_btn = gr.Button("Ingest", variant="primary")
                    ingest_out = gr.Textbox(label="", interactive=False, elem_classes=["savings-quiet"])
                    ingest_btn.click(fn=handle_ingest, inputs=[ingest_title, ingest_text], outputs=[ingest_out])

                with gr.Accordion("Embed", open=False):
                    with gr.Row():
                        embed_table = gr.Textbox(label="Table", value="chunks")
                        embed_col = gr.Textbox(label="Column(s)", value="content")
                        embed_batch = gr.Slider(8, 256, value=64, step=8, label="Batch")
                    embed_btn = gr.Button("Embed", variant="primary")
                    embed_out = gr.Textbox(label="", interactive=False, elem_classes=["savings-quiet"])
                    embed_btn.click(fn=handle_embed, inputs=[embed_table, embed_col, embed_batch], outputs=[embed_out])

            # ═══════ Status — the tacit substrate ═══════
            with gr.Tab("Status", id="status"):
                gr.Markdown("*What's running underneath.*")
                status_btn = gr.Button("Refresh", variant="secondary")
                status_out = gr.Textbox(label="System", lines=14, interactive=False)
                status_btn.click(fn=handle_status, outputs=[status_out])

        # ── Polanyi epigraph ──
        gr.HTML(
            '<div class="polanyi-quote">'
            '"We can know more than we can tell." — Michael Polanyi, '
            "<em>The Tacit Dimension</em> (1966)"
            "</div>"
        )

    return app


# ── Entry point ──────────────────────────────────────────────

def _get_auth() -> tuple[str, str] | None:
    import os
    user = os.environ.get("SEAMLESS_WEB_USER", "")
    pwd = os.environ.get("SEAMLESS_WEB_PASSWORD", "")
    if user and pwd:
        return (user, pwd)
    return None


def main():
    app = create_app()
    app.launch(server_name="127.0.0.1", server_port=7860, share=False, auth=_get_auth())


if __name__ == "__main__":
    main()
