.PHONY: setup test test-quick test-unit test-spec test-props test-all test-full \
       test-integration test-docker lint coverage score eval clean docker-up docker-down

CONDA_RUN = conda run -n seamless-rag

# ── Setup ──────────────────────────────────────────────────
setup:
	conda env create -f environment.yml 2>/dev/null || conda env update -f environment.yml
	$(CONDA_RUN) pip install -e ".[dev]" --quiet
	@echo "✓ Environment ready. Activate with: conda activate seamless-rag"

# ── Fast Feedback (hook target) ────────────────────────────
test-quick:
	$(CONDA_RUN) python -m pytest tests/unit -x -q --tb=line --no-header 2>&1 | tail -20

test: test-unit

# ── Individual Suites ──────────────────────────────────────
test-unit:
	$(CONDA_RUN) python -m pytest tests/unit -v --tb=short

test-spec:
	$(CONDA_RUN) python -m pytest tests/unit/test_toon_spec_fixtures.py -v --tb=short

test-props:
	$(CONDA_RUN) python -m pytest tests/unit/test_toon_properties.py -v --tb=short

test-integration: docker-up
	$(CONDA_RUN) python -m pytest tests/integration -v --tb=short -m integration

test-eval:
	$(CONDA_RUN) python -m pytest tests/eval -v --tb=short -m eval

# ── Quality Gates ──────────────────────────────────────────
lint:
	$(CONDA_RUN) ruff check src/ tests/

coverage:
	$(CONDA_RUN) python -m pytest tests/unit --cov=seamless_rag --cov-report=term-missing --cov-fail-under=80

# ── Combined ───────────────────────────────────────────────
test-all: lint test-unit test-spec
	@echo "═══════ ALL CORE TESTS PASSED (lint+unit+spec) ═══════"

test-full: lint test-unit test-spec test-props test-integration
	@echo "═══════ FULL SUITE PASSED ═══════"

# ── Scoring ────────────────────────────────────────────────
score:
	$(CONDA_RUN) python scripts/score.py

eval:
	$(CONDA_RUN) python eval/harness.py

# ── Docker ─────────────────────────────────────────────────
docker-up:
	docker compose -f docker-compose.test.yml up -d --wait

docker-down:
	docker compose -f docker-compose.test.yml down -v

# ── Cleanup ────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage .test-scores.json
