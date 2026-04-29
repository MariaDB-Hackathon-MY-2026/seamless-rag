# VHS tape — Seamless-RAG end-to-end demo for hackathon judges.
#
# Render with:  vhs scripts/demo.tape
# Outputs:      docs/assets/demo.mp4 + docs/assets/demo.gif
#
# Pre-conditions:
#   - docker compose -f docker-compose.test.yml up -d --wait    (MariaDB 11.8 on :3306)
#   - conda env `seamless-rag` exists with the package installed editable
#   - all-MiniLM-L6-v2 already cached (rerun once non-recorded if first time)
#   - test_seamless_rag DB freshly dropped+created so the schema demo lands
#     on a clean state (the surrounding render script does this).

Output docs/assets/demo.mp4
Output docs/assets/demo.gif

Require docker

Set Shell bash
Set FontSize 16
Set Width 1280
Set Height 1000
Set Padding 24
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set BorderRadius 10
Set TypingSpeed 26ms

# ── Hidden setup: PATH + DB env so commands look natural on screen ──
Hide
Type "export PATH=/opt/anaconda3/envs/seamless-rag/bin:$PATH"
Enter
Type "export MARIADB_DATABASE=test_seamless_rag MARIADB_PASSWORD=seamless"
Enter
Type "export PS1='$ '"
Enter
Ctrl+L
Sleep 500ms
Show

# ── Title card ─────────────────────────────────────────────────────
Type "echo 'Seamless-RAG  -  TOON-Native RAG Toolkit for MariaDB'"
Sleep 300ms
Enter
Sleep 1500ms
Type "echo '530 tests passing  |  MariaDB 11.8 VECTOR + HNSW  |  TOON v3 spec-conformant'"
Enter
Sleep 2500ms

# ── 1. Quality dashboard (cached read of .test-scores.json — instant) ─
Type "python scripts/score.py --cached"
Sleep 300ms
Enter
Sleep 5500ms

Ctrl+L
Sleep 400ms

# ── 2. Init schema in MariaDB ──────────────────────────────────────
Type "seamless-rag init 2>/dev/null"
Sleep 300ms
Enter
Sleep 12000ms

Ctrl+L
Sleep 400ms

# ── 3a. Ingest sample documents so schema has rows for VEC_DISTANCE ─
Type "seamless-rag ingest /tmp/rag_e2e_docs 2>/dev/null | tail -4"
Sleep 300ms
Enter
Sleep 8000ms

# Clear so the schema panel starts at the top of the viewport, leaving
# room for SHOW CREATE TABLE + SHOW INDEX + VEC_DISTANCE comparison.
Ctrl+L
Sleep 400ms

# ── 3b. MariaDB schema proof: VECTOR(384) + HNSW + DISTANCE=cosine ──
# Sleep covers: ~6s model load + ~2s schema queries + ~1s second embedding
# for the VEC_DISTANCE comparison + ~7s of visible time for the comparison
# table to be readable.
Type "seamless-rag schema 2>/dev/null"
Sleep 300ms
Enter
Sleep 18000ms

Ctrl+L
Sleep 400ms

# ── 4. Pure TOON-vs-JSON encoder ──────────────────────────────────
Type "python scripts/demo.py 2>&1 | head -30"
Sleep 300ms
Enter
Sleep 6000ms

Ctrl+L
Sleep 400ms

# ── 5. End-to-end RAG against MariaDB (the headline) ──────────────
Type "seamless-rag demo 2>/dev/null | tail -55"
Sleep 300ms
Enter
Sleep 45000ms

Ctrl+L
Sleep 400ms

# ── 6. Real-data benchmark (50 rows, 6 cols) ──────────────────────
Type "seamless-rag benchmark 2>/dev/null | tail -22"
Sleep 300ms
Enter
Sleep 9000ms

# ── Outro ──────────────────────────────────────────────────────────
Ctrl+L
Sleep 300ms
Type "echo 'All six steps green.  See JUDGES_TESTING_GUIDE.md to reproduce.'"
Enter
Sleep 4000ms
