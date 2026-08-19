#!/usr/bin/env python3
"""
Greenline Services — build checks.

Run after tools/build.py. Exits non-zero if anything fails, so it can gate a
deploy.

    python3 tools/build.py && python3 tools/check.py
"""

import glob
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}

# name -> CRM field, per the GHL mapping
GHL_FIELDS = {"full_name", "email", "phone",
              "property_address", "service_needed", "job_notes"}
GHL_TRACKING_ID = "tk_9f5144f196b340e59b8396dd9921dc07"

# page -> the one keyword it is built to rank for
TARGETS = {
    'index.html': 'lawn mowing frankston',
    'services/index.html': 'lawn mowing services frankston',
    'services/gutter-cleaning/index.html': 'gutter cleaning frankston',
    'services/rubbish-removal/index.html': 'rubbish removal frankston',
    'services/garden-maintenance/index.html': 'gardener frankston',
    'services/lawn-mowing/index.html': 'lawn mowing mornington',
    'services/hedge-trimming/index.html': 'hedge trimming frankston',
    'services/garden-clean-ups/index.html': 'garden clean up frankston',
}

failures = []


def fail(where, msg):
    failures.append("%s: %s" % (where, msg))


class Nesting(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append('stray </%s>' % tag)
        elif self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append('unclosed <%s>' % self.stack.pop())
            self.stack.pop()
        else:
            self.errors.append('stray </%s>' % tag)


def visible_text(body):
    body = re.sub(r'<(script|style|iframe)[^>]*>.*?</\1>', ' ', body, flags=re.S | re.I)
    # The quote popup is hidden boilerplate repeated on every page — it is not
    # body copy, so it must not count towards or dilute keyword density.
    body = re.sub(r'<div class="modal" id="quote-modal" hidden>.*?\n</div>', ' ', body, flags=re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', body)))


def check_page(f):
    s = open(f, encoding='utf-8').read()

    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(block)
        except Exception as e:
            fail(f, 'invalid JSON-LD (%s)' % e)

    n_h1 = len(re.findall(r'<h1[ >]', s))
    if n_h1 != 1:
        fail(f, 'expected exactly one <h1>, found %d' % n_h1)

    n = Nesting()
    n.feed(re.sub(r'<script.*?</script>', '', s, flags=re.S))
    for e in n.errors[:5]:
        fail(f, e)
    if n.stack:
        fail(f, 'unclosed tags %s' % n.stack[:5])

    title = re.search(r'<title>(.*?)</title>', s, re.S)
    desc = re.search(r'<meta name="description" content="(.*?)">', s, re.S)
    if not title:
        fail(f, 'no <title>')
    elif not 30 <= len(html.unescape(title.group(1))) <= 62:
        fail(f, 'title is %d chars (want 30-62)' % len(html.unescape(title.group(1))))
    if not desc:
        fail(f, 'no meta description')
    elif not 120 <= len(html.unescape(desc.group(1))) <= 160:
        fail(f, 'description is %d chars (want 120-160)' % len(html.unescape(desc.group(1))))

    if '<link rel="canonical"' not in s:
        fail(f, 'no canonical')
    n_robots = len(re.findall(r'<meta name="robots"', s))
    if n_robots != 1:
        fail(f, 'expected 1 robots meta, found %d' % n_robots)

    for tag in re.findall(r'<img [^>]*>', s):
        if 'alt="' not in tag:
            fail(f, 'image without alt text')
            break

    ids = re.findall(r'\bid="([^"]+)"', s)
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        fail(f, 'duplicate ids %s' % sorted(dupes))

    if GHL_TRACKING_ID not in s:
        fail(f, 'GHL tracking script missing')
    elif GHL_TRACKING_ID not in s.split('</head>')[0]:
        fail(f, 'GHL tracking script is not in <head>')


def check_form(f):
    """The five GHL form-capture requirements that live in the markup."""
    s = open(f, encoding='utf-8').read()
    if 'quote-form' not in s:
        return
    forms = re.findall(r'<form class="quote-form".*?</form>', s, re.S)
    if not forms:
        fail(f, 'quote form markup not found')
        return
    for form in forms:
        check_one_form(f, form)


def check_one_form(f, form):
    names = re.findall(r'name="([^"]+)"', form)
    missing = GHL_FIELDS - set(names)
    extra = set(names) - GHL_FIELDS
    if missing:
        fail(f, 'form missing GHL fields %s' % sorted(missing))
    if extra:
        fail(f, 'form has unmapped fields %s' % sorted(extra))

    if not re.search(r'<input[^>]*type="email"[^>]*name="email"', form):
        fail(f, 'no <input type="email" name="email"> for contact matching')
    if not re.search(r'<input[^>]*type="tel"[^>]*name="phone"', form):
        fail(f, 'no <input type="tel" name="phone">')
    if '<button type="submit"' not in form and 'type="submit"' not in form:
        fail(f, 'no native submit button')
    if re.search(r'\bdisabled\b', form):
        fail(f, 'form has a disabled field — GHL skips those')
    if '<iframe' in form:
        fail(f, 'form is iframe-based, which GHL does not support')


def check_js():
    js = open('assets/js/site.js', encoding='utf-8').read()
    # A submit handler that preventDefaults would silently stop every lead.
    for m in re.finditer(r"addEventListener\(\s*['\"]submit['\"]", js):
        window = js[m.start():m.start() + 600]
        if 'preventDefault' in window:
            fail('assets/js/site.js',
                 'a submit handler calls preventDefault() — this blocks GHL capture')


def check_density():
    for f, kw in TARGETS.items():
        if not os.path.exists(f):
            fail(f, 'page missing')
            continue
        body = open(f, encoding='utf-8').read().split('<body>', 1)[1]
        text = re.sub(r'[^a-z ]+', ' ', visible_text(body).lower())
        words = len(text.split())
        parts = kw.split()
        joiner = r'\W+(?:in\s+|the\s+|and\s+|services\s+|across\s+)?'
        hits = len(re.findall(r'\b' + joiner.join(parts) + r'\b', text))
        density = hits * len(parts) / words * 100 if words else 0
        if not 1.25 <= density <= 1.75:
            fail(f, 'keyword "%s" density %.2f%% (want 1.3-1.5%%)' % (kw, density))


def check_links(files):
    paths = {'/' + (os.path.dirname(f) + '/' if os.path.dirname(f) else '') for f in files}
    paths.add('/404.html')
    for f in files:
        for href in re.findall(r'href="([^"]+)"', open(f, encoding='utf-8').read()):
            if href.startswith(('http', 'mailto:', 'tel:', '#')):
                continue
            target = href.split('#')[0]
            if href.startswith('/assets/'):
                if not os.path.exists(target.lstrip('/')):
                    fail(f, 'missing asset %s' % target)
            elif target and target not in paths:
                fail(f, 'broken internal link %s' % href)


def check_sitemap(files):
    sm = open('sitemap.xml', encoding='utf-8').read()
    if '/thank-you/' in sm:
        fail('sitemap.xml', 'thank-you page should not be in the sitemap')
    if '/404' in sm:
        fail('sitemap.xml', '404 page should not be in the sitemap')
    for f in files:
        if f.endswith('404.html'):
            continue
        s = open(f, encoding='utf-8').read()
        path = '/' + (os.path.dirname(f) + '/' if os.path.dirname(f) else '')
        noindex = 'noindex' in (re.search(r'<meta name="robots" content="([^"]*)"', s) or
                                type('', (), {'group': lambda *a: ''})()).group(1)
        listed = '<loc>https://greenlineservices.com.au%s</loc>' % path in sm
        if noindex and listed:
            fail(f, 'noindex page is listed in the sitemap')
        if not noindex and not listed:
            fail(f, 'indexable page is missing from the sitemap')


def main():
    files = sorted(glob.glob('**/*.html', recursive=True))
    if not files:
        print("no HTML found — run tools/build.py first")
        return 1
    for f in files:
        check_page(f)
        check_form(f)
    check_js()
    check_density()
    check_links(files)
    check_sitemap(files)

    print("checked %d pages" % len(files))
    if failures:
        print("\n%d problem(s):\n" % len(failures))
        for f in failures:
            print("  x", f)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
