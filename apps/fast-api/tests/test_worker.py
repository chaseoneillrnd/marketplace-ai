"""Tests for the ARQ worker module."""

from __future__ import annotations

import asyncio
import os
import tempfile
import time

from skillhub.worker import aggregate_daily_metrics, clean_expired_exports, recalculate_trending


class TestWorker:
    """Tests for worker background job functions."""

    def test_aggregate_returns_ok(self) -> None:
        """aggregate_daily_metrics returns status ok."""
        result = asyncio.run(aggregate_daily_metrics({}))
        assert result["status"] == "ok"

    def test_recalculate_returns_ok(self) -> None:
        """recalculate_trending returns status ok."""
        result = asyncio.run(recalculate_trending({}))
        assert result["status"] == "ok"

    def test_clean_expired_exports_empty_dir(self) -> None:
        """clean_expired_exports with empty dir removes 0 files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["EXPORT_DIR"] = tmpdir
            try:
                result = asyncio.run(clean_expired_exports({}))
                assert result["removed"] == 0
            finally:
                del os.environ["EXPORT_DIR"]

    def test_clean_expired_exports_removes_old_files(self) -> None:
        """clean_expired_exports removes files older than 24h."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["EXPORT_DIR"] = tmpdir
            try:
                # Create an old file
                old_file = os.path.join(tmpdir, "old_export.csv")
                with open(old_file, "w") as f:
                    f.write("data")
                # Set mtime to 25 hours ago
                old_time = time.time() - 90000
                os.utime(old_file, (old_time, old_time))

                # Create a fresh file
                new_file = os.path.join(tmpdir, "new_export.csv")
                with open(new_file, "w") as f:
                    f.write("data")

                result = asyncio.run(clean_expired_exports({}))
                assert result["removed"] == 1
                assert not os.path.exists(old_file)
                assert os.path.exists(new_file)
            finally:
                del os.environ["EXPORT_DIR"]

    def test_clean_expired_exports_nonexistent_dir(self) -> None:
        """clean_expired_exports with missing dir returns 0."""
        os.environ["EXPORT_DIR"] = "/tmp/nonexistent-skillhub-test-dir-xyz"
        try:
            result = asyncio.run(clean_expired_exports({}))
            assert result["removed"] == 0
        finally:
            del os.environ["EXPORT_DIR"]
