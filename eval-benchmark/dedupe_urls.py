#!/usr/bin/env python3
"""Deduplicate URLs by base domain and filter against excluded domains."""
from urllib.parse import urlparse

def get_base_domain(domain):
    """Extract base domain, handling .co.uk, .com.au, etc."""
    if domain.startswith('www.'):
        domain = domain[4:]
    parts = domain.split('.')
    # Known multi-part TLDs
    multi_tlds = {'co.uk', 'com.au', 'co.nz', 'com.br', 'co.za', 'com.my',
                  'co.in', 'com.cn', 'org.uk', 'gov.uk', 'ac.uk', 'edu.au',
                  'gov.au', 'com.sg', 'com.hk', 'co.jp', 'com.mx', 'co.il',
                  'com.ar', 'gov.in', 'bearblog.dev', 'github.io', 'substack.com',
                  'wordpress.com', 'blogspot.com'}
    if len(parts) >= 3:
        potential_tld = '.'.join(parts[-2:])
        if potential_tld in multi_tlds:
            return '.'.join(parts[-3:])
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return domain

# Read excluded domains
with open('/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/eval-benchmark/excluded_domains.txt') as f:
    excluded = set(line.strip() for line in f if line.strip())

# Read URLs
with open('/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/eval-benchmark/urls_article.txt') as f:
    urls = [line.strip() for line in f if line.strip()]

print(f'Total URLs read: {len(urls)}')

# Deduplicate by base domain, filter excluded
domains_seen = set()
clean_urls = []
removed_excluded = []
removed_dupe = []

for url in urls:
    parsed = urlparse(url)
    domain = parsed.netloc
    if domain.startswith('www.'):
        domain = domain[4:]

    base_domain = get_base_domain(domain)

    # Check if base domain or any parent is excluded
    is_excluded = False
    parts = domain.split('.')
    for i in range(len(parts)):
        check_domain = '.'.join(parts[i:])
        if check_domain in excluded:
            is_excluded = True
            removed_excluded.append((url, check_domain))
            break

    if is_excluded:
        continue

    if base_domain in domains_seen:
        removed_dupe.append((url, base_domain))
        continue

    domains_seen.add(base_domain)
    clean_urls.append(url)

print(f'Removed as excluded: {len(removed_excluded)}')
for url, dom in removed_excluded:
    print(f'  EXCLUDED ({dom}): {url}')

print(f'Removed as duplicate domain: {len(removed_dupe)}')
for url, dom in removed_dupe[:30]:
    print(f'  DUPE ({dom}): {url}')
if len(removed_dupe) > 30:
    print(f'  ... and {len(removed_dupe) - 30} more')

print(f'Clean unique-domain URLs: {len(clean_urls)}')

# Write clean file
with open('/home/slimbook/web-content-extraction-benchmark/web-content-extraction-benchmark/eval-benchmark/urls_article.txt', 'w') as f:
    for url in clean_urls:
        f.write(url + '\n')

print(f'\nWrote {len(clean_urls)} URLs to urls_article.txt')
