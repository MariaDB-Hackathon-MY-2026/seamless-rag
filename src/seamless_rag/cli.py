"""Typer CLI — init, embed, watch, ask, export, benchmark."""
from __future__ import annotations

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
    """Lazy-import to avoid heavy loading for --help."""
    from seamless_rag.core import SeamlessRAG
    return SeamlessRAG(**kwargs)


def _db_options(
    host: str = typer.Option("127.0.0.1", "--host", "-H", envvar="MARIADB_HOST"),
    port: int = typer.Option(3306, "--port", "-P", envvar="MARIADB_PORT"),
    user: str = typer.Option("root", "--user", "-u", envvar="MARIADB_USER"),
    password: str = typer.Option("seamless", "--password", "-p", envvar="MARIADB_PASSWORD"),
    database: str = typer.Option("seamless_rag", "--database", "-d", envvar="MARIADB_DATABASE"),
):
    return {"host": host, "port": port, "user": user, "password": password, "database": database}


@app.command()
def embed(
    table: str = typer.Argument(..., help="Table to embed"),
    column: str = typer.Option("content", "--column", "-c", help="Text column name"),
    batch_size: int = typer.Option(64, "--batch-size", "-b"),
    host: str = typer.Option("127.0.0.1", "--host", envvar="MARIADB_HOST"),
    port: int = typer.Option(3306, "--port", envvar="MARIADB_PORT"),
    user: str = typer.Option("root", "--user", envvar="MARIADB_USER"),
    password: str = typer.Option("seamless", "--password", envvar="MARIADB_PASSWORD"),
    database: str = typer.Option("seamless_rag", "--database", envvar="MARIADB_DATABASE"),
):
    """Bulk-embed all rows in a table."""
    rag = _get_rag(host=host, port=port, user=user, password=password, database=database)
    result = rag.embed_table(table, text_column=column, batch_size=batch_size)
    rprint(f"[green]Embedded {result['embedded']} rows[/green]")
    if result["failed"]:
        rprint(f"[red]Failed: {result['failed']}[/red]")
    rag.close()


@app.command()
def watch(
    table: str = typer.Argument(..., help="Table to watch"),
    column: str = typer.Option("content", "--column", "-c"),
    interval: float = typer.Option(2.0, "--interval", "-i"),
    host: str = typer.Option("127.0.0.1", "--host", envvar="MARIADB_HOST"),
    port: int = typer.Option(3306, "--port", envvar="MARIADB_PORT"),
    user: str = typer.Option("root", "--user", envvar="MARIADB_USER"),
    password: str = typer.Option("seamless", "--password", envvar="MARIADB_PASSWORD"),
    database: str = typer.Option("seamless_rag", "--database", envvar="MARIADB_DATABASE"),
):
    """Watch a table for new inserts and auto-embed."""
    rag = _get_rag(host=host, port=port, user=user, password=password, database=database)
    rprint(f"[blue]Watching {table}.{column} every {interval}s[/blue]")
    try:
        rag.watch(table, text_column=column, interval=interval)
    except KeyboardInterrupt:
        rprint("\n[yellow]Watch stopped.[/yellow]")
    rag.close()


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask"),
    top_k: int = typer.Option(5, "--top-k", "-k"),
    host: str = typer.Option("127.0.0.1", "--host", envvar="MARIADB_HOST"),
    port: int = typer.Option(3306, "--port", envvar="MARIADB_PORT"),
    user: str = typer.Option("root", "--user", envvar="MARIADB_USER"),
    password: str = typer.Option("seamless", "--password", envvar="MARIADB_PASSWORD"),
    database: str = typer.Option("seamless_rag", "--database", envvar="MARIADB_DATABASE"),
):
    """Ask a question using RAG with token benchmarking."""
    rag = _get_rag(host=host, port=port, user=user, password=password, database=database)
    result = rag.ask(question, top_k=top_k)

    rprint(f"\n[bold]Context (TOON):[/bold]\n{result.context_toon}\n")

    table = Table(title="Token Benchmark")
    table.add_column("Format", style="cyan")
    table.add_column("Tokens", justify="right")
    table.add_row("JSON", str(result.json_tokens))
    table.add_row("TOON", str(result.toon_tokens))
    table.add_row("Savings", f"{result.savings_pct:.1f}%", style="green")
    console.print(table)

    rag.close()


@app.command()
def export(
    query: str = typer.Argument(..., help="SQL query to export as TOON"),
    host: str = typer.Option("127.0.0.1", "--host", envvar="MARIADB_HOST"),
    port: int = typer.Option(3306, "--port", envvar="MARIADB_PORT"),
    user: str = typer.Option("root", "--user", envvar="MARIADB_USER"),
    password: str = typer.Option("seamless", "--password", envvar="MARIADB_PASSWORD"),
    database: str = typer.Option("seamless_rag", "--database", envvar="MARIADB_DATABASE"),
):
    """Export SQL query results as TOON format."""
    rag = _get_rag(host=host, port=port, user=user, password=password, database=database)
    print(rag.export(query))
    rag.close()
