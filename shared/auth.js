// SWEAT440 Dashboard — Authentication Utilities
// Requires users.js to be loaded before this file.

const AUTH_SESSION_KEY = 'sw440_auth';

// Returns the authenticated user object from sessionStorage.
// Redirects to login.html if no valid session exists.
function checkAuth() {
  const raw = sessionStorage.getItem(AUTH_SESSION_KEY);
  if (!raw) {
    _redirectToLogin();
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (e) {
    sessionStorage.removeItem(AUTH_SESSION_KEY);
    _redirectToLogin();
    return null;
  }
}

// Returns the array of allowed studio names, or null if the user has full access.
function getAuthStudios(user) {
  if (!user || user.role === 'admin' || user.studios === null) return null;
  return user.studios;
}

// Clears the session and redirects to the login page.
function logout() {
  sessionStorage.removeItem(AUTH_SESSION_KEY);
  _redirectToLogin();
}

function _redirectToLogin() {
  const isNso = location.pathname.includes('/nso-dashboard/');
  location.replace(isNso ? '../login.html' : 'login.html');
}

// Renders the user info + sign-out button into the nav.
// Call once after checkAuth() succeeds.
function renderAuthNav(user) {
  const nav = document.querySelector('.nav');
  if (!nav || !user) return;
  const el = document.createElement('div');
  el.className = 'nav-user';
  el.innerHTML = `
    <span class="nav-user-name">${user.name}</span>
    <button class="logout-btn" onclick="logout()">Sign out</button>
  `;
  nav.appendChild(el);

}

// ── Admin-only: trigger all three GitHub Actions workflows ──────────────────

const _GH_REPO  = 'dev-leadteam/dashboards';
const _GH_WORKFLOWS = [
  { id: 'nso_daily_refresh.yml',  label: 'NSO Dashboard Daily Refresh' },
  { id: 'refresh.yml',            label: 'Refresh Dashboard Data' },
  { id: 'refresh-paid-ads.yml',   label: 'Refresh Paid Ads Data' },
];
const _GH_TOKEN_KEY = 'sw440_gh_token';

function _renderRefreshButton(nav) {
  const btn = document.createElement('button');
  btn.id        = 'refreshAllBtn';
  btn.className = 'refresh-all-btn';
  btn.textContent = 'Refresh all data (15 min)';
  btn.onclick   = _triggerAllWorkflows;
  nav.insertBefore(btn, nav.querySelector('.nav-user'));
}

async function _triggerAllWorkflows() {
  const btn = document.getElementById('refreshAllBtn');

  // Retrieve or prompt for PAT (stored per session so it's never in source)
  let token = sessionStorage.getItem(_GH_TOKEN_KEY);
  if (!token) {
    token = prompt(
      'Enter a GitHub Personal Access Token with "workflow" scope\n' +
      '(stored in your browser session only — never saved to disk):'
    );
    if (!token) return;
    sessionStorage.setItem(_GH_TOKEN_KEY, token.trim());
    token = token.trim();
  }

  btn.disabled    = true;
  btn.textContent = 'Triggering…';

  const results = await Promise.allSettled(
    _GH_WORKFLOWS.map(wf =>
      fetch(`https://api.github.com/repos/${_GH_REPO}/actions/workflows/${wf.id}/dispatches`, {
        method : 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body   : JSON.stringify({ ref: 'main' }),
      })
    )
  );

  const allOk = results.every(r => r.status === 'fulfilled' && r.value.status === 204);
  const anyAuth = results.some(r => r.status === 'fulfilled' && r.value.status === 401);

  if (anyAuth) {
    sessionStorage.removeItem(_GH_TOKEN_KEY);   // clear bad token
    btn.disabled    = false;
    btn.textContent = 'Refresh all data (15 min)';
    alert('GitHub token rejected (401). It has been cleared — try again with a valid token.');
    return;
  }

  if (allOk) {
    btn.textContent = '✓ Workflows triggered!';
    setTimeout(() => {
      btn.disabled    = false;
      btn.textContent = 'Refresh all data (15 min)';
    }, 5000);
  } else {
    const errors = results
      .map((r, i) => r.status === 'rejected' || r.value?.status !== 204
        ? `${_GH_WORKFLOWS[i].label} (${r.value?.status ?? 'network error'})`
        : null)
      .filter(Boolean);
    btn.disabled    = false;
    btn.textContent = 'Refresh all data (15 min)';
    alert('Some workflows failed to trigger:\n' + errors.join('\n'));
  }
}
