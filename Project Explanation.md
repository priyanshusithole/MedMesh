MedGuard — Hackathon Build Plan

AI-powered polypharmacy conflict detector for the elderly Decision support, not diagnosis. Always keeps a doctor/pharmacist in the loop.

0\. The 20-second pitch (memorize this)

"Grandma sees three doctors. Each prescription is safe on its own — but nobody checks the combined list. MedGuard does. Paste her medicines or snap a photo of the slips, and in seconds it flags dangerous drug interactions, hidden duplicate ingredients, and age-related warnings — in plain English — then tells you to confirm with a pharmacist. We build it on real NIH/FDA medical data, not guesses."

That pitch hits: relatable victim (grandma), invisible danger (combined list), instant payoff (seconds), credibility (real data), safety maturity (human-in-loop). Open and close your demo with it.

1\. What we're building (scope lock)

A web app with three moving parts:

Input — user types medicines OR uploads a photo of prescription(s). Photo → OCR → drug names.

Engine — normalize each name to its real active ingredient, then check every pair for interactions + detect duplicate ingredients + apply elderly-specific rules.

Report — a color-coded safety report (🔴 danger / 🟠 caution / 🟢 ok) with a plain-English explanation per finding and a mandatory "show this to a professional" banner.

Explicitly OUT of scope for the hackathon (say this to judges — it shows discipline):

No diagnosis, no dosing advice, no "replace your doctor."

No user accounts / login (use a session; auth is demo-killing time-waste).

No EHR integration.

Photo OCR is a bonus path — the typed path must work flawlessly first.

2\. ⚠️ The single most important technical fact

The NIH RxNav Drug-Drug Interaction API was DISCONTINUED (Jan 2024). Many tutorials still reference it; it will fail live. Do not build your interaction check on a live interaction API — it's the #1 way this demo dies on stage.

Our approach instead:

Use RxNorm / RxNav (still live and free, no key) only for what it's good at: normalizing a drug name → RxCUI → active ingredient. This is the credibility anchor and it's reliable.

Do the actual interaction + duplicate check against a LOCAL bundled dataset we ship in the repo (data/interactions\_seed.json). Curated from public sources (DDInter, openFDA labels, well-known interaction references). This means zero network dependency at demo time for the dangerous part — it always works, even on venue wifi.

The LLM layer (Gemini) only explains findings in plain English; it never invents the interaction. Facts come from the dataset; the LLM just translates. (This separation is also your best answer to "how do you prevent hallucination?")

Design rule: Facts from data, words from the LLM. Never let the model decide whether two drugs interact.

3\. Architecture

┌──────────────┐ meds (text) or photo ┌───────────────────────────────┐

│ Frontend │ ───────────────────────▶ │ FastAPI backend │

│ (single HTML)│ │ │

│ - med input │ ◀─── JSON report ─── │ 1. OCR (optional, Tesseract) │

│ - photo up │ │ 2. Normalize → RxNorm RxCUI │

│ - report UI │ │ → active ingredient(s) │

└──────────────┘ │ 3. Interaction engine │

│ (LOCAL seed dataset) │

│ - pairwise interactions │

│ - duplicate ingredients │

│ - elderly rules (Beers\*) │

│ 4. LLM explainer (Gemini) │

│ plain-English per finding │

└───────────────────────────────┘

\*Beers Criteria = standard list of

drugs risky for older adults

Data flow for one medicine: "Brufen 400" → RxNorm approximate match → RxCUI 5640 → ingredient ibuprofen. Then: does ibuprofen appear twice (duplicate)? Does it pair-interact with anything else on the list? Is it on the elderly-caution list?

4\. Tech stack (optimized for speed + reliability)

LayerChoiceWhy

BackendPython + FastAPIFastest to write, auto API docs at /docs (great for judges), async HTTP.

NormalizationRxNorm/RxNav REST (rxnav.nlm.nih.gov)Free, no key, authoritative US drug vocabulary.

Interaction dataLocal JSON seed (bundled)No live-API risk; always works offline.

Elderly rulesBeers Criteria subset (bundled)Adds the "built for the elderly" angle judges asked for.

OCR (bonus)Tesseract (pytesseract) or Google VisionPhoto-of-prescription wow factor. Optional path.

LLM explainerGoogle Gemini (gemini-2.0-flash)Plain-English explanations; you already have a key from your other project. Degrades gracefully to templated text if no key.

FrontendSingle index.html (vanilla JS + a little CSS)Zero build step. Nothing breaks. Deployable to Netlify in one drag.

DeployBackend on Render/Railway/Azure; frontend on NetlifyHave a live URL for judges.

Keep the frontend a single static file with no framework. In a hackathon, a broken npm run build at hour 18 has killed more demos than any bug.

5\. Repository layout (this scaffold)

MedGuard/

├── PLAN.md ← this file

├── README.md ← quick start

├── backend/

│ ├── requirements.txt

│ ├── main.py ← FastAPI app + endpoints

│ ├── rxnorm.py ← name → ingredient normalization

│ ├── interactions.py ← the safety engine (core IP)

│ ├── explainer.py ← LLM plain-English layer (optional)

│ └── data/

│ ├── interactions\_seed.json ← bundled interaction + duplicate data

│ └── beers\_elderly.json ← elderly-caution drug list

├── frontend/

│ └── index.html ← single-file UI

└── samples/

└── demo\_medlist.json ← the exact list to demo with

6\. API design

MethodEndpointBody / ParamsReturns

GET/health—{status: ok}

POST/api/normalize{names: \["Brufen 400", ...\]}each name → {rxcui, ingredient, matched}

POST/api/check{names: \[...\], patient\_age?: int}the main one — full safety report

POST/api/check-imagemultipart imageOCR → names → same report

/api/check response shape:

{

"medicines": \[

{"input": "Brufen 400", "ingredient": "ibuprofen", "rxcui": "5640", "matched": true}

\],

"findings": \[

{

"severity": "high",

"type": "interaction",

"drugs": \["warfarin", "ibuprofen"\],

"title": "Bleeding risk: warfarin + ibuprofen",

"detail\_plain": "Both increase bleeding risk...",

"source": "DDInter / FDA label"

},

{"severity":"high","type":"duplicate","drugs":\["ibuprofen"\],"title":"Duplicate ingredient: ibuprofen appears twice"}

\],

"summary": {"high": 1, "moderate": 1, "low": 0, "ok": false},

"disclaimer": "Decision support only. Confirm with a doctor or pharmacist before any change."

}

7\. The interaction engine (your core IP — get this right)

Three checks, in order:

Duplicate active ingredient — after normalizing, if two different-looking medicines resolve to the same ingredient → 🔴. (This is the demo showstopper: two "different" brand pills that are secretly the same drug.)

Pairwise interaction — for every unordered pair of ingredients, look it up in the seed dataset. Each hit carries a severity + a factual one-liner + a source.

Elderly rule — if patient\_age >= 65 and an ingredient is on the Beers-criteria list → add a caution finding ("risky for older adults because…").

Severity ranking for sorting the report: high > moderate > low. ok flag is false if any high/moderate exists.

Seed-data strategy: 25–40 well-known, high-impact pairs is plenty for a demo and looks comprehensive. Prioritize famous, easy-to-explain ones: warfarin+NSAIDs, warfarin+aspirin, ACE-inhibitor+potassium, statins+certain antibiotics, SSRIs+NSAIDs, metformin+contrast, two NSAIDs, beta-blocker duplicates. Each entry = {a, b, severity, detail, source}.

8\. 24-hour hour-by-hour timeline

Phase 1 — Core Spine & Walking Skeleton (Hours 0–4)
H0–1: Repo setup, FastAPI backend scaffold with CORS, /health endpoint, and basic frontend wireup.
H1–2.5: RxNorm normalization (rxnorm.py) — brand/generic to RxCUI and active ingredient(s) using free RxNav REST API.
H2.5–4: Interaction engine core (interactions.py) — duplicate active ingredient detection + pairwise lookup against bundled seed JSON. POST /api/check returns real report for typed med list.
★ Hour 4 Milestone: Type 4 medicines → see real conflict JSON. Demo spine is alive.

Phase 2 — Clinical UI & Knowledge Base (Hours 4–9)
H4–6.5: Build modern, trustworthy clinical UI (single index.html) with color cards (🔴 Danger, 🟠 Caution, ⚪ Unchecked), summary badges, patient age input, and safety disclaimer banner.
H6.5–8: Expand seed knowledge base: 30–40 high-impact drug interaction pairs (interactions_seed.json) + Beers Criteria list for older adults (beers_elderly.json).
H8–9: LLM Explainer layer (explainer.py) using Gemini to turn clinical findings into compassionate, plain-English sentences for caregivers (with deterministic template fallback if offline).
★ Hour 9 Milestone: Full visual dashboard working with typed input, Beers elderly checks, and plain-English explanations.

Phase 3 — Prescription Photo OCR & Polish (Hours 9–16)
H9–12: Photo upload path (POST /api/check-image) — upload prescription slip / bottle photo → OCR (Gemini Vision / Tesseract) → drug name extraction → seamless pass to safety engine.
H12–14: UI micro-polish: "Load Grandma's Meds" 1-click demo button, printable/PDF export view for doctor/pharmacist, loading skeletons, and strict "Not Checked" badge for unknown drugs.
H14–16: Live deployment (Backend on Render/Railway/Fly.io + Frontend on Netlify/Vercel) + mobile responsiveness testing.
★ Hour 16 Milestone: Live web app testable on phone with both text & photo input paths.

Phase 4 — Scripted Demo, Pitch Rehearsal & Disaster Buffer (Hours 17–24)
H17–19: Scripted demo hardening: ensure 1-click grandma scenario reliably triggers 1 lethal duplicate + 1 severe bleeding interaction + 1 elderly Beers warning.
H19–21: Pitch deck & demo rehearsals: time the 2.5-minute demo under pressure; drill the 5 critical judge questions (anti-hallucination proof, safety disclaimer, data sourcing).
H21–23: Disaster buffer: record a crisp 2-minute backup screen-recording demo video on phone/laptop in case venue Wi-Fi drops.
H23–24: Final code freeze, submit project portal details, and rest before judging.

9\. The demo script (≈ 2.5 minutes)

(20s) Pitch — say the grandma line from §0 verbatim.

(30s) Typed path — paste the 6-medicine demo list. Hit Check. Report fills: 🔴 "warfarin + ibuprofen: bleeding risk", 🔴 "duplicate: two medicines are both ibuprofen", 🟠 elderly caution. Read one finding aloud in plain English.

(40s) The reveal — point at the duplicate: "These came from two different doctors and look like different pills — but they're the same drug. A human scanning slips would miss this. That's the whole problem, solved."

(30s) Photo path — upload a photo of a prescription. Watch it OCR and produce the same report. "No typing. A caregiver just snaps a picture."

(20s) Safety close — scroll to the disclaimer. "We never diagnose. Every report says: confirm with your pharmacist. This is a safety net, not a replacement — built on NIH and FDA data."

End on the safety line. Judges remember the last thing you say.

10\. The 5 questions judges will ask (have answers ready)

"How do you avoid the AI making up interactions?" → "It can't. Interaction facts come from a curated dataset sourced from FDA labels and DDInter. The LLM only rephrases those facts in plain English — it never decides whether two drugs interact. Facts from data, words from the model."

"Is this medically safe / legal to give people?" → "It's explicitly decision support with a doctor/pharmacist in the loop — every report says so. We're the smoke alarm, not the fire department."

"What about drugs not in your dataset?" → "We normalize to RxNorm so we catch brand/generic variants, and we clearly flag anything unmatched as 'not checked' rather than falsely saying 'safe.'" (Never show green for unknowns.)

"How is this different from just Googling?" → "Google checks one pair at a time and can't see brand=generic duplicates. We check the whole combined list at once and resolve ingredients, which is exactly what humans miss."

"How would you scale this to production?" → "License a full interaction database (First Databank / Micromedex), add pharmacist review workflow, and integrate with e-prescription systems." (Shows you know the real path.)

11\. What makes this WIN vs. just work

Pick the demo list that creates drama — it must produce a scary-looking duplicate and a famous interaction (warfarin + ibuprofen). A boring "all clear" demo loses.

Never show green for an unknown drug. "Not checked" ≠ "safe." This one detail signals real medical maturity and judges notice it.

Make it feel clinical, not like a toy. Calm colors, a real disclaimer, a printable report. Trust is the product.

Lead and close with safety. Teams that over-claim ("replaces your doctor!") get torn apart in Q&A. You win by being the humble, careful one that still works.

12\. Stretch goals (only if ahead of schedule)

"Explain like I'm 70" toggle — even simpler language / larger text (accessibility = on-theme for elderly).

Voice input for caregivers.

Multi-language report (Hindi/regional) — huge for the "elderly in India" angle.

Reminder export (.ics) for the next refill check.

Do not start any stretch goal until the typed path, report UI, and demo script are rock solid.