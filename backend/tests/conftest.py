"""Shared pytest fixtures + .env loading for the backend test suite."""

import os
import sys

import pytest
from dotenv import load_dotenv

# make backend/ importable (store, tools, agent) when running from repo root
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND_DIR)

load_dotenv(os.path.join(_BACKEND_DIR, "..", ".env"))
load_dotenv(os.path.join(_BACKEND_DIR, ".env"))

# Tests that drive the live model are skipped unless a key is present, so CI
# stays green without secrets while the full agent suite runs locally with a key.
requires_api_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live-agent tests.",
)
