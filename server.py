#!/usr/bin/env python3
"""Serve the environment report and expose host details to the browser."""

import json
import mimetypes
import os
import platform
import re
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent.resolve()
PORT = int(os.environ.get("PORT", "3000"))


def read_os_release():
    values = {}
    try:
        lines = Path("/etc/os-release").read_text(encoding="utf-8").splitlines()
    except OSError:
        return values

    for line in lines:
        match = re.match(r"^([A-Z_]+)=(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip('"')
    return values


def detect_wsl():
    kernel = f"{platform.release()} {platform.version()}"
    is_wsl = bool(
        os.environ.get("WSL_INTEROP")
        or os.environ.get("WSL_DISTRO_NAME")
        or re.search(r"microsoft|wsl", kernel, re.IGNORECASE)
    )
    return {
        "isWsl": is_wsl,
        "version": 2 if is_wsl and re.search(r"microsoft-standard|wsl2", kernel, re.IGNORECASE) else (1 if is_wsl else None),
        "distro": os.environ.get("WSL_DISTRO_NAME"),
    }


def detect_browser(user_agent):
    patterns = (
        ("Edge", r"Edg(?:e|A|iOS)?/([\d.]+)"),
        ("Opera", r"OPR/([\d.]+)"),
        ("Chrome", r"(?:Chrome|CriOS)/([\d.]+)"),
        ("Firefox", r"(?:Firefox|FxiOS)/([\d.]+)"),
        ("Safari", r"Version/([\d.]+).*Safari"),
    )
    for name, pattern in patterns:
        match = re.search(pattern, user_agent, re.IGNORECASE)
        if match:
            return {"name": name, "version": match.group(1)}
    return {"name": "Unknown browser", "version": ""}


def environment_for(handler):
    os_release = read_os_release()
    wsl = detect_wsl()
    distro = wsl["distro"] or os_release.get("PRETTY_NAME") or os_release.get("NAME") or "Linux"
    kernel = platform.release()

    return {
        "os": {
            "name": "Linux (WSL)" if wsl["isWsl"] else os_release.get("PRETTY_NAME", platform.system()),
            "platform": platform.system().lower(),
            "version": os_release.get("VERSION_ID", ""),
            "architecture": platform.machine(),
        },
        "wsl": {
            "isWsl": wsl["isWsl"],
            "version": wsl["version"],
            "distro": distro,
        },
        "kernel": kernel,
        "browser": detect_browser(handler.headers.get("User-Agent", "")),
        "client": {"userAgent": handler.headers.get("User-Agent", "")},
        "checkedAt": datetime.now(timezone.utc).isoformat(),
    }


class ReportHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        request_path = urlparse(self.path).path
        if request_path == "/api/environment":
            self.send_json(environment_for(self))
            return

        requested_path = "index.html" if request_path == "/" else request_path.lstrip("/")
        file_path = (ROOT / requested_path).resolve()
        if ROOT not in file_path.parents:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        try:
            content = file_path.read_bytes()
        except OSError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)

    def send_json(self, value):
        content = json.dumps(value).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), ReportHandler)
    print(f"Server listening on http://localhost:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
