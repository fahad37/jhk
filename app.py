import os
import json
import base64
import smtplib
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

DATA_PATH = os.path.join(os.getcwd(), "smtp.json")

def read_data():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def write_data(items):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f)

class Handler(BaseHTTPRequestHandler):
    def _send(self, code=200, content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def do_GET(self):
        p = urlparse(self.path)
        if p.path == "/":
            try:
                with open(os.path.join(os.getcwd(), "templates", "index.html"), "rb") as f:
                    data = f.read()
                self._send(200, "text/html; charset=utf-8")
                self.wfile.write(data)
            except Exception:
                self._send(404, "text/plain")
                self.wfile.write(b"Not found")
            return
        if p.path == "/api/smtp":
            items = read_data()
            for it in items:
                if "passwordEnc" in it:
                    it["passwordEnc"] = "***"
            self._send(200, "application/json")
            self.wfile.write(json.dumps(items).encode("utf-8"))
            return
        self._send(404, "text/plain")
        self.wfile.write(b"Not found")

    def do_POST(self):
        p = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        data = {}
        try:
            data = json.loads(body)
        except Exception:
            pass
        if p.path == "/api/smtp":
            host = data.get("host")
            port = int(data.get("port", 587))
            username = data.get("username")
            password = data.get("password")
            secure = bool(data.get("secure", True))
            daily_limit = int(data.get("dailyLimit", 1000))
            if not host or not port or not username or not password:
                self._send(400)
                self.wfile.write(json.dumps({"error": "Missing required fields"}).encode("utf-8"))
                return
            items = read_data()
            new_id = (items[-1]["id"] + 1) if items else 1
            items.append({
                "id": new_id,
                "host": host,
                "port": port,
                "username": username,
                "passwordEnc": base64.b64encode(password.encode("utf-8")).decode("utf-8"),
                "secure": secure,
                "daily_limit": daily_limit
            })
            write_data(items)
            self._send(201)
            self.wfile.write(json.dumps({"ok": True, "id": new_id}).encode("utf-8"))
            return
        if p.path == "/api/smtp/test":
            idv = data.get("id")
            items = read_data()
            target = None
            for it in items:
                if str(it["id"]) == str(idv):
                    target = it
                    break
            if not target:
                self._send(404)
                self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))
                return
            host = target["host"]
            port = int(target["port"])
            username = target["username"]
            password = base64.b64decode(target["passwordEnc"].encode("utf-8")).decode("utf-8")
            secure = bool(target["secure"])
            try:
                if secure:
                    with smtplib.SMTP_SSL(host=host, port=port, timeout=12) as s:
                        s.login(username, password)
                else:
                    with smtplib.SMTP(host=host, port=port, timeout=12) as s:
                        s.starttls()
                        s.login(username, password)
                self._send(200)
                self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
            except Exception as e:
                self._send(400)
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            return
        self._send(404, "text/plain")
        self.wfile.write(b"Not found")

    def do_DELETE(self):
        p = urlparse(self.path)
        if p.path.startswith("/api/smtp/"):
            try:
                idv = int(p.path.split("/")[-1])
            except Exception:
                idv = None
            if idv is None:
                self._send(400)
                self.wfile.write(json.dumps({"error": "Bad id"}).encode("utf-8"))
                return
            items = read_data()
            items = [it for it in items if it["id"] != idv]
            write_data(items)
            self._send(200)
            self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
            return
        self._send(404, "text/plain")
        self.wfile.write(b"Not found")

def main():
    server = HTTPServer(("127.0.0.1", 8000), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
