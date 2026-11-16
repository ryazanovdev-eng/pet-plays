#!/usr/bin/env python3
"""Проверка MCP-сервера по stdio: initialize, tools/list и опционально tools/call.

Примеры:
    python tools/mcp_probe.py --name godot -- cmd /c npx -y @coding-solo/godot-mcp
    python tools/mcp_probe.py --name blender -- "C:\\path\\uvx.exe" mcp-for-blender
    python tools/mcp_probe.py --name godot --call get_godot_version -- cmd /c npx -y @coding-solo/godot-mcp
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "2024-11-05"


def pump_stdout(stream, sink: queue.Queue[str]) -> None:
    for line in stream:
        line = line.lstrip("\ufeff").rstrip("\r\n")
        if line:
            sink.put(line)


def pump_stderr(stream, sink: list[str]) -> None:
    for line in stream:
        line = line.rstrip("\r\n")
        if line:
            sink.append(line)


class McpClient:
    def __init__(self, command: list[str], env: dict[str, str], timeout: float) -> None:
        self.timeout = timeout
        self.stdout: queue.Queue[str] = queue.Queue()
        self.stderr: list[str] = []
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )
        threading.Thread(target=pump_stdout, args=(self.process.stdout, self.stdout), daemon=True).start()
        threading.Thread(target=pump_stderr, args=(self.process.stderr, self.stderr), daemon=True).start()

    def send(self, message: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def receive(self, timeout: float | None = None) -> dict[str, Any]:
        deadline = time.time() + (timeout if timeout is not None else self.timeout)
        while time.time() < deadline:
            try:
                line = self.stdout.get(timeout=0.2)
            except queue.Empty:
                if self.process.poll() is not None:
                    raise RuntimeError(f"сервер завершился с кодом {self.process.returncode}")
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                self.stderr.append(f"stdout (не JSON): {line}")
        raise TimeoutError(f"нет ответа за {timeout or self.timeout} с")

    def request(self, request_id: int, method: str, params: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        self.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.time() + (timeout if timeout is not None else self.timeout)
        while time.time() < deadline:
            message = self.receive(max(1.0, deadline - time.time()))
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message
        raise TimeoutError(f"{method}: нет ответа")

    def notify(self, method: str) -> None:
        self.send({"jsonrpc": "2.0", "method": method})

    def stop(self) -> None:
        if self.process.poll() is not None:
            return
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            self.process.terminate()


def parse_env(values: list[str]) -> dict[str, str]:
    env = os.environ.copy()
    for item in values:
        if "=" not in item:
            raise SystemExit(f"--env ожидает KEY=VALUE, получено: {item}")
        key, value = item.split("=", 1)
        env[key] = value
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверка MCP-сервера по stdio")
    parser.add_argument("--name", default="server", help="имя сервера для вывода")
    parser.add_argument("--timeout", type=float, default=120.0, help="таймаут, секунды")
    parser.add_argument("--env", action="append", default=[], help="переменная окружения KEY=VALUE")
    parser.add_argument("--call", help="вызвать инструмент после tools/list")
    parser.add_argument("--args", default="{}", help="JSON-аргументы для --call")
    parser.add_argument("--args-file", help="файл с JSON-аргументами для --call")
    parser.add_argument("--details", action="store_true", help="показать аргументы инструментов")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="команда запуска после --")
    args = parser.parse_args()

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("нужна команда запуска после --")

    try:
        if args.args_file:
            call_args = json.loads(Path(args.args_file).read_text(encoding="utf-8"))
        else:
            call_args = json.loads(args.args)
    except (OSError, json.JSONDecodeError) as error:
        parser.error(f"аргументы должны быть JSON: {error}")

    client = McpClient(command, parse_env(args.env), args.timeout)
    try:
        init = client.request(
            1,
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "pet-plays-mcp-probe", "version": "1.0"},
            },
        )
        client.notify("notifications/initialized")
        tools_response = client.request(2, "tools/list", {})
    except Exception as error:
        print(f"[{args.name}] ОШИБКА: {error}", file=sys.stderr)
        for line in client.stderr[-20:]:
            print(f"[{args.name}] stderr: {line}", file=sys.stderr)
        client.stop()
        return 1

    info = init.get("result", {}).get("serverInfo", {})
    protocol = init.get("result", {}).get("protocolVersion", "?")
    tools = tools_response.get("result", {}).get("tools", [])
    print(f"[{args.name}] подключено: {info.get('name', '?')} {info.get('version', '')}".strip())
    print(f"[{args.name}] протокол: {protocol}")
    print(f"[{args.name}] инструментов: {len(tools)}")
    for tool in tools:
        description = (tool.get("description") or "").replace("\n", " ")[:90]
        print(f"  - {tool.get('name')}: {description}")
        if args.details:
            schema = tool.get("inputSchema", {}) or {}
            properties = schema.get("properties", {}) or {}
            required = set(schema.get("required", []) or [])
            if properties:
                names = ", ".join(
                    f"{name}{'*' if name in required else ''}" for name in properties
                )
                print(f"      аргументы: {names}")

    exit_code = 0
    if args.call:
        try:
            result = client.request(
                3,
                "tools/call",
                {"name": args.call, "arguments": call_args},
            )
            print(f"[{args.name}] вызов {args.call}:")
            print(json.dumps(result.get("result", result), ensure_ascii=False, indent=2))
        except Exception as error:
            print(f"[{args.name}] ОШИБКА вызова {args.call}: {error}", file=sys.stderr)
            for line in client.stderr[-20:]:
                print(f"[{args.name}] stderr: {line}", file=sys.stderr)
            exit_code = 1

    client.stop()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
