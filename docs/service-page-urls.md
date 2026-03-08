# Service Page Benchmark URLs

Selected service/feature page URLs for the benchmark expansion.
Service pages are notoriously messy — CTAs, testimonials, trust badges, pricing, and forms mixed with actual service descriptions. They dominate competitive commercial search results.

Source list: `/home/slimbook/CascadeProjects/windsurf-project/output/service_page_urls.txt` (689K URLs) plus curated major brand pages.

**Legend:**
- Confirmed = URL verified, returns 200 via curl
- Manual = needs browser download

---

## Ground Truth Definition for Service Pages

**INCLUDE:**
- Service/feature title
- Service description narrative (what the service is, how it works, benefits explained)
- Feature lists that are part of the description narrative
- "How it works" sections with explanatory text

**EXCLUDE:**
- CTAs ("Get started", "Request a demo", "Contact us")
- Pricing tables and plan comparisons
- Testimonials and customer quotes
- Client logos / trust badges / awards
- Case study teasers
- FAQ sections (separate content type)
- Contact forms
- "Related services" or "Other products" links
- Statistics/metrics callouts ("10,000+ customers", "99.9% uptime")
- Header/footer navigation
- Cookie/consent banners

---

## 1. Major SaaS / Cloud Service Pages (10 pages)

| # | ID | Company | URL | Category | Status |
|---|-----|---------|-----|----------|--------|
| 1 | 0690 | HubSpot | https://www.hubspot.com/products/marketing | Marketing automation | Confirmed |
| 2 | 0691 | Salesforce | https://www.salesforce.com/crm/ | CRM | Confirmed |
| 3 | 0692 | Cloudflare | https://www.cloudflare.com/application-services/products/cdn/ | CDN / Security | Confirmed |
| 4 | 0693 | Zendesk | https://www.zendesk.com/service/ | Customer support | Confirmed |
| 5 | 0694 | Mailchimp | https://mailchimp.com/features/email/ | Email marketing | Confirmed |
| 6 | 0695 | Webflow | https://webflow.com/cms | CMS | Confirmed |
| 7 | 0696 | Monday.com | https://monday.com/work-management | Project management | Confirmed |
| 8 | 0697 | Freshdesk | https://www.freshworks.com/freshdesk/ | Helpdesk | Confirmed |
| 9 | 0698 | Stripe | https://stripe.com/payments | Payments | Confirmed |
| 10 | 0699 | Zapier | https://zapier.com/platform | Automation | Confirmed |

---

## 2. Cloud Provider Service Pages (3 pages)

| # | ID | Provider | URL | Category | Status |
|---|-----|----------|-----|----------|--------|
| 1 | 0700 | AWS | https://aws.amazon.com/lambda/ | Serverless compute | Confirmed |
| 2 | 0701 | Google Cloud | https://cloud.google.com/bigquery | Data warehouse | Confirmed |
| 3 | 0702 | Azure | https://azure.microsoft.com/en-us/products/functions | Serverless compute | Confirmed |

---

## 3. SEO / Marketing Tool Pages (3 pages)

| # | ID | Company | URL | Category | Status |
|---|-----|---------|-----|----------|--------|
| 1 | 0703 | Ahrefs | https://ahrefs.com/seo | SEO tools | Confirmed |
| 2 | 0704 | BrightLocal | https://www.brightlocal.com/local-seo-tools/ | Local SEO | Confirmed |
| 3 | 0705 | Intercom | https://www.intercom.com/customer-support-software | Support platform | Confirmed |

---

## 4. Freelance / Marketplace Service Pages (3 pages)

| # | ID | Platform | URL | Category | Status |
|---|-----|----------|-----|----------|--------|
| 1 | 0706 | Fiverr | https://www.fiverr.com/categories/writing-translation | Writing services | Confirmed |
| 2 | 0707 | Toptal | https://www.toptal.com/designers | Design talent | Confirmed |
| 3 | 0708 | Twilio | https://www.twilio.com/en-us/messaging | Messaging API | Confirmed |

---

## 5. Consulting / Professional Services (2 pages)

| # | ID | Firm | URL | Category | Status |
|---|-----|------|-----|----------|--------|
| 1 | 0709 | Deloitte | https://www2.deloitte.com/us/en/services/consulting.html | Management consulting | Confirmed |
| 2 | 0710 | PwC | https://www.pwc.com/us/en/services/consulting.html | Strategy consulting | Confirmed |

---

## 6. IT / Dev Agencies (from source list) (6 pages)

| # | ID | Agency | URL | Category | Status |
|---|-----|--------|-----|----------|--------|
| 1 | 0711 | LeewayHertz | https://www.leewayhertz.com/ai-development-company/ | AI development | Confirmed |
| 2 | 0712 | ScienceSoft | https://www.scnsoft.com/services/analytics/managed | Managed analytics | Confirmed |
| 3 | 0713 | Neoteric | https://neoteric.eu/services/progressive-web-app-development-company | PWA development | Confirmed |
| 4 | 0714 | SmartCat | https://smartcat.io/genai/ | GenAI services | Confirmed |
| 5 | 0715 | QBurst | https://www.qburst.com/en-in/software-testing-services/ | QA testing | Confirmed |
| 6 | 0716 | BrandWisdom | https://brandwisdom.in/services/digital-marketing-services-management/marketing-and-advertising/ | Digital marketing | Confirmed |

---

## 7. Creative / Design Services (from source list) (3 pages)

| # | ID | Agency | URL | Category | Status |
|---|-----|--------|-----|----------|--------|
| 1 | 0717 | DoodloDesigns | https://doodlodesigns.com/services/packaging/cosmetic-packaging-design | Packaging design | Confirmed |
| 2 | 0718 | Netsmartz | https://netsmartz.com/generative-ai-consulting-services/ | AI consulting | Confirmed |
| 3 | 0719 | LeverX | https://leverx.com/services/ai-consulting-services | SAP/AI consulting | Confirmed |

---

## Summary

| Status | Count |
|--------|-------|
| Confirmed (auto-download) | 30 |
| Manual (needs browser save) | 0 |
| **Total** | **30** |

### Service Category Distribution

| Category | Count |
|----------|-------|
| SaaS / Cloud platforms | 13 |
| SEO / Marketing tools | 3 |
| Freelance / Marketplace | 3 |
| Consulting / Professional | 2 |
| IT / Dev agencies | 6 |
| Creative / Design | 3 |
| **Total** | **30** |

### Page Characteristics

| Trait | Expected |
|-------|----------|
| Heavy CTA noise | Most pages |
| Testimonials mixed in | ~20 pages |
| Pricing tables | ~10 pages |
| "How it works" sections | ~15 pages |
| Client logos / badges | ~25 pages |
| Thin content (mostly visuals) | ~5 pages |
| Rich narrative description | ~15 pages |

### File IDs: 0690-0719

---

## Next Steps

1. Download HTML files (all 30 should be auto-downloadable)
2. Create ground truth annotations (service title + description narrative)
3. Run benchmark extractors
