import asyncio
import logging
import unittest
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.request_id import (
    RequestIDLogFilter,
    RequestIDMiddleware,
    get_current_request_id,
    reset_current_request_id,
    set_current_request_id,
)


class TestRequestIdPropagation(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.add_middleware(RequestIDMiddleware)

        @self.app.get("/test-endpoint")
        async def test_endpoint():
            req_id_in_handler = get_current_request_id()
            logger = logging.getLogger("test_logger")
            logger.info("Handling test endpoint")
            return {"request_id": req_id_in_handler}

        @self.app.get("/test-error")
        async def test_error():
            raise RuntimeError("Forced test error")

        @self.app.get("/test-async-sleep")
        async def test_async_sleep(delay: float = 0.05):
            initial_id = get_current_request_id()
            await asyncio.sleep(delay)
            after_sleep_id = get_current_request_id()
            return {"initial": initial_id, "after_sleep": after_sleep_id}

        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_incoming_request_id_preserved(self):
        custom_id = "trace-client-abc-12345"
        response = self.client.get(
            "/test-endpoint",
            headers={"X-Request-ID": custom_id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Request-ID"), custom_id)
        self.assertEqual(response.json()["request_id"], custom_id)

    def test_generated_request_id_when_missing(self):
        response = self.client.get("/test-endpoint")
        self.assertEqual(response.status_code, 200)
        returned_id = response.headers.get("X-Request-ID")
        self.assertIsNotNone(returned_id)
        self.assertTrue(len(returned_id) >= 16)
        self.assertEqual(response.json()["request_id"], returned_id)

    def test_invalid_incoming_request_id_replaced_with_generated(self):
        invalid_id = "invalid id with spaces!@#$%^&*()_+"
        response = self.client.get(
            "/test-endpoint",
            headers={"X-Request-ID": invalid_id},
        )
        self.assertEqual(response.status_code, 200)
        returned_id = response.headers.get("X-Request-ID")
        self.assertNotEqual(returned_id, invalid_id)
        self.assertTrue(len(returned_id) >= 16)

    def test_context_availability_and_cleanup_on_success(self):
        self.assertIsNone(get_current_request_id())
        response = self.client.get("/test-endpoint")
        self.assertEqual(response.status_code, 200)
        # Context must be cleared after request completion
        self.assertIsNone(get_current_request_id())

    def test_context_cleanup_on_unhandled_exception(self):
        self.assertIsNone(get_current_request_id())
        response = self.client.get("/test-error")
        self.assertEqual(response.status_code, 500)
        # Context must be reset even when an exception occurs
        self.assertIsNone(get_current_request_id())

    def test_log_filter_enrichment(self):
        log_filter = RequestIDLogFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )

        # Outside request context
        log_filter.filter(record)
        self.assertEqual(record.request_id, "-")

        # Inside request context
        token = set_current_request_id("req-ctx-999")
        try:
            log_filter.filter(record)
            self.assertEqual(record.request_id, "req-ctx-999")
        finally:
            reset_current_request_id(token)

        # Back outside context
        log_filter.filter(record)
        self.assertEqual(record.request_id, "-")

    def test_concurrent_request_isolation(self):
        import concurrent.futures

        ids = [f"trace-concurrent-{i}" for i in range(10)]

        def send_request(req_id: str):
            res = self.client.get(
                "/test-async-sleep",
                headers={"X-Request-ID": req_id},
            )
            return req_id, res.status_code, res.json()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_request, req_id) for req_id in ids]
            for future in concurrent.futures.as_completed(futures):
                req_id, status_code, data = future.result()
                self.assertEqual(status_code, 200)
                self.assertEqual(data["initial"], req_id)
                self.assertEqual(data["after_sleep"], req_id)

        # After all threads complete, main thread context is clean
        self.assertIsNone(get_current_request_id())


if __name__ == "__main__":
    unittest.main()
