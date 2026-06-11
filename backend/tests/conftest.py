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

# Tests that drive the live model are skipped unless a REAL key is present, so CI
# stays green without secrets while the full agent suite runs locally with a key.
# The placeholder from .env.example ("sk-ant-...") counts as "no key" — otherwise a
# reviewer who runs pytest before pasting their key would see 401s instead of skips.
_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
_HAS_REAL_KEY = bool(_API_KEY) and "..." not in _API_KEY

requires_api_key = pytest.mark.skipif(
    not _HAS_REAL_KEY,
    reason="No real ANTHROPIC_API_KEY (unset or still the .env.example placeholder) "
    "— skipping live-agent tests.",
)
