"""Local HTTP Sandbox Server for Browser Tool Advanced Integration Tests.

Runs a multi-threaded HTTP server serving local endpoints simulating
logins, SPA rendering delays, infinite scrolling, file uploads/downloads,
redirects, and server errors.
"""

import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie
from typing import Any

class SandboxHTTPRequestHandler(BaseHTTPRequestHandler):
    """Handler implementing sandbox endpoints for browser action testing."""

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress standard request logs to keep test output clean
        pass

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/login":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
            <!DOCTYPE html>
            <html>
            <head><title>Login Page</title></head>
            <body>
                <h1>Login Form</h1>
                <form action="/login" method="POST">
                    <input type="text" id="username" name="username" placeholder="Username" />
                    <input type="password" id="password" name="password" placeholder="Password" />
                    <input type="checkbox" id="remember" name="remember" /> Remember Me
                    <button type="submit" id="submit-login">Login</button>
                </form>
            </body>
            </html>
            """)

        elif path == "/admin":
            cookie_header = self.headers.get("Cookie", "")
            cookie = SimpleCookie(cookie_header)
            session_id = cookie.get("session-id")

            if session_id and session_id.value == "authenticated-secret":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                <!DOCTYPE html>
                <html>
                <head><title>Admin Panel</title></head>
                <body>
                    <h1>Welcome Admin!</h1>
                    <p id="admin-secret">Dashboard Loaded Successfully.</p>
                </body>
                </html>
                """)
            else:
                self.send_response(403)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>403 Forbidden</h1><p>Invalid Cookie Session.</p>")

        elif path == "/spa":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SPA Delay Demo</title>
                <script>
                    setTimeout(() => {
                        const container = document.getElementById("content-container");
                        container.innerHTML = "<p id='async-loaded'>SPA Content Loaded Dynamically!</p>";
                    }, 1000);
                </script>
            </head>
            <body>
                <h1>Single Page App</h1>
                <div id="content-container"><p id="loading">Loading initial SPA state...</p></div>
            </body>
            </html>
            """)

        elif path == "/infinite-scroll":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Infinite Scroll Demo</title>
                <style>
                    body { height: 2000px; }
                    .item { height: 200px; border: 1px solid #ccc; margin: 10px 0; }
                </style>
                <script>
                    window.addEventListener("scroll", () => {
                        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 50) {
                            const newDiv = document.createElement("div");
                            newDiv.className = "item";
                            newDiv.id = "scroll-target";
                            newDiv.innerText = "Target Scrolled Node Found!";
                            document.body.appendChild(newDiv);
                        }
                    });
                </script>
            </head>
            <body>
                <h1>Scroll down to load items</h1>
                <div class="item">Item 1</div>
                <div class="item">Item 2</div>
            </body>
            </html>
            """)

        elif path == "/download":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-Disposition", 'attachment; filename="download_file.txt"')
            self.end_headers()
            self.wfile.write(b"Production download contents verified.")

        elif path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/login")
            self.end_headers()

        elif path == "/error":
            self.send_response(500)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Internal Server Error</h1>")

        elif path == "/pdf":
            self.send_response(200)
            self.send_header("Content-type", "application/pdf")
            self.end_headers()
            self.wfile.write(b"%PDF-1.4 Mock PDF Content")

        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/login":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = urllib.parse.parse_qs(post_data)

            username = params.get("username", [""])[0]
            password = params.get("password", [""])[0]

            if username == "admin" and password == "secret":
                self.send_response(302)
                cookie = SimpleCookie()
                cookie["session-id"] = "authenticated-secret"
                cookie["session-id"]["path"] = "/"
                self.send_header("Set-Cookie", cookie.output(header=""))
                self.send_header("Location", "/admin")
                self.end_headers()
            else:
                self.send_response(401)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>401 Unauthorized</h1>")

        elif path == "/upload":
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Requires multipart/form-data")
                return

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            # Simple mock checks for the uploaded boundary values
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"File uploaded successfully! Total size: {len(body)} bytes".encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()


class SandboxServer:
    """Manages the lifecycle of a daemonized background HTTPServer instance."""

    def __init__(self) -> None:
        self.server = HTTPServer(("127.0.0.1", 0), SandboxHTTPRequestHandler)
        self.port = self.server.server_port
        self.url = f"http://127.0.0.1:{self.port}"
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the sandbox server in a background daemon thread."""
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop serving and release the allocated network socket."""
        self.server.shutdown()
        self.server.server_close()
        if self._thread:
            self._thread.join()
