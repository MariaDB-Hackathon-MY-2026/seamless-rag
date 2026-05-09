# Releasing

Seamless-RAG releases are driven by **git tags**. Push a tag matching
`v*.*.*` and `.github/workflows/release.yml` does everything else: builds
sdist + wheel, validates with `twine check`, uploads to PyPI, and creates
the matching GitHub Release with notes pulled from `CHANGELOG.md`.

The single source of truth for the version number is `pyproject.toml`. The
runtime `seamless_rag.__version__` reads from `importlib.metadata`, so a
bump in `pyproject.toml` automatically flows everywhere — there is no
second file to keep in sync.

## One-time setup (project owner only)

1. Generate a PyPI API token scoped to the `seamless-rag` project:
   <https://pypi.org/manage/account/token/>.
2. Add it to the GitHub repository as a secret named `PYPI_API_TOKEN`:
   `Settings → Secrets and variables → Actions → New repository secret`.
3. (Recommended, optional follow-up.) Replace the token with PyPI's
   **Trusted Publisher** (OIDC) — see the comment block inside
   `.github/workflows/release.yml`. OIDC requires no stored secret and is
   the modern best practice.

## Release flow

```bash
# 1. Bump the version (single edit) and update the changelog.
$EDITOR pyproject.toml          # version = "0.1.5"
$EDITOR CHANGELOG.md            # move Unreleased entries → ## [0.1.5] - YYYY-MM-DD

# 2. Commit and push to main.
git add pyproject.toml CHANGELOG.md
git commit -m "release: 0.1.5"
git push origin main

# 3. Tag and push the tag — this is the trigger.
git tag v0.1.5
git push origin v0.1.5
```

Watch the run at
`https://github.com/MariaDB-Hackathon-MY-2026/seamless-rag/actions/workflows/release.yml`.
The pipeline:

1. **verify** — refuses to continue if the tag doesn't match the version
   declared in `pyproject.toml`. This is the most common release-mistake
   class (tagged before bumping); the workflow catches it before
   publishing anything.
2. **build** — `python -m build` produces sdist + wheel; `twine check`
   validates metadata.
3. **pypi** — uploads to PyPI. `skip-existing: false` is intentional —
   if the version was already uploaded, the run fails so you notice
   rather than silently no-op.
4. **github-release** — extracts the changelog section for this version
   and creates the GitHub Release with the dist/ artifacts attached.

## What can go wrong

| Symptom | Cause | Recovery |
|---|---|---|
| `verify` job fails: tag mismatch | Forgot to bump `pyproject.toml` before tagging | Delete the bad tag (`git push --delete origin v0.1.5`), commit the bump, re-tag. |
| `pypi` job 403 | `PYPI_API_TOKEN` missing or expired | Regenerate on pypi.org, update the GitHub secret, re-run the failed job (no need to re-tag if `pypi` is the only failure). |
| `pypi` job: "version already exists" | Same version was previously uploaded | Bump to the next patch (`0.1.6`), re-tag. PyPI versions are immutable by design. |
| `github-release` job fails | Tag created but Release missing | Re-run that job individually; it's idempotent. |

## Yanking a bad release

PyPI lets you **yank** a release (existing installs keep working, but
`pip install seamless-rag` won't pick it up by default). Don't delete —
delete is destructive and breaks reproducibility:

```bash
# yank from the PyPI web UI:
# https://pypi.org/manage/project/seamless-rag/release/0.1.5/
# Reason: short string, e.g. "Broken init on Python 3.10"
```

Then ship the next version with the fix.
