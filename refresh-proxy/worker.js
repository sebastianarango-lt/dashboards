// Cloudflare Worker — proxies GitHub Actions workflow_dispatch calls and the
// Add Studio admin widget so the GitHub token never ships to the browser.
// Secrets (GITHUB_TOKEN, APP_SECRET) are configured via `wrangler secret put`,
// never committed here.

const REPO = 'dev-leadteam/dashboards';
const ALLOWED_ORIGIN = 'https://reports.sweat440.com';

const WORKFLOW_SETS = {
  all:       ['nso_daily_refresh.yml', 'refresh.yml', 'refresh-paid-ads.yml'],
  snowflake: ['refresh-snowflake.yml'],
};

function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin':  origin === ALLOWED_ORIGIN ? origin : 'null',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-App-Secret',
  };
}

function jsonResponse(obj, status, headers) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...headers, 'Content-Type': 'application/json' },
  });
}

function b64EncodeUnicode(str) {
  return btoa(unescape(encodeURIComponent(str)));
}

function b64DecodeUnicode(b64) {
  return decodeURIComponent(escape(atob(b64)));
}

function slugify(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function ghHeaders(env) {
  return {
    Authorization: `Bearer ${env.GITHUB_TOKEN}`,
    'Content-Type': 'application/json',
    'User-Agent': 'sweat440-refresh-proxy',
    Accept: 'application/vnd.github+json',
  };
}

async function dispatchWorkflows(body, env, headers) {
  const workflows = WORKFLOW_SETS[body.set];
  if (!workflows) return jsonResponse({ ok: false, error: 'Unknown workflow set' }, 400, headers);

  const results = await Promise.all(
    workflows.map(wf =>
      fetch(`https://api.github.com/repos/${REPO}/actions/workflows/${wf}/dispatches`, {
        method: 'POST',
        headers: ghHeaders(env),
        body: JSON.stringify({ ref: 'main' }),
      })
    )
  );

  const statuses = results.map(r => r.status);
  const allOk = statuses.every(s => s === 204);
  return jsonResponse({ ok: allOk, workflows, statuses }, allOk ? 200 : 502, headers);
}

// Build a normalized studios.json entry from whatever fields the widget submitted.
// Every field defaults to null rather than being omitted, so every entry in the
// registry has the same shape.
function normalizeStudio(studio) {
  const str = v => (typeof v === 'string' && v.trim()) ? v.trim() : null;
  return {
    name: str(studio.name),
    code: str(studio.code),
    state: str(studio.state),
    status: str(studio.status) || 'nso',
    excluded_default: !!studio.excluded_default,
    meta: {
      match: str(studio.meta && studio.meta.match),
      ad_account_id: str(studio.meta && studio.meta.ad_account_id),
      page_id: str(studio.meta && studio.meta.page_id),
      instagram_account_id: str(studio.meta && studio.meta.instagram_account_id),
    },
    google_ads: {
      match: str(studio.google_ads && studio.google_ads.match),
      customer_id: str(studio.google_ads && studio.google_ads.customer_id),
    },
    ga4: { studio_page_path: str(studio.ga4 && studio.ga4.studio_page_path) },
    gbp: { location_id: str(studio.gbp && studio.gbp.location_id) },
    snowflake_id: studio.snowflake_id ? Number(studio.snowflake_id) : null,
    social_slug: str(studio.social_slug),
    tier_pricing: (studio.tier_pricing && Object.keys(studio.tier_pricing).length) ? studio.tier_pricing : null,
  };
}

function prBodyFor(studio) {
  const lines = [
    `Adds **${studio.name}** to the canonical studio registry (\`studios.json\`), submitted via the Add Studio admin widget.`,
    '',
    '| Field | Value |',
    '|---|---|',
    `| Code | ${studio.code || '_(none yet)_'} |`,
    `| State | ${studio.state} |`,
    `| Status | ${studio.status} |`,
    `| Excluded from dashboards by default | ${studio.excluded_default} |`,
    `| Meta match | ${studio.meta.match || '_(none)_'} |`,
    `| Google Ads match | ${studio.google_ads.match || '_(none)_'} |`,
    `| GA4 page path | ${studio.ga4.studio_page_path || '_(none)_'} |`,
    `| GBP location ID | ${studio.gbp.location_id || '_(none)_'} |`,
    `| Snowflake ID | ${studio.snowflake_id ?? '_(none)_'} |`,
    '',
    'Review the fields above against real ad-account/campaign naming before merging — this only wires up config, it does not verify the studio actually has live campaigns yet.',
  ];
  return lines.join('\n');
}

async function handleAddStudio(body, env, headers) {
  const studio = normalizeStudio(body.studio || {});
  if (!studio.name || !studio.state) {
    return jsonResponse({ ok: false, error: 'Studio name and state are required.' }, 400, headers);
  }

  const gh = ghHeaders(env);

  // 1. Read current studios.json
  const contentRes = await fetch(`https://api.github.com/repos/${REPO}/contents/studios.json?ref=main`, { headers: gh });
  if (!contentRes.ok) {
    return jsonResponse({ ok: false, error: `Failed to read studios.json (${contentRes.status})` }, 502, headers);
  }
  const contentJson = await contentRes.json();
  const registry = JSON.parse(b64DecodeUnicode(contentJson.content));

  if (studio.code && registry.studios.some(s => s.code === studio.code)) {
    return jsonResponse({ ok: false, error: `Code ${studio.code} already exists in studios.json.` }, 409, headers);
  }
  if (registry.studios.some(s => s.name.toLowerCase() === studio.name.toLowerCase())) {
    return jsonResponse({ ok: false, error: `A studio named "${studio.name}" already exists in studios.json.` }, 409, headers);
  }

  registry.studios.push(studio);
  registry.studios.sort((a, b) => a.name.localeCompare(b.name));
  const newContent = JSON.stringify(registry, null, 2) + '\n';

  // 2. Branch from main's latest commit
  const refRes = await fetch(`https://api.github.com/repos/${REPO}/git/ref/heads/main`, { headers: gh });
  if (!refRes.ok) {
    return jsonResponse({ ok: false, error: `Failed to read main ref (${refRes.status})` }, 502, headers);
  }
  const mainSha = (await refRes.json()).object.sha;

  const branch = `add-studio-${slugify(studio.name)}-${Date.now()}`;
  const branchRes = await fetch(`https://api.github.com/repos/${REPO}/git/refs`, {
    method: 'POST',
    headers: gh,
    body: JSON.stringify({ ref: `refs/heads/${branch}`, sha: mainSha }),
  });
  if (!branchRes.ok) {
    return jsonResponse({ ok: false, error: `Failed to create branch (${branchRes.status})` }, 502, headers);
  }

  // 3. Commit updated studios.json to the new branch
  const commitRes = await fetch(`https://api.github.com/repos/${REPO}/contents/studios.json`, {
    method: 'PUT',
    headers: gh,
    body: JSON.stringify({
      message: `Add studio: ${studio.name}`,
      content: b64EncodeUnicode(newContent),
      sha: contentJson.sha,
      branch,
    }),
  });
  if (!commitRes.ok) {
    return jsonResponse({ ok: false, error: `Failed to commit studios.json (${commitRes.status})` }, 502, headers);
  }

  // 4. Open the PR
  const prRes = await fetch(`https://api.github.com/repos/${REPO}/pulls`, {
    method: 'POST',
    headers: gh,
    body: JSON.stringify({
      title: `Add studio: ${studio.name}`,
      head: branch,
      base: 'main',
      body: prBodyFor(studio),
    }),
  });
  if (!prRes.ok) {
    return jsonResponse({ ok: false, error: `Failed to open pull request (${prRes.status})` }, 502, headers);
  }
  const pr = await prRes.json();

  return jsonResponse({ ok: true, prUrl: pr.html_url }, 200, headers);
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const headers = corsHeaders(origin);

    if (request.method === 'OPTIONS') return new Response(null, { headers });
    if (origin !== ALLOWED_ORIGIN) return new Response('Forbidden origin', { status: 403, headers });
    if (request.method !== 'POST') return new Response('Method not allowed', { status: 405, headers });
    if (request.headers.get('X-App-Secret') !== env.APP_SECRET) {
      return new Response('Unauthorized', { status: 401, headers });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return new Response('Bad request', { status: 400, headers });
    }

    if (body.action === 'add_studio') {
      try {
        return await handleAddStudio(body, env, headers);
      } catch (e) {
        return jsonResponse({ ok: false, error: `Unexpected error: ${e.message}` }, 500, headers);
      }
    }

    return dispatchWorkflows(body, env, headers);
  },
};
