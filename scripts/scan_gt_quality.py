#!/usr/bin/env python3
"""
Comprehensive ground truth quality scan.

Detects boilerplate contamination, formatting issues, and content quality
problems across all GT entries. Checks articleBody for patterns that
indicate non-article content leaked in.
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
GT_PATH = ROOT / "release" / "ground-truth.json"

# ============================================================
# Boilerplate pattern definitions
# Each pattern: (category, regex, description)
# We use \b word boundaries and context to reduce false positives
# ============================================================

BOILERPLATE_PATTERNS = [
    # --- Newsletter / Subscription CTAs ---
    ("newsletter", r"(?i)\bsign\s+up\s+for\s+(our\s+)?(free\s+)?(newsletter|email|updates|mailing\s+list)", "newsletter signup CTA"),
    ("newsletter", r"(?i)\bsubscribe\s+to\s+(our\s+)?(newsletter|email\s+list|mailing\s+list|updates)", "subscribe to newsletter"),
    ("newsletter", r"(?i)\benter\s+your\s+email\s+(address\s+)?to\s+(subscribe|sign\s+up|get|receive)", "enter email to subscribe"),
    ("newsletter", r"(?i)\bget\s+(our\s+)?(latest|weekly|daily|monthly)\s+(news|updates|stories|articles)\s+(delivered|sent|straight)\s+to", "newsletter delivery CTA"),
    ("newsletter", r"(?i)\bjoin\s+our\s+(newsletter|mailing\s+list|email\s+list)", "join newsletter"),
    ("newsletter", r"(?i)\bnever\s+miss\s+(a\s+)?(story|post|update|article)\b", "never miss a story CTA"),
    ("newsletter", r"(?i)\bstay\s+(up\s+to\s+date|informed|connected)\s+with\s+(our|the)\s+(latest|newest)", "stay up to date CTA"),
    ("newsletter", r"(?i)\bsubscribe\s+now\b", "subscribe now CTA"),
    ("newsletter", r"(?i)\bsign\s+up\s+now\b(?!.*\b(account|service|trial|class|course|program|membership)\b)", "sign up now CTA"),

    # --- Cookie / Privacy notices ---
    ("cookie", r"(?i)\bwe\s+use\s+cookies\s+to\b", "cookie notice"),
    ("cookie", r"(?i)\bthis\s+(site|website)\s+uses\s+cookies\b", "cookie notice"),
    ("cookie", r"(?i)\bby\s+(continuing|using)\s+(to\s+)?(browse|use|navigate)\s+(this\s+)?(site|website),?\s+you\s+(agree|consent|accept)", "cookie consent"),
    ("cookie", r"(?i)\baccept\s+(all\s+)?cookies\b", "accept cookies button"),
    ("cookie", r"(?i)\bcookie\s+(settings|preferences|policy)\b(?=.*\b(manage|customize|update|change|accept|decline)\b)", "cookie settings"),

    # --- Social sharing widgets ---
    ("social", r"(?i)^share\s+(this|on)\s+(article|post|story|facebook|twitter|linkedin|x)\s*$", "share widget (standalone line)"),
    ("social", r"(?i)\bfollow\s+us\s+on\s+(facebook|twitter|instagram|linkedin|youtube|x|tiktok)", "follow us on social"),
    ("social", r"(?i)\blike\s+us\s+on\s+facebook\b", "like us on facebook"),
    ("social", r"(?i)^(share|tweet|pin\s+it|email)\s*\n(share|tweet|pin\s+it|email)", "social sharing button block"),

    # --- Comment section artifacts ---
    ("comments", r"(?i)^(leave\s+a\s+)?(comment|reply)\s*$", "comment section header"),
    ("comments", r"(?i)\bpost\s+a\s+comment\b", "post a comment"),
    ("comments", r"(?i)\byou\s+must\s+be\s+logged\s+in\s+to\s+post\s+a\s+comment\b", "login to comment"),
    ("comments", r"(?i)\b\d+\s+comments?\s*$", "comment count"),
    ("comments", r"(?i)^notify\s+me\s+of\s+(follow-up|new)\s+comments\b", "notify me of comments"),

    # --- Footer / Legal ---
    ("footer", r"(?i)\ball\s+rights\s+reserved\.?\s*$", "all rights reserved"),
    ("footer", r"(?i)^©\s*\d{4}\b", "copyright line"),
    ("footer", r"(?i)\bterms\s+(of\s+)?(service|use)\s*\|\s*privacy\s+policy", "terms | privacy footer"),
    ("footer", r"(?i)^(about\s+us|contact\s+us|careers|press|advertise)\s*\n(about\s+us|contact\s+us|careers|press|advertise)", "footer nav links"),

    # --- Ad / Sponsored content ---
    ("ads", r"(?i)^advertisement\s*$", "advertisement label"),
    ("ads", r"(?i)^sponsored\s+(content|post|by)\b", "sponsored content label"),
    ("ads", r"(?i)^promoted\s+(content|post|story)\b", "promoted content label"),

    # --- Related articles ---
    ("related", r"(?i)^(related|recommended|popular|trending|more)\s+(articles?|posts?|stories|reads?)\s*:?\s*$", "related articles header"),
    ("related", r"(?i)^you\s+(might|may)\s+(also\s+)?(like|enjoy|be\s+interested)\s*:?\s*$", "you might also like"),
    ("related", r"(?i)^(read\s+)?(more|next|also)\s*:\s*$", "read more label"),

    # --- Login / Account ---
    ("login", r"(?i)\b(sign|log)\s+in\s+to\s+(your\s+)?(account|continue|access)\b", "login prompt"),
    ("login", r"(?i)\bcreate\s+(a\s+)?(free\s+)?account\s+to\b", "create account prompt"),
    ("login", r"(?i)\balready\s+(a\s+)?(member|subscriber|have\s+an\s+account)\??\s*(sign|log)\s+in", "already a member login"),

    # --- Popups / Modals ---
    ("popup", r"(?i)\bbefore\s+you\s+go\b.*\b(subscribe|sign\s+up|newsletter|offer)\b", "exit intent popup"),
    ("popup", r"(?i)\bdon'?t\s+miss\s+out\b.*\b(subscribe|sign\s+up|newsletter|offer)\b", "FOMO popup"),

    # --- Author bio blocks (lengthy ones at end) ---
    ("author_bio", r"(?i)\babout\s+the\s+author\s*\n.{50,}", "about the author block"),
    ("author_bio", r"(?i)\b(he|she|they)\s+(is|are)\s+(a|an)\s+(senior\s+)?(staff\s+)?(writer|reporter|journalist|editor|columnist|contributor|correspondent)\s+(at|for|with)\s+", "author bio sentence"),

    # --- Paywall / Subscription gate ---
    ("paywall", r"(?i)\b(this|the)\s+(article|content|story)\s+is\s+(for\s+)?(premium|paid|subscriber|member)", "paywall notice"),
    ("paywall", r"(?i)\bto\s+(continue\s+)?read(ing)?\s+(this\s+)?(article|story),?\s+(please\s+)?(subscribe|sign\s+up|log\s+in|become\s+a\s+member)", "paywall gate"),
    ("paywall", r"(?i)\bunlock\s+(this\s+)?(article|story|content)\b", "unlock content"),

    # --- Navigation breadcrumbs ---
    ("nav", r"(?i)^home\s*[>›»/]\s*\w+\s*[>›»/]", "breadcrumb navigation"),

    # --- Print/email article ---
    ("utility", r"(?i)^(print|email)\s+(this\s+)?(article|story|page)\s*$", "print/email article"),
    ("utility", r"(?i)^(font\s+size|text\s+size)\s*:?\s*(small|medium|large|a\+|a-)", "font size control"),

    # --- App download prompts ---
    ("app", r"(?i)\bdownload\s+(our|the)\s+(free\s+)?app\b", "download app CTA"),
    ("app", r"(?i)\bget\s+it\s+on\s+(google\s+play|the\s+app\s+store)\b", "app store CTA"),
]

# Patterns that check the START of the content (first 200 chars)
START_PATTERNS = [
    ("nav", r"(?i)^(menu|navigation|skip\s+to\s+(main\s+)?content)", "navigation artifact at start"),
]

# Patterns that check the END of the content (last 500 chars)
END_PATTERNS = [
    ("footer", r"(?i)(©\s*\d{4}|all\s+rights\s+reserved|terms\s+of\s+(service|use)|privacy\s+policy)\s*\.?\s*$", "footer text at end"),
    ("newsletter", r"(?i)(subscribe|sign\s+up|newsletter|mailing\s+list|email\s+updates)\s*\.?\s*$", "newsletter CTA at end"),
    ("related", r"(?i)(related\s+(articles?|posts?)|you\s+(might|may)\s+also\s+like|recommended\s+for\s+you)\s*:?\s*$", "related articles at end"),
]


def scan_entry(file_id: str, entry: dict) -> list:
    """Scan a single GT entry for quality issues. Returns list of findings."""
    findings = []
    body = entry.get("articleBody", "")

    if not body:
        findings.append(("empty", "CRITICAL", "articleBody is empty", ""))
        return findings

    # --- Check body against all boilerplate patterns ---
    for category, pattern, description in BOILERPLATE_PATTERNS:
        matches = list(re.finditer(pattern, body, re.MULTILINE))
        for m in matches:
            # Get surrounding context (40 chars before/after)
            start = max(0, m.start() - 40)
            end = min(len(body), m.end() + 40)
            context = body[start:end].replace("\n", "\\n")
            findings.append((category, "WARNING", description, f"...{context}..."))

    # --- Check start of content ---
    start_text = body[:200]
    for category, pattern, description in START_PATTERNS:
        if re.search(pattern, start_text):
            findings.append((category, "WARNING", description, start_text[:80].replace("\n", "\\n")))

    # --- Check end of content ---
    end_text = body[-500:]
    for category, pattern, description in END_PATTERNS:
        if re.search(pattern, end_text):
            context = body[-100:].replace("\n", "\\n")
            findings.append((category, "WARNING", description, f"...{context}"))

    # --- Check for repeated paragraphs ---
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    seen = {}
    for i, para in enumerate(paragraphs):
        if len(para) > 50:  # Only check substantial paragraphs
            normalized = re.sub(r'\s+', ' ', para.lower().strip())
            if normalized in seen:
                findings.append(("duplicate", "WARNING", f"Duplicate paragraph (first at #{seen[normalized]+1}, repeated at #{i+1})",
                                 para[:80].replace("\n", "\\n") + "..."))
            else:
                seen[normalized] = i

    # --- Check for content starting/ending mid-sentence ---
    first_char = body.lstrip()[0] if body.strip() else ""
    if first_char.islower():
        findings.append(("format", "INFO", "Content starts with lowercase (possible truncation at start)",
                         body[:60].replace("\n", "\\n")))

    # Check if content ends mid-sentence (no terminal punctuation)
    last_line = body.rstrip().split("\n")[-1].strip()
    if last_line and not re.search(r'[.!?"\'\)\]…]$', last_line) and len(last_line) > 20:
        findings.append(("format", "INFO", "Content may end mid-sentence",
                         f"...{last_line[-80:]}"))

    # --- Check for encoding artifacts ---
    encoding_issues = re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f]|â€™|â€"|â€œ|â€|Â |Ã©|Ã¨|Ã¼|â€¢', body)
    if encoding_issues:
        findings.append(("encoding", "WARNING", f"Possible encoding artifacts found ({len(encoding_issues)} instances)",
                         str(encoding_issues[:5])))

    return findings


def main():
    print("Loading ground truth...")
    with open(GT_PATH, "r", encoding="utf-8") as f:
        gt = json.load(f)
    print(f"  {len(gt)} entries loaded\n")

    all_findings = {}
    category_counts = defaultdict(int)
    severity_counts = defaultdict(int)
    files_by_category = defaultdict(set)

    for file_id in sorted(gt.keys()):
        entry = gt[file_id]
        findings = scan_entry(file_id, entry)
        if findings:
            all_findings[file_id] = findings
            for category, severity, desc, context in findings:
                category_counts[category] += 1
                severity_counts[severity] += 1
                files_by_category[category].add(file_id)

    # === Report ===
    print("=" * 90)
    print("GROUND TRUTH QUALITY SCAN REPORT")
    print("=" * 90)

    print(f"\nTotal entries scanned: {len(gt)}")
    print(f"Entries with findings: {len(all_findings)}")
    print(f"Entries clean:         {len(gt) - len(all_findings)}")
    print()

    print("Severity breakdown:")
    for sev in ["CRITICAL", "WARNING", "INFO"]:
        if severity_counts[sev]:
            print(f"  {sev}: {severity_counts[sev]}")
    print()

    print("Category breakdown:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        file_count = len(files_by_category[cat])
        print(f"  {cat:20s}: {count:4d} findings in {file_count:3d} files")
    print()

    # Print all WARNING+ findings grouped by category
    print("-" * 90)
    print("DETAILED FINDINGS (WARNING+)")
    print("-" * 90)

    # Group by category
    categories_with_warnings = defaultdict(list)
    for file_id, findings in sorted(all_findings.items()):
        for category, severity, desc, context in findings:
            if severity in ("CRITICAL", "WARNING"):
                categories_with_warnings[category].append((file_id, desc, context))

    for category in sorted(categories_with_warnings.keys()):
        items = categories_with_warnings[category]
        print(f"\n=== {category.upper()} ({len(items)} findings) ===")
        for file_id, desc, context in items:
            print(f"  [{file_id}] {desc}")
            if context:
                # Truncate context for display
                ctx = context[:120]
                print(f"           {ctx}")

    # Save detailed results
    results_path = ROOT / "quality_scan_results.json"
    serializable = {}
    for file_id, findings in all_findings.items():
        serializable[file_id] = [
            {"category": c, "severity": s, "description": d, "context": ctx}
            for c, s, d, ctx in findings
        ]
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False, sort_keys=True)
    print(f"\n\nDetailed results saved to: {results_path}")

    return 1 if severity_counts.get("CRITICAL", 0) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
