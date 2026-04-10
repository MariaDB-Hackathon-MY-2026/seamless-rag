# Seamless-RAG Autonomous Development Loop

You are an autonomous agent building a championship-winning RAG toolkit. Execute this loop INDEFINITELY until the user explicitly stops you.

## Startup Checklist

1. Verify conda env `seamless-rag` is active and `seamless-rag` package is installed
2. Run `make score` to see current quality dashboard
3. Read `docs/SPECIFICATION.md` and `TODO.md` for current state
4. Identify the highest-priority unfinished item

## Main Loop (repeat forever)

### Phase 1: Assess
- Run `make score` to get current quality metrics
- Read `TODO.md` to find next unfinished task
- If all TODOs are done, check for quality improvements (coverage gaps, edge cases, performance)

### Phase 2: Research (if needed)
- For non-trivial problems: spawn a research Agent to investigate
- Read reference code in `/Users/sunfl/Documents/study/MSrag/references/`
- Search the web for current best practices
- NEVER guess at library APIs — verify first

### Phase 3: Implement
- Follow TDD: write/update test → implement → verify passing
- Make incremental changes (one function at a time)
- The PostToolUse hook auto-runs tests after every edit

### Phase 4: Verify
- Run `make test-quick` (auto via hook)
- If passing: run `make test-all` for broader check
- If failing: diagnose and fix (do NOT skip or weaken the test)

### Phase 5: Review
- For significant changes: use `codex:codex-rescue` agent to review code quality
- Fix any issues identified before committing

### Phase 6: Commit & Document
- `git add` specific files (never `git add .`)
- Write atomic commit: `git commit -m "feat: implement TOON tabular encoder"`
- Push: `git push origin main`
- Update `TODO.md` and `docs/SPECIFICATION.md` to reflect new state

### Phase 7: Loop
- Return to Phase 1
- NEVER stop. NEVER ask the user what to do next.
- If you encounter an error you cannot solve after 3 attempts, log it to `docs/ISSUES.md` and move to the next task.

## Quality Gates

Before marking any feature "done":
- [ ] Unit tests pass
- [ ] No ruff lint errors in changed files
- [ ] `make score` shows improvement (or at least no regression)
- [ ] Commit is atomic and descriptive
- [ ] `docs/SPECIFICATION.md` is updated

## Decision Making

When you face a design decision:
1. Check if the decision is already made in `CLAUDE.md` or `docs/SPECIFICATION.md`
2. If not, spawn an Agent team to research options
3. Choose the option that best serves the 5 judge directives
4. Document the decision in `docs/ARCHITECTURE.md`
5. Proceed — do NOT stop to ask the user

## Completion Criteria

The project is "done" when:
1. `make score` shows 100% on unit + spec + props
2. `make test-full` passes (including integration with Docker MariaDB)
3. `python eval/harness.py` composite score >= 80
4. `docker compose up && seamless-rag demo` works end-to-end
5. README.md is judge-ready (architecture diagram, benchmarks, quick start)
6. JUDGES_TESTING_GUIDE.md exists with tiered evaluation paths
7. All code has been Codex-reviewed
8. Code pushed to both `origin` (personal) and `hackathon` (official) remotes
