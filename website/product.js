/* Orbit product layer: Today view, explainable fit, kanban board, goals & streaks, follow-up reminders,
   first-run tuning, shift report, command palette, dark mode.
   Everything is local. Orbit never contacts anyone: "Apply" only opens the listing, and a status
   changes only when the user confirms. State lives in the same dashboard_state.json via app.js. */
(() => {
  const A = window.OrbitApp;
  if (!A) return;
  const R = window.OrbitRobots;
  const S = A.state, esc = A.esc;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const pad = n => String(n).padStart(2, "0");
  const fmtD = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const today = () => A.nowISODate();
  const dayDiff = (a, b) => Math.round((new Date(b + "T00:00:00") - new Date(a + "T00:00:00")) / 864e5);
  const addDays = (iso, n) => { const d = new Date(iso + "T00:00:00"); d.setDate(d.getDate() + n); return fmtD(d); };
  const weekStart = () => { const d = new Date(); const k = (d.getDay() + 6) % 7; d.setDate(d.getDate() - k); return fmtD(d); };
  const plural = (n, a, b) => `${n} ${n === 1 ? a : b || a + "s"}`;
  const hash = str => { let h = 2166136261; for (const ch of str) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); } return (h >>> 0) / 4294967295; };

  /* ---------- persisted product state (inside meta, so the server accepts it unchanged) ---------- */
  const meta = () => {
    const m = (S.saved.meta ||= {});
    for (const k of ["prefs", "goals", "skips", "today", "milestones", "followups", "onboarded", "mission", "verify", "reach"]) m[k] ||= {};
    m.activity ||= [];
    return m;
  };
  let quiet = false;
  const save = () => { quiet = true; try { A.persist(); } finally { quiet = false; } };

  /* ---------- preferences ---------- */
  const FAM = {
    backend: { label: "Backend", re: /backend|back-end|server[- ]side|\bapi\b|platform|distributed|infrastructure|systems?\b/i },
    sde: { label: "SDE / Software", re: /\bsde\b|software (development )?engineer|software developer|\bswe\b|member of technical staff|\bmts\b|programmer/i },
    fullstack: { label: "Full-stack", re: /full[- ]?stack/i },
    data: { label: "Data / ML", re: /data (engineer|scientist|analyst)|machine learning|\bml\b|\bai\b|analytics/i },
    frontend: { label: "Frontend", re: /front[- ]?end|\bui\b|react|web developer/i },
    devops: { label: "DevOps / SRE", re: /devops|\bsre\b|reliability|cloud|security engineer/i },
    quant: { label: "Quant / low-latency", re: /quant|low[- ]?latency|trading|hft/i },
  };
  const PLACES = ["Bengaluru", "Hyderabad", "Pune", "Delhi NCR", "Mumbai", "Chennai", "Kolkata", "Remote", "Anywhere in India"];
  const CITY = {
    Bengaluru: /bengaluru|bangalore|karnataka/i, Hyderabad: /hyderabad|telangana/i, Pune: /\bpune\b/i,
    "Delhi NCR": /delhi|\bncr\b|gurgaon|gurugram|noida|faridabad|ghaziabad|haryana/i, Mumbai: /mumbai|thane|navi mumbai/i,
    Chennai: /chennai|tamil nadu/i, Kolkata: /kolkata|calcutta/i, Remote: /remote|work from home|\bwfh\b|anywhere/i,
  };
  const LEVELS = { entry: "Early career (grad / SDE I)", mid: "SDE II (some SDE III)", senior: "Senior / SDE III+" };
  const DEFAULTS = {
    Vaanya: { roles: ["sde", "backend", "fullstack"], level: "entry", places: ["Bengaluru", "Hyderabad", "Pune", "Delhi NCR", "Remote"], skills: [], payFloor: 0, goal: 5 },
    Vrinda: { roles: ["backend", "sde"], level: "mid", places: ["Bengaluru", "Hyderabad", "Pune", "Delhi NCR", "Remote"], skills: [], payFloor: 0, goal: 5 },
  };
  const mission = c => ({ companies: [], any: false, minLPA: 0, unknownPay: true, started: null, ...(meta().mission[c] || {}) });
  const prefs = c => { const b = { ...(DEFAULTS[c] || DEFAULTS.Vrinda), ...(meta().prefs[c] || {}) }; const ms = mission(c); if (ms.minLPA) b.payFloor = ms.minLPA; return b; };
  const inScope = (job, c) => { const m = mission(c); return !m.started || m.any || m.companies.includes(A.norm(job.company)); };
  const payState = (job, c) => { const lpa = payLPA(job.compensation), f = mission(c).minLPA || 0; return !lpa ? "unknown" : (!f || lpa >= f ? "ok" : "below"); };
  const payOk = (job, c) => { const s = payState(job, c); return s === "ok" || (s === "unknown" && mission(c).unknownPay); };

  /* ---------- explainable fit: a local heuristic, not the Analyst agent's score ---------- */
  const LVRE = [
    ["exec", /director|\bvp\b|vice president|head of|manager|principal|distinguished|fellow|chief/i],
    ["senior", /senior|\bsr\b|staff|\blead\b|architect|\bsde[\s-]*(iii|3)\b|engineer[\s-]*(iii|3)\b|\b(iii|iv)\b/i],
    ["entry", /graduate|intern|trainee|fresher|entry|new grad|campus|associate|junior|\bjr\b|apprentice|early career|university|\bsde[\s-]*(i|1)\b|engineer[\s-]*(i|1)\b/i],
  ];
  const levelOf = t => (LVRE.find(([, re]) => re.test(t)) || ["mid"])[0];
  const levelPts = (pref, lv) => {
    if (lv === "exec") return 0;
    if (pref === lv) return 20;
    const pair = `${pref}>${lv}`;
    return { "mid>senior": 12, "senior>mid": 12, "entry>mid": 10, "mid>entry": 6, "senior>entry": 0, "entry>senior": 0 }[pair] ?? 8;
  };
  const cityOf = loc => Object.keys(CITY).find(k => CITY[k].test(loc || ""));
  const payLPA = s => { const m = String(s || "").match(/(\d+(?:\.\d+)?)\s*(?:-|to|–)?\s*(\d+(?:\.\d+)?)?\s*(lpa|lakh|l\b)/i); return m ? parseFloat(m[2] || m[1]) : null; };
  const labelOf = n => n >= 80 ? "Strong" : n >= 65 ? "Potential" : n >= 50 ? "Stretch" : "Low";

  function learned(c) {
    const sk = Object.values(meta().skips).filter(x => x.c === c);
    const count = (field, val) => sk.filter(x => x[field] === val && x.reason === { city: "Location", lv: "Level", fam: "Stack", co: "Pay" }[field]).length;
    return { count, any: sk.length };
  }
  function fit(job, c, L = learned(c)) {
    const p = prefs(c), title = job.title || "", comps = [];
    const text = `${title} ${job.notes || ""}`;
    const fams = p.roles.filter(id => FAM[id] && FAM[id].re.test(title));
    comps.push({ k: "Role type", max: 30, got: fams.length ? 30 : /engineer|developer|software|programmer/i.test(title) ? 14 : 0,
      note: fams.length ? `${FAM[fams[0]].label} role` : "Not one of your chosen role types" });
    const lv = levelOf(title);
    comps.push({ k: "Level", max: 20, got: levelPts(p.level, lv), note: lv === "exec" ? "Looks like a management/staff+ level" : `Reads as ${LEVELS[lv] ? LEVELS[lv].split(" (")[0].toLowerCase() : lv}` });
    const city = cityOf(job.location);
    if (job.location) {
      const hit = p.places.find(pl => CITY[pl] && CITY[pl].test(job.location));
      const anyIndia = p.places.includes("Anywhere in India") && /india/i.test(job.location);
      comps.push({ k: "Place", max: 15, got: hit ? 15 : anyIndia ? 12 : 0, note: hit ? `In ${hit}` : anyIndia ? "In India" : "Outside your chosen places" });
    }
    if (p.skills.length) {
      const hits = p.skills.filter(s => new RegExp(`\\b${s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i").test(text));
      comps.push({ k: "Skills", max: 10, got: Math.min(10, hits.length * 5), note: hits.length ? `Mentions ${hits.slice(0, 3).join(", ")}` : "No skill keywords in the title or notes" });
    }
    const lpa = payLPA(job.compensation);
    if (p.payFloor && lpa) comps.push({ k: "Pay", max: 10, got: lpa >= p.payFloor ? 10 : 0, note: lpa >= p.payFloor ? `Listed ${lpa} LPA, above your floor` : `Listed ${lpa} LPA, below your floor` });
    const n = A.getContacts(c, job.company).length;
    if (n) comps.push({ k: "Contacts", max: 10, got: 10, note: `${plural(n, "contact")} you added` });
    comps.push({ k: "Listing link", max: 5, got: A.jobUrl(job) ? 5 : 0, note: A.jobUrl(job) ? "Source link ready" : "No listing link yet" });
    if (A.isHistorical(job)) comps.push({ k: "Freshness", max: 5, got: 0, note: "Older wave role" });
    else if (A.isNew(job, c)) comps.push({ k: "Freshness", max: 5, got: 5, note: "Newly added" });
    // No job description in the sheets, so cap confidence unless skills or pay give extra evidence.
    const evidence = p.skills.length || (p.payFloor && lpa) ? 1 : 0.92;
    let score = Math.round(comps.reduce((a, x) => a + x.got, 0) / comps.reduce((a, x) => a + x.max, 0) * 100 * evidence);
    const pen = Math.min(12, L.count("city", city) * 4) + Math.min(12, L.count("lv", lv) * 4) + Math.min(12, (fams[0] ? L.count("fam", fams[0]) : 0) * 4) + Math.min(10, L.count("co", A.norm(job.company)) * 5);
    if (pen) { comps.push({ k: "Learned from your skips", max: 0, got: -pen, note: "Similar roles you passed on" }); score -= pen; }
    score = Math.max(0, Math.min(100, score));
    return { score, label: labelOf(score), comps, lv, city, fam: fams[0] || null, exec: lv === "exec" };
  }

  const isTracked = (job, c) => {
    const st = A.jobState(job, c);
    return A.jobStatus(job, c) !== "Not started" || !!(st.appliedAt || st.applicationNotes || st.nextStep) || !!job.manual;
  };
  function ranked(c) {
    const L = learned(c), d = today(), sk = meta().skips;
    return A.allJobs(c)
      .filter(j => !isTracked(j, c) && !sk[A.roleKey(c, j)] && !A.isHistorical(j) && inScope(j, c) && payOk(j, c))
      .map(j => ({ job: j, key: A.roleKey(c, j), fit: fit(j, c, L) }))
      .filter(r => !r.fit.exec)
      .sort((a, b) => (Math.round(b.fit.score / 4) - Math.round(a.fit.score / 4)) || (hash(a.key + d) - hash(b.key + d)));
  }
  function picksFor(c) {
    const m = meta(), d = today();
    let rec = m.today[c];
    if (!rec || rec.date !== d) rec = m.today[c] = { date: d, keys: [], extra: 0 };
    const all = ranked(c), byKey = new Map(all.map(r => [r.key, r]));
    let keys = rec.keys.filter(k => byKey.has(k));
    const want = 5 + (rec.extra || 0);
    for (const r of all) { if (keys.length >= want) break; if (!keys.includes(r.key)) keys.push(r.key); }
    if (keys.length !== rec.keys.length || keys.some((k, i) => k !== rec.keys[i])) { rec.keys = keys; save(); }
    return keys.map(k => byKey.get(k)).filter(Boolean);
  }

  /* ---------- activity, goals, streak, milestones ---------- */
  const log = (c, type, key) => { const a = meta().activity; a.push({ d: today(), t: type, c, k: key }); if (a.length > 600) a.splice(0, a.length - 600); };
  /* The user's sheets already hold history (statuses, dates, notes). Treat them as first-class data. */
  const appliedOf = (j, c) => A.jobState(j, c).appliedAt || j.appliedAt || "";
  const isApplied = (j, c) => ["Applied", "Interviewing", "Offer"].includes(A.jobStatus(j, c));
  const appliedTotal = c => A.allJobs(c).filter(j => isApplied(j, c)).length;
  function activeDays(c) {
    const days = new Set(meta().activity.filter(x => x.c === c).map(x => x.d));
    A.allJobs(c).forEach(j => { const d = appliedOf(j, c); if (d && isApplied(j, c)) days.add(d); });
    return days;
  }
  function streak(c) {
    const days = activeDays(c);
    let d = today(), n = 0, gap = 0;
    if (!days.has(d)) { d = addDays(d, -1); }
    if (!days.has(d) && !days.has(addDays(d, -1))) return { n: 0, active: false };
    for (let i = 0; i < 400; i++) {
      if (days.has(d)) { n++; gap = 0; } else { gap++; if (gap > 2) break; }  // up to two rest days never break a streak
      d = addDays(d, -1);
    }
    return { n, active: days.has(today()) };
  }
  const goalOf = c => meta().goals[c] || prefs(c).goal || 5;
  const appliedThisWeek = c => { const w = weekStart(); return A.allJobs(c).filter(j => isApplied(j, c) && appliedOf(j, c) >= w).length; };

  const MILESTONES = {
    first_apply: ["First application!", "That's the hardest one. Orbit-bot is doing a little dance."],
    apply_5: ["Five applications", "Steady and real progress. Look at that pipeline."],
    first_interview: ["An interview!", "They noticed you. Time to prep and breathe."],
    first_offer: ["An offer!", "All that follow-through paid off. Congratulations!"],
  };
  function milestone(c, id, extra) {
    const m = meta().milestones, key = `${c}:${id}`;
    if (m[key]) return false;
    m[key] = today(); const [t, s] = extra || MILESTONES[id]; celebrate(t, s, c); return true;
  }
  function afterStatus(c, status) {
    if (status === "Applied") {
      const total = appliedTotal(c);
      if (total === 1) milestone(c, "first_apply");
      if (total === 5) milestone(c, "apply_5");
      if (total === 25) milestone(c, "apply_25", ["25 applications", "That is real follow-through. Keep the rhythm kind to yourself."]);
      const g = goalOf(c), w = appliedThisWeek(c);
      if (w >= g) milestone(c, `goal_${weekStart()}`, ["Weekly goal reached", `${w} applications this week. You can rest easy. Streak stays warm.`]);
    }
    if (status === "Interviewing") milestone(c, "first_interview");
    if (status === "Offer") milestone(c, "first_offer");
  }

  function setStatus(job, status, c = S.candidate, opts = {}) {
    const key = A.roleKey(c, job), old = A.jobState(job, c);
    const next = { ...old, candidate: c, status, updatedAt: new Date().toISOString() };
    if (status === "Applied") {
      next.appliedAt = old.appliedAt || today();
      if (!old.nextStep) next.nextStep = "Follow up in 4 days";
    }
    S.saved.jobs[key] = next;
    log(c, status === "Watching" ? "watch" : "move", key);
    save();
    if (!opts.silent) afterStatus(c, status);
  }

  /* ---------- toasts + celebration ---------- */
  function toastHost() { let h = $("#ob-toasts"); if (!h) { h = document.createElement("div"); h.id = "ob-toasts"; h.setAttribute("aria-live", "polite"); document.body.appendChild(h); } return h; }
  function toast(msg, o = {}) {
    const t = document.createElement("div"); t.className = "ob-toast" + (o.cheer ? " cheer" : "");
    const bot = o.cheer && R ? `<svg viewBox="-70 -200 140 210" class="ob-toast-bot" aria-hidden="true">${R.robot(R.CREW[0])}</svg>` : "";
    t.innerHTML = `${bot}<div><b>${esc(msg)}</b>${o.sub ? `<small>${esc(o.sub)}</small>` : ""}</div>${o.undo ? `<button type="button">Undo</button>` : ""}`;
    toastHost().appendChild(t);
    if (o.undo) $("button", t).addEventListener("click", () => { o.undo(); t.remove(); });
    requestAnimationFrame(() => t.classList.add("in"));
    setTimeout(() => { t.classList.remove("in"); setTimeout(() => t.remove(), 400); }, o.ms || 5200);
    return t;
  }
  function celebrate(title, sub) {
    toast(title, { sub, cheer: true, ms: 6500 });
    if (reduced) return;
    const colors = ["#426B56", "#B87860", "#6F5C4B", "#E2A24D", "#8fb7a0"];
    for (let i = 0; i < 46; i++) {
      const e = document.createElement("i"); e.className = "ob-confetti";
      const x = innerWidth * (.15 + Math.random() * .7), dx = (Math.random() - .5) * 360, rot = Math.random() * 720 - 360;
      e.style.cssText = `left:${x}px;top:${innerHeight * .35}px;background:${colors[i % colors.length]};width:${6 + Math.random() * 6}px;height:${8 + Math.random() * 8}px`;
      document.body.appendChild(e);
      const a = e.animate([{ transform: "translate(0,0) rotate(0)", opacity: 1 }, { transform: `translate(${dx}px,${innerHeight * (.35 + Math.random() * .4)}px) rotate(${rot}deg)`, opacity: 0 }], { duration: 1400 + Math.random() * 900, easing: "cubic-bezier(.2,.7,.3,1)" });
      a.onfinish = () => e.remove();
    }
  }

  /* ---------- small view helpers ---------- */
  const avatar = i => R ? `<svg viewBox="-44 -190 88 96" class="ob-avatar" aria-hidden="true">${R.robot(R.CREW[i])}</svg>` : "";
  const ring = (pct, label, cls = "") => `<span class="ob-ring ${cls}" style="--p:${Math.max(0, Math.min(100, pct))}"><svg viewBox="0 0 44 44" aria-hidden="true"><circle cx="22" cy="22" r="18"/><circle class="v" cx="22" cy="22" r="18" pathLength="100"/></svg><b>${label}</b></span>`;
  const greeting = () => { const h = new Date().getHours(); return h < 5 ? "Still up" : h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening"; };
  const emptyBot = (i, t, p) => `<div class="ob-empty">${R ? `<svg viewBox="-70 -200 140 210" aria-hidden="true">${R.robot(R.CREW[i])}</svg>` : ""}<h3>${t}</h3><p>${p}</p></div>`;
  const contactPills = (c, co, max = 3) => {
    const list = A.getContacts(c, co); if (!list.length) return `<span class="ob-nocontact">No contact yet</span>`;
    return list.slice(0, max).map(x => `<span class="referral-pill ${/hr|talent|recruit|people/i.test(`${x.title || ""} ${x.name}`) ? "hr" : ""}" title="${esc(x.title || "")}">${esc(x.name)}</span>`).join("") + (list.length > max ? `<span class="ob-more">+${list.length - max}</span>` : "");
  };

  /* ---------- shift report ---------- */
  function shiftReport(c) {
    const jobs = A.allJobs(c), rk = ranked(c), d = S.data;
    const cutoff = Date.now() - 7 * 864e5;
    const fresh = jobs.filter(j => { const st = S.saved.meta?.newOpportunities?.[A.roleKey(c, j)]; return st && new Date(st).getTime() > cutoff; }).length;
    const companies = new Set(jobs.map(j => A.norm(j.company))).size;
    const strong = rk.filter(r => r.fit.score >= 80).length, pot = rk.filter(r => r.fit.score >= 65 && r.fit.score < 80).length;
    const withC = jobs.filter(j => A.getContacts(c, j.company).length).length;
    const ids = new Set(jobs.map(A.jobIdentity)); const dupes = jobs.length - ids.size;
    const when = d ? new Date(d.generated_at) : null;
    const vOk = jobs.filter(j => meta().verify[A.roleKey(c, j)]?.status === "ok").length;
    const vFix = jobs.filter(j => ["dead", "closed"].includes(meta().verify[A.roleKey(c, j)]?.status)).length;
    const rows = [
      [0, "Detective", `${fresh ? plural(fresh, "new role") + " this week" : "No new roles this week"} · ${plural(jobs.length, "role")} across ${plural(companies, "company", "companies")}`],
      [1, "Analyst", `${plural(strong, "strong fit")} and ${plural(pot, "potential match", "potential matches")} waiting in your picks`],
      [2, "Verifier", `${plural(vOk, "link")} confirmed live${vFix ? `, ${plural(vFix, "role")} pulled as closed or broken` : ""} · ${plural(dupes, "duplicate")} folded`],
      [3, "Connector", `${plural(withC, "role")} with HR, alumni or engineer contacts you added`],
    ];
    return `<section class="ob-card ob-shift" aria-label="Shift report"><div class="ob-card-h"><h3>Shift report</h3><span>${when ? `Synced ${when.toLocaleDateString(undefined, { day: "numeric", month: "short" })}, ${when.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}` : ""}</span></div>
      <ul>${rows.map(([i, n, t]) => `<li>${avatar(i)}<div><b>${n}</b><span>${t}</span></div></li>`).join("")}</ul>
      <div class="ob-shift-foot"><button class="button button-quiet" type="button" data-act="run-now">↻ Run now</button><small>Re-reads your Google Sheets, where the agent adds new roles daily. Nothing is sent anywhere.</small></div></section>`;
  }

  /* ---------- TODAY ---------- */
  const ui = { apply: {}, skip: {}, view: null };
  const hooks = { renderAvail: null };
  let todayEl;
  function followupsDue(c) {
    const f = meta().followups, d = today();
    return A.allJobs(c).filter(j => {
      const key = A.roleKey(c, j);
      if (A.jobStatus(j, c) !== "Applied" || !appliedOf(j, c)) return false;
      if (dayDiff(appliedOf(j, c), d) < 4) return false;
      const x = f[key]; return !(x && (x.done || (x.until && x.until > d)));
    }).sort((a, b) => appliedOf(a, c).localeCompare(appliedOf(b, c)));
  }

  function pickCard(r, c, i) {
    const j = r.job, f = r.fit, key = r.key, st = ui.skip[key] ? "skip" : ui.apply[key] ? "confirm" : "idle";
    const good = f.comps.filter(x => x.got > 0 && x.max > 0).sort((a, b) => b.got - a.got).slice(0, 4);
    const bad = f.comps.filter(x => x.got === 0 && x.max > 0).slice(0, 1);
    const url = A.jobUrl(j);
    const actions = st === "idle" ? `
        <button class="ob-btn primary" data-act="apply" data-key="${esc(key)}">${url ? "Apply ↗" : "Mark applied"}</button>
        <button class="ob-btn" data-act="watch" data-key="${esc(key)}">Watch</button>
        <button class="ob-btn ghost" data-act="skip" data-key="${esc(key)}">Skip</button>`
      : st === "confirm" ? `
        <span class="ob-ask">${url ? "Listing opened. Did you apply?" : "Applied to this one?"}</span>
        <button class="ob-btn primary" data-act="applied" data-key="${esc(key)}">Yes, mark applied</button>
        <button class="ob-btn" data-act="watch" data-key="${esc(key)}">Not yet · Watch</button>
        <button class="ob-btn ghost" data-act="cancel" data-key="${esc(key)}">Cancel</button>`
      : `
        <span class="ob-ask">No problem. What's off?</span>
        ${["Pay", "Location", "Stack", "Level", "Just not for me"].map(x => `<button class="ob-btn chip" data-act="skip-reason" data-reason="${x}" data-key="${esc(key)}">${x}</button>`).join("")}
        <button class="ob-btn ghost" data-act="cancel" data-key="${esc(key)}">Cancel</button>`;
    return `<article class="ob-pick fit-${f.label.toLowerCase()}" data-key="${esc(key)}" style="--i:${i}">
      <div class="ob-pick-top">${A.logo(j.company)}<div class="ob-pick-co"><b>${esc(j.company)}</b><small>${esc(j.location || "Location not listed")}</small></div>
        ${ring(f.score, f.score, "fit " + f.label.toLowerCase())}</div>
      <h3>${esc(j.title)}</h3>
      <div class="ob-fitlabel"><span class="lab ${f.label.toLowerCase()}">${f.label} fit</span>${A.isNew(j, c) ? '<span class="lab new">NEW</span>' : ""}${meta().verify[key]?.status === "ok" ? '<span class="lab strong">✓ Link verified</span>' : ""}${j.category && j.category !== "Job link" ? `<span class="lab">${esc(j.category)}</span>` : ""}</div>
      <ul class="ob-reasons">${good.map(x => `<li class="ok">${esc(x.note)}</li>`).join("")}${bad.map(x => `<li class="no">${esc(x.note)}</li>`).join("")}</ul>
      <div class="ob-contacts">${contactPills(c, j.company)}</div>
      <details class="ob-why"><summary>How is this scored?</summary>
        <table>${f.comps.map(x => `<tr><td>${esc(x.k)}</td><td><i style="--w:${x.max ? Math.round(x.got / x.max * 100) : 0}%"></i></td><td>${x.max ? `${x.got}/${x.max}` : x.got}</td><td>${esc(x.note)}</td></tr>`).join("")}</table>
        <p>A transparent local estimate from the title, level, place, contacts and link. The sheets hold no job description, so it is capped until you add skills. It never guesses salary and isn't a promise of an interview.</p></details>
      <div class="ob-actions ${st}">${actions}</div></article>`;
  }

  function renderToday() {
    if (!todayEl || !S.data) return;
    const c = S.candidate, picks = picksFor(c), due = followupsDue(c), g = goalOf(c), w = appliedThisWeek(c), sk = streak(c);
    const m = meta(), lastPick = ranked(c).length;
    const first = A.profile(c) ? c : "there";
    const dateLabel = new Date().toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long" });
    const needsTune = !m.onboarded[c];
    const hint = !picks.length ? "Nothing left to review right now." : `${plural(picks.length, "role")} picked for you${due.length ? `, ${plural(due.length, "follow-up")} due` : ""}.`;
    markEnter();
    todayEl.innerHTML = `<div class="ob-wrap">
      <header class="ob-hello">
        <div><div class="ob-eyebrow"><i></i> TODAY · ${esc(dateLabel.toUpperCase())}</div>
          <h1>${greeting()}, <em>${esc(first)}.</em></h1><p>${hint} One calm step at a time.</p></div>
        <div class="ob-hello-actions"><div class="ob-switch" role="group" aria-label="Candidate">${["Vaanya", "Vrinda"].map(n => `<button type="button" data-act="cand" data-c="${n}" aria-pressed="${n === c}">${n}</button>`).join("")}</div>
          <button class="button button-quiet" type="button" data-act="tune">⚙ Tune picks</button></div>
      </header>
      ${needsTune ? `<div class="ob-banner"><div>${avatar(1)}</div><p><b>Step 1 · Tune your picks.</b> Role types, level and places. It takes about a minute.</p><button class="button button-bright" type="button" data-act="tune">Set up in 1 minute</button></div>` : !mission(c).started ? `<div class="ob-banner"><div>${avatar(0)}</div><p><b>Step 2 · Send the detective out.</b> Choose the companies you'd love to join, or stay open to any company above your minimum pay.</p><button class="button button-bright" type="button" data-act="tab" data-tab="choose">Choose companies</button></div>` : ""}
      <div class="ob-grid">
        <section class="ob-main" aria-label="Today's picks">
          <div class="ob-h"><h2>Today's picks</h2><span>Ranked by a local fit score · nothing is sent for you</span></div>
          <div class="ob-picks">${picks.length ? picks.map((r, i) => pickCard(r, c, i)).join("") : emptyBot(0, "All caught up", lastPick ? "Scout is out looking. Check back tomorrow, or see more roles below." : "No untouched roles left. Track a new one or refresh your sheets.")}</div>
          <div class="ob-more-row">${lastPick > picks.length ? `<button class="button button-quiet" type="button" data-act="more">Show 5 more</button>` : ""}<a class="button button-quiet" href="/${c.toLowerCase()}">Browse all by company ↗</a></div>
        </section>
        <aside class="ob-side">
          <section class="ob-card ob-goal"><div class="ob-card-h"><h3>This week</h3><button class="ob-link" type="button" data-act="goal">${g} / week</button></div>
            <div class="ob-goal-row">${ring(g ? w / g * 100 : 0, `${w}<small>/${g}</small>`, "big")}<p>${w >= g ? "Goal reached. Everything from here is a bonus." : `${plural(g - w, "application")} to your weekly goal. A few focused ones beat many rushed ones.`}</p></div></section>
          <section class="ob-card ob-streak"><div class="ob-card-h"><h3>Rhythm</h3></div>
            <div class="ob-streak-row"><b>${sk.n}</b><span>${sk.n === 1 ? "active day" : "active days"} in a row</span></div>
            <p class="ob-soft">${sk.n ? (sk.active ? "You've done something today. Nice." : "One rest day is fine. Your streak stays warm.") : "Apply, watch or skip a role to start your rhythm."}</p></section>
          <section class="ob-card ob-follow"><div class="ob-card-h"><h3>Follow-ups</h3><span>${due.length ? due.length + " due" : "none due"}</span></div>
            ${due.length ? `<ul>${due.slice(0, 5).map(j => { const key = A.roleKey(c, j), days = dayDiff(appliedOf(j, c), today()); return `<li data-key="${esc(key)}"><div><b>${esc(j.company)}</b><span>${esc(j.title)} · applied ${days} days ago</span><em>${(j.tags || []).includes("Referred") ? "Referred. A short thank-you or check-in is enough" : A.getContacts(c, j.company).length ? `You listed ${esc(A.getContacts(c, j.company)[0].name)}` : "No contact listed"}</em>${j.notes ? `<em class="src">Your sheet: ${esc(j.notes.slice(0, 70))}</em>` : ""}</div>
              <div class="ob-mini"><button data-act="fu-open" data-key="${esc(key)}">Notes</button><button data-act="fu-done" data-key="${esc(key)}">Done</button><button data-act="fu-snooze" data-key="${esc(key)}">+2d</button></div></li>`; }).join("")}</ul>${due.length > 5 ? `<p class="ob-soft">+ ${due.length - 5} more waiting. Use Done or +2d to clear them calmly.</p>` : ""}` : `<p class="ob-soft">Applied roles show up here after 4 days, as a gentle reminder. Orbit never sends anything for you.</p>`}</section>
          ${sheetCard(c)}
          ${shiftReport(c)}
        </aside>
      </div>
      ${weeklyCard(c)}
      <p class="ob-safe">Orbit never submits an application, sends a message or contacts anyone. You decide every step.</p></div>`;
  }
  function markEnter() { if (ui.entered) return; ui.entered = true; todayEl.classList.add("enter"); setTimeout(() => todayEl.classList.remove("enter"), 1400); }

  function sheetCard(c) {
    const jobs = A.allJobs(c), by = s => jobs.filter(j => A.jobStatus(j, c) === s);
    const asks = jobs.filter(j => (j.tags || []).includes("Referral asked")).length;
    const closed = jobs.filter(j => A.jobStatus(j, c) === "Closed").length;
    const events = jobs.filter(j => appliedOf(j, c) && isApplied(j, c)).sort((a, b) => appliedOf(b, c).localeCompare(appliedOf(a, c))).slice(0, 4);
    const when = d => new Date(d + "T00:00:00").toLocaleDateString(undefined, { day: "numeric", month: "short" });
    if (!jobs.some(j => j.status || (j.tags || []).length || j.notes)) return "";
    return `<section class="ob-card ob-sheets"><div class="ob-card-h"><h3>From your sheets</h3><span>read-only</span></div>
      <div class="ob-sheet-grid"><div><b>${by("Applied").length + by("Interviewing").length}</b><span>applied</span></div><div><b>${asks}</b><span>referral asks</span></div><div><b>${by("Interviewing").length}</b><span>interviewing</span></div><div><b>${closed}</b><span>closed</span></div></div>
      ${events.length ? `<ul class="ob-sheet-log">${events.map(j => `<li><span>${when(appliedOf(j, c))}</span><b>${esc(j.company)}</b><em>${esc(A.jobStatus(j, c))}</em></li>`).join("")}</ul>` : ""}
      <p class="ob-soft">Status and notes you type in the sheets show up here after the next sync. Edits made in Orbit stay in Orbit.</p></section>`;
  }

  function weeklyCard(c) {
    const w = weekStart(), jobs = A.allJobs(c);
    const applied = jobs.filter(j => isApplied(j, c) && appliedOf(j, c) >= w).length;
    const watching = jobs.filter(j => A.jobStatus(j, c) === "Watching").length;
    const live = jobs.filter(j => ["Interviewing", "Offer"].includes(A.jobStatus(j, c))).length;
    const skipped = meta().activity.filter(x => x.c === c && x.t === "skip" && x.d >= w).length;
    const msg = applied ? `You applied to ${plural(applied, "role")} this week${live ? `, and ${plural(live, "conversation")} ${live === 1 ? "is" : "are"} moving` : ""}. That's real momentum.` : watching ? `You're watching ${plural(watching, "role")}. When one feels right, today's picks are ready.` : "A fresh week. Start with one role that feels exciting. That's enough.";
    return `<section class="ob-card ob-week"><div class="ob-card-h"><h3>Your week, gently summarised</h3></div><div class="ob-week-grid"><div><b>${applied}</b><span>applied</span></div><div><b>${watching}</b><span>watching</span></div><div><b>${live}</b><span>in conversation</span></div><div><b>${skipped}</b><span>skipped</span></div></div><p>${msg}</p></section>`;
  }

  function bindToday() {
    todayEl.addEventListener("click", e => {
      const b = e.target.closest("[data-act]"); if (!b) return;
      const act = b.dataset.act, c = S.candidate, key = b.dataset.key;
      const job = key && A.allJobs(c).find(j => A.roleKey(c, j) === key);
      const rerender = () => renderToday();
      if (act === "cand") { setCandidate(b.dataset.c); history.replaceState(null, "", `/apply?tab=picks&c=${b.dataset.c}`); rerender(); }
      else if (act === "tab") showTab(b.dataset.tab);
      else if (act === "tune") openTune();
      else if (act === "goal") openTune(true);
      else if (act === "more") { picksFor(c); meta().today[c].extra = (meta().today[c].extra || 0) + 5; save(); rerender(); }
      else if (act === "run-now") A.refreshSheets(b).then?.(() => {});
      else if (act === "apply" && job) { const url = A.jobUrl(job); if (url) window.open(url, "_blank", "noopener,noreferrer"); ui.apply[key] = 1; rerender(); }
      else if (act === "cancel") { delete ui.apply[key]; delete ui.skip[key]; rerender(); }
      else if (act === "applied" && job) { delete ui.apply[key]; leaveCard(key, () => { setStatus(job, "Applied", c); rerender(); }); }
      else if (act === "watch" && job) { delete ui.apply[key]; leaveCard(key, () => { setStatus(job, "Watching", c, { silent: true }); toast("Added to watching", { sub: job.company + " · " + job.title }); rerender(); }); }
      else if (act === "skip" && job) { ui.skip[key] = 1; rerender(); }
      else if (act === "skip-reason" && job) {
        const f = fit(job, c); delete ui.skip[key];
        meta().skips[key] = { c, reason: b.dataset.reason, at: today(), city: f.city || null, lv: f.lv, fam: f.fam, co: A.norm(job.company) };
        log(c, "skip", key); save();
        leaveCard(key, () => {
          rerender();
          toast("Skipped. Orbit will weigh similar roles lower.", { undo: () => { delete meta().skips[key]; save(); renderToday(); }, ms: 6500 });
        });
      }
      else if (act === "fu-open" && job) openEditor(job);
      else if (act === "fu-done") { meta().followups[key] = { done: true }; log(c, "move", key); save(); toast("Marked as followed up"); rerender(); }
      else if (act === "fu-snooze") { meta().followups[key] = { until: addDays(today(), 2) }; save(); toast("Snoozed for 2 days"); rerender(); }
    });
  }
  function leaveCard(key, done) {
    const el = $(`.ob-pick[data-key="${CSS.escape(key)}"]`, todayEl);
    if (!el || reduced) return done();
    el.classList.add("leaving"); setTimeout(done, 340);
  }

  /* ---------- Apply now: two tabs, one page ---------- */
  let tabBar;
  function showTab(t) {
    if (!tabBar) return;
    $("#hunt-page").classList.toggle("hidden", t !== "choose");
    $("#today-page").classList.toggle("hidden", t !== "picks");
    $$("button", tabBar).forEach(b => b.setAttribute("aria-selected", String(b.dataset.tab === t)));
    history.replaceState(null, "", `/apply?tab=${t}&c=${S.candidate}`);
    if (t === "picks") renderToday();
    scrollTo({ top: 0, behavior: "instant" });
  }
  function applyTabs() {
    tabBar = document.createElement("div"); tabBar.id = "apply-tabs"; tabBar.className = "ob-apply-tabs";
    tabBar.innerHTML = `<div class="ob-tabs" role="tablist" aria-label="Apply now"><button type="button" role="tab" data-tab="choose"><b>1</b> Choose companies</button><button type="button" role="tab" data-tab="picks"><b>2</b> Today's picks</button></div>`;
    $("main").insertBefore(tabBar, $("#today-page"));
    tabBar.addEventListener("click", e => { const b = e.target.closest("[data-tab]"); if (b) showTab(b.dataset.tab); });
    const q = new URLSearchParams(location.search).get("tab");
    showTab(["choose", "picks"].includes(q) ? q : S.applyTab || (mission(S.candidate).started ? "picks" : "choose"));
  }

  /* ---------- candidate memory ---------- */
  function setCandidate(c) { S.candidate = c; try { localStorage.setItem("orbit.candidate", c); } catch (_) {} }

  /* ---------- note editor (shared by Today follow-ups and the board) ---------- */
  const TEMPLATES = ["Referred by … ", "Recruiter reached out · ", "Phone screen on … ", "Interview round 1 on … ", "Waiting to hear back. ", "Follow up with recruiter on … ", "Rejected · reason: "];
  function openEditor(job) {
    const c = S.candidate, key = A.roleKey(c, job), st = A.jobState(job, c);
    let dlg = $("#ob-edit"); if (dlg) dlg.remove();
    dlg = document.createElement("dialog"); dlg.id = "ob-edit"; dlg.className = "modal ob-modal";
    dlg.innerHTML = `<form method="dialog"><div class="modal-kicker">${esc(job.company.toUpperCase())}</div><h3>${esc(job.title)}</h3>
      <div class="form-two"><label>Stage<select id="obe-status">${A.statuses.map(s => `<option ${s === A.jobStatus(job, c) ? "selected" : ""}>${s}</option>`).join("")}</select></label>
      <label>Date applied<input type="date" id="obe-date" value="${esc(appliedOf(job, c))}"></label></div>
      ${(job.notes || (job.tags || []).length || job.status) ? `<div class="ob-sheetbox"><b>From your sheet</b>${job.status ? `<span class="tiny-chip">${esc(job.status)}</span>` : ""}${(job.tags || []).map(t => `<span class="tiny-chip sheet-tag">${esc(t)}</span>`).join("")}${job.notes ? `<p>${esc(job.notes)}</p>` : ""}<small>Read-only. Orbit never writes to your sheet.</small></div>` : ""}
      <label>What should you remember?<textarea id="obe-notes" rows="4" placeholder="Interview notes, referral context, what mattered…">${esc(st.applicationNotes || "")}</textarea></label>
      <div class="ob-templates" aria-label="Quick note starters">${TEMPLATES.map(t => `<button type="button" data-t="${esc(t)}">${esc(t.trim().replace(/…|·|:/g, "").trim())}</button>`).join("")}</div>
      <label>Next step<input id="obe-next" maxlength="200" value="${esc(st.nextStep || "")}" placeholder="Follow up with …"></label>
      <div class="ob-contacts" style="margin-top:12px">${contactPills(c, job.company, 6)}</div>
      <div class="modal-buttons"><button class="button button-quiet" value="cancel">Cancel</button><button class="button button-bright" id="obe-save" value="default">Save</button></div></form>`;
    document.body.appendChild(dlg);
    $(".ob-templates", dlg).addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; const t = $("#obe-notes", dlg); t.value = (t.value ? t.value.replace(/\s*$/, "\n") : "") + b.dataset.t; t.focus(); });
    $("#obe-save", dlg).addEventListener("click", () => {
      const status = $("#obe-status", dlg).value, old = A.jobState(job, c);
      const next = { ...old, candidate: c, status, applicationNotes: $("#obe-notes", dlg).value.trim().slice(0, 4000), nextStep: $("#obe-next", dlg).value.trim().slice(0, 200), appliedAt: $("#obe-date", dlg).value || (status === "Applied" ? old.appliedAt || today() : old.appliedAt), updatedAt: new Date().toISOString() };
      const changed = status !== A.jobStatus(job, c);
      S.saved.jobs[key] = next; if (changed) log(c, "move", key); save();
      if (changed) afterStatus(c, status);
      toast("Saved"); refreshViews();
    });
    dlg.addEventListener("close", () => dlg.remove());
    dlg.showModal();
  }

  /* ---------- BOARD (tracker page) ---------- */
  const COLS = ["Watching", "Applied", "Interviewing", "Offer", "Closed"];
  const COLNOTE = { Watching: "Interesting, not yet applied", Applied: "Sent. Waiting to hear", Interviewing: "Conversations in motion", Offer: "Decision time", Closed: "Done or passed" };
  let boardEl, availEl, dragKey = null;
  function initBoard() {
    const page = $("#tracker-page"); if (!page) return;
    const list = $("#tracker-results"); if (!list) return;
    boardEl = document.createElement("div"); boardEl.id = "ob-board"; boardEl.className = "ob-board";
    list.parentNode.insertBefore(boardEl, list);
    availEl = document.createElement("div"); availEl.id = "ob-avail"; availEl.className = "ob-avail";
    list.parentNode.insertBefore(availEl, boardEl);
    const qv = new URLSearchParams(location.search).get("view"), sv = (() => { try { return localStorage.getItem("orbit.trackview"); } catch (_) { return null; } })();
    ui.view = ["available", "board", "list"].includes(qv) ? qv : ["available", "board", "list"].includes(sv) ? sv : (mission(S.candidate).started ? "available" : "board");
    const sw = $(".view-switch", page);
    if (sw) {
      sw.innerHTML = `<div class="ob-switch small" role="group" aria-label="Tracker view">${[["available", "Jobs available"], ["board", "Board"], ["list", "List"]].map(([v, l]) => `<button type="button" data-view="${v}" aria-pressed="${ui.view === v}">${l}</button>`).join("")}</div>`;
      sw.addEventListener("click", e => { const b = e.target.closest("[data-view]"); if (!b) return; ui.view = b.dataset.view; try { localStorage.setItem("orbit.trackview", ui.view); } catch (_) {} $$("button", sw).forEach(x => x.setAttribute("aria-pressed", String(x.dataset.view === ui.view))); applyView(); });
    }
    new MutationObserver(() => { renderBoard(); renderAvail(); }).observe(list, { childList: true });
    boardEl.addEventListener("dragstart", e => { const card = e.target.closest(".ob-kcard"); if (!card) return; dragKey = card.dataset.key; card.classList.add("dragging"); e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", dragKey); });
    boardEl.addEventListener("dragend", () => { dragKey = null; $$(".dragging,.over", boardEl).forEach(x => x.classList.remove("dragging", "over")); });
    boardEl.addEventListener("dragover", e => { const col = e.target.closest(".ob-col"); if (!col) return; e.preventDefault(); $$(".over", boardEl).forEach(x => x !== col && x.classList.remove("over")); col.classList.add("over"); });
    boardEl.addEventListener("drop", e => { const col = e.target.closest(".ob-col"); if (!col || !dragKey) return; e.preventDefault(); moveKey(dragKey, col.dataset.status); });
    boardEl.addEventListener("click", e => {
      const b = e.target.closest("[data-bact]"); if (!b) return;
      const key = b.closest(".ob-kcard")?.dataset.key, c = S.candidate, job = key && A.allJobs(c).find(j => A.roleKey(c, j) === key); if (!job) return;
      if (b.dataset.bact === "edit") openEditor(job);
      else if (b.dataset.bact === "left" || b.dataset.bact === "right") {
        const cur = COLS.indexOf(A.jobStatus(job, c)), nx = COLS[Math.max(0, Math.min(COLS.length - 1, (cur < 0 ? 0 : cur) + (b.dataset.bact === "right" ? 1 : -1)))];
        moveKey(key, nx);
      }
    });
    applyView(); renderBoard(); renderAvail();
  }
  function moveKey(key, status) {
    const c = S.candidate, job = A.allJobs(c).find(j => A.roleKey(c, j) === key); if (!job || A.jobStatus(job, c) === status) return;
    setStatus(job, status, c); refreshViews();
  }
  function renderAvail() { if (availEl && hooks.renderAvail && ui.view === "available") hooks.renderAvail(availEl); }
  function applyView() { if (!boardEl) return; boardEl.classList.toggle("hidden", ui.view !== "board"); availEl.classList.toggle("hidden", ui.view !== "available"); $("#tracker-results")?.classList.toggle("hidden", ui.view !== "list"); renderAvail(); }
  function renderBoard() {
    if (!boardEl || !S.data) return;
    const c = S.candidate, jobs = A.allJobs(c).filter(j => isTracked(j, c));
    const by = Object.fromEntries(COLS.map(k => [k, []]));
    jobs.forEach(j => { const s = A.jobStatus(j, c); (by[s] || by.Watching).push(j); });
    COLS.forEach(k => by[k].sort((a, b) => (A.jobState(b, c).updatedAt || "").localeCompare(A.jobState(a, c).updatedAt || "")));
    const due = new Set(followupsDue(c).map(j => A.roleKey(c, j)));
    if (!jobs.length) { boardEl.innerHTML = emptyBot(3, "Your board is empty", "Pick something from Today, or add a role with “Track role”. It will show up here."); return; }
    boardEl.innerHTML = COLS.map(k => `<section class="ob-col" data-status="${k}" aria-label="${k}"><header><b>${k}</b><span>${by[k].length}</span><small>${COLNOTE[k]}</small></header>
      <div class="ob-col-body">${by[k].map(j => kcard(j, c, due)).join("") || `<p class="ob-colempty">Drop a card here</p>`}</div></section>`).join("");
  }
  function kcard(j, c, due) {
    const st = A.jobState(j, c), key = A.roleKey(c, j), at = appliedOf(j, c), days = at ? dayDiff(at, today()) : null;
    const sheetStatus = A.statuses.includes(j.status) ? j.status : "", local = st.status, now = A.jobStatus(j, c);
    const prov = local && local !== sheetStatus && sheetStatus ? `<span class="prov edit" title="Your sheet says ${esc(sheetStatus)}">Edited here · sheet: ${esc(sheetStatus)}</span>` : sheetStatus && !local ? `<span class="prov sheet">From your sheet</span>` : local ? `<span class="prov edit">Set here</span>` : "";
    const tags = (j.tags || []).slice(0, 3).map(t => `<span class="sheet-tag ${/reject|deadline|not /i.test(t) ? "bad" : /referr|asked/i.test(t) ? "ref" : ""}">${esc(t)}</span>`).join("");
    return `<article class="ob-kcard" draggable="true" data-key="${esc(key)}">
      <div class="ob-kc-top">${A.logo(j.company)}<b>${esc(j.company)}</b></div>
      <button class="ob-kc-title" type="button" data-bact="edit">${esc(j.title)}</button>
      <div class="ob-kc-meta">${at ? `<span>${now === "Applied" || now === "Interviewing" ? "Applied" : "Dated"} ${days === 0 ? "today" : days + "d ago"}</span>` : ""}${due.has(key) ? `<span class="due">Follow-up due</span>` : ""}${st.nextStep ? `<span class="next">${esc(st.nextStep)}</span>` : ""}</div>
      ${tags ? `<div class="ob-kc-tags">${tags}</div>` : ""}
      ${j.notes ? `<p class="ob-kc-note"><b>Sheet note</b> ${esc(j.notes.slice(0, 96))}${j.notes.length > 96 ? "…" : ""}</p>` : ""}
      ${prov}
      <div class="ob-kc-people">${contactPills(c, j.company, 2)}</div>
      <div class="ob-kc-foot"><button type="button" data-bact="left" aria-label="Move left">←</button><button type="button" data-bact="edit" class="edit">Notes</button><button type="button" data-bact="right" aria-label="Move right">→</button></div></article>`;
  }

  /* ---------- first-run tuning ---------- */
  function openTune(goalOnly) {
    const c = S.candidate; const p = prefs(c);
    const draft = { roles: [...p.roles], level: p.level, places: [...p.places], skills: p.skills.join(", "), payFloor: p.payFloor || "", goal: goalOf(c) };
    let step = goalOnly ? 3 : 1;
    let dlg = $("#ob-tune"); if (dlg) dlg.remove();
    dlg = document.createElement("dialog"); dlg.id = "ob-tune"; dlg.className = "modal ob-modal ob-tune";
    document.body.appendChild(dlg);
    const chip = (v, label, on, kind) => `<button type="button" class="ob-chipsel" aria-pressed="${on}" data-k="${kind}" data-v="${esc(v)}">${esc(label)}</button>`;
    const render = () => {
      const dots = [1, 2, 3, 4].map(n => `<i class="${n === step ? "on" : n < step ? "done" : ""}"></i>`).join("");
      let body = "";
      if (step === 1) body = `<h3>What kind of roles?</h3><p class="ob-sub">Pick every role type you'd be happy to see for <b>${esc(c)}</b>.</p><div class="ob-chips">${Object.keys(FAM).map(k => chip(k, FAM[k].label, draft.roles.includes(k), "role")).join("")}</div>
        <h4>Which level fits?</h4><div class="ob-chips">${Object.keys(LEVELS).map(k => chip(k, LEVELS[k], draft.level === k, "level")).join("")}</div>`;
      if (step === 2) body = `<h3>Where would you work?</h3><p class="ob-sub">Cities and remote options count towards a role's fit.</p><div class="ob-chips">${PLACES.map(k => chip(k, k, draft.places.includes(k), "place")).join("")}</div>
        <label>Skills to look for <small>(optional, comma separated)</small><input id="ot-skills" value="${esc(draft.skills)}" placeholder="Node.js, C#, Azure, Java"></label>
        <label>Pay floor in LPA <small>(optional, only used when a listing shows pay)</small><input id="ot-pay" inputmode="numeric" value="${esc(draft.payFloor)}" placeholder="35"></label>`;
      if (step === 3) body = `<h3>A goal that feels kind</h3><p class="ob-sub">How many applications a week would feel good? Quality over volume.</p><div class="ob-chips">${[2, 3, 5, 8, 10].map(n => chip(n, `${n} / week`, +draft.goal === n, "goal")).join("")}</div>`;
      if (step === 4) {
        const prev = prefsPreview(c, draft);
        body = `<h3>The line just ran on your preferences</h3><div class="ob-scan">${[0, 1, 2, 3].map(i => `<div style="--i:${i}">${avatar(i)}<span>${["Hunting", "Scoring", "Verifying", "Connecting"][i]}</span></div>`).join("")}</div>
        <p class="ob-sub">${prev.total ? `${plural(prev.strong, "strong fit")} and ${plural(prev.pot, "potential match", "potential matches")} out of ${plural(prev.total, "role")}. A first look:` : "Nothing untouched matches yet. Try widening roles or places."}</p>
        <ol class="ob-preview">${prev.top.map(r => `<li><b>${esc(r.job.title)}</b><span>${esc(r.job.company)}</span><em>${r.fit.score}</em></li>`).join("")}</ol>`;
      }
      dlg.innerHTML = `<form method="dialog"><div class="ob-dots">${dots}</div>${body}
        <div class="modal-buttons">${step > 1 && !goalOnly ? `<button type="button" class="button button-quiet" data-s="back">Back</button>` : `<button class="button button-quiet" value="cancel">Cancel</button>`}
        <button type="button" class="button button-bright" data-s="next">${step === 4 || goalOnly ? "Save and show my picks" : "Continue"}</button></div></form>`;
    };
    const readInputs = () => { const s = $("#ot-skills", dlg), p2 = $("#ot-pay", dlg); if (s) draft.skills = s.value; if (p2) draft.payFloor = p2.value; };
    dlg.addEventListener("click", e => {
      const chipEl = e.target.closest(".ob-chipsel");
      if (chipEl) {
        const { k, v } = chipEl.dataset;
        if (k === "level") draft.level = v; else if (k === "goal") draft.goal = +v;
        else { const arr = k === "role" ? draft.roles : draft.places; const i = arr.indexOf(v); i < 0 ? arr.push(v) : arr.splice(i, 1); }
        readInputs(); render(); return;
      }
      const sb = e.target.closest("[data-s]"); if (!sb) return;
      readInputs();
      if (sb.dataset.s === "back") { step--; render(); return; }
      if (step < 4 && !goalOnly) { step++; render(); return; }
      const m = meta();
      m.prefs[c] = { roles: draft.roles.length ? draft.roles : p.roles, level: draft.level, places: draft.places, skills: String(draft.skills).split(",").map(x => x.trim()).filter(Boolean).slice(0, 12), payFloor: parseFloat(draft.payFloor) || 0, goal: +draft.goal || 5 };
      m.goals[c] = +draft.goal || 5; m.onboarded[c] = today();
      m.today[c] = { date: today(), keys: [], extra: 0 };
      save(); dlg.close(); toast("Picks tuned", { sub: "Your fit scores now use your preferences." }); refreshViews();
    });
    dlg.addEventListener("close", () => dlg.remove());
    render(); dlg.showModal();
  }
  function prefsPreview(c, draft) {
    const old = meta().prefs[c];
    meta().prefs[c] = { roles: draft.roles.length ? draft.roles : prefs(c).roles, level: draft.level, places: draft.places, skills: String(draft.skills).split(",").map(x => x.trim()).filter(Boolean), payFloor: parseFloat(draft.payFloor) || 0, goal: +draft.goal || 5 };
    const rk = ranked(c); if (old) meta().prefs[c] = old; else delete meta().prefs[c];
    return { total: rk.length, strong: rk.filter(r => r.fit.score >= 80).length, pot: rk.filter(r => r.fit.score >= 65 && r.fit.score < 80).length, top: rk.slice(0, 3) };
  }

  /* ---------- command palette ---------- */
  function actionsList() {
    const go = (label, href, hint) => ({ label, hint: hint || "Go to", run: () => { location.href = href; } });
    return [
      go("Apply now", "/apply"), go("Choose companies", "/apply?tab=choose"), go("Today's picks", "/apply?tab=picks"), go("Tracker: jobs available", "/person?view=available"), go("Tracker: board", "/person?view=board"), go("Vaanya's roles", "/vaanya"), go("Vrinda's roles", "/vrinda"), go("How Orbit works", "/home"),
      { label: "Switch to Vaanya", hint: "Candidate", run: () => { setCandidate("Vaanya"); if (S.route === "apply") { renderToday(); } else toast("Candidate set to Vaanya"); } },
      { label: "Switch to Vrinda", hint: "Candidate", run: () => { setCandidate("Vrinda"); if (S.route === "apply") { renderToday(); } else toast("Candidate set to Vrinda"); } },
      { label: "Tune my picks", hint: "Action", run: () => openTune() },
      { label: "Add an opportunity", hint: "Action", run: () => A.openEntry() },
      { label: "Toggle dark mode", hint: "Action", run: toggleTheme },
      { label: "Refresh from sheets", hint: "Action", run: () => { const b = document.createElement("button"); A.refreshSheets(b); toast("Refreshing from your sheets…"); } },
      { label: "Export my tracker", hint: "Action", run: () => $("#export")?.click() },
    ];
  }
  function openPalette() {
    if ($("#ob-pal")) return;
    const wrap = document.createElement("div"); wrap.id = "ob-pal"; wrap.setAttribute("role", "dialog"); wrap.setAttribute("aria-label", "Command palette");
    wrap.innerHTML = `<div class="ob-pal-box"><div class="ob-pal-in"><span>⌕</span><input id="ob-pal-q" placeholder="Search roles, companies or actions…" autocomplete="off" aria-controls="ob-pal-list"><kbd>esc</kbd></div><ul id="ob-pal-list" role="listbox"></ul><div class="ob-pal-foot"><span>↑↓ to move</span><span>↵ to choose</span></div></div>`;
    document.body.appendChild(wrap);
    const q = $("#ob-pal-q", wrap), ul = $("#ob-pal-list", wrap); let items = [], sel = 0;
    const close = () => { wrap.remove(); document.removeEventListener("keydown", onKey, true); };
    const roles = () => { const out = []; for (const p of S.data.profiles) for (const j of A.allJobs(p.candidate)) out.push({ label: `${j.title}`, sub: `${j.company} · ${p.candidate}${j.location ? " · " + j.location : ""}`, hint: A.jobStatus(j, p.candidate), job: j, c: p.candidate }); return out; };
    let roleCache = null;
    const draw = () => {
      const term = q.value.trim().toLowerCase();
      const acts = actionsList().filter(a => !term || a.label.toLowerCase().includes(term));
      let rs = [];
      if (term.length >= 2) { roleCache ||= roles(); const parts = term.split(/\s+/); rs = roleCache.filter(r => parts.every(t => `${r.label} ${r.sub}`.toLowerCase().includes(t))).slice(0, 8); }
      items = [...acts.slice(0, term ? 6 : 12).map(a => ({ ...a, kind: "act" })), ...rs.map(r => ({ ...r, kind: "role" }))];
      sel = Math.min(sel, Math.max(0, items.length - 1));
      ul.innerHTML = items.map((it, i) => `<li role="option" aria-selected="${i === sel}" data-i="${i}"><span class="k ${it.kind}">${it.kind === "act" ? "↳" : "◦"}</span><div><b>${esc(it.label)}</b>${it.sub ? `<small>${esc(it.sub)}</small>` : ""}</div><em>${esc(it.hint || "")}</em></li>`).join("") || `<li class="none">No matches. Try a company name.</li>`;
      $(`li[aria-selected=true]`, ul)?.scrollIntoView({ block: "nearest" });
    };
    const choose = it => {
      if (!it) return; close();
      if (it.kind === "act") return it.run();
      location.href = `/${it.c.toLowerCase()}#q=${encodeURIComponent(it.job.company)}`;
    };
    const onKey = e => {
      if (e.key === "Escape") { e.preventDefault(); close(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); sel = (sel + 1) % Math.max(1, items.length); draw(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); sel = (sel - 1 + items.length) % Math.max(1, items.length); draw(); }
      else if (e.key === "Enter") { e.preventDefault(); choose(items[sel]); }
    };
    document.addEventListener("keydown", onKey, true);
    q.addEventListener("input", () => { sel = 0; draw(); });
    ul.addEventListener("click", e => { const li = e.target.closest("li[data-i]"); if (li) choose(items[+li.dataset.i]); });
    wrap.addEventListener("mousedown", e => { if (e.target === wrap) close(); });
    draw(); q.focus();
  }

  /* ---------- theme ---------- */
  function toggleTheme() {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("orbit.theme", next); } catch (_) {}
    const b = $("#ob-theme"); if (b) { b.setAttribute("aria-pressed", String(next === "dark")); b.textContent = next === "dark" ? "☀" : "☾"; }
  }
  function themeButton() {
    const host = $(".top-actions"); if (!host || $("#ob-theme")) return;
    const dark = document.documentElement.dataset.theme === "dark";
    const t = document.createElement("button"); t.id = "ob-theme"; t.type = "button"; t.className = "ob-icon-btn"; t.setAttribute("aria-label", "Toggle dark mode"); t.setAttribute("aria-pressed", String(dark)); t.textContent = dark ? "☀" : "☾";
    t.addEventListener("click", toggleTheme);
    const k = document.createElement("button"); k.type = "button"; k.className = "ob-kbd-btn"; k.setAttribute("aria-label", "Open command palette"); k.innerHTML = "<span>⌕</span> Search <kbd>⌘K</kbd>";
    k.addEventListener("click", openPalette);
    host.prepend(t); host.prepend(k);
  }

  /* ---------- shift report on candidate pages ---------- */
  function candidateShift() {
    if (!["vaanya", "vrinda"].includes(S.route)) return;
    const desk = $("#opportunities-page .route-desk"); if (!desk) return;
    let host = $("#ob-cand-shift"); if (!host) { host = document.createElement("div"); host.id = "ob-cand-shift"; desk.prepend(host); host.addEventListener("click", e => { const b = e.target.closest('[data-act="run-now"]'); if (b) A.refreshSheets(b); }); }
    host.innerHTML = shiftReport(S.candidate) + `<a class="ob-today-link" href="/apply?tab=picks&c=${S.candidate}"><span>Open today's picks</span><b>→</b></a>`;
  }

  /* ---------- plumbing ---------- */
  function refreshViews() {
    if (S.route === "apply") renderToday();
    if (S.route === "person") { A.renderTracker(); renderBoard(); renderAvail(); }
    candidateShift();
  }
  let raf = 0;
  A.listeners.push(() => { if (quiet) return; cancelAnimationFrame(raf); raf = requestAnimationFrame(() => { if (S.route === "apply" && !$("dialog[open]")) renderToday(); if (S.route === "person") { renderBoard(); renderAvail(); } candidateShift(); }); });

  window.OrbitProduct = { appliedOf, celebrate, dayDiff, fit, hooks, inScope, log, meta, mission, openEditor, openTune, payOk, payState, plural, prefs, save, setCandidate, setStatus, showTab, toast, today };
  function init() {
    if (S.route === "apply") {
      todayEl = $("#today-page");
      const q = new URLSearchParams(location.search).get("c"), stored = (() => { try { return localStorage.getItem("orbit.candidate"); } catch (_) { return null; } })();
      const pick = ["Vaanya", "Vrinda"].find(n => n === q) || ["Vaanya", "Vrinda"].find(n => n === stored) || "Vrinda";
      setCandidate(pick);
      bindToday(); renderToday(); applyTabs();
    } else if (["vaanya", "vrinda"].includes(S.route)) {
      setCandidate(S.candidate);
      const h = decodeURIComponent((location.hash.match(/^#q=(.*)$/) || [])[1] || "");
      if (h) { const s = $("#search"); if (s) { s.value = h; s.dispatchEvent(new Event("input")); } }
    } else if (S.route === "person") {
      try { const st = localStorage.getItem("orbit.candidate"); if (st && !new URLSearchParams(location.search).get("candidate") && ["Vaanya", "Vrinda"].includes(st) && S.candidate !== st) { S.candidate = st; A.renderTracker(); } } catch (_) {}
      initBoard();
    }
    themeButton(); candidateShift();
    document.addEventListener("keydown", e => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openPalette(); }
      else if (e.key === "/" && !/input|textarea|select/i.test(document.activeElement?.tagName || "")) { e.preventDefault(); openPalette(); }
    });
  }
  if (A.ready) init(); else window.addEventListener("orbit:ready", init, { once: true });
})();
