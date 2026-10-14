# MP · New Songs

The advertising page for new music from **McLearn Media LLC** — artist **MP**,
written by Michael Shun McLaurin. Kept separate from the McLearn Media website
on purpose: this page is for promotion, programmers and music supervisors.

| File | What it is |
|---|---|
| `index.html` | the ad page — release dates, 45-second snippets, contact |
| `mp/index.html` | the MP fan page — songs, news, email sign-up, fan wall |
| `worker.js` | answers `/api/*` for the fan page (comments, news, sign-ups) |
| `wrangler.jsonc` | Cloudflare settings: site files + worker + storage |
| `.assetsignore` | files Cloudflare should not serve publicly |
| `legal.html` | privacy notice and terms of use |
| `audio/*.mp3` | twelve 45-second excerpts |
| `og-image.png` | preview image shown when the link is shared |
| `_headers` | security headers and cache rules |

## Deploying

No build step. Cloudflare deploys the `mclearn-songs` Worker from this repo
on every push to `main`, using `wrangler.jsonc`.

### Fan page storage (one time)
1. Cloudflare → **Storage & Databases → KV → Create** → name it `MP_FANS`.
2. Paste its ID into `wrangler.jsonc` under `kv_namespaces` (binding `FANS`).
3. Cloudflare → **Workers & Pages → mclearn-songs → Settings → Variables and Secrets**
   → add a **Secret** named `ADMIN_KEY` (the artist password, 12+ characters).

### Running the fan page
- Open `/mp/`, scroll to the bottom, tap **Artist sign-in**, enter the password.
- Signed in, you can post news, remove any post (tap **Remove** twice), and
  download the fan email list as a spreadsheet file.
- The password stays signed in only until the browser tab closes.
- Fans can't post links, and each visitor can post once a minute.

### Adding a new song
Put the 45-second clip in `audio/`, then add it to the top of the `SONGS`
list in `mp/index.html` and to `TRACKS` in `index.html`.

## Streaming links

In `index.html`, the block marked `TOO LOST SMART LINKS` has one slot per
song. Paste each release's `too.fm` link between the quotes. A song with a
link shows a "Listen everywhere" button.

---

McLearn Media LLC · Mclearn2025@gmail.com · 601-808-9559
