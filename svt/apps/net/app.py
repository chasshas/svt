"""SVT Net App - Networking utilities."""

import base64
import socket
import subprocess
import urllib.parse
import urllib.request
import urllib.error
import ssl
import json as _json
import re
from svt.sdk import SVTApp, CommandResult, ExecutionContext


class NetApp(SVTApp):

    # ── HTTP GET ──────────────────────────────────────────────────────────────

    def cmd_get(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: net:get <url>")
        url = str(ctx.args[0])
        timeout = int(ctx.options.get("timeout", 10))
        show_headers = ctx.options.get("headers", False)
        return_status = ctx.options.get("status", False)
        insecure = ctx.options.get("insecure", False)

        ssl_ctx = self._ssl_context(insecure)
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
                status = resp.status
                if show_headers:
                    for k, v in resp.headers.items():
                        print(f"  {k}: {v}")
                body = resp.read().decode("utf-8", errors="replace")
            if return_status:
                print(f"  {status}")
                return CommandResult.success(value=status)
            print(body)
            return CommandResult.success(value=body)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if return_status:
                print(f"  {e.code}")
                return CommandResult.success(value=e.code)
            return CommandResult.error(f"HTTP {e.code}: {e.reason}")
        except Exception as e:
            return CommandResult.error(str(e))

    # ── HTTP POST ─────────────────────────────────────────────────────────────

    def cmd_post(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: net:post <url> [--data body | --json body]")
        url = str(ctx.args[0])
        timeout = int(ctx.options.get("timeout", 10))
        return_status = ctx.options.get("status", False)
        insecure = ctx.options.get("insecure", False)
        json_body = ctx.options.get("json", None)
        raw_data = ctx.options.get("data", None)

        ssl_ctx = self._ssl_context(insecure)
        if json_body is not None:
            data = str(json_body).encode("utf-8")
            content_type = "application/json"
        elif raw_data is not None:
            data = str(raw_data).encode("utf-8")
            content_type = "application/x-www-form-urlencoded"
        else:
            data = b""
            content_type = "application/x-www-form-urlencoded"

        try:
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", content_type)
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
                status = resp.status
                body = resp.read().decode("utf-8", errors="replace")
            if return_status:
                print(f"  {status}")
                return CommandResult.success(value=status)
            print(body)
            return CommandResult.success(value=body)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if return_status:
                print(f"  {e.code}")
                return CommandResult.success(value=e.code)
            return CommandResult.error(f"HTTP {e.code}: {e.reason}")
        except Exception as e:
            return CommandResult.error(str(e))

    # ── HTTP HEADERS ──────────────────────────────────────────────────────────

    def cmd_headers(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: net:headers <url>")
        url = str(ctx.args[0])
        timeout = int(ctx.options.get("timeout", 10))
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = {}
                for k, v in resp.headers.items():
                    print(f"  {k}: {v}")
                    result[k] = v
            return CommandResult.success(value=result)
        except urllib.error.HTTPError as e:
            result = {}
            for k, v in e.headers.items():
                print(f"  {k}: {v}")
                result[k] = v
            return CommandResult.success(value=result)
        except Exception as e:
            return CommandResult.error(str(e))

    # ── DNS RESOLVE ───────────────────────────────────────────────────────────

    def cmd_resolve(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: net:resolve <hostname>")
        host = str(ctx.args[0])
        try:
            infos = socket.getaddrinfo(host, None)
            seen = []
            for info in infos:
                addr = info[4][0]
                if addr not in seen:
                    seen.append(addr)
            for addr in seen:
                print(f"  {addr}")
            return CommandResult.success(value=seen)
        except socket.gaierror as e:
            return CommandResult.error(f"DNS resolution failed: {e}")

    # ── PING ──────────────────────────────────────────────────────────────────

    def cmd_ping(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: net:ping <host>")
        host = str(ctx.args[0])
        count = int(ctx.options.get("count", 4))
        try:
            result = subprocess.run(
                ["ping", "-c", str(count), host],
                capture_output=True, text=True, timeout=count * 5 + 5
            )
            output = result.stdout
            print(output.rstrip())
            avg = self._parse_ping_avg(output)
            if avg is not None:
                return CommandResult.success(value=avg)
            if result.returncode != 0:
                return CommandResult.error(f"Ping failed: {result.stderr.strip() or 'host unreachable'}")
            return CommandResult.success(value=None)
        except subprocess.TimeoutExpired:
            return CommandResult.error("Ping timed out")
        except FileNotFoundError:
            return CommandResult.error("ping command not found on this system")
        except Exception as e:
            return CommandResult.error(str(e))

    # ── PORT SCAN ─────────────────────────────────────────────────────────────

    def cmd_scan(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: net:scan <host> [--ports 1-1024] [--timeout 0.5]")
        host = str(ctx.args[0])
        ports_opt = str(ctx.options.get("ports", "1-1024"))
        per_timeout = float(ctx.options.get("timeout", 0.5))

        start, end = self._parse_port_range(ports_opt)
        if start is None:
            return CommandResult.error(f"Invalid port spec: {ports_opt}. Use '80' or '20-1024'.")

        open_ports = []
        for port in range(start, end + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(per_timeout)
                if s.connect_ex((host, port)) == 0:
                    service = self._port_service(port)
                    label = f"{port}/tcp  open  {service}" if service else f"{port}/tcp  open"
                    print(f"  {label}")
                    open_ports.append(port)

        if not open_ports:
            print(f"  No open ports found on {host} ({ports_opt})")
        return CommandResult.success(value=open_ports)

    # ── LOCAL / PUBLIC IP ─────────────────────────────────────────────────────

    def cmd_ip(self, ctx: ExecutionContext) -> CommandResult:
        want_public = ctx.options.get("public", False)
        want_local = ctx.options.get("local", False)
        # default: show both
        if not want_public and not want_local:
            want_public = True
            want_local = True

        result = {}

        if want_local:
            local_ip = self._local_ip()
            print(f"  local:  {local_ip}")
            result["local"] = local_ip

        if want_public:
            public_ip = self._public_ip()
            if public_ip:
                print(f"  public: {public_ip}")
                result["public"] = public_ip
            else:
                print("  public: (unavailable)")
                result["public"] = None

        return CommandResult.success(value=result)

    # ── DOWNLOAD ──────────────────────────────────────────────────────────────

    def cmd_download(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: net:download <url> <dest>")
        url = str(ctx.args[0])
        dest = str(ctx.args[1])
        timeout = int(ctx.options.get("timeout", 30))
        insecure = ctx.options.get("insecure", False)
        ssl_ctx = self._ssl_context(insecure)
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
                content = resp.read()
            with open(dest, "wb") as f:
                f.write(content)
            size = len(content)
            print(f"  Saved {size} bytes → {dest}")
            return CommandResult.success(value=size)
        except Exception as e:
            return CommandResult.error(str(e))

    # ── URL ENCODE / DECODE ───────────────────────────────────────────────────

    def cmd_urlencode(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: net:urlencode <text>")
        text = str(ctx.args[0])
        encoded = urllib.parse.quote(text, safe="")
        print(encoded)
        return CommandResult.success(value=encoded)

    def cmd_urldecode(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: net:urldecode <text>")
        text = str(ctx.args[0])
        decoded = urllib.parse.unquote(text)
        print(decoded)
        return CommandResult.success(value=decoded)

    # ── BASE64 ────────────────────────────────────────────────────────────────

    def cmd_base64enc(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: net:base64enc <text>")
        text = str(ctx.args[0])
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        print(encoded)
        return CommandResult.success(value=encoded)

    def cmd_base64dec(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: net:base64dec <text>")
        text = str(ctx.args[0])
        try:
            decoded = base64.b64decode(text).decode("utf-8", errors="replace")
            print(decoded)
            return CommandResult.success(value=decoded)
        except Exception as e:
            return CommandResult.error(f"Base64 decode failed: {e}")

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _ssl_context(insecure: bool):
        if insecure:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx
        return None

    @staticmethod
    def _parse_ping_avg(output: str):
        # macOS/Linux: "round-trip min/avg/max/stddev = 1.234/2.345/3.456/0.123 ms"
        m = re.search(r"[\d.]+/([\d.]+)/[\d.]+", output)
        if m:
            return float(m.group(1))
        return None

    @staticmethod
    def _parse_port_range(spec: str):
        spec = spec.strip()
        if "-" in spec:
            parts = spec.split("-", 1)
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                return None, None
        try:
            p = int(spec)
            return p, p
        except ValueError:
            return None, None

    @staticmethod
    def _port_service(port: int) -> str:
        well_known = {
            21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
            80: "http", 110: "pop3", 143: "imap", 443: "https", 465: "smtps",
            587: "submission", 993: "imaps", 995: "pop3s", 3306: "mysql",
            5432: "postgresql", 6379: "redis", 8080: "http-alt", 8443: "https-alt",
            27017: "mongodb",
        }
        return well_known.get(port, "")

    @staticmethod
    def _local_ip() -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    @staticmethod
    def _public_ip() -> str:
        for url in ("https://api.ipify.org", "https://icanhazip.com"):
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return resp.read().decode().strip()
            except Exception:
                continue
        return ""