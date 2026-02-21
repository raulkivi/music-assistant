"""pytest configuration for omr-mcp tests."""

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip integration-marked tests unless explicitly requested with -m integration."""
    mark_expr = config.option.markexpr if hasattr(config.option, "markexpr") else ""
    if mark_expr == "integration":
        return  # user is explicitly running integration tests — don't skip

    skip_integration = pytest.mark.skip(
        reason="Integration test — run with: uv run pytest tests/ -v -m integration"
    )
    for item in items:
        if item.get_closest_marker("integration"):
            item.add_marker(skip_integration)
