#!/usr/bin/env python3
"""Simple webhook receiver for Grafana alerts."""

import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

ALERTS_FILE = os.environ.get("ALERTS_FILE", "/data/alerts.jsonl")
PORT = int(os.environ.get("PORT", "8080"))

class AlertHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(body) if body else {}

            # Extract alert info
            alerts = payload.get("alerts", [payload])

            for alert in alerts:
                record = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "status": alert.get("status", "unknown"),
                    "alertname": alert.get("labels", {}).get("alertname",
                                 payload.get("title", "unknown")),
                    "severity": alert.get("labels", {}).get("severity", "info"),
                    "summary": alert.get("annotations", {}).get("summary", ""),
                    "description": alert.get("annotations", {}).get("description", ""),
                }

                # Log to stdout
                status_icon = "🔴" if record["status"] == "firing" else "✅"
                print(f"{status_icon} [{record['timestamp']}] {record['alertname']}: {record['summary']}")

                # Append to file
                with open(ALERTS_FILE, "a") as f:
                    f.write(json.dumps(record) + "\n")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')

        except Exception as e:
            print(f"Error processing alert: {e}")
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        """Health check endpoint."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

if __name__ == "__main__":
    print(f"🔔 DevOS Alert Webhook listening on port {PORT}")
    print(f"   Alerts will be logged to {ALERTS_FILE}")
    server = HTTPServer(("0.0.0.0", PORT), AlertHandler)
    server.serve_forever()
