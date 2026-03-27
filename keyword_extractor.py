"""
keyword_extractor.py
Uses OpenAI GPT to extract smart search keywords from the user's profile.
Supports GitHub Models API (GITHUB_TOKEN) and OpenAI API (OPENAI_API_KEY).
Falls back to simple regex extraction if neither key is set.
"""

import os
import re


def _simple_keyword_extract(profile: dict) -> list[str]:
    """
    Fallback: extract likely job keywords from profile text without AI.
    Returns a list of keyword strings to search on Green.
    """
    combined = (
        profile["resume_text"] + " " + profile["situation"] + " " + profile["hope"]
    )
    # Common Japanese IT / business job keywords
    patterns = [
        r"\bPython\b", r"\bJava\b", r"\bReact\b", r"\bNode\.js\b", r"\bTypeScript\b",
        r"\bAWS\b", r"\bAzure\b", r"\bGCP\b", r"\bDocker\b", r"\bKubernetes\b",
        r"\bML\b", r"\bAI\b", r"\bデータサイエンティスト\b", r"\bエンジニア\b",
        r"\bバックエンド\b", r"\bフロントエンド\b", r"\bフルスタック\b",
        r"\b営業\b", r"\bマーケティング\b", r"\b人事\b", r"\bデザイナー\b",
        r"\bプロジェクトマネージャー\b", r"\bPM\b", r"\bコンサルタント\b",
        r"\bリモート\b", r"\bremote\b",
    ]
    found = []
    for p in patterns:
        if re.search(p, combined, re.IGNORECASE):
            # Clean up the pattern to a readable keyword
            kw = p.replace(r"\b", "").replace("\\.", ".").replace("\\", "")
            found.append(kw)
    # Also grab words from 'hope' directly
    hope_words = re.findall(r"[\w]+", profile["hope"])
    found.extend([w for w in hope_words if len(w) >= 3])
    # Deduplicate preserving order
    seen = set()
    result = []
    for k in found:
        k_lower = k.lower()
        if k_lower not in seen:
            seen.add(k_lower)
            result.append(k)
    return result[:10]  # top 10


def extract_keywords_with_ai(profile: dict) -> list[str]:
    """
    AI (GitHub Models or OpenAI) でキーワードを抽出する。
    キーが設定されていない場合は正規表現フォールバックを使用。
    """
    from ai_client import get_client, get_backend_name

    client, model = get_client()
    if client is None:
        print(f"[keyword_extractor] AI not configured ({get_backend_name()}), using simple extraction.")
        return _simple_keyword_extract(profile)

    print(f"[keyword_extractor] Using {get_backend_name()}")

    system_prompt = (
        "You are a Japanese job-search assistant. "
        "Given a resume, a current situation, and a job hope, "
        "extract 5-8 concise search keywords suitable for the Green Japan job site "
        "(https://www.green-japan.com). "
        "Return ONLY a JSON array of strings, e.g. [\"Python\", \"バックエンド\", \"リモート\"]. "
        "Mix Japanese and English keywords as appropriate."
    )
    user_content = (
        f"## Resume\n{profile['resume_text'][:3000]}\n\n"
        f"## Current Situation\n{profile['situation']}\n\n"
        f"## Job Hope\n{profile['hope']}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        import json
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        keywords = json.loads(raw)
        if isinstance(keywords, list):
            return [str(k) for k in keywords]
    except Exception as e:
        print(f"[keyword_extractor] AI call failed ({e}), using simple extraction.")

    return _simple_keyword_extract(profile)
