import os
import subprocess


class TestCLI:
    """Test CLI functionality."""

    def _get_env(self):
        """Get environment with version check disabled."""
        env = os.environ.copy()
        env["OWA_DISABLE_VERSION_CHECK"] = "1"
        return env

    def test_help_command(self):
        """Test that help command works."""
        result = subprocess.run(["ocap", "--help"], capture_output=True, text=True, timeout=10, env=self._get_env())

        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_version_command(self):
        """Test that version flag doesn't exist (expected behavior)."""
        result = subprocess.run(["ocap", "--version"], capture_output=True, text=True, timeout=10, env=self._get_env())

        # --version flag doesn't exist, so it should fail
        assert result.returncode != 0
        assert "No such option: --version" in result.stderr

    def test_invalid_command(self):
        """Test invalid command fails gracefully."""
        result = subprocess.run(
            ["ocap", "--invalid-flag"], capture_output=True, text=True, timeout=10, env=self._get_env()
        )

        assert result.returncode != 0
