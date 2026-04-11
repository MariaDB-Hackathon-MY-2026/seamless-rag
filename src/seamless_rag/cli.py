"""Typer CLI — init, embed, watch, ask, export, benchmark, demo."""
from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="seamless-rag",
    help="TOON-Native Auto-Embedding & RAG Toolkit for MariaDB",
)
console = Console()

# ── Global state (set by callback) ──────────────────────────

_state: dict = {}


@app.callback()
def main(
    host: str = typer.Option("127.0.0.1", envvar="MARIADB_HOST", help="MariaDB host"),
    port: int = typer.Option(3306, envvar="MARIADB_PORT", help="MariaDB port"),
    user: str = typer.Option("root", envvar="MARIADB_USER", help="MariaDB user"),
    password: str = typer.Option("seamless", envvar="MARIADB_PASSWORD", help="MariaDB password"),
    database: str = typer.Option("seamless_rag", envvar="MARIADB_DATABASE"),
    log_level: str = typer.Option("WARNING", "--log-level", envvar="LOG_LEVEL", help="Log level"),
) -> None:
    """TOON-Native Auto-Embedding & RAG Toolkit for MariaDB."""
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.WARNING))
    _state["db"] = {
        "host": host, "port": port, "user": user, "password": password, "database": database,
    }


def _get_rag(**extra):
    from seamless_rag.core import SeamlessRAG

    return SeamlessRAG(**_state["db"], **extra)


# ── Commands ────────────────────────────────────────────────


@app.command()
def init() -> None:
    """Initialize database schema (documents + chunks tables)."""
    rag = _get_rag()
    rag.init()
    rprint("[green]Schema initialized.[/green]")
    rag.close()


def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into chunks at sentence boundaries with overlap."""
    import re as _re

    sentences = _re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        if current_len + len(sent) > size and current:
            chunks.append(" ".join(current))
            # Keep overlap: retain last N chars worth of sentences
            kept: list[str] = []
            kept_len = 0
            for s in reversed(current):
                if kept_len + len(s) > overlap:
                    break
                kept.insert(0, s)
                kept_len += len(s) + 1
            current = kept
            current_len = kept_len
        current.append(sent)
        current_len += len(sent) + 1

    if current:
        chunks.append(" ".join(current))
    return chunks if chunks else [text.strip()]


@app.command()
def ingest(
    path: Path = typer.Argument(..., help="Text file or directory to ingest"),
    chunk_size: int = typer.Option(500, "--chunk-size", help="Chars per chunk"),
    overlap: int = typer.Option(50, "--overlap", help="Overlap between chunks"),
) -> None:
    """Ingest text files with sentence-boundary chunking and overlap."""
    rag = _get_rag()
    rag.init()

    files = list(path.glob("*.txt")) if path.is_dir() else [path]
    total_chunks = 0

    for f in files:
        text = f.read_text(encoding="utf-8")
        # Split by paragraphs first, then chunk within paragraphs
        chunks: list[str] = []
        for para in text.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            chunks.extend(_chunk_text(para, chunk_size, overlap))
        if chunks:
            rag.ingest(f.name, chunks)
            total_chunks += len(chunks)
            rprint(f"  [cyan]{f.name}[/cyan]: {len(chunks)} chunks")

    rprint(f"[green]Ingested {len(files)} files, {total_chunks} chunks total.[/green]")
    rag.close()


@app.command()
def embed(
    table: str = typer.Option("chunks", "--table", "-t"),
    column: str = typer.Option("content", "--column", "-c"),
    batch_size: int = typer.Option(64, "--batch-size", "-b"),
) -> None:
    """Bulk-embed all rows in a table that lack embeddings."""
    rag = _get_rag()
    rprint(f"[blue]Embedding {table}.{column} (batch_size={batch_size})...[/blue]")
    result = rag.embed_table(table, text_column=column, batch_size=batch_size)
    rprint(
        f"[green]Done.[/green] "
        f"Embedded: {result['embedded']}, Failed: {result['failed']}, "
        f"Total: {result['total']}"
    )
    rag.close()


@app.command()
def watch(
    table: str = typer.Option("chunks", "--table", "-t"),
    column: str = typer.Option("content", "--column", "-c"),
    interval: float = typer.Option(2.0, "--interval", "-i"),
) -> None:
    """Watch a table for new inserts and auto-embed."""
    rag = _get_rag()
    rprint(f"[blue]Watching {table}.{column} every {interval}s (Ctrl+C to stop)[/blue]")
    try:
        rag.watch(table, text_column=column, interval=interval)
    except KeyboardInterrupt:
        rprint("\n[yellow]Watch stopped.[/yellow]")
    rag.close()


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask"),
    top_k: int = typer.Option(5, "--top-k", "-k"),
    context_window: int = typer.Option(0, "--context-window", "-w", help="Neighboring chunks"),
) -> None:
    """Ask a question using RAG with token benchmarking."""
    rag = _get_rag()
    result = rag.ask(question, top_k=top_k)

    if result.sources:
        if result.answer:
            rprint(f"\n[bold green]Answer:[/bold green] {result.answer}\n")

        rprint(f"[bold]Context (TOON — {result.toon_tokens} tokens):[/bold]")
        rprint(result.context_toon)

        _print_benchmark_table(result)
    else:
        rprint(
            "[yellow]No results found. "
            "Run 'seamless-rag init' and 'seamless-rag ingest' first.[/yellow]"
        )
    rag.close()


@app.command(name="export")
def export_cmd(
    query: str = typer.Argument(..., help="SQL SELECT query to export as TOON"),
) -> None:
    """Export SQL query results as TOON format."""
    rag = _get_rag()
    rprint(rag.export(query))
    rag.close()


@app.command()
def benchmark(
    rows: int = typer.Option(50, "--rows", "-n", help="Number of sample rows"),
    cols: int = typer.Option(6, "--cols", "-c", help="Number of columns"),
) -> None:
    """Run token benchmark: JSON vs TOON on sample data."""
    from seamless_rag.benchmark.compare import TokenBenchmark
    from seamless_rag.toon.encoder import encode_tabular

    bench = TokenBenchmark()
    data = [
        {
            "id": i,
            **{f"field_{c}": f"value_{i}_{c}" for c in range(1, cols)},
            "score": round(0.99 - i * 0.01, 2),
        }
        for i in range(1, rows + 1)
    ]

    result = bench.compare(data)
    toon_out = encode_tabular(data)

    rprint(f"\n[bold]TOON vs JSON Benchmark ({rows} rows, {cols} columns)[/bold]\n")
    rprint("[dim]TOON output (first 5 lines):[/dim]")
    for line in toon_out.split("\n")[:5]:
        rprint(f"  {line}")
    if rows > 4:
        rprint(f"  ... ({rows - 4} more rows)")
    rprint()

    table = Table(title="Token & Cost Comparison (GPT-4o @ $2.50/1M)")
    table.add_column("Format", style="cyan")
    table.add_column("Tokens", justify="right")
    table.add_column("Bytes", justify="right")
    table.add_column("Est. Cost", justify="right")
    jc = f"${result.json_cost_usd:.6f}"
    tc = f"${result.toon_cost_usd:.6f}"
    sc = f"${result.savings_cost_usd:.6f}/q"
    table.add_row("JSON", str(result.json_tokens), str(result.json_bytes), jc)
    table.add_row("TOON", str(result.toon_tokens), str(result.toon_bytes), tc)
    table.add_row("Savings", f"{result.savings_pct:.1f}%", "", sc, style="green")
    console.print(table)

    daily = result.savings_cost_usd * 1000
    m1 = f"${daily:.2f}/day → ${daily * 30:.2f}/month"
    m10 = f"${daily * 10:.2f}/day → ${daily * 300:.2f}/month"
    rprint(f"\n  [dim]At 1,000 queries/day: {m1}[/dim]")
    rprint(f"  [dim]At 10,000 queries/day: {m10}[/dim]\n")


@app.command()
def web(
    port: int = typer.Option(7860, "--port", "-p", help="Server port"),
    share: bool = typer.Option(False, "--share", help="Create public link"),
) -> None:
    """Launch Gradio web UI in browser."""
    from seamless_rag.web import create_app

    rprint(f"[blue]Launching web UI on http://localhost:{port}[/blue]")
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=port, share=share)


@app.command()
def demo(
) -> None:
    """Run end-to-end demo: init -> seed data -> ask question -> show benchmark."""
    rag = _get_rag()

    rprint("\n[bold magenta]Seamless-RAG End-to-End Demo[/bold magenta]\n")

    rprint("[bold]1. Initializing schema...[/bold]")
    rag.init()
    rprint("   [green]Done.[/green]\n")

    rprint("[bold]2. Ingesting sample documents...[/bold]")
    docs = [
        ("Climate Science", [
            "Climate change affects biodiversity through multiple mechanisms.",
            "Rising temperatures force species to migrate to new habitats.",
            "Ocean acidification reduces carbonate ion availability.",
            "Deforestation contributes to carbon emissions.",
        ]),
        ("Renewable Energy", [
            "Solar panel efficiency has increased by 25% over the past decade.",
            "Wind energy now accounts for a growing share of global electricity.",
            "Battery storage technology is key to making renewable energy reliable.",
            "Green hydrogen from electrolysis could decarbonize heavy industry.",
        ]),
        ("AI Research", [
            "Large language models demonstrate emergent capabilities at scale.",
            "Retrieval-augmented generation improves factual accuracy of AI.",
            "Vector databases enable efficient similarity search for embeddings.",
            "Token efficiency in context windows directly impacts inference costs.",
        ]),
    ]
    for title, chunks in docs:
        rag.ingest(title, chunks)
        rprint(f"   [cyan]{title}[/cyan]: {len(chunks)} chunks")
    rprint("   [green]Done.[/green]\n")

    questions = [
        "How does climate change affect biodiversity?",
        "What are the recent advances in renewable energy?",
        "How does retrieval-augmented generation work?",
    ]
    for q in questions:
        rprint(f"[bold]3. Asking:[/bold] {q}")
        result = rag.ask(q, top_k=3)

        if result.answer:
            rprint(f"\n   [bold green]Answer:[/bold green] {result.answer}")

        rprint(f"\n   [bold]TOON Context ({result.toon_tokens} tokens):[/bold]")
        for line in result.context_toon.split("\n"):
            rprint(f"   {line}")

        _print_benchmark_table(result)
        rprint()

    rag.close()
    rprint("[bold green]Demo complete![/bold green]\n")


def _print_benchmark_table(result) -> None:
    """Print the token & cost comparison table for a RAG result."""
    table = Table(title="\nToken & Cost Comparison (GPT-4o pricing)")
    table.add_column("Format", style="cyan")
    table.add_column("Tokens", justify="right")
    table.add_column("Est. Cost", justify="right")
    table.add_row("JSON", str(result.json_tokens), f"${result.json_cost_usd:.6f}")
    table.add_row("TOON", str(result.toon_tokens), f"${result.toon_cost_usd:.6f}")
    table.add_row(
        "Savings", f"{result.savings_pct:.1f}%",
        f"${result.savings_cost_usd:.6f}/query", style="green",
    )
    console.print(table)
    daily = result.savings_cost_usd * 1000
    rprint(
        f"  [dim]At 1,000 queries/day: "
        f"${daily:.2f}/day saved → ${daily * 30:.2f}/month[/dim]"
    )
