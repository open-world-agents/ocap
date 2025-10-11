"""
Shared test fixtures and utilities for the ocap test suite.
"""

import os
from pathlib import Path
from typing import List, Tuple
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file path for testing using pytest's tmp_path."""
    return tmp_path / "test_recording"


@pytest.fixture
def temp_mcap_file(tmp_path):
    """Create a temporary MCAP file path for testing."""
    return tmp_path / "test_recording.mcap"


@pytest.fixture
def temp_mkv_file(tmp_path):
    """Create a temporary MKV file path for testing."""
    return tmp_path / "test_recording.mkv"


@pytest.fixture
def mock_resource():
    """Create a mock resource with is_alive method."""
    resource = MagicMock()
    resource.is_alive.return_value = True
    resource.start.return_value = None
    resource.stop.return_value = None
    resource.join.return_value = None
    return resource


@pytest.fixture
def mock_resources():
    """Create a list of mock resources for testing."""
    resources = []
    for i in range(3):
        resource = MagicMock()
        resource.is_alive.return_value = True
        resource.start.return_value = None
        resource.stop.return_value = None
        resource.join.return_value = None
        resources.append((resource, f"resource_{i}"))
    return resources


@pytest.fixture
def disable_version_check():
    """Disable version checking during tests."""
    original_value = os.environ.get("OWA_DISABLE_VERSION_CHECK")
    os.environ["OWA_DISABLE_VERSION_CHECK"] = "1"
    yield
    if original_value is None:
        os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
    else:
        os.environ["OWA_DISABLE_VERSION_CHECK"] = original_value


@pytest.fixture
def mock_subprocess_env():
    """Get environment variables for subprocess calls with proper encoding."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["OWA_DISABLE_VERSION_CHECK"] = "1"  # Disable version check in subprocess
    return env


class MockRecordingContext:
    """Mock recording context for testing."""

    def __init__(self, mcap_location: Path):
        self.event_queue = MagicMock()
        self.mcap_location = mcap_location
        self.events = []

    def enqueue_event(self, event, *, topic):
        """Mock event enqueueing."""
        self.events.append((topic, event))


@pytest.fixture
def mock_recording_context(temp_mcap_file):
    """Create a mock recording context."""
    return MockRecordingContext(temp_mcap_file)


def create_healthy_resources(count: int = 3) -> List[Tuple[MagicMock, str]]:
    """Create a list of healthy mock resources with proper attributes."""
    resources = []
    for i in range(count):
        resource = MagicMock()
        resource.is_alive.return_value = True
        resource.name = f"healthy_resource_{i}"
        resource.resource_type = "test_resource"
        resource.status = "healthy"
        resources.append((resource, f"resource_{i}"))
    return resources


def create_mixed_health_resources() -> List[Tuple[MagicMock, str]]:
    """Create a list of resources with mixed health status."""
    healthy = MagicMock()
    healthy.is_alive.return_value = True
    healthy.name = "healthy_resource"
    healthy.resource_type = "test_resource"
    healthy.status = "healthy"

    unhealthy = MagicMock()
    unhealthy.is_alive.return_value = False
    unhealthy.name = "unhealthy_resource"
    unhealthy.resource_type = "test_resource"
    unhealthy.status = "unhealthy"

    return [(healthy, "healthy_resource"), (unhealthy, "unhealthy_resource")]


def create_unhealthy_resources(count: int = 2) -> List[Tuple[MagicMock, str]]:
    """Create a list of unhealthy mock resources with proper attributes."""
    resources = []
    for i in range(count):
        resource = MagicMock()
        resource.is_alive.return_value = False
        resource.name = f"failing_resource_{i}"
        resource.resource_type = "test_resource"
        resource.status = "unhealthy"
        resources.append((resource, f"failing_resource_{i}"))
    return resources


@pytest.fixture
def test_event_factory():
    """Factory for creating test events with consistent structure."""

    def _create_event(event_id: int = 0, data: str = "test_data", event_type: str = "test_event"):
        event = MagicMock()
        event.id = event_id
        event.data = data
        event.type = event_type
        event.timestamp = 1234567890 + event_id
        return event

    return _create_event


@pytest.fixture
def test_resource_factory():
    """Factory for creating test resources with consistent structure."""

    def _create_resource(name: str, is_healthy: bool = True, resource_type: str = "test_resource"):
        resource = MagicMock()
        resource.is_alive.return_value = is_healthy
        resource.name = name
        resource.resource_type = resource_type
        resource.status = "healthy" if is_healthy else "unhealthy"
        return resource

    return _create_resource


# Additional test utilities
class MockLogger:
    """Mock logger for testing logging calls."""

    def __init__(self):
        self.info_calls = []
        self.warning_calls = []
        self.error_calls = []
        self.debug_calls = []

    def info(self, message):
        self.info_calls.append(message)

    def warning(self, message):
        self.warning_calls.append(message)

    def error(self, message):
        self.error_calls.append(message)

    def debug(self, message):
        self.debug_calls.append(message)

    def clear(self):
        """Clear all logged messages."""
        self.info_calls.clear()
        self.warning_calls.clear()
        self.error_calls.clear()
        self.debug_calls.clear()


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return MockLogger()


@pytest.fixture
def mock_requests_response():
    """Create a mock requests response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"tag_name": "v1.0.0"}
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def sample_additional_properties():
    """Sample additional properties for testing."""
    return {"key1": "value1", "key2": "value2", "url": "http://example.com", "number": "42"}


def assert_no_exceptions_in_stderr(stderr: str):
    """Assert that stderr doesn't contain Python exceptions."""
    exception_indicators = [
        "Traceback",
        "ImportError",
        "ModuleNotFoundError",
        "AttributeError",
        "TypeError",
        "ValueError",
        "RuntimeError",
        "Exception:",
    ]

    for indicator in exception_indicators:
        assert indicator not in stderr, f"Found exception indicator '{indicator}' in stderr: {stderr}"


def create_mock_subprocess_result(returncode: int = 0, stdout: str = "", stderr: str = ""):
    """Create a mock subprocess result."""
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


@pytest.fixture
def clean_environment():
    """Fixture that provides a clean environment for testing."""
    original_env = os.environ.copy()

    # Remove test-affecting environment variables
    test_vars = [
        "OWA_DISABLE_VERSION_CHECK",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
    ]

    for var in test_vars:
        os.environ.pop(var, None)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
