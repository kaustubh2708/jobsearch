/* Orbit home: factory scene, crew, tour video, journey, live launch cards.
   Everything is derived from a single timeline time `t` (render(t)) so scrubbing
   forwards and backwards always shows a consistent state. */
(() => {
  const home = document.getElementById("home-page");
  if (!home) return;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const NS = "http://www.w3.org/2000/svg";
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- palette ---------- */
  const C = { ink: "#202923", green: "#426B56", clay: "#6F5C4B", terra: "#B87860", paper: "#FFFDF8", ivory: "#F4F1E9", stone: "#EBE6E2" };
  const CREW = [
    { key: "scout", n: "01", name: "Detective", role: "Detective agent", color: C.green, dark: "#2F5240", prop: "hunt", hat: true, bubble: "On the case!",
      does: ["Watches company career portals first", "Reads LinkedIn job posts you can see, and other job platforms", "Records title, place, link and posting date"],
      never: ["Logs in anywhere or bypasses a CAPTCHA", "Scrapes profiles or connection lists", "Applies to anything"] },
    { key: "analyst", n: "02", name: "Analyst", role: "Fit analyst", color: C.clay, dark: "#54463A", prop: "score", bubble: "Scoring the fit…",
      does: ["Matches skills, level, place and pay to your profile", "Scores each role with a plain-language reason", "Sets aside roles that clearly miss"],
      never: ["Invents a salary from a company name", "Promises an interview or an offer", "Hides why a role was rejected"] },
    { key: "guard", n: "03", name: "Verifier", role: "Verifier agent", color: "#34433A", dark: "#222C26", prop: "shield", bubble: "Double-checking…",
      does: ["Opens every listing link and checks it still works", "Flags closed or expired openings", "Removes duplicates and marks third-party listings"],
      never: ["Passes a dead link as ‘verified’", "Overwrites your notes or status", "Marks anything applied on its own"] },
    { key: "connector", n: "04", name: "Connector", role: "Referral connector", color: C.terra, dark: "#8F5A45", prop: "link", bubble: "Who can help?",
      does: ["Lines up the HR/TA, alumni and engineers you already added", "Drafts a polite note you can edit and send yourself", "Shows reach-out status next to each opening"],
      never: ["Looks up people you haven’t added", "Sends a message or request for you", "Reads hidden connection data"] },
  ];

  /* ---------- svg helpers ---------- */
  const robotSVG = c => `
    <g class="rb" data-k="${c.key}">
      <g class="rb-sway">
        <rect x="-36" y="-92" width="72" height="72" rx="22" fill="${c.color}"/>
        <rect x="-36" y="-92" width="72" height="30" rx="16" fill="#fff" opacity=".08"/>
        <rect x="-22" y="-70" width="44" height="30" rx="9" fill="#FFFDF8" opacity=".6"/>
        <circle class="rb-led" cx="-11" cy="-55" r="3.2" fill="${c.dark}"/><circle class="rb-led l2" cx="0" cy="-55" r="3.2" fill="${c.dark}"/><circle class="rb-led l3" cx="11" cy="-55" r="3.2" fill="${c.dark}"/>
        <rect x="-8" y="-100" width="16" height="10" rx="4" fill="${c.dark}"/>
        <g transform="translate(-47,-76)"><g class="rb-arm rb-arm-l"><rect x="-6" y="0" width="12" height="30" rx="6" fill="${c.dark}"/><g transform="translate(0,26)"><g class="rb-fore"><rect x="-5.5" y="0" width="11" height="26" rx="5.5" fill="${c.dark}"/><circle cx="0" cy="27" r="8.5" fill="${c.color}" stroke="${c.dark}" stroke-width="2"/></g></g></g></g>
        <g transform="translate(47,-76)"><g class="rb-arm rb-arm-r"><rect x="-6" y="0" width="12" height="30" rx="6" fill="${c.dark}"/><g transform="translate(0,26)"><g class="rb-fore"><rect x="-5.5" y="0" width="11" height="26" rx="5.5" fill="${c.dark}"/><circle cx="0" cy="27" r="8.5" fill="${c.color}" stroke="${c.dark}" stroke-width="2"/></g></g></g></g>
        <g class="rb-head">
          ${c.hat ? "" : `<line x1="0" y1="-152" x2="0" y2="-172" stroke="${c.dark}" stroke-width="4" stroke-linecap="round"/><circle class="rb-bulb" cx="0" cy="-176" r="6" fill="${C.terra}"/>`}
          <rect x="-36" y="-154" width="72" height="56" rx="20" fill="${c.color}"/>
          <rect x="-36" y="-154" width="72" height="24" rx="14" fill="#fff" opacity=".1"/>
          <rect x="-28" y="-144" width="56" height="36" rx="14" fill="#1B241E"/>
          <g class="rb-eyes"><ellipse class="rb-eye" cx="-12" cy="-127" rx="5.4" ry="6.6" fill="#BFE8CC"/><ellipse class="rb-eye" cx="12" cy="-127" rx="5.4" ry="6.6" fill="#BFE8CC"/></g>
          <path class="rb-mouth" d="M-6 -115 Q0 -110 6 -115" fill="none" stroke="#BFE8CC" stroke-width="2.2" stroke-linecap="round"/>
          <circle cx="-23" cy="-117" r="3.4" fill="${C.terra}" opacity=".55"/><circle cx="23" cy="-117" r="3.4" fill="${C.terra}" opacity=".55"/>
          ${c.hat ? `<g class="rb-hat"><ellipse cx="0" cy="-153" rx="50" ry="9" fill="#3A2F27"/><path d="M-27 -153 Q-27 -184 0 -184 Q27 -184 27 -153Z" fill="#4A3B30"/><rect x="-27" y="-165" width="54" height="8" fill="${C.terra}"/><circle class="rb-bulb" cx="0" cy="-184" r="0" fill="none"/></g>` : ""}
        </g>
      </g>
          </g>`;

  const propSVG = (kind) => {
    const base = `<rect x="0" y="0" width="64" height="50" rx="12" fill="${C.paper}" stroke="rgba(32,41,35,.2)"/>`;
    if (kind === "hunt") return `<g class="prop prop-hunt"><rect x="0" y="0" width="104" height="64" rx="12" fill="${C.paper}" stroke="rgba(32,41,35,.2)"/>${["CAREER PORTALS", "LINKEDIN POSTS", "JOB PLATFORMS"].map((t, i) => `<g class="src src${i}"><rect x="8" y="${7 + i * 18}" width="88" height="15" rx="7.5" fill="rgba(66,107,86,.1)"/><circle cx="17" cy="${14.5 + i * 18}" r="3" fill="${C.terra}"/><text x="25" y="${18 + i * 18}" font-size="7.6" font-weight="700" font-family="DM Mono, monospace" letter-spacing=".4" fill="${C.green}">${t}</text></g>`).join("")}</g>`;
    if (kind === "score") return `<g class="prop prop-score">${base}<text class="score-num" x="32" y="33" text-anchor="middle" font-size="22" font-weight="800" fill="${C.ink}">--</text><rect x="12" y="40" width="40" height="3.5" rx="2" fill="rgba(32,41,35,.12)"/><rect class="score-bar" x="12" y="40" width="0" height="3.5" rx="2" fill="${C.green}"/></g>`;
    if (kind === "link") return `<g class="prop prop-link">${base}<g fill="none" stroke="${C.terra}" stroke-width="4" stroke-linecap="round"><rect x="13" y="16" width="24" height="18" rx="9"/><rect x="27" y="16" width="24" height="18" rx="9" stroke="${C.green}"/></g><text class="link-text" x="32" y="46" text-anchor="middle" font-size="8" font-family="DM Mono, monospace" font-weight="500" fill="${C.clay}" letter-spacing=".5">CONTACT</text></g>`;
    return `<g class="prop prop-shield">${base}<path class="shield-p" d="M32 9 L50 15 V27 C50 36 42 41 32 44 C22 41 14 36 14 27 V15 Z" fill="rgba(66,107,86,.16)" stroke="${C.green}" stroke-width="2.4"/><path class="shield-mark" d="M23 26 L30 33 L42 20" fill="none" stroke="${C.green}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></g>`;
  };

  /* ---------- the factory ---------- */
  const W = 1400, H = 640;
  const S = [150, 410, 670, 930];   // station centres
  const BELT_Y = 388, GATE_X = 1300;
  const V = 170, T = 12;            // belt speed px/s, timeline length
  const CARDS = [
    { title: "Sales Exec",   score: 41, fate: "fit",  ref: false, end: null },
    { title: "SDE II",       score: 76, fate: "link", ref: true,  end: null },
    { title: "Backend Eng",  score: 88, fate: "ok",   ref: true,  end: 1215 },
    { title: "Platform Eng", score: 82, fate: "ok",   ref: true,  end: 1127 },
    { title: "SDE III",      score: 91, fate: "ok",   ref: false, end: 1039 },
  ];
  CARDS.forEach((c, i) => {
    c.x0 = -90 - i * 95;
    c.pass = S.map(s => (s - c.x0) / V);                // time centre reaches each station
    if (c.fate === "fit") c.dropAt = c.pass[1] + .12;
    if (c.fate === "link") c.dropAt = c.pass[2] + .12;
    c.endT = c.end != null ? (c.end - c.x0) / V : null;
  });
  const PHASES = [
    { k: "scout", a: 0,   b: 2.2 }, { k: "analyst", a: 2.2, b: 4.6 }, { k: "guard", a: 4.6, b: 6.4 },
    { k: "connector", a: 6.4, b: 8.3 }, { k: "you", a: 8.3, b: T },
  ];
  const CAPS = {
    scout: ["01 · Detective", "A detective on the lookout", "Watches your chosen companies’ career portals first, then LinkedIn job posts you can see and other job platforms. It records only job facts: title, place, link and posting date.", ["Career portals first", "No logins or CAPTCHA bypass", "No profile scraping"]],
    analyst: ["02 · Analyst", "Filters by skills and fit score", "Compares skills, level, place and pay with your profile, then explains the score. A role that clearly misses goes to the ‘not a fit’ bin instead of your list.", ["Skills match", "Fit score with reasons", "Your pay floor respected"]],
    guard: ["03 · Verifier", "Double-checks everything", "Opens each listing, confirms the link works and the opening is still live, and removes duplicates. A broken or closed role is pulled off the line and labelled, never passed through.", ["Link check", "Opening still live", "Honest labels"]],
    connector: ["04 · Connector", "Referral options, ready to use", "Lines up the HR/TA, alumni and engineer contacts you already added for each company, with a polite draft you can edit and send yourself.", ["Your contacts only", "Drafts, not sends", "Reach-out status"]],
    you: ["05 · You", "Your tracker, and your call", "Verified roles land on your tracker as Jobs available, with the listing link, referral options and tracking details side by side. Nothing is sent or submitted without you.", ["Jobs available", "Review first", "You decide"]],
  };

  const el = (name, attrs = {}, html = "") => { const e = document.createElementNS(NS, name); for (const k in attrs) e.setAttribute(k, attrs[k]); if (html) e.innerHTML = html; return e; };

  function buildFactory() {
    const stage = $("#hx-stage");
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: "xMidYMid meet", "aria-hidden": "true", class: "hx-svg" });
    svg.innerHTML = `
      <defs>
        <linearGradient id="hxWall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F7F4EC"/><stop offset="1" stop-color="#ECE6D8"/></linearGradient>
        <linearGradient id="hxCone" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFF3CC" stop-opacity=".75"/><stop offset="1" stop-color="#FFF3CC" stop-opacity="0"/></linearGradient>
        <pattern id="hxStripe" width="28" height="28" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width="14" height="28" fill="${C.terra}" opacity=".55"/></pattern>
        <pattern id="hxGrid" width="56" height="56" patternUnits="userSpaceOnUse"><path d="M56 0H0V56" fill="none" stroke="rgba(32,41,35,.045)"/></pattern>
        <clipPath id="hxClip"><rect width="${W}" height="${H}" rx="26"/></clipPath>
      </defs>
      <g clip-path="url(#hxClip)">
        <rect width="${W}" height="470" fill="url(#hxWall)"/><rect width="${W}" height="470" fill="url(#hxGrid)"/>
        <rect y="470" width="${W}" height="${H - 470}" fill="#E3DCCB"/><rect y="470" width="${W}" height="6" fill="rgba(32,41,35,.08)"/>
        <rect y="610" width="${W}" height="14" fill="url(#hxStripe)"/>
        <rect x="0" y="62" width="${W}" height="12" fill="#D8D0BF"/><rect x="0" y="62" width="${W}" height="4" fill="#fff" opacity=".35"/>
        <text x="34" y="40" font-family="DM Mono, monospace" font-size="13" letter-spacing="2.4" fill="${C.clay}" opacity=".85">ORBIT FLOOR · SHIFT 01</text>
        <text x="${W - 34}" y="40" text-anchor="end" font-family="DM Mono, monospace" font-size="13" letter-spacing="2.4" fill="${C.clay}" opacity=".85">5 SAMPLE ROLES · ILLUSTRATIVE</text>
        ${S.map((s, i) => `
          <polygon class="cone" points="${s - 16},96 ${s + 16},96 ${s + 120},395 ${s - 120},395" fill="url(#hxCone)"/>
          <line x1="${s}" y1="74" x2="${s}" y2="108" stroke="#8B8272" stroke-width="3"/>
          <path d="M${s - 26} 124 Q${s} 92 ${s + 26} 124 Z" fill="${CREW[i].color}"/>
          <ellipse class="lamp" cx="${s}" cy="124" rx="18" ry="4.5" fill="#FFF3CC"/>
          <g class="sign" transform="translate(${s - 82},134)"><rect width="164" height="30" rx="9" fill="${C.ink}"/><text x="82" y="20" text-anchor="middle" font-family="DM Mono, monospace" font-size="12.5" font-weight="500" letter-spacing="2.2" fill="${C.ivory}">${CREW[i].n} · ${CREW[i].name.toUpperCase()}</text></g>
          <rect x="${s - 70}" y="262" width="11" height="130" rx="4" fill="#CFC6B2"/><rect x="${s + 59}" y="262" width="11" height="130" rx="4" fill="#CFC6B2"/>
          <rect x="${s - 74}" y="252" width="148" height="14" rx="7" fill="#BDB39E"/>`).join("")}
        <!-- robots (behind the belt) -->
        ${CREW.map((c, i) => `<g class="station" data-k="${c.key}" transform="translate(${S[i]},${BELT_Y + 6})">${robotSVG(c)}<g class="prop-wrap" transform="translate(58,-150)">${propSVG(c.prop)}</g>
          <g class="bubble" transform="translate(0,-192)" opacity="0"><rect x="-76" y="-30" width="152" height="34" rx="17" fill="${C.paper}" stroke="${C.ink}" stroke-opacity=".22"/><path d="M-8 4 L0 14 L8 4 Z" fill="${C.paper}" stroke="${C.ink}" stroke-opacity=".22"/><rect x="-10" y="2" width="20" height="4" fill="${C.paper}"/><text y="-8" text-anchor="middle" font-size="13.5" font-weight="700" fill="${C.ink}">${c.bubble}</text></g></g>`).join("")}
        <!-- human gate -->
        <g class="gate" transform="translate(${GATE_X},${BELT_Y + 6})">
          <circle class="you-head" cx="22" cy="-132" r="30" fill="#E8C9A8"/><path d="M-8 -140 Q22 -190 52 -140 Q48 -166 22 -166 Q-4 -166 -8 -140Z" fill="#4A3A2E"/>
          <circle cx="12" cy="-134" r="3.2" fill="${C.ink}"/><circle cx="34" cy="-134" r="3.2" fill="${C.ink}"/><path d="M13 -121 Q22 -113 31 -121" fill="none" stroke="${C.ink}" stroke-width="3" stroke-linecap="round"/>
          <rect x="-16" y="-100" width="76" height="86" rx="26" fill="#6F5C4B"/>
          <g class="you-arm" transform="translate(-14,-82)"><rect x="-6" y="0" width="12" height="42" rx="6" fill="#5C4B3C"/><circle cy="44" r="9" fill="#E8C9A8"/></g>
          <rect x="62" y="-100" width="12" height="104" rx="5" fill="#BDB39E"/>
          <g class="barrier" transform="translate(68,-44)"><rect x="-84" y="-6" width="90" height="12" rx="6" fill="#fff" stroke="${C.ink}" stroke-opacity=".3"/><rect x="-84" y="-6" width="90" height="12" rx="6" fill="url(#hxStripe)"/></g>
          <g class="bubble" transform="translate(-34,-200)" opacity="0"><rect x="-96" y="-34" width="192" height="40" rx="20" fill="${C.green}"/><path d="M-9 6 L0 17 L9 6 Z" fill="${C.green}"/><text y="-9" text-anchor="middle" font-size="15" font-weight="700" fill="#fff">Your call. Review first.</text></g>
        </g>
        <text x="${GATE_X - 90}" y="236" text-anchor="middle" font-family="DM Mono, monospace" font-size="12" letter-spacing="2.2" fill="${C.clay}">FOR YOUR REVIEW</text>
        <path d="M${GATE_X - 168} 244 H${GATE_X - 12}" stroke="${C.clay}" stroke-opacity=".35" stroke-dasharray="3 6"/>
        <!-- bins -->
        ${[[S[1], "NOT A FIT"], [S[2], "LINK BROKEN"]].map(([x, t], i) => `<g class="bin bin${i}" transform="translate(${x},0)"><path d="M-52 482 H52 L44 566 H-44 Z" fill="#CFC6B2"/><path d="M-52 482 H52 L49 496 H-49 Z" fill="#B9AE98"/><text y="556" text-anchor="middle" font-family="DM Mono, monospace" font-size="12" letter-spacing="1.6" fill="${C.clay}">${t}</text></g>`).join("")}
        <!-- belt -->
        <g class="belt">
          <rect x="0" y="${BELT_Y}" width="${W}" height="12" fill="#56635A"/>
          <rect x="0" y="${BELT_Y + 12}" width="${W}" height="52" fill="#3C4840"/>
          <line class="belt-run" x1="-40" y1="${BELT_Y + 5}" x2="${W + 40}" y2="${BELT_Y + 5}" stroke="#A6B3A9" stroke-width="3" stroke-dasharray="14 30"/>
          ${Array.from({ length: 26 }, (_, i) => `<circle class="roller" cx="${24 + i * 56}" cy="${BELT_Y + 40}" r="9" fill="#2D3731" stroke="#566259" stroke-width="2"/>`).join("")}
          <rect x="0" y="${BELT_Y + 64}" width="${W}" height="10" fill="#2A322D"/>
          ${[100, 540, 800, 1150].map(x => `<rect x="${x}" y="${BELT_Y + 74}" width="16" height="96" fill="#9E947F"/>`).join("")}
        </g>
        <!-- cards -->
        <g id="hx-cards">${CARDS.map((c, i) => `
          <g class="card" data-i="${i}"><rect x="-42" y="0" width="84" height="52" rx="10" fill="${C.paper}" stroke="rgba(32,41,35,.28)" stroke-width="1.4"/>
                        <text x="0" y="17" text-anchor="middle" font-size="11" font-weight="800" fill="${C.ink}">${c.title}</text>
            <rect x="-28" y="24" width="56" height="3" rx="1.5" fill="rgba(32,41,35,.13)"/>
            <g class="c-score" opacity="0"><rect x="-32" y="32" width="30" height="14" rx="7" fill="${c.score < 60 ? C.terra : C.green}"/><text x="-17" y="42.6" text-anchor="middle" font-size="9.5" font-weight="800" fill="#fff" font-family="DM Mono, monospace">${c.score}</text></g>
            <g class="c-ref" opacity="0"><rect x="2" y="32" width="30" height="14" rx="7" fill="${c.ref ? "rgba(66,107,86,.16)" : "rgba(32,41,35,.08)"}"/><text x="17" y="42.4" text-anchor="middle" font-size="8.5" font-weight="700" fill="${c.ref ? C.green : C.clay}" font-family="DM Mono, monospace">${c.ref ? "↗ ref" : "none"}</text></g>
            <g class="c-ok" opacity="0"><circle cx="42" cy="2" r="10" fill="${c.fate === "link" ? "#B4553D" : C.green}"/><path d="${c.fate === "link" ? "M37.5 -2.5 L46.5 6.5 M46.5 -2.5 L37.5 6.5" : "M37.5 2 L41 5.5 L47 -1"}" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></g>
          </g>`).join("")}</g>
        <rect x="0" y="${BELT_Y + 12}" width="${W}" height="1" fill="rgba(0,0,0,0)"/>
      </g>`;
    stage.appendChild(svg);

    /* worker nodes */
    const st = {};
    $$(".station", svg).forEach(g => st[g.dataset.k] = {
      g, armL: $(".rb-arm-l", g), armR: $(".rb-arm-r", g), head: $(".rb-head", g), bulb: $(".rb-bulb", g), bubble: $(".bubble", g), prop: $(".prop-wrap", g),
      scoreNum: $(".score-num", g), scoreBar: $(".score-bar", g), shield: $(".shield-p", g), mark: $(".shield-mark", g), linkText: $(".link-text", g),
    });
    const gate = $(".gate", svg);
    return {
      svg, st,
      gate: { bubble: $(".bubble", gate), arm: $(".you-arm", gate), barrier: $(".barrier", gate), head: $(".you-head", gate) },
      cards: $$(".card", svg).map((g, i) => ({ g, score: $(".c-score", g), ref: $(".c-ref", g), ok: $(".c-ok", g), data: CARDS[i] })),
      bins: $$(".bin", svg),
    };
  }

  /* ---------- crew, hero ---------- */
  function buildHero() {
    const stage = $("#hx-hero-stage");
    const w = 560, h = 520;
    const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, class: "hx-hero-svg" });
    const xs = [96, 218, 340, 462];
    svg.innerHTML = `
      <defs><pattern id="hxHeroGrid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="rgba(32,41,35,.06)"/></pattern></defs>
      <rect x="6" y="40" width="${w - 12}" height="${h - 80}" rx="30" fill="#FFFDF8" stroke="rgba(32,41,35,.12)"/>
      <rect x="6" y="40" width="${w - 12}" height="${h - 80}" rx="30" fill="url(#hxHeroGrid)"/>
      <text x="36" y="84" font-family="DM Mono, monospace" font-size="12" letter-spacing="2.4" fill="${C.clay}">SHIFT 01 · ON DUTY</text>
      <circle cx="${w - 44}" cy="79" r="5" fill="${C.green}" class="hx-live-dot"/>
      <rect x="40" y="318" width="${w - 80}" height="14" rx="7" fill="#56635A"/><rect x="40" y="332" width="${w - 80}" height="34" rx="10" fill="#3C4840"/>
      <line class="belt-run" x1="30" y1="325" x2="${w - 30}" y2="325" stroke="#A6B3A9" stroke-width="3" stroke-dasharray="12 26"/>
      ${xs.map((x, i) => `<g transform="translate(${x},324) scale(.92)" class="hero-bot hero-bot-${i}" style="--d:${i * .45}s">${robotSVG(CREW[i])}</g>`).join("")}
      <g class="hero-card hc1"><rect x="0" y="0" width="86" height="56" rx="11" fill="${C.paper}" stroke="rgba(32,41,35,.28)"/><text x="43" y="22" text-anchor="middle" font-size="12" font-weight="800" fill="${C.ink}">Backend Eng</text><rect x="12" y="31" width="62" height="3.5" rx="2" fill="rgba(32,41,35,.13)"/><rect x="12" y="40" width="30" height="10" rx="5" fill="${C.green}"/></g>
      <g class="hero-card hc2"><rect x="0" y="0" width="86" height="56" rx="11" fill="${C.paper}" stroke="rgba(32,41,35,.28)"/><text x="43" y="22" text-anchor="middle" font-size="12" font-weight="800" fill="${C.ink}">SDE II</text><rect x="12" y="31" width="62" height="3.5" rx="2" fill="rgba(32,41,35,.13)"/><rect x="12" y="40" width="30" height="10" rx="5" fill="${C.terra}"/></g>
      <g transform="translate(36,392)"><rect width="${w - 72}" height="68" rx="16" fill="rgba(66,107,86,.1)"/><text x="22" y="29" font-size="13" font-weight="700" fill="${C.ink}">Find → Fit → Context → Verify</text><text x="22" y="50" font-size="12.5" fill="${C.clay}">…then it waits for your decision.</text></g>`;
    stage.appendChild(svg);
    return svg;
  }

  function buildCrew() {
    const host = $("#hx-crew");
    host.innerHTML = CREW.map((c, i) => `
      <article class="hx-crew-card" style="--c:${c.color}">
        <button class="hx-crew-flip" type="button" aria-pressed="false" aria-label="${c.role}: show what it checks and never does">
          <span class="hx-crew-face">
            <span class="hx-crew-num">${c.n}</span>
            <svg viewBox="-70 -200 140 210" class="hx-crew-bot" aria-hidden="true">${robotSVG(c)}</svg>
            <b>${c.role}</b>
            <small>${CAPS[c.key][1]}</small>
            <span class="hx-crew-hint">Tap to flip ↻</span>
          </span>
          <span class="hx-crew-back">
            <span class="hx-crew-num">${c.n} · ${c.name.toUpperCase()}</span>
            <em>It does</em><ul>${c.does.map(x => `<li>${x}</li>`).join("")}</ul>
            <em class="never">It never</em><ul class="never">${c.never.map(x => `<li>${x}</li>`).join("")}</ul>
          </span>
        </button>
      </article>`).join("");
    $$(".hx-crew-flip", host).forEach(b => b.addEventListener("click", () => {
      const on = b.getAttribute("aria-pressed") === "true";
      b.setAttribute("aria-pressed", String(!on));
      b.closest(".hx-crew-card").classList.toggle("flipped", !on);
    }));
  }

  /* ---------- tour video ---------- */
  function buildFilm() {
    const chapters = [["0:00", "Pick your companies", 0], ["0:04", "Choose, or stay open to any", 3.7], ["0:08", "A detective on the lookout", 7.9], ["0:12", "Fit and verify", 12.1], ["0:16", "Jobs available", 16.3], ["0:21", "You review. You send.", 20.5]];
    const ol = $("#hx-chapters"), v = $("#hx-video"), tog = $("#hx-video-toggle"), fill = $("#hx-video-fill");
    ol.innerHTML = chapters.map(([t, n, s], i) => `<li><button type="button" data-t="${s}"><span>${t}</span>${n}</button></li>`).join("");
    ol.addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; v.currentTime = +b.dataset.t; v.play().catch(() => {}); });
    const setIcon = () => { tog.textContent = v.paused ? "▶" : "❚❚"; tog.setAttribute("aria-label", v.paused ? "Play video" : "Pause video"); };
    tog.addEventListener("click", () => { v.paused ? v.play().catch(() => {}) : v.pause(); setIcon(); });
    v.addEventListener("play", setIcon); v.addEventListener("pause", setIcon);
    v.addEventListener("timeupdate", () => {
      fill.style.width = (v.currentTime / (v.duration || 23.7) * 100) + "%";
      const idx = chapters.reduce((a, c, i) => (v.currentTime >= c[2] ? i : a), 0);
      $$("li", ol).forEach((li, i) => li.classList.toggle("on", i === idx));
    });
    if (!reduced && "IntersectionObserver" in window) {
      new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) v.play().catch(() => {}); else v.pause(); }), { threshold: .5 }).observe(v);
    } else { tog.textContent = "▶"; }
  }

  /* ---------- journey ---------- */
  const JOURNEY = [
    ["Choose", "Pick your companies", "Browse company blocks showing the HR/TA, alumni and engineer contacts you already have, or stay open to any company as long as your minimum pay is met.",
      `<div class="mk"><div class="mk-cards"><i>Company A<br><small>HR · 2</small></i><i class="on">Company B<br><small>Alumni · 1</small></i><i class="on">Company C<br><small>Eng · 3</small></i><i>Company D<br><small>HR · 1</small></i></div><div class="mk-row"><span class="mk-chip on">Open to any company</span><span class="mk-chip">Min pay · 35 LPA</span></div></div>`],
    ["Hunt", "A detective on the lookout", "It watches career portals first, then LinkedIn job posts you can see and other job platforms, for openings that match your role types.",
      `<div class="mk"><div class="mk-cards"><i>Career portals</i><i>LinkedIn posts</i><i>Job platforms</i><i>Your list</i></div><div class="mk-arrow">⟶</div><div class="mk-pill">Possible openings</div></div>`],
    ["Filter", "Skills and fit score", "Each opening is compared with your skills, level, place and pay, and scored in the open with the reasons shown. Clear misses are set aside.",
      `<div class="mk"><div class="mk-split"><div><small>YOUR SKILLS</small><p>Backend · APIs</p><p>Node.js · Azure</p></div><div><small>THIS ROLE</small><p>Backend · APIs</p><p>Node.js · Azure</p></div></div><div class="mk-ok">✓ Fit 88 · skills match</div></div>`],
    ["Verify", "Double-checked, then shown", "A verifier opens every listing to confirm the link works and the opening is still live. Broken, closed or blocked links are labelled, never passed through.",
      `<div class="mk"><div class="mk-track"><b>Backend Engineer</b><span>✓ Live</span></div><div class="mk-track"><b>SDE II</b><span class="plan">✗ Link broken</span></div><div class="mk-track dim"><b>LinkedIn post</b><span class="plan">Check yourself</span></div></div>`],
    ["Track", "Jobs available, on your tracker", "Verified roles appear as Jobs available. Open a company to see its openings with the link, tracking details and referral options on the side.",
      `<div class="mk"><div class="mk-track"><b>Company B · 3 jobs</b><span>✓ 3 verified</span></div><div class="mk-split"><div><small>OPENINGS</small><p>Backend Engineer</p></div><div><small>REACH OUT</small><p>HR · Alumni · Eng</p></div></div></div>`],
    ["Decide", "Your approval, always", "Orbit drafts a polite note you can edit and send yourself. It never applies, messages or contacts anyone for you.",
      `<div class="mk"><div class="mk-draft"><i></i><i></i><i></i></div><div class="mk-gate">🔒 You review, you send</div></div>`],
  ];
  function buildJourney() {
    const steps = $("#hx-steps"), panel = $("#hx-panel");
    steps.innerHTML = JOURNEY.map((j, i) => `<button type="button" role="tab" aria-selected="${i === 0}" data-i="${i}"><span>0${i + 1}</span><b>${j[0]}</b><small>${j[1]}</small></button>`).join("");
    const show = (i, focus) => {
      $$("button", steps).forEach((b, k) => { b.setAttribute("aria-selected", String(k === i)); b.tabIndex = k === i ? 0 : -1; });
      panel.innerHTML = `<div class="hx-panel-in"><div class="hx-panel-n">STEP 0${i + 1} OF 06</div><h3>${JOURNEY[i][1]}</h3><p>${JOURNEY[i][2]}</p>${JOURNEY[i][3]}</div>`;
      if (window.gsap && !reduced) gsap.fromTo(".hx-panel-in > *, .hx-panel-in .mk > *", { y: 14, opacity: 0 }, { y: 0, opacity: 1, duration: .5, ease: "power3.out", stagger: .05 });
      if (focus) $$("button", steps)[i].focus();
    };
    steps.addEventListener("click", e => { const b = e.target.closest("button"); if (b) show(+b.dataset.i); });
    steps.addEventListener("keydown", e => {
      const cur = $$("button", steps).findIndex(b => b.getAttribute("aria-selected") === "true");
      if (["ArrowDown", "ArrowRight"].includes(e.key)) { e.preventDefault(); show((cur + 1) % JOURNEY.length, true); }
      if (["ArrowUp", "ArrowLeft"].includes(e.key)) { e.preventDefault(); show((cur + JOURNEY.length - 1) % JOURNEY.length, true); }
    });
    show(0);
    if (!reduced) { let n = 0; const auto = setInterval(() => { if (document.hidden || steps.matches(":hover, :focus-within") || panel.matches(":hover")) return; n = (n + 1) % JOURNEY.length; if (home.classList.contains("hidden")) return clearInterval(auto); show(n); }, 6500); }
  }

  /* ---------- live launch cards ---------- */
  async function buildLaunch() {
    const host = $("#hx-launch");
    const defs = [
      { who: "Vaanya", href: "/apply?c=Vaanya", tag: "A / EARLY CAREER", line: "Graduate roles, fresher tracks and hiring drives, grouped by company.", bot: 0 },
      { who: "Vrinda", href: "/apply?c=Vrinda", tag: "B / EXPERIENCED", line: "Backend and SDE roles, with source links and referral context close by.", bot: 1 },
    ];
    let data = null;
    try { const r = await fetch("/api/data"); if (r.ok) data = await r.json(); } catch (_) {}
    host.innerHTML = defs.map((d, i) => {
      const p = data && data.profiles.find(x => x.candidate === d.who);
      const rec = p ? p.jobs.length : null, co = p ? p.companies.length : null;
      return `<a class="hx-launch-card" href="${d.href}" style="--c:${CREW[d.bot * 1].color}">
        <svg viewBox="-70 -200 140 210" class="hx-launch-bot" aria-hidden="true">${robotSVG(CREW[d.bot])}</svg>
        <span class="hx-launch-tag">${d.tag}</span><h3>${d.who}’s search</h3><p>${d.line}</p>
        <div class="hx-launch-stats"><div><b data-count="${rec ?? ""}">${rec ?? "—"}</b><span>records</span></div><div><b data-count="${co ?? ""}">${co ?? "—"}</b><span>companies</span></div></div>
        <span class="hx-launch-go">View openings <b>↗</b></span></a>`;
    }).join("");
    if (window.gsap && !reduced) {
      $$("[data-count]", host).forEach(n => {
        const target = +n.dataset.count; if (!target) return;
        n.textContent = "0";
        const o = { v: 0 };
        const run = () => gsap.to(o, { v: target, duration: 1.4, ease: "power2.out", onUpdate: () => n.textContent = Math.round(o.v) });
        if ("IntersectionObserver" in window) { const io = new IntersectionObserver(es => { if (es[0].isIntersecting) { run(); io.disconnect(); } }, { threshold: .4 }); io.observe(n); } else run();
      });
    }
  }

  /* ---------- eyes follow the pointer ---------- */
  function trackEyes() {
    if (reduced || !matchMedia("(pointer:fine)").matches) return;
    let px = 0, py = 0, raf = 0;
    const bots = () => $$(".rb-eyes");
    addEventListener("pointermove", e => {
      px = e.clientX; py = e.clientY;
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        bots().forEach(g => {
          const r = g.getBoundingClientRect(); if (!r.width) return;
          const dx = px - (r.left + r.width / 2), dy = py - (r.top + r.height / 2), d = Math.hypot(dx, dy) || 1, m = Math.min(1, d / 260);
          g.style.transform = `translate(${(dx / d) * 4 * m}px,${(dy / d) * 3 * m}px)`;
        });
      });
    }, { passive: true });
  }

  /* ---------- smooth anchor ---------- */
  function anchors() {
    $$("[data-scroll]", home).forEach(a => a.addEventListener("click", e => {
      e.preventDefault();
      const t = $(a.dataset.scroll); if (!t) return;
      const y = t.getBoundingClientRect().top + scrollY - 70;
      if (window.gsap && !reduced) { const o = { y: scrollY }; gsap.to(o, { y, duration: 1.1, ease: "power3.inOut", onUpdate: () => scrollTo({ top: o.y, behavior: "instant" }) }); }
      else scrollTo({ top: y });
    }));
  }

  /* ---------- reveal ---------- */
  function reveals() {
    const items = $$(".hx-head, .hx-crew-card, .hx-film-grid > *, .hx-journey-grid > *, .hx-launch-card, .hx-note", home);
    if (reduced || !window.gsap || !("IntersectionObserver" in window)) return;
    items.forEach(i => i.classList.add("hx-pre"));
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return;
      io.unobserve(e.target);
      gsap.to(e.target, { opacity: 1, y: 0, duration: .8, ease: "power3.out", delay: (+e.target.dataset.d || 0) / 1000, onComplete: () => e.target.classList.remove("hx-pre") });
    }), { rootMargin: "0px 0px -8% 0px", threshold: .08 });
    items.forEach((i, k) => { if (i.matches(".hx-crew-card,.hx-launch-card")) i.dataset.d = (k % 4) * 90; io.observe(i); });
  }

  /* ---------- factory timeline ---------- */
  function wireFactory(F) {
    const capsHost = $("#hx-caps"), chips = $("#hx-chips"), hud = $("#hx-hud");
    capsHost.innerHTML = PHASES.map(p => `<article class="hx-cap" data-k="${p.k}"><div class="hx-cap-n">${CAPS[p.k][0]}</div><h3>${CAPS[p.k][1]}</h3><p>${CAPS[p.k][2]}</p><ul>${CAPS[p.k][3].map(t => `<li>${t}</li>`).join("")}</ul></article>`).join("");
    chips.innerHTML = PHASES.map((p, i) => `<button type="button" role="tab" data-i="${i}" aria-selected="false"><span>${i + 1}</span>${p.k === "you" ? "You" : CAPS[p.k][0].split("· ")[1]}</button>`).join("");
    const hv = k => $(`[data-hud="${k}"]`, hud);
    const set = (g, o) => g && (g.style.opacity = o);
    let lastPhase = -1;

    function render(t) {
      /* hud counts */
      const n = f => CARDS.filter(f).length;
      const found = n(c => c.pass[0] <= t);
      const scored = n(c => c.pass[1] <= t);
      const ver = n(c => c.fate === "ok" && c.pass[2] <= t);
      const ctx = n(c => c.fate === "ok" && c.pass[3] <= t);
      const wait = n(c => c.endT != null && c.endT <= t);
      [["found", found], ["scored", scored], ["context", ctx], ["verified", ver], ["waiting", wait]].forEach(([k, v]) => { const e = hv(k); if (e && e.textContent != v) { e.textContent = v; if (window.gsap && !reduced) gsap.fromTo(e, { scale: 1.35 }, { scale: 1, duration: .35, ease: "back.out(3)" }); } });

      /* card badges */
      F.cards.forEach(({ g, score, ref, ok, data }) => {
        set(score, t >= data.pass[1] ? 1 : 0);
        set(ref, data.fate === "ok" && t >= data.pass[3] ? 1 : 0);
        set(ok, data.fate !== "fit" && t >= data.pass[2] ? 1 : 0);
      });

      /* analyst & guard readouts */
      const last = (k, filt = () => true) => CARDS.filter(c => filt(c) && c.pass[k] <= t).pop();
      const a = last(1), A = F.st.analyst;
      if (A) { A.scoreNum.textContent = a ? a.score : "--"; A.scoreNum.setAttribute("fill", a && a.score < 60 ? C.terra : C.ink); A.scoreBar.setAttribute("width", a ? 40 * a.score / 100 : 0); A.scoreBar.setAttribute("fill", a && a.score < 60 ? C.terra : C.green); }
      const gd = last(2, c => c.fate !== "fit"), G = F.st.guard;
      if (G) { const bad = gd && gd.fate === "link"; G.shield.setAttribute("stroke", bad ? "#B4553D" : C.green); G.shield.setAttribute("fill", bad ? "rgba(180,85,61,.14)" : "rgba(66,107,86,.16)"); G.mark.setAttribute("stroke", bad ? "#B4553D" : C.green); G.mark.setAttribute("d", bad ? "M24 21 L40 37 M40 21 L24 37" : "M23 26 L30 33 L42 20"); }
      const cn = last(3, c => c.fate === "ok"), Cn = F.st.connector;
      if (Cn) Cn.linkText.textContent = cn ? (cn.ref ? "FOUND ↗" : "NO CONTACT") : "CONTACT";

      /* bubbles: shown briefly when a card is at the station */
      const bub = (k, list) => { const b = F.st[k].bubble; const on = list.some(x => t >= x - .15 && t <= x + .95); b.style.opacity = on ? 1 : 0; };
      bub("scout", [CARDS[0].pass[0], CARDS[2].pass[0]]);
      bub("analyst", [CARDS[0].pass[1], CARDS[2].pass[1]]);
      bub("guard", [CARDS[1].pass[2], CARDS[2].pass[2]]);
      bub("connector", [CARDS[2].pass[3], CARDS[3].pass[3]]);
      F.gate.bubble.style.opacity = t >= 9.2 ? 1 : 0;

      /* phase, captions, chips */
      const ph = PHASES.findIndex(p => t >= p.a && t < p.b); const idx = ph < 0 ? PHASES.length - 1 : ph;
      if (idx !== lastPhase) {
        lastPhase = idx;
        $$(".hx-cap", capsHost).forEach((c, i) => c.classList.toggle("on", i === idx));
        $$("button", chips).forEach((b, i) => b.setAttribute("aria-selected", String(i === idx)));
        $$(".station", F.svg).forEach(s => s.classList.toggle("active", PHASES[idx].k === s.dataset.k));
        F.svg.classList.toggle("you-on", PHASES[idx].k === "you");
        if (mobile) camTo(PHASES[idx].k);
      }
    }

    /* mobile camera: zoom the viewBox on the active station */
    let mobile = matchMedia("(max-width: 820px)").matches;
    const camX = { scout: S[0] - 230, analyst: S[1] - 230, guard: S[2] - 230, connector: S[3] - 230, you: GATE_X - 440 };
    const cam = { x: 0, w: W };
    const applyCam = () => F.svg.setAttribute("viewBox", `${cam.x} 0 ${cam.w} ${H}`);
    function camTo(k) { if (!window.gsap) return; gsap.to(cam, { x: Math.max(0, Math.min(W - 520, camX[k])), duration: .9, ease: "power3.inOut", onUpdate: applyCam }); }
    function setMobile() {
      mobile = matchMedia("(max-width: 820px)").matches;
      if (mobile) { cam.w = 520; cam.x = Math.max(0, camX[PHASES[Math.max(lastPhase, 0)].k]); } else { cam.w = W; cam.x = 0; }
      applyCam();
    }
    matchMedia("(max-width: 820px)").addEventListener("change", setMobile); setMobile();

    /* timeline */
    const tl = window.gsap ? gsap.timeline({ paused: true, defaults: { ease: "none" }, onUpdate: () => render(tl.time()) }) : null;
    if (!tl) { render(T); return { static: true }; }

    gsap.set(F.gate.barrier, { svgOrigin: `${GATE_X + 68 - 0} ${BELT_Y + 6 - 44}`, rotation: 0 });
    F.cards.forEach(({ g, data }) => {
      gsap.set(g, { x: data.x0, y: BELT_Y - 52 });
      const stop = data.end != null ? data.endT : data.dropAt;
      tl.to(g, { x: data.end != null ? data.end : data.x0 + V * stop, duration: stop, ease: "none" }, 0);
      if (data.dropAt) {
        const bx = data.fate === "fit" ? 1 : 2;
        tl.to(g, { y: 488, rotation: data.fate === "fit" ? 24 : -20, opacity: 0, duration: .7, ease: "power2.in" }, data.dropAt);
        tl.fromTo(F.bins[bx === 1 ? 0 : 1], { y: 0 }, { y: 5, duration: .12, yoyo: true, repeat: 3, ease: "sine.inOut" }, data.dropAt + .45);
      }
    });
    /* worker animations, scheduled from the same pass times */
    const work = (k, times, arm) => times.forEach(tp => {
      const s = F.st[k], a = arm === "l" ? s.armL : s.armR;
      tl.to(a, { rotation: arm === "l" ? 130 : -130, transformOrigin: "50% 0%", duration: .22, ease: "power2.out" }, tp - .3)
        .to(a, { rotation: 0, duration: .35, ease: "power2.inOut" }, tp + .1)
        .to(s.head, { rotation: 8, transformOrigin: "50% 100%", duration: .18, ease: "sine.out" }, tp - .25)
        .to(s.head, { rotation: 0, duration: .3, ease: "sine.inOut" }, tp + .15)
        .fromTo(s.bulb, { attr: { r: 6 } }, { attr: { r: 9 }, duration: .15, yoyo: true, repeat: 1 }, tp - .15);
    });
    work("scout", CARDS.map(c => c.pass[0]), "r");
    work("analyst", CARDS.map(c => c.pass[1]), "l");
    work("guard", CARDS.filter(c => c.fate !== "fit").map(c => c.pass[2]), "l");
    work("connector", CARDS.filter(c => c.fate === "ok").map(c => c.pass[3]), "r");
    /* human gate: nod, thumbs up */
    tl.to(F.gate.head, { y: 6, duration: .25, yoyo: true, repeat: 1, ease: "sine.inOut" }, 9.3)
      .to(F.gate.arm, { rotation: 150, transformOrigin: "50% 0%", duration: .35, ease: "back.out(2)" }, 9.5);
    tl.to({}, { duration: .01 }, T);                                  // pad to T
    tl.to(cam, { x: 0, duration: .01 }, T);

    /* scroll-driven when allowed */
    let st = null;
    if (!reduced && window.ScrollTrigger) {
      gsap.registerPlugin(ScrollTrigger);
      st = ScrollTrigger.create({
        trigger: "#factory", start: "top top", end: () => "+=" + Math.round(innerHeight * 3.4), pin: true, scrub: .7, anticipatePin: 1, animation: tl,
        onToggle: s => document.documentElement.classList.toggle("hx-pinned", s.isActive),
      });
      addEventListener("load", () => ScrollTrigger.refresh());
    } else { tl.progress(1); render(T); document.documentElement.classList.add("hx-static-mode"); }

    /* controls */
    let runTween = null;
    const stopRun = () => { if (runTween) { runTween.kill(); runTween = null; } $("#hx-run").textContent = "▶ Run the line"; };
    const goto = (t, dur) => {
      if (!st) { tl.time(t); render(t); return; }
      stopRun();
      const y1 = st.start + (t / T) * (st.end - st.start), o = { y: scrollY };
      runTween = gsap.to(o, { y: y1, duration: dur, ease: dur > 3 ? "none" : "power3.inOut", onUpdate: () => scrollTo({ top: o.y, behavior: "instant" }), onComplete: stopRun });
    };
    chips.addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; const p = PHASES[+b.dataset.i]; goto(Math.min(T - .05, p.a + .45), 1.1); });
    $("#hx-run").addEventListener("click", () => {
      if (runTween) { stopRun(); return; }
      if (!st) { tl.time(0); gsap.to(tl, { time: T, duration: T, ease: "none" }); return; }
      const nearTop = scrollY < st.start - 40 || scrollY > st.end - 40;
      if (nearTop) scrollTo({ top: st.start, behavior: "instant" });
      const o = { y: nearTop ? st.start : scrollY }, remain = (st.end - o.y) / (st.end - st.start);
      $("#hx-run").textContent = "❚❚ Pause";
      runTween = gsap.to(o, { y: st.end, duration: Math.max(1, T * remain * 1.15), ease: "none", onUpdate: () => scrollTo({ top: o.y, behavior: "instant" }), onComplete: stopRun });
    });
    ["wheel", "touchstart", "keydown"].forEach(ev => addEventListener(ev, () => { if (runTween) stopRun(); }, { passive: true }));
    render(0);
    return { tl, st };
  }

  /* ---------- a friendly worker on the other pages ---------- */
  function routeBot() {
    const p = location.pathname.replace(/\/+$/, "");
    const idx = { "/vaanya": 0, "/vrinda": 1, "/person": 2 }[p];
    if (idx == null) return;
    const hero = $(p === "/person" ? "#tracker-page .route-hero" : "#opportunities-page .route-hero");
    if (!hero) return;
    const d = document.createElement("div");
    d.className = "rf-routebot"; d.setAttribute("aria-hidden", "true");
    d.innerHTML = `<svg viewBox="-70 -200 140 210">${robotSVG(CREW[idx])}</svg>`;
    hero.appendChild(d);
  }

  window.OrbitRobots = { robot: robotSVG, CREW };

  /* ---------- go ---------- */
  function init() {
    routeBot(); buildHero(); buildCrew(); buildFilm(); buildJourney(); buildLaunch(); trackEyes(); anchors();
    const F = buildFactory();
    wireFactory(F);
    reveals();
    if (window.gsap && !reduced) {
      gsap.from(".hx-hero-copy > *", { y: 26, opacity: 0, duration: .9, ease: "power3.out", stagger: .09, delay: .1 });
      gsap.from(".hero-bot", { y: "+=36", opacity: 0, duration: .8, ease: "back.out(1.6)", stagger: .12, delay: .3 });
    }
  }
  const boot = () => { try { init(); } catch (e) { console.error("home init failed", e); } };
  if (document.readyState === "loading") addEventListener("DOMContentLoaded", boot); else boot();
})();
