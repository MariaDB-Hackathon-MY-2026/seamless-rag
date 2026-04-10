"""Auto-embedding pipeline — watch mode and batch mode.

Watch mode features (per Judge Directive 3 — "killer feature must be bulletproof"):
- High-water mark tracking (checkpoint)
- Exponential backoff retry on failure
- Error isolation (failed rows don't block others)
- Rich live display of progress
"""


class AutoEmbedder:
    """Auto-embedding pipeline with watch and batch modes."""

    def __init__(self, provider: object, store: object) -> None:
        raise NotImplementedError("AutoEmbedder not yet implemented")

    def batch_embed(self, table: str, text_column: str, batch_size: int = 64) -> None:
        """Bulk-embed all rows lacking embeddings. Shows Rich progress bar."""
        raise NotImplementedError

    def watch(self, table: str, text_column: str, interval: float = 2.0) -> None:
        """Watch for new inserts and auto-embed. Runs until interrupted.

        Features:
        - Checkpoint: tracks MAX(id) as high-water mark
        - Retry: exponential backoff (2s, 4s, 8s) on transient failures
        - Isolation: failed rows are logged and skipped, not blocking
        - Display: Rich live panel showing detected/embedded/failed counts
        """
        raise NotImplementedError
