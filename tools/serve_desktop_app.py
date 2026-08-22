#!/usr/bin/env python3
"""Serve the SoloForge desktop MVP over local HTTP."""

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "desktop"


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve apps/desktop for local browser testing.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Open the app in the default browser.")
    args = parser.parse_args()

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(APP_DIR))
    url = f"http://{args.host}:{args.port}/"

    with ReusableTCPServer((args.host, args.port), handler) as server:
        print(f"Serving SoloForge from {APP_DIR}")
        print(url)
        if args.open:
            webbrowser.open(url)
        server.serve_forever()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
