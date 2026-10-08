/* Orbit v2: keyboard-driven triage workspace. Self-contained: it reads the same /api/data and /api/state as v1
   and writes the same state keys (jobs, meta.mission/skips/verify/reach/followups), so both UIs stay in sync.
   Orbit never applies or messages for you: "Applied" is only recorded when you press the key or the button. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const norm = v => String(v || "").trim().toLowerCase().replace(/[.,]/g, "").replace(/\s+/g, " ");
  const plural = (n, a, b) => `${n} ${n === 1 ? a : b || a + "s"}`;
  const STATUSES = ["Not started", "Watching", "Applied", "Interviewing", "Offer", "Closed"];
  const pad = n => String(n).padStart(2, "0");
  const fmt = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const today = () => fmt(new Date());
  const addDays = (iso, n) => { const d = new Date(iso + "T00:00:00"); d.setDate(d.getDate() + n); return fmt(d); };
  const dayDiff = (a, b) => Math.round((new Date(b + "T00:00:00") - new Date(a + "T00:00:00")) / 864e5);
  const weekStart = () => { const d = new Date(); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return fmt(d); };

  const S = { data: null, st: null, c: localStorage.getItem("orbit.candidate") || "Vrinda", stage: "inbox", sel: null, q: "", fu: false, rows: [], scope: null };

  /* ---------- state ---------- */
  const meta = () => { const m = (S.st.meta ||= {}); for (const k of ["prefs", "skips", "verify", "reach", "followups", "mission"]) m[k] ||= {}; return m; };
  let timer;
  const save = () => { clearTimeout(timer); timer = setTimeout(() => fetch("/api/state", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(S.st) }).catch(() => toast("Could not save locally")), 250); };

  /* ---------- identity, jobs, contacts ---------- */
  const IDP = ["jk", "gh_jid", "jobid", "job_id", "requisitionid", "reqid", "folderid", "id"];
  const ident = j => {
    if (j.url) { try { const u = new URL(j.url); const q = IDP.map(k => [k, u.searchParams.get(k)]).filter(x => x[1]).map(x => x.join("=")).join("&"); return `url:${u.hostname.toLowerCase()}${u.pathname.replace(/\/$/, "")}${q ? "?" + q : ""}`; } catch (_) {} }
    return `role:${norm(j.company)}|${norm(j.title)}|${norm(j.location)}`;
  };
  const keyOf = (c, j) => `${c}:${ident(j)}`;
  const urlOf = j => { const m = String(j.url || j.notes || "").match(/https?:\/\/[^\s<>"']+/i); return m ? m[0].replace(/[),.;]+$/, "") : ""; };
  const profile = c => S.data.profiles.find(p => p.candidate === c);
  const jobsOf = c => [...(profile(c)?.jobs || []), ...Object.values(S.st.customJobs || {}).filter(j => j.candidate === c)];
  const PLACEHOLDER = /^(no\s+(contact|referral)|none|n\/a|na|nil|tbd|unknown|-+)\b/i;
  function contactsOf(c, company) {
    const p = profile(c), found = [], seen = new Set();
    for (const x of p?.contacts || []) if (norm(x.company) === norm(company)) found.push(x);
    const roster = (p?.companies || []).find(x => norm(x.name) === norm(company));
    for (const n of roster?.contacts || []) found.push(typeof n === "string" ? { company, name: n, title: "" } : n);
    return found.filter(x => x.name && !PLACEHOLDER.test(String(x.name).trim()) && !seen.has(norm(x.name)) && seen.add(norm(x.name)));
  }
  const CAT = { hr: /\b(hr|human resources|talent|recruit\w*|people (ops|operations|partner|team)|\bta\b|hiring)\b/i, eng: /engineer|\bsde\b|developer|software|architect|tech lead|\bswe\b|\bmts\b/i, alumni: /alumn|\biit\b|\bnit\b|\bbits\b|\biiit\b|\biim\b|xlri|\bisb\b|college|university|batch/i };
  const txt = x => `${x.title || ""} ${x.name || ""}`;
  const catOf = x => CAT.hr.test(txt(x)) ? "hr" : CAT.eng.test(txt(x)) ? "eng" : CAT.alumni.test(txt(x)) ? "alumni" : "other";
  const CATLABEL = { hr: "HR / TA", eng: "Engineers", alumni: "Alumni", other: "Other" };

  /* ---------- scope (same mission record as v1) ---------- */
  const mission = c => ({ companies: [], any: false, minLPA: 0, unknownPay: true, started: null, ...(meta().mission[c] || {}) });
  const payLPA = s => { const m = String(s || "").match(/(\d+(?:\.\d+)?)\s*(?:-|to|–)?\s*(\d+(?:\.\d+)?)?\s*(lpa|lakh|l\b)/i); return m ? parseFloat(m[2] || m[1]) : null; };
  const payState = (j, c) => { const l = payLPA(j.compensation), f = mission(c).minLPA || 0; return !l ? "unknown" : (!f || l >= f ? "ok" : "below"); };
  const inScope = (j, c) => { const m = mission(c); const okCo = !m.started || m.any || m.companies.includes(norm(j.company)); const p = payState(j, c); return okCo && (p === "ok" || (p === "unknown" && m.unknownPay)); };

  /* ---------- explainable fit (a local heuristic: title, level, place, contacts, link) ---------- */
  const FAM = {
    backend: /backend|back-end|server[- ]side|\bapi\b|platform|distributed|infrastructure|systems?\b/i,
    sde: /\bsde\b|software (development )?engineer|software developer|\bswe\b|member of technical staff|\bmts\b|programmer/i,
    fullstack: /full[- ]?stack/i, data: /data (engineer|scientist|analyst)|machine learning|\bml\b|\bai\b|analytics/i,
    frontend: /front[- ]?end|\bui\b|react|web developer/i, devops: /devops|\bsre\b|reliability|cloud|security engineer/i, quant: /quant|low[- ]?latency|trading|hft/i,
  };
  const PLACES = ["Bengaluru", "Hyderabad", "Pune", "Delhi NCR", "Mumbai", "Chennai", "Remote"];
  const CITY = { Bengaluru: /bengaluru|bangalore|karnataka/i, Hyderabad: /hyderabad|telangana/i, Pune: /\bpune\b/i, "Delhi NCR": /delhi|\bncr\b|gurgaon|gurugram|noida|haryana/i, Mumbai: /mumbai|thane/i, Chennai: /chennai/i, Remote: /remote|work from home|\bwfh\b|anywhere/i };
  const DEFAULTS = { Vaanya: { roles: ["sde", "backend", "fullstack"], level: "entry", places: PLACES }, Vrinda: { roles: ["backend", "sde"], level: "mid", places: PLACES } };
  const prefs = c => ({ ...(DEFAULTS[c] || DEFAULTS.Vrinda), ...(meta().prefs[c] || {}) });
  const LV = [["exec", /director|\bvp\b|vice president|head of|manager|principal|distinguished|fellow|chief/i], ["senior", /senior|\bsr\b|staff|\blead\b|architect|\bsde[\s-]*(iii|3)\b|\b(iii|iv)\b/i], ["entry", /graduate|intern|trainee|fresher|entry|new grad|campus|associate|junior|\bjr\b|apprentice|early career|\bsde[\s-]*(i|1)\b/i]];
  const levelOf = t => (LV.find(([, re]) => re.test(t)) || ["mid"])[0];
  const levelPts = (pref, lv) => lv === "exec" ? 0 : pref === lv ? 20 : ({ "mid>senior": 12, "senior>mid": 12, "entry>mid": 10, "mid>entry": 6 }[`${pref}>${lv}`] ?? 0);
  function fit(r) {
    if (r.fit) return r.fit;
    const j = r.j, p = prefs(S.c), t = j.title || "", comps = [];
    const fam = (p.roles || []).find(id => FAM[id] && FAM[id].test(t));
    comps.push({ k: "Role type", max: 30, got: fam ? 30 : /engineer|developer|software|programmer/i.test(t) ? 14 : 0, note: fam ? `${fam} role` : "Not a chosen role type" });
    const lv = levelOf(t);
    comps.push({ k: "Level", max: 20, got: levelPts(p.level, lv), note: lv === "exec" ? "Management or staff+ level" : `Reads as ${lv}` });
    if (j.location) { const hit = (p.places || []).find(pl => CITY[pl] && CITY[pl].test(j.location)); comps.push({ k: "Place", max: 15, got: hit ? 15 : /india/i.test(j.location) ? 8 : 0, note: hit ? `In ${hit}` : /india/i.test(j.location) ? "In India" : "Outside your places" }); }
    const n = contactsOf(S.c, j.company).length;
    if (n) comps.push({ k: "Contacts", max: 10, got: 10, note: `${plural(n, "contact")} you added` });
    comps.push({ k: "Listing link", max: 5, got: urlOf(j) ? 5 : 0, note: urlOf(j) ? "Source link ready" : "No listing link yet" });
    const score = Math.max(0, Math.min(100, Math.round(comps.reduce((a, x) => a + x.got, 0) / comps.reduce((a, x) => a + x.max, 0) * 92)));
    return (r.fit = { score, comps, exec: lv === "exec" });
  }

  /* ---------- rows and stages ---------- */
  function build() {
    const c = S.c;
    S.rows = jobsOf(c).map(j => {
      const k = keyOf(c, j), loc = S.st.jobs[k] || {};
      const status = STATUSES.includes(loc.status) ? loc.status : STATUSES.includes(j.status) ? j.status : "Not started";
      return { j, k, loc, status, applied: loc.appliedAt || j.appliedAt || "", skipped: !!meta().skips[k], fit: null };
    });
  }
  const STAGES = [["inbox", "Inbox", "1"], ["Watching", "Watching", "2"], ["Applied", "Applied", "3"], ["Interviewing", "Interviewing", "4"], ["Offer", "Offer", "5"], ["Closed", "Closed", "6"], ["skipped", "Skipped", "7"]];
  function inStage(r, stage) {
    if (stage === "skipped") return r.skipped;
    if (r.skipped) return false;
    if (stage === "inbox") return r.status === "Not started" && r.j.category !== "Historical / wave role" && inScope(r.j, S.c) && fit(r).score >= 50 && !fit(r).exec;
    return r.status === stage;
  }
  const followupDue = r => r.status === "Applied" && r.applied && dayDiff(r.applied, today()) >= 4 && !meta().followups[r.k]?.done;
  function visible() {
    const q = norm(S.q);
    let out = S.rows.filter(r => inStage(r, S.stage) && (!S.fu || followupDue(r)) && (!q || norm(`${r.j.company} ${r.j.title} ${r.j.location} ${r.j.notes} ${(r.j.tags || []).join(" ")}`).includes(q)));
    out.sort(S.stage === "inbox" ? (a, b) => fit(b).score - fit(a).score : (a, b) => (b.applied || "").localeCompare(a.applied || "") || a.j.company.localeCompare(b.j.company));
    return out;
  }

  /* ---------- toasts ---------- */
  function toast(msg, undo) {
    const t = document.createElement("div"); t.className = "toast";
    t.innerHTML = `<span>${esc(msg)}</span>${undo ? "<button type='button'>Undo</button>" : ""}`;
    $("#toasts").appendChild(t);
    if (undo) $("button", t).addEventListener("click", () => { undo(); t.remove(); });
    setTimeout(() => t.remove(), undo ? 6500 : 3200);
  }

  /* ---------- render ---------- */
  function render() {
    build();
    $("#cand").innerHTML = ["Vaanya", "Vrinda"].map(n => `<button type="button" data-c="${n}" aria-pressed="${n === S.c}">${n}</button>`).join("");
    renderBrief(); renderRail(); renderList(); renderDetail();
  }
  function renderBrief() {
    const w = weekStart(), rows = S.rows.filter(r => !r.skipped);
    const inbox = rows.filter(r => inStage(r, "inbox")).length;
    const week = rows.filter(r => ["Applied", "Interviewing", "Offer"].includes(r.status) && r.applied >= w).length;
    const due = rows.filter(followupDue).length, asks = rows.filter(r => r.status === "Watching" && (r.j.tags || []).includes("Referral asked")).length;
    $("#brief").innerHTML = `
      <button class="tile hot" data-go="inbox"><b>${inbox}</b><span>fit roles waiting<br>in your inbox</span></button>
      <div class="tile cool"><b>${week}</b><span>applications<br>this week</span></div>
      <button class="tile ${due ? "hot" : ""}" data-go="fu"><b>${due}</b><span>follow-ups due<br>(applied 4+ days ago)</span></button>
      <button class="tile" data-go="Watching"><b>${asks}</b><span>referral asks<br>you have sent</span></button>`;
    $$(".tile[data-go]").forEach(b => b.style.cursor = "pointer");
  }
  function renderRail() {
    $("#rail").innerHTML = `<h6>Pipeline</h6>` + STAGES.map(([id, label, n]) => `<button class="stage" data-stage="${id}" aria-current="${S.stage === id}"><i>${n}</i>${label}<em>${S.rows.filter(r => inStage(r, id)).length}</em></button>`).join("")
      + `<div class="rail-foot"><span>Scope: ${mission(S.c).started ? (mission(S.c).any ? "any company" : plural(mission(S.c).companies.length, "company", "companies")) : "everything"}${mission(S.c).minLPA ? ` · min ${mission(S.c).minLPA} LPA` : ""}</span><span><kbd>j</kbd> <kbd>k</kbd> move · <kbd>?</kbd> help</span></div>`;
  }
  function badgeFor(r) {
    const out = [];
    const v = meta().verify[r.k]?.status;
    if (v === "ok") out.push(["✓ live", "ok"]); else if (v === "dead" || v === "closed") out.push(["✗ " + v, "bad"]); else if (v === "manual") out.push(["check by hand", "warn"]);
    for (const t of (r.j.tags || []).slice(0, 2)) out.push([t, /referr|asked/i.test(t) ? "ref" : /reject|not |deadline/i.test(t) ? "bad" : ""]);
    if (r.status === "Applied" && r.applied) out.push([`applied ${dayDiff(r.applied, today())}d ago`, followupDue(r) ? "warn" : ""]);
    return out.map(([t, k]) => `<span class="tag ${k}">${esc(t)}</span>`).join("");
  }
  function renderList() {
    const rows = visible();
    if (!rows.find(r => r.k === S.sel)) S.sel = rows[0]?.k || null;
    const head = S.fu ? `<div class="empty" style="padding:10px 16px;text-align:left;border-bottom:1px solid var(--line)"><button class="btn ghost" data-clearfu>Showing follow-ups due ✕</button></div>` : "";
    $("#list").innerHTML = head + (rows.length ? rows.slice(0, 400).map(r => {
      const f = S.stage === "inbox" ? fit(r).score : null;
      return `<div class="row" role="option" data-k="${esc(r.k)}" aria-selected="${r.k === S.sel}"><span class="co">${esc(r.j.company)}</span><span class="ti">${esc(r.j.title)}</span>${f != null ? `<span class="fit ${f >= 80 ? "hi" : f >= 65 ? "mid" : ""}">${f}</span>` : ""}<div class="meta"><span class="tag">${esc(r.j.location || "location n/a")}</span>${badgeFor(r)}</div></div>`;
    }).join("") : `<div class="empty"><b>${S.stage === "inbox" ? "Inbox zero" : "Nothing here"}</b>${S.stage === "inbox" ? "No more fit roles in your scope. Widen the scope or sync your sheets." : "Move roles here from the detail pane."}</div>`);
    $(`.row[aria-selected="true"]`, $("#list"))?.scrollIntoView({ block: "nearest" });
  }
  const rowOf = k => S.rows.find(r => r.k === k);

  function draftText(ct, j) {
    const first = (ct.name || "").trim().split(/\s+/)[0] || "there", role = j.title, co = j.company, cat = catOf(ct);
    if (cat === "hr") return `Hi ${first}, I came across the ${role} opening at ${co} and it looks like a strong match for my background. Could you point me to the right process, or share my profile with the hiring team? Happy to send my resume. Thank you!\n${S.c}`;
    if (cat === "alumni") return `Hi ${first}, fellow alum here. I'm looking at the ${role} role at ${co}. Would you be open to a 10-minute chat about the team, and a referral if it feels like a fit?\nThanks, ${S.c}`;
    return `Hi ${first}, I'm exploring the ${role} role at ${co}. Could I ask what the team works on and what the interview looks like?\nThanks, ${S.c}`;
  }
  const drafts = {};
  function renderDetail() {
    const r = rowOf(S.sel), el = $("#detail");
    if (!r) { el.innerHTML = `<div class="empty"><b>Select a role</b>Use <kbd>j</kbd> / <kbd>k</kbd> to move through the list.</div>`; return; }
    const j = r.j, f = fit(r), url = urlOf(j), v = meta().verify[r.k], people = contactsOf(S.c, j.company);
    const groups = { hr: [], eng: [], alumni: [], other: [] }; people.forEach(p => groups[catOf(p)].push(p));
    const pay = payLPA(j.compensation) ? `${j.compensation}` : "Not published";
    el.innerHTML = `
      <button class="btn ghost back" data-back>← Back</button>
      <div class="d-head"><div class="d-co">${esc(j.company)}</div><h1>${esc(j.title)}</h1>
        <div class="d-sub"><span>${esc(j.location || "Location not listed")}</span><span>Pay: ${esc(pay)}</span>${j.experience ? `<span>${esc(j.experience)}</span>` : ""}<span>${esc(j.category || "Role")}</span></div></div>
      <div class="d-actions">
        ${url ? `<a class="btn primary" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Open listing <kbd>o</kbd></a>` : `<span class="tag warn">No listing link yet</span>`}
        <button class="btn" data-act="watch">Watch <kbd>w</kbd></button>
        <button class="btn ok" data-act="applied">Mark applied <kbd>a</kbd></button>
        <button class="btn danger" data-act="skip">Skip <kbd>s</kbd></button>
        ${url ? `<button class="btn" data-act="verify">${v ? "Re-verify" : "Verify link"}${v ? ` · ${esc(v.status)}` : ""}</button>` : ""}
      </div>
      <div class="stagebar" role="group" aria-label="Stage">${STATUSES.map(s => `<button data-status="${s}" aria-pressed="${s === r.status}">${s}</button>`).join("")}</div>

      <div class="sec"><h3>Fit ${f.score}</h3><div class="card">${f.comps.map(c => `<div class="fitrow"><span>${esc(c.k)}</span><div class="bar2"><i style="width:${c.max ? Math.round(c.got / c.max * 100) : 0}%"></i></div><small>${c.got}/${c.max}</small></div><div class="fitnote" style="margin:-2px 0 4px 140px">${esc(c.note)}</div>`).join("")}
        <p class="fitnote">A transparent local estimate. The sheets hold no job description, so it is capped. It never guesses salary.</p></div></div>

      ${(j.notes || (j.tags || []).length) ? `<div class="sec"><h3>From your sheet</h3><div class="sheetnote"><b>read-only</b>${(j.tags || []).map(t => `<span class="tag">${esc(t)}</span> `).join("")}${j.notes ? `<div>${esc(j.notes)}</div>` : ""}</div></div>` : ""}

      <div class="sec"><h3>Your tracking</h3>
        <label class="f">Date applied<input type="date" data-field="appliedAt" value="${esc(r.applied)}"></label>
        <label class="f">Next step<input type="text" data-field="nextStep" value="${esc(r.loc.nextStep || "")}" placeholder="Follow up with…"></label>
        <label class="f">Notes<textarea data-field="applicationNotes" placeholder="Interview notes, referral context…">${esc(r.loc.applicationNotes || "")}</textarea></label></div>

      <div class="sec"><h3>Reach out</h3>${people.length ? `<div class="people">${["hr", "eng", "alumni", "other"].flatMap(g => groups[g].map(p => {
        const rk = `${S.c}|${norm(j.company)}|${norm(p.name)}`, done = meta().reach[rk], open = drafts[rk] !== undefined;
        return `<div class="person"><div class="row2"><div><b>${esc(p.name)}</b><small>${CATLABEL[g]}${p.title ? " · " + esc(p.title) : ""}</small></div>${done ? `<span class="tag ok">reached out ${dayDiff(done.at, today())}d ago</span>` : ""}<button class="btn" data-draft="${esc(rk)}" data-name="${esc(p.name)}">${open ? "Hide" : "Draft"}</button></div>
          ${open ? `<div class="draft"><textarea data-draftbox="${esc(rk)}">${esc(drafts[rk])}</textarea><div style="display:flex;gap:6px"><button class="btn primary" data-copy="${esc(rk)}">Copy</button><button class="btn" data-sent="${esc(rk)}">I sent it</button></div><small class="fitnote">Orbit never sends this. Copy it, edit it, send it yourself.</small></div>` : ""}</div>`; })).join("")}</div>` : `<div class="card fitnote">No contact for ${esc(j.company)} yet. Add one to your sheet, or use the listing link.</div>`}</div>`;
  }

  /* ---------- actions ---------- */
  function setStatus(r, status, msg) {
    const old = S.st.jobs[r.k] ? { ...S.st.jobs[r.k] } : null;
    const next = { ...(S.st.jobs[r.k] || {}), candidate: S.c, status, updatedAt: new Date().toISOString() };
    if (status === "Applied") { next.appliedAt = next.appliedAt || r.applied || today(); next.nextStep = next.nextStep || "Follow up in 4 days"; }
    S.st.jobs[r.k] = next; save(); render();
    toast(msg || `Moved to ${status}`, () => { old ? S.st.jobs[r.k] = old : delete S.st.jobs[r.k]; save(); render(); });
  }
  function skip(r) {
    meta().skips[r.k] = { c: S.c, reason: "Not for me", at: today() }; save(); render();
    toast("Skipped. It stays in Skipped if you change your mind.", () => { delete meta().skips[r.k]; save(); render(); });
  }
  async function verify(r) {
    const url = urlOf(r.j); if (!url) return;
    toast("Checking the link…");
    try {
      const res = await fetch("/api/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ urls: [url] }) });
      const out = (await res.json()).results?.[url];
      meta().verify[r.k] = { ...(out || { status: "error" }), at: today() }; save(); render();
      toast(out?.status === "ok" ? "Link is live" : `Result: ${out?.status || "error"}`);
    } catch (_) { toast("Verifier unavailable"); }
  }
  const move = d => { const rows = visible(), i = rows.findIndex(r => r.k === S.sel); const n = rows[Math.max(0, Math.min(rows.length - 1, (i < 0 ? 0 : i) + d))]; if (n) { S.sel = n.k; renderList(); renderDetail(); } };
  const setStage = id => { S.stage = id; S.fu = false; S.sel = null; render(); };

  /* ---------- scope drawer ---------- */
  function openScope() {
    const c = S.c, m = mission(c), p = profile(c);
    const names = new Map(); (p?.companies || []).forEach(x => names.set(norm(x.name), { name: x.name, jobs: 0, people: 0 }));
    jobsOf(c).forEach(j => { const k = norm(j.company); if (!names.has(k)) names.set(k, { name: j.company, jobs: 0, people: 0 }); names.get(k).jobs++; });
    names.forEach(e => e.people = contactsOf(c, e.name).length);
    S.scope = { sel: new Set(m.companies), any: m.any, min: m.minLPA || "", unk: m.unknownPay !== false, q: "", list: [...names.entries()].sort((a, b) => b[1].jobs - a[1].jobs || b[1].people - a[1].people) };
    drawScope(); $("#scope").classList.remove("hidden"); $("#backdrop").classList.remove("hidden");
  }
  function drawScope() {
    const sc = S.scope, q = norm(sc.q), list = sc.list.filter(([k, e]) => !q || k.includes(q)).slice(0, 120);
    $("#scope").innerHTML = `<header><h2>Scope for ${esc(S.c)}</h2><button class="btn ghost" data-close>Close ✕</button></header>
      <div class="body"><div class="modes"><button class="mode" data-mode="pick" aria-pressed="${!sc.any}"><b>Choose companies</b><small>Only these show in your inbox</small></button><button class="mode" data-mode="any" aria-pressed="${sc.any}"><b>Open to any company</b><small>As long as the pay floor is met</small></button></div>
        <label class="f">Minimum fixed pay (LPA), only applied when a listing shows pay<input type="number" data-min value="${esc(sc.min)}" placeholder="35"></label>
        <label class="f" style="flex-direction:row;display:flex;gap:8px;align-items:center"><input type="checkbox" data-unk ${sc.unk ? "checked" : ""} style="width:auto"> Keep roles that don't publish pay</label>
        ${sc.any ? "" : `<label class="f">Search companies<input type="text" data-scopeq value="${esc(sc.q)}" placeholder="Search…"></label><div class="cogrid">${list.map(([k, e]) => `<button class="co-opt" data-co="${esc(k)}" aria-pressed="${sc.sel.has(k)}"><i>${sc.sel.has(k) ? "✓" : ""}</i><span>${esc(e.name)}</span><small>${e.jobs} · ${e.people}p</small></button>`).join("")}</div>`}</div>
      <footer><span class="fitnote">${sc.any ? "Any company" : plural(sc.sel.size, "company", "companies") + " selected"}</span><div style="display:flex;gap:6px"><button class="btn" data-clear>Clear</button><button class="btn primary" data-apply ${sc.any || sc.sel.size ? "" : "disabled"}>Apply scope</button></div></footer>`;
  }
  const closeScope = () => { $("#scope").classList.add("hidden"); $("#backdrop").classList.add("hidden"); S.scope = null; };

  /* ---------- events ---------- */
  document.addEventListener("click", e => {
    const t = e.target, q = sel => t.closest(sel);
    if (q("[data-c]") && q("#cand")) { S.c = q("[data-c]").dataset.c; localStorage.setItem("orbit.candidate", S.c); S.sel = null; render(); return; }
    if (q("[data-stage]")) return setStage(q("[data-stage]").dataset.stage);
    if (q(".tile[data-go]")) { const g = q(".tile[data-go]").dataset.go; if (g === "fu") { S.stage = "Applied"; S.fu = true; S.sel = null; render(); } else setStage(g); return; }
    if (q("[data-clearfu]")) { S.fu = false; render(); return; }
    const row = q(".row[data-k]"); if (row) { S.sel = row.dataset.k; renderList(); renderDetail(); $("#detail").classList.add("open"); return; }
    if (q("[data-back]")) { $("#detail").classList.remove("open"); return; }
    const r = rowOf(S.sel);
    const act = q("[data-act]")?.dataset.act;
    if (act && r) { if (act === "watch") setStatus(r, "Watching"); else if (act === "applied") setStatus(r, "Applied", "Marked applied. Orbit only records what you tell it."); else if (act === "skip") skip(r); else if (act === "verify") verify(r); return; }
    const st = q("[data-status]"); if (st && r) return setStatus(r, st.dataset.status);
    const dr = q("[data-draft]"); if (dr && r) { const k = dr.dataset.draft; if (drafts[k] !== undefined) delete drafts[k]; else drafts[k] = draftText(contactsOf(S.c, r.j.company).find(p => p.name === dr.dataset.name) || { name: dr.dataset.name }, r.j); renderDetail(); return; }
    const cp = q("[data-copy]"); if (cp) { navigator.clipboard?.writeText($(`[data-draftbox="${CSS.escape(cp.dataset.copy)}"]`)?.value || "").then(() => toast("Copied. Paste it into your own message.")); return; }
    const sent = q("[data-sent]"); if (sent) { meta().reach[sent.dataset.sent] = { at: today(), job: S.sel }; save(); renderDetail(); toast("Marked as reached out"); return; }
    if (q("#scope-btn")) return openScope();
    if (q("#refresh-btn")) { toast("Re-reading your sheets…"); fetch("/api/refresh", { method: "POST" }).then(() => load()).then(() => toast("Synced")).catch(() => toast("Sync failed")); return; }
    if (q("#theme-btn")) { const n = document.documentElement.dataset.theme === "dark" ? "light" : "dark"; document.documentElement.dataset.theme = n; localStorage.setItem("orbit.v2.theme", n); return; }
    if (q("#help-btn")) return showHelp();
    if (q("[data-close]") || t.id === "backdrop") return closeScope();
    if (S.scope) {
      const mode = q("[data-mode]"); if (mode) { S.scope.any = mode.dataset.mode === "any"; return drawScope(); }
      const co = q("[data-co]"); if (co) { const k = co.dataset.co; S.scope.sel.has(k) ? S.scope.sel.delete(k) : S.scope.sel.add(k); return drawScope(); }
      if (q("[data-clear]")) { S.scope.sel.clear(); return drawScope(); }
      if (q("[data-apply]")) { meta().mission[S.c] = { companies: [...S.scope.sel], any: S.scope.any, minLPA: parseFloat(S.scope.min) || 0, unknownPay: S.scope.unk, started: today() }; save(); closeScope(); S.stage = "inbox"; render(); toast("Scope applied"); return; }
    }
    if (t.closest("#help") && !t.closest(".box")) $("#help").classList.add("hidden");
  });
  document.addEventListener("input", e => {
    const t = e.target;
    if (t.id === "q") { S.q = t.value; renderList(); renderDetail(); }
    else if (t.matches("[data-scopeq]")) { S.scope.q = t.value; const pos = t.selectionStart; drawScope(); const n = $("[data-scopeq]"); n.focus(); n.setSelectionRange(pos, pos); }
    else if (t.matches("[data-min]")) S.scope.min = t.value;
    else if (t.matches("[data-unk]")) S.scope.unk = t.checked;
    else if (t.matches("[data-draftbox]")) drafts[t.dataset.draftbox] = t.value;
  });
  document.addEventListener("change", e => {
    const t = e.target, r = rowOf(S.sel);
    if (t.matches("[data-field]") && r) { S.st.jobs[r.k] = { ...(S.st.jobs[r.k] || {}), candidate: S.c, [t.dataset.field]: t.value.trim().slice(0, 4000), updatedAt: new Date().toISOString() }; save(); toast("Saved"); }
  });
  function showHelp() {
    $("#help").innerHTML = `<div class="box"><h2>Keyboard shortcuts</h2><div class="keys"><span><kbd>j</kbd> <kbd>k</kbd></span>Next / previous role<span><kbd>o</kbd></span>Open the listing<span><kbd>w</kbd></span>Watch<span><kbd>a</kbd></span>Mark applied (undo available)<span><kbd>s</kbd></span>Skip<span><kbd>1</kbd>–<kbd>7</kbd></span>Jump to a pipeline stage<span><kbd>/</kbd></span>Filter<span><kbd>c</kbd></span>Open scope<span><kbd>?</kbd></span>This help</div></div>`;
    $("#help").classList.remove("hidden");
  }
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") { $("#help").classList.add("hidden"); if (S.scope) closeScope(); $("#detail").classList.remove("open"); if (/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) document.activeElement.blur(); return; }
    if (/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) || e.metaKey || e.ctrlKey || e.altKey || S.scope) return;
    const r = rowOf(S.sel), k = e.key;
    if (k === "j" || k === "ArrowDown") { e.preventDefault(); move(1); }
    else if (k === "k" || k === "ArrowUp") { e.preventDefault(); move(-1); }
    else if (k === "/") { e.preventDefault(); $("#q").focus(); }
    else if (k === "?") showHelp();
    else if (k === "c") openScope();
    else if (/^[1-7]$/.test(k)) setStage(STAGES[+k - 1][0]);
    else if (r && k === "o") { const u = urlOf(r.j); if (u) window.open(u, "_blank", "noopener,noreferrer"); }
    else if (r && k === "w") setStatus(r, "Watching");
    else if (r && k === "a") setStatus(r, "Applied", "Marked applied. Orbit only records what you tell it.");
    else if (r && k === "s") skip(r);
  });

  async function load() {
    const [d, s] = await Promise.all([fetch("/api/data", { cache: "no-store" }).then(r => r.json()), fetch("/api/state", { cache: "no-store" }).then(r => r.json())]);
    S.data = d; S.st = s; meta(); render();
  }
  load().catch(err => { console.error(err); $("#list").innerHTML = `<div class="empty"><b>Could not load data</b>Run <code>python3 website/export_data.py</code> and refresh.</div>`; });
})();
