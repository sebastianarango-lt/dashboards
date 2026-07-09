// Cloudflare Worker — proxies GitHub Actions workflow_dispatch calls so the
// GitHub token never ships to the browser. Secrets (GITHUB_TOKEN, APP_SECRET)
// are configured via `wrangler secret put`, never committed here.

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

    const workflows = WORKFLOW_SETS[body.set];
    if (!workflows) return new Response('Unknown workflow set', { status: 400, headers });

    const results = await Promise.all(
      workflows.map(wf =>
        fetch(`https://api.github.com/repos/${REPO}/actions/workflows/${wf}/dispatches`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${env.GITHUB_TOKEN}`,
            'Content-Type': 'application/json',
            'User-Agent': 'sweat440-refresh-proxy',
            Accept: 'application/vnd.github+json',
          },
          body: JSON.stringify({ ref: 'main' }),
        })
      )
    );

    const statuses = results.map(r => r.status);
    const allOk = statuses.every(s => s === 204);

    return new Response(JSON.stringify({ ok: allOk, workflows, statuses }), {
      status: allOk ? 200 : 502,
      headers: { ...headers, 'Content-Type': 'application/json' },
    });
  },
};
