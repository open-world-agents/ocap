"""
Shared test fixtures for the ocap test suite.
"""

import pytest


@pytest.fixture
def temp_mcap_file(tmp_path):
    """Create a temporary MCAP file path for testing."""
    return tmp_path / "test_recording.mcap"
