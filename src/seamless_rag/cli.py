"""Typer CLI — init, ingest, embed, watch, ask, export."""
from __future__ import annotations

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


def _get_rag(**kwargs):
    from seamless_rag.core import SeamlessRAG
    return SeamlessRAG(**kwargs)


def _db_kwargs(host, port, user, password, database):
    return {"host": host, "port": port, "user": user, "password": password, "database": database}


# ── Common options via callback ────────────────────────────

@app.command()
def init(
    host: str = typer.Option("127.0.0.1", envvar="MARIADB_HOST"),
    port: int = typer.Option(3306, envvar="MARIADB_PORT"),
    user: str = typer.Option("root", envvar="MARIADB_USER"),
    password: str = typer.Option("seamless", envvar="MARIADB_PASSWORD"),
    database: str = typer.Option("seamless_rag", envvar="MARIADB_DATABASE"),
):
    """Initialize database schema (documents + chunks tables)."""
    rag = _get_rag(**_db_kwargs(host, port, user, password, database))
    rag.init()
    rprint("[green]Schema initialized.[/green]")
    rag.close()


@app.command()
def ingest(
    path: Path = typer.Argument(..., help="Text file or directory to ingest"),
    host: str = typer.Option("127.0.0.1", envvar="MARIADB_HOST"),
    port: int = typer.Option(3306, envvar="MARIADB_PORT"),
    user: str = typer.Option("root", envvar="MARIADB_USER"),
    password: str = typer.Option("seamless", envvar="MARIADB_PASSWORD"),
    database: str = typer.Option("seamless_rag", envvar="MARIADB_DATABASE"),
    chunk_size: int = typer.Option(500, "--chunk-size", help="Characters per chunk"),
):
    """Ingest text files into the database with automatic embedding."""
    rag = _get_rag(**_db_kwargs(host, port, user, password, database))
    rag.init()

    files = list(path.glob("*.txt")) if path.is_dir() else [path]
    total_chunks = 0

    for f in files:
        text = f.read_text(encoding="utf-8")
        # Simple chunking by paragraph or fixed size
        chunks = []
        for para in text.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            if len(para) <= chunk_size:
                chunks.append(para)
            else:
                for i in range(0, len(para), chunk_size):
                    chunks.append(para[i:i + chunk_size])

        if chunks:
            rag.ingest(f.name, chunks)
            total_chunks += len(chunks)
            rprint(f"  [cyan]{f.name}[/cyan]: {len(chunks)} chunks")

    rprint(f"[green]Ingested {len(files)} files, {total_chunks} chunks total.[/green]")
    rag.close()


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask"),
    top_k: int = typer.Option(5, "--top-k", "-k"),
    host: str = typer.Option("127.0.0.1", envvar="MARIADB_HOST"),
    port: int = typer.Option(3306, envvar="MARIADB_PORT"),
    user: str = typer.Option("root", envvar="MARIADB_USER"),
    password: str = typer.Option("seamless", envvar="MARIADB_PASSWORD"),
    database: str = typer.Option("seamless_rag", envvar="MARIADB_DATABASE"),
):
    """Ask a question using RAG with token benchmarking."""
    rag = _get_rag(**_db_kwargs(host, port, user, password, database))
    result = rag.ask(question, top_k=top_k)

    if result.sources:
        rprint(f"\n[bold]Context (TOON — {result.toon_tokens} tokens):[/bold]")
        rprint(result.context_toon)

        table = Table(title="\nToken Benchmark")
        table.add_column("Format", style="cyan")
        table.add_column("Tokens", justify="right")
        table.add_row("JSON", str(result.json_tokens))
        table.add_row("TOON", str(result.toon_tokens))
        table.add_row("Savings", f"{result.savings_pct:.1f}%", style="green")
        console.print(table)
    else:
        rprint(
            "[yellow]No results found. "
            "Run 'seamless-rag init' and 'seamless-rag ingest' first.[/yellow]"
        )

    rag.close()


@app.command()
def watch(
    table: str = typer.Option("chunks", "--table", "-t"),
    column: str = typer.Option("content", "--column", "-c"),
    interval: float = typer.Option(2.0, "--interval", "-i"),
    host: str = typer.Option("127.0.0.1", envvar="MARIADB_HOST"),
    port: int = typer.Option(3306, envvar="MARIADB_PORT"),
    user: str = typer.Option("root", envvar="MARIADB_USER"),
    password: str = typer.Option("seamless", envvar="MARIADB_PASSWORD"),
    database: str = typer.Option("seamless_rag", envvar="MARIADB_DATABASE"),
):
    """Watch a table for new inserts and auto-embed."""
    rag = _get_rag(**_db_kwargs(host, port, user, password, database))
    rprint(f"[blue]Watching {table}.{column} every {interval}s (Ctrl+C to stop)[/blue]")
    try:
        rag.watch(table, text_column=column, interval=interval)
    except KeyboardInterrupt:
        rprint("\n[yellow]Watch stopped.[/yellow]")
    rag.close()


@app.command(name="export")
def export_cmd(
    query: str = typer.Argument(..., help="SQL query to export as TOON"),
    host: str = typer.Option("127.0.0.1", envvar="MARIADB_HOST"),
    port: int = typer.Option(3306, envvar="MARIADB_PORT"),
    user: str = typer.Option("root", envvar="MARIADB_USER"),
    password: str = typer.Option("seamless", envvar="MARIADB_PASSWORD"),
    database: str = typer.Option("seamless_rag", envvar="MARIADB_DATABASE"),
):
    """Export SQL query results as TOON format."""
    rag = _get_rag(**_db_kwargs(host, port, user, password, database))
    rprint(rag.export(query))
    rag.close()


@app.command()
def demo(
    host: str = typer.Option("127.0.0.1", envvar="MARIADB_HOST"),
    port: int = typer.Option(3306, envvar="MARIADB_PORT"),
    user: str = typer.Option("root", envvar="MARIADB_USER"),
    password: str = typer.Option("seamless", envvar="MARIADB_PASSWORD"),
    database: str = typer.Option("seamless_rag", envvar="MARIADB_DATABASE"),
):
    """Run end-to-end demo: init -> seed data -> ask question -> show benchmark."""
    rag = _get_rag(**_db_kwargs(host, port, user, password, database))

    rprint("\n[bold magenta]Seamless-RAG End-to-End Demo[/bold magenta]\n")

    # 1. Init schema
    rprint("[bold]1. Initializing schema...[/bold]")
    rag.init()
    rprint("   [green]Done.[/green]\n")

    # 2. Seed data
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
            "Wind energy now accounts for a growing share of global electricity generation.",
            "Battery storage technology is key to making renewable energy reliable.",
            "Green hydrogen produced from electrolysis could decarbonize heavy industry.",
        ]),
        ("AI Research", [
            "Large language models demonstrate emergent capabilities at scale.",
            "Retrieval-augmented generation improves factual accuracy of AI responses.",
            "Vector databases enable efficient similarity search for embedding-based retrieval.",
            "Token efficiency in context windows directly impacts AI inference costs.",
        ]),
    ]
    for title, chunks in docs:
        rag.ingest(title, chunks)
        rprint(f"   [cyan]{title}[/cyan]: {len(chunks)} chunks")
    rprint("   [green]Done.[/green]\n")

    # 3. Ask questions
    questions = [
        "How does climate change affect biodiversity?",
        "What are the recent advances in renewable energy?",
        "How does retrieval-augmented generation work?",
    ]
    for q in questions:
        rprint(f"[bold]3. Asking:[/bold] {q}")
        result = rag.ask(q, top_k=3)

        rprint(f"\n   [bold]TOON Context ({result.toon_tokens} tokens):[/bold]")
        for line in result.context_toon.split("\n"):
            rprint(f"   {line}")

        table = Table(title="Token Benchmark", show_header=True, header_style="bold cyan")
        table.add_column("Format")
        table.add_column("Tokens", justify="right")
        table.add_row("JSON", str(result.json_tokens))
        table.add_row("TOON", str(result.toon_tokens))
        table.add_row("Savings", f"[green]{result.savings_pct:.1f}%[/green]")
        console.print(table)
        rprint()

    rag.close()
    rprint("[bold green]Demo complete![/bold green]\n")
