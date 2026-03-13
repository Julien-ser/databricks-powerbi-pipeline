"""
Unit tests for utils module.
"""

import json
import logging
import tempfile
from pathlib import Path

import pytest

from src.utils import ensure_directory, load_config, setup_logging, get_project_root


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_creates_new_directory(self):
        """Test that a new directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_dir"
            result = ensure_directory(str(test_dir))
            assert result.exists()
            assert result.is_dir()

    def test_existing_directory_does_not_fail(self):
        """Test that existing directory doesn't raise error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_directory(tmpdir)
            assert result.exists()


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_json_config(self):
        """Test loading a JSON config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"test": "value", "number": 42}, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config["test"] == "value"
            assert config["number"] == 42
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_config(self):
        """Test loading a YAML config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test: value\nnumber: 42\n")
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config["test"] == "value"
            assert config["number"] == 42
        finally:
            Path(temp_path).unlink()

    def test_missing_file_raises_error(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/file.json")

    def test_unsupported_format_raises_error(self):
        """Test that unsupported format raises ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("some content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()


class TestGetProjectRoot:
    """Tests for get_project_root function."""

    def test_returns_path(self):
        """Test that function returns a Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_contains_expected_directories(self):
        """Test that project root contains expected directories."""
        root = get_project_root()
        expected_dirs = ["src", "config", "data", "notebooks", "tests", "docs"]
        for dir_name in expected_dirs:
            assert (root / dir_name).exists() or (root / dir_name).is_dir()


class TestSetupLogging:
    """Tests for setup_logging function."""

    def _reset_logging(self):
        """Reset logging configuration to clean state."""
        logging.root.manager.loggerDict.clear()
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            handler.close()
        logging.root.setLevel(logging.WARNING)

    def test_setup_logging_with_default_level(self, tmp_path):
        """Test that setup_logging works with default INFO level."""
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            ensure_directory("logs")
            self._reset_logging()
            setup_logging()
            root_logger = logging.getLogger()
            assert root_logger.level == logging.INFO
        finally:
            os.chdir(old_cwd)
            self._reset_logging()

    def test_setup_logging_with_custom_level(self, tmp_path):
        """Test that setup_logging works with custom log level."""
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            ensure_directory("logs")
            self._reset_logging()
            setup_logging("DEBUG")
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG
        finally:
            os.chdir(old_cwd)
            self._reset_logging()

    def test_setup_logging_creates_handlers(self, tmp_path):
        """Test that setup_logging creates expected handlers."""
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            ensure_directory("logs")
            self._reset_logging()
            setup_logging()
            root_logger = logging.getLogger()
            # Should have at least 2 handlers (StreamHandler and FileHandler)
            assert len(root_logger.handlers) >= 2
            # Check for FileHandler
            file_handlers = [
                h for h in root_logger.handlers if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) == 1
        finally:
            os.chdir(old_cwd)
            self._reset_logging()

    def test_setup_logging_creates_handlers(self, tmp_path):
        """Test that setup_logging creates expected handlers."""
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            ensure_directory("logs")
            setup_logging()
            root_logger = logging.getLogger()
            # Should have at least 2 handlers (StreamHandler and FileHandler)
            assert len(root_logger.handlers) >= 2
            # Check for FileHandler
            file_handlers = [
                h for h in root_logger.handlers if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) == 1
        finally:
            os.chdir(old_cwd)
            logging.root.manager.loggerDict.clear()
            logging.basicConfig(level=logging.WARNING, force=True)
