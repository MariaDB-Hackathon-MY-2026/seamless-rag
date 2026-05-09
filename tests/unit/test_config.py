"""Tests for the Pydantic Settings configuration.

These regression tests lock in the documented env-var aliases. Users copy
keys from many places (Google AI Studio uses GEMINI_API_KEY, Google Cloud
uses GOOGLE_API_KEY, Vertex Express uses VERTEX_AI_API_KEY); making them
rename their .env to match our internal convention is a footgun we
already shipped once.
"""
from __future__ import annotations

import os
from contextlib import contextmanager

import pytest

from seamless_rag.config import Settings


@contextmanager
def env(**vars):
    """Temporarily set env vars for one test, restore on exit."""
    saved = {k: os.environ.get(k) for k in vars}
    # Clear conflicting names too: pydantic-settings reads .env by default,
    # but we want each test to control exactly what's in the environment.
    # Anything starting with EMBEDDING_/LLM_/MARIADB_/GEMINI/GOOGLE/VERTEX/OPENAI
    # we save + clear, then restore. Keeps tests isolated.
    extra_clears = [
        k for k in os.environ
        if k.startswith(("EMBEDDING_", "LLM_", "MARIADB_", "OPENAI_", "GEMINI_", "GOOGLE_", "VERTEX_"))
        and k not in vars
    ]
    for k in extra_clears:
        saved[k] = os.environ.pop(k)
    for k, v in vars.items():
        os.environ[k] = v
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        for k in vars:
            if k not in saved:
                os.environ.pop(k, None)


class TestApiKeyAliases:
    """Provider-specific Google key names should populate embedding_api_key
    and llm_api_key, so users don't have to rename their .env."""

    def test_canonical_embedding_key(self):
        with env(EMBEDDING_API_KEY="canonical"):
            assert Settings(_env_file=None).embedding_api_key == "canonical"

    def test_gemini_api_key_populates_embedding(self):
        with env(GEMINI_API_KEY="from-ai-studio"):
            assert Settings(_env_file=None).embedding_api_key == "from-ai-studio"

    def test_google_api_key_populates_embedding(self):
        with env(GOOGLE_API_KEY="from-cloud"):
            assert Settings(_env_file=None).embedding_api_key == "from-cloud"

    def test_vertex_ai_api_key_populates_embedding(self):
        with env(VERTEX_AI_API_KEY="from-vertex"):
            assert Settings(_env_file=None).embedding_api_key == "from-vertex"

    def test_canonical_llm_key(self):
        with env(LLM_API_KEY="canonical"):
            assert Settings(_env_file=None).llm_api_key == "canonical"

    def test_gemini_api_key_populates_llm(self):
        with env(GEMINI_API_KEY="shared-google-key"):
            s = Settings(_env_file=None)
            # Same Google key fans out to BOTH embedding and llm fields,
            # which is what users expect — one Google account, both surfaces.
            assert s.embedding_api_key == "shared-google-key"
            assert s.llm_api_key == "shared-google-key"

    def test_canonical_takes_precedence_over_alias(self):
        # If both are set, the canonical name wins — first item in
        # AliasChoices is the highest priority.
        with env(EMBEDDING_API_KEY="canonical", GEMINI_API_KEY="alias"):
            assert Settings(_env_file=None).embedding_api_key == "canonical"

    def test_openai_key_unchanged(self):
        # The OpenAI field has its own dedicated env var; setting Google
        # aliases must not leak into it.
        with env(GEMINI_API_KEY="google-key", OPENAI_API_KEY="oai-key"):
            s = Settings(_env_file=None)
            assert s.openai_api_key == "oai-key"
            assert s.embedding_api_key == "google-key"

    def test_no_keys_means_empty_strings(self):
        with env():
            s = Settings(_env_file=None)
            assert s.embedding_api_key == ""
            assert s.llm_api_key == ""
            assert s.openai_api_key == ""

    def test_extra_unknown_env_vars_ignored(self):
        # Settings has extra="ignore"; .env files often contain unrelated
        # entries (TWINE_PASSWORD, HF_TOKEN, etc.) which must not cause
        # validation errors.
        with env(EMBEDDING_API_KEY="x", TWINE_PASSWORD="secret"):
            Settings(_env_file=None)  # should not raise
