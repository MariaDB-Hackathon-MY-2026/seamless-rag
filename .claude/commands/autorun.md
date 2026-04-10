# Seamless-RAG Autonomous Development Loop

You are an autonomous agent building a championship-winning RAG toolkit for the MariaDB Hackathon MY 2026. Execute this loop INDEFINITELY until the user explicitly stops you with Ctrl+C.

**NEVER stop to ask the user anything. NEVER say "shall I continue". Just keep going.**

## Startup Checklist

1. Run `conda run -n seamless-rag python -m pytest tests/unit --co -q 2>&1 | tail -3` to verify env works
2. Run `conda run -n seamless-rag python scripts/score.py` to see current dashboard
3. Read `TODO.md` for what needs doing
4. Read `docs/SPECIFICATION.md` for current state
5. Begin the main loop at Phase 1

## Main Loop (repeat forever)

### Phase 1: ASSESS — What's the next task?

```
conda run -n seamless-rag python scripts/score.py
```

Read `TODO.md`. Pick the **first unchecked item** in priority order.
If all are checked, look for quality improvements (coverage gaps, flaky tests, missing edge cases, docs).

### Phase 2: RESEARCH — Understand before coding

**RULE: Never guess. Always verify. Use these tools:**

**For understanding a library API or TOON spec detail:**
```
Use Agent tool with subagent_type="Explore" to search the reference code:
  prompt: "Find how the TypeScript TOON encoder handles tabular arrays.
           Look in /Users/sunfl/Documents/study/MSrag/references/p0-core/toon-official/packages/toon/src/encode/"
```

**For current best practices or library docs:**
```
Use WebSearch tool:
  query: "mariadb-connector-python array.array vector insert example 2026"
```

**For complex technical questions requiring deep research:**
```
Use Agent tool (general-purpose, background):
  prompt: "Research how to implement exponential backoff retry in Python for a database
           polling loop. Find production-grade patterns. Return code examples."
```

**For reading specific documentation pages:**
```
Use WebFetch tool:
  url: "https://mariadb.com/kb/en/vector-overview/"
```

**For multi-faceted investigation (spawn a team):**
```
Launch multiple Agent tools in parallel:
  Agent 1: "Research TOON v3 spec Section 7.2 quoting rules by reading /references/p0-core/toon-spec/SPEC.md"
  Agent 2: "Search web for Python regex patterns for TOON numeric detection"
  Agent 3: "Read the TypeScript reference encoder at /references/p0-core/toon-official/packages/toon/src/encode/primitives.ts"
```

### Phase 3: IMPLEMENT — TDD cycle

1. **Read the failing test** carefully — understand exactly what it expects
2. **Read reference code** if the implementation requires specific API knowledge
3. **Write the minimum code** to pass the test
4. **Let the PostToolUse hook** run tests automatically after each edit
5. If tests pass: move to next failing test
6. If tests fail: read the error, fix the implementation (NOT the test)
7. Repeat until all tests in the current component pass

### Phase 4: VERIFY — Broader checks

After a component passes its unit tests:
```bash
conda run -n seamless-rag python -m pytest tests/unit -v --tb=short   # all unit tests
conda run -n seamless-rag ruff check src/seamless_rag/                # lint
conda run -n seamless-rag python scripts/score.py                     # score dashboard
```

### Phase 5: CODEX REVIEW — Quality gate

**Before any commit of a new feature or significant refactor, get a Codex review:**

```
Use Agent tool with subagent_type="codex:codex-rescue":
  prompt: "Review the TOON v3 tabular encoder implementation at
           /Users/sunfl/Documents/study/MSrag/workspace/src/seamless_rag/toon/encoder.py

           Check for:
           1. Correctness against TOON v3 spec (quoting rules, escape sequences, number canonicalization)
           2. Edge cases: null, empty string, commas in values, newlines, unicode, negative zero
           3. Code quality: type hints, readability, no unnecessary complexity
           4. Performance: no quadratic algorithms for large datasets

           Rate the code A/B/C/D and list specific issues to fix."
```

**Fix ALL issues Codex identifies before committing.** If Codex rates B or lower on critical code (TOON encoder, RAG engine), iterate until it's an A.

### Phase 6: COMMIT & DOCUMENT

```bash
# Stage specific files (NEVER git add . or git add -A)
git add src/seamless_rag/toon/encoder.py tests/unit/test_toon_encoder.py

# Atomic commit with conventional prefix
git commit -m "feat: implement TOON v3 tabular encoder with value quoting and number canonicalization"

# Push
git push origin main
```

Then update live docs:
- Mark the item as `[x]` in `TODO.md`
- Update `docs/SPECIFICATION.md` with what's now implemented
- Update `docs/HANDOFF.md` milestones

### Phase 7: LOOP

Go back to Phase 1. **Do NOT stop.** Do NOT ask the user.
If you hit an unsolvable blocker after 3 attempts:
1. Log it to `docs/ISSUES.md` with full context
2. Skip to the next TODO item
3. Continue the loop

## Tool Usage Recipes

### Recipe: "I don't know how this MariaDB API works"
```
1. Agent(subagent_type="Explore", prompt="Find vector insert examples in /references/p0-core/mariadb-connector-python/testing/test/integration/")
2. If not enough: WebSearch("mariadb connector python vector insert array.array example")
3. If still unclear: WebFetch("https://mariadb-corporation.github.io/mariadb-connector-python/usage.html")
```

### Recipe: "I need to understand a TOON spec rule"
```
1. Read the specific section from /references/p0-core/toon-spec/SPEC.md
2. Read the TypeScript reference implementation in /references/p0-core/toon-official/packages/toon/src/encode/
3. Check the test fixtures in tests/fixtures/toon_spec/encode/ for examples
```

### Recipe: "A test is failing and I don't understand why"
```
1. Run the single failing test with -v --tb=long to see full traceback
2. Read the test code to understand what it expects
3. Read the fixture/input data
4. If it's a TOON spec test: compare with the TypeScript reference encoder output
5. If still stuck: spawn an Agent to investigate the specific edge case
```

### Recipe: "I need to make a design decision"
```
1. Check CLAUDE.md and docs/ARCHITECTURE.md for existing decisions
2. Spawn parallel research agents:
   Agent 1: "Search web for [option A] best practices"
   Agent 2: "Search web for [option B] best practices"
   Agent 3: "Check how the YT semantic search winner handled this in /references/p1-reference/yt-semantic-search-winner/"
3. Compare findings against the 5 judge directives
4. Choose the option, document in docs/ARCHITECTURE.md
5. Proceed — do NOT ask the user
```

### Recipe: "Integration test needs Docker MariaDB"
```bash
# Start test MariaDB
docker compose -f docker-compose.test.yml up -d --wait
# Run integration tests
conda run -n seamless-rag python -m pytest tests/integration -v --tb=short
# Clean up
docker compose -f docker-compose.test.yml down -v
```

### Recipe: "Final delivery push to hackathon remote"
```bash
# Ensure all tests pass
conda run -n seamless-rag python -m pytest tests/ -v --tb=short -m "not eval"
# Push to personal
git push origin main
# Push to hackathon
git push hackathon main
```

## Quality Gates

Before marking any feature "done":
- [ ] All related unit tests pass (not just the new ones)
- [ ] `ruff check` passes on changed files
- [ ] `make score` shows improvement or no regression
- [ ] Codex review is A-grade (for critical components)
- [ ] Commit is atomic with conventional message prefix
- [ ] `docs/SPECIFICATION.md` and `TODO.md` are updated

## Completion Criteria (the project is "done" when ALL are true)

1. `make score` → 100% unit + 100% spec + 95%+ props
2. `make test-full` → all pass including Docker integration
3. `python eval/harness.py` → composite score >= 80
4. `docker compose up -d && conda run -n seamless-rag seamless-rag ask "test question"` → works end-to-end
5. README.md → judge-ready with architecture, benchmarks, quick start
6. JUDGES_TESTING_GUIDE.md → exists with 4 evaluation tiers
7. All critical code Codex-reviewed at A grade
8. Pushed to both `origin` and `hackathon` remotes
9. `docs/HANDOFF.md` → all milestones marked complete
