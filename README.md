# MP · New Songs

The advertising page for new music from **McLearn Media LLC** — artist **MP**,
written by Michael Shun McLaurin. Kept separate from the McLearn Media website
on purpose: this page is for promotion, programmers and music supervisors.

| File | What it is |
|---|---|
| `index.html` | the ad page — release dates, 45-second snippets, contact |
| `legal.html` | privacy notice and terms of use |
| `audio/*.mp3` | twelve 45-second excerpts |
| `og-image.png` | preview image shown when the link is shared |
| `_headers` | security headers and cache rules |

## Deploying

Static files, no build step. On Cloudflare Pages, create a **new** project
connected to this repository (separate from the website's project):
framework preset **None**, build command empty, output directory `/`.

## Streaming links

In `index.html`, the block marked `TOO LOST SMART LINKS` has one slot per
song. Paste each release's `too.fm` link between the quotes. A song with a
link shows a "Listen everywhere" button.

---

McLearn Media LLC · Mclearn2025@gmail.com · 601-808-9559
