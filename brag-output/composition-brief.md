# Hyperframes Composition Brief: Orbit

## Objective
Create a short launch-style brag video for Orbit (job search with a detective agent).

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape, 1920x1080
- Duration: 23.7s

## Source Material
- Project root: /Users/kaustubhsingh/Developer/job_search_agent 2/website
- Primary files read: index.html, home.js (robots, factory, hunt scene), hunt.js (company blocks, detective scene, Jobs available + Reach out), home.css, product.css, README.md
- Product name: Orbit
- Strongest claim: "Pick your companies. Let a detective hunt."
- Key UI to recreate: company blocks with HR/Alumni/Eng badges; the factory belt with analyst + verifier; Jobs available + Reach out panel
- Copy that must appear verbatim:
  - Pick your companies.
  - Let a detective hunt.
  - A detective on the lookout
  - Career portals / LinkedIn posts / Job platforms
  - Jobs available
  - Orbit never applies or messages for you.

## Creative Direction
- Tone preset: default
- Creative direction: warm, quietly confident factory-floor story with small robot agents
- Angle: choose → hunt → filter → verify → Jobs available + reach-out → you stay in control
- Hook: "Pick your companies." then "Let a detective hunt." with the hatted detective
- Outro: "You review. You send." + lockup
- Avoid: generic SaaS language, fake metrics, any depiction of auto-applying or auto-sending, abstract filler

## Visual Identity
- Background #F4F1E9, paper #FFFDF8, stone #EBE6E2, text #202923, evergreen #426B56, terracotta #B87860, clay #6F5C4B
- Display/body: Manrope; labels DM Mono (local woff2 in assets/fonts)
- References: website/home.js robot SVG (detective has a hat + magnifier), website/hunt.js scene

## Storyboard
See `brag-plan.md`.
1. Hook — 3.70s
2. Choose — 4.22s
3. Hunt — 4.20s
4. Filter and verify — 4.22s
5. Jobs available — 4.20s
6. Outro — 3.16s

## Audio
- Role: warm bed with sparse professional accents
- Music: assets/music/music.mp3 (vol-9, ≈115 BPM); fade out last 1.5s
- Cue guidance: bundled preset. Strong cues 3.70, 7.92, 12.65; grid ≈0.53s.
- Audio-reactive: subtle. bass breathes scene backdrop warmth and robot presence; treble softly shadows the active card. Data in audio-data.js.
- SFX: bong_001 (reveals), click_003 (selection), drop_001 (bins), rollover2 (boards), impactSoft_medium_001 (scene changes), select_008 (tracker). Sparse.

## Hyperframes Instructions
Follow current hyperframes-core / animation / creative / cli guidance. Run `hyperframes check` before render.
