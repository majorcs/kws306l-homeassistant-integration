"""Shared pytest fixtures for the KWS306L integration tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom_components from the repository under test."""
    yield
