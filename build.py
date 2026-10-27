#!/usr/bin/env python3
"""Build the Lindsey Channel site from catalog.csv.

    python3 build.py

catalog.csv is the one place paintings live. Edit it in Google Sheets or Excel
(File > Download > CSV), drop it here, run this, commit, push.

It writes:
  index.html            the gallery data between // CATALOG:START and // CATALOG:END,
                        and a noindex tag while the catalog is empty
  paintings/<slug>.html one page per painting (what Google finds)
  sitemap.xml, robots.txt

Columns (header row required; only title is mandatory):
  title, year, type (original|print), status (available|sold|collection|nfs),
  medium, dimensions, price, print_kind, description, image, slug
image defaults to paintings/<slug>.jpg; slug defaults to the title, lowercased.
"""
import csv, html, json, os, re, sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
ARTIST = "Lindsey Channel"
EMAIL = "channeloutfitters1@gmail.com"   # keep in sync with site.email in index.html
PHONE, PHONE_LINK = "406-261-2772", "+14062612772"
STATUSES = {"available", "sold", "collection", "nfs"}


def base_url():
    cname = open(os.path.join(ROOT, "CNAME")).read().strip() if os.path.exists(os.path.join(ROOT, "CNAME")) else ""
    return f"https://{cname}" if cname else "https://jordansawceswagger.github.io/lindsey-channel-art"


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def load():
    path = os.path.join(ROOT, "catalog.csv")
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for n, r in enumerate(csv.DictReader(f), start=2):
            r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
            if not r.get("title"):
                continue
            r["slug"] = r.get("slug") or slugify(r["title"])
            r["type"] = (r.get("type") or "original").lower()
            r["status"] = (r.get("status") or "available").lower()
            if r["type"] not in {"original", "print"}:
                sys.exit(f"catalog.csv line {n}: type must be original or print, got {r['type']!r}")
            if r["status"] not in STATUSES:
                sys.exit(f"catalog.csv line {n}: status must be one of {sorted(STATUSES)}, got {r['status']!r}")
            r["image"] = r.get("image") or f"paintings/{r['slug']}.jpg"
            rows.append(r)
    slugs = [r["slug"] for r in rows]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        sys.exit(f"catalog.csv: duplicate slugs {sorted(dupes)}; give one of them its own slug column value")
    # available first, then newest first
    rows.sort(key=lambda r: (r["status"] != "available", -(int(r["year"]) if r.get("year", "").isdigit() else 0)))
    for i, r in enumerate(rows, start=1):
        r["id"] = i
    return rows


def js_entry(r):
    keys = ["id", "slug", "title", "year", "type", "status", "medium", "dimensions", "price", "image", "description"]
    d = {k: r.get(k, "") for k in keys}
    d["printKind"] = r.get("print_kind", "")
    return d


def write_index(rows):
    p = os.path.join(ROOT, "index.html")
    s = open(p, encoding="utf-8").read()
    data = json.dumps([js_entry(r) for r in rows], indent=2, ensure_ascii=False).replace("</", "<\\/")
    s = re.sub(r"// CATALOG:START\n.*?// CATALOG:END", lambda m: f"// CATALOG:START\nconst paintings = {data};\n// CATALOG:END", s, flags=re.S)
    robots = "" if rows else '<meta name="robots" content="noindex" />'
    s = re.sub(r"<!-- ROBOTS:START -->.*?<!-- ROBOTS:END -->", lambda m: f"<!-- ROBOTS:START -->{robots}<!-- ROBOTS:END -->", s, flags=re.S)
    canon = f'<link rel="canonical" href="{base_url()}/" />'
    s = re.sub(r'<link rel="canonical"[^>]*>\n?', "", s)
    s = s.replace("<!-- ROBOTS:END -->", "<!-- ROBOTS:END -->\n" + canon, 1)
    open(p, "w", encoding="utf-8").write(s)


def price_number(price):
    m = re.search(r"[\d,]+(?:\.\d+)?", price or "")
    return m.group(0).replace(",", "") if m else ""


def painting_page(r):
    e = lambda k: html.escape(r.get(k, ""))
    url = f"{base_url()}/paintings/{r['slug']}.html"
    img_url = f"{base_url()}/{r['image']}"
    status_label = {"sold": "Sold", "collection": "Private collection", "nfs": "Not for sale"}.get(r["status"], "")
    kind = status_label or (r.get("print_kind") or "Print" if r["type"] == "print" else "Original oil painting")
    available = r["status"] == "available"
    meta_line = " · ".join(x for x in [r.get("year", ""), r.get("medium", ""), r.get("dimensions", "")] if x)
    desc = r.get("description") or f"{r['title']}, {kind.lower()} by {ARTIST}" + (f", {r['year']}" if r.get("year") else "") + "."
    schema = {
        "@context": "https://schema.org", "@type": "VisualArtwork",
        "name": r["title"], "url": url, "image": img_url,
        "creator": {"@type": "Person", "name": ARTIST},
        "artform": "Painting" if r["type"] == "original" else "Print",
    }
    if r.get("year"): schema["dateCreated"] = r["year"]
    if r.get("medium"): schema["artMedium"] = r["medium"]
    if r.get("description"): schema["description"] = r["description"]
    if available and price_number(r.get("price")):
        schema["offers"] = {"@type": "Offer", "price": price_number(r["price"]), "priceCurrency": "USD",
                            "availability": "https://schema.org/InStock", "url": url}
    buy_subject = f"Purchase Inquiry: {r['title']}" if available else f"Prints of {r['title']}"
    buy_label = "Request purchase" if available else "Ask about prints"
    mail = lambda subj: f"mailto:{EMAIL}?subject={html.escape(subj.replace(' ', '%20'))}"
    title_tag = f"{r['title']} — {ARTIST}" + (f", {r['year']}" if r.get("year") else "")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{html.escape(title_tag)}</title>
<meta name="description" content="{html.escape(desc)}" />
<link rel="canonical" href="{url}" />
<meta property="og:type" content="article" />
<meta property="og:title" content="{html.escape(title_tag)}" />
<meta property="og:description" content="{html.escape(desc)}" />
<meta property="og:image" content="{img_url}" />
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;1,400&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#100c08;color:#d4b896;font-family:'Lora',Georgia,serif;font-size:17px;line-height:1.7}}
  a{{color:inherit}}
  .wrap{{max-width:1100px;margin:0 auto;padding:32px 16px 64px}}
  .back{{font-size:12px;letter-spacing:.18em;text-transform:uppercase;text-decoration:none;opacity:.75}}
  .grid{{display:grid;grid-template-columns:1fr;gap:32px;margin-top:28px}}
  @media(min-width:860px){{.grid{{grid-template-columns:3fr 2fr;gap:56px}}}}
  img{{display:block;width:100%;height:auto;box-shadow:0 12px 40px rgba(0,0,0,.45)}}
  .ph{{aspect-ratio:4/5;background:linear-gradient(160deg,#5c4423,#1a1208)}}
  h1{{font-family:'Playfair Display',serif;font-weight:400;font-size:clamp(30px,5vw,44px);line-height:1.15;color:#ecdcc4}}
  .meta{{color:#8a9a78;font-size:14px;margin-top:10px}}
  .kind{{text-transform:uppercase;letter-spacing:.18em;font-size:11px;margin-top:14px}}
  .price{{font-size:22px;color:#ecdcc4;margin-top:14px}}
  .desc{{margin-top:18px}}
  .btns{{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px}}
  .btn{{display:inline-block;padding:12px 20px;border:1px solid #d4b896;text-decoration:none;font-size:13px;letter-spacing:.12em;text-transform:uppercase}}
  .btn.primary{{background:#d4b896;color:#100c08}}
  footer{{margin-top:56px;font-size:13px;opacity:.7}}
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="../index.html#gallery">&larr; The collection</a>
  <div class="grid">
    <div><img src="../{e('image')}" alt="{html.escape(', '.join(x for x in [r['title'], 'by ' + ARTIST, r.get('medium','').lower(), r.get('year','')] if x))}" onerror="this.replaceWith(Object.assign(document.createElement('div'),{{className:'ph'}}))" /></div>
    <div>
      <h1>{e('title')}</h1>
      <div class="meta">{html.escape(meta_line)}</div>
      <div class="kind">{html.escape(kind)}</div>
      {f'<div class="price">{e("price")}</div>' if available and r.get("price") else ""}
      {f'<p class="desc">{e("description")}</p>' if r.get("description") else ""}
      <div class="btns">
        <a class="btn primary" href="{mail(buy_subject)}">{buy_label}</a>
        <a class="btn" href="{mail('Commission Inquiry')}">Request commission</a>
        <a class="btn" href="tel:{PHONE_LINK}">Call {PHONE}</a>
      </div>
    </div>
  </div>
  <footer>&copy; {date.today().year} {ARTIST}. Bigfork, Montana. Reproduction prohibited without written consent.</footer>
</div>
</body>
</html>
"""


def write_pages(rows):
    d = os.path.join(ROOT, "paintings")
    os.makedirs(d, exist_ok=True)
    keep = {f"{r['slug']}.html" for r in rows}
    for f in os.listdir(d):  # drop pages for paintings removed from the catalog
        if f.endswith(".html") and f not in keep:
            os.remove(os.path.join(d, f))
    for r in rows:
        open(os.path.join(d, f"{r['slug']}.html"), "w", encoding="utf-8").write(painting_page(r))


def write_sitemap(rows):
    today = date.today().isoformat()
    urls = [f"{base_url()}/"] + [f"{base_url()}/paintings/{r['slug']}.html" for r in rows]
    body = "\n".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n')
    open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {base_url()}/sitemap.xml\n")


if __name__ == "__main__":
    rows = load()
    write_index(rows)
    write_pages(rows)
    write_sitemap(rows)
    print(f"{len(rows)} paintings · {sum(r['status']=='available' for r in rows)} available · "
          f"{'noindex ON (catalog empty)' if not rows else 'indexable'} · base {base_url()}")
