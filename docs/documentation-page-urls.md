# Documentation Page Benchmark URLs

Selected documentation/reference page URLs for the benchmark expansion.
Selection criteria: substantive technical content, mix of doc generators/platforms, diverse content types (tutorials, API refs, guides, man pages), publicly accessible.

**Legend:**
- Confirmed = URL verified, returns 200 via curl

---

## Ground Truth Definition for Documentation Pages

**INCLUDE:**
- Page title / heading
- All narrative/explanatory text (descriptions, explanations, notes, warnings)
- Code blocks and code snippets (code is core content on doc pages)
- Admonitions / callouts (Note, Warning, Tip, etc.)
- Tables that are part of the content (parameter descriptions, option tables)
- Inline code references

**EXCLUDE:**
- Sidebar navigation / table of contents
- Breadcrumbs
- Version selectors / language switchers
- "Edit this page" / "Report an issue" links
- Search bars
- Footer navigation / copyright
- "On this page" / "In this article" mini-TOC
- Previous/Next page navigation
- Header site navigation
- Cookie/consent banners

---

## 1. Sphinx / ReadTheDocs (5 pages)

| # | ID | Project | URL | Content Type |
|---|-----|---------|-----|--------------|
| 1 | 0661 | Django | https://docs.djangoproject.com/en/5.1/ref/models/querysets/ | API reference |
| 2 | 0662 | Flask | https://flask.palletsprojects.com/en/stable/quickstart/ | Tutorial |
| 3 | 0663 | Requests | https://requests.readthedocs.io/en/latest/user/advanced/ | Guide |
| 4 | 0664 | SQLAlchemy | https://docs.sqlalchemy.org/en/20/orm/quickstart.html | Tutorial |
| 5 | 0665 | Celery | https://docs.celeryq.dev/en/stable/userguide/tasks.html | Guide |

---

## 2. Language Official Docs (5 pages)

| # | ID | Language | URL | Content Type |
|---|-----|----------|-----|--------------|
| 1 | 0666 | Python | https://docs.python.org/3/library/itertools.html | Standard library ref |
| 2 | 0667 | Rust | https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html | Book chapter |
| 3 | 0668 | Go | https://go.dev/doc/effective_go | Style guide |
| 4 | 0669 | TypeScript | https://www.typescriptlang.org/docs/handbook/2/types-from-types.html | Handbook |
| 5 | 0670 | PostgreSQL | https://www.postgresql.org/docs/current/sql-select.html | SQL reference |

---

## 3. MDN Web Docs (3 pages)

| # | ID | Topic | URL | Content Type |
|---|-----|-------|-----|--------------|
| 1 | 0671 | Fetch API | https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch | API guide |
| 2 | 0672 | CSS Flexbox | https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Flexbox | Tutorial |
| 3 | 0673 | Promises | https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises | Guide |

---

## 4. Docusaurus / Modern React-based (4 pages)

| # | ID | Project | URL | Content Type |
|---|-----|---------|-----|--------------|
| 1 | 0674 | React | https://react.dev/learn | Tutorial |
| 2 | 0675 | Docusaurus | https://docusaurus.io/docs | Getting started |
| 3 | 0676 | Supabase | https://supabase.com/docs/guides/auth | Guide |
| 4 | 0677 | Tauri | https://v2.tauri.app/start/ | Getting started |

---

## 5. MkDocs / Material (2 pages)

| # | ID | Project | URL | Content Type |
|---|-----|---------|-----|--------------|
| 1 | 0678 | FastAPI | https://fastapi.tiangolo.com/tutorial/ | Tutorial |
| 2 | 0679 | Pydantic | https://docs.pydantic.dev/latest/concepts/models/ | Concepts |

---

## 6. API Reference Docs (2 pages)

| # | ID | Service | URL | Content Type |
|---|-----|---------|-----|--------------|
| 1 | 0680 | Stripe | https://docs.stripe.com/api/charges | API reference |
| 2 | 0681 | Twilio | https://www.twilio.com/docs/sms/send-messages | API guide |

---

## 7. Wiki-style Docs (3 pages)

| # | ID | Wiki | URL | Content Type |
|---|-----|------|-----|--------------|
| 1 | 0682 | ArchWiki | https://wiki.archlinux.org/title/OpenSSH | Reference |
| 2 | 0683 | Gentoo Wiki | https://wiki.gentoo.org/wiki/Portage | Reference |
| 3 | 0684 | Nginx | https://nginx.org/en/docs/http/ngx_http_core_module.html | Module reference |

---

## 8. DevOps / Infrastructure Docs (3 pages)

| # | ID | Project | URL | Content Type |
|---|-----|---------|-----|--------------|
| 1 | 0685 | Kubernetes | https://kubernetes.io/docs/concepts/workloads/pods/ | Concepts |
| 2 | 0686 | Terraform | https://developer.hashicorp.com/terraform/language/resources/syntax | Language ref |
| 3 | 0687 | Ansible | https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_intro.html | Guide |

---

## 9. Man Pages / CLI Docs (2 pages)

| # | ID | Tool | URL | Content Type |
|---|-----|------|-----|--------------|
| 1 | 0688 | grep | https://man7.org/linux/man-pages/man1/grep.1.html | Man page |
| 2 | 0689 | git-commit | https://git-scm.com/docs/git-commit | Man page |

---

## Summary

| Status | Count |
|--------|-------|
| Confirmed (auto-download) | 29 |
| Manual (needs browser save) | 0 |
| **Total** | **29** |

### Platform/Generator Distribution

| Platform | Count |
|----------|-------|
| Sphinx / ReadTheDocs | 5 |
| Language official docs | 5 |
| MDN | 3 |
| Docusaurus / React-based | 4 |
| MkDocs / Material | 2 |
| API reference | 2 |
| Wiki-style | 3 |
| DevOps/infra docs | 3 |
| Man pages | 2 |
| **Total** | **29** |

### Content Type Distribution

| Type | Count |
|------|-------|
| Tutorial / Getting started | 8 |
| API / Library reference | 8 |
| Guide / Concepts | 8 |
| Man page / CLI reference | 2 |
| Book chapter | 1 |
| Style guide | 1 |
| Module reference | 1 |

### File IDs: 0661-0689

---

## Next Steps

1. Download HTML files (all 29 should be auto-downloadable)
2. Create ground truth annotations (title + full content including code blocks)
3. Run benchmark extractors
