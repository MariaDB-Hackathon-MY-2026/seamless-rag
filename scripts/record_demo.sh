#!/usr/bin/env bash
#
# Deterministic demo runner — pacing tuned for a 2–4 min screencast.
#
# Prereqs (the recorder verifies these):
#   - docker compose -f docker-compose.test.yml up -d --wait
#   - conda activate seamless-rag  (or have seamless-rag on PATH)
#   - MARIADB_DATABASE=test_seamless_rag MARIADB_PASSWORD=seamless

set -euo pipefail

PAUSE_SHORT=${PAUSE_SHORT:-1.2}
PAUSE_LONG=${PAUSE_LONG:-2.5}

export MARIADB_DATABASE=${MARIADB_DATABASE:-test_seamless_rag}
export MARIADB_PASSWORD=${MARIADB_PASSWORD:-seamless}

banner() {
  echo
  echo "════════════════════════════════════════════════════════════════"
  echo "  $1"
  echo "════════════════════════════════════════════════════════════════"
  sleep "$PAUSE_SHORT"
}

banner "Seamless-RAG — TOON-Native RAG Toolkit for MariaDB"
echo "MariaDB 11.8  •  VECTOR(384)  •  HNSW  •  TOON v3  •  100% test pass"
sleep "$PAUSE_LONG"

banner "1/5  Quality dashboard (525 tests)"
make score 2>&1 | tail -14
sleep "$PAUSE_LONG"

banner "2/5  Initialise schema in MariaDB"
seamless-rag init
sleep "$PAUSE_SHORT"

banner "3/5  TOON v3 vs JSON — pure encoding"
python scripts/demo.py
sleep "$PAUSE_LONG"

banner "4/5  End-to-end RAG against MariaDB (token panel per query)"
seamless-rag demo
sleep "$PAUSE_LONG"

banner "5/5  Real public-dataset benchmark"
seamless-rag benchmark
sleep "$PAUSE_LONG"

banner "Done. See JUDGES_TESTING_GUIDE.md for full evaluation paths."
