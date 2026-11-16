# Terminal 1 website

The marketing and project page for Terminal 1. A hand-written static site: HTML, CSS and vanilla JavaScript, with
no build step and no framework.

```
website/
  public/                 everything that gets published
    index.html            the page
    404.html              self-contained "not found" page (GitHub Pages serves it for any missing path)
    assets/css/site.css   all styles
    assets/js/site.js     all behaviour (terminal demo, scroll effects, 3D model loader)
    assets/images/        concept renders (WebP + JPEG), og-image, favicon
    assets/models/        terminal-1.glb goes here once it is exported from Onshape
```

## Run locally

From the repository root:

```sh
python3 -m http.server -d website/public 8000
```

Then open <http://localhost:8000>. Use a server rather than opening the file directly: the 3D model check uses
`fetch`, which does not work from `file://` (the page falls back to the poster image).

## Things to know before editing

- **Repository URL.** It lives in one place: `REPO_URL` at the top of `assets/js/site.js`. Every link marked
  `data-repo="…"` in the HTML is built from it (the attribute value is the path appended to the URL). Without
  JavaScript those links fall back to the in-page "Open source" section.
- **Site URL.** `canonical`, `og:url` and `og:image` in `index.html` assume
  `https://mmuhlariholdings.github.io/terminal-1/`. Change them if the repo name or a custom domain changes.
- **Honesty rules.** Nothing is built yet. Every figure is an estimate or target, renders are labelled "Concept
  render", and the "Vibe coded" section and footer line stay. Update numbers from `system/plan/interfaces.md`, which
  is the project's single source of truth.
- **Motion.** All scroll and typing effects switch off under `prefers-reduced-motion`; the page must read fully
  without them. Check both.

## The 3D model

The "Turn it over" section uses Google's `<model-viewer>` **3.5.0** (pinned, loaded from jsDelivr only when a model
exists). To publish the model:

1. In Onshape, export the assembly as **glTF binary (.glb)**. Keep it small (aim for under 5 MB: simplify fillets
   and hide fasteners if needed).
2. Save it as `website/public/assets/models/terminal-1.glb`.
3. Optional: if the export includes an animation whose name contains `explode` or `layer`, an **Exploded view**
   button appears automatically.

Until the file exists, the section shows the concept render with a "3D model coming with the first CAD export"
note. Do not commit test models.

## Images

Source renders live in `docs/media/concept-renders/`. Variants were made with `sips` and `cwebp`, for example:

```sh
sips -s format jpeg -s formatOptions 78 --resampleWidth 896 docs/media/concept-renders/carbon-back.jpg \
  --out website/public/assets/images/carbon-back-896.jpg
cwebp -q 76 website/public/assets/images/carbon-back-896.jpg -o website/public/assets/images/carbon-back-896.webp
```

`keyboard-detail-520.*` is a crop of `annotated-desk.jpg` that avoids its baked-in labels. `og-image.jpg`
(1200 × 630) and `apple-touch-icon.png` were rendered from HTML with headless Chrome.

## Deploy

`.github/workflows/website.yml` publishes `website/public` to **GitHub Pages** on every push to `main` that touches
`website/**` (or by running the workflow by hand). One-time setup in the repository: **Settings → Pages → Build and
deployment → Source: GitHub Actions**.

## Licence

Website code is MIT; text and images are CC BY-SA 4.0, like the rest of the project's documentation.
