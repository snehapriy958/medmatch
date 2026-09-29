import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.api.routes.health import readiness
from app.config.settings import settings


class TestHealthReadiness(unittest.TestCase):
    def test_readiness_no_disk_churn(self):
        """Verify readiness probe verifies upload directory without creating temporary files."""
        upload_path = Path(settings.UPLOAD_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)
        files_before = set(upload_path.iterdir())

        mock_conn = MagicMock()
        mock_conn.execute.return_value.scalar_one_or_none.side_effect = [
            "6f0604b23df6",  # alembic_version
            "0.8.0",         # pg_extension vector
        ]

        with patch("app.api.routes.health.engine.connect") as mock_connect, \
             patch("app.api.routes.health.RedisClient.ping") as mock_ping:
            mock_connect.return_value.__enter__.return_value = mock_conn

            response = readiness()

            self.assertEqual(response["status"], "UP")
            self.assertEqual(response["checks"]["uploads"], "UP")
            self.assertEqual(response["checks"]["database"], "UP")
            self.assertEqual(response["checks"]["redis"], "UP")
            self.assertEqual(response["checks"]["vector_search"], "UP")

        files_after = set(upload_path.iterdir())
        self.assertEqual(
            files_before,
            files_after,
            "Readiness probe should not create or delete files in the upload directory",
        )
        self.assertFalse(
            (upload_path / ".readiness_check.tmp").exists(),
            ".readiness_check.tmp must not exist",
        )

    def test_readiness_fails_when_upload_dir_not_writable(self):
        """Verify readiness fails with 503 when upload directory lacks write permission."""
        mock_conn = MagicMock()
        mock_conn.execute.return_value.scalar_one_or_none.side_effect = [
            "6f0604b23df6",
            "0.8.0",
        ]

        with patch("app.api.routes.health.engine.connect") as mock_connect, \
             patch("app.api.routes.health.RedisClient.ping"), \
             patch("os.access", return_value=False):
            mock_connect.return_value.__enter__.return_value = mock_conn

            with self.assertRaises(HTTPException) as ctx:
                readiness()

            self.assertEqual(ctx.exception.status_code, 503)
            self.assertEqual(ctx.exception.detail["checks"]["uploads"], "DOWN")


if __name__ == "__main__":
    unittest.main()
