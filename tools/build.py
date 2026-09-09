#!/usr/bin/env python3
"""
Prestige Property Care — static site generator.

Builds every page in the site from the shared chrome + per-page content below,
so navigation, schema, canonicals and metadata can never drift between pages.

Usage:  python3 tools/build.py
Output: index.html, about/, contact/, services/... , sitemap.xml, robots.txt

NOTE: edit content HERE, not in the generated .html files — a rebuild overwrites them.
"""

import os
import re
import html
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- business data
SITE = "https://prestigepropertycare.com.au"

# Only the weights the stylesheet actually uses: Fraunces 600/700/900, Karla 400-700.
FONT_HREF = ("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700;9..144,900"
             "&family=Karla:wght@400;500;600;700&display=swap")
BIZ = {
    "name": "Prestige Property Care",
    # The street address is deliberately NOT shown anywhere on the pages. It
    # lives only in the LocalBusiness JSON-LD below, which is the legitimate
    # machine-readable channel — hiding text in the markup to feed crawlers
    # would be cloaking. tools/check.py fails the build if it leaks into any
    # visible copy.
    "street": "2/15 St Johns Ave",
    "public_address": "Frankston VIC 3199",
    "locality": "Frankston",
    "region": "VIC",
    "postcode": "3199",
    "country": "AU",
    "phone_display": "0466 687 252",
    "phone_link": "+61466687252",
    "phone_intl": "+61 466 687 252",
    # The amendment sheet wrote this as "Dave@prestgiepropertycare.com.au".
    # prestgiepropertycare.com.au does not resolve and prestigepropertycare.com.au
    # does, so the transposed spelling is treated as a typo. If the mailbox really
    # is on the misspelt domain, change this one line and rebuild.
    "email": "dave@prestigepropertycare.com.au",
    "owner": "Dave Coelho",
    "lat": -38.1442,
    "lng": 145.1281,
    "facebook": "https://www.facebook.com/profile.php?id=61594050001979",
    "instagram": "https://www.instagram.com/prestigepropertycarefrankston/",
}

# The logo mark. Three alternatives live in assets/img/logo/ (mark-crest.svg,
# mark-pleaf.svg, mark-level.svg) — switching the brand over is this one line
# plus a re-run of tools/gen-icons.py to redraw the favicon and app icons.
LOGO_MARK = "/assets/img/logo/mark-crest.svg"

SUBURBS = [
    "Frankston", "Frankston South", "Frankston North", "Seaford", "Langwarrin",
    "Langwarrin South", "Karingal", "Carrum Downs", "Skye", "Baxter",
    "Mount Eliza", "Pearcedale", "Mornington", "Mount Martha", "Moorooduc",
    "Somerville", "Tyabb", "Mornington Peninsula",
]

GMB_EMBED = (
    "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d200705.6214454393!2d145.1110961"
    "!3d-38.1860856!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x471521d92f4fcf41"
    "%3A0xae0f0cd5a3ad64b2!2sGreenline%20services!5e0!3m2!1sen!2sph!4v1787142280589!5m2!1sen!2sph"
)

# ------------------------------------------------------------ GoHighLevel CRM
# Loaded on every page. GHL's external tracking script reads the native form
# submit event and syncs the submission to a contact, so the form must render
# in the page DOM, every field needs a name attribute, and nothing may call
# preventDefault() on a valid submit. See README.
GHL_TRACKING = (
    '<script defer\n'
    '  src="https://link.msgsndr.com/js/external-tracking.js"\n'
    '  data-tracking-id="tk_9f5144f196b340e59b8396dd9921dc07">\n'
    '</script>\n'
)

# The quote form submits natively so GHL can capture it, then lands the visitor
# on the thank-you page.
#
# Default: a GET straight to /thank-you/. Works on any static host with no
# backend, and GHL still captures the submission.
#
# To also deliver the lead by email, point FORM_ACTION at a form endpoint and
# let it redirect to /thank-you/ — the hidden field below carries the redirect:
#   Formspree:   FORM_ACTION = "https://formspree.io/f/XXXXXXXX"
#                FORM_METHOD = "post"
#                FORM_REDIRECT_FIELD = "_next"
#   Web3Forms:   FORM_ACTION = "https://api.web3forms.com/submit"
#                FORM_METHOD = "post"
#                FORM_REDIRECT_FIELD = "redirect"
#                (plus a hidden access_key input)
FORM_ACTION = "/thank-you/"
FORM_METHOD = "get"
FORM_REDIRECT_FIELD = None      # hidden redirect field name, if the endpoint needs one
FORM_HIDDEN = {}                # any extra hidden inputs the endpoint needs

# ---------------------------------------------------------------------- images
# Real job photography supplied by the client (Google Drive), resized and
# compressed for the web. Nothing here is stock or generated.
IMG_FILES = {
    "hero":               "hero.jpg",
    "lawn-mowing":        "lawn-mowing.jpg",
    "gutter-cleaning":    "gutter-cleaning.jpg",
    "garden-maintenance": "garden-maintenance.jpg",
    "hedge-trimming":     "hedge-trimming.jpg",
    "rubbish-removal":    "rubbish-removal.jpg",
    "garden-clean-ups":   "garden-clean-ups.jpg",
    "about-dave":         "about-dave.jpg",
    "work-lawn":          "work-lawn.jpg",
    "work-hedge":         "work-hedge.jpg",
    "work-garden":        "work-garden.jpg",
    "og":                 "og.jpg",
    "ba1-before":         "ba1-before.jpg",
    "ba1-after":          "ba1-after.jpg",
    "ba2-before":         "ba2-before.jpg",
    "ba2-after":          "ba2-after.jpg",
    "ba3-before":         "ba3-before.jpg",
    "ba3-after":          "ba3-after.jpg",
}

# Alt text describes what is actually in each frame — keyword-relevant, but
# never claiming more than the photo shows.
IMG_ALT = {
    "hero": "Freshly mown back lawn with stepping stones and clipped garden beds at a Frankston home maintained by Prestige Property Care",
    "lawn-mowing": "Freshly mown back lawn edged along the concrete path, with planted garden beds behind, on a Mornington Peninsula property",
    "gutter-cleaning": "Roof gutter in Frankston packed with gum leaves and bark before a Prestige Property Care gutter clean",
    "garden-maintenance": "Garden bed remulched and re-edged beside a mown lawn during a regular garden maintenance visit in Frankston",
    "hedge-trimming": "Large hedge cut square and level on every face after hedge trimming in Frankston",
    "rubbish-removal": "Backyard cleared back to bare ground in Frankston, with all green waste and rubbish taken away",
    "garden-clean-ups": "Overgrown Frankston backyard with knee-high grass and debris, before an end-of-lease garden clean up",
    "about-dave": "Tidy front garden in Frankston with clipped shrubs, a swept aggregate path and a mown lawn",
    "work-lawn": "Sloping back lawn mown and edged with the garden beds cut clean around it",
    "work-hedge": "Shaped topiary hedging along a pool surround, cut square and level",
    "work-garden": "Maintained back garden with a mown lawn, edged beds and the paths blown clean",
    "og": "Prestige Property Care — lawn mowing, hedge trimming and garden maintenance in Frankston and the Mornington Peninsula",
    "ba1-before": "Overgrown Frankston backyard before a clean-up, with knee-high grass and dumped sheeting against the fence",
    "ba1-after": "The same Frankston backyard after the clean-up, mown flat with the paving cleared and the waste gone",
    "ba2-before": "Patchy, overgrown back lawn around a timber deck before a Prestige Property Care visit",
    "ba2-after": "The same back lawn mown even and edged along the garden beds after the visit",
    "ba3-before": "Garden bed overgrown and spilling across brick paving before a garden maintenance visit in Frankston",
    "ba3-after": "The same garden bed cut back to its rock edging with the brick paving swept clean",
}


# Responsive variants + real intrinsic dimensions, written by tools/gen-images.py.
# Read here with the stdlib so this build script keeps zero dependencies.
_MANIFEST_PATH = os.path.join(ROOT, "assets", "img", "manifest.json")
try:
    with open(_MANIFEST_PATH, encoding="utf-8") as _fh:
        IMG_META = json.load(_fh)
except FileNotFoundError:       # not generated yet — fall back to plain <img>
    IMG_META = {}


def img(key):
    return "/assets/img/" + IMG_FILES[key]


def _meta(key):
    return IMG_META.get(os.path.splitext(IMG_FILES[key])[0], {})


def srcset_for(key):
    rows = _meta(key).get("srcset") or []
    return ", ".join("/assets/img/%s %dw" % (f, w) for w, f in rows)


SPLIT_SIZES = "(max-width:900px) 100vw, 50vw"
CARD_SIZES = "(max-width:600px) 100vw, (max-width:1040px) 50vw, 360px"
BA_SIZES = "(max-width:1244px) 100vw, 1116px"


def picture(key, cls="", sizes=None, eager=False, extra=""):
    """An <img> with its real intrinsic size and a responsive srcset.

    The width/height attributes must match the file, or the browser reserves
    the wrong box and the page shifts as images land.
    """
    m = _meta(key)
    w, h = m.get("w", 1200), m.get("h", 900)
    loading = ('loading="eager" fetchpriority="high"' if eager
               else 'loading="lazy"')
    ss = srcset_for(key)
    ss_attr = ' srcset="%s"' % ss if ss else ""
    # A srcset without sizes makes the browser assume 100vw and over-download.
    sz_attr = ' sizes="%s"' % (sizes or "100vw") if ss else ""
    c = ' class="%s"' % cls if cls else ""
    return ('<img src="%s"%s%s alt="%s"%s width="%d" height="%d" %s decoding="async"%s>'
            % (img(key), ss_attr, sz_attr, html.escape(IMG_ALT[key]), c, w, h,
               loading, extra))


# ------------------------------------------------------------------- services
# Order matters: it drives the nav dropdown, the footer and the sitemap.
SERVICES = [
    {
        "slug": "lawn-mowing",
        "nav": "Lawn Mowing",
        "nav_sub": "Mornington, Mount Eliza &amp; the Peninsula",
        "card_title": "Lawn Mowing in Mornington &amp; the Peninsula",
        "card_text": "Regular or one-off mowing, catching and edging included. Weekly and fortnightly rounds through Mornington, Mount Eliza and Mount Martha.",
        "img": "lawn-mowing",
        "icon": '<path d="M2 17h11v-4H2z"/><circle cx="5" cy="19.5" r="2"/><circle cx="19" cy="19.5" r="2.5"/><path d="M13 15h4l3-9h2"/>',
    },
    {
        "slug": "gutter-cleaning",
        "nav": "Gutter Cleaning",
        "nav_sub": "Frankston, Seaford &amp; Carrum Downs",
        "card_title": "Gutter Cleaning in Frankston",
        "card_text": "Gutters and downpipes cleared by hand, debris bagged and taken with us. Worth booking before storm season and after the autumn leaf drop.",
        "img": "gutter-cleaning",
        "icon": '<path d="M3 7h18"/><path d="M3 7v5a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7"/><path d="M12 14v3"/><path d="M12 22a2 2 0 0 1-2-2c0-1.2 2-3 2-3s2 1.8 2 3a2 2 0 0 1-2 2Z"/>',
    },
    {
        "slug": "garden-maintenance",
        "nav": "Garden Maintenance",
        "nav_sub": "Frankston &amp; Frankston South",
        "card_title": "Your Local Gardener in Frankston",
        "card_text": "Weeding, mulching, pruning and general garden maintenance on a schedule that suits you. Ideal if you are time-poor or managing a property from elsewhere.",
        "img": "garden-maintenance",
        "icon": '<path d="M11 20A7 7 0 0 1 4 13c0-5 4-9 9-10 1 6-1 12-2 17Z"/><path d="M11 20c1-4 4-7 8-8"/>',
    },
    {
        "slug": "hedge-trimming",
        "nav": "Hedge Trimming &amp; Edging",
        "nav_sub": "Langwarrin, Karingal &amp; Baxter",
        "card_title": "Hedge Trimming &amp; Lawn Edging",
        "card_text": "Hedges shaped and levelled, edges cut sharp along paths, drives and garden beds. The two jobs that make a tidy yard look properly finished.",
        "img": "hedge-trimming",
        "icon": '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M7.7 16.3 18 4"/><path d="M16.3 16.3 6 4"/>',
    },
    {
        "slug": "rubbish-removal",
        "nav": "Green Waste &amp; Rubbish Removal",
        "nav_sub": "Frankston, Skye &amp; Carrum Downs",
        "card_title": "Green Waste &amp; Rubbish Removal",
        "card_text": "Clippings, prunings, old timber and general household rubbish loaded and taken away. No waiting months for a council hard waste booking.",
        "img": "rubbish-removal",
        "icon": '<path d="M4 7h16"/><path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/><path d="M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13"/><path d="M10 11v6M14 11v6"/>',
    },
    {
        "slug": "garden-clean-ups",
        "nav": "Garden Clean-Ups",
        "nav_sub": "End-of-lease &amp; pre-sale, Mount Eliza",
        "card_title": "End-of-Lease &amp; Pre-Sale Clean-Ups",
        "card_text": "Overgrown yards brought back to inspection standard. Popular with renters chasing a bond back, and with agents preparing a home for photos.",
        "img": "garden-clean-ups",
        "icon": '<path d="M12 3l1.8 4.7L18.5 9.5 13.8 11.3 12 16l-1.8-4.7L5.5 9.5l4.7-1.8Z"/><path d="M18 16.5l.9 2.3 2.3.9-2.3.9-.9 2.3-.9-2.3-2.3-.9 2.3-.9Z"/>',
    },
]
SVC_BY_SLUG = {s["slug"]: s for s in SERVICES}

# ------------------------------------------------------------------- SVG icons
IC = {
    "leaf": '<path d="M12 21c0-6 3-10 8-11-1 6-4 9-8 11Z"/><path d="M12 21c0-6-3-10-8-11 1 6 4 9 8 11Z"/><path d="M12 21v-6"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 6 10-6"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "arrows": '<path d="M9 7 4 12l5 5M15 7l5 5-5 5"/>',
    "facebook": '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3Z"/>',
    "instagram": ('<rect x="2" y="2" width="20" height="20" rx="5"/>'
                  '<path d="M16 11.4A4 4 0 1 1 12.6 8 4 4 0 0 1 16 11.4Z"/>'
                  '<path d="M17.5 6.5h.01"/>'),
    "chev-left": '<path d="M15 5 8 12l7 7"/>',
    "chev-right": '<path d="m9 5 7 7-7 7"/>',
}
STAR = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.3-6.2 3.3L7 14.2l-5-4.9 6.9-1Z"/></svg>'
STARS = ('<div class="stars" role="img" aria-label="Rated 5 out of 5">%s</div>'
         % (STAR * 5))


def svg(name, cls="", size=None):
    attrs = ' class="%s"' % cls if cls else ""
    dim = ' width="%d" height="%d"' % (size, size) if size else ""
    return '<svg viewBox="0 0 24 24"%s%s aria-hidden="true">%s</svg>' % (attrs, dim, IC[name])




# ------------------------------------------------------------------ page chrome
def head(page):
    """<head> for one page."""
    url = SITE + page["path"]
    og_img = SITE + img("og")
    depth_css = "/assets/css/site.min.css"
    extra = page.get("head_extra", "")
    robots = page.get("robots", "index, follow, max-image-preview:large, max-snippet:-1")
    lcp = page.get("lcp")
    lcp_preload = ""
    if lcp:
        ss = srcset_for(lcp)
        lcp_preload = ('<link rel="preload" as="image" href="%s"%s imagesizes="100vw" fetchpriority="high">\n'
                       % (img(lcp), ' imagesrcset="%s"' % ss if ss else ""))
    return f"""<!DOCTYPE html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page['title']}</title>
<meta name="description" content="{page['desc']}">
<link rel="canonical" href="{url}">
<meta name="robots" content="{robots}">
<meta name="theme-color" content="#0C2A12">
<meta name="geo.region" content="AU-VIC">
<meta name="geo.placename" content="Frankston, Victoria">
<meta name="geo.position" content="{BIZ['lat']};{BIZ['lng']}">
<meta name="ICBM" content="{BIZ['lat']}, {BIZ['lng']}">

<meta property="og:type" content="website">
<meta property="og:locale" content="en_AU">
<meta property="og:site_name" content="Prestige Property Care">
<meta property="og:title" content="{page['title']}">
<meta property="og:description" content="{page['desc']}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{page['title']}">
<meta name="twitter:description" content="{page['desc']}">
<meta name="twitter:image" content="{og_img}">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="{FONT_HREF}">
<link rel="stylesheet" href="{FONT_HREF}" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="{FONT_HREF}"></noscript>
<link rel="icon" href="{LOGO_MARK}" type="image/svg+xml">
<link rel="icon" href="/assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="/assets/img/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="stylesheet" href="{depth_css}">
{lcp_preload}

{GHL_TRACKING}{extra}</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
"""


def site_header(active, solid=False, modal_cta=True):
    # On the contact page the form is right there in the hero, so the header
    # button scrolls to it instead of opening the popup.
    cta_attr = ' data-quote-open' if modal_cta else ''
    cta_href = '/contact/' if modal_cta else '#quote'

    dd_items = ['''<a class="dd-item" role="menuitem" href="/services/">
            <span class="dd-icon" aria-hidden="true">%s</span>
            <span class="dd-text"><strong>All Services</strong><em>Complete property upkeep</em></span>
          </a>''' % svg("grid")]
    for s in SERVICES:
        dd_items.append('''<a class="dd-item" role="menuitem" href="/services/%s/">
            <span class="dd-icon" aria-hidden="true"><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></span>
            <span class="dd-text"><strong>%s</strong><em>%s</em></span>
          </a>''' % (s["slug"], s["icon"], s["nav"], s["nav_sub"]))

    def cls(name):
        return ' is-active' if active == name else ''

    return f"""<header class="site-header{' solid' if solid else ''}" id="top">
  <div class="nav-inner">
    <a href="/" class="brand" aria-label="Prestige Property Care home">
      <span class="brand-mark"><img src="{LOGO_MARK}" alt="Prestige Property Care logo" width="120" height="120" decoding="async"></span>
      <span class="brand-name">Prestige Property Care</span>
    </a>

    <nav class="nav-main" aria-label="Main navigation">
      <a href="/" class="nav-link{cls('home')}">Home</a>

      <div class="nav-dropdown">
        <button class="nav-link nav-trigger{cls('services')}" aria-expanded="false" aria-controls="services-menu">
          Services
          <svg class="caret" viewBox="0 0 12 8" aria-hidden="true"><path d="M1 1.5 6 6.5l5-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        </button>
        <div class="dropdown-panel" id="services-menu" role="menu">
          {"".join(dd_items)}
        </div>
      </div>

      <a href="/about/" class="nav-link{cls('about')}">About</a>
      <a href="/#areas" class="nav-link">Areas</a>
      <a href="/contact/" class="nav-link{cls('contact')}">Contact</a>
    </nav>

    <div class="nav-actions">
      <a href="tel:{BIZ['phone_link']}" class="nav-phone">{BIZ['phone_display']}</a>
      <a href="{cta_href}" class="btn-cta"{cta_attr}>Get a Free Quote</a>
    </div>

    <button class="nav-burger" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-nav">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>

<div class="scrim" hidden></div>

<nav class="mobile-nav" id="mobile-nav" aria-label="Mobile navigation">
  <a href="/">Home</a>
  <button class="acc-btn" aria-expanded="false">Services <span aria-hidden="true">+</span></button>
  <div class="acc-body">
    <a href="/services/">All Services</a>
    {"".join('<a href="/services/%s/">%s</a>' % (s["slug"], s["nav"]) for s in SERVICES)}
  </div>
  <a href="/about/">About</a>
  <a href="/#areas">Areas</a>
  <a href="/contact/">Contact</a>
  <a href="{cta_href}"{cta_attr} class="mobile-quote">Get a free quote</a>
  <a href="tel:{BIZ['phone_link']}">Call {BIZ['phone_display']}</a>
</nav>
"""


def crumbs(trail):
    """trail = [(name, href|None)] — last item is the current page."""
    items = []
    for i, (name, href) in enumerate(trail):
        if href:
            items.append('<li><a href="%s">%s</a></li>' % (href, name))
        else:
            items.append('<li><span aria-current="page">%s</span></li>' % name)
    return ('<nav class="crumbs" aria-label="Breadcrumb"><ol>%s</ol></nav>'
            % "".join(items))


def cta_band(heading, text):
    return f"""<section class="cta-band">
  <div class="wrap">
    <div>
      <h2>{heading}</h2>
      <p>{text}</p>
    </div>
    <div class="hero-cta">
      <a href="tel:{BIZ['phone_link']}" class="btn-lg btn-solid">{svg('phone')} Call {BIZ['phone_display']}</a>
      <button type="button" class="btn-lg btn-ghost" data-quote-open>Request a quote</button>
    </div>
  </div>
</section>
"""


def quote_modal():
    """Quote popup, rendered once per page.

    A real <form> in the page DOM with the same six GHL field names as the
    inline form — hidden with CSS, never `disabled`, so GHL still captures it.
    Ids are prefixed `qm-` so they cannot collide with an inline form.
    """
    return f"""<div class="modal" id="quote-modal" hidden>
  <div class="modal-scrim" data-quote-close></div>
  <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="quote-modal-title">
    <button class="modal-close" type="button" aria-label="Close" data-quote-close>
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>
    </button>
    <div class="modal-head">
      <span class="eyebrow">Free quote</span>
      <h2 id="quote-modal-title">Tell us about the property</h2>
      <p>Fixed price, no call-out fee, no obligation. Or call <a href="tel:{BIZ['phone_link']}">{BIZ['phone_display']}</a> for a same-day answer.</p>
    </div>
    {quote_form(idp="qm", card=False)}
  </div>
</div>
"""


def site_footer(with_modal=True):
    modal = quote_modal() if with_modal else ""
    svc_links = "".join('<li><a href="/services/%s/">%s</a></li>' % (s["slug"], s["nav"]) for s in SERVICES)
    area_links = "".join('<li><a href="/#areas">%s</a></li>' % s for s in
                         ["Frankston", "Frankston South", "Seaford", "Langwarrin",
                          "Carrum Downs", "Mount Eliza", "Mornington", "Mount Martha"])
    return f"""<footer>
  <div class="wrap">
    <div class="f-grid">
      <div class="f-about">
        <a href="/" class="brand">
          <span class="brand-mark"><img src="{LOGO_MARK}" alt="Prestige Property Care logo" width="120" height="120" loading="lazy" decoding="async"></span>
          <span class="brand-name">Prestige Property Care</span>
        </a>
        <p>Lawn, garden and property maintenance for Frankston and the Mornington Peninsula. Locally owned and run by {BIZ['owner']}.</p>
        <ul class="f-social">
          <li><a href="{BIZ['facebook']}" aria-label="Prestige Property Care on Facebook" rel="noopener">{svg('facebook')}</a></li>
          <li><a href="{BIZ['instagram']}" aria-label="Prestige Property Care on Instagram" rel="noopener">{svg('instagram')}</a></li>
        </ul>
      </div>
      <div>
        <h2 class="f-head">Services</h2>
        <ul>{svc_links}</ul>
      </div>
      <div>
        <h2 class="f-head">Areas served</h2>
        <ul>{area_links}</ul>
      </div>
      <div>
        <h2 class="f-head">Contact</h2>
        <ul>
          <li><a href="tel:{BIZ['phone_link']}">{BIZ['phone_display']}</a></li>
          <li><a href="mailto:{BIZ['email']}">{BIZ['email']}</a></li>
          <li>{BIZ['public_address']}</li>
          <li><a href="/contact/">Request a free quote</a></li>
          <li><a href="/about/">About Prestige</a></li>
        </ul>
      </div>
    </div>
    <div class="f-bottom">
      <span>&copy; 2026 Prestige Property Care. Frankston, Victoria. ABN details on request.</span>
      <span>Lawn mowing in Frankston, gardening and property maintenance across the Mornington Peninsula.</span>
    </div>
  </div>
</footer>

{modal}<script src="/assets/js/site.js" defer></script>
</body>
</html>
"""


# ------------------------------------------------------------------- fragments
def map_embed(title, short=False):
    return f"""<div class="map-embed{' short' if short else ''}">
  <iframe title="{title}" src="{GMB_EMBED}" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="strict-origin-when-cross-origin"></iframe>
</div>"""


def nap_list():
    return f"""<ul class="nap">
  <li>
    <span class="ico" aria-hidden="true">{svg('phone')}</span>
    <span><b>Phone</b><a href="tel:{BIZ['phone_link']}">{BIZ['phone_display']}</a></span>
  </li>
  <li>
    <span class="ico" aria-hidden="true">{svg('mail')}</span>
    <span><b>Email</b><a href="mailto:{BIZ['email']}">{BIZ['email']}</a></span>
  </li>
  <li>
    <span class="ico" aria-hidden="true">{svg('pin')}</span>
    <span><b>Based in</b>{BIZ['public_address']}<br>Mobile service &mdash; we come to you</span>
  </li>
  <li>
    <span class="ico" aria-hidden="true">{svg('clock')}</span>
    <span><b>Hours</b>Monday to Friday 7:00am&ndash;5:00pm, Saturday 8:00am&ndash;2:00pm</span>
  </li>
  <li>
    <span class="ico" aria-hidden="true">{svg('leaf')}</span>
    <span><b>Service area</b>Frankston, the Frankston City suburbs and the Mornington Peninsula</span>
  </li>
</ul>"""


def quote_form(preselect=None, heading=None, idp="qf", card=True):
    """The quote form.

    Field names map 1:1 onto the GHL contact fields:
        full_name        -> {{contact.full_name}}
        email            -> {{contact.email}}
        phone            -> {{contact.phone}}
        property_address -> {{contact.property_address}}
        service_needed   -> {{contact.service_needed}}
        property_size    -> {{contact.property_size}}
        job_notes        -> {{contact.job_notes}}

    Submits natively (no preventDefault anywhere) so the GHL tracking script
    can read the submission. Do not add a JS handler that blocks submit.
    """
    sizes = ["Small &mdash; under 300m&sup2;",
             "Medium &mdash; 300&ndash;600m&sup2;",
             "Large &mdash; 600&ndash;1000m&sup2;",
             "Acreage &mdash; over 1000m&sup2;",
             "Not sure"]
    size_opts = '<option value="">Select a size</option>' + "".join(
        "<option>%s</option>" % x for x in sizes)

    opts = []
    labels = ["Lawn mowing", "Gutter cleaning", "Garden maintenance",
              "Hedge trimming &amp; edging", "Green waste &amp; rubbish removal",
              "End-of-lease or pre-sale clean-up", "Commercial property maintenance",
              "Something else"]
    for lb in labels:
        sel = " selected" if preselect and preselect.lower() in lb.lower() else ""
        opts.append("<option%s>%s</option>" % (sel, lb))

    hidden = ""
    if FORM_REDIRECT_FIELD:
        hidden += '<input type="hidden" name="%s" value="%s/thank-you/">\n    ' % (
            FORM_REDIRECT_FIELD, SITE)
    for k, v in FORM_HIDDEN.items():
        hidden += '<input type="hidden" name="%s" value="%s">\n    ' % (k, v)

    # h2, not h3: on the contact page this is the first heading after the h1,
    # and jumping h1 -> h3 fails the heading-order audit.
    head_html = '<h2 class="form-head">%s</h2>' % heading if heading else ""
    open_card = '<div class="contact-card">' if card else ""
    close_card = "</div>" if card else ""
    return f"""{open_card}
  {head_html}<form class="quote-form" action="{FORM_ACTION}" method="{FORM_METHOD}">
    {hidden}<div class="form-grid">
      <div class="field">
        <label for="{idp}-full_name">Name</label>
        <input type="text" id="{idp}-full_name" name="full_name" required autocomplete="name" placeholder="Your name">
      </div>
      <div class="field">
        <label for="{idp}-email">Email</label>
        <input type="email" id="{idp}-email" name="email" required autocomplete="email" placeholder="Enter your email">
      </div>
      <div class="field">
        <label for="{idp}-phone">Phone</label>
        <input type="tel" id="{idp}-phone" name="phone" required autocomplete="tel" placeholder="Enter your phone">
      </div>
      <div class="field">
        <label for="{idp}-service_needed">Service needed</label>
        <select id="{idp}-service_needed" name="service_needed">{"".join(opts)}</select>
      </div>
      <div class="field full">
        <label for="{idp}-property_address">Property address</label>
        <input type="text" id="{idp}-property_address" name="property_address" required autocomplete="street-address" placeholder="e.g. 12 Smith St, Frankston VIC">
      </div>
      <div class="field full">
        <label for="{idp}-property_size">Property size</label>
        <select id="{idp}-property_size" name="property_size">{size_opts}</select>
      </div>
      <div class="field full">
        <label for="{idp}-job_notes">Job notes</label>
        <textarea id="{idp}-job_notes" name="job_notes" placeholder="How long since it was last done, access notes, anything else we should know&hellip;"></textarea>
      </div>
      <div class="field full" style="margin-bottom:0">
        <button type="submit" class="btn-submit">Send my quote request</button>
        <p class="form-note">Or call <a href="tel:{BIZ['phone_link']}">{BIZ['phone_display']}</a> for a same-day answer.</p>
      </div>
    </div>
  </form>
{close_card}"""


def areas_grid():
    return '<div class="areas-grid">%s</div>' % "".join(
        '<span class="area">%s%s</span>' % (svg("pin"), s) for s in SUBURBS)


def service_cards(exclude=None, limit=None):
    items = [s for s in SERVICES if s["slug"] != exclude]
    if limit:
        items = items[:limit]
    out = []
    for s in items:
        out.append(f"""<a class="svc" href="/services/{s['slug']}/">
        <span class="svc-photo">{picture(s['img'], sizes='(max-width:600px) 100vw, (max-width:1040px) 50vw, 360px')}</span>
        <span class="svc-body">
          <span class="svc-icon" aria-hidden="true"><svg viewBox="0 0 24 24">{s['icon']}</svg></span>
          <h3>{s['card_title']}</h3>
          <p>{s['card_text']}</p>
          <span class="svc-link">See {s['nav'].replace('&amp;', 'and').lower()} {svg('arrow')}</span>
        </span>
      </a>""")
    return '<div class="svc-grid">%s</div>' % "".join(out)


# Captions describe the job in the frame. No suburb is named unless it is known,
# so nothing here invents a location for a real client's property.
WORK = [
    ("work-lawn", "Mown, caught and edged",
     "A regular round: the lawn cut and caught, then every edge along the paths and beds cut clean."),
    ("work-hedge", "Hedges shaped square",
     "Pool-surround hedging cut level on every face, with the clippings taken away the same day."),
    ("work-garden", "The whole property kept tidy",
     "Lawn mown, beds edged and mulched, and the paths blown down before we left."),
]


BEFORE_AFTER = [
    ("ba1", "End-of-lease clean-up",
     "Knee-high grass and dumped sheeting cleared, the whole yard mown flat and every bit of waste taken away the same day."),
    ("ba2", "Back lawn brought back",
     "Overgrown, patchy grass around the decking cut back to an even lawn and edged along the garden beds."),
    ("ba3", "Garden bed cut back",
     "A bed spilling out across the brick paving, cut back to its rock edging with the paving swept clean."),
]


def before_after_slider():
    """Before/after comparison slider for the recent work section.

    Each slide is a wipe comparison driven by a real <input type="range">, so
    it is keyboard operable and works with assistive tech for free. The track
    uses native CSS scroll-snap, so swiping and scrolling still work with no
    JavaScript at all — the buttons and dots are progressive enhancement.
    """
    slides = []
    for i, (key, title, text) in enumerate(BEFORE_AFTER):
        slides.append(f"""<div class="ba-slide" role="group" aria-roledescription="slide" aria-label="{i+1} of {len(BEFORE_AFTER)}: {title}">
        <div class="ba" style="--pos:50%">
          <div class="ba-frame">
            {picture(key + '-after', cls='ba-img', sizes=BA_SIZES)}
            <div class="ba-clip">{picture(key + '-before', cls='ba-img', sizes=BA_SIZES)}</div>
            <span class="ba-tag ba-tag-before" aria-hidden="true">Before</span>
            <span class="ba-tag ba-tag-after" aria-hidden="true">After</span>
            <span class="ba-divider" aria-hidden="true"><span class="ba-knob">{svg('arrows')}</span></span>
            <input class="ba-range" type="range" min="0" max="100" value="50" step="1"
                   aria-label="{title}: drag to compare the before and after photos">
          </div>
          <div class="ba-caption"><b>{title}</b>{text}</div>
        </div>
      </div>""")

    dots = "".join(
        '<button type="button" class="ba-dot%s" data-ba-go="%d" aria-label="Show job %d of %d"%s></button>'
        % (" is-on" if i == 0 else "", i, i + 1, len(BEFORE_AFTER),
           ' aria-current="true"' if i == 0 else "")
        for i in range(len(BEFORE_AFTER)))

    return f"""<div class="ba-slider" data-ba-slider>
      <div class="ba-track" data-ba-track tabindex="0" aria-label="Before and after jobs, scrollable">
        {"".join(slides)}
      </div>
      <div class="ba-nav">
        <button type="button" class="ba-arrow" data-ba-prev aria-label="Previous job">{svg('chev-left')}</button>
        <div class="ba-dots" role="group" aria-label="Choose a job">{dots}</div>
        <button type="button" class="ba-arrow" data-ba-next aria-label="Next job">{svg('chev-right')}</button>
      </div>
    </div>"""


def work_gallery():
    out = []
    for key, title, text in WORK:
        out.append('<figure class="work">%s<figcaption><b>%s</b>%s</figcaption></figure>'
                   % (picture(key, sizes=CARD_SIZES), title, text))
    return '<div class="work-grid">%s</div>' % "".join(out)


# Real reviews from the Prestige Property Care Google Business Profile, quoted
# verbatim. Do not edit the wording, and do not add invented ones — fabricated
# testimonials are a breach of Australian Consumer Law.
TESTIMONIALS = [
    ("Dave did a fantastic job on our overgrown front yard. He got it looking great in just a few hours and saved me a full day&rsquo;s work. Friendly, professional, and easy to deal with. Highly recommend. Thanks mate!",
     "Stefan Nel"),
    ("Dave is brilliant. Fun, friendly and an incredible worker. Always punctual and gives that little bit extra. Had gutters cleaned for the first time in years, thrilled with the result. And third time he has edged and mowed the lawns. Great bloke, great ethics, you won&rsquo;t be disappointed. 11/10",
     "Trudi Maulday"),
    ("Yesterday was the second time I have used Dave to do my garden, and I&rsquo;m happy to say that both times he has done a great job. Happy to recommend him, he was punctual, efficient and friendly. He left my garden looking fab, and cleaned up all the mess.",
     "Claudine Barry"),
    ("Dave took it on board to clear out my aunty&rsquo;s property at short notice. He was thorough, prompt and did an amazing job. Would highly recommend his services.",
     "Alicia"),
]

GOOGLE_REVIEWS_URL = "https://www.google.com/maps?cid=12542257598963737778"


def testimonials():
    out = []
    for text, name in TESTIMONIALS:
        out.append(f"""<figure class="quote">
        {STARS}
        <blockquote>&ldquo;{text}&rdquo;</blockquote>
        <figcaption><cite>{name}</cite><span>Google review</span></figcaption>
      </figure>""")
    return '<div class="quotes">%s</div>' % "".join(out)


def faq_block(faqs):
    out = []
    for q, a in faqs:
        out.append(f"""<div class="faq">
        <button class="faq-q" aria-expanded="false">{q}</button>
        <div class="faq-a"><p>{a}</p></div>
      </div>""")
    return '<div class="faq-list">%s</div>' % "".join(out)


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return (s.replace("&mdash;", "—").replace("&ndash;", "–").replace("&rsquo;", "’")
             .replace("&ldquo;", "“").replace("&rdquo;", "”").replace("&amp;", "&")
             .replace("&hellip;", "…").replace("&nbsp;", " ").strip())


# --------------------------------------------------------------------- schema
def jsonld(obj_str):
    return '<script type="application/ld+json">\n%s\n</script>\n' % obj_str


def local_business_schema():
    areas = ",\n    ".join('{"@type":"Place","name":"%s, VIC, Australia"}' % s for s in SUBURBS)
    offers = ",\n      ".join(
        '{"@type":"Offer","itemOffered":{"@type":"Service","name":"%s","url":"%s/services/%s/"}}'
        % (strip_tags(s["nav"]), SITE, s["slug"]) for s in SERVICES)
    return f"""{{
  "@context": "https://schema.org",
  "@type": ["LocalBusiness","HomeAndConstructionBusiness"],
  "@id": "{SITE}/#business",
  "name": "{BIZ['name']}",
  "description": "Lawn mowing, garden maintenance, hedge trimming, gutter cleaning and green waste removal in Frankston and across the Mornington Peninsula.",
  "url": "{SITE}/",
  "telephone": "{BIZ['phone_intl']}",
  "email": "{BIZ['email']}",
  "founder": {{"@type":"Person","name":"{BIZ['owner']}"}},
  "priceRange": "$$",
  "currenciesAccepted": "AUD",
  "paymentAccepted": "Cash, Bank transfer, Card",
  "image": "{SITE + img('og')}",
  "address": {{
    "@type": "PostalAddress",
    "streetAddress": "{BIZ['street']}",
    "addressLocality": "{BIZ['locality']}",
    "addressRegion": "{BIZ['region']}",
    "postalCode": "{BIZ['postcode']}",
    "addressCountry": "{BIZ['country']}"
  }},
  "geo": {{"@type":"GeoCoordinates","latitude":{BIZ['lat']},"longitude":{BIZ['lng']}}},
  "hasMap": "https://www.google.com/maps?cid=12542257598963737778",
  "sameAs": [
    "{BIZ['facebook']}",
    "{BIZ['instagram']}",
    "https://www.google.com/maps?cid=12542257598963737778"
  ],
  "openingHoursSpecification": [
    {{"@type":"OpeningHoursSpecification","dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday"],"opens":"07:00","closes":"17:00"}},
    {{"@type":"OpeningHoursSpecification","dayOfWeek":["Saturday"],"opens":"08:00","closes":"14:00"}}
  ],
  "areaServed": [
    {areas}
  ],
  "hasOfferCatalog": {{
    "@type": "OfferCatalog",
    "name": "Lawn, garden and property maintenance services",
    "itemListElement": [
      {offers}
    ]
  }}
}}"""


def website_schema():
    return f"""{{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": "{SITE}/#website",
  "url": "{SITE}/",
  "name": "{BIZ['name']}",
  "publisher": {{"@id": "{SITE}/#business"}},
  "inLanguage": "en-AU"
}}"""


def faq_schema(faqs):
    items = ",\n    ".join(
        '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
        % (json_str(strip_tags(q)), json_str(strip_tags(a))) for q, a in faqs)
    return """{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    %s
  ]
}""" % items


def breadcrumb_schema(trail):
    items = []
    for i, (name, href) in enumerate(trail, start=1):
        url = SITE + (href if href else "")
        items.append('{"@type":"ListItem","position":%d,"name":%s,"item":"%s"}'
                     % (i, json_str(strip_tags(name)), url))
    return """{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    %s
  ]
}""" % ",\n    ".join(items)


def service_schema(name, desc, path, service_type):
    areas = ",\n    ".join('{"@type":"Place","name":"%s, VIC, Australia"}' % s for s in SUBURBS)
    return f"""{{
  "@context": "https://schema.org",
  "@type": "Service",
  "@id": "{SITE}{path}#service",
  "name": {json_str(name)},
  "serviceType": {json_str(service_type)},
  "description": {json_str(desc)},
  "url": "{SITE}{path}",
  "provider": {{"@id": "{SITE}/#business"}},
  "areaServed": [
    {areas}
  ],
  "offers": {{
    "@type": "Offer",
    "priceCurrency": "AUD",
    "availability": "https://schema.org/InStock",
    "url": "{SITE}/contact/"
  }}
}}"""


def json_str(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


# =============================================================== HOME PAGE
HOME_FAQS = [
    ("How much does lawn mowing cost in Frankston?",
     "There is no single price for lawn mowing in Frankston, because it depends on the size of the lawn, how much growth has built up and whether you want edging and catching included. A small suburban block is quick. An overgrown yard that has been left for a few months takes longer and costs more. We quote every property before we start, so you get a fixed price rather than an hourly rate that keeps climbing while you watch from the window. Regular fortnightly rounds work out cheaper per visit than one-off jobs, because the grass never gets away from us."),
    ("How often should gutters be cleaned in Frankston and on the Mornington Peninsula?",
     "Twice a year suits most homes here &mdash; once after the autumn leaf drop and again before storm season. If your roof sits under gum trees, or you are close to the coast at Seaford, Mount Martha or Mornington, once every three or four months is safer. Blocked gutters overflow into eaves and wall cavities, and that repair costs far more than the clean would have."),
    ("Do you service Mount Eliza, Mornington and Mount Martha?",
     "Yes. Our regular round covers Mount Eliza, Mornington, Mount Martha, Moorooduc, Somerville and Tyabb, along with everything closer to home in Frankston, Frankston South, Frankston North, Seaford, Langwarrin, Karingal, Carrum Downs, Skye, Baxter and Pearcedale. Peninsula properties are often on a fortnightly or monthly schedule, including holiday homes we maintain while the owners are away."),
    ("Can you do an end-of-lease garden clean-up in Frankston?",
     "Yes, and it is one of the jobs we are booked for most. We bring an overgrown yard back to inspection standard: lawns cut and edged, beds weeded, hedges shaped, and every bit of green waste taken away the same day. If you have an inspection date, tell us when you call and we will work backwards from it."),
    ("Do you take away green waste after mowing?",
     "Always. Clippings, prunings and hedge trimmings go straight on the trailer and leave with us. You are not left with a pile beside the bin, or waiting on a council hard waste booking. We also take general rubbish removal jobs on their own if you have a shed, garage or yard to clear out."),
    ("Do you offer commercial property maintenance around Frankston?",
     "Yes. We maintain grounds for commercial sites, rental portfolios and body corporate properties across Frankston and the surrounding suburbs, on scheduled visits with consistent presentation between them. Send us the site address and how often you need it attended and we will price it."),
]

HOME_TRAIL = [("Home", "/")]


def page_home():
    return f"""{crumbs([]) if False else ''}<section class="hero">
  <div class="hero-media" aria-hidden="true">{picture('hero', eager=True, sizes='100vw')}</div>
  <div class="hero-in">
    <span class="eyebrow">Frankston &amp; the Mornington Peninsula</span>
    <h1>Lawn Mowing &amp; Garden Maintenance in <em>Frankston</em></h1>
    <p class="hero-sub">Prestige Property Care is a local lawn and garden crew based in Frankston. We handle lawn mowing in Frankston, hedge trimming, gutter cleaning and full property tidy-ups &mdash; from Seaford and Carrum Downs down to Mornington and Mount Martha.</p>
    <div class="hero-cta">
      <button type="button" class="btn-lg btn-solid" data-quote-open>Get a free quote</button>
    </div>
    <div class="hero-strip">
      <div>{svg('check')}Frankston based, locally owned</div>
      <div>{svg('check')}Free, no-obligation quotes</div>
      <div>{svg('check')}Residential &amp; commercial</div>
      <div>{svg('check')}Green waste taken away</div>
    </div>
  </div>
</section>

<div class="trustbar">
  <div class="wrap">
    <ul>
      <li>{svg('check')}Same crew every visit</li>
      <li>{svg('check')}Fixed quotes, not hourly rates</li>
      <li>{svg('check')}18 suburbs across Frankston &amp; the Peninsula</li>
      <li>{svg('check')}Fully insured</li>
      <li>{svg('check')}One booking for the whole property</li>
    </ul>
  </div>
</div>

<hr class="stripe-rule">

<main id="main">

<!-- ===== SERVICES ===== -->
<section class="sec" id="services">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">What we do</span>
      <h2>One crew for the whole property</h2>
      <p class="lede">Lawn mowing in Frankston is where most clients start, and it rarely stops at the lawn &mdash; the same visit usually picks up the gutters, the hedges and the pile of green waste out the back. Book it in one go instead of chasing three different trades.</p>
    </div>
    {service_cards()}
    <p style="margin-top:26px"><a href="/services/" class="svc-link">See all services {svg('arrow')}</a></p>
  </div>
</section>

<!-- ===== INTRO / GEO ANSWER BLOCK ===== -->
<section class="sec sec-alt">
  <div class="wrap">
    <div class="split">
      <div class="prose">
        <span class="eyebrow">Local lawn care</span>
        <h2>Straight answers, a fixed price, and the same person each time</h2>
        <p><strong>Prestige Property Care provides lawn mowing in Frankston, Victoria, along with garden maintenance, hedge trimming, gutter cleaning and green waste removal, from a base in Frankston VIC 3199.</strong> We cover 18 suburbs across the Frankston City area and the Mornington Peninsula, on both one-off visits and regular weekly, fortnightly or monthly rounds.</p>
        <p>Most people calling about lawn mowing in Frankston have one of two problems. Either the lawn has quietly got away from them over a wet fortnight, or they have been let down by someone who stopped turning up. Both are fixable. We quote the property before we start, we give you a day, and we keep to it.</p>
        <p>Every visit finishes the same way: lawn cut and caught, edges cut sharp along the paths and drives, paths blown clean, and the clippings on the trailer and gone. Nothing is left in a pile by the bin for you to sort out later.</p>
        <div class="callout">
          <p><strong>Not sure what you need?</strong> Call {BIZ['phone_display']} and describe the property. We will tell you what the job actually needs &mdash; and if it is not something we do, we will say so rather than quote you for it.</p>
        </div>
      </div>
      <div class="split-media">{picture('lawn-mowing', sizes=SPLIT_SIZES)}</div>
    </div>
  </div>
</section>

<!-- ===== WHY / ABOUT ===== -->
<section class="sec sec-dark" id="about">
  <div class="stripes" aria-hidden="true"></div>
  <div class="wrap" style="position:relative;z-index:2">
    <div class="sec-head">
      <span class="eyebrow">About Prestige</span>
      <h2>Local, and it shows in the work</h2>
      <p class="lede">Prestige Property Care is run by {BIZ['owner']} out of Frankston. You deal with the person doing the job, not a call centre and not a rotating roster of subcontractors.</p>
    </div>
    <div class="why-grid">
      <div class="why-item">
        <span class="why-num">01</span>
        <div><h3>You get the same person each visit</h3><p>The same crew turns up, so nobody needs reminding where the side gate key lives or which bed is not to be touched.</p></div>
      </div>
      <div class="why-item">
        <span class="why-num">02</span>
        <div><h3>Every service under one booking</h3><p>Lawns, hedges, gutters, waste removal and general property upkeep. One call, one invoice, one crew that knows the place.</p></div>
      </div>
      <div class="why-item">
        <span class="why-num">03</span>
        <div><h3>Green waste leaves with us</h3><p>Clippings and prunings go on the trailer the same day. Nothing gets left in a pile beside the bin for you to deal with later.</p></div>
      </div>
      <div class="why-item">
        <span class="why-num">04</span>
        <div><h3>Straight answers on price</h3><p>Quotes are free and given up front once we have seen the property. No hourly rate creeping upwards while you watch from the window.</p></div>
      </div>
    </div>
    <div class="hero-cta" style="margin-top:44px;margin-bottom:0">
      <a href="/about/" class="btn-lg btn-ghost">More about Prestige {svg('arrow')}</a>
    </div>
  </div>
</section>

<!-- ===== PROCESS ===== -->
<section class="sec sec-alt">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">How it works</span>
      <h2>Booked in four steps</h2>
    </div>
    <div class="steps">
      <div class="step"><div class="step-n">1</div><h3>Tell us what you need</h3><p>Call or send the form with your suburb and the jobs you want looked at.</p></div>
      <div class="step"><div class="step-n">2</div><h3>We quote it</h3><p>We assess the property and come back with a fixed price, free of charge.</p></div>
      <div class="step"><div class="step-n">3</div><h3>Pick your day</h3><p>One-off visit, or a weekly, fortnightly or monthly round that runs on schedule.</p></div>
      <div class="step"><div class="step-n">4</div><h3>We tidy and go</h3><p>Job done, edges cut, waste loaded, paths blown clean before we leave.</p></div>
    </div>
  </div>
</section>

<!-- ===== RECENT WORK ===== -->
<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Our recent work</span>
      <h2>Jobs from around Frankston and the Peninsula</h2>
      <p class="lede">Real properties, photographed on the day. Drag the handle across each one to see what the yard looked like when we arrived and what we left behind.</p>
    </div>
    {before_after_slider()}
  </div>
</section>

<!-- ===== TESTIMONIALS ===== -->
<section class="sec sec-alt">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">What clients say</span>
      <h2>Booked again, and again</h2>
      <p class="lede">Reviews left on our <a href="{GOOGLE_REVIEWS_URL}" rel="nofollow noopener" target="_blank">Google Business Profile</a>, quoted word for word.</p>
    </div>
    {testimonials()}
  </div>
</section>

<!-- ===== AREAS ===== -->
<section class="sec" id="areas">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Where we work</span>
      <h2>Serving Frankston and the Mornington Peninsula</h2>
      <p class="lede">We cover lawn mowing in Frankston and every other service on this page across 18 suburbs, working out of Frankston. If yours is on the list, we can usually get to you within the week.</p>
    </div>
    {areas_grid()}
    {map_embed('Prestige Property Care service area map — Frankston VIC and the Mornington Peninsula')}
  </div>
</section>

<!-- ===== FAQ ===== -->
<section class="sec sec-alt">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Common questions</span>
      <h2>Before you call</h2>
    </div>
    {faq_block(HOME_FAQS)}
  </div>
</section>

<!-- ===== CONTACT ===== -->
<section class="sec" id="contact">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Get in touch</span>
      <h2>Free quote, no obligation</h2>
      <p class="lede">Whether it is lawn mowing in Frankston, a gutter clean or a full property tidy-up, call for the fastest answer or send the form and we will come back to you with a price.</p>
    </div>
    <div class="contact-grid">
      <div>{nap_list()}</div>
      {quote_form()}
    </div>
  </div>
</section>

</main>
"""


# =============================================================== SERVICE PAGES
def page_service(sp):
    s = SVC_BY_SLUG[sp["slug"]]
    path = "/services/%s/" % sp["slug"]
    trail = [("Home", "/"), ("Services", "/services/"), (sp["crumb"], None)]
    panels = "".join(
        '<div class="panel"><h3>%s</h3><p>%s</p><ul>%s</ul></div>'
        % (p[0], p[1], "".join("<li>%s</li>" % li for li in p[2]))
        for p in sp["panels"])
    return f"""<section class="page-hero">
  <div class="hero-media" aria-hidden="true">{picture(s['img'], eager=True, sizes='100vw')}</div>
  <div class="hero-in">
    {crumbs(trail)}
    <span class="eyebrow">{sp['eyebrow']}</span>
    <h1>{sp['h1']}</h1>
    <p class="hero-sub">{sp['sub']}</p>
    <div class="hero-cta">
      <a href="#quote" class="btn-lg btn-solid">Get a free quote</a>
    </div>
  </div>
</section>

<div class="trustbar">
  <div class="wrap">
    <ul>
      <li>{svg('check')}Free fixed-price quotes</li>
      <li>{svg('check')}Frankston based</li>
      <li>{svg('check')}All waste taken away</li>
      <li>{svg('check')}Residential &amp; commercial</li>
      <li>{svg('check')}Fully insured</li>
    </ul>
  </div>
</div>

<main id="main">

<section class="sec">
  <div class="wrap">
    <div class="split start">
      <div class="prose">
        <div class="callout">
          <p><strong>{sp['answer']}</strong></p>
        </div>
        {sp['body']}
      </div>
      <div class="quote-col"><div id="quote">{quote_form(preselect=sp.get('preselect'), heading='Get a free quote')}</div></div>
    </div>
  </div>
</section>

<section class="sec sec-alt">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">What&rsquo;s included</span>
      <h2>{sp['panels_head']}</h2>
    </div>
    <div class="panels">{panels}</div>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Where we work</span>
      <h2>{sp['areas_head']}</h2>
      <p class="lede">{sp['areas_lede']}</p>
    </div>
    {areas_grid()}
  </div>
</section>

<section class="sec sec-alt">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Common questions</span>
      <h2>{sp['faq_head']}</h2>
    </div>
    {faq_block(sp['faqs'])}
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Also from Prestige</span>
      <h2>Other services we bring on the same visit</h2>
      <p class="lede">Most jobs get booked together. If we are already on site, adding another task rarely costs a second trip.</p>
    </div>
    {service_cards(exclude=sp['slug'], limit=3)}
  </div>
</section>

</main>

{cta_band(sp['cta_head'], sp['cta_text'])}"""


SERVICE_PAGES = [
# ------------------------------------------------------- 1. GUTTER CLEANING
{
 "slug": "gutter-cleaning",
 "crumb": "Gutter Cleaning",
 "title": "Gutter Cleaning Frankston | Prestige Property Care",
 "desc": "Gutter cleaning in Frankston by Prestige Property Care. Gutters and downpipes cleared by hand, all debris taken away. Free quotes across the Peninsula.",
 "keyword": "gutter cleaning frankston",
 "eyebrow": "Gutter cleaning",
 "h1": "Gutter Cleaning in Frankston &amp; Surrounding Suburbs",
 "sub": "Gutters and downpipes cleared by hand, every bit of debris bagged and taken with us. Booked most often before storm season and after the autumn leaf drop.",
 "preselect": "Gutter cleaning",
 "answer": "Gutter cleaning in Frankston costs less than the eaves repair it prevents. Prestige Property Care clears gutters and downpipes by hand across Frankston, Seaford, Carrum Downs, Langwarrin and the Mornington Peninsula, removes all debris from the property, and quotes a fixed price before starting.",
 "body": """
<h2>Why gutter cleaning in Frankston matters more than it does most places</h2>
<p>Frankston sits under a lot of gum. Between the leaf drop and the bark, a gutter that looked fine in February can be packed solid by May. Once it is full, water does not go down the downpipe &mdash; it goes over the lip, into the eaves, and then into the wall cavity or the ceiling. That is a plaster and timber job, and it costs many times what a <strong>gutter cleaning</strong> visit does.</p>
<p>Homes close to the coast at Seaford, Mount Eliza and Mount Martha have a second problem. Salt air and constant sea breeze fill gutters with fine grit that packs down hard and holds water against the metal. Left alone it rusts the gutter through from the inside.</p>
<h2>How we clean gutters</h2>
<p>We work off ladders and clear by hand, not by blowing debris across the roof and into your garden. Every gutter run is emptied, the downpipes are checked for blockages and flushed, and the debris goes into buckets and onto the trailer. Before we leave, the ground under the gutter line is cleared so you cannot tell we were there except by looking up.</p>
<p>If we find a problem &mdash; a sagging bracket, a split joint, rust starting through, a downpipe that will not clear &mdash; we tell you and show you a photo. We do not quietly patch things or invent work that is not needed.</p>
<h2>When to book</h2>
<p>Two cleans a year covers most Frankston homes: one after autumn drops its load, and one going into spring before the storms arrive. Properties with gums directly overhead, or with a lot of tree cover across Frankston South and Langwarrin, are better on a three or four month cycle. Ask us when we are there and we will tell you honestly which one your roof needs.</p>
<p>We also clean gutters on commercial buildings, rental properties and body corporate sites on a scheduled cycle, with the same report-back on anything that needs a roof plumber rather than a gutter clean.</p>
""",
 "panels_head": "What gutter cleaning in Frankston covers",
 "panels": [
   ("Gutters cleared by hand", "Every run emptied properly, not blown out across the roof and garden.",
    ["All gutter runs cleared end to end", "Debris bagged on site", "Ground under the gutter line left clean"]),
   ("Downpipes checked and flushed", "A clear gutter still overflows if the downpipe below it is blocked.",
    ["Downpipes tested and cleared", "Flushed through where access allows", "Blockages reported before we leave"]),
   ("An honest look at the roofline", "You get told what we found, with photos, not a sales pitch.",
    ["Loose brackets and split joints flagged", "Rust and wear pointed out early", "No work done that you did not agree to"]),
 ],
 "areas_head": "Gutter cleaning across Frankston and the Peninsula",
 "areas_lede": "We clean gutters in Frankston and every suburb below, including Mornington, where gutter cleaning is one of our most requested jobs.",
 "faq_head": "Gutter cleaning questions",
 "faqs": [
   ("How much does gutter cleaning cost in Frankston?",
    "Price depends on the size of the roof, how many storeys, how much debris has built up and how easy the gutters are to reach. A standard single-storey Frankston home with reasonable access is straightforward. A double-storey with steep pitch or tight side access takes longer and costs more. We quote a fixed price before we start, so there is no hourly rate running while we work."),
   ("How often should gutters be cleaned in Frankston?",
    "Twice a year suits most homes &mdash; after the autumn leaf drop and again before storm season. If your roof sits under gum trees, or you are near the coast at Seaford, Mount Eliza or Mount Martha, every three to four months is safer. Blocked gutters overflow into the eaves and wall cavity, and that repair costs far more than the clean."),
   ("Do you clean two-storey gutters?",
    "Yes, where it can be done safely from a ladder with proper footing. Tell us the height and the access when you call and we will let you know before we come out. If a roof genuinely needs height equipment we will say so rather than take a risk on it."),
   ("Do you take the debris away?",
    "Yes. Leaves, bark, grit and anything else that comes out of the gutter goes into buckets, onto the trailer and off the property with us. Nothing is left in a pile by the bin."),
   ("Do you clean gutters on rental and commercial properties?",
    "Yes. We work with landlords, property managers, body corporates and commercial sites across Frankston and the Peninsula on scheduled cleans, and we can report back with photos after each visit."),
 ],
 "cta_head": "Book a gutter clean before the next storm",
 "cta_text": "Free fixed-price quotes across Frankston, Seaford, Carrum Downs, Langwarrin, Mount Eliza and the Mornington Peninsula.",
},

# ---------------------------------------------------- 2. RUBBISH REMOVAL
{
 "slug": "rubbish-removal",
 "crumb": "Green Waste &amp; Rubbish Removal",
 "title": "Rubbish Removal Frankston | Prestige Property Care",
 "desc": "Rubbish removal in Frankston from Prestige Property Care. Green waste, clippings, old timber and household junk loaded and taken away. Free quotes.",
 "keyword": "rubbish removal frankston",
 "eyebrow": "Green waste &amp; rubbish removal",
 "h1": "Green Waste &amp; Rubbish Removal in Frankston",
 "sub": "Clippings, prunings, old timber and general household junk loaded onto the trailer and taken away the same day. No waiting months for a council hard waste booking.",
 "preselect": "rubbish removal",
 "answer": "Rubbish removal in Frankston through Prestige Property Care means we load it and it leaves the same day. We take green waste, garden clippings, prunings, old timber and general household junk from properties across Frankston, Carrum Downs, Skye, Seaford and the Mornington Peninsula, for a fixed price quoted before we start.",
 "body": """
<h2>Rubbish removal in Frankston, without waiting on the council</h2>
<p>Frankston City runs a hard waste service, and for some things it is the right answer. But it is booked out, it has rules about what goes on the nature strip, and it will not touch most garden waste at all. If you have a trailer load of hedge clippings, a dismantled deck or a garage that has not been emptied since you moved in, waiting is not much of a plan.</p>
<p>We do <strong>rubbish removal</strong> the direct way. We turn up, we load it, and it goes. You do not lift anything, you do not stack it on the nature strip, and you do not spend a Saturday doing trailer runs to the transfer station.</p>
<h2>What we take</h2>
<p>Green waste is the bulk of it: grass clippings, hedge and tree prunings, leaves, weeds, old turf and garden bed clear-outs. Alongside that we take general household and yard junk &mdash; old fence palings and timber, broken outdoor furniture, cardboard and packaging, garage and shed clear-outs, and the odds and ends left behind after a tenant moves out.</p>
<p>What we do not take is anything hazardous: asbestos, paint, chemicals, gas bottles, tyres, batteries or liquids. If you are unsure about something, send a photo when you call and we will tell you straight away.</p>
<h2>Booked with the mowing, or on its own</h2>
<p>Most green waste removal happens as part of a job we are already doing &mdash; the clippings from a mow, the branches from a hedge trim, the whole yard after an end-of-lease clean-up. That costs less, because there is no second trip. But we take standalone loads too, and that is often what people want after a renovation, a big garden clear-out or a house clearance.</p>
<p>One thing worth saying plainly: if what you actually want is the free council hard waste collection, book that with Frankston City Council rather than paying us. We are for the jobs where you want it gone now, gone properly, and without doing the lifting.</p>
""",
 "panels_head": "What our rubbish removal in Frankston takes",
 "panels": [
   ("Green waste", "Everything the garden produces, taken the same day.",
    ["Grass clippings and lawn thatch", "Hedge, shrub and tree prunings", "Weeds, leaves and old turf"]),
   ("Yard and household junk", "The things that have been &lsquo;going to the tip one day&rsquo; for two years.",
    ["Old timber, palings and decking", "Broken outdoor furniture", "Shed, garage and house clear-outs"]),
   ("What we cannot take", "Told up front, so nothing is a surprise on the day.",
    ["No asbestos or building hazards", "No paint, chemicals or liquids", "No gas bottles, tyres or batteries"]),
 ],
 "areas_head": "Rubbish removal across Frankston and the Peninsula",
 "areas_lede": "Same-week pickups in Frankston and every suburb below, with the Peninsula runs usually grouped so we can get to you faster.",
 "faq_head": "Rubbish removal questions",
 "faqs": [
   ("How much does rubbish removal cost in Frankston?",
    "It is priced on volume and what the load is. A trailer of green waste from a hedge trim is cheap. A full garage clear-out with heavy timber and furniture takes longer and costs more. Send a photo when you call and we can usually give you a price on the spot rather than making you wait for a site visit."),
   ("Is this the same as council hard rubbish collection?",
    "No, and it is worth being clear about it. Frankston City Council runs a free hard waste collection with its own booking system and rules, and it does not cover most garden waste. We are a paid service for when you want it gone now, loaded by us, without stacking it on the nature strip or waiting for a booking date."),
   ("Do you take green waste away after mowing and hedge trimming?",
    "Always, and it is included in the job. Clippings and prunings go straight on the trailer and leave with us. Nothing is left in a pile beside the bin."),
   ("Do I need to be home?",
    "Not if we can get to the load and you have told us what is going. Plenty of clear-outs happen while people are at work. We will confirm what is being taken beforehand so nothing goes that should have stayed."),
   ("Can you clear a whole property after a tenant leaves?",
    "Yes. Full yard and property clear-outs are a regular job for us, often alongside an end-of-lease garden clean-up so the place is presented ready for the final inspection."),
 ],
 "cta_head": "Get that pile off the property this week",
 "cta_text": "Fixed-price rubbish and green waste removal in Frankston, Carrum Downs, Skye, Seaford and across the Mornington Peninsula.",
},

# --------------------------------------------------- 3. GARDEN MAINTENANCE
{
 "slug": "garden-maintenance",
 "crumb": "Garden Maintenance",
 "title": "Gardener Frankston | Garden Maintenance | Prestige",
 "desc": "Need a gardener in Frankston? Prestige Property Care covers weeding, mulching, pruning and regular garden maintenance across Frankston and the Peninsula.",
 "keyword": "gardener frankston",
 "eyebrow": "Garden maintenance",
 "h1": "Your Local Gardener in Frankston &amp; Frankston South",
 "sub": "Weeding, mulching, pruning and general garden upkeep on a schedule that suits the property &mdash; whether you are time-poor, getting older, or managing the place from somewhere else.",
 "preselect": "Garden maintenance",
 "answer": "Prestige Property Care is a local gardener in Frankston covering weeding, mulching, pruning, bed maintenance and seasonal tidy-ups on regular scheduled visits. We work across Frankston, Frankston South, Karingal, Langwarrin and the Mornington Peninsula, and quote a fixed price per visit rather than charging by the hour.",
 "body": """
<h2>What a regular gardener in Frankston actually does</h2>
<p>Mowing keeps the lawn under control. Everything else in a garden &mdash; the beds, the shrubs, the mulch, the weeds coming up through the gravel &mdash; needs a different kind of attention, and it is what most people are really asking for when they go looking for a <strong>gardener</strong> in Frankston.</p>
<p>On a maintenance visit we weed the beds properly, cut back and shape shrubs, prune what is due for pruning, top up mulch where it has thinned, clear the leaf litter out of the corners, and keep the borders between lawn and bed clean. Over a few visits a garden that had been slipping starts holding its shape between visits instead of needing rescuing.</p>
<h2>Who books a gardener in Frankston</h2>
<p>Three groups, mostly. People who work full time and have simply run out of weekends. Older residents around Frankston South and Karingal who have kept a beautiful garden for thirty years and now want the heavy part done by someone else. And owners who are not here &mdash; investment properties, holiday homes on the Peninsula, and people managing a family home from interstate.</p>
<p>That last group is why we send a note after each visit if you want one. If you are not there to see the garden, you should still know what was done.</p>
<h2>How often it needs doing</h2>
<p>Fortnightly through spring and summer, when everything is growing at once and weeds are the main enemy. Monthly through the cooler months is usually enough, shifting to a bigger seasonal tidy-up in early spring and again in autumn. We will tell you what the garden needs rather than selling you the most frequent option.</p>
<p>If the garden has already got away from you, that is a clean-up first, then maintenance. We quote the two separately so you can see what is the one-off catch-up and what the ongoing cost looks like.</p>
""",
 "panels_head": "What your gardener in Frankston does each visit",
 "panels": [
   ("Beds and borders", "The part that makes a garden look cared for rather than just cut.",
    ["Hand weeding through beds and gravel", "Mulch topped up and levelled", "Clean edges between lawn and bed"]),
   ("Shrubs and pruning", "Cut back at the right time, not just when it is convenient.",
    ["Shaping and cutting back", "Seasonal pruning of shrubs and small trees", "Dead growth and spent flowers removed"]),
   ("Seasonal tidy-ups", "The bigger reset, twice a year.",
    ["Full leaf and litter clear", "Beds reset going into spring", "All green waste taken away"]),
 ],
 "areas_head": "A gardener across Frankston and the Peninsula",
 "areas_lede": "Regular garden maintenance rounds through Frankston, Frankston South, Karingal, Langwarrin, Mount Eliza, Mornington and the suburbs below.",
 "faq_head": "Garden maintenance questions",
 "faqs": [
   ("How much does a gardener in Frankston cost?",
    "We price per visit based on the size of the garden and what it needs, not by the hour. That means you know the cost before we arrive and it does not change because a job took longer than expected. Regular fortnightly or monthly visits cost less per visit than one-off work, because the garden never gets far enough away to need catching up."),
   ("Do you do one-off garden work or only regular visits?",
    "Both. Plenty of people start with a one-off tidy-up to get the garden back under control and then decide whether to put it on a schedule. There is no contract and no minimum term either way."),
   ("Can you maintain a property while I am away?",
    "Yes. We maintain holiday homes across Mount Eliza, Mornington and Mount Martha and investment properties throughout Frankston for owners who are not local. We can send a short note or photos after each visit so you know exactly what was done."),
   ("Do you look after native gardens?",
    "Yes. Native and coastal plantings are common across the Peninsula and they need a lighter hand than an exotic garden &mdash; pruned at the right time of year, mulched properly and not fertilised like a rose bed. Tell us what is planted and we will work with it."),
   ("Do you take the green waste with you?",
    "Always. Weeds, prunings and clippings go on the trailer and leave with us on the day."),
 ],
 "cta_head": "Get your garden back on a schedule",
 "cta_text": "Free quotes for regular garden maintenance across Frankston, Frankston South, Karingal, Langwarrin and the Mornington Peninsula.",
},
]

SERVICE_PAGES += [
# -------------------------------------------------------- 4. LAWN MOWING
{
 "slug": "lawn-mowing",
 "crumb": "Lawn Mowing",
 "title": "Lawn Mowing Mornington | Prestige Property Care",
 "desc": "Lawn mowing in Mornington and across the Peninsula. Prestige Property Care mows, catches and edges on weekly, fortnightly or one-off visits. Free quotes.",
 "keyword": "lawn mowing mornington",
 "eyebrow": "Lawn mowing",
 "h1": "Lawn Mowing in Mornington &amp; the Mornington Peninsula",
 "sub": "Mown, caught and edged on every visit. Weekly and fortnightly rounds through Mornington, Mount Eliza, Mount Martha and Moorooduc, plus one-off cuts when a lawn has got away.",
 "preselect": "Lawn mowing",
 "answer": "Lawn mowing in Mornington from Prestige Property Care includes mowing, catching and edging on every visit, with all clippings taken away. We run weekly, fortnightly and monthly rounds across Mornington, Mount Eliza, Mount Martha, Moorooduc, Somerville and Tyabb, and quote a fixed price per visit.",
 "body": """
<h2>Lawn mowing in Mornington is its own kind of job</h2>
<p>Grass on the Peninsula grows on a different clock to the rest of Melbourne. The coastal humidity through Mornington and Mount Martha pushes couch and kikuyu hard from October onwards, and a lawn that was fine on a fortnightly cycle in September will be shin-deep by late November on the same schedule.</p>
<p>That is why we adjust the round rather than running the same interval all year. Through the peak of the growing season most properties go weekly or ten-daily. Through winter, monthly is usually plenty. You are not paying for visits the lawn does not need.</p>
<h2>What is included in every visit</h2>
<p>Mow, catch and edge, every time. The lawn is cut at a height that suits the grass type rather than scalped to make the next visit easier. Edges are cut sharp along paths, driveways and garden beds &mdash; the single thing that makes the difference between a lawn that has been cut and a lawn that looks looked after. Paths and drives are blown clean, and the clippings go on the trailer and leave with us.</p>
<h2>Holiday homes and absentee owners</h2>
<p>A lot of Peninsula properties are not lived in full time, and an empty house with knee-high grass advertises the fact. We maintain holiday homes across Mornington, Mount Martha and Mount Eliza on standing schedules, keeping the place presentable between visits from the owners. If you want a note or a photo after each visit, we will send one.</p>
<h2>One-off cuts and overgrown lawns</h2>
<p>If the lawn has been left for months, the first cut is a different job to a regular mow &mdash; often two passes, sometimes a slasher first, and always a lot more waste to take away. We quote that separately and honestly. Once it is back under control, the ongoing cost drops to a normal round.</p>
<p>Closer to home we also cover <a href="/">lawn mowing in Frankston</a> and the surrounding suburbs, so if your property is on the Frankston side of the Peninsula that is the same crew and the same schedule.</p>
""",
 "panels_head": "Every mowing visit includes",
 "panels": [
   ("Mown and caught", "Cut at the right height for the grass, not scalped.",
    ["Height set to the grass type and season", "Clippings caught, not left in rows", "Two passes when a lawn has got away"]),
   ("Edged properly", "The detail that makes a lawn look finished.",
    ["Sharp edges along paths and drives", "Garden bed borders cut clean", "Around trees, poles and letterboxes"]),
   ("Left tidy", "We do not leave the mess for you.",
    ["Paths and drives blown clean", "Clippings on the trailer and gone", "Gates closed and pets kept in mind"]),
 ],
 "areas_head": "Mowing rounds across the Peninsula and Frankston",
 "areas_lede": "Regular lawn mowing in Mornington, Mount Eliza, Mount Martha, Moorooduc, Somerville and Tyabb, plus every Frankston City suburb below.",
 "faq_head": "Lawn mowing questions",
 "faqs": [
   ("How much does lawn mowing cost in Mornington?",
    "It depends on the size of the lawn, the access, and how much growth has built up since the last cut. We quote a fixed price per visit after seeing the property, so it does not change week to week. Regular rounds cost less per visit than one-off cuts, because the lawn never gets long enough to need extra work."),
   ("How often should you mow a lawn on the Mornington Peninsula?",
    "Weekly to ten-daily through the peak growing season from October to March, then fortnightly through the shoulder months and monthly over winter. Coastal humidity through Mornington and Mount Martha pushes growth harder than inland Melbourne, so a fixed year-round interval usually means the lawn is either overgrown in summer or being cut for no reason in July."),
   ("Do you edge as well as mow?",
    "Yes, on every visit, at no extra cost. Edging along paths, drives and garden beds is included in the mowing price rather than being an add-on."),
   ("Do you mow lawns at holiday homes when the owner is away?",
    "Yes. It is a large part of what we do on the Peninsula. We keep the property presentable on a standing schedule and can report back after each visit if you are not local."),
   ("My lawn has not been cut in months. Can you still do it?",
    "Yes. It takes longer and produces a lot more waste, so we quote the first cut separately from the ongoing round. After that first visit the cost comes back down to a normal mow."),
 ],
 "cta_head": "Get on the mowing round",
 "cta_text": "Weekly, fortnightly and monthly lawn mowing across Mornington, Mount Eliza, Mount Martha, Frankston and the surrounding suburbs.",
},

# ------------------------------------------------------ 5. HEDGE TRIMMING
{
 "slug": "hedge-trimming",
 "crumb": "Hedge Trimming &amp; Edging",
 "title": "Hedge Trimming Frankston | Prestige Property Care",
 "desc": "Hedge trimming in Frankston from Prestige Property Care. Hedges shaped and levelled, lawn edges cut sharp, all clippings taken away. Free quotes.",
 "keyword": "hedge trimming frankston",
 "eyebrow": "Hedge trimming &amp; edging",
 "h1": "Hedge Trimming &amp; Lawn Edging in Frankston",
 "sub": "Hedges shaped, levelled and brought back into line, and edges cut sharp along every path, drive and garden bed. The two jobs that make a tidy yard look properly finished.",
 "preselect": "Hedge trimming",
 "answer": "Hedge trimming in Frankston from Prestige Property Care covers shaping, levelling and height reduction on hedges of any size, plus sharp lawn edging along paths, drives and garden beds. All clippings are taken away the same day, and we quote a fixed price across Frankston, Langwarrin, Karingal, Baxter and the Mornington Peninsula.",
 "body": """
<h2>Hedge trimming in Frankston: shaped, or just a bush</h2>
<p>Hedges have a habit of creeping. A few centimetres a season on the top and both faces, and after three or four years the thing that was a crisp screen along the fence line is a wall of growth leaning into the path. It happens slowly enough that you stop noticing it.</p>
<p>Our <strong>hedge trimming</strong> work puts the shape back: faces cut plumb and level, the top run straight to a line rather than by eye, and the height brought down where it has got away. If a hedge has been let go badly we will often bring it back over two visits rather than cutting hard into old wood in one hit, which can leave bare patches that take a season or more to fill.</p>
<h2>Edging, which nobody books but everybody notices</h2>
<p>Lawn edging is the cheapest improvement to the look of a property that exists. A lawn that has been mown but not edged reads as unfinished; the same lawn with clean edges along the footpath, the driveway and every garden bed reads as maintained. We edge as part of every mowing visit, and we also do one-off edging on properties we are not mowing &mdash; usually before a sale, an inspection or a family event.</p>
<h2>What we cut</h2>
<p>Most hedge trimming in Frankston we take on is formal hedging &mdash; box, photinia, murraya, viburnum, lilly pilly &mdash; alongside the informal screening hedges that are common through Langwarrin and Baxter, native screens, and topiary that needs keeping in shape. Larger jobs on body corporate and commercial sites are done on a scheduled cycle so the presentation stays consistent instead of swinging between overgrown and freshly cut.</p>
<p>Every hedge trimming job in Frankston ends the same way: clippings raked and blown out of the beds, paths cleared, and the whole lot on the trailer and off the property. Hedge clippings left on site are the most common complaint people have about the last person who did it.</p>
""",
 "panels_head": "What hedge trimming in Frankston covers",
 "panels": [
   ("Shaping and levelling", "Cut to a line, not by eye.",
    ["Faces cut plumb, tops run level", "Height reduction on overgrown hedges", "Staged cutting where a hedge has been let go"]),
   ("Lawn and bed edging", "The finish that makes the whole yard read as maintained.",
    ["Sharp edges along paths and drives", "Garden bed borders cut clean", "Included free with every mow"]),
   ("Scheduled hedge rounds", "For sites that need to stay presentable year round.",
    ["Body corporate and commercial screens", "Rental portfolios kept consistent", "Set cycles so nothing gets away"]),
 ],
 "areas_head": "Hedge trimming across Frankston and the Peninsula",
 "areas_lede": "We trim hedges and cut edges in Frankston, Langwarrin, Karingal, Baxter and every suburb below, across the Frankston City area and the Mornington Peninsula.",
 "faq_head": "Hedge trimming in Frankston: your questions",
 "faqs": [
   ("How much does hedge trimming cost in Frankston?",
    "It comes down to the length and height of the hedge, how far it has been let go, and how much waste comes off it. A regularly maintained hedge is quick. One that has not been touched in three years is a bigger job with a lot more to take away. We quote a fixed price after seeing it, and we will tell you if it is better done over two visits."),
   ("When is the best time to trim a hedge in Melbourne?",
    "Late spring and again in late summer suits most formal hedges here, with a light tidy in between if you want it crisp year round. Avoid hard cutting in the middle of winter or during a heatwave. Flowering hedges are better trimmed just after they finish flowering so you do not cut off next season's buds."),
   ("Can you bring an overgrown hedge back?",
    "Usually, yes. If the hedge is healthy we can reduce it back towards its original line, though on some species cutting hard into old bare wood will leave patches that take a season to fill. Where that is a risk we stage it over two visits so it recovers properly."),
   ("Do you do edging on its own?",
    "Yes. Edging is included free on every mowing visit, but we also do one-off edging for properties we do not mow &mdash; commonly before a sale, an open inspection or an event."),
   ("What happens to the clippings?",
    "They are raked and blown out of the beds and off the paths, loaded onto the trailer and taken away the same day. Nothing is left behind the shed."),
 ],
 "cta_head": "Get the hedges back into line",
 "cta_text": "Free quotes on hedge trimming and lawn edging across Frankston, Langwarrin, Karingal, Baxter and the Mornington Peninsula.",
},

# ---------------------------------------------------- 6. GARDEN CLEAN-UPS
{
 "slug": "garden-clean-ups",
 "crumb": "Garden Clean-Ups",
 "title": "Garden Clean Up Frankston | Prestige Property Care",
 "desc": "Garden clean up in Frankston for end-of-lease and pre-sale. Prestige brings overgrown yards back to inspection standard and clears all waste.",
 "keyword": "garden clean up frankston",
 "eyebrow": "End-of-lease &amp; pre-sale",
 "h1": "End-of-Lease &amp; Pre-Sale Garden Clean-Ups in Frankston",
 "sub": "Overgrown yards brought back to inspection standard, with every bit of waste gone the same day. Booked by renters chasing a bond, landlords between tenants, and agents preparing a home for photos.",
 "preselect": "clean-up",
 "answer": "A garden clean up in Frankston with Prestige Property Care brings an overgrown yard back to inspection standard in a single visit: lawns cut and edged, beds weeded, hedges shaped, paths cleared and all green waste removed. We work to your inspection or photography date across Frankston, Carrum Downs, Seaford, Mount Eliza and the Mornington Peninsula.",
 "body": """
<h2>A garden clean up in Frankston usually has a deadline attached</h2>
<p>Almost every <strong>garden clean up</strong> we do in Frankston is driven by a date. Either there is a final inspection and a bond on the line, or the property is going to market and the photographer is booked for Thursday. Both mean the yard has to go from wherever it is now to presentable, in one visit, by a fixed day.</p>
<p>Tell us the date when you call. We work backwards from it, and if it is not achievable we will say so straight away rather than taking the booking and letting you find out on the day.</p>
<h2>End-of-lease clean-ups</h2>
<p>Property managers assess a yard on a short list of things: is the lawn cut and edged, are the beds free of weeds, are the hedges in shape, are the paths and paving clear, and is there any rubbish left on the property. We do all of it, including hauling away whatever has accumulated down the side of the house over the tenancy.</p>
<p>The maths is simple. A clean-up costs a fraction of what a property manager will charge back against your bond to send their own contractor, and you get to be there and see it done.</p>
<h2>Pre-sale garden makeovers</h2>
<p>Buyers look at a photo for about two seconds. An unedged lawn and a weedy front bed drag down the first impression of a house that is otherwise fine. A pre-sale tidy-up &mdash; lawn cut and edged, mulch topped up, hedges shaped, paths pressure-swept and clear &mdash; is one of the cheapest things you can do before listing, and it shows up in the photos immediately.</p>
<p>We work with agents and vendors across Frankston, Frankston South, Seaford and the Peninsula, and we can schedule around the photography date so the garden peaks on the right day.</p>
<h2>What a clean-up covers</h2>
<p>Lawns cut, often in two passes if it is deep, then caught and edged. Beds weeded by hand and re-mulched where needed. Hedges and shrubs cut back into shape. Paths, paving and drives cleared and blown. Then every bit of it &mdash; clippings, prunings, weeds and any rubbish left on site &mdash; loaded and taken away. You are not left with the mess or a full green bin.</p>
""",
 "panels_head": "What a garden clean up in Frankston puts right",
 "panels": [
   ("Lawns and edges", "Back from overgrown to inspection standard.",
    ["Two passes where the grass is deep", "Caught, not left in windrows", "Every edge cut sharp"]),
   ("Beds, hedges and paths", "The things an inspection or a photo picks up first.",
    ["Beds hand-weeded and re-mulched", "Hedges and shrubs cut back into shape", "Paths, paving and drives cleared"]),
   ("Everything taken away", "The yard is empty when we leave.",
    ["All green waste loaded and gone", "Rubbish left on site removed", "No waiting on a council booking"]),
 ],
 "areas_head": "Garden clean up in Frankston and across the Peninsula",
 "areas_lede": "End-of-lease and pre-sale garden clean-ups in Frankston and every suburb below, scheduled around your inspection or photography date.",
 "faq_head": "Garden clean up in Frankston: your questions",
 "faqs": [
   ("How much does a garden clean up cost in Frankston?",
    "It depends on the size of the yard and how far it has gone. A tidy that is mostly mowing and edging is straightforward. A yard that has not been touched in a year, with waist-high grass and a pile down the side of the house, is a bigger job with a lot more waste to remove. We quote a fixed price after seeing it, or from photos if you are short on time."),
   ("Will a clean-up get my bond back?",
    "It handles the garden side of the inspection, which is what most tenants get pulled up on: lawns cut and edged, beds weeded, hedges shaped, paths clear and no rubbish left. We cannot speak for the inside of the house, but the yard will not be the reason you lose the bond."),
   ("How quickly can you do it?",
    "Often within the same week, and we prioritise jobs with a hard inspection or photography date. Tell us the deadline when you call and we will tell you honestly whether we can meet it."),
   ("Do you work with real estate agents and property managers?",
    "Yes, regularly. We handle pre-sale makeovers before photography and between-tenancy clean-ups for agencies and landlords across Frankston, Frankston South, Seaford, Carrum Downs and the Peninsula."),
   ("Do you take away the rubbish as well as the green waste?",
    "Yes. Green waste and general rubbish left on the property both go with us the same day, so the yard is genuinely clear rather than just cut."),
 ],
 "cta_head": "Got an inspection date?",
 "cta_text": "Tell us the deadline and we will work backwards from it. Free quotes on end-of-lease and pre-sale clean-ups across Frankston and the Peninsula.",
},
]


# ============================================================ SERVICES HUB
HUB_FAQS = [
    ("What services does Prestige Property Care offer in Frankston?",
     "Prestige Property Care offers lawn mowing, lawn edging, garden maintenance, hedge trimming, gutter cleaning, green waste and rubbish removal, end-of-lease and pre-sale garden clean-ups, and general property maintenance for commercial sites and rental portfolios. All of it is available across Frankston and the Mornington Peninsula, and most of it can be booked on a single visit."),
    ("Can I book more than one service at once?",
     "Yes, and it is usually cheaper. If we are already on site for a mow, adding a hedge trim, a gutter clean or a load of green waste rarely costs a second call-out. One booking, one invoice, one crew that already knows the property."),
    ("Do you do regular visits or only one-off jobs?",
     "Both. Regular weekly, fortnightly and monthly rounds are what most residential clients end up on, but there is no contract and no minimum term. Plenty of people start with a one-off clean-up and decide afterwards whether to put the property on a schedule."),
    ("Do you work on commercial and rental properties?",
     "Yes. We maintain grounds for commercial sites, body corporate properties and rental portfolios across Frankston and the surrounding suburbs on scheduled visits, with consistent presentation between them."),
]

def page_services():
    trail = [("Home", "/"), ("Services", None)]
    return f"""<section class="page-hero">
  <div class="hero-media" aria-hidden="true">{picture('work-garden', eager=True, sizes='100vw')}</div>
  <div class="hero-in">
    {crumbs(trail)}
    <span class="eyebrow">All services</span>
    <h1>Lawn Mowing Services in Frankston &amp; Property Care</h1>
    <p class="hero-sub">Everything Prestige Property Care does, in one place. Lawn mowing services in Frankston and across the Peninsula, plus gutters, hedges, gardens, green waste and full clean-ups &mdash; bookable together on a single visit.</p>
    <div class="hero-cta">
      <button type="button" class="btn-lg btn-solid" data-quote-open>Get a free quote</button>
    </div>
  </div>
</section>

<div class="trustbar">
  <div class="wrap">
    <ul>
      <li>{svg('check')}One crew, every service</li>
      <li>{svg('check')}Fixed quotes, not hourly rates</li>
      <li>{svg('check')}All waste taken away</li>
      <li>{svg('check')}18 suburbs covered</li>
      <li>{svg('check')}No contracts</li>
    </ul>
  </div>
</div>

<main id="main">

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Choose a service</span>
      <h2>Six things we do, and we do them properly</h2>
      <p class="lede">Most clients start with lawn mowing services in Frankston and add the rest as they need it. Each page below covers what is included, what it costs and which suburbs we cover.</p>
    </div>
    {service_cards()}
  </div>
</section>

<section class="sec sec-alt">
  <div class="wrap">
    <div class="split">
      <div class="prose">
        <span class="eyebrow">Also available</span>
        <h2>Commercial and property maintenance</h2>
        <p>Alongside the residential work, Prestige Property Care maintains grounds for commercial sites, body corporate properties and rental portfolios across Frankston and the Mornington Peninsula. That covers scheduled mowing and edging, hedge and garden bed upkeep, gutter cleaning, exterior tidy-ups and waste removal &mdash; run on a set cycle so the presentation never swings between overgrown and freshly cut.</p>
        <p>We also take on general property maintenance: the odd jobs around a site that fall between trades and never quite get booked. If you are not sure whether something is in scope, call and ask. We will tell you plainly if it is not our work.</p>
        <div class="callout">
          <p><strong>Managing more than one property?</strong> Send the addresses and how often each needs attention and we will price the lot together.</p>
        </div>
      </div>
      <div class="split-media">{picture('work-hedge', sizes=SPLIT_SIZES)}</div>
    </div>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Where we work</span>
      <h2>Every service, across 18 suburbs</h2>
      <p class="lede">From the Frankston City suburbs down through the Mornington Peninsula. If your suburb is listed, we can usually get to you within the week.</p>
    </div>
    {areas_grid()}
  </div>
</section>

<section class="sec sec-alt">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Common questions</span>
      <h2>Booking Prestige</h2>
    </div>
    {faq_block(HUB_FAQS)}
  </div>
</section>

</main>

{cta_band('One call covers the whole property', 'Free, no-obligation quotes on any service across Frankston and the Mornington Peninsula.')}"""


# ================================================================== ABOUT
ABOUT_FAQS = [
    ("Who is Prestige Property Care?",
     "Prestige Property Care is a lawn, garden and property maintenance business based in Frankston VIC 3199, run by Dave Coelho. It covers lawn mowing, garden maintenance, hedge trimming, gutter cleaning, green waste removal and end-of-lease clean-ups across Frankston and the Mornington Peninsula."),
    ("Are you insured?",
     "Yes. Prestige Property Care carries public liability insurance, and we are happy to provide the certificate of currency to property managers, body corporates and commercial clients who need it on file before work starts."),
    ("Do you use subcontractors?",
     "No. The person who quotes your property is the person who does the work. That is the main reason clients stay with us &mdash; nobody has to be re-briefed on where the gate key is or which garden bed is not to be touched."),
    ("What areas do you cover?",
     "Frankston, Frankston South, Frankston North, Seaford, Langwarrin, Langwarrin South, Karingal, Carrum Downs, Skye, Baxter, Mount Eliza, Pearcedale, Mornington, Mount Martha, Moorooduc, Somerville, Tyabb and the wider Mornington Peninsula."),
    ("Do you require a contract?",
     "No. Regular rounds run on an ongoing basis with no minimum term and no lock-in. If you want to pause over winter or stop altogether, tell us and we will take you off the round."),
]

def page_about():
    trail = [("Home", "/"), ("About", None)]
    return f"""<section class="page-hero">
  <div class="hero-media" aria-hidden="true">{picture('about-dave', eager=True, sizes='100vw')}</div>
  <div class="hero-in">
    {crumbs(trail)}
    <span class="eyebrow">About us</span>
    <h1>About Prestige Property Care, Frankston</h1>
    <p class="hero-sub">A local lawn and garden business run out of Frankston by {BIZ['owner']}. Same crew every visit, fixed prices, and the waste leaves with us.</p>
    <div class="hero-cta">
      <button type="button" class="btn-lg btn-solid" data-quote-open>Get a free quote</button>
    </div>
  </div>
</section>

<div class="trustbar">
  <div class="wrap">
    <ul>
      <li>{svg('check')}Locally owned and run</li>
      <li>{svg('check')}No subcontractors</li>
      <li>{svg('check')}Fully insured</li>
      <li>{svg('check')}Residential &amp; commercial</li>
      <li>{svg('check')}No contracts or lock-ins</li>
    </ul>
  </div>
</div>

<main id="main">

<section class="sec">
  <div class="wrap">
    <div class="split">
      <div class="prose">
        <span class="eyebrow">Our story</span>
        <h2>One person, one trailer, and a round that kept growing</h2>
        <p><strong>Prestige Property Care is a lawn, garden and property maintenance business operating from Frankston VIC 3199.</strong> It is owned and run by {BIZ['owner']}, and it covers Frankston, the Frankston City suburbs and the Mornington Peninsula.</p>
        <p>The business grew the way these ones tend to: one property, then the neighbour, then their sister in Seaford. Nearly all of it came from people telling someone else that we turned up when we said we would. That is not a marketing line, it is just what happens in this trade when most operators do not.</p>
        <p>What has not changed as the round has grown is who does the work. There are no subcontractors and no rotating crews. The person who quotes your property is the person standing in it on the day, which is why nobody ever has to be told twice about the side gate, the dog, or the bed of natives that is not to be trimmed.</p>
        <h2>How we price</h2>
        <p>Fixed quotes, given free after we have seen the property. Not an hourly rate. An hourly rate rewards working slowly and leaves you watching the clock from the kitchen window, which is a strange way to run a relationship with someone who is at your house every fortnight.</p>
        <p>If a job turns out to be bigger than it looked, we tell you before we start rather than after we finish. And if what you actually need is not something we do, we say so &mdash; you are better off with the right trade than with us having a go at it.</p>
      </div>
      <div class="split-media tall">{picture('garden-maintenance', sizes=SPLIT_SIZES)}</div>
    </div>
  </div>
</section>

<section class="sec sec-dark">
  <div class="stripes" aria-hidden="true"></div>
  <div class="wrap" style="position:relative;z-index:2">
    <div class="sec-head">
      <span class="eyebrow">How we work</span>
      <h2>Four things we do not compromise on</h2>
    </div>
    <div class="why-grid">
      <div class="why-item"><span class="why-num">01</span><div><h3>We turn up</h3><p>You get a day and we keep to it. If weather moves a job we call you, rather than leaving you to work it out from the uncut lawn.</p></div></div>
      <div class="why-item"><span class="why-num">02</span><div><h3>The waste leaves with us</h3><p>Clippings, prunings, gutter debris. On the trailer and off the property the same day, every time.</p></div></div>
      <div class="why-item"><span class="why-num">03</span><div><h3>We finish the detail</h3><p>Edges cut, paths blown, gates closed. The last ten minutes of a job are what people actually remember.</p></div></div>
      <div class="why-item"><span class="why-num">04</span><div><h3>We tell you the truth about the job</h3><p>Including when a hedge is better done over two visits, or when the thing you are worried about does not need doing at all.</p></div></div>
    </div>
  </div>
</section>

<section class="sec sec-alt">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Our recent work</span>
      <h2>Properties we look after</h2>
      <p class="lede">Regular rounds, coastal gardens and gutter cleans from around Frankston and the Peninsula.</p>
    </div>
    {work_gallery()}
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">What clients say</span>
      <h2>The reason the round keeps growing</h2>
      <p class="lede">Straight from our <a href="{GOOGLE_REVIEWS_URL}" rel="nofollow noopener" target="_blank">Google reviews</a>.</p>
    </div>
    {testimonials()}
  </div>
</section>

<section class="sec sec-alt">
  <div class="wrap">
    <div class="contact-grid">
      <div>
        <div class="sec-head" style="margin-bottom:26px">
          <span class="eyebrow">Find us</span>
          <h2>Based in Frankston</h2>
          <p class="lede">We are based in Frankston and cover 18 suburbs across the Frankston City area and the Mornington Peninsula.</p>
        </div>
        {nap_list()}
      </div>
      <div>{map_embed('Map of the Prestige Property Care area around Frankston VIC 3199')}</div>
    </div>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Common questions</span>
      <h2>About Prestige</h2>
    </div>
    {faq_block(ABOUT_FAQS)}
  </div>
</section>

</main>

{cta_band('Work with a local you can actually get on the phone', 'Call ' + BIZ['phone_display'] + ' or send the form. Free quotes across Frankston and the Mornington Peninsula.')}"""


# ================================================================ CONTACT
CONTACT_FAQS = [
    ("How do I get a quote from Prestige Property Care?",
     "Call 0466 687 252, email dave@prestigepropertycare.com.au, or send the form on this page with your suburb and what you need looked at. Quotes are free, given as a fixed price rather than an hourly rate, and there is no obligation to book once you have the number."),
    ("How quickly do you respond?",
     "Calls are the fastest way to get an answer and are usually picked up or returned the same day. Form and email enquiries are answered within one business day. If you have a hard deadline &mdash; an inspection, a photography date, a storm on the way &mdash; say so and we will prioritise it."),
    ("What are your hours?",
     "We work Monday to Friday 7:00am to 5:00pm and Saturday 8:00am to 2:00pm. The phone is on outside those hours, but it may go to message if we are on a job."),
    ("Do you charge for quotes or call-outs?",
     "No. Quotes are free and there is no call-out fee to come and look at the property."),
    ("Do you service my suburb?",
     "We cover Frankston, Frankston South, Frankston North, Seaford, Langwarrin, Langwarrin South, Karingal, Carrum Downs, Skye, Baxter, Mount Eliza, Pearcedale, Mornington, Mount Martha, Moorooduc, Somerville, Tyabb and the wider Mornington Peninsula. If you are just outside that, call anyway &mdash; if we are already working nearby we can often fit you in."),
]

def page_contact():
    trail = [("Home", "/"), ("Contact", None)]
    return f"""<section class="page-hero hero-form">
  <div class="hero-media" aria-hidden="true">{picture('work-lawn', eager=True, sizes='100vw')}</div>
  <div class="hero-in">
    <div class="hero-split">
      <div class="hero-copy">
        {crumbs(trail)}
        <span class="eyebrow">Get in touch</span>
        <h1>Contact Prestige Property Care &mdash; Free Quotes in Frankston</h1>
        <p class="hero-sub">Fill in the form and we will come back to you with a fixed price, usually the same day. No call-out fee, no obligation.</p>
        <div class="hero-cta">
          <a href="mailto:{BIZ['email']}" class="btn-lg btn-ghost">{svg('mail')} Email us</a>
        </div>
        <div class="hero-strip">
          <div>{svg('check')}Free quotes</div>
          <div>{svg('check')}No call-out fee</div>
          <div>{svg('check')}Same-day phone answers</div>
        </div>
      </div>
      <div id="quote">{quote_form(heading='Request a free quote')}</div>
    </div>
  </div>
</section>

<div class="trustbar">
  <div class="wrap">
    <ul>
      <li>{svg('check')}Mon&ndash;Fri 7am&ndash;5pm, Sat 8am&ndash;2pm</li>
      <li>{svg('check')}Fixed prices, not hourly rates</li>
      <li>{svg('check')}18 suburbs across Frankston &amp; the Peninsula</li>
      <li>{svg('check')}Residential &amp; commercial</li>
    </ul>
  </div>
</div>

<main id="main">

<section class="sec">
  <div class="wrap">
    <div class="contact-grid">
      <div>
        <div class="sec-head" style="margin-bottom:26px">
          <span class="eyebrow">Our details</span>
          <h2>Based in Frankston VIC 3199</h2>
          <p class="lede">We are based in Frankston and work across the Frankston City suburbs and the Mornington Peninsula &mdash; from Seaford and Carrum Downs through to Mornington, Mount Martha and Tyabb.</p>
        </div>
        {nap_list()}
        <div class="callout" style="margin-top:28px">
          <p><strong>Got a deadline?</strong> End-of-lease inspections and pre-sale photography dates get priority. Tell us the date when you call and we will work backwards from it.</p>
        </div>
      </div>
      <div>{map_embed('Map of the Prestige Property Care area around Frankston VIC 3199')}</div>
    </div>
  </div>
</section>

<section class="sec sec-alt">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Where we work</span>
      <h2>Suburbs we cover</h2>
    </div>
    {areas_grid()}
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Common questions</span>
      <h2>Before you get in touch</h2>
    </div>
    {faq_block(CONTACT_FAQS)}
  </div>
</section>

</main>

{cta_band('Call and get a number today', 'Free fixed-price quotes on lawn mowing, gutters, hedges, gardens and clean-ups across Frankston and the Peninsula.')}"""


def build_pages():
    pages = []

    # Home
    pages.append({
        "path": "/",
        "file": "index.html",
        "active": "home",
        "title": "Lawn Mowing Frankston | Garden Care | Prestige Property Care",
        "desc": "Lawn mowing in Frankston from Prestige Property Care. Local lawn care, garden maintenance, hedge trimming and gutter cleaning across the Mornington Peninsula.",
        "body": page_home(), "lcp": "hero",
        "schema": [local_business_schema(), website_schema(),
                   faq_schema(HOME_FAQS), breadcrumb_schema([("Home", "/")])],
        "priority": "1.0",
    })

    # Services hub
    pages.append({
        "path": "/services/",
        "file": "services/index.html",
        "active": "services",
        "title": "Lawn Mowing Services Frankston | All Services | Prestige",
        "desc": "All Prestige Property Care lawn mowing services in Frankston: mowing, gutter cleaning, garden maintenance, hedge trimming, rubbish removal and garden clean-ups.",
        "body": page_services(), "lcp": "work-garden",
        "schema": [faq_schema(HUB_FAQS),
                   breadcrumb_schema([("Home", "/"), ("Services", "/services/")])],
        "priority": "0.9",
    })

    # Service pages
    for sp in SERVICE_PAGES:
        path = "/services/%s/" % sp["slug"]
        pages.append({
            "path": path,
            "file": "services/%s/index.html" % sp["slug"],
            "active": "services",
            "title": sp["title"],
            "desc": sp["desc"],
            "body": page_service(sp), "lcp": sp["slug"],
            "schema": [
                service_schema(strip_tags(sp["h1"]), sp["desc"], path,
                               strip_tags(sp["crumb"])),
                faq_schema(sp["faqs"]),
                breadcrumb_schema([("Home", "/"), ("Services", "/services/"),
                                   (strip_tags(sp["crumb"]), path)]),
            ],
            "priority": "0.8",
        })

    # About
    pages.append({
        "path": "/about/",
        "file": "about/index.html",
        "active": "about",
        "title": "About Prestige Property Care | Lawn &amp; Garden Care Frankston",
        "desc": "Prestige Property Care is a Frankston lawn and garden business run by Dave Coelho. Same crew every visit, fixed quotes, waste taken away. Serving 18 suburbs.",
        "body": page_about(), "lcp": "about-dave",
        "schema": [local_business_schema(),
                   faq_schema(ABOUT_FAQS),
                   breadcrumb_schema([("Home", "/"), ("About", "/about/")]),
                   about_page_schema()],
        "priority": "0.7",
    })

    # Contact
    pages.append({
        "path": "/contact/",
        "file": "contact/index.html",
        "active": "contact",
        "title": "Contact Prestige Property Care | Free Quote Frankston VIC",
        "desc": "Contact Prestige Property Care in Frankston for a free lawn mowing, gutter cleaning or garden clean-up quote. Call 0466 687 252 or send the quote form.",
        "body": page_contact(), "modal": False, "lcp": "work-lawn",
        "schema": [local_business_schema(),
                   faq_schema(CONTACT_FAQS),
                   breadcrumb_schema([("Home", "/"), ("Contact", "/contact/")]),
                   contact_page_schema()],
        "priority": "0.7",
    })

    return pages


def about_page_schema():
    return f"""{{
  "@context": "https://schema.org",
  "@type": "AboutPage",
  "url": "{SITE}/about/",
  "name": "About Prestige Property Care",
  "mainEntity": {{"@id": "{SITE}/#business"}}
}}"""


def contact_page_schema():
    return f"""{{
  "@context": "https://schema.org",
  "@type": "ContactPage",
  "url": "{SITE}/contact/",
  "name": "Contact Prestige Property Care",
  "mainEntity": {{"@id": "{SITE}/#business"}}
}}"""


def page_thanks():
    return f"""<section class="page-hero">
  <div class="hero-in">
    <span class="eyebrow">Request received</span>
    <h1>Thanks &mdash; we&rsquo;ve got your details</h1>
    <p class="hero-sub">Your quote request has come through to Prestige Property Care. {BIZ['owner']} will get back to you with a fixed price, usually the same day and always within one business day.</p>
    <div class="hero-cta">
      <a href="/" class="btn-lg btn-solid">Back to the homepage</a>
    </div>
  </div>
</section>

<div class="trustbar">
  <div class="wrap">
    <ul>
      <li>{svg('check')}Fixed price, not an hourly rate</li>
      <li>{svg('check')}No call-out fee</li>
      <li>{svg('check')}No obligation to book</li>
    </ul>
  </div>
</div>

<main id="main">

<section class="sec">
  <div class="wrap">
    <div class="split">
      <div class="prose">
        <span class="eyebrow">What happens next</span>
        <h2>Three steps from here</h2>
        <ol class="steps-list">
          <li><b>We read your notes.</b> If the job is clear from what you have written, we can often price it without coming out at all.</li>
          <li><b>We call or email you back.</b> Same day where we can, within one business day otherwise. If we need to see the property first, we will book a time that suits you.</li>
          <li><b>You get a fixed price.</b> Free, no obligation, and it does not change once the work starts.</li>
        </ol>
        <div class="callout">
          <p><strong>In a hurry?</strong> If you have an inspection date, a photography booking or a storm on the way, call {BIZ['phone_display']} rather than waiting on the email. We prioritise jobs with a hard deadline.</p>
        </div>
      </div>
      <div class="split-media">{picture('work-hedge', sizes=SPLIT_SIZES)}</div>
    </div>
  </div>
</section>

<section class="sec sec-alt">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">While you wait</span>
      <h2>Everything else we can do on the same visit</h2>
      <p class="lede">If we are already coming out, adding another job to the same visit rarely costs a second trip.</p>
    </div>
    {service_cards(limit=3)}
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="contact-grid">
      <div>
        <div class="sec-head" style="margin-bottom:26px">
          <span class="eyebrow">Our details</span>
          <h2>Prestige Property Care, Frankston</h2>
        </div>
        {nap_list()}
      </div>
      <div>{map_embed('Map of the Prestige Property Care area around Frankston VIC 3199')}</div>
    </div>
  </div>
</section>

</main>
"""


BANNER = ("<!-- Generated by tools/build.py — edit the content there, not here. "
          "Prestige Property Care, Frankston VIC. -->\n")


def render(page):
    has_modal = page.get("modal", True)
    # Every page used to open <main> partway down, leaving the hero, trust bar
    # and CTA band outside any landmark. Wrap the whole body once instead.
    body = page["body"].replace('<main id="main">', "").replace("</main>", "")
    body = '<main id="main">\n' + body + "\n</main>\n"
    out = [head(page), BANNER,
           site_header(page["active"], solid=page["path"] != "/", modal_cta=has_modal),
           body, site_footer(with_modal=has_modal)]
    doc = "".join(out)
    # schema goes just before </body>
    schema = "".join(jsonld(s) for s in page["schema"])
    doc = doc.replace('<script src="/assets/js/site.js" defer></script>',
                      schema + '<script src="/assets/js/site.js" defer></script>')
    return doc


def sitemap(pages):
    urls = []
    for p in pages:
        urls.append("""  <url>
    <loc>%s%s</loc>
    <lastmod>2026-08-19</lastmod>
    <changefreq>monthly</changefreq>
    <priority>%s</priority>
  </url>""" % (SITE, p["path"], p["priority"]))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n")


ROBOTS = """User-agent: *
Allow: /

# Answer engines and AI assistants are welcome — GEO/AEO is part of the strategy.
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: %s/sitemap.xml
""" % SITE


NOT_FOUND_BODY = """<section class="page-hero">
  <div class="hero-in">
    <span class="eyebrow">404</span>
    <h1>That page has been mown down</h1>
    <p class="hero-sub">The page you were after does not exist. Try the services below, or call us and we will point you in the right direction.</p>
    <div class="hero-cta">
      <a href="/" class="btn-lg btn-solid">Back to the homepage</a>
      <a href="/contact/" class="btn-lg btn-ghost">Contact us</a>
    </div>
  </div>
</section>
<main id="main">
<section class="sec">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Our services</span><h2>Where you were probably heading</h2></div>
    %s
  </div>
</section>
</main>""" % service_cards()


def minify_css(css):
    """Conservative CSS minification.

    Deliberately leaves spaces around + and - alone: this stylesheet uses
    calc(100% - var(--pos)) and calc(var(--header-h) + 24px), and stripping
    those spaces silently breaks both.
    """
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)      # comments
    css = re.sub(r"\s+", " ", css)                        # collapse whitespace
    css = re.sub(r"\s*([{};,])\s*", r"\1", css)           # around delimiters
    css = re.sub(r";\}", "}", css)                        # trailing semicolons
    css = re.sub(r"\s*:\s*", ":", css)                    # after property names
    return css.strip()


def build_css():
    src = os.path.join(ROOT, "assets", "css", "site.css")
    with open(src, encoding="utf-8") as fh:
        raw = fh.read()
    out = minify_css(raw)
    write("assets/css/site.min.css", out)
    return len(raw), len(out)


def write(rel_path, content):
    full = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)
    return rel_path


def main():
    raw, mini = build_css()
    print("css %d -> %d bytes (%d%% smaller)" % (raw, mini, 100 - mini * 100 // raw))
    pages = build_pages()
    written = []
    for p in pages:
        written.append(write(p["file"], render(p)))

    written.append(write("thank-you/index.html", render({
        "path": "/thank-you/", "active": "", "title": "Thank You | Prestige Property Care Frankston",
        "desc": "Thanks for your quote request. Prestige Property Care will come back to you with a fixed price, usually the same day and always within one business day.",
        "body": page_thanks(), "schema": [], "robots": "noindex, follow",
    })))

    written.append(write("404.html", render({
        "path": "/404.html", "active": "", "title": "Page not found | Prestige Property Care",
        "desc": "The page you were looking for does not exist. Browse Prestige Property Care lawn and garden services in Frankston, or get in touch for a free quote.",
        "body": NOT_FOUND_BODY, "schema": [], "robots": "noindex, follow",
    })))
    written.append(write("sitemap.xml", sitemap(pages)))
    written.append(write("robots.txt", ROBOTS))

    for w in written:
        print("wrote", w)
    print("\n%d files." % len(written))


if __name__ == "__main__":
    main()
