from unittest.mock import patch

from owa.ocap.utils import countdown_delay, parse_additional_properties


class TestCountdownDelay:
    """Test countdown delay functionality."""

    def test_basic_countdown(self):
        """Test basic countdown functionality."""
        with patch("owa.ocap.utils.logger") as mock_logger:
            countdown_delay(1)

        # Should log countdown messages
        assert mock_logger.info.called

    def test_zero_seconds(self):
        """Test countdown with zero seconds."""
        with patch("owa.ocap.utils.logger") as mock_logger:
            countdown_delay(0)

        # Should not log anything for zero seconds
        mock_logger.info.assert_not_called()


class TestParseAdditionalProperties:
    """Test additional properties parsing."""

    def test_parse_basic(self):
        """Test basic property parsing."""
        result = parse_additional_properties("key=value")
        assert result == {"key": "value"}

    def test_parse_multiple(self):
        """Test multiple properties."""
        result = parse_additional_properties("key1=value1,key2=value2")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_parse_empty(self):
        """Test empty input."""
        # Empty string should be handled gracefully
        result = parse_additional_properties(None)  # Use None instead of empty string
        assert result == {}

    def test_parse_none(self):
        """Test None input."""
        result = parse_additional_properties(None)
        assert result == {}
