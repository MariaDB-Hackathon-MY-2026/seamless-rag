"""Token benchmark comparing JSON vs TOON encoding."""
from __future__ import annotations

import json
from dataclasses import dataclass

import tiktoken

from seamless_rag.toon.encoder import encode_tabular

# GPT-4o pricing: $2.50 per 1M input tokens (as of 2026)
_GPT4O_COST_PER_TOKEN = 2.50 / 1_000_000


@dataclass
class BenchmarkResult:
    """Result of a token comparison benchmark."""

    json_tokens: int
    toon_tokens: int
    savings_pct: float
    json_bytes: int
    toon_bytes: int
    json_cost_usd: float
    toon_cost_usd: float
    savings_cost_usd: float


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
        json_cost = json_tokens * _GPT4O_COST_PER_TOKEN
        toon_cost = toon_tokens * _GPT4O_COST_PER_TOKEN

        return BenchmarkResult(
            json_tokens=json_tokens,
            toon_tokens=toon_tokens,
            savings_pct=savings_pct,
            json_bytes=json_bytes,
            toon_bytes=toon_bytes,
            json_cost_usd=json_cost,
            toon_cost_usd=toon_cost,
            savings_cost_usd=json_cost - toon_cost,
        )
