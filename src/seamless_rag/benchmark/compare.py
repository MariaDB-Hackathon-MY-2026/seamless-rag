"""Token benchmark comparing JSON vs TOON encoding."""
from __future__ import annotations

import json
from dataclasses import dataclass

import tiktoken

from seamless_rag.toon.encoder import encode_tabular


@dataclass
class BenchmarkResult:
    """Result of a token comparison benchmark."""

    json_tokens: int
    toon_tokens: int
    savings_pct: float
    json_bytes: int
    toon_bytes: int


class TokenBenchmark:
    """Compare JSON vs TOON token counts using tiktoken (cl100k_base)."""

    def __init__(self, model: str = "cl100k_base"):
        self._enc = tiktoken.get_encoding(model)

    def count_tokens(self, text: str) -> int:
        return len(self._enc.encode(text))

    def compare(self, data: list[dict]) -> BenchmarkResult:
        json_str = json.dumps(data)
        toon_str = encode_tabular(data)

        json_bytes = len(json_str.encode("utf-8"))
        toon_bytes = len(toon_str.encode("utf-8"))

        json_tokens = self.count_tokens(json_str)
        toon_tokens = self.count_tokens(toon_str)

        savings_pct = (json_tokens - toon_tokens) / json_tokens * 100 if json_tokens > 0 else 0.0

        return BenchmarkResult(
            json_tokens=json_tokens,
            toon_tokens=toon_tokens,
            savings_pct=savings_pct,
            json_bytes=json_bytes,
            toon_bytes=toon_bytes,
        )
