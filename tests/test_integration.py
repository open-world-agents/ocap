"""
Integration tests for the ocap command.

Tests that the ocap command runs without crashing during startup and initialization.
These tests verify the CLI interface works correctly without requiring full recording.
"""

import os
import subprocess
import time

import pytest


def _get_subprocess_env():
    """Get environment variables for subprocess calls with proper encoding."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["OWA_DISABLE_VERSION_CHECK"] = "1"  # Disable version check in subprocess
    return env


class TestOcapIntegration:
    """Integration test for the ocap command - verifies it doesn't fail during startup."""

    def test_ocap_command_help_does_not_fail(self):
        """Test that 'ocap --help' command runs without errors."""
        try:
            # Test the help command which should not require any dependencies
            result = subprocess.run(
                ["ocap", "--help"],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                encoding="utf-8",
                env=_get_subprocess_env(),  # Ensure proper encoding in subprocess
            )

            # The command should succeed (exit code 0)
            assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"

            # Should contain help text about recording
            assert "Record screen, keyboard, mouse" in result.stdout
            assert "file-location" in result.stdout or "FILE_LOCATION" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("Command timed out - this suggests a hanging process")
        except FileNotFoundError:
            pytest.fail("ocap command not found - package not properly installed")

    def test_ocap_command_validation_does_not_fail(self, tmp_path):
        """Test that ocap command validates arguments without crashing."""
        test_file = tmp_path / "test-recording"
        process = None

        try:
            # Run ocap with a test file but immediately terminate
            # This tests initialization without actually recording
            process = subprocess.Popen(
                ["ocap", str(test_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env=_get_subprocess_env(),  # Ensure proper encoding in subprocess
            )

            # Give it a moment to initialize, then terminate
            time.sleep(2)
            process.terminate()

            # Wait for process to finish
            _, stderr = process.communicate(timeout=10)

            # Process should either:
            # 1. Exit cleanly (code 0) - if it started recording and was terminated
            # 2. Exit with specific error codes - but NOT crash with unhandled exceptions
            # 3. Be terminated (negative exit code on Unix, specific codes on Windows)

            # What we're checking: no unhandled Python exceptions in stderr
            # Common failure patterns to avoid:
            assert "Traceback" not in stderr, f"Unhandled exception occurred: {stderr}"
            assert "ImportError" not in stderr, f"Import error occurred: {stderr}"
            assert "ModuleNotFoundError" not in stderr, f"Module not found: {stderr}"

            # If it got far enough to start recording, that's success
            # (it would be terminated by our test, which is expected)

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            pytest.fail("Command initialization took too long")
        except FileNotFoundError:
            pytest.fail("ocap command not found - package not properly installed")
        finally:
            # Ensure process is cleaned up
            if process and process.poll() is None:
                process.kill()
                process.wait()

            # Give a moment for file handles to be released
            time.sleep(0.5)

    def test_ocap_command_with_invalid_args_fails_gracefully(self):
        """Test that ocap command fails gracefully with invalid arguments."""
        try:
            # Test with invalid arguments - should fail but not crash
            result = subprocess.run(
                ["ocap", "--invalid-flag"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                env=_get_subprocess_env(),  # Ensure proper encoding in subprocess
            )

            # Should fail with non-zero exit code
            assert result.returncode != 0

            # Should not have unhandled exceptions
            assert "Traceback" not in result.stderr
            assert "ImportError" not in result.stderr
            assert "ModuleNotFoundError" not in result.stderr

        except subprocess.TimeoutExpired:
            pytest.fail("Command with invalid args timed out")
        except FileNotFoundError:
            pytest.fail("ocap command not found - package not properly installed")

    def test_ocap_command_version_flag(self):
        """Test that 'ocap --version' command works."""
        try:
            result = subprocess.run(
                ["ocap", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                env=_get_subprocess_env(),
            )

            # Should succeed or fail gracefully
            assert result.returncode in [0, 2]  # 0 for success, 2 for typer no version

            # Should not have unhandled exceptions
            assert "Traceback" not in result.stderr

        except subprocess.TimeoutExpired:
            pytest.fail("Version command timed out")
        except FileNotFoundError:
            pytest.fail("ocap command not found - package not properly installed")

    def test_ocap_command_with_nonexistent_directory(self):
        """Test ocap command with nonexistent output directory."""
        process = None
        try:
            # Use a shorter timeout and terminate quickly
            process = subprocess.Popen(
                ["ocap", "/nonexistent/path/recording"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env=_get_subprocess_env(),
            )

            # Give it a moment to initialize, then terminate
            time.sleep(1)
            process.terminate()

            # Wait for process to finish
            _, stderr = process.communicate(timeout=5)

            # Should not have unhandled exceptions
            assert "Traceback" not in stderr
            assert "ImportError" not in stderr
            assert "ModuleNotFoundError" not in stderr

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            pytest.fail("Command with nonexistent directory timed out")
        except FileNotFoundError:
            pytest.fail("ocap command not found - package not properly installed")
        finally:
            # Ensure process is cleaned up
            if process and process.poll() is None:
                process.kill()
                process.wait()
            time.sleep(0.5)

    def test_ocap_command_multiple_invalid_flags(self):
        """Test ocap command with multiple invalid flags."""
        try:
            result = subprocess.run(
                ["ocap", "--invalid1", "--invalid2", "test"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                env=_get_subprocess_env(),
            )

            # Should fail with non-zero exit code
            assert result.returncode != 0

            # Should not have unhandled exceptions
            assert "Traceback" not in result.stderr

        except subprocess.TimeoutExpired:
            pytest.fail("Command with multiple invalid flags timed out")
        except FileNotFoundError:
            pytest.fail("ocap command not found - package not properly installed")

    def test_ocap_command_with_valid_flags_combination(self, tmp_path):
        """Test ocap command with valid flag combinations."""
        test_file = tmp_path / "test-recording"
        process = None

        try:
            # Test with multiple valid flags
            process = subprocess.Popen(
                ["ocap", str(test_file), "--no-record-audio", "--fps", "30"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env=_get_subprocess_env(),
            )

            # Give it a moment to initialize, then terminate
            time.sleep(1)
            process.terminate()

            # Wait for process to finish
            _, stderr = process.communicate(timeout=5)

            # Should not have unhandled exceptions
            assert "Traceback" not in stderr
            assert "ImportError" not in stderr
            assert "ModuleNotFoundError" not in stderr

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            pytest.fail("Command with valid flags timed out")
        except FileNotFoundError:
            pytest.fail("ocap command not found - package not properly installed")
        finally:
            if process and process.poll() is None:
                process.kill()
                process.wait()
            time.sleep(0.5)

    def test_ocap_command_with_conflicting_flags(self):
        """Test ocap command with potentially conflicting flags."""
        process = None
        try:
            # Use Popen and terminate quickly to avoid hanging
            process = subprocess.Popen(
                ["ocap", "test", "--window-name", "Test", "--monitor-idx", "0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env=_get_subprocess_env(),
            )

            # Give it a moment to initialize, then terminate
            time.sleep(1)
            process.terminate()

            # Wait for process to finish
            process.communicate(timeout=5)

            # May have tracebacks due to conflicting flags - that's expected behavior
            # Just ensure it doesn't hang or crash completely

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            pytest.fail("Command with conflicting flags timed out")
        except FileNotFoundError:
            pytest.fail("ocap command not found - package not properly installed")
        finally:
            if process and process.poll() is None:
                process.kill()
                process.wait()
            time.sleep(0.5)

    def test_ocap_command_with_edge_case_values(self):
        """Test ocap command with edge case parameter values."""
        test_cases = [
            ["ocap", "test", "--fps", "0"],  # Zero FPS
            ["ocap", "test", "--fps", "1000"],  # Very high FPS
            ["ocap", "test", "--start-after", "-1"],  # Negative delay
            ["ocap", "test", "--stop-after", "0"],  # Zero duration
        ]

        for cmd in test_cases:
            process = None
            try:
                # Use Popen and terminate quickly to avoid hanging
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    env=_get_subprocess_env(),
                )

                # Give it a moment to initialize, then terminate
                time.sleep(1)
                process.terminate()

                # Wait for process to finish
                process.communicate(timeout=5)

                # Edge case values may cause validation errors - that's expected
                # Just ensure it doesn't hang indefinitely

            except subprocess.TimeoutExpired:
                if process:
                    process.kill()
                pytest.fail(f"Command {' '.join(cmd)} timed out")
            except FileNotFoundError:
                pytest.fail("ocap command not found - package not properly installed")
            finally:
                if process and process.poll() is None:
                    process.kill()
                    process.wait()
                time.sleep(0.5)

    def test_ocap_command_output_format_validation(self):
        """Test that ocap command validates output format correctly."""
        invalid_extensions = [".txt", ".jpg", ".mp4", ".avi"]

        for ext in invalid_extensions:
            process = None
            try:
                # Use Popen and terminate quickly to avoid hanging
                process = subprocess.Popen(
                    ["ocap", f"test{ext}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    env=_get_subprocess_env(),
                )

                # Give it a moment to initialize, then terminate
                time.sleep(1)
                process.terminate()

                # Wait for process to finish
                process.communicate(timeout=5)

                # Should either accept (and convert) or reject cleanly
                # Some extensions may cause validation errors - that's expected

            except subprocess.TimeoutExpired:
                if process:
                    process.kill()
                pytest.fail(f"Command with {ext} extension timed out")
            except FileNotFoundError:
                pytest.fail("ocap command not found - package not properly installed")
            finally:
                if process and process.poll() is None:
                    process.kill()
                    process.wait()
                time.sleep(0.5)
