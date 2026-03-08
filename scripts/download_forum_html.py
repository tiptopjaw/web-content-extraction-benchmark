#!/usr/bin/env python3
"""
Download HTML for forum benchmark threads.

Some sites require JavaScript rendering (Reddit, Quora, ResetEra, etc.)
and will need manual download via browser "Save As" (Ctrl+S, HTML Only).

Usage:
    python scripts/download_forum_html.py           # Download all
    python scripts/download_forum_html.py --dry-run  # Just list URLs and IDs
    python scripts/download_forum_html.py --manual-only  # Show which need manual download
"""
import argparse
import json
import time
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.parent
HTML_DIR = BASE_DIR / "benchmark" / "html"
GT_DIR = BASE_DIR / "benchmark" / "ground-truth"

# Sites that need JavaScript rendering — must be saved manually via browser
JS_REQUIRED_DOMAINS = {
    "www.reddit.com",
    "old.reddit.com",
    "www.quora.com",
    "www.resetera.com",
    "gamefaqs.gamespot.com",
    "lemmy.world",
    "lemmy.ml",
    "lobste.rs",
}

# Sites that may block automated requests — try with browser UA first
STRICT_DOMAINS = {
    "forums.macrumors.com",
    "www.head-fi.org",
    "boards.cruisecritic.com",
    "www.nairaland.com",
}

# All 79 forum thread URLs with metadata
FORUM_THREADS = [
    # === Discourse (12) ===
    {"id": "0501", "platform": "discourse", "forum": "OpenAI Community",
     "url": "https://community.openai.com/t/4o-update-2024-09-05-broken/931828"},
    {"id": "0502", "platform": "discourse", "forum": "Docker Forums",
     "url": "https://forums.docker.com/t/confusing-resolver-structure/144854"},
    {"id": "0503", "platform": "discourse", "forum": "Home Assistant",
     "url": "https://community.home-assistant.io/t/2024-4-4-2024-5-0-issue-stuck-on-home-assistant-is-starting/724779"},
    {"id": "0504", "platform": "discourse", "forum": "Rust Users Forum",
     "url": "https://users.rust-lang.org/t/is-changing-the-msrv-a-non-breaking-change-since-the-rust-2024-edition/138416"},
    {"id": "0505", "platform": "discourse", "forum": "Let's Encrypt",
     "url": "https://community.letsencrypt.org/t/how-to-request-the-longer-chain-after-08-02-2024/212419"},
    {"id": "0506", "platform": "discourse", "forum": "Obsidian Forum",
     "url": "https://forum.obsidian.md/t/plugin-recommendations/88771"},
    {"id": "0507", "platform": "discourse", "forum": "Motley Fool",
     "url": "https://discussion.fool.com/t/my-take-on-valuation/105724"},
    {"id": "0508", "platform": "discourse", "forum": "EVE Online",
     "url": "https://forums.eveonline.com/t/project-discovery-july-2024/457348"},
    {"id": "0509", "platform": "discourse", "forum": "Brave Community",
     "url": "https://community.brave.app/t/youtube-auto-dubbed/612558"},
    {"id": "0510", "platform": "discourse", "forum": "Netlify Answers",
     "url": "https://answers.netlify.com/t/deploy-failed-for-unknown-reason/117253"},
    {"id": "0511", "platform": "discourse", "forum": "MS Society",
     "url": "https://forum.mssociety.org.uk/t/struggling-with-getting-stronger-and-what-my-body-is-doing/79349"},
    {"id": "0512", "platform": "discourse", "forum": "Straight Dope",
     "url": "https://boards.straightdope.com/t/the-best-movies-of-2024/1012822"},

    # === XenForo (12) ===
    {"id": "0513", "platform": "xenforo", "forum": "MacRumors",
     "url": "https://forums.macrumors.com/threads/messages-in-icloud-still-taking-up-space-after-having-disabled-it.2350553/"},
    {"id": "0514", "platform": "xenforo", "forum": "ResetEra",
     "url": "https://www.resetera.com/threads/you-and-your-real-life-friends-gotta-go-fight-giygas.1146081/"},
    {"id": "0515", "platform": "xenforo", "forum": "Head-Fi",
     "url": "https://www.head-fi.org/threads/best-closed-headphones-as-of-07-2024.973407/"},
    {"id": "0516", "platform": "xenforo", "forum": "Physics Forums",
     "url": "https://www.physicsforums.com/threads/buying-microsoft-office-2024-but-not-from-microsoft.1066181/"},
    {"id": "0517", "platform": "xenforo", "forum": "SpigotMC",
     "url": "https://www.spigotmc.org/threads/best-minecraft-server-hosts-2025-updated.691400/"},
    {"id": "0518", "platform": "xenforo", "forum": "Student Doctor Network",
     "url": "https://forums.studentdoctor.net/threads/official-2024-2025-infectious-disease-application-thread.1498484/"},
    {"id": "0519", "platform": "xenforo", "forum": "AVForums",
     "url": "https://www.avforums.com/threads/discussion-of-our-review-of-apple-ipad-pro-tablet-2024.2509029/"},
    {"id": "0520", "platform": "xenforo", "forum": "Digital Point",
     "url": "https://forums.digitalpoint.com/threads/do-forums-still-have-a-role-in-the-age-of-social-media.2880547/"},
    {"id": "0521", "platform": "xenforo", "forum": "Basenotes",
     "url": "https://basenotes.com/community/threads/fragrance-budget-or-limit-for-2024.547532/"},
    {"id": "0522", "platform": "xenforo", "forum": "Cameraderie",
     "url": "https://cameraderie.org/threads/digital-cameras-a-2024-status-symbol.56948/"},
    {"id": "0523", "platform": "xenforo", "forum": "The Fighting Cock",
     "url": "https://thefightingcock.co.uk/forum/threads/squad-2024-2025.49320/"},
    {"id": "0524", "platform": "xenforo", "forum": "ALS Forums",
     "url": "https://www.alsforums.com/community/threads/early-als-symptoms.53800/"},

    # === vBulletin (10) ===
    {"id": "0525", "platform": "vbulletin", "forum": "Doom9 Forum",
     "url": "https://forum.doom9.org/showthread.php?t=186269"},
    {"id": "0526", "platform": "vbulletin", "forum": "Warrior Forum",
     "url": "https://www.warriorforum.com/beginners-area/1488296-will-simple-method-work-beginner-2024-a.html"},
    {"id": "0527", "platform": "vbulletin", "forum": "FlyerTalk",
     "url": "https://www.flyertalk.com/forum/trip-reports/2212958-scenic-turkish-french-sights-lowjhg.html"},
    {"id": "0528", "platform": "vbulletin", "forum": "AVS Forum",
     "url": "https://www.avsforum.com/threads/replacement-projector-recommendations-2024.3291860/"},
    {"id": "0529", "platform": "vbulletin", "forum": "WatchUSeek",
     "url": "https://www.watchuseek.com/threads/what-do-you-guys-think-will-be-the-trend-in-the-watch-market-in-2024.5542550/"},
    {"id": "0530", "platform": "vbulletin", "forum": "MTBR",
     "url": "https://www.mtbr.com/threads/suggestions-for-a-beginner-mtb.1231381/"},
    {"id": "0531", "platform": "vbulletin", "forum": "Netmums",
     "url": "https://www.netmums.com/coffeehouse/other-chat-514/general-chat-18/3c5c944d-would-you-ever-consider-a-career-in-earl.html"},
    {"id": "0532", "platform": "vbulletin", "forum": "Reef Central",
     "url": "https://forums.reefcentral.com/threads/new-tank-thoughts.32375893/"},
    {"id": "0533", "platform": "vbulletin", "forum": "Web Hosting Talk",
     "url": "https://www.webhostingtalk.com/showthread.php?t=1930933"},
    {"id": "0534", "platform": "vbulletin", "forum": "Toyota Nation",
     "url": "https://www.toyotanation.com/threads/2024-led-liftgate-lights.1797645/"},

    # === phpBB (8) ===
    {"id": "0535", "platform": "phpbb", "forum": "Raspberry Pi",
     "url": "https://forums.raspberrypi.com/viewtopic.php?t=361697"},
    {"id": "0536", "platform": "phpbb", "forum": "VirtualBox",
     "url": "https://forums.virtualbox.org/viewtopic.php?t=112320"},
    {"id": "0537", "platform": "phpbb", "forum": "FreeBSD",
     "url": "https://forums.freebsd.org/threads/2024-the-year-of-desktop-freebsd.91732/"},
    {"id": "0538", "platform": "phpbb", "forum": "Bogleheads",
     "url": "https://www.bogleheads.org/forum/viewtopic.php?t=425337"},
    {"id": "0539", "platform": "phpbb", "forum": "Audacity",
     "url": "https://forum.audacityteam.org/t/4-0-update-blogpost/148991"},
    {"id": "0540", "platform": "phpbb", "forum": "NationStates",
     "url": "https://forum.nationstates.net/viewtopic.php?f=20&t=487157"},
    {"id": "0541", "platform": "phpbb", "forum": "Arch Linux",
     "url": "https://bbs.archlinux.org/viewtopic.php?id=309936"},
    {"id": "0542", "platform": "phpbb", "forum": "MozillaZine",
     "url": "https://forums.mozillazine.org/viewtopic.php?t=3127128"},

    # === Invision Community (6) ===
    {"id": "0543", "platform": "invision", "forum": "Corsair Forum",
     "url": "https://forum.corsair.com/forums/topic/188682-new-2500x-pc-case/"},
    {"id": "0544", "platform": "invision", "forum": "Kerbal Space Program",
     "url": "https://forum.kerbalspaceprogram.com/topic/225132-if-the-forum-comes-to-an-end-soon/"},
    {"id": "0545", "platform": "invision", "forum": "Evernote Forum",
     "url": "https://discussion.evernote.com/forums/topic/150745-new-ui-2024/"},
    {"id": "0546", "platform": "invision", "forum": "Squarespace Forum",
     "url": "https://forum.squarespace.com/topic/319445-squarespace-roadmap-discussion/"},
    {"id": "0547", "platform": "invision", "forum": "Affinity Forum",
     "url": "https://forum.affinity.serif.com/index.php?/topic/201820-ai-discussion-split-from-canva-thread/"},
    {"id": "0548", "platform": "invision", "forum": "PrestaShop",
     "url": "https://forum.prestashop.com/topic/1103020-payment-issues-how-to-delete-or-change-payment-method/"},

    # === NodeBB (6) ===
    {"id": "0549", "platform": "nodebb", "forum": "NodeBB Community",
     "url": "https://community.nodebb.org/topic/18427/rc1-of-nodebb-v4"},
    {"id": "0550", "platform": "nodebb", "forum": "LTT Forums",
     "url": "https://linustechtips.com/topic/1571202-editing-pc-build-may-2024/"},
    {"id": "0551", "platform": "nodebb", "forum": "Meatgistics",
     "url": "https://meatgistics.waltons.com/topic/7853/syrup"},
    {"id": "0552", "platform": "nodebb", "forum": "Qt Forum",
     "url": "https://forum.qt.io/topic/156087/which-qt6-version-for-ubuntu-24-04"},
    {"id": "0553", "platform": "nodebb", "forum": "Windy Community",
     "url": "https://community.windy.com/topic/43227/how-to-display-saved-kml-or-gpx-route-on-ipad-or-mobile-app"},
    {"id": "0554", "platform": "nodebb", "forum": "Netdata Community",
     "url": "https://community.netdata.cloud/t/multiple-agents-crashing/7798"},

    # === Other Platform Software (6) ===
    {"id": "0555", "platform": "fluxbb", "forum": "Arch Linux (FluxBB)",
     "url": "https://bbs.archlinux.org/viewtopic.php?id=298271"},
    {"id": "0556", "platform": "smf", "forum": "SMF Community",
     "url": "https://www.simplemachines.org/community/index.php?topic=589061.0"},
    {"id": "0557", "platform": "flarum", "forum": "Flarum Community",
     "url": "https://discuss.flarum.org/d/2068-types-of-threads-flarum-as-a-discussion-engine"},
    {"id": "0558", "platform": "mybb", "forum": "MyBB Community",
     "url": "https://community.mybb.com/thread-222085.html"},
    {"id": "0559", "platform": "vanilla", "forum": "Vanilla Community",
     "url": "https://open.vanillaforums.com/discussion/39620/higher-logic-has-terminated-open-source-vanilla"},
    {"id": "0560", "platform": "tapatalk", "forum": "Tapatalk (TFH Magazine)",
     "url": "https://www.tapatalk.com/groups/tfhmagazine/what-to-look-for-before-purchasing-new-fish-t17351.html"},

    # === Custom/Unique Platforms (19) ===
    {"id": "0561", "platform": "custom-reddit", "forum": "Reddit (new r/technology)",
     "url": "https://www.reddit.com/r/technology/comments/1rl4mew/fcc_chair_to_europe_if_you_restrict_us_satellite/"},
    {"id": "0562", "platform": "custom-reddit-old", "forum": "Reddit (old r/science)",
     "url": "https://old.reddit.com/r/science/comments/1rku5x9/fully_functional_hair_follicles_have_been_grown/"},
    {"id": "0563", "platform": "custom-reddit", "forum": "Reddit (new r/Cooking)",
     "url": "https://www.reddit.com/r/Cooking/comments/1rl0nt4/enameled_cast_iron_pan_and_metal/"},
    {"id": "0564", "platform": "custom-se", "forum": "Stack Overflow",
     "url": "https://stackoverflow.com/questions/21553327/what-is-main-py"},
    {"id": "0565", "platform": "custom-se", "forum": "Super User",
     "url": "https://superuser.com/questions/442960/why-does-64-bit-windows-need-a-separate-program-files-x86-folder"},
    {"id": "0566", "platform": "custom-se", "forum": "Server Fault",
     "url": "https://serverfault.com/questions/2888/why-is-raid-not-a-backup"},
    {"id": "0567", "platform": "custom-se", "forum": "Ask Ubuntu",
     "url": "https://askubuntu.com/questions/7809/how-to-make-a-disk-image-and-restore-from-it-later"},
    {"id": "0568", "platform": "custom-arc", "forum": "Hacker News",
     "url": "https://news.ycombinator.com/item?id=38777115"},
    {"id": "0569", "platform": "custom-quora", "forum": "Quora (History)",
     "url": "https://www.quora.com/Was-World-War-II-really-that-bad"},
    {"id": "0570", "platform": "custom-slash", "forum": "Slashdot",
     "url": "https://linux.slashdot.org/story/24/01/12/169219/a-2024-discussion-whether-to-convert-the-linux-kernel-from-c-to-modern-c"},
    {"id": "0571", "platform": "discourse", "forum": "Discourse Meta",
     "url": "https://meta.discourse.org/t/newbie-question-is-there-a-comprehensive-guide-to-configuring-and-administering-discourse-instance/397040"},
    {"id": "0572", "platform": "custom-lemmy", "forum": "Lemmy (lemmy.world)",
     "url": "https://lemmy.world/post/8732029"},
    {"id": "0573", "platform": "custom-lemmy", "forum": "Lemmy (lemmy.ml)",
     "url": "https://lemmy.ml/post/21018364"},
    {"id": "0574", "platform": "custom", "forum": "GameFAQs",
     "url": "https://gamefaqs.gamespot.com/boards/189706-nintendo-switch/80702016"},
    {"id": "0575", "platform": "custom-rails", "forum": "Lobsters",
     "url": "https://lobste.rs/s/dwip3v/rust_project_goals_for_2024"},
    {"id": "0576", "platform": "custom-php", "forum": "Nairaland",
     "url": "https://www.nairaland.com/7603790/hybrid-quantum-classical-computing"},
    {"id": "0577", "platform": "custom", "forum": "The Student Room",
     "url": "https://www.thestudentroom.co.uk/showthread.php?t=7481802"},
    {"id": "0578", "platform": "custom", "forum": "Mumsnet",
     "url": "https://www.mumsnet.com/talk/food_and_recipes/5498613-your-favourite-lowish-cost-family-meals"},
    {"id": "0579", "platform": "custom", "forum": "CruiseCritic",
     "url": "https://boards.cruisecritic.com/topic/3003956-2024-pros-cons-of-using-a-travel-agent-princess/"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def needs_manual_download(url: str) -> bool:
    """Check if a URL requires manual browser download (JS rendering needed)."""
    domain = urlparse(url).netloc
    return domain in JS_REQUIRED_DOMAINS


def download_html(url: str, output_path: Path, timeout: int = 30) -> dict:
    """Download HTML from a URL. Returns status dict."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        content = resp.text
        # Basic sanity check — page should have some HTML
        if len(content) < 500:
            return {"status": "too_small", "size": len(content)}

        output_path.write_text(content, encoding="utf-8")
        return {"status": "ok", "size": len(content)}

    except requests.exceptions.HTTPError as e:
        return {"status": "http_error", "code": e.response.status_code if e.response else None}
    except requests.exceptions.ConnectionError:
        return {"status": "connection_error"}
    except requests.exceptions.Timeout:
        return {"status": "timeout"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_gt_stub(thread: dict, gt_path: Path):
    """Create a minimal ground truth stub file for later annotation."""
    gt_data = {
        "file_id": thread["id"],
        "url": thread["url"],
        "source": thread["forum"],
        "page_type": {"primary": "forum"},
        "platform": thread["platform"],
        "ground_truth": {
            "title": "",
            "author": "",
            "publish_date": None,
            "main_content": "",
            "with": [],
            "without": []
        }
    }
    gt_path.write_text(json.dumps(gt_data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Download forum HTML for benchmark")
    parser.add_argument("--dry-run", action="store_true", help="Just list URLs and IDs")
    parser.add_argument("--manual-only", action="store_true", help="Show which need manual download")
    parser.add_argument("--skip-existing", action="store_true", help="Skip files that already exist")
    parser.add_argument("--stubs", action="store_true", help="Create GT stub files")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests (seconds)")
    args = parser.parse_args()

    HTML_DIR.mkdir(parents=True, exist_ok=True)
    GT_DIR.mkdir(parents=True, exist_ok=True)

    manual = []
    auto = []
    for t in FORUM_THREADS:
        if needs_manual_download(t["url"]):
            manual.append(t)
        else:
            auto.append(t)

    if args.manual_only:
        print(f"\n=== Sites requiring manual browser download ({len(manual)}) ===\n")
        print("Save each page via browser: Ctrl+S > 'HTML Only'\n")
        for t in manual:
            html_path = HTML_DIR / f"{t['id']}.html"
            exists = "EXISTS" if html_path.exists() else "MISSING"
            print(f"  {t['id']}  {exists:7s}  {t['forum']:30s}  {t['url']}")
        print(f"\n=== Sites downloadable via script ({len(auto)}) ===\n")
        for t in auto:
            html_path = HTML_DIR / f"{t['id']}.html"
            exists = "EXISTS" if html_path.exists() else "MISSING"
            print(f"  {t['id']}  {exists:7s}  {t['forum']:30s}  {t['url']}")
        return

    if args.dry_run:
        print(f"\n=== All {len(FORUM_THREADS)} forum threads ===\n")
        for t in FORUM_THREADS:
            manual_flag = " [MANUAL]" if needs_manual_download(t["url"]) else ""
            print(f"  {t['id']}  {t['platform']:20s}  {t['forum']:30s}{manual_flag}")
            print(f"          {t['url']}")
        return

    if args.stubs:
        print(f"\nCreating GT stub files in {GT_DIR}...\n")
        created = 0
        for t in FORUM_THREADS:
            gt_path = GT_DIR / f"{t['id']}.json"
            if not gt_path.exists():
                create_gt_stub(t, gt_path)
                created += 1
                print(f"  Created {gt_path.name}")
            else:
                print(f"  Skipped {gt_path.name} (exists)")
        print(f"\nCreated {created} stub files.")
        return

    # Download automated ones
    print(f"\n=== Downloading {len(auto)} pages (skipping {len(manual)} manual) ===\n")

    ok = 0
    skipped = 0
    failed = []

    for i, t in enumerate(auto):
        html_path = HTML_DIR / f"{t['id']}.html"

        if args.skip_existing and html_path.exists():
            print(f"  [{i+1}/{len(auto)}] {t['id']} SKIP (exists) — {t['forum']}")
            skipped += 1
            continue

        print(f"  [{i+1}/{len(auto)}] {t['id']} downloading — {t['forum']}...", end=" ", flush=True)
        result = download_html(t["url"], html_path)

        if result["status"] == "ok":
            size_kb = result["size"] / 1024
            print(f"OK ({size_kb:.0f} KB)")
            ok += 1
        else:
            print(f"FAILED: {result}")
            failed.append(t)

        if i < len(auto) - 1:
            time.sleep(args.delay)

    print(f"\n=== Results ===")
    print(f"  Downloaded: {ok}")
    print(f"  Skipped:    {skipped}")
    print(f"  Failed:     {len(failed)}")
    print(f"  Manual:     {len(manual)}")

    if failed:
        print(f"\n=== Failed downloads (try manually) ===")
        for t in failed:
            print(f"  {t['id']}  {t['forum']:30s}  {t['url']}")

    if manual:
        print(f"\n=== Needs manual browser download ({len(manual)}) ===")
        print("Save each page via browser: Ctrl+S > 'HTML Only'")
        for t in manual:
            html_path = HTML_DIR / f"{t['id']}.html"
            exists = "EXISTS" if html_path.exists() else "MISSING"
            print(f"  {t['id']}  {exists:7s}  {t['forum']:30s}  {t['url']}")


if __name__ == "__main__":
    main()
