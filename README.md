# Sky View Real Estate — Foreal-layout rebuild

A static rebuild of the [Foreal](https://foreal.framer.website/) real-estate template layout,
populated entirely with **Sky View Real Estate Brokers** content and imagery from
`skyviewdubai.com`. 24 pages, no framework, no runtime build step.

## Run it

```bash
python3 -m http.server 4477 --directory skyview-site
```

## Rebuild after editing content

All copy, listings, team and config live in `build.py`. Edit it, then:

```bash
python3 build.py
```

That regenerates every `.html` file. **Do not hand-edit the generated HTML** — your changes will
be overwritten on the next build. Edit `build.py`, `styles.css`, `script.js` or `data/reviews.json`.

## Files

```
skyview-site/
├── build.py            all content + config; regenerates the site
├── data/reviews.json   testimonials (see "Reviews" below)
├── styles.css          design tokens + every component
├── script.js           reveal, filters, search, counters, carousel, video, forms
├── assets/             27 images (5.4 MB, resized to ≤1600px)
└── *.html              24 generated pages
```

## Pages

| | |
|---|---|
| `index.html` | Home — full Foreal section sequence |
| `listings.html` | All properties with live search, filter and sort |
| `property/<slug>.html` | 6 property detail pages |
| `services.html` | 6 services with full client copy |
| `about.html` | Company story, CEO message, credentials |
| `team.html` | 9 leadership cards + full 65-person roster |
| `blog.html` + `blog/<slug>.html` | Index + 6 posts |
| `contact.html` | Both offices, all contact routes, full FAQ |
| `careers.html` | Culture copy + 5 real vacancies |
| `privacy.html` / `terms.html` | Legal templates — **need legal review** |
| `thank-you.html` / `404.html` | Form success + error |

## Design tokens (lifted from the reference)

| Token | Value |
|---|---|
| `--ink` | `#16232B` |
| `--muted` | `#4F5F69` |
| `--bg` | `#F8F8F8` |
| `--cream` / `--cream-ink` | `#FFEBC6` / `#7E4B3A` |
| `--r-card` / `--r-img` / `--r-btn` | `20px` / `14px` / `10px` |

**Fonts** — Inter Tight (headings, 400/500, `-0.04em`), Instrument Serif (italic accent),
Inter (UI labels), Host Grotesk (wordmark).

## What's wired up

**Forms** — `#leadForm` and `#newsForm` validate, then:
- With `form_endpoint` set in `build.py`: POST JSON to that endpoint, redirect to `thank-you.html`
  on success, and fall back to WhatsApp with an error message if the request fails.
- With `form_endpoint` empty (current default): open a pre-filled WhatsApp message to the
  client's business number. **The form is functional today** — it just routes to WhatsApp
  rather than a database.

Set `form_endpoint` to a Formspree/Getform/own-API URL and rebuild to collect submissions.

**Showreel** — click-to-load facade for the client's own YouTube video
(`Why Pay Rent When You Can Own`, from their channel). No YouTube script or cookie loads until
the visitor presses play; the embed uses `youtube-nocookie.com`.

**Listings search** — purpose, property type, beds, keyword, and four sort orders, all client-side.
Deep links work: `listings.html?purpose=rent`, `?kind=villa`.

**Analytics** — GA4 (`G-VFL778XHQY`) and GTM (`GTM-WL937D6C`) are implemented but
**disabled by default** via `analytics_enabled = False`. These are the client's *live* property
IDs; firing demo or staging traffic into them corrupts their real reporting. Flip to `True` only
on the production deploy.

## Reviews — read this before launch

`data/reviews.json` contains **placeholder content, and it is visibly marked as such** on the page.
No real person is named and no review is invented: attributions read "Verified buyer" with a
monogram instead of a face, and each quote begins "Placeholder — replace with…".

Sky View has 200+ real Google reviews. Replace each entry with a genuine one, keeping the same
field names. The carousel picks them up automatically. If you empty the array, the entire section
removes itself rather than showing filler.

I did not write plausible-looking testimonials attributed to invented people — fabricated reviews
are the kind of thing that causes real problems if they ship by accident.

## Still outstanding

1. **Legal pages need review.** `privacy.html` and `terms.html` are reasonable template wording
   with a visible note saying so. The client's counsel should approve them.
2. **Founding year.** Set to **2005** throughout (used on most of the client's pages). Their
   homepage sidebar says 2006. Confirm which is right — it's flagged in `build.py`.
3. **Only 6 listings.** The live site has ~1,580. Real deployment needs a CMS or a feed from their
   `skyview-cpanel`; `LISTINGS` in `build.py` is the shape to populate.
4. **Blog posts are shortened.** Titles, dates and openings are the client's; full bodies were
   truncated on the source site, so each post carries 2–3 paragraphs. Paste in the full text.
5. **No sitemap/robots.** Add on deploy once the domain is known.

## Verification performed

- 852 internal links resolve; 0 broken. (The 404 page's root-absolute links are intentional.)
- Every `<img>` has `alt`; every page has exactly one `<h1>`, a title, meta description and `lang`.
- 0 unlabelled form fields, 0 unlabelled icon-only controls.
- 0 unsized inline SVGs — an SVG without `width`/`height` falls back to 300×150 and wrecks layout;
  this bit the first build and is now enforced at the `icon()` helper.
- No horizontal overflow at 375px on all 14 page types; also checked at 1440/1080/860.
- Filters, keyword search, empty state, clear, and all four sorts verified.
- Stat counters render their true value in HTML and animate from 0, so a throttled
  `requestAnimationFrame` or disabled JS still shows the right figure rather than "0".
- `prefers-reduced-motion` disables reveals, counters and smooth scrolling.
- FAQ uses native `<details>`; reviews use native scroll-snap — both work without JS.

## Deploying to Vercel

This is a plain static site — no build command, no framework.

1. **Import** the repo at [vercel.com/new](https://vercel.com/new).
2. When Vercel asks for framework settings:
   - Framework Preset: **Other**
   - Build Command: *leave empty*
   - Output Directory: *leave empty* (the site is at the repo root)
   - Install Command: *leave empty*
3. Deploy.

`vercel.json` sets long-lived caching on `/assets/*`, short caching on CSS/JS, and basic security
headers. `404.html` is served automatically for unknown paths.

**Before the production deploy**, in `build.py`:
- set `analytics_enabled = True` (only for the real production domain — the GA4/GTM IDs are the
  client's live properties)
- set `form_endpoint` to a real endpoint if you want submissions stored rather than sent to WhatsApp

then run `python3 build.py` and commit the regenerated HTML.

Links use explicit `.html` extensions so the site works identically on Vercel and via
`python3 -m http.server` locally. If you'd prefer extensionless URLs, add `"cleanUrls": true` to
`vercel.json` — Vercel will redirect `/about.html` to `/about`.
