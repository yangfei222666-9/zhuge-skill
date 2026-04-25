import json
import tempfile
import unittest
from pathlib import Path

from adapters import api_football
from core.llm import LLMClient
from scripts import backfill


class FakeGeminiRequests:
    def __init__(self):
        self.url = None
        self.headers = None
        self.body = None

    def post(self, url, headers=None, json=None, timeout=None):
        self.url = url
        self.headers = headers or {}
        self.body = json or {}

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "candidates": [
                        {"content": {"parts": [{"text": "ok"}]}}
                    ]
                }

        return Response()


class P0RegressionTests(unittest.TestCase):
    def test_gemini_api_key_is_not_sent_in_url(self):
        fake_requests = FakeGeminiRequests()
        client = LLMClient(
            provider="gemini",
            api_key="secret-key",
            model="gemini-test",
            base_url="https://gemini.example/v1beta",
        )

        result = client._call_gemini("hello", "system", 32, 1, fake_requests)

        self.assertEqual(result, "ok")
        self.assertNotIn("secret-key", fake_requests.url)
        self.assertNotIn("?key=", fake_requests.url)
        self.assertEqual(fake_requests.headers.get("x-goog-api-key"), "secret-key")
        self.assertEqual(fake_requests.headers.get("Content-Type"), "application/json")

    def test_get_odds_returns_none_when_bookmakers_missing(self):
        old_get = api_football._get
        api_football._get = lambda *args, **kwargs: {"response": [{"bookmakers": []}]}
        try:
            self.assertIsNone(api_football.get_odds(123))
        finally:
            api_football._get = old_get

    def test_get_odds_ignores_malformed_odd_values(self):
        payload = {
            "response": [
                {
                    "bookmakers": [
                        {
                            "bets": [
                                {
                                    "name": "Match Winner",
                                    "values": [
                                        {"value": "Home", "odd": "bad"},
                                        {"value": "Draw", "odd": "3.2"},
                                    ],
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        old_get = api_football._get
        api_football._get = lambda *args, **kwargs: payload
        try:
            odds = api_football.get_odds(123)
        finally:
            api_football._get = old_get

        self.assertIsNone(odds["home"])
        self.assertEqual(odds["draw"], 3.2)
        self.assertIsNone(odds["away"])

    def test_backfill_load_db_logs_malformed_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_db, old_seed = backfill.DB, backfill.SEED
            old_logger = backfill._log_error
            errors = []
            backfill.DB = Path(tmp) / "experience.jsonl"
            backfill.SEED = Path(tmp) / "seed_experience.jsonl"
            backfill.DB.write_text(
                '{"exp_id":"ok","api_fixture_id":1}\n{broken json\n',
                encoding="utf-8",
            )
            backfill._log_error = lambda category, exc, context: errors.append(
                (category, type(exc).__name__, context)
            )
            try:
                records = backfill._load_db()
            finally:
                backfill.DB, backfill.SEED = old_db, old_seed
                backfill._log_error = old_logger

        self.assertEqual([r["exp_id"] for r in records], ["ok"])
        self.assertEqual(errors[0][0], "backfill_load_db")
        self.assertEqual(errors[0][2]["line_no"], 2)

    def test_save_db_creates_backup_before_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_db, old_seed = backfill.DB, backfill.SEED
            backfill.DB = Path(tmp) / "experience.jsonl"
            backfill.SEED = Path(tmp) / "seed_experience.jsonl"
            backfill.DB.write_text('{"exp_id":"old"}\n', encoding="utf-8")
            try:
                backfill._save_db([{"exp_id": "new"}])
                backup = backfill.DB.with_suffix(backfill.DB.suffix + ".bak")
                backup_exists = backup.exists()
                saved = [
                    json.loads(line)
                    for line in backfill.DB.read_text(encoding="utf-8").splitlines()
                ]
            finally:
                backfill.DB, backfill.SEED = old_db, old_seed

        self.assertTrue(backup_exists)
        self.assertEqual(saved, [{"exp_id": "new"}])


if __name__ == "__main__":
    unittest.main()
