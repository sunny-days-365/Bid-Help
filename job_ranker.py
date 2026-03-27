"""
job_ranker.py
Ranks scraped jobs by relevance to the user's profile.
Supports GitHub Models API (GITHUB_TOKEN) and OpenAI API (OPENAI_API_KEY).
Falls back to keyword-overlap scoring if neither key is set.
"""

import os
import re


def _keyword_score(job: dict, profile: dict) -> float:
    """Simple keyword overlap scoring (fallback)."""
    combined_profile = (
        profile["resume_text"] + " " + profile["situation"] + " " + profile["hope"]
    ).lower()
    job_text = (job.get("title", "")).lower()
    words = re.findall(r"\w+", job_text)
    score = sum(1 for w in words if len(w) >= 3 and w in combined_profile)
    return score


def rank_jobs_simple(jobs: list[dict], profile: dict, top_n: int = 20) -> list[dict]:
    """Rank jobs by simple keyword overlap score."""
    scored = [(job, _keyword_score(job, profile)) for job in jobs]
    scored.sort(key=lambda x: x[1], reverse=True)
    ranked = []
    for job, score in scored[:top_n]:
        ranked.append({**job, "score": score})
    return ranked


def rank_jobs_with_ai(jobs: list[dict], profile: dict, top_n: int = 20) -> list[dict]:
    """
    AI (GitHub Models or OpenAI) で求人をランク付けする。
    キーが設定されていない場合はキーワードスコアでソート。
    """
    from ai_client import get_client, get_backend_name

    client, model = get_client()
    if client is None or len(jobs) == 0:
        return rank_jobs_simple(jobs, profile, top_n)

    print(f"[ranker] Using {get_backend_name()}")

    candidates = jobs[:50]
    jobs_text = "\n".join(
        f"{i+1}. {j['title']} | {j['url']}" for i, j in enumerate(candidates)
    )

    system_prompt = (
        "You are a Japanese job-matching expert. "
        "Given a user's profile and a list of job listings, "
        "rank the top jobs by how well they match the user. "
        "Return a JSON array of objects with keys: rank, index (1-based), reason. "
        f"Return at most {top_n} items."
    )
    user_content = (
        f"## User Situation\n{profile['situation']}\n\n"
        f"## User Hope\n{profile['hope']}\n\n"
        f"## Resume Summary\n{profile['resume_text'][:1500]}\n\n"
        f"## Job Listings\n{jobs_text}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
            max_tokens=1500,
        )
        import json
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        ranking = json.loads(raw)

        ranked = []
        for item in ranking:
            idx = int(item.get("index", 1)) - 1
            if 0 <= idx < len(candidates):
                job = candidates[idx].copy()
                job["rank"] = item.get("rank", 99)
                job["reason"] = item.get("reason", "")
                ranked.append(job)
        return ranked

    except Exception as e:
        print(f"[ranker] AI ranking failed ({e}), using simple ranking.")
        return rank_jobs_simple(jobs, profile, top_n)
