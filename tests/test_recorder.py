"""
Tests for core recorder functionality in owa.ocap.recorder module.
"""

from queue import Queue
from unittest.mock import MagicMock, patch

import pytest
import typer

from owa.ocap.recorder import (
    RecordingContext,
    check_plugin,
    check_resources_health,
    ensure_output_files_ready,
)


# Helper functions for creating test resources
def create_healthy_resources(count: int = 3):
    """Create a list of healthy mock resources."""
    resources = []
    for i in range(count):
        resource = MagicMock()
        resource.is_alive.return_value = True
        resources.append((resource, f"resource_{i}"))
    return resources


def create_mixed_health_resources():
    """Create a list of resources with mixed health status."""
    healthy = MagicMock()
    healthy.is_alive.return_value = True

    unhealthy = MagicMock()
    unhealthy.is_alive.return_value = False

    return [(healthy, "healthy_resource"), (unhealthy, "unhealthy_resource")]


def create_unhealthy_resources(count: int = 2):
    """Create a list of unhealthy mock resources."""
    resources = []
    for i in range(count):
        resource = MagicMock()
        resource.is_alive.return_value = False
        resources.append((resource, f"failing_resource_{i}"))
    return resources


class TestRecordingContext:
    """Test the RecordingContext class."""

    def test_init(self, temp_mcap_file):
        """Test RecordingContext initialization."""
        context = RecordingContext(temp_mcap_file)

        assert isinstance(context.event_queue, Queue), "Event queue should be a Queue instance"
        assert context.mcap_location == temp_mcap_file, f"MCAP location should be {temp_mcap_file}"
        assert context.event_queue.empty(), "Event queue should be empty initially"

    def test_enqueue_event(self, temp_mcap_file):
        """Test event enqueueing."""
        context = RecordingContext(temp_mcap_file)

        mock_event = MagicMock()
        topic = "test_topic"
        expected_timestamp = 123456789

        with patch("time.time_ns", return_value=expected_timestamp):
            context.enqueue_event(mock_event, topic=topic)

        # Verify event was queued
        assert not context.event_queue.empty(), "Event queue should not be empty after enqueueing"
        assert context.event_queue.qsize() == 1, "Event queue should contain exactly one event"

        queued_topic, queued_event, timestamp = context.event_queue.get()

        assert queued_topic == topic, f"Expected topic '{topic}', got '{queued_topic}'"
        assert queued_event == mock_event, "Event object should match the enqueued event"
        assert timestamp == expected_timestamp, f"Expected timestamp {expected_timestamp}, got {timestamp}"

    def test_enqueue_multiple_events(self, temp_mcap_file):
        """Test enqueueing multiple events."""
        context = RecordingContext(temp_mcap_file)

        events = [
            (MagicMock(), "topic1"),
            (MagicMock(), "topic2"),
            (MagicMock(), "topic3"),
        ]

        for event, topic in events:
            context.enqueue_event(event, topic=topic)

        # Verify all events were queued in order
        assert context.event_queue.qsize() == 3

        for expected_event, expected_topic in events:
            queued_topic, queued_event, _ = context.event_queue.get()
            assert queued_topic == expected_topic
            assert queued_event == expected_event


class TestCheckResourcesHealth:
    """Test the check_resources_health function."""

    def test_all_resources_healthy(self):
        """Test health check when all resources are healthy."""
        resources = create_healthy_resources(3)
        unhealthy = check_resources_health(resources)

        assert unhealthy == []

        # Verify is_alive was called on all resources
        for resource, _ in resources:
            resource.is_alive.assert_called_once()

    def test_some_resources_unhealthy(self):
        """Test health check when some resources are unhealthy."""
        resources = create_mixed_health_resources()
        unhealthy = check_resources_health(resources)

        assert unhealthy == ["unhealthy_resource"]

    def test_all_resources_unhealthy(self):
        """Test health check when all resources are unhealthy."""
        resources = create_unhealthy_resources(2)
        unhealthy = check_resources_health(resources)

        assert set(unhealthy) == {"failing_resource_0", "failing_resource_1"}

    def test_empty_resources_list(self):
        """Test health check with empty resources list."""
        unhealthy = check_resources_health([])
        assert unhealthy == []

    def test_resource_is_alive_exception(self):
        """Test health check when is_alive raises an exception."""
        resource = MagicMock()
        resource.is_alive.side_effect = Exception("Connection lost")

        resources = [(resource, "failing_resource")]

        # Should treat exception as unhealthy
        with pytest.raises(Exception):
            check_resources_health(resources)


class TestEnsureOutputFilesReady:
    """Test the ensure_output_files_ready function."""

    def test_new_file_in_existing_directory(self, tmp_path):
        """Test creating new file in existing directory."""
        file_path = tmp_path / "new_recording"
        result = ensure_output_files_ready(file_path)

        expected = file_path.with_suffix(".mcap")
        assert result == expected, f"Expected {expected}, got {result}"
        assert result.parent.exists(), f"Parent directory {result.parent} should exist"

    def test_new_file_creates_directory(self, tmp_path):
        """Test creating new file creates parent directory."""
        file_path = tmp_path / "subdir" / "new_recording"

        with patch("owa.ocap.recorder.logger") as mock_logger:
            result = ensure_output_files_ready(file_path)

        expected = file_path.with_suffix(".mcap")
        assert result == expected, f"Expected {expected}, got {result}"
        assert result.parent.exists(), f"Parent directory {result.parent} should exist"
        # Check that a warning was called about directory creation
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "directory" in warning_call.lower(), f"Warning should mention directory creation: {warning_call}"
        assert str(result.parent) in warning_call, f"Warning should mention the created directory path: {warning_call}"

    def test_existing_file_user_confirms_delete(self, tmp_path):
        """Test handling existing file when user confirms deletion."""
        base_file = tmp_path / "test_recording"
        mcap_file = base_file.with_suffix(".mcap")
        mkv_file = base_file.with_suffix(".mkv")

        # Create existing files
        mcap_file.touch()
        mkv_file.touch()

        assert mcap_file.exists(), "MCAP file should exist before test"
        assert mkv_file.exists(), "MKV file should exist before test"

        with (
            patch("typer.confirm", return_value=True) as mock_confirm,
            patch("owa.ocap.recorder.logger") as mock_logger,
        ):
            result = ensure_output_files_ready(base_file)

        assert result == mcap_file, f"Expected {mcap_file}, got {result}"
        assert not mcap_file.exists(), "MCAP file should be deleted"
        assert not mkv_file.exists(), "MKV file should be deleted"
        mock_confirm.assert_called_once()
        mock_logger.warning.assert_called_once()

    def test_existing_file_user_cancels(self, tmp_path):
        """Test handling existing file when user cancels."""
        base_file = tmp_path / "test_recording"
        mcap_file = base_file.with_suffix(".mcap")
        mcap_file.touch()

        assert mcap_file.exists(), "MCAP file should exist before test"

        with patch("typer.confirm", return_value=False) as mock_confirm:
            with pytest.raises(typer.Abort, match=""):
                ensure_output_files_ready(base_file)

        mock_confirm.assert_called_once()
        assert mcap_file.exists(), "MCAP file should still exist after cancellation"

    def test_existing_mcap_only(self, tmp_path):
        """Test handling when only .mcap file exists."""
        base_file = tmp_path / "test_recording"
        mcap_file = base_file.with_suffix(".mcap")
        mcap_file.touch()

        assert mcap_file.exists(), "MCAP file should exist before test"

        with (
            patch("typer.confirm", return_value=True) as mock_confirm,
            patch("owa.ocap.recorder.logger") as mock_logger,
        ):
            result = ensure_output_files_ready(base_file)

        assert result == mcap_file, f"Expected {mcap_file}, got {result}"
        assert not mcap_file.exists(), "MCAP file should be deleted"
        mock_confirm.assert_called_once()
        mock_logger.warning.assert_called_once()

    def test_existing_mkv_only(self, tmp_path):
        """Test handling when only .mkv file exists."""
        base_file = tmp_path / "test_recording"
        mkv_file = base_file.with_suffix(".mkv")
        mkv_file.touch()

        assert mkv_file.exists(), "MKV file should exist before test"

        with (
            patch("typer.confirm", return_value=True) as mock_confirm,
            patch("owa.ocap.recorder.logger") as mock_logger,
        ):
            result = ensure_output_files_ready(base_file)

        expected_mcap = base_file.with_suffix(".mcap")
        assert result == expected_mcap, f"Expected {expected_mcap}, got {result}"
        assert not mkv_file.exists(), "MKV file should be deleted"
        mock_confirm.assert_called_once()
        mock_logger.warning.assert_called_once()


class TestCheckPlugin:
    """Test the check_plugin function."""

    def test_check_plugin_success(self):
        """Test successful plugin check."""
        mock_discovery = MagicMock()
        mock_discovery.get_plugin_info.return_value = (["desktop", "gst"], [])

        with patch("owa.ocap.recorder.get_plugin_discovery", return_value=mock_discovery):
            # Should not raise any exception
            check_plugin()

        mock_discovery.get_plugin_info.assert_called_once_with(["desktop", "gst"])

    def test_check_plugin_failure(self):
        """Test plugin check failure."""
        mock_discovery = MagicMock()
        mock_discovery.get_plugin_info.return_value = (["desktop"], ["gst"])

        with patch("owa.ocap.recorder.get_plugin_discovery", return_value=mock_discovery):
            with pytest.raises(AssertionError, match="Failed to load plugins"):
                check_plugin()

    def test_check_plugin_partial_failure(self):
        """Test plugin check with partial failure."""
        mock_discovery = MagicMock()
        mock_discovery.get_plugin_info.return_value = (["desktop"], ["gst"])

        with patch("owa.ocap.recorder.get_plugin_discovery", return_value=mock_discovery):
            with pytest.raises(AssertionError):
                check_plugin()

    def test_check_plugin_complete_failure(self):
        """Test plugin check with complete failure."""
        mock_discovery = MagicMock()
        mock_discovery.get_plugin_info.return_value = ([], ["desktop", "gst"])

        with patch("owa.ocap.recorder.get_plugin_discovery", return_value=mock_discovery):
            with pytest.raises(AssertionError):
                check_plugin()


class TestHealthCheckIntegration:
    """Integration tests for health checking functionality."""

    def test_health_check_workflow(self):
        """Test complete health check workflow."""
        # Create resources with mixed health
        healthy_resource = MagicMock()
        healthy_resource.is_alive.return_value = True

        unhealthy_resource = MagicMock()
        unhealthy_resource.is_alive.return_value = False

        resources = [
            (healthy_resource, "recorder"),
            (unhealthy_resource, "listener"),
        ]

        # Initial check - one unhealthy
        unhealthy = check_resources_health(resources)
        assert unhealthy == ["listener"]

        # Fix the unhealthy resource
        unhealthy_resource.is_alive.return_value = True

        # Check again - all healthy
        unhealthy = check_resources_health(resources)
        assert unhealthy == []

        # Break all resources
        healthy_resource.is_alive.return_value = False
        unhealthy_resource.is_alive.return_value = False

        # Check again - all unhealthy
        unhealthy = check_resources_health(resources)
        assert set(unhealthy) == {"recorder", "listener"}

    def test_resource_lifecycle_simulation(self):
        """Test simulating resource lifecycle."""
        resource = MagicMock()

        # Resource starts healthy
        resource.is_alive.return_value = True
        resources = [(resource, "test_resource")]

        assert check_resources_health(resources) == []

        # Resource becomes unhealthy
        resource.is_alive.return_value = False
        assert check_resources_health(resources) == ["test_resource"]

        # Resource recovers
        resource.is_alive.return_value = True
        assert check_resources_health(resources) == []
