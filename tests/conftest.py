"""Shared pytest fixtures for the sphinx-sv-domain test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ["sphinx.testing.fixtures"]

# The ``roots`` directory holds mini Sphinx projects, not test modules.
collect_ignore = ["roots"]


@pytest.fixture(scope="session")
def rootdir() -> Path:
    """Directory containing the ``test-*`` Sphinx roots used by ``app``."""
    return Path(__file__).parent.resolve() / "roots"
