from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path


class LLMError(RuntimeError):
    """大模型调用失败时抛出的统一异常。"""


class LLMConfigError(LLMError):
    """大模型环境变量配置缺失时抛出的异常。"""


def chat_completion(messages: list[dict[str, str]], *, temperature: float = 0.7) -> str:
    """调用 OpenAI-compatible Chat Completions 接口生成回复。

    需要在环境变量中配置：
    - OPENAI_API_KEY：API 密钥
    - OPENAI_MODEL：模型名称
    - OPENAI_BASE_URL：可选，默认 https://api.openai.com/v1
    """

    load_local_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    if not api_key:
        raise LLMConfigError("缺少 OPENAI_API_KEY，请先配置大模型 API Key。")
    if not model:
        raise LLMConfigError("缺少 OPENAI_MODEL，请先配置要调用的模型名称。")

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    request = urllib.request.Request(
        url=f"{base_url}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise LLMError(f"大模型接口返回 HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise LLMError(f"无法连接大模型接口: {exc.reason}") from exc

    data = json.loads(raw)
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"大模型返回格式不符合预期: {raw}") from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMError("大模型返回了空回复。")
    return content.strip()


def load_local_env() -> None:
    """读取项目根目录的 .env 文件，已存在的系统环境变量优先。"""

    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
