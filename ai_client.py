"""
ai_client.py
Unified AI client factory.

Priority order for AI backend:
  1. GitHub Models API  (GITHUB_TOKEN が設定されている場合)
  2. OpenAI API         (OPENAI_API_KEY が設定されている場合)
  3. None              → fallback to pattern-matching / simple scoring

GitHub Models は OpenAI SDK と完全互換のエンドポイントを提供する。
  endpoint : https://models.inference.ai.azure.com
  token    : GitHub Personal Access Token (models:read 権限)
             https://github.com/settings/tokens で発行
"""

import os

GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"

# GitHub Models で利用できる GPT-4o 互換モデル
GITHUB_MODEL = "gpt-4o"
OPENAI_MODEL = "gpt-4o"


def get_client():
    """
    OpenAI クライアントを返す。
    利用できる場合は GitHub Models を優先する。

    Returns:
        (client, model_name) のタプル。
        クライアントが作れない場合は (None, None) を返す。
    """
    from openai import OpenAI

    # ── 1. GitHub Models (GitHub Copilot ユーザーに推奨) ──────────────────
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if github_token:
        client = OpenAI(
            base_url=GITHUB_MODELS_ENDPOINT,
            api_key=github_token,
        )
        return client, GITHUB_MODEL

    # ── 2. OpenAI API ─────────────────────────────────────────────────────
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        client = OpenAI(api_key=openai_key)
        return client, OPENAI_MODEL

    # ── 3. No AI available ────────────────────────────────────────────────
    return None, None


def get_backend_name() -> str:
    """現在使用中の AI バックエンド名を返す（UI 表示用）。"""
    if os.environ.get("GITHUB_TOKEN"):
        return "GitHub Models (gpt-4o)"
    if os.environ.get("OPENAI_API_KEY"):
        return "OpenAI API (gpt-4o)"
    return "Pattern matching (no AI)"
