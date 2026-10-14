"""Tiny web app. Only Python's built-in libraries are used."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
import os

PORT = int(os.environ.get("PORT", "8080"))
COUNTER = 0
LOCK = Lock()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global COUNTER
        if self.path == "/health":
            body, content_type, status = b"OK\n", "text/plain", 200
        elif self.path == "/metrics":
            with LOCK:
                count = COUNTER
            body = ("# HELP demo_requests_total Requests to the home page\n"
                    "# TYPE demo_requests_total counter\n"
                    f"demo_requests_total {count}\n").encode()
            content_type, status = "text/plain; version=0.0.4", 200
        elif self.path == "/":
            with LOCK:
                COUNTER += 1
                count = COUNTER
            body = ("<!doctype html><html><head><title>DevOps Class</title></head>"
                    "<body style='font-family:Arial;max-width:650px;margin:70px auto'>"
                    "<h1>Welcome to the DevOps Class!</h1>"
                    "<p>Our simple app is running inside Kubernetes.</p>"
                    f"<p>Home page visits on this pod: <b>{count}</b></p>"
                    "<p>Try <a href='/health'>/health</a> and "
                    "<a href='/metrics'>/metrics</a>.</p></body></html>").encode()
            content_type, status = "text/html; charset=utf-8", 200
        else:
            body, content_type, status = b"Not found\n", "text/plain", 404
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    print(f"Listening on {PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
