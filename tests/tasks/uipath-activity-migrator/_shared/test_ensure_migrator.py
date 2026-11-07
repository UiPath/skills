"""Unit tests for skills/uipath-activity-migrator/scripts/ensure-migrator.mjs — the download stage.

Placement note. Like test_summarize_sarif.py beside it, nothing in CI runs this file: every job in
.github/workflows/test-helpers.yml runs on Linux and the script exits `not-windows` there. Run it
locally on Windows from the repository root (needs pytest, node, curl and the .NET Framework's csc.exe,
which every Windows 10/11 install carries):
    python -m pytest tests/tasks/uipath-activity-migrator/_shared -q

Each test serves a small archive from a local HTTP server that behaves like download.uipath.com
(Content-Length, Accept-Ranges: bytes, ETag, Last-Modified, Content-MD5, 206 on Range) with knobs for
the shapes the download must survive: an edge that serves every plain-URL request at a crawl past the
bytes it has cached, a connection dropped mid-response, a server that ignores or refuses ranges or
answers from the wrong offset, an archive replaced mid-download, a corrupted body, a curl that cannot
reach the server, files held open by a stale process, and a second run on the same folder. The archive
holds a stub UiPath.Upgrade.exe that prints a version, so a run that reaches the verify stage ends in
`status: ok`. A stall is detected by curl's speed limit after ~20 s, so the two stall tests take that long.
"""

import base64
import email.utils
import hashlib
import http.server
import json
import os
import subprocess
import sys
import threading
import time
import zipfile

from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="the Activity Migrator and its acquisition script are Windows-only")

SCRIPT = Path(__file__).resolve().parents[4] / "skills" / "uipath-activity-migrator" / "scripts" / "ensure-migrator.mjs"
CSC = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe"
MIB = 1024 * 1024
CHUNK = 16 * MIB
FILLER_MIB = 40  # three chunks: 16 + 16 + 8
SHORT_WINDOW = {"UIPATH_ACTIVITY_MIGRATOR_WINDOW_SECONDS": "8"}  # lock wait = window/8 = 1 s
HOLD_LOCK_JS = (
    "const fs=require('fs');"
    "fs.openSync(process.argv[1],fs.constants.O_RDWR|fs.constants.O_CREAT|0x10000000);"
    "if(process.argv[2])fs.writeFileSync(process.argv[2],String(process.pid));"
    "console.log('held');setTimeout(()=>{},120000)"
)


def compile_stub(directory, name, source):
    if not CSC.is_file():
        pytest.skip(f"{CSC} not found; {name} cannot be compiled")
    src = directory / (name + ".cs")
    src.write_text(source, encoding="ascii")
    exe = directory / name
    subprocess.run([str(CSC), "/nologo", "/target:exe", f"/out:{exe}", str(src)], check=True, capture_output=True)
    return exe


@pytest.fixture(scope="session")
def archive(tmp_path_factory):
    """Zip with a stub UiPath.Upgrade.exe, an Extensions/ folder and a 40 MiB stored filler."""
    stage = tmp_path_factory.mktemp("archive")
    exe = compile_stub(stage, "UiPath.Upgrade.exe", 'class P { static int Main(string[] a) { System.Console.WriteLine(a.Length > 0 && a[0] == "version" ? "25.10.1-stub" : "usage"); return 0; } }\n')
    readme = stage / "Extensions" / "UIAutomation" / "readme.txt"
    readme.parent.mkdir(parents=True)
    readme.write_text("stub extension\n")
    filler = stage / "filler.bin"
    block = bytes(range(256)) * 4096  # 1 MiB
    with filler.open("wb") as f:
        for _ in range(FILLER_MIB):
            f.write(block)
    zip_path = stage / "UiPath.Upgrade.Cli.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as z:
        z.write(exe, "UiPath.Upgrade.exe")
        z.write(readme, "Extensions/UIAutomation/readme.txt")
        z.write(filler, "filler.bin")
    return zip_path


@pytest.fixture(scope="session")
def blocked_curl(tmp_path_factory):
    """A curl.exe that fails every request the way a blocked proxy makes the real one fail."""
    directory = tmp_path_factory.mktemp("blocked-curl")
    compile_stub(directory, "curl.exe", 'class P { static int Main(string[] a) { System.Console.Error.WriteLine("curl: (7) Failed to connect"); return 7; } }\n')
    return directory


class ArchiveServer:
    """download.uipath.com stand-in. `requests` records (method, range, status, etag) and `paths` the request
    target, in request order.

    plain_slow_from: bytes of the object at or past this offset are served at throttle_bps when the request
    carries no query string (the edge serving the stuck cache fill of the plain URL); a query string gets
    full speed. throttle_after: per connection, full speed for that many bytes, then throttle_bps.
    slow_first_gets: the first N GETs are served at throttle_bps from their first byte, whatever the URL.
    close_after: every response is cut after that many bytes. range_status: answer range requests with
    this status and no body. no_ranges: ignore Range and omit Accept-Ranges. ignore_range: advertise
    Accept-Ranges but answer every GET with the whole object. range_shift: answer a range from another
    offset. corrupt_at: flip one byte in a response starting at that offset. etag_switch_after: from that
    GET on, advertise another ETag."""

    def __init__(self, archive, throttle_after=0, throttle_bps=256, no_ranges=False, corrupt_at=-1, etag_switch_after=0, range_status=0, plain_slow_from=-1, close_after=0, range_shift=0, ignore_range=False, slow_first_gets=0):
        self.archive = Path(archive)
        self.size = self.archive.stat().st_size
        self.md5 = base64.b64encode(hashlib.md5(self.archive.read_bytes()).digest()).decode()
        self.last_modified = email.utils.formatdate(self.archive.stat().st_mtime, usegmt=True)
        self.knobs = dict(throttle_after=throttle_after, throttle_bps=throttle_bps, no_ranges=no_ranges, corrupt_at=corrupt_at, etag_switch_after=etag_switch_after, range_status=range_status, plain_slow_from=plain_slow_from, close_after=close_after, range_shift=range_shift, ignore_range=ignore_range, slow_first_gets=slow_first_gets)
        self.requests = []
        self.paths = []
        self.gets = 0
        self.lock = threading.Lock()
        server = self

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_):
                pass

            def etag(self):
                with server.lock:
                    switched = server.knobs["etag_switch_after"] and server.gets >= server.knobs["etag_switch_after"]
                return '"v2"' if switched else '"v1"'

            def common(self):
                self.send_header("Content-Type", "application/x-zip-compressed")
                self.send_header("ETag", self.etag())
                self.send_header("Last-Modified", server.last_modified)
                self.send_header("Content-MD5", server.md5)
                if not server.knobs["no_ranges"]:
                    self.send_header("Accept-Ranges", "bytes")

            def do_HEAD(self):
                server.requests.append(("HEAD", None, 200, self.etag()))
                server.paths.append(self.path)
                self.send_response(200)
                self.common()
                self.send_header("Content-Length", str(server.size))
                self.end_headers()

            def do_GET(self):
                with server.lock:
                    server.gets += 1
                    nth = server.gets
                rng = self.headers.get("Range")
                plain = "?" not in self.path
                start, end, status = 0, server.size - 1, 200
                if rng and not server.knobs["no_ranges"] and not server.knobs["ignore_range"]:
                    a, b = rng.replace("bytes=", "").split("-")
                    start = int(a or 0)
                    end = min(int(b) if b else server.size - 1, server.size - 1)
                    status = 206
                if status == 206 and server.knobs["range_shift"]:
                    # A proxy that answers a range request with bytes from another offset.
                    start = min(start + server.knobs["range_shift"], server.size - 1)
                server.paths.append(self.path)
                if status == 206 and server.knobs["range_status"]:
                    server.requests.append(("GET", rng, server.knobs["range_status"], self.etag()))
                    self.send_response(server.knobs["range_status"])
                    self.send_header("Content-Range", f"bytes */{server.size}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                server.requests.append(("GET", rng, status, self.etag()))
                length = end - start + 1
                self.send_response(status)
                self.common()
                if status == 206:
                    self.send_header("Content-Range", f"bytes {start}-{end}/{server.size}")
                self.send_header("Content-Length", str(length))
                self.end_headers()
                sent_conn = getattr(self, "_sent", 0)
                sent_resp = 0
                with server.archive.open("rb") as f:
                    f.seek(start)
                    remaining, first = length, True
                    while remaining > 0:
                        if server.knobs["close_after"] and sent_resp >= server.knobs["close_after"]:
                            self.close_connection = True
                            break
                        slow = (server.knobs["throttle_after"] and sent_conn >= server.knobs["throttle_after"]) or (
                            plain and server.knobs["plain_slow_from"] >= 0 and start + sent_resp >= server.knobs["plain_slow_from"]) or nth <= server.knobs["slow_first_gets"]
                        data = f.read(min(remaining, server.knobs["throttle_bps"] if slow else 1 << 16))
                        if first and server.knobs["corrupt_at"] == start:
                            data = bytes([data[0] ^ 0xFF]) + data[1:]
                        first = False
                        try:
                            self.wfile.write(data)
                        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                            break
                        remaining -= len(data)
                        sent_conn += len(data)
                        sent_resp += len(data)
                        self._sent = sent_conn
                        if slow:
                            time.sleep(1)

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/UiPath.Upgrade.Cli.zip"
        return self

    def __exit__(self, *_):
        self.httpd.shutdown()
        self.httpd.server_close()

    def ranged_gets(self):
        return [r for r in self.requests if r[0] == "GET" and r[2] == 206]

    def ranged_paths(self):
        return [p for r, p in zip(self.requests, self.paths) if r[0] == "GET" and r[2] == 206]

    def gets_with_range(self):
        return [r for r in self.requests if r[0] == "GET" and r[1] is not None]

    def marker(self):
        """What the script writes to .chunks/.etag for this server's archive."""
        return f'"v1":{self.size}'


def range_start(request):
    return int(request[1].replace("bytes=", "").split("-")[0])


def script_env(server, install, url_suffix="", path_prepend=None, extra_env=None, default_root=False):
    env = dict(os.environ)
    env.pop("UIPATH_TELEMETRY_DISABLED", None)
    env.pop("UIPATH_ACTIVITY_MIGRATOR_WINDOW_SECONDS", None)
    env.pop("UIPATH_ACTIVITY_MIGRATOR_DIR", None)
    env["UIPATH_ACTIVITY_MIGRATOR_URL"] = server.url + url_suffix
    if default_root:
        env["LOCALAPPDATA"] = str(install)  # the script then installs under <install>\UiPath\ActivityMigrator
    else:
        env["UIPATH_ACTIVITY_MIGRATOR_DIR"] = str(install)
    if path_prepend:
        env["PATH"] = f"{path_prepend};{env.get('PATH', '')}"
    env.update(extra_env or {})
    return env


def launch(server, install, *flags, **kwargs):
    return subprocess.Popen(["node", str(SCRIPT), *flags], env=script_env(server, install, **kwargs), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")


def finish(proc, timeout=180):
    out, err = proc.communicate(timeout=timeout)
    lines = out.strip().splitlines()
    assert lines, f"no stdout; stderr: {err[-800:]}"
    try:
        result = json.loads(lines[-1])
    except json.JSONDecodeError:
        raise AssertionError(f"last stdout line is not JSON: {lines[-1][:300]!r}; stderr: {err[-800:]}") from None
    return proc.returncode, result


def run_script(server, install, *flags, timeout=180, **kwargs):
    return finish(launch(server, install, *flags, **kwargs), timeout=timeout)


def assert_installed(install):
    assert (install / "current" / "UiPath.Upgrade.exe").is_file()
    assert (install / "current" / "Extensions").is_dir()
    assert not (install / ".chunks").exists()
    assert not (install / "UiPath.Upgrade.Cli.download.zip").exists()
    assert not (install / ".lock").exists()
    assert not (install / ".lock.pid").exists()


def seed_chunks(install, files):
    chunks = install / ".chunks"
    chunks.mkdir(parents=True)
    for name, data in files.items():
        (chunks / name).write_bytes(data)
    return chunks


# --- the CDN shapes ---------------------------------------------------------------------------------------------

def test_healthy_edge_is_fetched_in_plain_ranged_requests_only(archive, tmp_path):
    with ArchiveServer(archive) as srv:
        code, r = run_script(srv, tmp_path / "install")
    assert (code, r["status"], r["source"], r["version"]) == (0, "ok", "downloaded", "25.10.1-stub")
    assert [g[1] for g in srv.ranged_gets()] == [f"bytes={i * CHUNK}-{min((i + 1) * CHUNK, srv.size) - 1}" for i in range(3)]
    assert set(srv.paths) == {"/UiPath.Upgrade.Cli.zip"}  # no query string while nothing stalls
    assert_installed(tmp_path / "install")
    assert (tmp_path / "install" / ".last-modified").read_text() == srv.last_modified


def test_stuck_edge_cache_for_the_plain_url_is_bypassed_after_the_first_stalled_request(archive, tmp_path):
    # The 2026-10-26 shape: the plain URL serves its first 20 MiB at full speed and crawls past them; any other URL is
    # fast. Chunk 0 comes plain, chunk 1 stalls plain until curl's speed limit cuts it, every later request is busted.
    with ArchiveServer(archive, plain_slow_from=20 * MIB) as srv:
        code, r = run_script(srv, tmp_path / "install", timeout=120)
    assert (code, r["status"], r["source"]) == (0, "ok", "downloaded")
    paths = srv.ranged_paths()
    starts = [range_start(g) for g in srv.ranged_gets()]
    assert len(paths) == 4
    assert all("?" not in p for p in paths[:2])
    assert all("?r=" in p for p in paths[2:]) and len(set(paths[2:])) == 2
    assert (starts[0], starts[1], starts[3]) == (0, CHUNK, 2 * CHUNK)
    assert 4 * MIB <= starts[2] - CHUNK < 5 * MIB  # the busted request resumed from the bytes the stalled one delivered
    assert_installed(tmp_path / "install")


def test_url_that_already_has_a_query_string_is_used_unchanged_even_after_a_stall(archive, tmp_path):
    # A signed mirror link must not be altered, not even by the cache-busting a stalled request turns on.
    with ArchiveServer(archive, slow_first_gets=1) as srv:
        code, r = run_script(srv, tmp_path / "install", url_suffix="?sig=abc")
    assert (code, r["status"]) == (0, "ok")
    assert set(srv.paths) == {"/UiPath.Upgrade.Cli.zip?sig=abc"}
    assert len(srv.ranged_gets()) == 4  # chunk 0 stalled once and was resumed


def test_dropped_connection_mid_response_keeps_the_bytes_and_continues_from_the_offset(archive, tmp_path):
    # Every response is cut after 5 MiB: nothing is fetched twice, and a drop is not a stall, so the URL stays plain.
    with ArchiveServer(archive, close_after=5 * MIB) as srv:
        code, r = run_script(srv, tmp_path / "install")
    assert (code, r["status"]) == (0, "ok")
    starts = [range_start(g) for g in srv.ranged_gets()]
    assert starts[:4] == [0, 5 * MIB, 10 * MIB, 15 * MIB]
    assert starts == sorted(set(starts))
    assert len(starts) == 10  # 4 + 4 requests for the two 16 MiB chunks, 2 for the last 8 MiB
    assert all("?" not in p for p in srv.ranged_paths())
    assert_installed(tmp_path / "install")


# --- servers that cannot serve ranges ---------------------------------------------------------------------------

def test_server_without_range_support_gets_the_single_stream_download(archive, tmp_path):
    with ArchiveServer(archive, no_ranges=True) as srv:
        code, r = run_script(srv, tmp_path / "install")
    assert (code, r["status"], r["source"]) == (0, "ok", "downloaded")
    assert [(m, rng, st) for m, rng, st, _ in srv.requests] == [("HEAD", None, 200), ("GET", None, 200)]
    assert_installed(tmp_path / "install")


def test_server_that_answers_a_range_with_the_whole_archive_gets_the_single_stream(archive, tmp_path):
    # Ranges advertised, Range dropped (a proxy that strips the header): curl's --max-filesize cuts the first answer.
    install = tmp_path / "install"
    with ArchiveServer(archive, ignore_range=True) as srv:
        code, r = run_script(srv, install)
    assert (code, r["status"], r["source"]) == (0, "ok", "downloaded")
    assert [(m, rng is not None, st) for m, rng, st, _ in srv.requests] == [("HEAD", False, 200), ("GET", True, 200), ("GET", False, 200)]
    assert_installed(install)  # .chunks/ is gone too


def test_server_that_refuses_range_requests_reports_the_error(archive, tmp_path):
    # Ranges advertised, every range GET answers 416: nothing arrives, no single stream is tried, the error is named.
    install = tmp_path / "install"
    with ArchiveServer(archive, range_status=416) as srv:
        code, r = run_script(srv, install)
    assert (code, r["status"], r["code"]) == (1, "error", "download-failed")
    assert "416" in r["message"] and "Manual placement" in r["message"]
    assert "completedBytes" not in r
    assert len(srv.gets_with_range()) == 3 and srv.ranged_gets() == []
    assert all(m != "GET" or rng is not None for m, rng, _, _ in srv.requests)
    assert not (install / ".chunks").exists()


def test_range_answered_from_another_offset_is_discarded_and_reported(archive, tmp_path):
    # Without the Content-Range check the shifted bytes would be appended and only the MD5 would catch it at the end.
    install = tmp_path / "install"
    with ArchiveServer(archive, range_shift=4096) as srv:
        code, r = run_script(srv, install)
    assert (code, r["status"], r["code"]) == (1, "error", "download-failed")
    assert "offset 0 with bytes from offset 4096" in r["message"]
    assert "completedBytes" not in r
    assert len(srv.ranged_gets()) == 3  # three answers from the wrong offset, none accepted, no single stream tried
    assert all(m != "GET" or rng is not None for m, rng, _, _ in srv.requests)
    assert not (install / ".chunks").exists()


# --- integrity ------------------------------------------------------------------------------------------------------

def test_corrupted_chunk_fails_the_content_md5_check_and_the_next_run_starts_clean(archive, tmp_path):
    install = tmp_path / "install"
    with ArchiveServer(archive, corrupt_at=CHUNK) as srv:
        code, r = run_script(srv, install)
    assert (code, r["status"], r["code"]) == (1, "error", "download-failed")
    assert "Content-MD5" in r["message"]
    assert (r["completedBytes"], r["totalBytes"]) == (0, srv.size)  # a rerun is worth it, from scratch
    assert not (install / ".chunks").exists()
    assert not (install / "UiPath.Upgrade.Cli.download.zip").exists()
    with ArchiveServer(archive) as srv:
        code, r = run_script(srv, install)
    assert (code, r["status"]) == (0, "ok")
    assert len(srv.ranged_gets()) == 3


def test_archive_replaced_mid_download_is_reported_and_the_rerun_fetches_the_new_one(archive, tmp_path):
    install = tmp_path / "install"
    with ArchiveServer(archive, etag_switch_after=2) as srv:
        code, r = run_script(srv, install)
    assert (code, r["status"], r["code"]) == (1, "error", "download-failed")
    assert "changed on the server" in r["message"]
    assert (r["completedBytes"], r["totalBytes"]) == (0, srv.size)
    assert [g[3] for g in srv.ranged_gets()] == ['"v1"', '"v2"']  # chunk 0 under v1, chunk 1 arrives as v2: discarded
    assert not (install / ".chunks").exists()
    with ArchiveServer(archive) as srv:
        code, r = run_script(srv, install)
    assert (code, r["status"]) == (0, "ok")
    assert len(srv.ranged_gets()) == 3
    assert_installed(install)


# --- resume ---------------------------------------------------------------------------------------------------------

def test_rerun_resumes_from_the_parts_an_interrupted_run_left_and_keeps_its_bust_decision(archive, tmp_path):
    install = tmp_path / "install"
    data = Path(archive).read_bytes()
    with ArchiveServer(archive) as srv:
        seed_chunks(install, {"part-000.bin": data[:CHUNK], "part-001.bin.tmp": data[CHUNK:CHUNK + 4 * MIB], ".etag": srv.marker().encode(), ".bust": b""})
        code, r = run_script(srv, install)
    assert (code, r["status"]) == (0, "ok")
    assert [g[1] for g in srv.ranged_gets()] == [f"bytes={CHUNK + 4 * MIB}-{2 * CHUNK - 1}", f"bytes={2 * CHUNK}-{srv.size - 1}"]
    assert all("?r=" in p for p in srv.ranged_paths())  # the interrupted run had switched to busting; no stall is paid again
    assert_installed(install)


def test_attempt_file_held_by_a_stale_downloader_does_not_block_the_download(archive, tmp_path):
    # An interrupted run's curl may still be writing its attempt file when the next run starts.
    install = tmp_path / "install"
    with ArchiveServer(archive) as srv:
        chunks = seed_chunks(install, {".etag": srv.marker().encode()})
        with (chunks / "part-000.bin.4242-1.tmp").open("wb") as held:
            held.write(b"stale")
            held.flush()
            code, r = run_script(srv, install)
    assert (code, r["status"]) == (0, "ok")
    assert len(srv.ranged_gets()) == 3
    assert (install / "current" / "UiPath.Upgrade.exe").is_file()


def test_window_expiry_reports_the_bytes_kept_and_the_rerun_resumes(archive, tmp_path):
    install = tmp_path / "install"
    with ArchiveServer(archive, throttle_after=1, throttle_bps=2 * MIB) as srv:  # ~2 MiB/s from the first byte
        code, r = run_script(srv, install, extra_env={"UIPATH_ACTIVITY_MIGRATOR_WINDOW_SECONDS": "5"})
    assert (code, r["status"], r["code"]) == (1, "error", "download-failed")
    assert "within 5 seconds" in r["message"] and "rerun this script" in r["message"]
    assert (r["completedBytes"], r["totalBytes"]) == (CHUNK, srv.size)
    assert (install / ".chunks" / "part-000.bin").stat().st_size == CHUNK
    with ArchiveServer(archive) as srv:
        code, r = run_script(srv, install)
    assert (code, r["status"]) == (0, "ok")
    assert range_start(srv.ranged_gets()[0]) == CHUNK
    assert_installed(install)


def test_window_expiry_at_a_hopeless_pace_reports_manual_placement_not_a_rerun(archive, tmp_path):
    # 256 B/s after the first 64 KiB: a full window moves a few KB, so more runs of it would not finish either.
    install = tmp_path / "install"
    with ArchiveServer(archive, throttle_after=1) as srv:
        code, r = run_script(srv, install, extra_env={"UIPATH_ACTIVITY_MIGRATOR_WINDOW_SECONDS": "5"})
    assert (code, r["status"], r["code"]) == (1, "error", "download-failed")
    assert "more than three more runs" in r["message"] and "Manual placement" in r["message"]
    assert "completedBytes" not in r


def test_partial_held_open_at_completion_is_reported_not_a_crash(archive, tmp_path):
    # An on-access scanner holds a 16 MiB file that just changed exactly when it is complete and about to be renamed.
    install = tmp_path / "install"
    with ArchiveServer(archive) as srv:
        chunks = seed_chunks(install, {".etag": srv.marker().encode(), "part-000.bin.tmp": Path(archive).read_bytes()[:CHUNK]})
        with (chunks / "part-000.bin.tmp").open("rb"):
            code, r = run_script(srv, install)
    assert (code, r["status"], r["code"]) == (1, "error", "download-failed")
    assert "cannot rename" in r["message"]
    assert (r["completedBytes"], r["totalBytes"]) == (CHUNK, srv.size)
    assert srv.ranged_gets() == []  # the bytes are kept; nothing was re-requested


def test_leftover_download_held_by_another_process_is_reported_not_a_crash(archive, tmp_path):
    install = tmp_path / "install"
    install.mkdir()
    leftover = install / "UiPath.Upgrade.Cli.download.zip"
    with leftover.open("wb") as held:  # an open handle without FILE_SHARE_DELETE blocks the unlink
        held.write(b"partial")
        held.flush()
        with ArchiveServer(archive) as srv:
            code, r = run_script(srv, install)
    assert (code, r["status"], r["code"]) == (1, "error", "download-failed")
    assert "UiPath.Upgrade.Cli.download.zip" in r["message"]
    assert "still holding it" in r["message"]
    assert r["holder"] is True  # the busy path: the SKILL row sends the agent to rerun, not to manual placement
    assert "completedBytes" not in r
    assert srv.requests == []


# --- proxies and flags ------------------------------------------------------------------------------------------------

def test_curl_that_cannot_reach_the_archive_leaves_the_download_to_powershell(archive, blocked_curl, tmp_path):
    # Authenticating proxy or TLS inspection: curl fails every request, PowerShell's HEAD and WebClient get through.
    with ArchiveServer(archive) as srv:
        code, r = run_script(srv, tmp_path / "install", path_prepend=str(blocked_curl))
    assert (code, r["status"], r["source"]) == (0, "ok", "downloaded")
    assert [(m, rng, st) for m, rng, st, _ in srv.requests] == [("HEAD", None, 200), ("GET", None, 200)]
    assert_installed(tmp_path / "install")


def test_check_only_on_an_empty_dir_reports_missing_without_touching_the_network(archive, tmp_path):
    with ArchiveServer(archive) as srv:
        code, r = run_script(srv, tmp_path / "install", "--check-only")
    assert (code, r["status"]) == (3, "missing")
    assert srv.requests == []


def test_force_with_offline_is_refused_without_touching_the_network(archive, tmp_path):
    # OFFLINE=1 promises no network; --force asks for a download. The contradiction is reported, not resolved by downloading.
    install = tmp_path / "install"
    with ArchiveServer(archive) as srv:
        assert run_script(srv, install)[1]["status"] == "ok"
    with ArchiveServer(archive) as srv:
        code, r = run_script(srv, install, "--force", extra_env={"UIPATH_ACTIVITY_MIGRATOR_OFFLINE": "1"})
    assert (code, r["status"], r["code"]) == (1, "error", "offline-missing")
    assert "--force" in r["message"]
    assert srv.requests == []
    assert_installed(install)  # the cached tool is untouched


def test_update_run_is_not_short_circuited_by_the_installed_exe(archive, tmp_path):
    # Updates happen only on the default root (an override dir is never auto-updated), so LOCALAPPDATA points at tmp.
    root = tmp_path / "UiPath" / "ActivityMigrator"
    with ArchiveServer(archive) as srv:
        assert run_script(srv, tmp_path, default_root=True)[1]["source"] == "downloaded"
    (root / ".last-modified").write_text("Mon, 01 Jan 2001 00:00:00 GMT", encoding="ascii")  # the server has a newer archive
    with ArchiveServer(archive) as srv:
        code, r = run_script(srv, tmp_path, default_root=True)
    assert (code, r["status"], r["source"]) == (0, "ok", "updated")
    assert len(srv.ranged_gets()) == 3
    assert (root / ".last-modified").read_text() == srv.last_modified
    assert_installed(root)


# --- one run at a time per install root -------------------------------------------------------------------------------

def test_second_run_started_as_the_zip_appears_waits_and_reuses_the_install(archive, tmp_path):
    # The real extraction takes 40 s; an agent's overlapping second call lands exactly there. The lock must cover the
    # assembled zip, the extraction folder and current\, not only the chunk writes.
    install = tmp_path / "install"
    zip_path = install / "UiPath.Upgrade.Cli.download.zip"
    with ArchiveServer(archive, close_after=2 * MIB) as srv:
        first = launch(srv, install)
        deadline = time.time() + 60
        while not zip_path.exists() and first.poll() is None and time.time() < deadline:
            time.sleep(0.01)
        assert zip_path.exists(), "the first run finished before its zip was observed"
        second = launch(srv, install)
        results = [finish(first), finish(second)]
    assert [(code, r["status"], r["source"]) for code, r in results] == [(0, "ok", "downloaded"), (0, "ok", "cached")]
    assert len(srv.ranged_gets()) == 21  # one download: 8 + 8 requests for the 16 MiB chunks, 5 for the last 8,392,582 bytes
    assert_installed(install)


def hold_lock(install, with_pid_file):
    """A process holding <install>/.lock the way the script does: an exclusive handle, plus the pid sidecar when asked."""
    args = ["node", "-e", HOLD_LOCK_JS, str(install / ".lock")] + ([str(install / ".lock.pid")] if with_pid_file else [])
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.stdout.readline().strip() == "held"
    return proc


def test_lock_is_an_exclusive_handle_the_os_releases_when_the_run_dies(archive, tmp_path):
    # The lock's whole value: no other process can touch it while the holder lives, and nothing survives the holder.
    # A TerminateProcess from the host releases it at once, with no pid to probe and no stale clock to wait out.
    install = tmp_path / "install"
    lock, pid_file = install / ".lock", install / ".lock.pid"
    with ArchiveServer(archive, throttle_after=1, throttle_bps=256 * 1024) as srv:  # slow enough to catch mid-download
        proc = launch(srv, install)
        deadline = time.time() + 30
        while proc.poll() is None and time.time() < deadline and (not pid_file.exists() or pid_file.read_text() != str(proc.pid)):
            time.sleep(0.02)
        assert pid_file.read_text() == str(proc.pid)
        with pytest.raises(PermissionError):
            open(lock, "rb").close()
        with pytest.raises(PermissionError):
            os.remove(lock)
        proc.kill()
        proc.wait()
        open(lock, "rb").close()
        os.remove(lock)


def test_lock_of_a_live_run_is_waited_for_then_reported(archive, tmp_path):
    install = tmp_path / "install"
    install.mkdir()
    holder = hold_lock(install, with_pid_file=True)
    try:
        with ArchiveServer(archive) as srv:
            code, r = run_script(srv, install, extra_env=SHORT_WINDOW)
        assert (code, r["status"], r["code"]) == (1, "error", "download-failed")
        assert r["holder"] == holder.pid
        assert f"process {holder.pid}" in r["message"]
        assert "completedBytes" not in r
        assert srv.ranged_gets() == []
        assert holder.poll() is None  # the holder was left alone
    finally:
        holder.kill()
        holder.wait()
    # Before the holder has written .lock.pid it is still reported, as `true`.
    (install / ".lock.pid").unlink()
    holder = hold_lock(install, with_pid_file=False)
    try:
        with ArchiveServer(archive) as srv:
            code, r = run_script(srv, install, extra_env=SHORT_WINDOW)
        assert (code, r["code"], r["holder"]) == (1, "download-failed", True)
        assert "process" not in r["message"]
    finally:
        holder.kill()
        holder.wait()


def test_leftover_lock_files_of_a_dead_run_do_not_block(archive, tmp_path):
    install = tmp_path / "install"
    install.mkdir()
    (install / ".lock").write_text("", encoding="ascii")
    (install / ".lock.pid").write_text("999999", encoding="ascii")
    started = time.time()
    with ArchiveServer(archive) as srv:
        code, r = run_script(srv, install)
    assert (code, r["status"]) == (0, "ok")
    assert time.time() - started < 30  # nothing held the file, so nothing was waited for
    assert_installed(install)
