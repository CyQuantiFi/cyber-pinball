#!/usr/bin/env python3
"""Send finished Threat Tide games to CyQuantiFi.

Runs on the booth PC beside Visual Pinball. The table never touches the
network: it appends one JSON line per game to ThreatTide_games.jsonl, as it
always has. This script reads new lines from that file and posts them to
CyQuantiFi's POST /api/game/results, in batches, with a cabinet API key.

* The jsonl file stays the master copy. Nothing here deletes or edits it.
* Offline is normal. Network errors and server errors are retried with a
  growing delay (up to 5 minutes); the place reached is only saved after
  CyQuantiFi has answered.
* Sending a game twice is harmless: CyQuantiFi skips games it already has. So
  after a crash, or with --resend, lines are simply sent again.
* Lines CyQuantiFi refuses (and old lines written before the table had export
  support) are copied to ThreatTide_upload_errors.jsonl with the reason, so a
  bad line never blocks the ones after it.

Settings come from ThreatTide_upload.ini in the data folder, then environment
variables, then the command line (later wins):

    [upload]
    url = https://app.cyquantifi.com
    api_key = cqk_...

    CYQ_API_URL, CYQ_API_KEY, CYQ_DATA_DIR

Usage:

    python tools/uploader.py --data-dir "C:\\vPinball\\VisualPinball\\User"
    python tools/uploader.py --once        # send what is there, then exit
    python tools/uploader.py --dry-run     # show what would be sent
    python tools/uploader.py --resend      # start again from the first line

Standard library only, so the booth PC needs nothing but Python 3.10+.
"""

from __future__ import annotations

import argparse
import configparser
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

GAMES_FILE = "ThreatTide_games.jsonl"
STATE_FILE = "ThreatTide_upload_state.json"
ERRORS_FILE = "ThreatTide_upload_errors.jsonl"
LOG_FILE = "ThreatTide_upload.log"
CONFIG_FILE = "ThreatTide_upload.ini"

ENDPOINT = "/api/game/results"
#: CyQuantiFi accepts at most this many lines per request.
BATCH_SIZE = 100
POLL_SECONDS = 10
RETRY_FIRST_SECONDS = 5
RETRY_MAX_SECONDS = 300
TIMEOUT_SECONDS = 20

log = logging.getLogger("uploader")


class RetryLater(Exception):
    """CyQuantiFi could not be reached or could not take the batch right now."""


class Misconfigured(Exception):
    """The key or URL is wrong. Retrying will not help until someone fixes it."""


@dataclass
class Settings:
    data_dir: Path
    url: str
    api_key: str
    allow_http: bool = False

    @property
    def endpoint(self) -> str:
        return self.url.rstrip("/") + ENDPOINT


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def load_settings(args: argparse.Namespace, environ=os.environ) -> Settings:
    data_dir = args.data_dir or environ.get("CYQ_DATA_DIR") or "."
    data = Path(data_dir)
    url = api_key = ""

    ini = Path(args.config) if args.config else data / CONFIG_FILE
    if ini.exists():
        parser = configparser.ConfigParser()
        parser.read(ini, encoding="utf-8")
        url = parser.get("upload", "url", fallback="")
        api_key = parser.get("upload", "api_key", fallback="")

    url = environ.get("CYQ_API_URL", url)
    api_key = environ.get("CYQ_API_KEY", api_key)
    if args.url:
        url = args.url

    return Settings(data_dir=data, url=url.strip(), api_key=api_key.strip(), allow_http=args.allow_http)


def check_settings(settings: Settings, *, need_key: bool) -> list[str]:
    problems = []
    if not settings.data_dir.is_dir():
        problems.append(f"data folder not found: {settings.data_dir}")
    if not settings.url:
        problems.append(f"no CyQuantiFi URL (set url in {CONFIG_FILE} or CYQ_API_URL)")
    elif not settings.url.startswith("https://") and not settings.allow_http:
        problems.append("the URL must start with https:// (use --allow-http only for local testing)")
    if need_key and not settings.api_key:
        problems.append(f"no API key (set api_key in {CONFIG_FILE} or CYQ_API_KEY)")
    return problems


# ---------------------------------------------------------------------------
# Where we got to
# ---------------------------------------------------------------------------


def read_offset(data_dir: Path) -> int:
    try:
        return int(json.loads((data_dir / STATE_FILE).read_text(encoding="utf-8"))["offset"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def write_offset(data_dir: Path, offset: int) -> None:
    """Saved via a temporary file, so a power cut never leaves half a file."""
    path = data_dir / STATE_FILE
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"offset": offset}), encoding="utf-8")
    os.replace(tmp, path)


def record_errors(data_dir: Path, items: list[tuple[str, str]]) -> None:
    """Append ``(line, reason)`` pairs to the errors file."""
    if not items:
        return
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(data_dir / ERRORS_FILE, "a", encoding="utf-8") as f:
        for line, reason in items:
            f.write(json.dumps({"at": stamp, "reason": reason, "line": line}) + "\n")
    for _line, reason in items:
        log.warning("not sent: %s", reason)


# ---------------------------------------------------------------------------
# Reading the games file
# ---------------------------------------------------------------------------


@dataclass
class Pending:
    """New complete lines, and the offset just past the last one."""

    lines: list[str]
    end: int


def read_new_lines(path: Path, offset: int, limit: int = BATCH_SIZE) -> Pending:
    """Up to ``limit`` complete lines starting at ``offset``.

    A line still being written (no newline yet) is left for next time. If the
    file is now shorter than ``offset`` it was replaced, so start again from
    the top; CyQuantiFi skips anything it already has.
    """
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        return Pending([], offset)
    if size < offset:
        log.info("%s is shorter than last time; reading it from the start", path.name)
        offset = 0

    lines: list[str] = []
    end = offset
    with open(path, "rb") as f:
        f.seek(offset)
        while len(lines) < limit:
            raw = f.readline()
            if not raw or not raw.endswith(b"\n"):
                break
            end += len(raw)
            # The table writes ANSI text; the JSON itself is ASCII.
            text = raw.decode("utf-8", errors="replace").strip()
            if text:
                lines.append(text)
    return Pending(lines, end)


def split_sendable(lines: list[str]) -> tuple[list[tuple[str, dict]], list[tuple[str, str]]]:
    """Lines CyQuantiFi can take, and the ones it can't, with the reason."""
    sendable, rejected = [], []
    for line in lines:
        try:
            obj = json.loads(line)
        except ValueError:
            rejected.append((line, "not valid JSON"))
            continue
        if not isinstance(obj, dict):
            rejected.append((line, "not a JSON object"))
        elif "schema_version" not in obj:
            rejected.append((line, "written before the table had export support (no schema_version)"))
        else:
            sendable.append((line, obj))
    return sendable, rejected


# ---------------------------------------------------------------------------
# Talking to CyQuantiFi
# ---------------------------------------------------------------------------


def post_batch(settings: Settings, results: list[dict]) -> dict:
    body = json.dumps({"results": results}).encode("utf-8")
    request = urllib.request.Request(
        settings.endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ThreatTide-uploader/1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = _detail(exc)
        if exc.code in (401, 403, 404):
            raise Misconfigured(f"HTTP {exc.code}: {detail}") from exc
        if exc.code == 429 or exc.code >= 500:
            raise RetryLater(f"HTTP {exc.code}: {detail}") from exc
        # Any other 4xx refuses the batch as a whole.
        return {"created": 0, "skipped": 0, "rejected_batch": f"HTTP {exc.code}: {detail}"}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise RetryLater(str(exc)) from exc


def _detail(exc: urllib.error.HTTPError) -> str:
    try:
        payload = json.loads(exc.read().decode("utf-8"))
        return str(payload.get("detail", payload))[:300]
    except Exception:  # noqa: BLE001 - only for the log line
        return exc.reason or "no detail"


# ---------------------------------------------------------------------------
# One pass
# ---------------------------------------------------------------------------


def send_once(settings: Settings, *, dry_run: bool = False) -> int:
    """Send one batch. Returns how many lines it moved past (0 = nothing new).

    Raises RetryLater or Misconfigured without moving the offset.
    """
    games = settings.data_dir / GAMES_FILE
    offset = read_offset(settings.data_dir)
    pending = read_new_lines(games, offset)
    if not pending.lines and pending.end == offset:
        return 0

    sendable, rejected = split_sendable(pending.lines)

    if dry_run:
        for _line, obj in sendable:
            print(f"would send {obj.get('game_id')} ({obj.get('initials')}, {obj.get('score')})")
        for _line, reason in rejected:
            print(f"would skip: {reason}")
        return 0

    if sendable:
        reply = post_batch(settings, [obj for _line, obj in sendable])
        if "rejected_batch" in reply:
            rejected += [(line, reply["rejected_batch"]) for line, _obj in sendable]
        else:
            for err in reply.get("errors", []):
                index = err.get("index")
                if isinstance(index, int) and 0 <= index < len(sendable):
                    rejected.append((sendable[index][0], err.get("reason", "refused")))
            log.info(
                "sent %d line(s): %d new, %d already there, %d refused",
                len(sendable),
                reply.get("created", 0),
                reply.get("skipped", 0),
                len(reply.get("errors", [])),
            )

    record_errors(settings.data_dir, rejected)
    write_offset(settings.data_dir, pending.end)
    return len(pending.lines) or 1


def drain(settings: Settings, *, dry_run: bool = False) -> None:
    """Keep sending until nothing new is left."""
    while send_once(settings, dry_run=dry_run):
        if dry_run:
            return


def run_forever(settings: Settings, sleep=time.sleep) -> None:
    delay = RETRY_FIRST_SECONDS
    while True:
        try:
            drain(settings)
            delay = RETRY_FIRST_SECONDS
            sleep(POLL_SECONDS)
        except RetryLater as exc:
            log.warning("CyQuantiFi not reachable (%s); trying again in %ds", exc, delay)
            sleep(delay)
            delay = min(delay * 2, RETRY_MAX_SECONDS)
        except Misconfigured as exc:
            log.error("CyQuantiFi refused the key or URL (%s). Check %s. Trying again in %ds.", exc, CONFIG_FILE, RETRY_MAX_SECONDS)
            sleep(RETRY_MAX_SECONDS)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Send Threat Tide game results to CyQuantiFi.")
    p.add_argument("--data-dir", help="folder holding ThreatTide_games.jsonl (default: CYQ_DATA_DIR or .)")
    p.add_argument("--config", help=f"settings file (default: <data-dir>/{CONFIG_FILE})")
    p.add_argument("--url", help="CyQuantiFi base URL, e.g. https://app.cyquantifi.com")
    p.add_argument("--once", action="store_true", help="send what is there now, then exit")
    p.add_argument("--dry-run", action="store_true", help="show what would be sent; send nothing")
    p.add_argument("--resend", action="store_true", help="start again from the first line")
    p.add_argument("--allow-http", action="store_true", help="allow a plain http:// URL (local testing only)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = load_settings(args)

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if settings.data_dir.is_dir():
        handlers.append(logging.FileHandler(settings.data_dir / LOG_FILE, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)

    problems = check_settings(settings, need_key=not args.dry_run)
    if problems:
        for problem in problems:
            log.error(problem)
        return 2

    if args.resend:
        write_offset(settings.data_dir, 0)
        log.info("starting again from the first line")

    if args.dry_run:
        drain(settings, dry_run=True)
        return 0

    if args.once:
        try:
            drain(settings)
        except (RetryLater, Misconfigured) as exc:
            log.error("stopped: %s", exc)
            return 1
        return 0

    log.info("watching %s; sending to %s", settings.data_dir / GAMES_FILE, settings.endpoint)
    try:
        run_forever(settings)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
