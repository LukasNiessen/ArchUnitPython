"""Tests for the logging system."""

import os
import shutil
from pathlib import Path

from archunitpy.common.logging.types import LoggingOptions
from archunitpy.common.util.logger import CheckLogger


class TestCheckLogger:
    def test_no_logging_when_disabled(self):
        logger = CheckLogger()
        # Should not raise
        logger.info(None, "test")
        logger.info(LoggingOptions(enabled=False), "test")
        logger.close()

    def test_logging_when_enabled(self, caplog):
        import logging

        logger = CheckLogger()
        logger._logger.propagate = True
        opts = LoggingOptions(enabled=True, level="debug")
        with caplog.at_level(logging.DEBUG, logger="archunitpy"):
            logger.info(opts, "hello world")
        assert "hello world" in caplog.text
        logger.close()

    def test_level_filtering(self, caplog):
        import logging

        logger = CheckLogger()
        logger._logger.propagate = True
        opts = LoggingOptions(enabled=True, level="warn")
        with caplog.at_level(logging.DEBUG, logger="archunitpy"):
            logger.debug(opts, "debug msg")
            logger.info(opts, "info msg")
            logger.warn(opts, "warn msg")
            logger.error(opts, "error msg")
        assert "debug msg" not in caplog.text
        assert "info msg" not in caplog.text
        assert "warn msg" in caplog.text
        assert "error msg" in caplog.text
        logger.close()

    def test_start_and_end_check(self, caplog):
        import logging

        logger = CheckLogger()
        logger._logger.propagate = True
        opts = LoggingOptions(enabled=True, level="info")
        with caplog.at_level(logging.INFO, logger="archunitpy"):
            logger.start_check("cycle-check", opts)
            logger.end_check("cycle-check", 3, opts)
        assert "Starting check: cycle-check" in caplog.text
        assert "3 violation(s)" in caplog.text
        logger.close()

    def test_file_logging(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        logger = CheckLogger()
        opts = LoggingOptions(enabled=True, level="info", log_file=True)
        logger.info(opts, "file log test")
        logger.close()

        log_dir = tmp_path / "logs"
        assert log_dir.exists()
        log_files = list(log_dir.glob("archunit-*.log"))
        assert len(log_files) == 1
        content = log_files[0].read_text()
        assert "file log test" in content
