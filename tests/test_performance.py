"""
Performance and edge case tests for the ocap package.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from owa.ocap.recorder import RecordingContext, check_resources_health
from owa.ocap.utils import countdown_delay


class TestPerformance:
    """Test performance characteristics of key functions."""

    def test_check_resources_health_performance_with_many_resources(self):
        """Test performance of health check with many resources."""
        # Create 1000 mock resources
        resources = []
        for i in range(1000):
            resource = MagicMock()
            resource.is_alive.return_value = True
            resources.append((resource, f"resource_{i}"))

        start_time = time.time()
        unhealthy = check_resources_health(resources)
        elapsed = time.time() - start_time

        assert unhealthy == []
        assert elapsed < 1.0  # Should complete within 1 second

        # Verify all resources were checked
        for resource, _ in resources:
            resource.is_alive.assert_called_once()

    def test_recording_context_queue_performance(self, temp_mcap_file):
        """Test performance of event queue operations."""
        context = RecordingContext(temp_mcap_file)

        # Enqueue many events
        num_events = 10000
        start_time = time.time()

        for i in range(num_events):
            mock_event = MagicMock()
            context.enqueue_event(mock_event, topic=f"topic_{i % 10}")

        enqueue_time = time.time() - start_time

        # Dequeue all events
        start_time = time.time()
        events = []
        while not context.event_queue.empty():
            events.append(context.event_queue.get())

        dequeue_time = time.time() - start_time

        assert len(events) == num_events
        assert enqueue_time < 5.0  # Should complete within 5 seconds
        assert dequeue_time < 5.0  # Should complete within 5 seconds

    def test_countdown_delay_precision(self):
        """Test precision of countdown delay timing."""
        delays = [0.1, 0.5, 1.0, 2.0]

        for delay in delays:
            with patch("owa.ocap.utils.logger"), patch("time.sleep") as mock_sleep:
                start_time = time.time()
                countdown_delay(delay)
                elapsed = time.time() - start_time

                # Should be very fast when mocked
                assert elapsed < 0.1

                if delay >= 3:
                    # Should call sleep multiple times for long delays
                    assert mock_sleep.call_count > 1
                else:
                    # Should call sleep once for short delays
                    mock_sleep.assert_called_once_with(delay)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_check_resources_health_with_slow_resources(self):
        """Test health check with resources that take time to respond."""

        def slow_is_alive():
            time.sleep(0.1)  # Simulate slow response
            return True

        resources = []
        for i in range(10):
            resource = MagicMock()
            resource.is_alive.side_effect = slow_is_alive
            resources.append((resource, f"slow_resource_{i}"))

        start_time = time.time()
        unhealthy = check_resources_health(resources)
        elapsed = time.time() - start_time

        assert unhealthy == []
        assert elapsed >= 1.0  # Should take at least 1 second (10 * 0.1)
        assert elapsed < 2.0  # But not too long

    def test_check_resources_health_with_intermittent_failures(self):
        """Test health check with resources that fail intermittently."""
        call_count = 0

        def intermittent_is_alive():
            nonlocal call_count
            call_count += 1
            return call_count % 2 == 0  # Fail every other call

        resource = MagicMock()
        resource.is_alive.side_effect = intermittent_is_alive
        resources = [(resource, "intermittent_resource")]

        # First call should show as unhealthy
        unhealthy = check_resources_health(resources)
        assert unhealthy == ["intermittent_resource"]

        # Second call should show as healthy
        unhealthy = check_resources_health(resources)
        assert unhealthy == []

    def test_recording_context_with_large_events(self, temp_mcap_file):
        """Test recording context with large event objects."""
        context = RecordingContext(temp_mcap_file)

        # Create a large mock event
        large_event = MagicMock()
        large_event.data = "x" * 1000000  # 1MB of data

        # Should handle large events without issues
        context.enqueue_event(large_event, topic="large_topic")

        assert not context.event_queue.empty(), "Queue should not be empty after adding large event"
        assert context.event_queue.qsize() == 1, "Queue should contain exactly one event"

        topic, event, timestamp = context.event_queue.get()
        assert topic == "large_topic", f"Expected topic 'large_topic', got '{topic}'"
        assert event == large_event, "Event should match the large event object"
        assert len(event.data) == 1000000, "Event data should be 1MB in size"

    def test_countdown_delay_with_extreme_values(self):
        """Test countdown delay with extreme values."""
        extreme_cases = [
            -1000.0,  # Very negative
            0.0,  # Zero
            0.001,  # Very small positive
            1000.0,  # Very large
        ]

        for delay in extreme_cases:
            with patch("owa.ocap.utils.logger"), patch("time.sleep") as mock_sleep:
                countdown_delay(delay)

                if delay <= 0:
                    # Should not sleep for non-positive delays
                    mock_sleep.assert_not_called()
                else:
                    # Should sleep for positive delays
                    mock_sleep.assert_called()

    def test_recording_context_queue_overflow_behavior(self, temp_mcap_file):
        """Test behavior when event queue grows very large."""
        context = RecordingContext(temp_mcap_file)

        # Fill queue with many events
        num_events = 100000
        for i in range(num_events):
            mock_event = MagicMock()
            mock_event.id = i  # Add identifier for verification
            context.enqueue_event(mock_event, topic="stress_test")

        # Queue should still be functional
        assert context.event_queue.qsize() == num_events, f"Expected {num_events} events in queue"

        # Should be able to retrieve events
        topic, event, timestamp = context.event_queue.get()
        assert topic == "stress_test", f"Expected topic 'stress_test', got '{topic}'"
        assert hasattr(event, "id"), "Event should have an id attribute"
        assert context.event_queue.qsize() == num_events - 1, (
            f"Queue should have {num_events - 1} events after getting one"
        )


class TestErrorConditions:
    """Test error conditions and exception handling."""

    def test_check_resources_health_with_exception_in_is_alive(self):
        """Test health check when is_alive raises exceptions."""

        def failing_is_alive():
            raise RuntimeError("Resource connection lost")

        resource = MagicMock()
        resource.is_alive.side_effect = failing_is_alive
        resources = [(resource, "failing_resource")]

        # Should propagate the exception
        with pytest.raises(RuntimeError, match="Resource connection lost"):
            check_resources_health(resources)

    def test_check_resources_health_with_mixed_exceptions(self):
        """Test health check with some resources raising exceptions."""
        healthy_resource = MagicMock()
        healthy_resource.is_alive.return_value = True

        failing_resource = MagicMock()
        failing_resource.is_alive.side_effect = Exception("Connection error")

        resources = [
            (healthy_resource, "healthy"),
            (failing_resource, "failing"),
        ]

        # Should raise exception from the failing resource
        with pytest.raises(Exception, match="Connection error"):
            check_resources_health(resources)

    def test_recording_context_with_invalid_topic(self, temp_mcap_file):
        """Test recording context with invalid topic types."""
        context = RecordingContext(temp_mcap_file)

        # Should handle various topic types
        invalid_topics = [None, 123, [], {}]

        for i, topic in enumerate(invalid_topics):
            # Create unique event for each topic
            unique_event = MagicMock()
            unique_event.test_id = i

            # Should not raise exception (topic is just stored)
            context.enqueue_event(unique_event, topic=topic)

            queued_topic, queued_event, timestamp = context.event_queue.get()
            assert queued_topic == topic, f"Expected topic {topic}, got {queued_topic}"
            assert queued_event == unique_event, f"Event should match for topic {topic}"
            assert hasattr(queued_event, "test_id"), "Event should have test_id attribute"
            assert queued_event.test_id == i, f"Event test_id should be {i}"


class TestBoundaryConditions:
    """Test boundary conditions and limits."""

    def test_check_resources_health_empty_list(self):
        """Test health check with empty resource list."""
        unhealthy = check_resources_health([])
        assert unhealthy == []

    def test_check_resources_health_single_resource(self):
        """Test health check with single resource."""
        resource = MagicMock()
        resource.is_alive.return_value = True
        resources = [(resource, "single_resource")]

        unhealthy = check_resources_health(resources)
        assert unhealthy == []

    def test_countdown_delay_boundary_values(self):
        """Test countdown delay at boundary values."""
        boundary_values = [2.999, 3.0, 3.001]

        for delay in boundary_values:
            with patch("owa.ocap.utils.logger") as mock_logger, patch("time.sleep") as mock_sleep:
                countdown_delay(delay)

                # All should log start message
                mock_logger.info.assert_any_call(f"⏱️ Recording will start in {delay} seconds...")
                mock_logger.info.assert_any_call("🎬 Recording started!")

                if delay >= 3.0:
                    # Should show countdown for >= 3 seconds
                    mock_logger.info.assert_any_call("Starting in 3...")
                    assert mock_sleep.call_count >= 3
                else:
                    # Should not show countdown for < 3 seconds
                    assert "Starting in" not in str(mock_logger.info.call_args_list)
                    mock_sleep.assert_called_once_with(delay)
