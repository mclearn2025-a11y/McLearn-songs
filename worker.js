/* MP fan page — comments, updates and email sign-ups.
   Everything else on the site is served as plain files by Cloudflare.
   Storage: one Workers KV namespace bound as FANS.
   Artist password: the ADMIN_KEY secret, set in the Cloudflare dashboard. */

const LIMITS = {
  name: 40,          // characters
  comment: 500,
  updateTitle: 80,
  updateBody: 600,
  wallSize: 60,      // newest comments shown
  updatesShown: 12,
  cooldown: 60,      // seconds between posts from one visitor (KV minimum is 60)
};

/* Fan vote: "What should MP share next?"
   To start a new vote, give it a new id (old votes stay stored under the old id) and new choices.
   Each phone or computer gets one vote and can change it. */
const POLL = {
  id: "next-1",
  question: "What should MP share next?",
  choices: [
    { k: "story",   t: "The story behind “Who Got Your Back”" },
    { k: "version", t: "A new version of a fan favorite" },
    { k: "preview", t: "A first listen to the next new song" },
  ],
};
const DEVICE = /^[a-z0-9-]{16,40}$/;

// Newest first: KV lists keys in ascending order, so store an inverted timestamp.
const sortKey = (ts) => String(9999999999999 - ts).padStart(13, "0");
const rid = () => crypto.randomUUID().slice(0, 8);

const json = (data, status = 200, extra = {}) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra },
  });
const fail = (status, message) => json({ error: message }, status);

function clean(s, max) {
  return String(s ?? "")
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F​-‏‪-‮⁦-⁩]/g, "")
    .replace(/\r\n?/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
    .slice(0, max);
}

const LINKY = /(https?:\/\/|www\.|\b[a-z0-9-]+\.(com|net|org|io|xyz|ru|info|biz|top|link|click|shop|site|online|co)\b)/i;

async function sha256(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

// Constant-time comparison of the admin key.
async function isAdmin(request, env) {
  const given = request.headers.get("x-admin-key") || "";
  if (!env.ADMIN_KEY || env.ADMIN_KEY.length < 8 || !given) return false;
  const [a, b] = await Promise.all([sha256(given), sha256(env.ADMIN_KEY)]);
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function readBody(request) {
  const type = request.headers.get("content-type") || "";
  if (!type.includes("application/json")) return null;
  const len = Number(request.headers.get("content-length") || 0);
  if (len > 8000) return null;
  try { return await request.json(); } catch { return null; }
}

// Only accept writes sent from this site's own pages.
function sameOrigin(request) {
  const origin = request.headers.get("origin");
  return !origin || origin === new URL(request.url).origin;
}

async function listNewest(env, prefix, limit) {
  const { keys } = await env.FANS.list({ prefix, limit });
  return keys.filter((k) => k.metadata).map((k) => ({ id: k.name.slice(prefix.length), ...k.metadata }));
}

async function cooldown(env, request, bucket) {
  const ip = request.headers.get("cf-connecting-ip") || "unknown";
  const key = `rl:${bucket}:${(await sha256("mp-fans:" + ip)).slice(0, 24)}`;
  if (await env.FANS.get(key)) return true;
  await env.FANS.put(key, "1", { expirationTtl: LIMITS.cooldown });
  return false;
}

// The device id is scrambled before it's stored, so the stored key can't be traced back to a browser.
const voteKey = async (device) => `v:${POLL.id}:${(await sha256("mp-vote:" + device)).slice(0, 32)}`;

async function pollState(env, device, justVoted) {
  const counts = Object.fromEntries(POLL.choices.map((c) => [c.k, 0]));
  const myKey = device ? await voteKey(device) : "";
  let cursor, pages = 0, listed = null;
  do {
    const page = await env.FANS.list({ prefix: `v:${POLL.id}:`, cursor });
    for (const k of page.keys) {
      if (!k.metadata || !(k.metadata.c in counts)) continue;
      counts[k.metadata.c]++;
      if (k.name === myKey) listed = k.metadata.c;
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor && ++pages < 25);
  // KV lists can lag a few seconds behind a write. Make a fresh or changed vote show in its own result.
  if (justVoted && listed !== justVoted) {
    if (listed) counts[listed]--;
    counts[justVoted]++;
  }
  const mine = justVoted || (myKey ? await env.FANS.get(myKey) : null);
  return {
    id: POLL.id, question: POLL.question, mine,
    total: Object.values(counts).reduce((a, b) => a + b, 0),
    choices: POLL.choices.map((c) => ({ ...c, n: counts[c.k] })),
  };
}

async function handle(request, env) {
  const url = new URL(request.url);
  const path = url.pathname.replace(/\/+$/, "");
  const method = request.method;

  if (!env.FANS) return fail(503, "Comments are not switched on yet.");
  if (method !== "GET" && !sameOrigin(request)) return fail(403, "Not allowed.");

  // --- read the wall --------------------------------------------------------
  if (path === "/api/wall" && method === "GET") {
    const [comments, updates] = await Promise.all([
      listNewest(env, "c:", LIMITS.wallSize),
      listNewest(env, "u:", LIMITS.updatesShown),
    ]);
    return json({ comments, updates });
  }

  // --- post a comment -------------------------------------------------------
  if (path === "/api/comments" && method === "POST") {
    const body = await readBody(request);
    if (!body) return fail(400, "Something went wrong sending that. Try again.");
    if (body.website) return json({ ok: true }); // hidden field only bots fill in
    const name = clean(body.name, LIMITS.name) || "A fan";
    const text = clean(body.text, LIMITS.comment);
    if (text.length < 2) return fail(400, "Write a little more before posting.");
    if (LINKY.test(text) || LINKY.test(name)) return fail(400, "Links can't be posted on the wall. Take the link out and try again.");
    if (await cooldown(env, request, "c")) return fail(429, "You just posted. Give it a minute, then post again.");
    const ts = Date.now();
    const id = `${sortKey(ts)}-${rid()}`;
    const meta = { name, text, ts };
    await env.FANS.put(`c:${id}`, "", { metadata: meta });
    return json({ ok: true, comment: { id, ...meta } }, 201);
  }

  // --- fan vote --------------------------------------------------------------
  if (path === "/api/poll" && method === "GET") {
    const device = (url.searchParams.get("d") || "").toLowerCase();
    return json(await pollState(env, DEVICE.test(device) ? device : ""));
  }
  if (path === "/api/vote" && method === "POST") {
    const body = await readBody(request);
    if (!body) return fail(400, "Something went wrong. Try again.");
    const device = String(body.device || "").toLowerCase();
    const choice = String(body.choice || "");
    if (body.poll !== POLL.id) return fail(409, "This vote has closed. Refresh the page to see the new one.");
    if (!DEVICE.test(device) || !POLL.choices.some((c) => c.k === choice)) return fail(400, "Something went wrong. Try again.");
    const key = await voteKey(device);
    const had = await env.FANS.get(key);
    // A new vote is limited to one a minute from the same connection; changing a vote is not.
    if (had === null && (await cooldown(env, request, "v"))) return fail(429, "A vote just came from this connection. Give it a minute.");
    await env.FANS.put(key, choice, { metadata: { c: choice, ts: Date.now() } });
    return json(await pollState(env, device, choice), 201);
  }

  // --- email sign-up --------------------------------------------------------
  if (path === "/api/subscribe" && method === "POST") {
    const body = await readBody(request);
    if (!body) return fail(400, "Something went wrong. Try again.");
    if (body.website) return json({ ok: true });
    const email = clean(body.email, 120).toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return fail(400, "That email address doesn't look right. Check it and try again.");
    if (await cooldown(env, request, "s")) return fail(429, "Give it a minute, then try again.");
    // Where they signed up: "music" (the MP fan page) or "books" (the Reading Room).
    // "music" (fan page), "books" (Reading Room) or "books-<channel>" from a tracking link like /books/?from=tiktok
    const src = /^books(-[a-z0-9-]{1,20})?$/.test(String(body.src || "")) ? String(body.src) : "music";
    const prev = await env.FANS.getWithMetadata(`e:${email}`);
    const had = prev?.metadata?.src ? String(prev.metadata.src).split("+") : [];
    const from = had.includes(src) ? had : [...had, src];
    await env.FANS.put(`e:${email}`, "", { metadata: { ts: prev?.metadata?.ts || Date.now(), src: from.join("+") } });
    return json({ ok: true }, 201);
  }

  // --- leave the email list -------------------------------------------------
  if (path === "/api/unsubscribe" && method === "POST") {
    const body = await readBody(request);
    const email = clean(body?.email, 120).toLowerCase();
    if (email) await env.FANS.delete(`e:${email}`);
    return json({ ok: true }); // same answer either way: the list is never revealed
  }

  // --- artist only ----------------------------------------------------------
  if (path.startsWith("/api/admin")) {
    if (!env.ADMIN_KEY) return fail(503, "Set the ADMIN_KEY secret in Cloudflare first.");
    if (!(await isAdmin(request, env))) {
      await new Promise((r) => setTimeout(r, 400));
      return fail(401, "That password isn't right.");
    }

    if (path === "/api/admin/check" && method === "GET") return json({ ok: true });

    if (path === "/api/admin/updates" && method === "POST") {
      const body = await readBody(request);
      const title = clean(body?.title, LIMITS.updateTitle);
      const text = clean(body?.text, LIMITS.updateBody);
      if (!title && !text) return fail(400, "Write a title or a message.");
      const ts = Date.now();
      const id = `${sortKey(ts)}-${rid()}`;
      const meta = { title, text, ts };
      await env.FANS.put(`u:${id}`, "", { metadata: meta });
      return json({ ok: true, update: { id, ...meta } }, 201);
    }

    const del = path.match(/^\/api\/admin\/(comments|updates)\/([0-9]{13}-[0-9a-f]{8})$/);
    if (del && method === "DELETE") {
      await env.FANS.delete(`${del[1] === "comments" ? "c" : "u"}:${del[2]}`);
      return json({ ok: true });
    }

    if (path === "/api/admin/subscribers" && method === "GET") {
      const rows = [];
      let cursor;
      do {
        const page = await env.FANS.list({ prefix: "e:", cursor });
        for (const k of page.keys) {
          // Keep spreadsheet apps from treating an address as a formula.
          const email = k.name.slice(2).replace(/^[=+\-@]/, "'$&").replace(/[",\n]/g, "");
          rows.push([email, new Date(k.metadata?.ts || 0).toISOString(), k.metadata?.src || "music"]);
        }
        cursor = page.list_complete ? undefined : page.cursor;
      } while (cursor);
      const csv = "email,signed_up,signed_up_from\n" + rows.map((r) => r.join(",")).join("\n") + "\n";
      return new Response(csv, {
        headers: {
          "content-type": "text/csv; charset=utf-8",
          "content-disposition": 'attachment; filename="mp-fan-emails.csv"',
          "cache-control": "no-store",
        },
      });
    }
  }

  return fail(404, "Not found.");
}

/* Campaign links: the same fan page, with its own headline and picture for Facebook/X previews.
   Add a new entry here to start a fresh campaign without changing the page. */
const CAMPAIGNS = {
  "/new": {
    title: "New Music from McLearn Media · 12 Songs Out Now",
    description: "Tap to listen free: southern soul from MP, out of Brandon, Mississippi. 12 songs out now, featuring the new Who Got Your Back (Flow Mix, Remastered). Plus news and the fan wall.",
    image: "/mp/og-new.png",
    alt: "New music from McLearn Media: 12 songs from MP, out now, free to listen",
  },
  "/tiktok": {
    title: "MP · Hear the full songs from TikTok",
    description: "You heard it on TikTok. Play all 12 MP songs free, find the full songs on your music app, and get new music first.",
    image: "/mp/og-new.png",
    alt: "New music from McLearn Media: songs from MP, free to listen",
  },
};

async function campaignPage(request, env, path) {
  const c = CAMPAIGNS[path];
  const origin = new URL(request.url).origin;
  const page = await env.ASSETS.fetch(new Request(origin + "/mp/", request));
  const set = (attr) => ({ element(el) { el.setAttribute("content", attr); } });
  return new HTMLRewriter()
    .on("title", { element(el) { el.setInnerContent(c.title); } })
    .on('meta[name="description"]', set(c.description))
    .on('meta[property="og:title"]', set(c.title))
    .on('meta[property="og:description"]', set(c.description))
    .on('meta[property="og:url"]', set(origin + path))
    .on('meta[property="og:image"]', set(origin + c.image))
    .on('meta[property="og:image:alt"]', set(c.alt))
    .on('link[rel="canonical"]', { element(el) { el.setAttribute("href", origin + path); } })
    .transform(page);
}

// The fan page's preview tags are written with the workers.dev address. Swap in whatever
// address the visitor used, so a custom domain (e.g. mclearnmedia.com) works with no other change.
const BUILT_ON = "https://mclearn-songs.mclearn2025.workers.dev";
function localize(response, origin) {
  if (origin === BUILT_ON) return response;
  const fix = (attr) => ({ element(el) { const v = el.getAttribute(attr); if (v && v.startsWith(BUILT_ON)) el.setAttribute(attr, origin + v.slice(BUILT_ON.length)); } });
  return new HTMLRewriter().on("meta[content]", fix("content")).on("link[href]", fix("href")).transform(response);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const clean = url.pathname.replace(/\/+$/, "");
    if (CAMPAIGNS[clean] && request.method === "GET") return localize(await campaignPage(request, env, clean), url.origin);
    if (clean === "/mp" && request.method === "GET") return localize(await env.ASSETS.fetch(request), url.origin);
    if (url.pathname.startsWith("/api/")) {
      try { return await handle(request, env); }
      catch (err) { console.error(err); return fail(500, "Something went wrong on our end. Try again in a minute."); }
    }
    return env.ASSETS.fetch(request);
  },
};
