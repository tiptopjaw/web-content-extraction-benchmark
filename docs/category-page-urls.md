# Category Page Benchmark URLs

Selected e-commerce category/listing page URLs for the benchmark expansion.
Selection criteria: publicly accessible, diverse platforms, mix of pages WITH and WITHOUT descriptive text.

**Legend:**
- Confirmed = URL verified, returns 200 via curl
- Manual = needs browser download (JS required or blocks automated requests)
- has-desc = page has category description / SEO text block
- no-desc = page is product grid only (no descriptive text)

---

## Ground Truth Definition for Category Pages

**INCLUDE:**
- Category title / heading
- Category description text (intro paragraph, SEO text block at top or bottom)
- Any narrative text that describes the category or helps shoppers understand it

**For no-desc pages:** Ground truth main_content will be empty or near-empty (just the category title). This tests that extractors correctly return minimal content rather than pulling in product card text, filter labels, or navigation.

**EXCLUDE:**
- Individual product cards (names, prices, thumbnails)
- Filter/facet navigation (size, color, price range selectors)
- Sort controls, pagination
- Breadcrumbs, category navigation trees
- "Recently viewed" or "Recommended" sections
- Newsletter signup forms
- Store policies, shipping info
- Cookie/privacy banners

---

## 1. Shopify (8 pages)

| # | ID | Store | URL | Desc | Status |
|---|-----|-------|-----|------|--------|
| 1 | 0632 | Allbirds | https://www.allbirds.com/collections/mens-runners | has-desc | Confirmed |
| 2 | 0633 | Gymshark | https://www.gymshark.com/collections/t-shirts-tops/mens | has-desc | Confirmed |
| 3 | 0634 | Brooklinen | https://www.brooklinen.com/collections/sheets | has-desc | Confirmed |
| 4 | 0635 | Ridge Wallet | https://ridge.com/collections/wallets | has-desc | Confirmed |
| 5 | 0636 | Beardbrand | https://www.beardbrand.com/collections/beard-oil | has-desc | Confirmed |
| 6 | 0637 | Skullcandy | https://www.skullcandy.com/collections/headphones | has-desc | Confirmed |
| 7 | 0638 | Death Wish Coffee | https://www.deathwishcoffee.com/collections/coffee | no-desc | Confirmed |
| 8 | 0639 | Bombas | https://bombas.com/collections/mens-socks | no-desc | Confirmed |

---

## 2. BigCommerce (4 pages)

| # | ID | Store | URL | Desc | Status |
|---|-----|-------|-----|------|--------|
| 1 | 0640 | UPLIFT Desk | https://www.upliftdesk.com/desk-accessories/ | has-desc | Confirmed |
| 2 | 0641 | Green Roads | https://greenroads.com/cbd-gummies | has-desc | Confirmed |
| 3 | 0642 | Green Roads | https://greenroads.com/thc-gummies | has-desc | Confirmed (rich FAQ content) |
| 4 | 0643 | UPLIFT Desk | https://www.upliftdesk.com/standing-desks/ | has-desc | Confirmed (replaces AS Colour — region blocked) |

---

## 3. PrestaShop (2 pages)

| # | ID | Store | URL | Desc | Status |
|---|-----|-------|-----|------|--------|
| 1 | 0644 | Esprit Barbecue | https://www.esprit-barbecue.fr/11-barbecue-charbon | has-desc | Confirmed (French, buying guide) |
| 2 | 0645 | Esprit Barbecue | https://www.esprit-barbecue.fr/10-barbecue-charbon | has-desc | Confirmed (French, FAQ + brand reviews) |

---

## 4. Magento (1 page)

| # | ID | Store | URL | Desc | Status |
|---|-----|-------|-----|------|--------|
| 1 | 0646 | Solo Stove | https://www.solostove.com/us/en-us/c/fire-pits | has-desc | Confirmed |

---

## 5. Custom Platform / Major Retailers (12 pages)

| # | ID | Site | URL | Desc | Status |
|---|-----|------|-----|------|--------|
| 1 | 0647 | IKEA | https://www.ikea.com/us/en/cat/bookcases-shelving-units-st002/ | has-desc | Confirmed |
| 2 | 0648 | IKEA | https://www.ikea.com/us/en/cat/sofas-fu003/ | has-desc | Confirmed |
| 3 | 0649 | Newegg | https://www.newegg.com/GPUs-Video-Graphics-Cards/SubCategory/ID-48 | has-desc | Confirmed |
| 4 | 0650 | Apple Store | https://www.apple.com/shop/buy-mac/macbook-air | has-desc | Confirmed |
| 5 | 0651 | iFixit | https://www.ifixit.com/Parts | has-desc | Confirmed |
| 6 | 0652 | iFixit | https://www.ifixit.com/Parts/iPhone | has-desc | Confirmed |
| 7 | 0653 | Target | https://www.target.com/c/bedding/-/N-5xtnr | has-desc | Confirmed |
| 8 | 0654 | Target | https://www.target.com/c/electronics/-/N-5xtg5 | no-desc | Confirmed (replaces Walmart — page not found) |
| 9 | 0655 | Amazon | https://www.amazon.com/Headphones-Accessories-Supplies/b?node=172541 | no-desc | Manual (captcha risk) |
| 10 | 0656 | Nike | https://www.nike.com/w/mens-running-shoes-37v7jznik1zy7ok | no-desc | Manual (JS-rendered) |
| 11 | 0657 | Nordstrom | https://www.nordstrom.com/browse/men/clothing/jackets-coats | no-desc | Confirmed |
| 12 | 0658 | eBay | https://www.ebay.com/b/Collectibles-Art/bn_7000259855 | no-desc | Confirmed |

---

## 6. WooCommerce (2 pages)

| # | ID | Store | URL | Desc | Status |
|---|-----|-------|-----|------|--------|
| 1 | 0659 | JOCO Cups | https://jococups.com/shop/ | has-desc | Confirmed |
| 2 | 0660 | Bird Buddy | https://mybirdbuddy.eu/shop/ | no-desc | Confirmed |

---

## Summary

| Status | Count |
|--------|-------|
| Confirmed (auto-download) | 27 |
| Manual (needs browser save) | 2 |
| **Total** | **29** |

### Description Text Distribution

| Type | Count |
|------|-------|
| has-desc (SEO/description text) | 20 |
| no-desc (product grid only) | 9 |
| **Total** | **29** |

### Platform Distribution

| Platform | Count |
|----------|-------|
| Shopify | 8 |
| Custom/Major Retailers | 12 |
| BigCommerce | 4 |
| PrestaShop | 2 |
| Magento | 1 |
| WooCommerce | 2 |
| **Total** | **29** |

### File IDs: 0632-0660

---

## Next Steps

1. Download HTML files (25 automated + 4 manual browser saves)
2. Create ground truth annotations (category title + description text where present)
3. Run benchmark extractors
