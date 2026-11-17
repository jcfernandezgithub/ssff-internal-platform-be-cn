import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app import gemini_audit


class GeminiAuditTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "BIGQUERY_AUDIT_ENABLED": "true",
            "BIGQUERY_PROJECT_ID": "poc-ia-growth-y-productos",
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = Mock()
        self.client.insert_rows_json.return_value = []
        self.client_patch = patch.object(gemini_audit, "_get_client", return_value=self.client)
        self.get_client = self.client_patch.start()
        self.addCleanup(self.client_patch.stop)
        self.response = SimpleNamespace(usage_metadata=SimpleNamespace(
            prompt_token_count=100, candidates_token_count=20, total_token_count=125,
        ))

    def record(self, **kwargs):
        return gemini_audit.registrar_consumo_gemini(
            self.response, model="gemini-3.5-flash", **kwargs,
        )

    def test_destination_schema_and_provider_token_counts(self):
        self.assertTrue(self.record())
        args, kwargs = self.client.insert_rows_json.call_args
        self.assertEqual(args[0], "poc-ia-growth-y-productos.audit_ia.gemini_tokens")
        row, = args[1]
        self.assertEqual(set(row), {
            "timestamp", "agent_id", "product", "model", "prompt_tokens",
            "completion_tokens", "total_tokens",
        })
        self.assertEqual(row["prompt_tokens"], 100)
        self.assertEqual(row["completion_tokens"], 20)
        # Preserve provider total, which can include additional token categories.
        self.assertEqual(row["total_tokens"], 125)
        self.assertEqual(row["model"], "gemini-3.5-flash")
        self.assertEqual(row["agent_id"], "SSFF_Cambio_Nombre")
        self.assertEqual(row["product"], "SSFF_Internal_Platform")
        self.assertEqual(datetime.fromisoformat(row["timestamp"]).utcoffset().total_seconds(), 0)
        self.assertEqual(kwargs["timeout"], 5.0)

    def test_disabled_by_default_does_not_access_bigquery(self):
        del os.environ["BIGQUERY_AUDIT_ENABLED"]
        self.assertFalse(self.record())
        self.get_client.assert_not_called()

    def test_missing_usage_does_not_invent_consumption(self):
        self.response.usage_metadata = None
        self.assertFalse(self.record())
        self.get_client.assert_not_called()

    def test_configured_identity_and_explicit_override(self):
        os.environ["BIGQUERY_AUDIT_AGENT_ID"] = "configured-agent"
        os.environ["BIGQUERY_AUDIT_PRODUCT"] = "configured-product"
        self.assertTrue(self.record())
        row = self.client.insert_rows_json.call_args.args[1][0]
        self.assertEqual(row["agent_id"], "configured-agent")
        self.assertEqual(row["product"], "configured-product")
        self.assertTrue(self.record(agent_id="explicit-agent", product="explicit-product"))
        row = self.client.insert_rows_json.call_args.args[1][0]
        self.assertEqual(row["agent_id"], "explicit-agent")
        self.assertEqual(row["product"], "explicit-product")

    def test_rejected_insert_returns_false(self):
        self.client.insert_rows_json.return_value = [{"index": 0, "errors": [{"reason": "invalid"}]}]
        self.assertFalse(self.record())

    def test_connection_failure_does_not_interrupt_processing(self):
        self.client.insert_rows_json.side_effect = TimeoutError("unavailable")
        self.assertFalse(self.record())

    def test_missing_project_does_not_interrupt_processing(self):
        del os.environ["BIGQUERY_PROJECT_ID"]
        self.assertFalse(self.record())
        self.get_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
