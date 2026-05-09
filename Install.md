# Seamless-RAG Install

This file is for coding agents. If the Seamless-RAG repository is not already cloned and open, clone `https://github.com/MariaDB-Hackathon-MY-2026/seamless-rag.git` first, then continue from the repository root.

## Goal

Bootstrap a Seamless-RAG local development workspace on the user's machine with the least risky path available.

Default preference:

1. Docker development environment (brings up MariaDB 11.8 with VECTOR support and an app container in one command).
2. Local development environment (the user already has MariaDB 11.7.2+ available, or only wants the TOON encoder).

Do not assume API keys, model credentials, or a running MariaDB exist. Set up everything that can be prepared safely, then stop with a concise summary of what the user still needs to provide.

## Operating Rules

- Be idempotent. Re-running this document should not damage an existing setup.
- Prefer existing repo commands (`docker compose`, `make`, `seamless-rag` CLI) over ad-hoc shell.
- Do not use `sudo` or install system packages without explicit user approval.
- Do not overwrite existing user config values unless the user asks.
- Do not read `.env`, `.env.local`, or any other file likely to contain secrets. Inspect filenames and `.env.example` only.
- If a step fails, stop, explain the blocker, and provide the smallest next action — do not retry destructively.
- If multiple setup paths are possible, prefer Docker when Docker is already available and the daemon is reachable.
- Seamless-RAG **requires MariaDB 11.7.2 or newer** (VECTOR type and HNSW index landed in that release). Do not silently fall back to MySQL or older MariaDB.

## Success Criteria

Consider the setup successful when all of the following are true:

- The Seamless-RAG repository is cloned and the current working directory is the repo root.
- `.env` exists (created from `.env.example` if missing — never overwritten).
- For the **Docker** path: `docker compose up -d --wait` returned successfully and `docker compose ps` shows the `db` service `healthy` and the `app` service running. The app container's entrypoint runs `seamless-rag init` once on startup, so the schema is already created. You did not start any additional long-running processes.
- For the **local** path: `pip install` of `seamless-rag[mariadb,embeddings]` (or `-e ".[mariadb,embeddings]"` from source) completed successfully, and the `seamless-rag` CLI is reachable on `PATH`. You did NOT start MariaDB on the user's behalf — the user must point the CLI at an existing MariaDB 11.7.2+ instance.
- The user has been told the **exact next command** to verify the install (typically `docker compose exec app seamless-rag demo` or `seamless-rag demo`).
- The user has been told **which environment variables still need real values** (read from `.env.example`, not `.env`) — typically API keys for hosted providers, or nothing at all if they're staying on the default local providers.

## Steps

1. **Locate or clone the repo.**
   - If the current directory contains `pyproject.toml` with `name = "seamless-rag"` and a `src/seamless_rag/` directory, treat it as the repo root and continue.
   - Otherwise clone `https://github.com/MariaDB-Hackathon-MY-2026/seamless-rag.git` into the user's chosen working directory and `cd` into it. Confirm `Makefile`, `docker-compose.yml`, `pyproject.toml`, and `src/seamless_rag/` all exist before continuing.

2. **Create `.env` if missing.** If `.env` does not exist, copy `.env.example` to `.env`. Do not modify any values. Do not read `.env` afterward — defaults are documented in `.env.example`.

3. **Detect Docker.** Run `docker info` (silently, ignore stderr). If it succeeds, take the Docker path. Otherwise take the local path.

4. **Docker path:**
    - Check that port 3306 on `localhost` is free (`lsof -i :3306` or equivalent). If something else is listening, stop and tell the user — they likely have a local MySQL/MariaDB running and need to either stop it or remap the compose port.
    - Run `docker compose up -d --wait`. This brings up MariaDB 11.8 (image `mariadb:11.8`) and the `app` container; the app container's command runs `seamless-rag init` and then sleeps so the user can `docker compose exec app seamless-rag <cmd>`.
    - Run `docker compose ps` to confirm the `db` service is `healthy` and the `app` service is `running`.
    - Tell the user the recommended next command is `docker compose exec app seamless-rag demo`.
    - Do NOT run `seamless-rag demo` yourself — `demo` may pull embedding/LLM models and take a few minutes; that is the user's call.

5. **Local path:**
    - Detect a Python interpreter ≥ 3.10. Prefer `python3` over `python`. If only Python < 3.10 is available, stop and tell the user.
    - If a virtualenv / conda env is not already active, create one (`python -m venv .venv && source .venv/bin/activate`). Do not install into the system Python.
    - Run `pip install -e ".[mariadb,embeddings]"` from the repo root. This pulls in the `mariadb` Python connector (a C extension) and the local sentence-transformers embedding stack.
    - If the `mariadb` build fails with `mariadb_config not found`, stop and tell the user to install the system library first (do NOT run these for them):
        - macOS: `brew install mariadb-connector-c`
        - Debian/Ubuntu: `sudo apt install libmariadb-dev`
        - RHEL/Fedora: `sudo dnf install mariadb-connector-c-devel`
    - Verify the CLI works: `seamless-rag --help` should print the command list. If it doesn't, stop and report the error.
    - Tell the user **they** must provide a running MariaDB **11.7.2 or newer** before `seamless-rag init` will work. The fastest one-liner is `docker run -d -p 3306:3306 -e MARIADB_ROOT_PASSWORD=seamless -e MARIADB_DATABASE=seamless_rag mariadb:11.8`. Do not run this on their behalf unless they ask.
    - Tell the user the recommended next command is `seamless-rag init` (once their MariaDB is reachable), then `seamless-rag demo`.

6. **Identify remaining configuration the user must provide.** Inspect `.env.example` (NOT `.env`) and report which environment variables still need real values for the user's intended use case:
    - Defaults (`EMBEDDING_PROVIDER=sentence-transformers`, `LLM_PROVIDER=ollama`) need no API keys but require Ollama running locally with a pulled model.
    - For Gemini: `EMBEDDING_API_KEY` / `LLM_API_KEY` (one Google AI Studio or Vertex AI Express key works for both — keys with the `AQ.` prefix auto-route through Vertex AI).
    - For OpenAI: `EMBEDDING_API_KEY` / `LLM_API_KEY` / `OPENAI_API_KEY`.
    - Ask the user which provider they want and only mention the variables relevant to that choice.

## Verification

Use the lightest verification that matches the chosen setup path.

For Docker setup:
- `docker compose ps` shows `db` healthy and `app` running.
- `.env` exists.
- State explicitly that `seamless-rag demo` was NOT run yet, and that it is the user's first real-launch step.

For local setup:
- `seamless-rag --help` exits 0.
- `.env` exists.
- State explicitly that you did NOT start a MariaDB instance on their behalf and that they must provide one.

In neither case should you leave background services running unless the user asked for that.

## Final Response Format

Return a short status report with:

1. **Setup path used**: Docker or local.
2. **Setup level reached**: e.g. "Docker compose stack up and healthy", "pip install completed, MariaDB still required".
3. **Files created or detected**: e.g. `.env (created from .env.example)`, `.venv/ (created)`.
4. **Remaining user action**: API keys to set, MariaDB to provide, models to pull (Ollama), or "nothing — you're ready to run the demo".
5. **Exact next command** to verify the install end-to-end.

If any step failed, replace 4 and 5 with the smallest concrete fix (one command or one config edit) the user can do to unblock.

## Optional: AI Agent Skills

This repository ships agent skills under `skills/public/`:

- `skills/public/seamless-rag/SKILL.md` — using the toolkit (CLI + Python API + TOON format).
- `skills/public/text-to-sql/SKILL.md` — turning natural-language data questions into safe SELECTs against MariaDB.

If the user is running an Anthropic-skill-aware agent (Claude Code, Claude.ai with skills enabled, or any agent that loads SKILL.md files), they can install these into their agent's skills directory after bootstrap completes. They are NOT required for the package to work — only for richer agent guidance.

## EXECUTE NOW

Complete the steps above. When finished, stop after the setup boundary and report status instead of continuing into unrelated project work, model downloads, or running the demo.
