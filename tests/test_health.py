"""Smoke tests for the repository skeleton."""
import unittest
from apps.api.app import ApiApplication
from core import health_status
class HealthTest(unittest.TestCase):
    def test_core_health_status(self) -> None:
        self.assertEqual(health_status(), {"service": "securellmbench", "status": "ok"})
    def test_api_health_delegates_to_core(self) -> None:
        self.assertEqual(ApiApplication().health(), health_status())
