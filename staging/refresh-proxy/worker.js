// Cloudflare Worker — proxies GitHub Actions workflow_dispatch calls and the
// Add Studio admin widget so the GitHub token never ships to the browser.
// Secrets (GITHUB_TOKEN, APP_SECRET) are configured via `wrangler secret put`,
// never committed here.

const REPO = 'dev-leadteam/dashboards';
const ALLOWED_ORIGIN = 'https://reports.sweat440.com';

const WORKFLOW_SETS = {
  all:       ['nso_daily_refresh.yml', 'refresh.yml', 'refresh-paid-ads.yml'],
  'no-ads':  ['refresh-no-ads.yml'],
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

// Normalize a studio name for duplicate comparison: case-insensitive, and
// dashes/extra whitespace collapsed — so "Dallas - Uptown" and "Dallas Uptown"
// (or "dallas  uptown") are recognized as the same studio.
function normalizeName(name) {
  return name.toLowerCase().replace(/[-–—]/g, ' ').replace(/\s+/g, ' ').trim();
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

// Merge a submitted patch into an existing studios.json entry. For most
// optional fields, a blank/null value in the patch means "leave unchanged"
// (so filling in just one missing field doesn't wipe out the rest of the
// profile). name/state/status/excluded_default always take the submitted
// value as-is — the form always shows a definite current value for those,
// there's no "blank" state to distinguish from "unchanged".
function mergeStudio(existing, patch) {
  const keep = (existingVal, patchVal) => (patchVal === null || patchVal === undefined) ? existingVal : patchVal;
  return {
    name: patch.name || existing.name,
    code: keep(existing.code, patch.code),
    state: patch.state || existing.state,
    status: patch.status || existing.status,
    excluded_default: !!patch.excluded_default,
    meta: {
      match: keep(existing.meta.match, patch.meta.match),
      ad_account_id: keep(existing.meta.ad_account_id, patch.meta.ad_account_id),
      page_id: keep(existing.meta.page_id, patch.meta.page_id),
      instagram_account_id: keep(existing.meta.instagram_account_id, patch.meta.instagram_account_id),
    },
    google_ads: {
      match: keep(existing.google_ads.match, patch.google_ads.match),
      customer_id: keep(existing.google_ads.customer_id, patch.google_ads.customer_id),
    },
    ga4: { studio_page_path: keep(existing.ga4.studio_page_path, patch.ga4.studio_page_path) },
    gbp: { location_id: keep(existing.gbp.location_id, patch.gbp.location_id) },
    snowflake_id: keep(existing.snowflake_id, patch.snowflake_id),
    social_slug: keep(existing.social_slug, patch.social_slug),
    // tier_pricing merges key-by-key so e.g. adding tier3 doesn't drop tier1/tier2.
    tier_pricing: patch.tier_pricing
      ? { ...(existing.tier_pricing || {}), ...patch.tier_pricing }
      : existing.tier_pricing,
  };
}

function fieldRows(studio) {
  return [
    ['Code', studio.code],
    ['State', studio.state],
    ['Status', studio.status],
    ['Excluded from dashboards by default', studio.excluded_default],
    ['Meta match', studio.meta.match],
    ['Meta ad account', studio.meta.ad_account_id],
    ['Meta page ID', studio.meta.page_id],
    ['Meta IG ID', studio.meta.instagram_account_id],
    ['Google Ads match', studio.google_ads.match],
    ['Google Ads customer ID', studio.google_ads.customer_id],
    ['GA4 page path', studio.ga4.studio_page_path],
    ['GBP location ID', studio.gbp.location_id],
    ['Snowflake ID', studio.snowflake_id],
    ['Social slug', studio.social_slug],
    ['Tier pricing', studio.tier_pricing ? JSON.stringify(studio.tier_pricing) : null],
  ];
}

function prBodyForAdd(studio) {
  const lines = [
    `Adds **${studio.name}** to the canonical studio registry (\`studios.json\`), submitted via the Add Studio admin widget.`,
    '',
    '| Field | Value |',
    '|---|---|',
    ...fieldRows(studio).map(([label, val]) => `| ${label} | ${val ?? '_(none)_'} |`),
    '',
    'Review the fields above against real ad-account/campaign naming before merging — this only wires up config, it does not verify the studio actually has live campaigns yet.',
  ];
  return lines.join('\n');
}

function prBodyForUpdate(existing, merged) {
  const before = new Map(fieldRows(existing));
  const after = fieldRows(merged);
  const changed = after.filter(([label, val]) => JSON.stringify(before.get(label)) !== JSON.stringify(val));

  const lines = [
    `Updates **${existing.name}**'s entry in the canonical studio registry (\`studios.json\`), submitted via the Add Studio admin widget's Edit mode.`,
    '',
  ];
  if (existing.name !== merged.name) {
    lines.push(`Renamed to **${merged.name}**.`, '');
  }
  if (changed.length) {
    lines.push('| Field | Before | After |', '|---|---|---|');
    for (const [label, val] of changed) {
      lines.push(`| ${label} | ${before.get(label) ?? '_(none)_'} | ${val ?? '_(none)_'} |`);
    }
  } else {
    lines.push('_No fields changed._');
  }
  lines.push('', 'Review before merging.');
  return lines.join('\n');
}

// Shared GitHub plumbing for both add and update: read studios.json, let the
// caller mutate the parsed registry (returning an {error, status} to abort),
// then branch + commit + open a PR with the result.
async function openStudiosPr(env, { branchPrefix, commitMessage, prTitle, mutate }) {
  const gh = ghHeaders(env);

  const contentRes = await fetch(`https://api.github.com/repos/${REPO}/contents/studios.json?ref=main`, { headers: gh });
  if (!contentRes.ok) {
    return { error: `Failed to read studios.json (${contentRes.status})`, status: 502 };
  }
  const contentJson = await contentRes.json();
  const registry = JSON.parse(b64DecodeUnicode(contentJson.content));

  const mutation = mutate(registry) || {};
  if (mutation.error) return mutation;
  const prBody = mutation.prBody;

  registry.studios.sort((a, b) => a.name.localeCompare(b.name));
  const newContent = JSON.stringify(registry, null, 2) + '\n';

  const refRes = await fetch(`https://api.github.com/repos/${REPO}/git/ref/heads/main`, { headers: gh });
  if (!refRes.ok) {
    return { error: `Failed to read main ref (${refRes.status})`, status: 502 };
  }
  const mainSha = (await refRes.json()).object.sha;

  const branch = `${branchPrefix}-${Date.now()}`;
  const branchRes = await fetch(`https://api.github.com/repos/${REPO}/git/refs`, {
    method: 'POST',
    headers: gh,
    body: JSON.stringify({ ref: `refs/heads/${branch}`, sha: mainSha }),
  });
  if (!branchRes.ok) {
    return { error: `Failed to create branch (${branchRes.status})`, status: 502 };
  }

  const commitRes = await fetch(`https://api.github.com/repos/${REPO}/contents/studios.json`, {
    method: 'PUT',
    headers: gh,
    body: JSON.stringify({
      message: commitMessage,
      content: b64EncodeUnicode(newContent),
      sha: contentJson.sha,
      branch,
    }),
  });
  if (!commitRes.ok) {
    return { error: `Failed to commit studios.json (${commitRes.status})`, status: 502 };
  }

  const prRes = await fetch(`https://api.github.com/repos/${REPO}/pulls`, {
    method: 'POST',
    headers: gh,
    body: JSON.stringify({ title: prTitle, head: branch, base: 'main', body: prBody }),
  });
  if (!prRes.ok) {
    return { error: `Failed to open pull request (${prRes.status})`, status: 502 };
  }
  const pr = await prRes.json();

  return { prUrl: pr.html_url };
}

async function handleAddStudio(body, env, headers) {
  const studio = normalizeStudio(body.studio || {});
  if (!studio.name || !studio.state) {
    return jsonResponse({ ok: false, error: 'Studio name and state are required.' }, 400, headers);
  }

  const result = await openStudiosPr(env, {
    branchPrefix: `add-studio-${slugify(studio.name)}`,
    commitMessage: `Add studio: ${studio.name}`,
    prTitle: `Add studio: ${studio.name}`,
    mutate(registry) {
      if (studio.code && registry.studios.some(s => s.code === studio.code)) {
        return { error: `Code ${studio.code} already exists in studios.json.`, status: 409 };
      }
      const normalizedNew = normalizeName(studio.name);
      const nameMatch = registry.studios.find(s => normalizeName(s.name) === normalizedNew);
      if (nameMatch) {
        return {
          error: `"${studio.name}" looks like a duplicate of the existing studio "${nameMatch.name}"` +
                 (nameMatch.code ? ` (${nameMatch.code})` : '') + '.',
          status: 409,
        };
      }
      registry.studios.push(studio);
      return { prBody: prBodyForAdd(studio) };
    },
  });

  if (result.error) return jsonResponse({ ok: false, error: result.error }, result.status || 502, headers);
  return jsonResponse({ ok: true, prUrl: result.prUrl }, 200, headers);
}

async function handleUpdateStudio(body, env, headers) {
  const originalName = typeof body.originalName === 'string' ? body.originalName.trim() : '';
  const patch = normalizeStudio(body.studio || {});
  if (!originalName) {
    return jsonResponse({ ok: false, error: 'Missing originalName — which studio to update.' }, 400, headers);
  }
  if (!patch.name || !patch.state) {
    return jsonResponse({ ok: false, error: 'Studio name and state are required.' }, 400, headers);
  }

  const result = await openStudiosPr(env, {
    branchPrefix: `update-studio-${slugify(patch.name)}`,
    commitMessage: `Update studio: ${patch.name}`,
    prTitle: `Update studio: ${patch.name}`,
    mutate(registry) {
      const idx = registry.studios.findIndex(s => s.name === originalName);
      if (idx === -1) {
        return {
          error: `Couldn't find a studio named "${originalName}" in studios.json — it may have been renamed or removed. Refresh and try again.`,
          status: 404,
        };
      }
      const existing = registry.studios[idx];
      const merged = mergeStudio(existing, patch);

      const others = registry.studios.filter((_, i) => i !== idx);
      if (merged.code && others.some(s => s.code === merged.code)) {
        return { error: `Code ${merged.code} already exists on another studio in studios.json.`, status: 409 };
      }
      const normalizedNew = normalizeName(merged.name);
      const nameMatch = others.find(s => normalizeName(s.name) === normalizedNew);
      if (nameMatch) {
        return {
          error: `"${merged.name}" looks like a duplicate of the existing studio "${nameMatch.name}"` +
                 (nameMatch.code ? ` (${nameMatch.code})` : '') + '.',
          status: 409,
        };
      }

      registry.studios[idx] = merged;
      return { prBody: prBodyForUpdate(existing, merged) };
    },
  });

  if (result.error) return jsonResponse({ ok: false, error: result.error }, result.status || 502, headers);
  return jsonResponse({ ok: true, prUrl: result.prUrl }, 200, headers);
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

    if (body.action === 'add_studio' || body.action === 'update_studio') {
      try {
        return await (body.action === 'add_studio' ? handleAddStudio(body, env, headers) : handleUpdateStudio(body, env, headers));
      } catch (e) {
        return jsonResponse({ ok: false, error: `Unexpected error: ${e.message}` }, 500, headers);
      }
    }

    return dispatchWorkflows(body, env, headers);
  },
};
