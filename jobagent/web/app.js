/* LocalJobAgent dashboard — vanilla JS, no build step. */

const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const api = async (path, opts = {}) => {
  const r = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.status === 204 ? null : r.json();
};

let JOBS = [], APPS = [], SELECTED = new Set(), VIEW = 'review';

function toast(msg, ms = 3000) {
  const t = $('#toast');
  t.textContent = msg; t.hidden = false;
  clearTimeout(t._t); t._t = setTimeout(() => (t.hidden = true), ms);
}

const scoreColor = (s) => s >= 85 ? 'var(--ok)' : s >= 75 ? 'var(--acc)' : s >= 65 ? 'var(--warn)' : 'var(--no)';
const ago = (iso) => {
  if (!iso) return '';
  const d = (Date.now() - new Date(iso)) / 86400000;
  if (d < 0.04) return 'just now';
  if (d < 1) return `${Math.round(d * 24)}h ago`;
  return `${Math.round(d)}d ago`;
};

/* ============================ navigation ============================ */
$$('.nav').forEach(b => b.onclick = () => {
  VIEW = b.dataset.view;
  $$('.nav').forEach(x => x.classList.toggle('active', x === b));
  $$('.view').forEach(v => v.hidden = v.id !== `view-${VIEW}`);
  refresh();
});

/* ============================== review ============================== */
async function loadJobs() {
  const min = $('#fScore').value, src = $('#fSource').value, q = $('#search').value;
  JOBS = await api(`/api/jobs?status=pending&limit=300&min_score=${min}&source=${encodeURIComponent(src)}&q=${encodeURIComponent(q)}`);
  renderJobs();
  const sources = [...new Set(JOBS.map(j => j.source))].sort();
  const sel = $('#fSource');
  if (sel.options.length - 1 !== sources.length) {
    sel.innerHTML = '<option value="">All sources</option>' +
      sources.map(s => `<option ${s === src ? 'selected' : ''}>${esc(s)}</option>`).join('');
  }
}

function renderJobs() {
  const el = $('#jobList');
  if (!JOBS.length) {
    el.innerHTML = `<div class="empty"><b>Nothing waiting for review</b>
      Hit <em>Run job search</em> in the sidebar, or loosen the filters.</div>`;
    return;
  }
  el.innerHTML = JOBS.map(j => {
    const sal = j.salary_min_lpa ? `${j.salary_min_lpa}–${j.salary_max_lpa ?? j.salary_min_lpa} LPA` : '';
    const chips = [
      ...(j.matched_skills || []).slice(0, 6).map(s => `<span class="chip ok">${esc(s)}</span>`),
      ...(j.missing_skills || []).slice(0, 3).map(s => `<span class="chip miss">− ${esc(s)}</span>`),
      ...(j.red_flags || []).slice(0, 2).map(s => `<span class="chip flag">⚑ ${esc(s)}</span>`),
    ].join('');
    return `<div class="card ${j.score >= 85 ? 'strong' : ''}" data-id="${j.id}">
      <input type="checkbox" data-sel="${j.id}" ${SELECTED.has(j.id) ? 'checked' : ''} />
      <div class="body">
        <div class="t">${esc(j.title)}</div>
        <div class="m">
          <b>${esc(j.company)}</b> · ${esc(j.location || '—')}
          ${j.is_remote ? '· Remote' : ''} ${sal ? '· ' + sal : ''}
          <span class="chip src">${esc(j.source)}</span>
          <span style="color:var(--tx3)">${ago(j.posted_at || j.discovered_at)}</span>
        </div>
        <div class="why">${esc(j.verdict || j.reasoning || '')}</div>
        <div class="chips">${chips}</div>
      </div>
      <div class="acts">
        <div class="score" style="--p:${j.score};--sc:${scoreColor(j.score)}"><span>${j.score}</span></div>
        <button class="btn ok sm" data-act="approved" data-id="${j.id}">Approve</button>
        <button class="btn no sm" data-act="rejected" data-id="${j.id}">Reject</button>
      </div>
    </div>`;
  }).join('');
}

$('#jobList').addEventListener('click', async (e) => {
  const sel = e.target.closest('[data-sel]');
  if (sel) {
    const id = +sel.dataset.sel;
    sel.checked ? SELECTED.add(id) : SELECTED.delete(id);
    updateBulk(); e.stopPropagation(); return;
  }
  const btn = e.target.closest('[data-act]');
  if (btn) {
    e.stopPropagation();
    await api(`/api/jobs/${btn.dataset.id}`, { method: 'PATCH', body: { status: btn.dataset.act } });
    toast(btn.dataset.act === 'approved' ? 'Approved — queued for the agent to apply' : 'Rejected');
    refresh(); return;
  }
  const card = e.target.closest('.card');
  if (card) openDrawer(+card.dataset.id);
});

function updateBulk() {
  $('#bulkbar').hidden = SELECTED.size === 0;
  $('#bulkCount').textContent = `${SELECTED.size} selected`;
}
$$('[data-bulk]').forEach(b => b.onclick = async () => {
  await api('/api/jobs/bulk', { method: 'POST', body: { ids: [...SELECTED], status: b.dataset.bulk } });
  toast(`${SELECTED.size} jobs → ${b.dataset.bulk}`);
  SELECTED.clear(); updateBulk(); refresh();
});
$('#bulkClear').onclick = () => { SELECTED.clear(); updateBulk(); renderJobs(); };

/* ============================== drawer ============================== */
async function openDrawer(id) {
  const j = await api(`/api/jobs/${id}`);
  const a = j.application;
  const pending = a?.pending_questions || [];
  const sal = j.salary_min_lpa ? `${j.salary_min_lpa}–${j.salary_max_lpa ?? j.salary_min_lpa} LPA` : (j.salary_text || 'not disclosed');

  $('#drawer').innerHTML = `
    <button class="close" id="dClose">×</button>
    <h2>${esc(j.title)}</h2>
    <div class="meta"><b>${esc(j.company)}</b> · ${esc(j.location)} ${j.is_remote ? '· Remote' : ''}</div>

    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">
      <button class="btn ok" data-act="approved" data-id="${j.id}">Approve &amp; auto-apply</button>
      <button class="btn no" data-act="rejected" data-id="${j.id}">Reject</button>
      <a class="btn" href="${esc(j.url)}" target="_blank" rel="noopener">Open posting ↗</a>
    </div>

    <div class="grid2">
      <div class="panel">
        <div class="kv"><b>Match score</b><span style="color:${scoreColor(j.score)};font-weight:700">${j.score}/100</span></div>
        <div class="kv"><b>Seniority fit</b><span>${esc(j.seniority_fit || '—')}</span></div>
        <div class="kv"><b>Salary</b><span>${esc(sal)}</span></div>
        <div class="kv"><b>Source</b><span>${esc(j.source)} · ${esc(j.ats)}</span></div>
        <div class="kv"><b>Posted</b><span>${ago(j.posted_at) || 'unknown'}</span></div>
      </div>
      <div class="panel">
        <h4 style="font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--tx3);margin:0 0 8px">Why this score</h4>
        <div style="font-size:13px;color:var(--tx2);line-height:1.6">${esc(j.reasoning || j.verdict || '—')}</div>
      </div>
    </div>

    ${section('You match', (j.matched_skills || []).map(s => `<span class="chip ok">${esc(s)}</span>`).join(''))}
    ${section('Gaps', (j.missing_skills || []).map(s => `<span class="chip miss">${esc(s)}</span>`).join(''))}
    ${(j.red_flags || []).length ? section('Red flags', j.red_flags.map(s => `<span class="chip flag">${esc(s)}</span>`).join('')) : ''}

    ${pending.length ? `<div class="sec"><h4>The agent needs your answer</h4>
      ${pending.map((p, i) => `<div class="qa">
        <label>${esc(p.question)}</label>
        ${p.options?.length
          ? `<select class="input" data-q="${esc(p.question)}">${p.options.map(o => `<option ${o === p.suggested ? 'selected' : ''}>${esc(o)}</option>`).join('')}</select>`
          : `<input class="input" data-q="${esc(p.question)}" value="${esc(p.suggested || '')}" placeholder="Your answer" />`}
      </div>`).join('')}
      <button class="btn primary" id="saveAnswers" data-app="${a.id}">Save answers &amp; retry application</button>
      <p class="sub" style="margin-top:7px">These get remembered, so the same question never stops the agent twice.</p>
    </div>` : ''}

    ${a?.cover_letter ? section('Generated cover letter', `<div class="jd">${esc(a.cover_letter)}</div>`) : ''}
    ${section('Job description', `<div class="jd">${esc(j.description || 'No description captured.')}</div>`)}
  `;
  $('#drawer').hidden = false; $('#scrim').hidden = false;

  $('#dClose').onclick = closeDrawer;
  $$('#drawer [data-act]').forEach(b => b.onclick = async () => {
    await api(`/api/jobs/${b.dataset.id}`, { method: 'PATCH', body: { status: b.dataset.act } });
    toast(b.dataset.act === 'approved' ? 'Approved — the agent will apply' : 'Rejected');
    closeDrawer(); refresh();
  });
  const sa = $('#saveAnswers');
  if (sa) sa.onclick = async () => {
    const answers = {};
    $$('#drawer [data-q]').forEach(i => answers[i.dataset.q] = i.value);
    await api(`/api/applications/${sa.dataset.app}/answers`, { method: 'POST', body: { answers } });
    toast('Saved — requeued for the agent'); closeDrawer(); refresh();
  };
}
const section = (title, html) => html
  ? `<div class="sec"><h4>${title}</h4><div class="chips" style="margin:0">${html}</div></div>` : '';
function closeDrawer() { $('#drawer').hidden = true; $('#scrim').hidden = true; }
$('#scrim').onclick = closeDrawer;
document.addEventListener('keydown', e => e.key === 'Escape' && closeDrawer());

/* ============================== tracker ============================= */
const COLS = [
  ['queued', 'Queued'], ['applying', 'Applying'], ['needs_input', 'Needs you'],
  ['applied', 'Applied'], ['screening', 'Screening'], ['interview', 'Interview'],
  ['offer', 'Offer'], ['rejected', 'Rejected'],
];

async function loadApps() {
  APPS = await api('/api/applications?limit=400');
  const byCol = Object.fromEntries(COLS.map(([k]) => [k, []]));
  APPS.forEach(a => (byCol[a.status] ||= []).push(a));
  byCol.failed?.forEach?.(() => {});
  (APPS.filter(a => a.status === 'failed')).forEach(a => byCol.needs_input.push(a));

  $('#board').innerHTML = COLS.map(([k, label]) => `
    <div class="col" data-col="${k}">
      <h3>${label}<em>${(byCol[k] || []).length}</em></h3>
      ${(byCol[k] || []).map(a => {
        const j = a.job || {};
        const alert = a.status === 'needs_input' || a.status === 'failed';
        return `<div class="tcard ${alert ? 'alert' : ''}" draggable="true" data-app="${a.id}" data-job="${a.job_id}">
          <div class="t">${esc(j.title || 'Unknown role')}</div>
          <div class="c">${esc(j.company || '')}</div>
          <div class="f">
            <span>${esc(a.method || j.source || '')}</span>
            <span>${ago(a.submitted_at || a.updated_at)}</span>
          </div>
          ${a.error ? `<div class="c" style="color:var(--no);margin-top:6px;font-size:11px">${esc(a.error.slice(0, 110))}</div>` : ''}
        </div>`;
      }).join('') || '<div style="color:var(--tx3);font-size:12px;padding:6px 2px">—</div>'}
    </div>`).join('');

  $$('.tcard').forEach(c => {
    c.ondragstart = e => e.dataTransfer.setData('text/plain', c.dataset.app);
    c.onclick = () => openDrawer(+c.dataset.job);
  });
  $$('.col').forEach(col => {
    col.ondragover = e => { e.preventDefault(); col.classList.add('over'); };
    col.ondragleave = () => col.classList.remove('over');
    col.ondrop = async e => {
      e.preventDefault(); col.classList.remove('over');
      const id = e.dataTransfer.getData('text/plain');
      await api(`/api/applications/${id}`, { method: 'PATCH', body: { status: col.dataset.col } });
      toast(`Moved to ${col.dataset.col.replace('_', ' ')}`);
      loadApps();
    };
  });
}

/* ============================== profile ============================= */
async function loadProfile() {
  const p = await api('/api/profile');
  if (!p.exists) {
    $('#profileBody').innerHTML = `<div class="empty"><b>No skill library yet</b>
      Put your resume in the <code>resume/</code> folder, then hit “Re-parse resume”.</div>`;
    return;
  }
  const list = (title, arr, cls = '') => arr?.length
    ? `<div class="panel"><h2>${title}</h2><div class="chips" style="margin:0">
        ${arr.map(x => `<span class="chip ${cls}">${esc(x)}</span>`).join('')}</div></div>` : '';
  $('#profileBody').innerHTML = `
    <div class="panel" style="margin-bottom:12px">
      <h2>${esc(p.headline || '')}</h2>
      <div style="color:var(--tx2);font-size:13px;line-height:1.6">${esc(p.summary || '')}</div>
      <div class="kv" style="margin-top:12px"><b>Seniority</b><span>${esc(p.seniority || '')} · ${p.total_years_experience || 0} yrs</span></div>
      <div class="kv"><b>Parsed from</b><span>${esc((p.source_file || '').split('/').pop())}</span></div>
    </div>
    <div class="grid2">
      ${list('Searching for these roles', p.target_roles, 'src')}
      ${list('Core skills', p.core_skills, 'ok')}
      ${list('Domains', p.domains)}
      ${list('All skills', p.hard_skills)}
      ${list('Not a fit for', p.red_lines, 'flag')}
      ${p.achievements?.length ? `<div class="panel"><h2>Key achievements</h2>
        <ul style="margin:0;padding-left:17px;color:var(--tx2);font-size:12.5px;line-height:1.7">
        ${p.achievements.map(a => `<li>${esc(a)}</li>`).join('')}</ul></div>` : ''}
    </div>`;
}

/* ============================== activity =========================== */
async function loadLogs() {
  const rows = await api('/api/logs?limit=120');
  $('#logBody').innerHTML = rows.map(r => `<div class="logline ${esc(r.kind)}">
    <span class="ts">${new Date(r.ts).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'medium' })}</span>
    <span>${esc(r.message)}</span></div>`).join('') ||
    '<div class="empty">Nothing logged yet.</div>';
}

/* =============================== stats ============================= */
async function loadStats() {
  const s = await api('/api/stats');
  $('#navPending').textContent = s.pending;
  $('#navPending').dataset.zero = s.pending ? '0' : '1';
  $('#navApps').textContent = s.queued + s.needs_input;
  $('#navApps').dataset.zero = (s.queued + s.needs_input) ? '0' : '1';

  $('#stats').innerHTML = [
    ['Awaiting review', s.pending, 'accent'],
    ['Found today', s.found_today, ''],
    ['Avg match', s.avg_score, ''],
    ['Applied this week', s.applied_week, ''],
    ['Applied total', s.applied_total, ''],
    ['Needs your input', s.needs_input, ''],
    ['Interviews', s.interview, ''],
  ].map(([k, v, c]) => `<div class="stat ${c}"><div class="k">${k}</div><div class="v">${v}</div></div>`).join('');

  const busy = !!s.running;
  $('#btnDiscover').disabled = busy;
  $('#btnApply').disabled = busy;
  if (busy) {
    const b = s.running === 'discovery' ? $('#btnDiscover') : $('#btnApply');
    b.innerHTML = `<span class="spin"></span>${s.running === 'discovery' ? 'Searching…' : 'Applying…'}`;
  } else {
    $('#btnDiscover').textContent = 'Run job search';
    $('#btnApply').textContent = 'Apply to approved';
  }
  return s;
}

async function loadHealth() {
  try {
    const h = await api('/api/health');
    const models = Object.entries(h.models_present || {});
    $('#health').innerHTML = `
      <div class="row"><span><span class="dot ${h.ollama ? 'on' : 'off'}"></span>Ollama</span>
        <span>${h.ollama ? 'connected' : 'offline'}</span></div>
      ${models.map(([m, ok]) => `<div class="row"><span><span class="dot ${ok ? 'on' : 'off'}"></span>${esc(m.split(':')[0])}</span>
        <span>${ok ? 'ready' : 'missing'}</span></div>`).join('')}
      <div class="row"><span><span class="dot ${h.resume_pdf ? 'on' : 'off'}"></span>Resume PDF</span>
        <span>${h.resume_pdf ? 'found' : 'not set'}</span></div>
      <div class="row"><span>Auto-submit</span><span>${h.auto_submit ? 'on' : 'off'}</span></div>
      <div class="row"><span>Daily cap</span><span>${h.daily_cap}</span></div>`;
  } catch { /* server starting */ }
}

/* =============================== actions =========================== */
$('#btnDiscover').onclick = async () => {
  try { await api('/api/run/discovery', { method: 'POST' }); toast('Job search started — this takes a few minutes'); }
  catch (e) { toast(e.message); }
  loadStats();
};
$('#btnApply').onclick = async () => {
  try { await api('/api/run/apply', { method: 'POST' }); toast('Applying to your approved jobs…'); }
  catch (e) { toast(e.message); }
  loadStats();
};
$('#btnReparse').onclick = async () => {
  toast('Re-reading your resume with the local model…', 8000);
  try { const r = await api('/api/run/reparse-resume', { method: 'POST' }); toast(`Done — ${r.skills} skills indexed`); loadProfile(); }
  catch (e) { toast('Failed: ' + e.message, 6000); }
};
['#search', '#fSource', '#fScore'].forEach(s => {
  let t; $(s).addEventListener('input', () => { clearTimeout(t); t = setTimeout(loadJobs, 250); });
});

/* =============================== boot ============================== */
async function refresh() {
  await loadStats().catch(() => {});
  if (VIEW === 'review') loadJobs().catch(() => {});
  if (VIEW === 'tracker') loadApps().catch(() => {});
  if (VIEW === 'profile') loadProfile().catch(() => {});
  if (VIEW === 'activity') loadLogs().catch(() => {});
}
refresh(); loadHealth();
setInterval(() => { loadStats().catch(() => {}); if (VIEW === 'activity') loadLogs(); }, 5000);
setInterval(loadHealth, 30000);
