# Lindsey Channel — Art Sales Site

GitHub Pages site for original oil paintings by Lindsey Channel.

## To add a painting

1. Drop the JPG into the `/paintings/` folder
2. Open `index.html` in any text editor
3. Find the section marked **EDIT YOUR PAINTINGS HERE** near the top of the `<script>` block
4. Copy an existing painting block and change the title, price, image filename, and description
5. Save and push to GitHub

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
