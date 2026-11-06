"""Local server:  python server.py  ->  http://localhost:3000  (no dependencies)"""
import json, os, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "api"))
from simplify import run  # noqa: E402


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=os.path.join(ROOT, "frontend"), **k)

    def do_POST(self):
        if self.path != "/api/simplify":
            return self.send_error(404)
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            out, code = run(body), 200
        except (ValueError, KeyError, TypeError) as e:
            out, code = {"error": str(e)}, 400
        data = json.dumps(out).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"Dashboard running at http://localhost:{port}")
    ThreadingHTTPServer(("", port), Handler).serve_forever()
