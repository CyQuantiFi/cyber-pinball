"""Tests for tools/uploader.py against a fake CyQuantiFi on localhost.

    python3 -m unittest discover -s tests -p "test_*.py"
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import uploader  # noqa: E402


def game(n: int, **extra) -> str:
    obj = {
        "schema_version": 1,
        "game_id": f"TT-01-20261022T1403{n:02d}-{n}",
        "cabinet_id": "TT-01",
        "event_id": "booth",
        "ts": "2026-10-22T14:03:11+11:00",
        "initials": "ACE",
        "score": 1000 * n,
        "worst_path": 0,
        "worst_path_techniques": [],
    }
    obj.update(extra)
    return json.dumps(obj)


class FakeCyQuantiFi:
    """Records each batch and answers like POST /api/game/results."""

    def __init__(self):
        self.batches: list[list[dict]] = []
        self.seen: set[str] = set()
        self.status = 200
        self.refuse_ids: set[str] = set()
        self.auth: list[str] = []
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                fake.auth.append(self.headers.get("Authorization", ""))
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if fake.status != 200:
                    self.send_response(fake.status)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": "nope"}).encode())
                    return
                results = body["results"]
                fake.batches.append(results)
                created = skipped = 0
                errors = []
                for i, r in enumerate(results):
                    if r["game_id"] in fake.refuse_ids:
                        errors.append({"index": i, "game_id": r["game_id"], "reason": "ts: bad"})
                    elif r["game_id"] in fake.seen:
                        skipped += 1
                    else:
                        fake.seen.add(r["game_id"])
                        created += 1
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"created": created, "skipped": skipped, "errors": errors}).encode())

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class UploaderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.fake = FakeCyQuantiFi()
        self.settings = uploader.Settings(data_dir=self.dir, url=self.fake.url, api_key="cqk_test", allow_http=True)

    def tearDown(self):
        self.fake.close()
        self.tmp.cleanup()

    def write_games(self, *lines: str, partial: str = "") -> None:
        with open(self.dir / uploader.GAMES_FILE, "a", encoding="utf-8", newline="") as f:
            for line in lines:
                f.write(line + "\r\n")  # the table writes Windows line endings
            f.write(partial)

    def errors(self) -> list[dict]:
        path = self.dir / uploader.ERRORS_FILE
        if not path.exists():
            return []
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]

    # -- sending ---------------------------------------------------------

    def test_new_games_are_sent_with_the_key(self):
        self.write_games(game(1), game(2))
        uploader.drain(self.settings)
        self.assertEqual([r["game_id"] for r in self.fake.batches[0]], ["TT-01-20261022T140301-1", "TT-01-20261022T140302-2"])
        self.assertEqual(self.fake.auth, ["Bearer cqk_test"])

    def test_only_new_lines_are_sent_next_time(self):
        self.write_games(game(1))
        uploader.drain(self.settings)
        self.write_games(game(2))
        uploader.drain(self.settings)
        self.assertEqual(len(self.fake.batches), 2)
        self.assertEqual([r["game_id"] for r in self.fake.batches[1]], ["TT-01-20261022T140302-2"])

    def test_nothing_new_sends_nothing(self):
        self.write_games(game(1))
        uploader.drain(self.settings)
        uploader.drain(self.settings)
        self.assertEqual(len(self.fake.batches), 1)

    def test_a_line_still_being_written_waits(self):
        self.write_games(game(1), partial=game(2)[:20])
        uploader.drain(self.settings)
        self.assertEqual(len(self.fake.batches[0]), 1)
        with open(self.dir / uploader.GAMES_FILE, "a", encoding="utf-8", newline="") as f:
            f.write(game(2)[20:] + "\r\n")
        uploader.drain(self.settings)
        self.assertEqual([r["game_id"] for r in self.fake.batches[1]], ["TT-01-20261022T140302-2"])

    def test_large_backlogs_go_in_batches(self):
        self.write_games(*[game(i % 60, game_id=f"g{i}") for i in range(250)])
        uploader.drain(self.settings)
        self.assertEqual([len(b) for b in self.fake.batches], [100, 100, 50])

    def test_resend_is_safe(self):
        self.write_games(game(1))
        uploader.drain(self.settings)
        uploader.write_offset(self.dir, 0)
        uploader.drain(self.settings)
        self.assertEqual(len(self.fake.seen), 1)

    def test_a_replaced_file_is_read_from_the_start(self):
        self.write_games(game(1), game(2))
        uploader.drain(self.settings)
        (self.dir / uploader.GAMES_FILE).write_text(game(3) + "\n", encoding="utf-8")
        uploader.drain(self.settings)
        self.assertEqual([r["game_id"] for r in self.fake.batches[1]], ["TT-01-20261022T140303-3"])

    # -- refusals --------------------------------------------------------

    def test_refused_lines_are_kept_with_the_reason(self):
        self.fake.refuse_ids = {"TT-01-20261022T140301-1"}
        self.write_games(game(1), game(2))
        uploader.drain(self.settings)
        [err] = self.errors()
        self.assertEqual(err["reason"], "ts: bad")
        self.assertIn("TT-01-20261022T140301-1", err["line"])
        self.assertIn("TT-01-20261022T140302-2", self.fake.seen)

    def test_old_and_broken_lines_are_not_sent(self):
        old = json.dumps({"ts": "2026-10-01T10:00:00", "initials": "OLD", "score": 5})
        self.write_games(old, "{not json", game(1))
        uploader.drain(self.settings)
        self.assertEqual([r["game_id"] for r in self.fake.batches[0]], ["TT-01-20261022T140301-1"])
        reasons = [e["reason"] for e in self.errors()]
        self.assertTrue(any("schema_version" in r for r in reasons))
        self.assertIn("not valid JSON", reasons)

    # -- failures keep the place -----------------------------------------

    def test_server_errors_are_retried_without_losing_the_place(self):
        self.write_games(game(1))
        self.fake.status = 503
        with self.assertRaises(uploader.RetryLater):
            uploader.drain(self.settings)
        self.assertEqual(uploader.read_offset(self.dir), 0)
        self.fake.status = 200
        uploader.drain(self.settings)
        self.assertEqual(len(self.fake.seen), 1)

    def test_a_bad_key_stops_without_losing_the_place(self):
        self.write_games(game(1))
        self.fake.status = 403
        with self.assertRaises(uploader.Misconfigured):
            uploader.drain(self.settings)
        self.assertEqual(uploader.read_offset(self.dir), 0)

    def test_offline_is_retried(self):
        self.write_games(game(1))
        self.settings.url = "http://127.0.0.1:1"
        with self.assertRaises(uploader.RetryLater):
            uploader.drain(self.settings)
        self.assertEqual(uploader.read_offset(self.dir), 0)

    def test_run_forever_backs_off(self):
        self.write_games(game(1))
        self.settings.url = "http://127.0.0.1:1"
        waits: list[int] = []

        def sleep(seconds):
            waits.append(seconds)
            if len(waits) >= 8:
                raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            uploader.run_forever(self.settings, sleep=sleep)
        self.assertEqual(waits, [5, 10, 20, 40, 80, 160, 300, 300])

    # -- settings --------------------------------------------------------

    def test_settings_from_ini_then_environment(self):
        (self.dir / uploader.CONFIG_FILE).write_text(
            "[upload]\nurl = https://ini.example\napi_key = cqk_ini\n", encoding="utf-8"
        )
        args = uploader.parse_args(["--data-dir", str(self.dir)])
        s = uploader.load_settings(args, environ={})
        self.assertEqual((s.url, s.api_key), ("https://ini.example", "cqk_ini"))
        s = uploader.load_settings(args, environ={"CYQ_API_KEY": "cqk_env"})
        self.assertEqual(s.api_key, "cqk_env")

    def test_plain_http_is_refused_by_default(self):
        s = uploader.Settings(data_dir=self.dir, url="http://example", api_key="k")
        self.assertTrue(any("https" in p for p in uploader.check_settings(s, need_key=True)))

    def test_dry_run_sends_nothing(self):
        self.write_games(game(1))
        uploader.drain(self.settings, dry_run=True)
        self.assertEqual(self.fake.batches, [])
        self.assertEqual(uploader.read_offset(self.dir), 0)


if __name__ == "__main__":
    unittest.main()
