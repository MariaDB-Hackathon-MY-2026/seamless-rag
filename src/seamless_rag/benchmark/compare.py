"""Token benchmark comparing JSON vs TOON encoding."""

from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    """Result of a token comparison benchmark."""

    json_tokens: int
    toon_tokens: int
    savings_pct: float
    json_bytes: int
    toon_bytes: int


class TokenBenchmark:
    """Compare JSON vs TOON token counts."""

    def compare(self, data: list[dict]) -> BenchmarkResult:
        raise NotImplementedError("Token benchmark not yet implemented")
