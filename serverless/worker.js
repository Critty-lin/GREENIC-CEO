/*
 * 可选的无服务器战绩服务（Cloudflare Workers + KV）。
 *
 * 作用：GitHub Pages 只能托管静态文件，无法接收对局数据。把这个 Worker
 * 部署到 Cloudflare，再把 config.js 里的 ADVN_API 指向它，首页的「授勋」
 * 和 review.html 就能正常读写。
 *
 * API 与 server.py 完全一致：
 *   GET  /api/runs
 *   GET  /api/honor?score=N
 *   POST /api/runs
 */

const MAX_ROWS = 2000;
const MAX_BODY = 8192;

function cors(env) {
  return {
    "Access-Control-Allow-Origin": env.ALLOW_ORIGIN || "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
  };
}

function json(obj, status, env) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: Object.assign(
      {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
      },
      cors(env)
    ),
  });
}

async function loadRows(env) {
  const raw = await env.RUNS.get("runs", "json");
  return Array.isArray(raw) ? raw : [];
}

function toInt(value, fallback) {
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) ? n : fallback;
}

function toFloat(value, fallback) {
  const n = Number.parseFloat(value);
  return Number.isFinite(n) ? n : fallback;
}

async function handleHonor(url, env) {
  const score = toInt(url.searchParams.get("score"), 0);
  const best = new Map();
  for (const row of await loadRows(env)) {
    const device = String(row.device || "unknown").slice(0, 40);
    const value = toInt(row.score, 0);
    if (!best.has(device) || value > best.get(device)) best.set(device, value);
  }
  const total = best.size;
  if (total <= 1) {
    return json({ total, beat: 0, pct: 100, first: true }, 200, env);
  }
  let worse = 0;
  for (const value of best.values()) if (value < score) worse += 1;
  const pct = Math.max(0, Math.min(100, Math.round((100 * worse) / total)));
  return json({ total, beat: worse, pct, first: false }, 200, env);
}

async function handlePost(request, env) {
  const raw = await request.text();
  if (raw.length > MAX_BODY) {
    return json({ error: "too large" }, 413, env);
  }
  let body;
  try {
    body = JSON.parse(raw || "{}");
  } catch (_) {
    return json({ error: "bad json" }, 400, env);
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return json({ error: "bad body" }, 400, env);
  }

  const row = {
    score: toInt(body.score, 0),
    ending: String(body.ending || "").slice(0, 40),
    endingId: String(body.endingId || "").slice(0, 24),
    trust: Math.max(0, Math.min(100, toInt(body.trust, 0))),
    stock: Math.round(toFloat(body.stock, 0) * 100) / 100,
    rivals: toInt(body.rivals, 0),
    beaten: toInt(body.beaten, 0),
    quote: String(body.quote || "").slice(0, 24),
    device: String(body.device || "unknown").slice(0, 40),
    at: Math.floor(Date.now() / 1000),
  };

  const rows = await loadRows(env);
  rows.push(row);
  const trimmed = rows.slice(-MAX_ROWS);
  await env.RUNS.put("runs", JSON.stringify(trimmed));
  return json({ ok: true, id: trimmed.length }, 200, env);
}

export async function handleRequest(request, env) {
  const url = new URL(request.url);
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: cors(env) });
  }
  if (url.pathname === "/api/runs" && request.method === "GET") {
    return json(await loadRows(env), 200, env);
  }
  if (url.pathname === "/api/honor" && request.method === "GET") {
    return handleHonor(url, env);
  }
  if (url.pathname === "/api/runs" && request.method === "POST") {
    return handlePost(request, env);
  }
  return json({ error: "not found" }, 404, env);
}

export default {
  fetch: handleRequest,
};
