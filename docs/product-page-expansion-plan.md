# Product Page Benchmark Expansion Plan

## 1. Ground Truth Definition for Product Pages

### What counts as "main content" on a product page?

**INCLUDE:**
- Product title / name
- Main product description / body text (the marketing copy, feature narrative, etc.)

**EXCLUDE:**
- Price, sale price, currency info
- Specs/features tables
- Customer reviews and ratings
- Star ratings, review counts
- Seller / vendor info
- Shipping details, delivery estimates
- Stock/availability status
- "Add to cart" / buy buttons
- Variant selectors (size, color, quantity)
- Image galleries, thumbnails
- Breadcrumbs, category navigation
- "Customers also bought" / "Related products"
- Recently viewed products
- Product comparison widgets
- Size guides, measurement charts
- Return/warranty policy text
- Social share buttons
- Brand store links
- Product Q&A sections

### Title
- The product name/title

### Author
- The brand name, if clearly indicated. Otherwise null.

### Decisions
- **Description only**: We extract the narrative product description. Specs tables, bullet-point feature lists that are separate from the description, and structured data are excluded.
- **Multiple description sections**: Some sites have a short description near the title and a longer one below. Include both if they contain unique text.
- **Brand as author**: Use the product brand/manufacturer as author when available.

---

## 2. Product Page Selection Criteria

For each site, select product pages that:
- Have a **substantive text description** (not just a title + bullet specs)
- Are a **single product page** (not a category, listing, or search results page)
- Are **publicly accessible** (no login, no age gate)
- Cover **diverse product categories** (electronics, clothing, food, books, home, outdoor, etc.)
- Represent the platform's **default product template** (not heavily customized)

---

## 3. Collection Plan: ~60 Product Pages

### Shopify (~28% market share) — 12 pages
Pick from well-known Shopify stores across different verticals:

| # | Store | Category |
|---|-------|----------|
| 1 | Allbirds | Footwear |
| 2 | Gymshark | Athletic apparel |
| 3 | Bombas | Socks/basics |
| 4 | Death Wish Coffee | Food/beverage |
| 5 | Brooklinen | Home/bedding |
| 6 | Ruggable | Home/rugs |
| 7 | MVMT Watches | Watches/accessories |
| 8 | Chubbies | Casual apparel |
| 9 | Ridge Wallet | Accessories |
| 10 | Nomad | Tech accessories |
| 11 | Huel | Nutrition |
| 12 | Beardbrand | Grooming |

### WooCommerce (~33% market share) — 10 pages
WordPress + WooCommerce stores:

| # | Store | Category |
|---|-------|----------|
| 1 | Weber Grills | Outdoor/grills |
| 2 | Angry Orange | Pet products |
| 3 | Daelmans | Food (stroopwafels) |
| 4 | ClickMinded | Digital/education |
| 5 | Porter & York | Gourmet food |
| 6 | AeroPress | Coffee equipment |
| 7 | Singer | Sewing machines |
| 8 | All Blacks (official shop) | Sports merchandise |
| 9 | Sodastream (accessories) | Kitchen appliances |
| 10 | Ripley's Believe It or Not (shop) | Novelty/gifts |

### Magento/Adobe Commerce — 6 pages
Enterprise-grade stores:

| # | Store | Category |
|---|-------|----------|
| 1 | Helly Hansen | Outdoor apparel |
| 2 | Bulk Powders | Nutrition/supplements |
| 3 | Ahmad Tea | Tea/beverages |
| 4 | Liebherr | Appliances |
| 5 | HP (accessories store) | Tech accessories |
| 6 | Ford Accessories | Auto accessories |

### BigCommerce — 4 pages

| # | Store | Category |
|---|-------|----------|
| 1 | Skullcandy | Audio/headphones |
| 2 | Solo Stove | Outdoor/fire pits |
| 3 | Natori | Fashion |
| 4 | Humanscale | Office furniture |

### Squarespace Commerce — 4 pages

| # | Store | Category |
|---|-------|----------|
| 1 | TBD | Design/lifestyle |
| 2 | TBD | Artisan goods |
| 3 | TBD | Jewelry |
| 4 | TBD | Art prints |

### Wix eCommerce — 3 pages

| # | Store | Category |
|---|-------|----------|
| 1 | TBD | Small business |
| 2 | TBD | Handmade goods |
| 3 | TBD | Specialty food |

### PrestaShop — 3 pages

| # | Store | Category |
|---|-------|----------|
| 1 | TBD | EU retailer |
| 2 | TBD | EU retailer |
| 3 | TBD | EU retailer |

### OpenCart — 2 pages

| # | Store | Category |
|---|-------|----------|
| 1 | TBD | General retail |
| 2 | TBD | General retail |

### Custom Platform / Major Retailers — 16 pages
Major sites with proprietary e-commerce platforms:

| # | Site | Platform | Category |
|---|------|----------|----------|
| 1 | Amazon | Custom | Electronics |
| 2 | Amazon | Custom | Books |
| 3 | eBay | Custom | Collectibles |
| 4 | eBay | Custom | Electronics |
| 5 | Walmart | Custom | Home goods |
| 6 | Etsy | Custom | Handmade crafts |
| 7 | Etsy | Custom | Vintage items |
| 8 | Best Buy | Custom | Electronics |
| 9 | Target | Custom | Home/kitchen |
| 10 | Wayfair | Custom | Furniture |
| 11 | Home Depot | Custom | Tools/hardware |
| 12 | IKEA | Custom | Furniture |
| 13 | Apple Store | Custom | Consumer electronics |
| 14 | Nike | Custom | Athletic shoes |
| 15 | Zalando | Custom | Fashion (EU) |
| 16 | B&H Photo | Custom | Camera/electronics |

**Total: ~60 product pages**

### Product Category Diversity

| Category | Target Count |
|----------|-------------|
| Electronics/Tech | 8-10 |
| Apparel/Fashion | 8-10 |
| Food/Beverage | 5-6 |
| Home/Furniture | 6-8 |
| Outdoor/Sports | 5-6 |
| Beauty/Grooming | 3-4 |
| Accessories | 4-5 |
| Books/Media | 2-3 |
| Other (pets, gifts, etc.) | 4-6 |

---

## 4. File IDs

Continue from the forum expansion: 0580-0639 (60 pages).

---

## 5. Collection Process

### Step 1: Verify platforms
Confirm each store still uses the expected platform (stores migrate).

### Step 2: Select specific product URLs
Browse each store and pick a product with a substantive description.

### Step 3: Save HTML
Download via requests/Playwright or manual browser save.

### Step 4: Create ground truth
Extract product title + description text for each page.

### Step 5: Assign page type
All files get `page_type.primary = "product"`
