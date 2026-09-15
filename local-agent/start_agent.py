from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def port_ready(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    url = f"http://127.0.0.1:{args.port}/"
    if port_ready(args.port):
        if not args.no_browser:
            webbrowser.open(url)
        print(url)
        return 0
    process = subprocess.Popen([sys.executable, str(ROOT / "app.py"), "--port", str(args.port)], cwd=ROOT)
    for _ in range(40):
        if port_ready(args.port):
            if not args.no_browser:
                webbrowser.open(url)
            print(url)
            return process.wait()
        if process.poll() is not None:
            return process.returncode or 1
        time.sleep(0.25)
    process.terminate()
    print("Không khởi động được localhost trong 10 giây", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

