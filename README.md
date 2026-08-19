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

## Quote form → GoHighLevel

The quote form posts six fields, named to map straight onto the CRM contact
fields:

| Form field | `name` | CRM field |
|---|---|---|
| Name | `full_name` | `{{contact.full_name}}` |
| Email | `email` | `{{contact.email}}` |
| Phone | `phone` | `{{contact.phone}}` |
| Property address | `property_address` | `{{contact.property_address}}` |
| Services needed | `service_needed` | `{{contact.service_needed}}` |
| Job notes | `job_notes` | `{{contact.job_notes}}` |

`property_address`, `service_needed` and `job_notes` are custom fields — create
them in **Settings → Custom Fields** in GHL before the first submission, or
those three values will be dropped while name, email and phone still land.

The GHL tracking script is in the `<head>` of every page. In GHL, enable
**Form Analytics** and **Form Submissions** in Settings or nothing is recorded.

The build satisfies all five of GHL's capture requirements, and there is an
automated check for them (see *Verifying* below):

1. Form Analytics and Form Submissions enabled — **your side, in GHL settings**
2. Real `<form>` in the page DOM, no iframe ✓
3. Every field has a `name`, nothing is `disabled`, plus
   `<input type="email" name="email">` and `<input type="tel" name="phone">` ✓
4. Submits through the native submit event via `<button type="submit">` ✓
5. No JS blocks that event ✓

**This last one is a live constraint, not a one-off.** `assets/js/site.js`
deliberately has no submit handler on the form. Adding one that calls
`preventDefault()` on a valid submit will silently stop every lead reaching the
CRM — the form will still look like it works.

### Two forms per page

Most pages carry two copies of the form: the inline one, and the quote popup
(`#quote-modal`) that the header CTA and section CTAs open. Both are real
`<form>` elements in the DOM with the same six field names, so GHL captures
whichever is submitted.

Their ids are prefixed (`qf-` inline, `qm-` modal) so they never collide —
`tools/check.py` fails on duplicate ids and validates *every* form on a page,
not just the first.

The contact page is the exception: its form sits in the hero, so it ships no
modal and the header CTA scrolls to the form instead. Any `data-quote-open`
trigger falls back gracefully — modal if present, otherwise scroll to `#quote`,
otherwise follow the link to `/contact/`.

The popup is keyboard-accessible: `role="dialog"`, `aria-modal`, focus moves to
the first field on open, Tab is trapped inside it, Escape and the backdrop
close it, and focus returns to the trigger.

### Where submissions go

`FORM_ACTION` in `tools/build.py` defaults to a `GET` to `/thank-you/`. That
works on any static host with no backend, and GHL still captures the submission
from the submit event.

The tradeoff: a GET puts the lead's name, email, phone and address in the query
string, so they land in the host's access logs. The thank-you page strips them
from the address bar 1.5s after load so they do not sit in browser history or
leak through the referrer, but the logs still see them.

**Before launch, point the form at a real endpoint** so leads also arrive by
email and are not carried in a URL. Both settings are at the top of
`tools/build.py`:

```python
FORM_ACTION = "https://formspree.io/f/XXXXXXXX"
FORM_METHOD = "post"
FORM_REDIRECT_FIELD = "_next"        # Formspree redirect field
```

Rebuild and the hidden redirect field is written in automatically, pointing at
`/thank-you/`. Web3Forms works the same way with `redirect` plus an
`access_key` in `FORM_HIDDEN`.

Relying on the tracking script alone means a lead is lost if the script fails
to load — a real endpoint gives you a second copy.

## Thank-you page

`/thank-you/` is `noindex, follow` and kept out of `sitemap.xml`. It confirms
the request, sets the callback expectation, and cross-sells three services.
It is a clean conversion trigger for a GHL workflow or a GA4 goal.

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
- [ ] Enable Form Analytics and Form Submissions in GHL settings
- [ ] Create the `property_address`, `service_needed` and `job_notes` custom
      fields in GHL
- [ ] Point `FORM_ACTION` at a real form endpoint so leads also arrive by email
      and are not carried in a query string
- [ ] Submit a live test and confirm the contact appears in GHL with all six
      fields populated
- [ ] Verify the property in Google Search Console, submit `sitemap.xml`
- [ ] Request indexing on the homepage and all six service pages
- [ ] Connect GA4; set quote-form submits and `tel:` taps as conversion events
- [ ] Add the website URL to the Google Business Profile
- [ ] Test the rendered schema in Google's Rich Results Test

## Verifying

`tools/check.py` runs the whole suite — HTML nesting, JSON-LD parsing, one h1
per page, title and description lengths, canonicals, single robots tag, image
alt text, duplicate ids, broken internal links, the GHL field mapping and the
five capture requirements, and keyword density against each page's target.

```bash
python3 tools/build.py && python3 tools/check.py
```

## Not built (phase two)

Suburb landing pages, the three blog articles, and pages for pressure washing
and commercial property maintenance — all scoped in the research document as
later phases.
