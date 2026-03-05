# Forum Benchmark Expansion Plan

## 1. Ground Truth Definition for Forum Pages

### What counts as "main content" on a forum thread?

**INCLUDE:**
- Original post (OP) — full text body
- All reply/response posts — each poster's own words only
- Code blocks within posts
- Inline images described by alt text (if relevant)

**EXCLUDE:**
- Nested/block quotes (duplicated content from other posts in the thread)
- User signatures
- User profile info (join date, post count, reputation, avatar)
- "Like" / "Thank" / reaction counts and lists
- Post metadata (Posted: Jan 5, 2025 — keep minimal, exclude verbose timestamps)
- Navigation (breadcrumbs, pagination, forum index links)
- Sidebar content (forum stats, online users, who's reading)
- Moderation notices ("This thread is locked", "Moved from X")
- Advertisement blocks
- "Share this thread" / social buttons
- "Similar threads" / "Related topics" sections
- Login/register prompts
- Forum header/footer chrome
- User rank badges / custom titles

### Title
- The thread title (not the forum name or category)

### Author
- The OP's username

### Decisions
- **Multi-page threads**: Page 1 only — we save the HTML of one page, GT covers that page's content.
- **Nested quotes**: Excluded — quotes duplicate content already present in the thread. Each post's own original words only.
- **Stack Overflow special case**: Include the question + all answers (each answer is like a reply). Exclude comments unless they contain substantive information. Exclude vote counts, badges, related questions sidebar.
- **Reddit special case**: Include the post + all visible comments. Exclude vote scores, user karma, collapsed/hidden comments, sidebar subreddit info.
- **Quora special case**: Include the question + all answers. Exclude "related questions", credential badges, follower counts.

---

## 2. Thread Selection Criteria

For each forum, select threads that:
- Have **3-15 replies** (not empty, not mega-threads)
- Contain **substantive text** (not just "thanks" or "+1" replies)
- Are on **page 1** (no pagination complexity)
- Cover **diverse topics** across forums (tech, hobbies, health, gaming, etc.)
- Represent the platform's **default theme/layout** (not heavily customized)
- Are **publicly accessible** (no login required)

---

## 3. Collection Plan: 80 Forum Thread Pages

### Discourse (12 threads) — 32.9% market share
Pick from showcase customers with diverse topics:

| # | Forum | URL Base | Topic Area |
|---|-------|----------|------------|
| 1 | OpenAI Community | community.openai.com | AI/Tech |
| 2 | Docker Forums | forums.docker.com | DevOps |
| 3 | Home Assistant | community.home-assistant.io | IoT/Home |
| 4 | Rust Users Forum | users.rust-lang.org | Programming |
| 5 | Let's Encrypt | community.letsencrypt.org | Security |
| 6 | Obsidian Forum | forum.obsidian.md | Productivity |
| 7 | Motley Fool | discussion.fool.com | Finance |
| 8 | EVE Online | forums.eveonline.com | Gaming |
| 9 | Brave Community | community.brave.com | Browser/Privacy |
| 10 | Netlify Answers | answers.netlify.com | Web Dev |
| 11 | MS Society | forum.mssociety.org.uk | Health |
| 12 | Straight Dope | boards.straightdope.com | General |

### XenForo (12 threads) — 21.1% market share
Pick from showcase + known large forums:

| # | Forum | URL Base | Topic Area |
|---|-------|----------|------------|
| 1 | MacRumors | forums.macrumors.com | Apple/Tech |
| 2 | ResetEra | resetera.com | Gaming |
| 3 | Head-Fi | head-fi.org | Audio |
| 4 | Physics Forums | physicsforums.com | Science |
| 5 | SpigotMC | spigotmc.org | Game Dev |
| 6 | Student Doctor Network | forums.studentdoctor.net | Education/Medical |
| 7 | AVForums | avforums.com | A/V Tech |
| 8 | Digital Point | digitalpoint.com | Marketing/SEO |
| 9 | Basenotes | basenotes.com | Fragrance/Lifestyle |
| 10 | Cameraderie | cameraderie.org | Photography |
| 11 | The Fighting Cock | thefightingcock.co.uk/forum | Sports (Football) |
| 12 | ALS Forums | alsforums.com | Health |

### vBulletin (10 threads) — legacy but widespread
Pick from known large vB forums:

| # | Forum | URL Base | Topic Area |
|---|-------|----------|------------|
| 1 | Ubuntu Forums | ubuntuforums.org | Linux |
| 2 | Warrior Forum | warriorforum.com | Marketing |
| 3 | FlyerTalk | flyertalk.com | Travel |
| 4 | AVS Forum | avsforum.com | Home Theater |
| 5 | WatchUSeek | watchuseek.com | Watches/Luxury |
| 6 | MTBR | forums.mtbr.com | Mountain Biking |
| 7 | HysterSisters | hystersisters.com | Women's Health |
| 8 | Reef Central | reefcentral.com | Aquariums/Pets |
| 9 | Web Hosting Talk | webhostingtalk.com | Web Hosting |
| 10 | Toyota Nation | toyotanation.com | Automotive |

### phpBB (8 threads) — 3% market share
Pick from showcase + known forums:

| # | Forum | URL Base | Topic Area |
|---|-------|----------|------------|
| 1 | Raspberry Pi | forums.raspberrypi.com | Hardware/DIY |
| 2 | VirtualBox | forums.virtualbox.org | Virtualization |
| 3 | FreeBSD | forums.freebsd.org | OS |
| 4 | Bogleheads | bogleheads.org | Investing/Finance |
| 5 | Audacity | forum.audacityteam.org | Audio Software |
| 6 | NationStates | forum.nationstates.net | Gaming/Simulation |
| 7 | Arch Linux | bbs.archlinux.org | Linux |
| 8 | MozillaZine | forums.mozillazine.org | Browser/Mozilla |

### Invision Community (6 threads) — ~2.5% market share

| # | Forum | URL Base | Topic Area |
|---|-------|----------|------------|
| 1 | Corsair Forum | forum.corsair.com | PC Hardware |
| 2 | Kerbal Space Program | forum.kerbalspaceprogram.com | Gaming/Space |
| 3 | Evernote Forum | discussion.evernote.com | Productivity |
| 4 | Squarespace Forum | forum.squarespace.com | Web Design |
| 5 | Affinity Forum | forum.affinity.serif.com | Design Software |
| 6 | PrestaShop | prestashop.com/forums | E-commerce |

### NodeBB (6 threads) — ~2% market share

| # | Forum | URL Base | Topic Area |
|---|-------|----------|------------|
| 1 | NodeBB Community | community.nodebb.org | Meta/Tech |
| 2 | LTT Forums | linustechtips.com | PC/Tech |
| 3 | Meatgistics | meatgistics.waltonsinc.com | Food/Hobby |
| 4 | Subrion | subrion.org/forum | CMS |
| 5 | Manga Café | mangacafe.org | Anime/Entertainment |
| 6 | Pair Network | community.pair.com | Web Hosting |

### Other Platform Software (6 threads)
Less common platforms for breadth:

| # | Forum | URL Base | Platform | Topic Area |
|---|-------|----------|----------|------------|
| 1 | Arch Linux (FluxBB) | bbs.archlinux.org | FluxBB | Linux |
| 2 | SMF demo / community | simplemachines.org/community | SMF | Meta |
| 3 | Flarum Community | discuss.flarum.org | Flarum | Meta/Tech |
| 4 | MyBB Community | community.mybb.com | MyBB | Meta/Tech |
| 5 | Vanilla Community | open.vanillaforums.com | Vanilla | Meta/Tech |
| 6 | Tapatalk forum | tapatalk.com | Tapatalk | Mobile/Meta |

### Custom/Unique Platforms (20 threads)
Major sites with custom forum software — critical for extraction robustness:

| # | Forum | URL Base | Platform | Topic Area |
|---|-------|----------|----------|------------|
| 1 | Reddit (new) | reddit.com | Custom (React) | Tech |
| 2 | Reddit (old) | old.reddit.com | Custom (legacy) | Science |
| 3 | Reddit (new) | reddit.com | Custom (React) | Lifestyle |
| 4 | Stack Overflow | stackoverflow.com | Custom | Programming |
| 5 | Super User | superuser.com | Custom (SE) | Tech Support |
| 6 | Server Fault | serverfault.com | Custom (SE) | Sysadmin |
| 7 | Ask Ubuntu | askubuntu.com | Custom (SE) | Linux |
| 8 | Hacker News | news.ycombinator.com | Arc | Tech/Startups |
| 9 | Quora | quora.com | Custom | Science |
| 10 | Quora | quora.com | Custom | History |
| 11 | Slashdot | slashdot.org | Slash | Tech News |
| 12 | 4chan | boards.4chan.org | Custom | Technology (/g/) |
| 13 | Lemmy (lemmy.world) | lemmy.world | Lemmy/Rust | Tech |
| 14 | Lemmy (lemmy.ml) | lemmy.ml | Lemmy/Rust | FOSS |
| 15 | GameFAQs | gamefaqs.gamespot.com | Custom | Gaming |
| 16 | Something Awful | forums.somethingawful.com | Custom | General |
| 17 | Nairaland | nairaland.com | Custom (PHP) | General (Nigeria) |
| 18 | The Student Room | thestudentroom.co.uk | Custom | Education (UK) |
| 19 | Mumsnet | mumsnet.com/talk | Custom | Parenting (UK) |
| 20 | CruiseCritic | cruisecritic.com/cc | Custom | Travel |

**Total: 80 thread pages**

### Topic Diversity Summary

| Topic Area | Count | Sources |
|------------|-------|---------|
| Tech/Programming | 18 | SO, HN, Rust, Docker, Arch, etc. |
| Gaming | 8 | EVE, ResetEra, KSP, GameFAQs, etc. |
| Health/Medical | 4 | MS Society, ALS, HysterSisters, Student Doctor |
| Finance/Investing | 3 | Bogleheads, Motley Fool, etc. |
| Lifestyle/Hobbies | 10 | Head-Fi, WatchUSeek, Cameras, Fragrance, etc. |
| Science/Education | 5 | Physics Forums, Student Room, Ask Ubuntu, etc. |
| Automotive/Sports | 4 | Toyota Nation, MTBR, Fighting Cock, etc. |
| General/Regional | 6 | Reddit, Nairaland, Straight Dope, Mumsnet, etc. |
| Travel | 3 | FlyerTalk, CruiseCritic, etc. |
| Home/DIY | 3 | Home Assistant, Raspberry Pi, Reef Central |
| Marketing/Business | 4 | Digital Point, Warrior Forum, Web Hosting Talk, etc. |
| Entertainment | 4 | 4chan, Something Awful, Manga Café, etc. |
| Meta/Platform | 6 | Flarum, MyBB, SMF, Vanilla, NodeBB, etc. |

---

## 4. Collection Process

### Step 1: Select specific threads
For each forum above, manually browse and pick a thread that meets the selection criteria (3-15 replies, substantive content, page 1, public).

### Step 2: Save HTML
Save the full rendered HTML of each thread page. Use browser "Save As" or wget/curl to capture the complete page including inline styles.

### Step 3: Assign file IDs
Continue from the existing benchmark numbering (0501, 0502, ..., 0580).

### Step 4: Create ground truth
Use the annotation tool to mark:
- Thread title
- OP author username
- Main content (all post bodies, OP + replies)
- "with" snippets from post content
- "without" snippets from signatures, sidebars, nav, user metadata

### Step 5: Assign page type
All 80 files get `page_type.primary = "forum"`

---

## 5. Estimated Effort

| Task | Time Estimate |
|------|---------------|
| Select 80 specific thread URLs | 3-4 hours |
| Save HTML files | 2-3 hours |
| Create ground truth (80 files × ~10 min each) | 13-15 hours |
| Validation & quality check | 2-3 hours |
| **Total** | **~22 hours** |

---

## 6. Success Criteria

After expansion, we should have:
- 80 forum thread pages across 12+ platform families
- Ground truth annotations consistent with the rules above
- rs-trafilatura forum F1 baseline measured on all 80
- Clear signal on which platform families are hardest to extract
- Diverse topic coverage (tech, health, finance, gaming, lifestyle, etc.)

This gives enough data to:
1. Develop platform-specific extraction heuristics in rs-trafilatura
2. Test and validate those heuristics per platform family
3. Compare LLM-based extractors on forum content specifically
4. Identify common DOM patterns per platform for detection heuristics
