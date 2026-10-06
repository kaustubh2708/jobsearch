/* Orbit hunt: choose companies (or stay open to any above a pay floor) -> detective hunts -> analyst filters
   -> verifier double-checks real links -> tracker shows "Jobs available" with reach-out options.
   Orbit never sends anything: drafts are copied and sent by the user. */
(() => {
  const A = window.OrbitApp, P = window.OrbitProduct, R = window.OrbitRobots;
  if (!A || !P) return;
  const S = A.state, esc = A.esc, norm = A.norm;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const plural = P.plural;

  /* ---------- contacts: HR/TA, alumni, engineers ---------- */
  const RE = {
    hr: /\b(hr|human resources|talent|recruit\w*|people (ops|operations|partner|team)|\bta\b|acquisition|hiring)\b/i,
    eng: /engineer|\bsde\b|developer|software|architect|tech lead|\bswe\b|data scientist|\bmts\b|programmer|staff|\bsre\b/i,
    alumni: /alumn|\biit\b|\bnit\b|\bbits\b|\biiit\b|\biim\b|xlri|\bisb\b|college|university|batch|\bdtu\b|\bnsit\b|\bvit\b/i,
  };
  const textOf = ct => `${ct.title || ""} ${ct.function || ""} ${ct.name || ""}`;
  const catOf = ct => RE.hr.test(textOf(ct)) ? "hr" : RE.eng.test(textOf(ct)) ? "eng" : RE.alumni.test(textOf(ct)) ? "alumni" : "other";
  const stats = list => ({ hr: list.filter(x => catOf(x) === "hr").length, eng: list.filter(x => catOf(x) === "eng").length, alumni: list.filter(x => RE.alumni.test(textOf(x))).length, total: list.length });
  const LABEL = { hr: "HR / TA", eng: "Engineers", alumni: "Alumni", other: "Other connections" };

  function companyList(c) {
    const map = new Map();
    const add = name => { const k = norm(name); if (!k) return null; if (!map.has(k)) map.set(k, { key: k, name, jobs: [] }); return map.get(k); };
    (A.profile(c)?.companies || []).forEach(x => add(x.name));
    A.allJobs(c).forEach(j => { const e = add(j.company); if (e) e.jobs.push(j); });
    for (const e of map.values()) { e.contacts = A.getContacts(c, e.name); e.st = stats(e.contacts); }
    return [...map.values()];
  }

  /* ---------- the hunt pipeline (real data, real link checks) ---------- */
  function huntList(c) {
    return A.allJobs(c)
      .filter(j => P.inScope(j, c) && !A.isHistorical(j))
      .map(j => ({ job: j, key: A.roleKey(c, j), fit: P.fit(j, c), pay: P.payState(j, c) }))
      .filter(r => !r.fit.exec && r.fit.score >= 50 && P.payOk(r.job, c) && A.jobStatus(r.job, c) !== "Closed")
      .sort((a, b) => b.fit.score - a.fit.score);
  }
  const vstat = key => P.meta().verify[key]?.status || "unchecked";
  async function verifyKeys(c, rows, onProgress) {
    const m = P.meta();
    const todo = [], byUrl = new Map();
    for (const r of rows) {
      const url = A.jobUrl(r.job);
      if (!url) { m.verify[r.key] = { status: "nolink", at: P.today() }; continue; }
      if (A.isLinkedIn(r.job)) { m.verify[r.key] = { status: "manual", at: P.today(), note: "LinkedIn listing: check it in your own visible session." }; continue; }
      todo.push(r); (byUrl.get(url) || byUrl.set(url, []).get(url)).push(r.key);
    }
    const urls = [...byUrl.keys()]; let done = 0;
    for (let i = 0; i < urls.length; i += 12) {
      const batch = urls.slice(i, i + 12);
      try {
        const res = await fetch("/api/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ urls: batch }) });
        const out = res.ok ? (await res.json()).results : {};
        for (const u of batch) for (const key of byUrl.get(u)) m.verify[key] = { ...(out[u] || { status: "error", note: "No answer from the checker" }), at: P.today() };
      } catch (_) { for (const u of batch) for (const key of byUrl.get(u)) m.verify[key] = { status: "error", note: "Checker unreachable", at: P.today() }; }
      done += batch.length; P.save(); onProgress && onProgress(done, urls.length);
    }
    P.save();
  }

  /* ---------- shared bits ---------- */
  const VBADGE = {
    ok: ["✓ Verified live", "ok"], closed: ["✗ Opening closed", "bad"], dead: ["✗ Link broken", "bad"], manual: ["Check it yourself", "warn"],
    error: ["Couldn’t reach it", "warn"], nolink: ["No link yet", "warn"], unchecked: ["Not checked yet", "idle"],
  };
  const vbadge = key => { const [t, k] = VBADGE[vstat(key)] || VBADGE.unchecked; return `<span class="av-badge ${k}" title="${esc(P.meta().verify[key]?.note || "")}">${t}</span>`; };
  const payBadge = (pay, job) => pay === "ok" ? `<span class="av-badge ok">${esc(job.compensation)}</span>` : pay === "unknown" ? `<span class="av-badge idle">Pay not published</span>` : `<span class="av-badge bad">Below your floor</span>`;
  const bots = (i, cls = "") => `<svg viewBox="-44 -190 88 96" class="ob-avatar ${cls}" aria-hidden="true">${R.robot(R.CREW[i])}</svg>`;

  /* ============================== HUNT PAGE ============================== */
  const U = { q: "", filter: "all", sort: "jobs", limit: 60, sel: new Set(), any: false, minLPA: "", unknownPay: true, cand: null, phase: "choose" };
  let page;
  function loadFromMission(c) {
    const m = P.mission(c); U.cand = c;
    U.sel = new Set(m.companies); U.any = !!m.any; U.minLPA = m.minLPA || ""; U.unknownPay = m.unknownPay !== false;
  }
  function renderHunt() {
    const c = S.candidate; if (U.cand !== c) loadFromMission(c);
    if (U.phase === "run") return;
    const all = companyList(c), p = P.prefs(c);
    const q = U.q.trim().toLowerCase();
    let list = all.filter(e => (!q || e.name.toLowerCase().includes(q)) && ({ all: true, hr: e.st.hr > 0, alumni: e.st.alumni > 0, eng: e.st.eng > 0, jobs: e.jobs.length > 0, any: e.st.total > 0 })[U.filter]);
    list.sort(U.sort === "name" ? (a, b) => a.name.localeCompare(b.name) : U.sort === "people" ? (a, b) => b.st.total - a.st.total || b.jobs.length - a.jobs.length : (a, b) => b.jobs.length - a.jobs.length || b.st.total - a.st.total);
    const shown = list.slice(0, U.limit);
    const tot = { hr: 0, alumni: 0, eng: 0, all: 0 }; all.forEach(e => { tot.hr += e.st.hr; tot.alumni += e.st.alumni; tot.eng += e.st.eng; tot.all += e.st.total; });
    const fam = p.roles.map(k => ({ backend: "Backend", sde: "SDE", fullstack: "Full-stack", data: "Data / ML", frontend: "Frontend", devops: "DevOps", quant: "Quant" }[k])).filter(Boolean).join(" · ");
    const nSel = U.sel.size, ready = U.any ? true : nSel > 0;
    page.innerHTML = `<div class="ob-wrap hunt">
      <header class="ob-hello"><div><div class="ob-eyebrow"><i></i> STEP 2 OF 3 · THE HUNT</div>
        <h1>Who would you love <em>to work with?</em></h1>
        <p>Pick company blocks, or stay open to any company as long as your minimum pay is met. Then a detective agent goes looking.</p></div>
        <div class="ob-hello-actions"><div class="ob-switch" role="group" aria-label="Candidate">${["Vaanya", "Vrinda"].map(n => `<button type="button" data-act="cand" data-c="${n}" aria-pressed="${n === c}">${n}</button>`).join("")}</div></div></header>
      <ol class="hu-steps" aria-label="Progress"><li class="done"><b>1</b>Tune picks</li><li class="on"><b>2</b>Choose companies</li><li><b>3</b>Detective hunts</li><li><b>4</b>Jobs on your tracker</li></ol>
      <section class="ob-card hu-target"><div>${bots(0)}</div><p><b>Hunting for ${esc(c)}</b><span>${esc(fam || "Your role types")} · ${esc(({ entry: "early career", mid: "SDE II", senior: "senior" })[p.level])} · ${esc(p.places.slice(0, 4).join(", "))}${p.places.length > 4 ? "…" : ""}${p.skills.length ? " · " + esc(p.skills.slice(0, 4).join(", ")) : ""}</span></p><button class="button button-quiet" type="button" data-act="tune">⚙ Tune</button></section>
      <div class="hu-modes" role="radiogroup" aria-label="How to choose">
        <button type="button" role="radio" aria-checked="${!U.any}" class="hu-mode ${!U.any ? "on" : ""}" data-act="mode" data-v="pick"><b>Choose companies</b><span>Select the blocks below. ${tot.all ? `You have <i>${tot.all}</i> contacts across them: HR/TA ${tot.hr}, alumni ${tot.alumni}, engineers ${tot.eng}.` : ""}</span></button>
        <button type="button" role="radio" aria-checked="${U.any}" class="hu-mode ${U.any ? "on" : ""}" data-act="mode" data-v="any"><b>Open to any company</b><span>As long as your minimum pay is met. The detective looks everywhere.</span></button>
      </div>
      <section class="ob-card hu-pay"><div><b>Minimum fixed pay</b><span>Only used when a listing shows pay. Orbit never guesses a salary.</span></div>
        <label class="hu-input"><input id="hu-pay" inputmode="decimal" value="${esc(U.minLPA)}" placeholder="35" aria-label="Minimum fixed pay in lakhs per annum"><em>LPA</em></label>
        <label class="hu-check"><input type="checkbox" id="hu-unk" ${U.unknownPay ? "checked" : ""}> Keep roles that don't publish pay</label></section>
      ${U.any ? `<div class="ob-empty hu-any">${bots(0)}<h3>Every company is on the table</h3><p>The detective will watch all ${all.length} companies in your list for roles that fit${U.minLPA ? ` and meet ${esc(U.minLPA)} LPA` : ""}.</p></div>` : `
      <div class="hu-bar"><label class="searchbox hu-search"><span>⌕</span><input id="hu-q" type="search" placeholder="Search companies…" value="${esc(U.q)}" autocomplete="off"></label>
        <div class="hu-chips" role="group" aria-label="Filter companies">${[["all", "All"], ["jobs", "Has openings"], ["hr", "HR / TA"], ["alumni", "Alumni"], ["eng", "Engineers"]].map(([k, l]) => `<button type="button" aria-pressed="${U.filter === k}" data-act="filter" data-v="${k}">${l}</button>`).join("")}</div>
        <select id="hu-sort" aria-label="Sort companies"><option value="jobs" ${U.sort === "jobs" ? "selected" : ""}>Most openings</option><option value="people" ${U.sort === "people" ? "selected" : ""}>Most contacts</option><option value="name" ${U.sort === "name" ? "selected" : ""}>A–Z</option></select></div>
      <div class="hu-bulk"><span>${plural(list.length, "company", "companies")} shown</span><button type="button" class="ob-link" data-act="sel-shown">Select all shown</button><button type="button" class="ob-link" data-act="sel-people">Select all with contacts</button><button type="button" class="ob-link" data-act="sel-none">Clear</button></div>
      <div class="hu-grid" role="group" aria-label="Companies">${shown.map(e => block(e)).join("") || `<p class="ob-colempty">No companies match.</p>`}</div>
      ${list.length > shown.length ? `<div class="ob-more-row"><button class="button button-quiet" type="button" data-act="more">Show ${Math.min(60, list.length - shown.length)} more</button></div>` : ""}`}
      <div class="hu-dock" role="region" aria-label="Start the hunt"><div><b>${U.any ? "Open to any company" : plural(nSel, "company", "companies") + " selected"}</b><span>${U.minLPA ? `Minimum pay ${esc(U.minLPA)} LPA` : "No minimum pay set"} · ${U.unknownPay ? "unpublished pay kept" : "published pay only"}</span></div>
        <button class="button button-bright big" type="button" data-act="start" ${ready ? "" : "disabled"}>${S && P.mission(c).started ? "Update and hunt again" : "Start the hunt"} →</button></div>
    </div>`;
  }
  const block = e => {
    const on = U.sel.has(e.key), s = e.st;
    return `<button type="button" class="hu-co ${on ? "sel" : ""}" role="checkbox" aria-checked="${on}" data-act="co" data-k="${esc(e.key)}">
      <span class="hu-tick" aria-hidden="true">✓</span>${A.logo(e.name)}<b>${esc(e.name)}</b>
      <small>${e.jobs.length ? plural(e.jobs.length, "opening") : "No openings yet"}</small>
      <span class="hu-badges">${s.total ? `${s.hr ? `<i class="hr">HR ${s.hr}</i>` : ""}${s.alumni ? `<i class="al">Alumni ${s.alumni}</i>` : ""}${s.eng ? `<i class="en">Eng ${s.eng}</i>` : ""}${!s.hr && !s.alumni && !s.eng ? `<i>${plural(s.total, "contact")}</i>` : ""}` : `<i class="none">No contacts yet</i>`}</span></button>`;
  };

  function bindHunt() {
    page.addEventListener("click", e => {
      const b = e.target.closest("[data-act]"); if (!b) return; const act = b.dataset.act, c = S.candidate;
      if (act === "cand") { P.setCandidate(b.dataset.c); history.replaceState(null, "", "/apply?tab=choose&c=" + b.dataset.c); U.q = ""; renderHunt(); }
      else if (act === "tune") P.openTune();
      else if (act === "mode") { U.any = b.dataset.v === "any"; renderHunt(); }
      else if (act === "filter") { U.filter = b.dataset.v; U.limit = 60; renderHunt(); }
      else if (act === "more") { U.limit += 60; renderHunt(); }
      else if (act === "co") { const k = b.dataset.k; U.sel.has(k) ? U.sel.delete(k) : U.sel.add(k); b.classList.toggle("sel", U.sel.has(k)); b.setAttribute("aria-checked", String(U.sel.has(k))); dock(); }
      else if (act === "sel-shown") { $$(".hu-co", page).forEach(x => U.sel.add(x.dataset.k)); renderHunt(); }
      else if (act === "sel-people") { companyList(c).filter(x => x.st.total).forEach(x => U.sel.add(x.key)); renderHunt(); }
      else if (act === "sel-none") { U.sel.clear(); renderHunt(); }
      else if (act === "start") startHunt();
    });
    page.addEventListener("input", e => {
      if (e.target.id === "hu-q") { U.q = e.target.value; U.limit = 60; const pos = e.target.selectionStart; renderHunt(); const q = $("#hu-q", page); q.focus(); q.setSelectionRange(pos, pos); }
      else if (e.target.id === "hu-pay") { U.minLPA = e.target.value.replace(/[^\d.]/g, ""); dock(); }
      else if (e.target.id === "hu-unk") { U.unknownPay = e.target.checked; dock(); }
    });
    page.addEventListener("change", e => { if (e.target.id === "hu-sort") { U.sort = e.target.value; renderHunt(); } });
  }
  function dock() {
    const d = $(".hu-dock", page); if (!d) return;
    const n = U.sel.size;
    $("b", d).textContent = U.any ? "Open to any company" : plural(n, "company", "companies") + " selected";
    $("span", d).textContent = `${U.minLPA ? "Minimum pay " + U.minLPA + " LPA" : "No minimum pay set"} · ${U.unknownPay ? "unpublished pay kept" : "published pay only"}`;
    $(".button", d).disabled = !(U.any || n > 0);
  }

  /* ---------- the detective at work ---------- */
  function sceneSVG(c) {
    const sel = U.any ? "all companies" : plural(U.sel.size, "company", "companies");
    const board = (i, y, t, sub) => `<g class="hs-board" data-i="${i}" transform="translate(600,${y})"><rect width="330" height="96" rx="18" fill="#FFFDF8" stroke="rgba(32,41,35,.2)"/><rect x="14" y="14" width="10" height="10" rx="5" fill="#B87860"/><text x="34" y="24" font-family="DM Mono, monospace" font-size="13" letter-spacing="2" fill="#6F5C4B">${t}</text>
      ${[0, 1, 2, 3, 4].map(k => `<rect class="hs-row" x="14" y="${38 + k * 11}" width="${[250, 200, 280, 170, 230][k]}" height="6" rx="3" fill="rgba(32,41,35,.12)"/>`).join("")}<text x="316" y="84" text-anchor="end" font-size="12" font-weight="700" fill="#426B56">${sub}</text></g>`;
    return `<svg viewBox="0 0 1000 440" class="hs-svg" aria-hidden="true">
      <defs><pattern id="hsGrid" width="50" height="50" patternUnits="userSpaceOnUse"><path d="M50 0H0V50" fill="none" stroke="rgba(32,41,35,.05)"/></pattern></defs>
      <rect width="1000" height="440" rx="26" fill="#EFEADF"/><rect width="1000" height="440" rx="26" fill="url(#hsGrid)"/><rect y="372" width="1000" height="68" fill="#E3DCCB"/>
      <text x="30" y="40" font-family="DM Mono, monospace" font-size="13" letter-spacing="2.4" fill="#6F5C4B">CASE FILE · ${esc(c.toUpperCase())} · ${esc(sel.toUpperCase())}</text>
      ${board(0, 60, "CAREER PORTALS", "first")}${board(1, 170, "LINKEDIN POSTS", "visible posts only")}${board(2, 280, "JOB PLATFORMS", "public listings")}
      <line id="hs-beam" x1="330" y1="300" x2="600" y2="108" stroke="#B87860" stroke-width="3" stroke-dasharray="7 9" opacity="0"/>
      <g id="hs-cards">${Array.from({ length: 15 }, (_, i) => `<g class="hs-card" opacity="0" data-b="${Math.floor(i / 5)}"><rect x="-26" y="-18" width="52" height="36" rx="8" fill="#FFFDF8" stroke="rgba(32,41,35,.28)"/><rect x="-18" y="-8" width="36" height="4" rx="2" fill="rgba(32,41,35,.18)"/><rect x="-18" y="2" width="20" height="8" rx="4" fill="#426B56"/></g>`).join("")}</g>
      <g transform="translate(210,372) scale(1.5)" class="hs-det">${R.robot(R.CREW[0])}</g>
      <g class="hs-bubble"><rect x="70" y="40" width="190" height="40" rx="20" fill="#426B56"/><path d="M150 80 L158 92 L166 80Z" fill="#426B56"/><text x="165" y="66" text-anchor="middle" font-size="14" font-weight="700" fill="#fff" id="hs-say">Let me take a look…</text></g>
    </svg>`;
  }
  const STAGES = [
    [0, "Detective", "Watching career portals, LinkedIn posts and job platforms"],
    [1, "Analyst", "Filtering by skills, fit score and your pay floor"],
    [2, "Verifier", "Opening every listing to confirm it is real and still open"],
    [3, "Connector", "Lining up HR/TA, alumni and engineer contacts you added"],
  ];
  async function startHunt() {
    const c = S.candidate, m = P.meta();
    const minLPA = parseFloat(U.minLPA) || 0;
    m.mission[c] = { companies: [...U.sel], any: U.any, minLPA, unknownPay: U.unknownPay, started: P.today() };
    m.today[c] = { date: P.today(), keys: [], extra: 0 };
    P.save(); U.phase = "run";
    page.innerHTML = `<div class="ob-wrap ob-run"><header class="ob-hello"><div><div class="ob-eyebrow"><i></i> STEP 3 OF 3 · THE HUNT IS ON</div><h1>The detective is <em>on the lookout.</em></h1><p>${U.any ? "Looking across every company" : "Looking at " + plural(U.sel.size, "company", "companies")}${minLPA ? ` with a ${minLPA} LPA minimum` : ""}. Four agents, one careful pass.</p></div></header>
      <div class="ob-scene">${sceneSVG(c)}</div>
      <ol class="hs-stages">${STAGES.map(([i, n, t]) => `<li data-s="${i}"><span class="hs-av">${bots(i)}</span><div><b>${n}</b><small>${t}</small><em class="hs-out"></em><i class="hs-bar"><u></u></i></div><span class="hs-dot"></span></li>`).join("")}</ol>
      <div class="hs-done hidden" id="hs-done"></div></div>`;
    const set = (i, state, text, pct) => { const li = $(`.hs-stages li[data-s="${i}"]`, page); li.className = state; if (text != null) $(".hs-out", li).textContent = text; if (pct != null) $(".hs-bar u", li).style.width = pct + "%"; };
    const say = t => { const e = $("#hs-say", page); if (e) e.textContent = t; };
    animateScene();

    /* 1 detective: reads what the daily agent run has put in the sheets */
    set(0, "on", "Scanning…", 10); say("Checking career portals…");
    const scopeJobs = A.allJobs(c).filter(j => P.inScope(j, c) && !A.isHistorical(j));
    const cos = new Set(scopeJobs.map(j => norm(j.company))).size;
    await count(n => set(0, "on", `${n} openings at ${plural(cos, "company", "companies")}`, 40 + 60 * n / Math.max(1, scopeJobs.length)), scopeJobs.length, 1600);
    set(0, "done", `Found ${scopeJobs.length} openings at ${plural(cos, "company", "companies")}`, 100);
    /* 2 analyst */
    say("Scoring the fit…"); set(1, "on", "Scoring…", 15);
    const rows = huntList(c);
    await count(n => set(1, "on", `${n} of ${scopeJobs.length} fit`, 20 + 80 * n / Math.max(1, rows.length)), rows.length, 1400);
    const strong = rows.filter(r => r.fit.score >= 80).length;
    set(1, "done", `${rows.length} fit your skills, level, place and pay · ${strong} strong`, 100);
    /* 3 verifier: real link checks, best fits first */
    say("Double-checking links…"); set(2, "on", "Starting…", 4);
    const top = rows.slice(0, 40);
    await verifyKeys(c, top, (d, t) => set(2, "on", `Checked ${d} of ${t} links`, 4 + 96 * d / t));
    const vs = top.map(r => vstat(r.key));
    const ok = vs.filter(x => x === "ok").length, bad = vs.filter(x => x === "dead" || x === "closed").length, hand = vs.filter(x => ["manual", "error", "nolink"].includes(x)).length;
    set(2, "done", `${ok} confirmed live${bad ? ` · ${bad} pulled (closed or broken)` : ""}${hand ? ` · ${hand} to check by hand` : ""}`, 100);
    /* 4 connector */
    say("Who can help?"); set(3, "on", "Matching…", 30); await sleep(900);
    const avail = rows.filter(r => !["dead", "closed"].includes(vstat(r.key)));
    const withP = new Set(avail.filter(r => A.getContacts(c, r.job.company).length).map(r => norm(r.job.company)));
    const allP = [...withP].flatMap(k => A.getContacts(c, companyList(c).find(e => e.key === k)?.name || k));
    const st = stats(allP);
    set(3, "done", withP.size ? `${plural(withP.size, "company", "companies")} with contacts · HR ${st.hr} · alumni ${st.alumni} · engineers ${st.eng}` : "No contacts for these companies yet. Listing links are still ready.", 100);
    say("Case closed.");
    U.phase = "done";
    const companiesAvail = new Set(avail.map(r => norm(r.job.company))).size;
    const done = $("#hs-done", page);
    done.classList.remove("hidden");
    done.innerHTML = `<div>${bots(0, "big")}</div><div><h2>${avail.length ? `${plural(avail.length, "job")} available at ${plural(companiesAvail, "company", "companies")}` : "Nothing matched yet"}</h2><p>${avail.length ? "Each opening is on your tracker with its link, tracking details and referral options. Nothing has been sent to anyone." : "Try widening your companies, role types or pay floor. The detective checks again whenever your sheets update."}</p></div>
      <div class="hs-cta"><button class="button button-bright big" type="button" id="hs-picks">See today's picks →</button><a class="button button-quiet" href="/person?view=available">Open my tracker</a><button class="button button-quiet" type="button" id="hs-again">Change companies</button></div>`;
    $("#hs-again", page).addEventListener("click", () => { U.phase = "choose"; renderHunt(); });
    $("#hs-picks", page).addEventListener("click", () => P.showTab("picks"));
    if (avail.length) P.celebrate("The hunt is done", `${avail.length} jobs are waiting on your tracker.`);
  }
  async function count(fn, to, ms) { const steps = reduced ? 1 : 16; for (let i = 1; i <= steps; i++) { fn(Math.round(to * i / steps)); await sleep(ms / steps); } }
  function animateScene() {
    if (!window.gsap || reduced) return;
    const svg = $(".hs-svg", page); if (!svg) return;
    const beam = $("#hs-beam", svg), boards = $$(".hs-board", svg), cards = $$(".hs-card", svg), det = $(".hs-det", svg);
    const arm = $(".rb-arm-r", det);
    gsap.to(arm, { rotation: -75, transformOrigin: "50% 0%", duration: .6, ease: "power2.out" });
    const tl = gsap.timeline({ repeat: -1 });
    const ys = [108, 218, 328];
    boards.forEach((b, i) => {
      const t0 = i * 2.4;
      tl.set(beam, { attr: { x2: 600, y2: ys[i] }, opacity: 1 }, t0)
        .fromTo(b, { scale: 1 }, { scale: 1.03, svgOrigin: `765 ${ys[i]}`, duration: .35, yoyo: true, repeat: 3 }, t0)
        .to(b.querySelectorAll(".hs-row"), { fill: "rgba(184,120,96,.4)", duration: .2, stagger: .12 }, t0)
        .to(b.querySelectorAll(".hs-row"), { fill: "rgba(32,41,35,.12)", duration: .4 }, t0 + 1.8);
      cards.filter(k => +k.dataset.b === i).forEach((k, n) => {
        tl.set(k, { x: 640, y: ys[i], opacity: 1 }, t0 + .3 + n * .3)
          .to(k, { x: 300, y: 335 - n * 6, duration: 1, ease: "power2.in" }, t0 + .3 + n * .3)
          .to(k, { opacity: 0, duration: .15 }, t0 + 1.3 + n * .3);
      });
    });
    tl.to(beam, { opacity: 0, duration: .2 }, 7.2).to({}, { duration: .6 }, 7.2);
  }

  /* ============================== TRACKER · JOBS AVAILABLE ============================== */
  const V = { open: new Set(), panelCo: null, panelJob: null, drafts: {}, openDraft: null, verifying: false };
  function draftText(c, ct, job, co) {
    const first = (ct.name || "").trim().split(/\s+/)[0] || "there", role = job ? job.title : "an engineering role", skills = P.prefs(c).skills.slice(0, 3).join(", ") || "backend engineering";
    const cat = catOf(ct), alum = RE.alumni.test(textOf(ct));
    if (cat === "hr") return `Hi ${first}, I came across the ${role} opening at ${co} and it looks like a strong match for my background in ${skills}. Could you point me to the right process, or share my profile with the hiring team? Happy to send my resume. Thank you!\n${c}`;
    if (alum) return `Hi ${first}, fellow alum here. I'm looking at the ${role} role at ${co}. Would you be open to a 10-minute chat about the team, and a referral if it feels like a fit? I'd really appreciate your take.\nThanks, ${c}`;
    if (cat === "eng") return `Hi ${first}, I'm exploring the ${role} role at ${co}. Could I ask what the team works on and what the interview looks like? My background is in ${skills}, and I'd value your honest view.\nThanks, ${c}`;
    return `Hi ${first}, I'm interested in the ${role} role at ${co}. Do you know someone on the team, or would you be open to a quick chat about it? Happy to share my resume.\nThanks, ${c}`;
  }
  const rkey = (c, co, ct) => `${c}|${norm(co)}|${norm(ct.name)}`;

  function renderAvail(host) {
    const c = S.candidate, ms = P.mission(c);
    if (!ms.started) { host.innerHTML = `<div class="ob-empty">${bots(0, "xl")}<h3>No hunt yet</h3><p>Choose the companies you'd love to join, or stay open to any company above your minimum pay. The detective does the rest.</p><a class="button button-bright" href="/apply?tab=choose">Choose companies →</a></div>`; return; }
    const rows = huntList(c), live = rows.filter(r => !["dead", "closed"].includes(vstat(r.key))), pulled = rows.length - live.length;
    const groups = new Map();
    for (const r of live) { const k = norm(r.job.company); (groups.get(k) || groups.set(k, { key: k, name: r.job.company, rows: [] }).get(k)).rows.push(r); }
    const cos = [...groups.values()].sort((a, b) => b.rows[0].fit.score - a.rows[0].fit.score || b.rows.length - a.rows.length);
    if (!cos.length) { host.innerHTML = `<div class="ob-empty">${bots(0, "xl")}<h3>Nothing available right now</h3><p>${pulled ? plural(pulled, "opening") + " were pulled as closed or broken. " : ""}Widen your companies or pay floor, or check again after your sheets update.</p><a class="button button-quiet" href="/apply?tab=choose">Edit my hunt</a></div>`; return; }
    if (!V.panelCo || !groups.has(V.panelCo)) V.panelCo = cos[0].key;
    const unchecked = live.filter(r => vstat(r.key) === "unchecked").length;
    const focus = groups.get(V.panelCo);
    host.innerHTML = `<div class="av-head"><div><h2>Jobs available</h2><p>${plural(live.length, "opening")} at ${plural(cos.length, "company", "companies")}${pulled ? ` · ${plural(pulled, "opening")} pulled by the verifier` : ""} · ${ms.any ? "open to any company" : plural(ms.companies.length, "company", "companies") + " chosen"}${ms.minLPA ? ` · min ${ms.minLPA} LPA` : ""}</p></div>
      <div class="av-head-actions"><button class="button button-quiet" type="button" data-av="verify" ${V.verifying ? "disabled" : ""}>${V.verifying ? "Verifying…" : unchecked ? `✓ Verify ${unchecked} unchecked` : "↻ Re-verify links"}</button><a class="button button-quiet" href="/apply?tab=choose">Edit my hunt</a></div></div>
      <div class="av-grid"><div class="av-list">${cos.map(g => avCompany(g, c)).join("")}</div>
      <aside class="av-panel" aria-label="Reach out options">${panel(focus, c)}</aside></div>`;
  }
  function avCompany(g, c) {
    const open = V.open.has(g.key), contacts = A.getContacts(c, g.name), st = stats(contacts);
    const best = g.rows[0].fit, vOk = g.rows.filter(r => vstat(r.key) === "ok").length;
    return `<section class="av-co ${open ? "open" : ""} ${V.panelCo === g.key ? "focus" : ""}" data-co="${esc(g.key)}">
      <button type="button" class="av-sum" data-av="toggle" data-co="${esc(g.key)}" aria-expanded="${open}">${A.logo(g.name)}
        <div class="av-sum-main"><b>${esc(g.name)}</b><small>${plural(g.rows.length, "job")} · best fit ${best.score} · ${vOk ? `${vOk} verified live` : "not verified yet"}${g.rows.some(r => (r.job.tags || []).includes("Referral asked")) ? " · referral asked" : ""}</small></div>
        <span class="av-people">${st.total ? `${st.hr ? `<i class="hr">HR ${st.hr}</i>` : ""}${st.alumni ? `<i class="al">Alumni ${st.alumni}</i>` : ""}${st.eng ? `<i class="en">Eng ${st.eng}</i>` : ""}${!st.hr && !st.alumni && !st.eng ? `<i>${st.total} contacts</i>` : ""}` : `<i class="none">No contacts</i>`}</span>
        <span class="chevron" aria-hidden="true">⌄</span></button>
      ${open ? `<div class="av-body">${g.rows.map(r => avJob(r, c, g)).join("")}</div>` : ""}</section>`;
  }
  function avJob(r, c, g) {
    const j = r.job, url = A.jobUrl(j), st = A.jobState(j, c), status = A.jobStatus(j, c), reasons = r.fit.comps.filter(x => x.got > 0 && x.max > 0).sort((a, b) => b.got - a.got).slice(0, 3);
    return `<article class="av-job" data-key="${esc(r.key)}"><div class="av-job-main"><h4>${esc(j.title)}</h4>
      <div class="av-meta"><span>${esc(j.location || "Location not listed")}</span><span class="lab ${r.fit.label.toLowerCase()}">Fit ${r.fit.score} · ${r.fit.label}</span>${payBadge(r.pay, j)}${vbadge(r.key)}${(j.tags || []).map(t => `<span class="av-badge ${/referr|asked/i.test(t) ? "ref" : /reject|deadline|not /i.test(t) ? "bad" : "idle"}">${esc(t)}</span>`).join("")}</div>
      ${j.notes ? `<p class="av-sheetnote"><b>Your sheet</b> ${esc(j.notes.slice(0, 160))}</p>` : ""}
      <ul class="av-reasons">${reasons.map(x => `<li>${esc(x.note)}</li>`).join("")}</ul></div>
      <div class="av-job-actions">${url ? `<a class="ob-btn primary" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Open listing ↗</a>` : `<span class="ob-nocontact">No listing link yet</span>`}
        <label class="av-status"><span class="sr-only">Stage</span><select data-av="status" data-key="${esc(r.key)}">${A.statuses.map(s => `<option ${s === status ? "selected" : ""}>${s}</option>`).join("")}</select></label>
        <button class="ob-btn" type="button" data-av="notes" data-key="${esc(r.key)}">Notes</button>
        <button class="ob-btn ghost" type="button" data-av="reach" data-co="${esc(g.key)}" data-key="${esc(r.key)}">Reach out →</button></div>
      <div class="av-track">${status !== "Not started" ? `<b>${esc(status)}</b>${P.appliedOf(j, c) ? ` · applied ${esc(A.dateLabel(P.appliedOf(j, c)))}` : ""}` : "Not started"}${st.nextStep ? ` · Next: ${esc(st.nextStep)}` : ""}${st.applicationNotes ? ` · <em>${esc(st.applicationNotes.slice(0, 80))}${st.applicationNotes.length > 80 ? "…" : ""}</em>` : ""}</div></article>`;
  }
  function sheetBox(g, c, job) {
    const co = (A.profile(c)?.companies || []).find(x => norm(x.name) === g.key) || {};
    const tags = [...new Set([...(job.tags || []), ...(co.tags || [])])], notes = [job.notes, co.notes].filter(Boolean).join(" · ");
    if (!tags.length && !notes) return "";
    return `<div class="av-sheetbox"><b>From your sheet</b>${tags.map(t => `<span class="av-badge ${/referr|asked/i.test(t) ? "ref" : "idle"}">${esc(t)}</span>`).join("")}${notes ? `<p>${esc(notes.slice(0, 260))}</p>` : ""}</div>`;
  }
  function panel(g, c) {
    const contacts = A.getContacts(c, g.name), jobs = g.rows;
    if (!V.panelJob || !jobs.find(r => r.key === V.panelJob)) V.panelJob = jobs[0].key;
    const job = jobs.find(r => r.key === V.panelJob).job, m = P.meta();
    const grouped = { hr: [], alumni: [], eng: [], other: [] };
    contacts.forEach(ct => (RE.alumni.test(textOf(ct)) && catOf(ct) !== "hr" ? grouped.alumni : grouped[catOf(ct)]).push(ct));
    const person = ct => {
      const key = rkey(c, g.name, ct), done = m.reach[key], open = V.openDraft === key, days = done ? P.dayDiff(done.at, P.today()) : 0;
      const text = V.drafts[key] ?? draftText(c, ct, job, g.name);
      return `<li class="av-person"><div class="av-person-top"><div><b>${esc(ct.name)}</b><small>${esc(ct.title || ct.source_sheet || "")}</small></div>${done ? `<span class="av-badge ok">Reached out${days ? ` · ${days}d ago` : " · today"}</span>` : ""}${done && days >= 4 ? `<span class="av-badge warn">Follow up</span>` : ""}</div>
        <div class="av-person-actions"><button class="ob-btn chip" type="button" data-av="draft" data-k="${esc(key)}">${open ? "Hide draft" : done ? "View draft" : "Draft a note"}</button></div>
        ${open ? `<div class="av-draft"><textarea data-draft="${esc(key)}" rows="6" aria-label="Draft message to ${esc(ct.name)}">${esc(text)}</textarea><div class="av-draft-actions"><button class="ob-btn primary" type="button" data-av="copy" data-k="${esc(key)}">Copy</button><button class="ob-btn" type="button" data-av="sent" data-k="${esc(key)}" data-name="${esc(ct.name)}">${done ? "Sent again" : "I sent it"}</button></div><small>Orbit never sends this. Copy it, edit it, and send it yourself.</small></div>` : ""}</li>`;
    };
    const section = k => grouped[k].length ? `<div class="av-grp"><h5>${LABEL[k]} <span>${grouped[k].length}</span></h5><ul>${grouped[k].map(person).join("")}</ul></div>` : "";
    return `<div class="av-panel-in"><div class="ob-card-h"><h3>Reach out · ${esc(g.name)}</h3></div>
      ${sheetBox(g, c, job)}
      <label class="av-pick">About this opening<select data-av="pickjob">${jobs.map(r => `<option value="${esc(r.key)}" ${r.key === V.panelJob ? "selected" : ""}>${esc(r.job.title)}</option>`).join("")}</select></label>
      ${contacts.length ? section("hr") + section("alumni") + section("eng") + section("other") : `<div class="ob-empty small">${bots(3)}<p>No contact for ${esc(g.name)} yet. Add one to your sheet's contacts, or use the listing link to apply directly.</p></div>`}
      <p class="av-note">Contacts come only from the lists you added. Orbit doesn't look people up or send anything.</p></div>`;
  }

  function bindAvail(host) {
    host.addEventListener("click", async e => {
      const b = e.target.closest("[data-av]"); if (!b) return; const act = b.dataset.av, c = S.candidate;
      const rerender = () => renderAvail(host);
      if (act === "toggle") { const k = b.dataset.co; V.open.has(k) ? V.open.delete(k) : V.open.add(k); V.panelCo = k; V.panelJob = null; rerender(); }
      else if (act === "reach") { V.panelCo = b.dataset.co; V.panelJob = b.dataset.key; V.open.add(b.dataset.co); rerender(); $(".av-panel", host)?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "nearest" }); }
      else if (act === "notes") { const job = A.allJobs(c).find(j => A.roleKey(c, j) === b.dataset.key); job && P.openEditor(job); }
      else if (act === "draft") { V.openDraft = V.openDraft === b.dataset.k ? null : b.dataset.k; rerender(); }
      else if (act === "copy") {
        const ta = $(`textarea[data-draft="${CSS.escape(b.dataset.k)}"]`, host); if (!ta) return;
        try { await navigator.clipboard.writeText(ta.value); } catch (_) { ta.select(); document.execCommand("copy"); }
        P.toast("Copied. Paste it into your own message.", { sub: "Orbit never sends anything for you." });
      }
      else if (act === "sent") {
        const k = b.dataset.k; P.meta().reach[k] = { at: P.today(), job: V.panelJob }; P.log(c, "reach", k); P.save();
        P.toast("Marked as reached out", { sub: `${b.dataset.name} · we'll nudge you after 4 days` }); rerender();
      }
      else if (act === "verify" && !V.verifying) {
        V.verifying = true; rerender();
        const rows = huntList(c).filter(r => !["dead", "closed"].includes(vstat(r.key))).sort((a, b2) => (vstat(a.key) === "unchecked" ? 0 : 1) - (vstat(b2.key) === "unchecked" ? 0 : 1)).slice(0, 40);
        P.toast(`Checking ${plural(rows.length, "listing")}…`, { sub: "One polite request per site." });
        await verifyKeys(c, rows, () => {}); V.verifying = false; rerender();
        const bad = rows.filter(r => ["dead", "closed"].includes(vstat(r.key))).length;
        P.toast("Verification done", { sub: bad ? `${plural(bad, "opening")} pulled as closed or broken.` : "Everything checked looks live." });
      }
    });
    host.addEventListener("change", e => {
      const t = e.target, c = S.candidate;
      if (t.dataset.av === "status") { const job = A.allJobs(c).find(j => A.roleKey(c, j) === t.dataset.key); if (job) P.setStatus(job, t.value, c); }
      else if (t.dataset.av === "pickjob") { V.panelJob = t.value; Object.keys(V.drafts).forEach(k => delete V.drafts[k]); renderAvail(host); }
    });
    host.addEventListener("input", e => { const k = e.target.dataset?.draft; if (k) V.drafts[k] = e.target.value; });
  }

  /* ---------- plumbing ---------- */
  P.hooks.renderAvail = renderAvail;
  function init() {
    if (S.route === "apply") {
      page = $("#hunt-page");
      const q = new URLSearchParams(location.search).get("c"), stored = (() => { try { return localStorage.getItem("orbit.candidate"); } catch (_) { return null; } })();
      P.setCandidate(["Vaanya", "Vrinda"].find(n => n === q) || ["Vaanya", "Vrinda"].find(n => n === stored) || "Vrinda");
      loadFromMission(S.candidate); bindHunt(); renderHunt();
    } else if (S.route === "person") {
      const host = $("#ob-avail"); if (host) { bindAvail(host); renderAvail(host); }
    }
  }
  if (A.ready) setTimeout(init, 0); else window.addEventListener("orbit:ready", () => setTimeout(init, 0), { once: true });
})();
