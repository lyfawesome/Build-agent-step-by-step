"""读取已配置的 DeepSeek API，写法与参考项目 providers.py 类似。"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def _load_deepseek_environment() -> tuple[str, str, str, str]:
    # 从当前脚本逐级向上找 .env.local。
    for parent in Path(__file__).resolve().parents:
        env_file = parent / ".env.local"
        if env_file.is_file():
            load_dotenv(env_file)
            break

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError("没有找到 DEEPSEEK_API_KEY")

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    thinking = os.getenv("DEEPSEEK_THINKING", "disabled")
    return api_key, base_url, model, thinking


def get_chat_client():
    api_key, base_url, model, thinking = _load_deepseek_environment()

    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model, thinking


def get_langchain_chat_model():
    """返回使用同一 DeepSeek 配置的 LangChain ChatOpenAI 实例。"""

    from langchain_openai import ChatOpenAI

    api_key, base_url, model, thinking = _load_deepseek_environment()
    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0,
        extra_body={"thinking": {"type": thinking}},
    )
