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

# Next.js サイトで実際に job リンクが含まれる <a> のパターン
JOB_URL_PATTERN = re.compile(r"^https://www\.green-japan\.com/company/\d+/job/\d+$")


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
    seen_urls = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/"):
            href = "https://www.green-japan.com" + href
        if JOB_URL_PATTERN.match(href) and href not in seen_urls:
            seen_urls.add(href)
            title = a.get_text(separator=" ", strip=True)
            title = re.sub(r"\s+", " ", title)[:120]
            jobs.append({"title": title, "url": href})
    return jobs


def _extract_jobs_via_js(page) -> list[dict]:
    """
    JavaScript 経由で直接 DOM から job リンクを取得するフォールバック。
    BeautifulSoup でパースできなかった場合に使用。
    """
    try:
        links = page.evaluate("""
            () => {
                const anchors = Array.from(document.querySelectorAll('a[href*="/job/"]'));
                return anchors.map(a => ({
                    href: a.href,
                    text: a.innerText.trim().slice(0, 120)
                }));
            }
        """)
        jobs = []
        seen = set()
        for item in links:
            href = item.get("href", "")
            if JOB_URL_PATTERN.match(href) and href not in seen:
                seen.add(href)
                jobs.append({"title": item.get("text", ""), "url": href})
        return jobs
    except Exception:
        return []


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
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ja-JP",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        # デフォルトタイムアウトを60秒に設定
        page.set_default_timeout(60000)

        for keyword in keywords:
            print(f"[scraper] Searching keyword: '{keyword}'")
            for page_num in range(1, max_pages + 1):
                url = build_search_url(keyword, page_num)
                jobs = []
                try:
                    # networkidle ではなく domcontentloaded を使用
                    # Next.js サイトは networkidle で永遠に待機してしまう
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)

                    # JS レンダリングを待つ — job リンクが出現するまで最大20秒
                    try:
                        page.wait_for_selector(
                            "a[href*='/job/']",
                            timeout=20000,
                            state="attached",
                        )
                    except PlaywrightTimeout:
                        # セレクターが見つからなくてもページ内容で試みる
                        print(f"  [scraper] Selector wait timeout — trying JS extraction")

                    # 追加で少し待機してレンダリングを完了させる
                    page.wait_for_timeout(2000)

                    # まず JS 経由で取得（最も確実）
                    jobs = _extract_jobs_via_js(page)

                    # 取れなければ HTML パース
                    if not jobs:
                        content = page.content()
                        jobs = _extract_jobs_from_page(content)

                except PlaywrightTimeout:
                    print(f"  [scraper] Page load timeout on page {page_num}, skipping.")
                    break
                except Exception as e:
                    print(f"  [scraper] Error on page {page_num}: {e}")
                    break

                new_count = 0
                for job in jobs:
                    if job["url"] not in seen_urls:
                        seen_urls.add(job["url"])
                        job["keyword"] = keyword
                        all_jobs.append(job)
                        new_count += 1

                print(f"  [scraper] Page {page_num}: found {new_count} new jobs")

                if new_count == 0:
                    break

                time.sleep(1.5)  # 礼儀正しいウェイト

        browser.close()

    return all_jobs
