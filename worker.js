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

  // --- email sign-up --------------------------------------------------------
  if (path === "/api/subscribe" && method === "POST") {
    const body = await readBody(request);
    if (!body) return fail(400, "Something went wrong. Try again.");
    if (body.website) return json({ ok: true });
    const email = clean(body.email, 120).toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return fail(400, "That email address doesn't look right. Check it and try again.");
    if (await cooldown(env, request, "s")) return fail(429, "Give it a minute, then try again.");
    await env.FANS.put(`e:${email}`, "", { metadata: { ts: Date.now() } });
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
          rows.push([email, new Date(k.metadata?.ts || 0).toISOString()]);
        }
        cursor = page.list_complete ? undefined : page.cursor;
      } while (cursor);
      const csv = "email,signed_up\n" + rows.map((r) => r.join(",")).join("\n") + "\n";
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) {
      try { return await handle(request, env); }
      catch (err) { console.error(err); return fail(500, "Something went wrong on our end. Try again in a minute."); }
    }
    return env.ASSETS.fetch(request);
  },
};
