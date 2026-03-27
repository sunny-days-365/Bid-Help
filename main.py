"""
main.py  —  Green Japan Job Finder
==========================================
Usage:
    python main.py --resume path/to/resume.docx --situation "..." --hope "..."

Or run interactively (no arguments):
    python main.py
"""

import argparse
import json
import os
import sys
from pathlib import Path

# .env ファイルを自動読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from resume_parser import build_profile
from keyword_extractor import extract_keywords_with_ai
from green_scraper import scrape_green
from job_ranker import rank_jobs_with_ai


BANNER = r"""
  ____                        _       _       ____                      _
 / ___|_ __ ___  ___ _ __    | | ___ | |__   / ___|  ___  __ _ _ __ __| |
| |  _| '__/ _ \/ _ \ '_ \  | |/ _ \| '_ \  \___ \ / _ \/ _` | '__/ _` |
| |_| | | |  __/  __/ | | | | | (_) | |_) |  ___) |  __/ (_| | | | (_| |
 \____|_|  \___|\___|_| |_| |_|\___/|_.__/  |____/ \___|\__,_|_|  \__,_|

          Automatic Job Finder for Green Japan (green-japan.com)
"""


def get_inputs_interactive() -> tuple[str, str, str]:
    print("\n--- Resume File ---")
    while True:
        path = input("Enter path to your resume (.docx or .txt): ").strip().strip('"')
        if Path(path).exists():
            break
        print(f"  File not found: {path}. Please try again.")

    print("\n--- Current Situation ---")
    print("(e.g., '5 years experience as Python backend engineer, currently unemployed')")
    situation = input("> ").strip()

    print("\n--- Job Hope ---")
    print("(e.g., 'Remote Python or Go backend job in Tokyo, 700万円 or more, startup preferred')")
    hope = input("> ").strip()

    return path, situation, hope


def print_results(ranked_jobs: list[dict], output_file: str | None = None):
    print("\n" + "=" * 70)
    print(f"  TOP {len(ranked_jobs)} MATCHING JOBS ON GREEN JAPAN")
    print("=" * 70)

    lines = []
    for i, job in enumerate(ranked_jobs, 1):
        title = job.get("title", "(no title)")[:80]
        url = job.get("url", "")
        keyword = job.get("keyword", "")
        reason = job.get("reason", "")

        line = f"\n{i:>2}. {title}"
        line += f"\n    🔗 {url}"
        if keyword:
            line += f"\n    🔍 Search keyword: {keyword}"
        if reason:
            line += f"\n    💡 {reason}"
        print(line)
        lines.append(line)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"TOP {len(ranked_jobs)} MATCHING JOBS ON GREEN JAPAN\n")
            f.write("=" * 70 + "\n")
            for line in lines:
                f.write(line + "\n")
        print(f"\n📄 Results saved to: {output_file}")

    # Also save raw JSON
    json_file = (output_file or "results").replace(".txt", "") + ".json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(ranked_jobs, f, ensure_ascii=False, indent=2)
    print(f"📦 Raw JSON saved to: {json_file}")


def main():
    print(BANNER)

    parser = argparse.ArgumentParser(description="Green Japan Automatic Job Finder")
    parser.add_argument("--resume", help="Path to resume file (.docx or .txt)")
    parser.add_argument("--situation", help="Your current situation")
    parser.add_argument("--hope", help="Your job hope / ideal job description")
    parser.add_argument("--pages", type=int, default=3, help="Pages to scrape per keyword (default: 3)")
    parser.add_argument("--top", type=int, default=20, help="Number of top results to show (default: 20)")
    parser.add_argument("--output", default="results.txt", help="Output file (default: results.txt)")
    parser.add_argument("--keywords", help="Comma-separated keywords to use directly (skip AI extraction)")
    args = parser.parse_args()

    # --- Step 1: Get inputs ---
    if args.resume and args.situation and args.hope:
        resume_path = args.resume
        situation = args.situation
        hope = args.hope
    else:
        resume_path, situation, hope = get_inputs_interactive()

    print(f"\n✅ Resume: {resume_path}")

    # --- Step 2: Build profile ---
    print("📋 Parsing resume...")
    try:
        profile = build_profile(resume_path, situation, hope)
    except Exception as e:
        print(f"❌ Failed to parse resume: {e}")
        sys.exit(1)
    print(f"   Resume text length: {len(profile['resume_text'])} characters")

    # --- Step 3: Extract keywords ---
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
        print(f"🔑 Using provided keywords: {keywords}")
    else:
        print("🤖 Extracting search keywords from profile...")
        keywords = extract_keywords_with_ai(profile)
        print(f"🔑 Keywords: {keywords}")

    if not keywords:
        print("❌ No keywords extracted. Please provide keywords with --keywords.")
        sys.exit(1)

    # --- Step 4: Scrape Green Japan ---
    print(f"\n🌐 Scraping Green Japan (up to {args.pages} pages per keyword)...")
    jobs = scrape_green(keywords, max_pages=args.pages)
    print(f"\n✅ Total unique jobs found: {len(jobs)}")

    if not jobs:
        print("⚠️  No jobs found. Try different keywords.")
        sys.exit(0)

    # --- Step 5: Rank jobs ---
    print("\n🏆 Ranking jobs by relevance...")
    ranked = rank_jobs_with_ai(jobs, profile, top_n=args.top)

    # --- Step 6: Print & save results ---
    print_results(ranked, output_file=args.output)

    print("\n✅ Done! Open the URLs above to apply on Green Japan.")


if __name__ == "__main__":
    main()
