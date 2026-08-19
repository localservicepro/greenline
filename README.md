# Greenline Services — website

Static marketing site for **Greenline Services**, a lawn, garden and property
maintenance business at 2/15 St Johns Ave, Frankston VIC 3199.

Built to the SEO / GEO / AEO strategy in the client research document: one page
per money keyword, no cannibalisation, structured data throughout, and answer-first
copy so the content can be lifted by AI assistants as well as by Google.

---

## Pages

| URL | Target keyword | Vol/mo | Difficulty |
|---|---|---|---|
| `/` | lawn mowing frankston | 140 | 23 |
| `/services/` | lawn mowing services frankston | 30 | 25 |
| `/services/gutter-cleaning/` | gutter cleaning frankston | 110 | 32 |
| `/services/rubbish-removal/` | rubbish removal frankston | 110 | 31 |
| `/services/garden-maintenance/` | gardener frankston | 70 | 33 |
| `/services/lawn-mowing/` | lawn mowing mornington | 40 | 22 |
| `/services/hedge-trimming/` | hedge trimming frankston | 10 | 17 |
| `/services/garden-clean-ups/` | garden clean up frankston | 10 | 29 |
| `/about/` | brand / entity |  |  |
| `/contact/` | brand / navigational |  |  |

No two pages share a primary keyword. The homepage takes `lawn mowing frankston`,
so the lawn mowing service page targets `lawn mowing mornington` instead of
competing with it.

Deliberately **not** targeted, per the research: `hard rubbish frankston`,
`hard waste collection frankston` and their variants (720/mo each). Those are
council-service intent and will not book a paid job.

---

## Build

Every page is generated from `tools/build.py`, so the nav, footer, schema,
canonicals and metadata cannot drift apart across ten pages.

```bash
python3 tools/build.py     # no dependencies, stdlib only
```

**Edit content in `tools/build.py`, not in the generated `.html` files** — a
rebuild overwrites them. Each generated file carries a banner comment saying so.

Generated: `index.html`, `about/`, `contact/`, `services/` (hub + 6 service
pages), `404.html`, `sitemap.xml`, `robots.txt`.

Hand-written: `assets/css/site.css`, `assets/js/site.js`.

## Local preview

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

Clean URLs (`/services/lawn-mowing/`) work on any host that serves
`index.html` from a directory — Netlify, Cloudflare Pages, GitHub Pages, Apache,
nginx. No build step or server runtime is required.

---

## Images — one action needed before launch

The 12 photographs were generated with Recraft V4.1 and currently load from the
generator's CDN. **Before this site goes live, pull them onto the client's own
domain:**

```bash
bash tools/localise-images.sh
python3 tools/build.py
```

That downloads everything into `assets/img/`, flips `USE_LOCAL_IMAGES` in the
build script, and rebuilds so nothing points off-domain. Recommended follow-up
for Core Web Vitals — convert to WebP and resize the hero:

```bash
for f in assets/img/*.png; do cwebp -q 82 "$f" -o "${f%.png}.webp"; done
```

Alt text for every image lives in `IMG_ALT` in `tools/build.py` and is written
for a person, with the keyword carried naturally.

---

## SEO / GEO / AEO implementation

**On-page**
- One `<h1>` per page, containing the target keyword
- Keyword density 1.3–1.5% on all eight ranking pages (measured, not estimated)
- Meta titles ≤ 60 chars, descriptions 120–158 chars
- Self-referencing canonical on every page
- Descriptive alt text on every image
- All 18 suburbs named as readable text, not decoration
- Internal links: homepage → every service page, service pages → back and across

**Structured data**
- `LocalBusiness` + `HomeAndConstructionBusiness` with full NAP, geo coordinates,
  opening hours, `areaServed` for all 18 suburbs and a `hasOfferCatalog`
- `Service` on every service page, referencing the business by `@id`
- `FAQPage` on every FAQ block
- `BreadcrumbList` site-wide, with visible breadcrumbs to match
- `WebSite`, `AboutPage`, `ContactPage`

**Answer engines (GEO/AEO)**
- Each service page opens with a bolded direct-answer paragraph stating the
  service, the business, the suburbs and the pricing model in one block — the
  shape an AI assistant can quote
- Every FAQ question carries both a service and a location, so it is answered
  from this site rather than from general knowledge
- `robots.txt` explicitly allows GPTBot, OAI-SearchBot, PerplexityBot, ClaudeBot
  and Google-Extended

**Local**
- Google Business Profile map embedded on the homepage, About and Contact
- NAP identical on every page and matching the GBP listing exactly
- `geo.position` / `ICBM` meta tags

---

## Launch checklist

- [ ] Register `greenlineservices.com.au` and enable HTTPS
- [ ] Confirm `SITE` in `tools/build.py` matches the live domain, then rebuild
- [ ] Run `tools/localise-images.sh` so no images load from an external CDN
- [ ] Replace the quote form's `mailto:` fallback with a real endpoint
      (Formspree, Netlify Forms, Web3Forms) — see `assets/js/site.js`
- [ ] Verify the property in Google Search Console, submit `sitemap.xml`
- [ ] Request indexing on the homepage and all six service pages
- [ ] Connect GA4; set quote-form submits and `tel:` taps as conversion events
- [ ] Add the website URL to the Google Business Profile
- [ ] Test the rendered schema in Google's Rich Results Test

## Not built (phase two)

Suburb landing pages, the three blog articles, and pages for pressure washing
and commercial property maintenance — all scoped in the research document as
later phases.
