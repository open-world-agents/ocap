"""
Tests for utility functions in owa.ocap.utils module.
"""

import os
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from owa.ocap.utils import (
    check_for_update,
    countdown_delay,
    get_latest_release,
    get_local_version,
    parse_additional_properties,
)


class TestCountdownDelay:
    """Test the countdown_delay function."""

    def test_countdown_delay_zero_seconds(self):
        """Test that no delay occurs for zero seconds."""
        start_time = time.time()
        countdown_delay(0)
        elapsed = time.time() - start_time
        assert elapsed < 0.1  # Should be nearly instant

    def test_countdown_delay_negative_seconds(self):
        """Test that no delay occurs for negative seconds."""
        start_time = time.time()
        countdown_delay(-1.0)
        elapsed = time.time() - start_time
        assert elapsed < 0.1  # Should be nearly instant

    def test_countdown_delay_short_duration(self):
        """Test countdown for short duration (< 3 seconds)."""
        with patch("owa.ocap.utils.logger") as mock_logger, patch("time.sleep") as mock_sleep:
            countdown_delay(1.5)

            # Should log start message and call sleep once
            mock_logger.info.assert_any_call("⏱️ Recording will start in 1.5 seconds...")
            mock_logger.info.assert_any_call("🎬 Recording started!")
            mock_sleep.assert_called_once_with(1.5)

    def test_countdown_delay_long_duration(self):
        """Test countdown for long duration (>= 3 seconds)."""
        with patch("owa.ocap.utils.logger") as mock_logger, patch("time.sleep") as mock_sleep:
            countdown_delay(3.5)

            # Should log start message and countdown messages
            mock_logger.info.assert_any_call("⏱️ Recording will start in 3.5 seconds...")
            mock_logger.info.assert_any_call("Starting in 3...")
            mock_logger.info.assert_any_call("Starting in 2...")
            mock_logger.info.assert_any_call("Starting in 1...")
            mock_logger.info.assert_any_call("🎬 Recording started!")

            # Should call sleep for each second plus remaining fractional part
            expected_calls = [
                ((1,), {}),  # Sleep for each countdown second
                ((1,), {}),
                ((1,), {}),
                ((0.5,), {}),  # Sleep for remaining fractional part
            ]
            assert mock_sleep.call_count == 4
            mock_sleep.assert_has_calls(expected_calls, any_order=False)

    def test_countdown_delay_exact_integer_duration(self):
        """Test countdown for exact integer duration."""
        with patch("owa.ocap.utils.logger") as mock_logger, patch("time.sleep") as mock_sleep:
            countdown_delay(3.0)

            # Should log countdown messages
            mock_logger.info.assert_any_call("⏱️ Recording will start in 3.0 seconds...")
            mock_logger.info.assert_any_call("Starting in 3...")
            mock_logger.info.assert_any_call("Starting in 2...")
            mock_logger.info.assert_any_call("Starting in 1...")
            mock_logger.info.assert_any_call("🎬 Recording started!")

            # Should call sleep for each second only (no fractional part)
            assert mock_sleep.call_count == 3


class TestParseAdditionalProperties:
    """Test the parse_additional_properties function."""

    def test_parse_none_args(self):
        """Test parsing None additional arguments."""
        result = parse_additional_properties(None)
        assert result == {}, "None input should return empty dictionary"

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        # Empty string will cause split to return [''] which will fail
        with pytest.raises(ValueError, match=""):
            parse_additional_properties("")

    def test_parse_single_property(self):
        """Test parsing a single property."""
        input_str = "key=value"
        result = parse_additional_properties(input_str)
        expected = {"key": "value"}
        assert result == expected, f"Single property '{input_str}' should parse to {expected}"

    def test_parse_multiple_properties(self):
        """Test parsing multiple properties."""
        input_str = "key1=value1,key2=value2"
        result = parse_additional_properties(input_str)
        assert result == {"key1": "value1", "key2": "value2"}

    def test_parse_property_with_equals_in_value(self):
        """Test parsing property where value contains equals sign."""
        # This will fail with current implementation - it's a limitation
        with pytest.raises(ValueError):
            parse_additional_properties("url=http://example.com?param=value")

    def test_parse_property_with_spaces(self):
        """Test parsing property with spaces."""
        result = parse_additional_properties("key=value with spaces")
        assert result == {"key": "value with spaces"}

    def test_parse_invalid_property_format(self):
        """Test parsing invalid property format (no equals sign)."""
        with pytest.raises(ValueError):
            parse_additional_properties("invalid_property")

    def test_parse_empty_value(self):
        """Test parsing property with empty value."""
        result = parse_additional_properties("key=")
        assert result == {"key": ""}

    def test_parse_whitespace_only_string(self):
        """Test parsing string with only whitespace."""
        with pytest.raises(ValueError):
            parse_additional_properties("   ")

    def test_parse_multiple_equals_in_key_value(self):
        """Test parsing with multiple equals signs (limitation of current implementation)."""
        # Current implementation will fail with multiple equals
        with pytest.raises(ValueError):
            parse_additional_properties("key=value=extra")

    def test_parse_comma_separated_with_empty_parts(self):
        """Test parsing comma-separated string with empty parts."""
        with pytest.raises(ValueError):
            parse_additional_properties("key1=value1,,key2=value2")

    def test_parse_trailing_comma(self):
        """Test parsing string with trailing comma."""
        with pytest.raises(ValueError):
            parse_additional_properties("key1=value1,")

    def test_parse_leading_comma(self):
        """Test parsing string with leading comma."""
        with pytest.raises(ValueError):
            parse_additional_properties(",key1=value1")


class TestVersionFunctions:
    """Test version-related utility functions."""

    def test_get_local_version_default_package(self):
        """Test getting local version for default package."""
        with patch("importlib.metadata.version") as mock_version:
            mock_version.return_value = "1.2.3"
            version = get_local_version()
            assert version == "1.2.3"
            mock_version.assert_called_once_with("ocap")

    def test_get_local_version_custom_package(self):
        """Test getting local version for custom package."""
        with patch("importlib.metadata.version") as mock_version:
            mock_version.return_value = "2.0.0"
            version = get_local_version("custom-package")
            assert version == "2.0.0"
            mock_version.assert_called_once_with("custom-package")

    def test_get_local_version_package_not_found(self):
        """Test getting local version when package is not found."""
        with patch("importlib.metadata.version") as mock_version:
            mock_version.side_effect = Exception("Package not found")
            version = get_local_version("nonexistent-package")
            assert version == "unknown"

    def test_get_latest_release_success(self):
        """Test successful retrieval of latest release."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"tag_name": "v1.5.0"}

        with patch("requests.get", return_value=mock_response) as mock_get, patch.dict(os.environ, {}, clear=False):
            # Ensure OWA_DISABLE_VERSION_CHECK is not set
            os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
            version = get_latest_release()
            assert version == "1.5.0"  # Should strip 'v' prefix
            mock_get.assert_called_once()

    def test_get_latest_release_disabled_by_env(self):
        """Test that version check is disabled by environment variable."""
        with (
            patch("owa.ocap.utils.get_local_version", return_value="1.0.0") as mock_local,
            patch.dict(os.environ, {"OWA_DISABLE_VERSION_CHECK": "1"}),
        ):
            version = get_latest_release()
            assert version == "1.0.0"
            mock_local.assert_called_once()

    def test_get_latest_release_network_error(self):
        """Test handling of network errors."""
        with (
            patch("requests.get", side_effect=requests.RequestException("Network error")),
            patch.dict(os.environ, {}, clear=False),
        ):
            # Ensure OWA_DISABLE_VERSION_CHECK is not set
            os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
            with pytest.raises(requests.RequestException):
                get_latest_release()

    def test_get_latest_release_tag_without_v_prefix(self):
        """Test handling of tag without 'v' prefix."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"tag_name": "1.5.0"}

        with patch("requests.get", return_value=mock_response), patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
            version = get_latest_release()
            assert version == "1.5.0"

    def test_get_latest_release_custom_url(self):
        """Test with custom URL."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"tag_name": "v2.0.0"}

        with patch("requests.get", return_value=mock_response) as mock_get, patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
            version = get_latest_release("https://api.github.com/repos/custom/repo/releases/latest")
            assert version == "2.0.0"
            mock_get.assert_called_once_with("https://api.github.com/repos/custom/repo/releases/latest", timeout=5)

    def test_get_local_version_with_different_python_versions(self):
        """Test get_local_version with different Python version paths."""
        # Test the importlib.metadata path (Python 3.8+)
        with (
            patch("sys.version_info", (3, 8, 0)),
            patch("importlib.metadata.version", return_value="1.0.0") as mock_version,
        ):
            version = get_local_version("test-package")
            assert version == "1.0.0"
            mock_version.assert_called_once_with("test-package")

    def test_get_local_version_exception_handling(self):
        """Test various exception types in get_local_version."""
        with patch("importlib.metadata.version", side_effect=ImportError("Module not found")):
            version = get_local_version("test-package")
            assert version == "unknown"

        with patch("importlib.metadata.version", side_effect=RuntimeError("Runtime error")):
            version = get_local_version("test-package")
            assert version == "unknown"


class TestCheckForUpdate:
    """Test the check_for_update function."""

    def test_check_for_update_up_to_date(self):
        """Test when local version is up to date."""
        with (
            patch("owa.ocap.utils.get_local_version", return_value="1.0.0"),
            patch("owa.ocap.utils.get_latest_release", return_value="1.0.0"),
            patch.dict(os.environ, {}, clear=False),
        ):
            # Ensure OWA_DISABLE_VERSION_CHECK is not set
            os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
            result = check_for_update(silent=True)
            assert result is True

    def test_check_for_update_outdated(self):
        """Test when local version is outdated."""
        with (
            patch("owa.ocap.utils.get_local_version", return_value="1.0.0"),
            patch("owa.ocap.utils.get_latest_release", return_value="1.1.0"),
            patch.dict(os.environ, {}, clear=False),
        ):
            # Ensure OWA_DISABLE_VERSION_CHECK is not set
            os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
            result = check_for_update(silent=True)
            assert result is False

    def test_check_for_update_disabled_by_env(self):
        """Test that update check is disabled by environment variable."""
        with patch.dict(os.environ, {"OWA_DISABLE_VERSION_CHECK": "1"}):
            result = check_for_update(silent=True)
            assert result is True

    def test_check_for_update_network_timeout(self):
        """Test handling of network timeout."""
        with (
            patch("owa.ocap.utils.get_local_version", return_value="1.0.0"),
            patch("owa.ocap.utils.get_latest_release", side_effect=requests.Timeout("Timeout")),
            patch.dict(os.environ, {}, clear=False),
        ):
            # Ensure OWA_DISABLE_VERSION_CHECK is not set
            os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
            result = check_for_update(silent=True)
            assert result is False  # Should return False on timeout (as per implementation)

    def test_check_for_update_with_output(self, capsys):
        """Test update check with console output."""
        with (
            patch("owa.ocap.utils.get_local_version", return_value="1.0.0"),
            patch("owa.ocap.utils.get_latest_release", return_value="1.1.0"),
            patch.dict(os.environ, {}, clear=False),
        ):
            # Ensure OWA_DISABLE_VERSION_CHECK is not set
            os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
            result = check_for_update(silent=False)
            assert result is False

            captured = capsys.readouterr()
            assert "An update is available" in captured.out
            assert "1.0.0" in captured.out
            assert "1.1.0" in captured.out

    def test_check_for_update_request_exception(self):
        """Test handling of general request exceptions."""
        with (
            patch("owa.ocap.utils.get_local_version", return_value="1.0.0"),
            patch("owa.ocap.utils.get_latest_release", side_effect=requests.RequestException("Connection error")),
            patch.dict(os.environ, {}, clear=False),
        ):
            os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
            result = check_for_update(silent=True)
            assert result is False

    def test_check_for_update_general_exception(self):
        """Test handling of general exceptions."""
        with (
            patch("owa.ocap.utils.get_local_version", return_value="1.0.0"),
            patch("owa.ocap.utils.get_latest_release", side_effect=Exception("Unexpected error")),
            patch.dict(os.environ, {}, clear=False),
        ):
            os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
            result = check_for_update(silent=True)
            assert result is False

    def test_check_for_update_custom_package_and_url(self):
        """Test with custom package name and URL."""
        with (
            patch("owa.ocap.utils.get_local_version", return_value="1.0.0"),
            patch("owa.ocap.utils.get_latest_release", return_value="1.1.0"),
            patch.dict(os.environ, {}, clear=False),
        ):
            os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
            result = check_for_update(
                package_name="custom-package",
                url="https://api.github.com/repos/custom/repo/releases/latest",
                silent=True,
            )
            assert result is False

    def test_check_for_update_version_comparison_edge_cases(self):
        """Test version comparison edge cases."""
        test_cases = [
            ("1.0.0", "1.0.1", False),  # Patch update
            ("1.0.0", "1.1.0", False),  # Minor update
            ("1.0.0", "2.0.0", False),  # Major update
            ("1.0.0", "1.0.0", True),  # Same version
            ("1.1.0", "1.0.0", True),  # Local newer
            ("2.0.0", "1.9.9", True),  # Local much newer
        ]

        for local_ver, latest_ver, expected in test_cases:
            with (
                patch("owa.ocap.utils.get_local_version", return_value=local_ver),
                patch("owa.ocap.utils.get_latest_release", return_value=latest_ver),
                patch.dict(os.environ, {}, clear=False),
            ):
                os.environ.pop("OWA_DISABLE_VERSION_CHECK", None)
                result = check_for_update(silent=True)
                assert result is expected, f"Failed for {local_ver} vs {latest_ver}"
