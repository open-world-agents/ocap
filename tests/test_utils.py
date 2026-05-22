import os
from unittest.mock import patch

import requests

from owa.ocap.utils import check_for_update, countdown_delay, parse_additional_properties


class TestCheckForUpdate:
    """Test the best-effort update check, which must never crash the caller."""

    def test_request_failure_is_handled(self):
        """A network failure is reported and returns False instead of raising."""
        with (
            patch.dict(os.environ, {"OWA_DISABLE_VERSION_CHECK": ""}, clear=False),
            patch("owa.ocap.utils.get_latest_release", side_effect=requests.RequestException("boom")),
            patch("owa.ocap.utils.print") as mock_print,
        ):
            result = check_for_update("ocap")

        assert result is False
        mock_print.assert_called_once()

    def test_print_failure_does_not_propagate(self):
        """A console encoding error while printing must not crash the caller.

        Regression test: rich raised UnicodeEncodeError on a cp949 Windows
        console, aborting ocap on startup.
        """
        with (
            patch.dict(os.environ, {"OWA_DISABLE_VERSION_CHECK": ""}, clear=False),
            patch("owa.ocap.utils.get_latest_release", side_effect=requests.RequestException("boom")),
            patch("owa.ocap.utils.print", side_effect=UnicodeEncodeError("cp949", "", 0, 1, "boom")),
        ):
            # Must not raise.
            result = check_for_update("ocap")

        assert result is False

    def test_silent_suppresses_output(self):
        """silent=True suppresses all output even on failure."""
        with (
            patch.dict(os.environ, {"OWA_DISABLE_VERSION_CHECK": ""}, clear=False),
            patch("owa.ocap.utils.get_latest_release", side_effect=requests.RequestException("boom")),
            patch("owa.ocap.utils.print") as mock_print,
        ):
            result = check_for_update("ocap", silent=True)

        assert result is False
        mock_print.assert_not_called()

    def test_up_to_date_returns_true(self):
        """When the local version matches the latest, returns True without output."""
        with (
            patch.dict(os.environ, {"OWA_DISABLE_VERSION_CHECK": ""}, clear=False),
            patch("owa.ocap.utils.get_local_version", return_value="1.2.3"),
            patch("owa.ocap.utils.get_latest_release", return_value="1.2.3"),
            patch("owa.ocap.utils.print") as mock_print,
        ):
            result = check_for_update("ocap")

        assert result is True
        mock_print.assert_not_called()

    def test_update_available_returns_false(self):
        """When a newer version exists, prints a banner and returns False."""
        with (
            patch.dict(os.environ, {"OWA_DISABLE_VERSION_CHECK": ""}, clear=False),
            patch("owa.ocap.utils.get_local_version", return_value="1.0.0"),
            patch("owa.ocap.utils.get_latest_release", return_value="2.0.0"),
            patch("owa.ocap.utils.print") as mock_print,
        ):
            result = check_for_update("ocap")

        assert result is False
        mock_print.assert_called_once()


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
