from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from engine import generate_agent_reply, opening_message
from experiment import public_config
from llm_client import LLMConfigError, LLMError
from storage import append_interaction, read_recent, read_session


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"


class AppHandler(BaseHTTPRequestHandler):
    server_version = "TeachableAICoding/1.0"

    def do_GET(self) -> None:
        # 用 Python 标准库同时提供前端页面和 JSON 接口，
        # 让工程保持零第三方依赖。
        path = urlparse(self.path).path
        if path == "/":
            self._send_file(STATIC_DIR / "index.html")
            return
        if path == "/api/config":
            self._send_json(public_config())
            return
        if path == "/api/logs":
            self._send_json({"items": read_recent(100)})
            return
        if path.startswith("/static/"):
            self._send_file(STATIC_DIR / path.replace("/static/", "", 1))
            return
        self._send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        # 原型只需要两个写入接口：
        # 一个创建会话，一个把每轮学生-智能体互动追加到 JSONL 日志。
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/session":
                self._handle_session(payload)
                return
            if path == "/api/message":
                self._handle_message(payload)
                return
            self._send_error(HTTPStatus.NOT_FOUND, "Not found")
        except LLMConfigError as exc:
            self._send_error(HTTPStatus.PRECONDITION_FAILED, str(exc))
        except LLMError as exc:
            self._send_error(HTTPStatus.BAD_GATEWAY, str(exc))
        except ValueError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def log_message(self, format: str, *args: object) -> None:
        safe_print(f"[server] {self.address_string()} - {format % args}")

    def _handle_session(self, payload: dict[str, object]) -> None:
        personality = str(payload.get("personality", "neutral"))
        task = str(payload.get("task", "dedupe"))
        participant_id = str(payload.get("participant_id") or "anonymous")
        session_id = str(uuid.uuid4())
        message = opening_message(personality, task)
        self._send_json(
            {
                "session_id": session_id,
                "participant_id": participant_id,
                "personality": personality,
                "task": task,
                "turn_id": 0,
                "agent_message": message,
            }
        )

    def _handle_message(self, payload: dict[str, object]) -> None:
        session_id = str(payload.get("session_id") or uuid.uuid4())
        participant_id = str(payload.get("participant_id") or "anonymous")
        personality = str(payload.get("personality", "neutral"))
        task = str(payload.get("task", "dedupe"))
        student_message = str(payload.get("message") or "")
        turn_id = int(payload.get("turn_id") or 0)

        if not student_message.strip():
            raise ValueError("message cannot be empty")

        history = read_session(session_id, limit=8)
        agent_message, features = generate_agent_reply(
            personality_key=personality,
            task_key=task,
            student_message=student_message,
            turn_id=turn_id,
            history=history,
        )
        # 同时保存原始对话和规则编码结果，
        # 后续分析时既可以看原文，也可以直接使用预计算特征。
        record = {
            "participant_id": participant_id,
            "session_id": session_id,
            "personality": personality,
            "task_id": task,
            "turn_id": turn_id,
            "student_message": student_message,
            "agent_message": agent_message,
            **features,
        }
        append_interaction(record)
        self._send_json({"agent_message": agent_message, "turn_id": turn_id + 1, "features": features})

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        if not raw:
            return {}
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("JSON payload must be an object")
        return data

    def _send_json(self, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        resolved = path.resolve()
        # 限制静态文件只能从 static 目录读取，
        # 防止构造路径访问工程外部文件。
        if not str(resolved).startswith(str(STATIC_DIR.resolve())) or not resolved.exists():
            self._send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        body = resolved.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        body = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the teachable AI coding personality lab.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", default=int(os.environ.get("PORT", "8000")), type=int)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    safe_print(f"Teachable AI Coding Lab is running at http://{args.host}:{args.port}")
    safe_print("Press Ctrl+C to stop.")
    server.serve_forever()


def safe_print(message: str) -> None:
    if sys.stdout is not None:
        print(message, flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log_path = ROOT / "data" / "server-error.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        raise
