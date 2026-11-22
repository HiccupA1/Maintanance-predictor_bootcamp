"""Local stand-in for Supabase Auth, for demos only. Never deploy it.

    python -m tools.demo.auth_stub DEMO_DIR [--port 54321]

It answers the endpoints the frontend calls (password sign-in, refresh,
current user, logout) with the sessions that ``tools.testenv.seed`` wrote to
DEMO_DIR/sessions.json. The API still verifies every token through its real
JWKS path, so authorization behaves exactly as in production.

Demo accounts (password ``demo1234``):
    admin@testenv.invalid               Admin
    plantmanager@testenv.invalid        PlantManager
    operator@testenv.invalid            Operator
    maintenanceengineer@testenv.invalid MaintenanceEngineer
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

PASSWORD = "demo1234"


def make_handler(sessions: dict[str, dict]):
    by_email = {s["user"]["email"]: s for s in sessions.values()}
    by_token = {s["access_token"]: s for s in sessions.values()}
    by_refresh = {s["refresh_token"]: s for s in sessions.values()}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args) -> None:  # quiet
            pass

        def _cors(self) -> None:
            origin = self.headers.get("Origin") or "*"
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header(
                "Access-Control-Allow-Headers",
                "authorization, apikey, content-type, x-client-info, "
                "x-supabase-api-version",
            )
            self.send_header(
                "Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS"
            )

        def _json(self, status: int, body: dict | None = None) -> None:
            data = b"" if body is None else json.dumps(body).encode()
            self.send_response(status)
            self._cors()
            if body is not None:
                self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self) -> dict:
            length = int(self.headers.get("Content-Length") or 0)
            try:
                return json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return {}

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._json(204)

        def do_POST(self) -> None:  # noqa: N802
            url = urlsplit(self.path)
            if url.path.endswith("/auth/v1/token"):
                grant = parse_qs(url.query).get("grant_type", [""])[0]
                body = self._body()
                if grant == "password":
                    session = by_email.get(str(body.get("email", "")).lower())
                    if session and body.get("password") == PASSWORD:
                        return self._json(200, session)
                    return self._json(
                        400,
                        {
                            "error": "invalid_grant",
                            "error_description": "Invalid login credentials",
                        },
                    )
                if grant == "refresh_token":
                    session = by_refresh.get(body.get("refresh_token", ""))
                    if session:
                        return self._json(200, session)
                    return self._json(400, {"error": "invalid_grant"})
            if url.path.endswith("/auth/v1/logout"):
                return self._json(204)
            self._json(404, {"error": "not_found"})

        def do_GET(self) -> None:  # noqa: N802
            if urlsplit(self.path).path.endswith("/auth/v1/user"):
                token = (
                    self.headers.get("Authorization", "")
                    .removeprefix("Bearer ")
                    .strip()
                )
                session = by_token.get(token)
                if session:
                    return self._json(200, session["user"])
                return self._json(401, {"error": "invalid_token"})
            self._json(404, {"error": "not_found"})

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("demo_dir", type=Path)
    parser.add_argument("--port", type=int, default=54321)
    args = parser.parse_args()
    sessions = json.loads((args.demo_dir / "sessions.json").read_text())
    server = ThreadingHTTPServer(
        ("127.0.0.1", args.port), make_handler(sessions)
    )
    print(
        f"Demo auth stub on http://localhost:{args.port} (password {PASSWORD})"
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
