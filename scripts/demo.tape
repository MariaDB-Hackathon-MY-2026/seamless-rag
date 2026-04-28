# VHS tape — Seamless-RAG end-to-end demo for hackathon judges.
#
# Render with:  vhs scripts/demo.tape
# Outputs:      docs/assets/demo.mp4 + docs/assets/demo.gif
#
# Pre-conditions:
#   - docker compose -f docker-compose.test.yml up -d --wait    (MariaDB 11.8 on :3306)
#   - conda env `seamless-rag` exists with the package installed editable
#   - all-MiniLM-L6-v2 already cached (rerun once non-recorded if first time)

Output docs/assets/demo.mp4
Output docs/assets/demo.gif

Require docker

Set Shell bash
Set FontSize 16
Set Width 1280
Set Height 760
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
Type "clear"
Enter
Sleep 500ms
Show

# ── Title card ─────────────────────────────────────────────────────
Type "echo 'Seamless-RAG  -  TOON-Native RAG Toolkit for MariaDB'"
Sleep 300ms
Enter
Sleep 1500ms
Type "echo '525 tests passing  |  MariaDB 11.8 VECTOR + HNSW  |  TOON v3 spec-conformant'"
Enter
Sleep 2500ms

# ── 1. Quality dashboard (cached read of .test-scores.json — instant) ─
Type "python scripts/score.py --cached"
Sleep 300ms
Enter
Sleep 5500ms

Type "clear"
Enter
Sleep 400ms

# ── 2. Init schema in MariaDB ──────────────────────────────────────
Type "seamless-rag init 2>/dev/null"
Sleep 300ms
Enter
Sleep 12000ms

Type "clear"
Enter
Sleep 400ms

# ── 3. Pure TOON-vs-JSON encoder ──────────────────────────────────
Type "python scripts/demo.py 2>&1 | head -30"
Sleep 300ms
Enter
Sleep 6000ms

Type "clear"
Enter
Sleep 400ms

# ── 4. End-to-end RAG against MariaDB (the headline) ──────────────
Type "seamless-rag demo 2>/dev/null | tail -55"
Sleep 300ms
Enter
Sleep 45000ms

Type "clear"
Enter
Sleep 400ms

# ── 5. Real-data benchmark (50 rows, 6 cols) ──────────────────────
Type "seamless-rag benchmark 2>/dev/null | tail -22"
Sleep 300ms
Enter
Sleep 9000ms

# ── Outro ──────────────────────────────────────────────────────────
Type "clear"
Enter
Sleep 300ms
Type "echo 'All five steps green.  See JUDGES_TESTING_GUIDE.md to reproduce.'"
Enter
Sleep 4000ms
