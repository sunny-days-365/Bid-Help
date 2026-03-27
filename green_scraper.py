"""
green_scraper.py
Scrapes job listings from https://www.green-japan.com/search using Playwright.
Green is a JavaScript-rendered Next.js site, so requests+BS4 alone won't work.
"""

import time
import re
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = "https://www.green-japan.com/search"


def build_search_url(keyword: str, page: int = 1) -> str:
    params = {"keyword": keyword}
    if page > 1:
        params["page"] = str(page)
    return f"{BASE_URL}?{urlencode(params)}"


def _extract_jobs_from_page(page_content: str) -> list[dict]:
    """Parse job links and titles from rendered HTML."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page_content, "lxml")

    jobs = []
    # Job links follow pattern: /company/{id}/job/{id}
    job_pattern = re.compile(r"^https://www\.green-japan\.com/company/\d+/job/\d+$")

    seen_urls = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Make absolute
        if href.startswith("/"):
            href = "https://www.green-japan.com" + href
        if job_pattern.match(href) and href not in seen_urls:
            seen_urls.add(href)
            title = a.get_text(separator=" ", strip=True)
            # Clean up the title text
            title = re.sub(r"\s+", " ", title)[:120]
            jobs.append({"title": title, "url": href})
    return jobs


def scrape_green(keywords: list[str], max_pages: int = 3) -> list[dict]:
    """
    Search Green Japan for each keyword, scrape job URLs and titles.

    Args:
        keywords:  List of search keyword strings.
        max_pages: How many result pages to scrape per keyword (default 3).

    Returns:
        List of dicts: [{"title": ..., "url": ..., "keyword": ...}, ...]
    """
    all_jobs: list[dict] = []
    seen_urls: set[str] = set()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ja-JP",
        )
        page = context.new_page()

        for keyword in keywords:
            print(f"[scraper] Searching keyword: '{keyword}'")
            for page_num in range(1, max_pages + 1):
                url = build_search_url(keyword, page_num)
                try:
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    # Wait for job cards to appear
                    page.wait_for_selector("a[href*='/job/']", timeout=15000)
                except PlaywrightTimeout:
                    print(f"  [scraper] Timeout on page {page_num}, skipping.")
                    break

                content = page.content()
                jobs = _extract_jobs_from_page(content)

                new_count = 0
                for job in jobs:
                    if job["url"] not in seen_urls:
                        seen_urls.add(job["url"])
                        job["keyword"] = keyword
                        all_jobs.append(job)
                        new_count += 1

                print(f"  [scraper] Page {page_num}: found {new_count} new jobs")

                if new_count == 0:
                    # No new results, stop paginating this keyword
                    break

                time.sleep(1.5)  # polite delay

        browser.close()

    return all_jobs
