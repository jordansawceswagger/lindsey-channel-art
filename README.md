# Lindsey Channel — Art Sales Site

GitHub Pages site for original oil paintings by Lindsey Channel.

## To add or change paintings

Paintings live in **`catalog.csv`**, one row per painting (see `_kit/catalog-how-to.md` for the columns).

1. Edit `catalog.csv` (or replace it with the CSV downloaded from the Google Sheet)
2. Put each photo in `/paintings/` named `<slug>.jpg` (slug = title lowercased, spaces → dashes)
3. Run `python3 build.py`. It fills the gallery, writes one page per painting in `/paintings/`, and rebuilds `sitemap.xml`
4. Commit and push

While `catalog.csv` is empty the site carries a `noindex` tag so Google doesn't index an empty gallery. It comes off automatically on the first build with real paintings.

## Kit for Lindsey, Holly and Steve
`_kit/` (not published; Jekyll skips underscore folders): catalog template + how-to, photo brief for Steve, interview guide for the about copy.

## To deploy

```bash
cd lindsey-channel-art
git init
git add .
git commit -m "Initial build — Lindsey Channel art sales site"
git branch -M main
git remote add origin https://github.com/[USERNAME]/lindsey-channel-art.git
git push -u origin main
```

Then in GitHub: **Settings → Pages → Source: Deploy from branch → Branch: main → / (root) → Save.**

## Custom domain

Leave the `CNAME` file blank until you're ready to point a domain at it. Then add the bare domain (e.g. `lindseychannel.art`) on a single line and configure DNS at the registrar.
