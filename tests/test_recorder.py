from queue import Queue
from unittest.mock import MagicMock, patch

import pytest

from owa.ocap.recorder import (
    RecordingContext,
    check_resources_health,
    ensure_output_files_ready,
)


class TestRecordingContext:
    """Test core recording functionality."""

    def test_basic_functionality(self, temp_mcap_file):
        """Test RecordingContext basic operations."""
        context = RecordingContext(temp_mcap_file)

        # Test initialization
        assert isinstance(context.event_queue, Queue)
        assert context.mcap_location == temp_mcap_file
        assert context.event_queue.empty()

        # Test event enqueuing
        mock_event = MagicMock()
        context.enqueue_event(mock_event, topic="test")
        assert context.event_queue.qsize() == 1


class TestResourceHealth:
    """Test resource health checking."""

    def test_healthy_resources(self):
        """Test with all healthy resources."""
        resources = []
        for i in range(3):
            resource = MagicMock()
            resource.is_alive.return_value = True
            resources.append((resource, f"resource_{i}"))

        result = check_resources_health(resources)
        assert result == []

    def test_unhealthy_resources(self):
        """Test with some unhealthy resources."""
        healthy = MagicMock()
        healthy.is_alive.return_value = True

        unhealthy = MagicMock()
        unhealthy.is_alive.return_value = False

        resources = [(healthy, "good"), (unhealthy, "bad")]
        result = check_resources_health(resources)
        assert result == ["bad"]

    def test_empty_resources(self):
        """Test with no resources."""
        assert check_resources_health([]) == []


class TestFileHandling:
    """Test output file management."""

    def test_new_file(self, tmp_path):
        """Test creating new output file."""
        file_path = tmp_path / "recording"
        result = ensure_output_files_ready(file_path)

        expected = file_path.with_suffix(".mcap")
        assert result == expected

    def test_existing_file_confirmed(self, tmp_path):
        """Test overwriting existing file when confirmed."""
        file_path = tmp_path / "recording"
        mcap_file = file_path.with_suffix(".mcap")
        mcap_file.touch()

        with patch("typer.confirm", return_value=True):
            result = ensure_output_files_ready(file_path)

        assert result == mcap_file
        assert not mcap_file.exists()

    def test_existing_file_cancelled(self, tmp_path):
        """Test cancelling when file exists."""
        import typer

        file_path = tmp_path / "recording"
        mcap_file = file_path.with_suffix(".mcap")
        mcap_file.touch()

        with patch("typer.confirm", return_value=False):
            with pytest.raises(typer.Abort):
                ensure_output_files_ready(file_path)
