#!/usr/bin/env python3
"""Download forum HTML pages that failed curl/requests using Playwright headless browser."""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

HTML_DIR = Path(__file__).parent.parent / "benchmark" / "html"

# All pages that need browser-based download
PAGES = [
    ("0514", "https://www.resetera.com/threads/you-and-your-real-life-friends-gotta-go-fight-giygas.1146081/"),
    ("0519", "https://www.avforums.com/threads/discussion-of-our-review-of-apple-ipad-pro-tablet-2024.2509029/"),
    ("0525", "https://forum.doom9.org/showthread.php?t=186269"),
    ("0538", "https://www.bogleheads.org/forum/viewtopic.php?t=425337"),
    ("0540", "https://forum.nationstates.net/viewtopic.php?f=20&t=487157"),
    ("0543", "https://forum.corsair.com/forums/topic/188682-new-2500x-pc-case/"),
    ("0544", "https://forum.kerbalspaceprogram.com/topic/225132-if-the-forum-comes-to-an-end-soon/"),
    ("0545", "https://discussion.evernote.com/forums/topic/150745-new-ui-2024/"),
    ("0546", "https://forum.squarespace.com/topic/319445-squarespace-roadmap-discussion/"),
    ("0548", "https://forum.prestashop.com/topic/1103020-payment-issues-how-to-delete-or-change-payment-method/"),
    ("0558", "https://community.mybb.com/thread-222085.html"),
    ("0561", "https://www.reddit.com/r/technology/comments/1rl4mew/fcc_chair_to_europe_if_you_restrict_us_satellite/"),
    ("0562", "https://old.reddit.com/r/science/comments/1rku5x9/fully_functional_hair_follicles_have_been_grown/"),
    ("0563", "https://www.reddit.com/r/Cooking/comments/1rl0nt4/enameled_cast_iron_pan_and_metal/"),
    ("0569", "https://www.quora.com/Was-World-War-II-really-that-bad"),
    ("0572", "https://lemmy.world/post/8732029"),
    ("0573", "https://lemmy.ml/post/21018364"),
    ("0574", "https://gamefaqs.gamespot.com/boards/189706-nintendo-switch/80702016"),
    ("0575", "https://lobste.rs/s/dwip3v/rust_project_goals_for_2024"),
    ("0579", "https://boards.cruisecritic.com/topic/3003956-2024-pros-cons-of-using-a-travel-agent-princess/"),
]


async def download_page(page, file_id: str, url: str) -> dict:
    """Navigate to URL and save rendered HTML."""
    output = HTML_DIR / f"{file_id}.html"
    if output.exists() and output.stat().st_size > 1000:
        return {"id": file_id, "status": "skip", "size": output.stat().st_size}
    try:
        resp = await page.goto(url, wait_until="networkidle", timeout=30000)
        if resp and resp.status >= 400:
            return {"id": file_id, "status": "http_error", "code": resp.status}
        # Wait a bit for any lazy-loaded content
        await page.wait_for_timeout(2000)
        html = await page.content()
        if len(html) < 500:
            return {"id": file_id, "status": "too_small", "size": len(html)}
        output.write_text(html, encoding="utf-8")
        return {"id": file_id, "status": "ok", "size": len(html)}
    except Exception as e:
        return {"id": file_id, "status": "error", "message": str(e)[:200]}


async def main():
    HTML_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        ok = 0
        failed = []
        skipped = 0

        for i, (file_id, url) in enumerate(PAGES):
            print(f"  [{i+1}/{len(PAGES)}] {file_id} ", end="", flush=True)
            result = await download_page(page, file_id, url)

            if result["status"] == "ok":
                print(f"OK ({result['size']//1024} KB)")
                ok += 1
            elif result["status"] == "skip":
                print(f"SKIP (exists, {result['size']//1024} KB)")
                skipped += 1
            else:
                print(f"FAILED: {result}")
                failed.append((file_id, url, result))

        await browser.close()

    print(f"\n=== Results ===")
    print(f"  OK:      {ok}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {len(failed)}")
    if failed:
        print(f"\n=== Still need manual download ===")
        for fid, url, res in failed:
            print(f"  {fid}  {res.get('status')}  {url}")


if __name__ == "__main__":
    asyncio.run(main())
