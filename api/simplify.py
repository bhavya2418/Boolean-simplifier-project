"""Vercel serverless function: POST /api/simplify  {num_vars, minterms, dont_cares}"""
import json, os, sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from qm_solver import simplify  # noqa: E402


def run(payload: dict) -> dict:
    ints = lambda k: [int(x) for x in payload.get(k, [])]
    return simplify(int(payload["num_vars"]), ints("minterms"), ints("dont_cares"))


class handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            self._send(200, run(json.loads(self.rfile.read(length) or b"{}")))
        except (ValueError, KeyError, TypeError) as e:
            self._send(400, {"error": str(e)})
