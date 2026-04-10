# Seamless-RAG — Handoff Document

> This document tracks delivery milestones and provides context for anyone picking up the project.
> Last updated: 2026-04-11

## Current State

- **Phase**: Skeleton (all stubs, zero implementation)
- **Tests**: 259 defined, 0 passing
- **Eval Score**: 0/100
- **Repo**: https://github.com/SunflowersLwtech/seamless-rag

## What's Ready

- Complete test infrastructure (unit, integration, eval, spec conformance)
- 358 TOON v3 spec fixtures (read-only)
- 20 golden QA pairs for RAG evaluation (read-only)
- Immutable evaluation harness with composite scoring (read-only)
- Docker Compose for MariaDB 11.8
- Conda environment for isolated development
- Claude Code autorun configuration

## What's Needed

See `TODO.md` for the complete task list.

## Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Approach | Option C: Python + TOON | Organizer alignment, 95% completion confidence |
| TOON impl | Custom encoder | Official Python SDK deprecated; focused on tabular |
| Embedding | all-MiniLM-L6-v2 (384d) | Local, free, no API key, all winners used it |
| Architecture | typing.Protocol DI | Winner pattern, enables mock testing |
| CLI | Typer | Winner pattern, auto-generates help |
| Setup | Docker Compose | Every winner had one-command setup |

## Milestones

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| TOON encoder passing all tests | Apr 13 | Not started |
| Token benchmark working | Apr 14 | Not started |
| Embedding provider working | Apr 15 | Not started |
| MariaDB VectorStore working | Apr 18 | Not started |
| Watch mode working | Apr 20 | Not started |
| RAG engine end-to-end | Apr 22 | Not started |
| CLI + Docker demo | Apr 25 | Not started |
| README + JUDGES_GUIDE | Apr 27 | Not started |
| Final polish + submission | Apr 30 | Not started |
