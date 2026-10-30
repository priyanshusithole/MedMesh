# MedGuard — Staged 24-Hour Build & Deployment Plan

> **AI-Powered Polypharmacy Conflict Detector for the Elderly**  
> *Decision support, not diagnosis. Always keeps a doctor/pharmacist in the loop.*  
> **Golden Rule:** Always have a deployed, working version. Never leave the repo in a broken state. Deploy small and often.

---

## 🧭 Executive Overview (At a Glance)

| Stage | Name | Target Window (24h) | You Can Demo… | Deploy Target | Status |
| :---: | :--- | :---: | :--- | :--- | :---: |
| **0** | **Foundation & Setup** | H0 – H1 | Backend skeleton & plumbing | Local + GitHub | `[ ]` |
| **1** | **Core Safety Engine** | H1 – H3.5 | Typed meds $\rightarrow$ real conflict JSON | Local | `[ ]` |
| **2** | **Clinical UI & Report** | H3.5 – H6.5 | Clean, color-coded visual dashboard | Local | `[ ]` |
| **3** | **First Cloud Deploy 🌐** | H6.5 – H8 | Shareable live URL on mobile phone | **Live Web (MWP)** | `[ ]` |
| **4** | **Plain-English AI Layer** | H8 – H11 | Empathetic caregiver explanations | Live Web | `[ ]` |
| **5** | **Photo / Prescription Scan**| H11 – H15 | Snap slip $\rightarrow$ review chips $\rightarrow$ report | Live Web | `[ ]` |
| **6** | **Polish & Demo-Proofing** | H15 – H19 | 1-Click Grandma scenario & rehearse | Live Web | `[ ]` |
| **7** | **Stretch Goals & Buffer** | H19 – H24 | PDF export, Hindi/regional, video backup| Live Web | `[ ]` |

> 🏆 **Stages 0–3 = Minimum Winning Product (MWP).** Reaching Stage 3 by Hour 8 guarantees you have a live, working, demoable web app in judges' hands even if all Wi-Fi fails later. **Stages 4–6** turn "it works" into "it wins."

---

## 🔄 Synthesis & Architectural Safeguards

1. **Facts from Data, Words from the LLM:** The LLM *never* decides if two drugs interact. Interactions and duplicate ingredients are resolved by deterministic datasets (curated FDA / DDInter rules) and RxNorm normalization.
2. **Early Cloud Deployment (Stage 3):** We do not wait until the final hours to deploy. We deploy immediately after the UI + Engine work, so we have a live URL early and test on mobile cellular data.
3. **Mandatory Human-in-the-Loop for Photo Scan (Stage 5):** When photos are scanned, detected drugs are displayed as editable chips for user confirmation before running the safety checks, solving the doctor-handwriting dilemma.
4. **Strict Unknown Handling:** Drugs not found in the dataset return `"⚪ Not Checked"`—never a false green `"Safe"`.

---

## 🛠️ Stage-by-Stage Execution Plan

### Stage 0: Foundation & Setup (Hours 0 – 1)
**Goal:** Clean repository, virtual environment, and a running "Hello World" backend. No features yet.

- [ ] Initialize repository structure:
  ```text
  MedGuard/
  ├── backend/
  │   ├── data/
  │   ├── main.py
  │   └── requirements.txt
  ├── frontend/
  │   └── index.html
  ├── samples/
  │   └── demo_medlist.json
  ├── STEPS.md
  └── Project Explanation.md
  ```
- [ ] Configure `backend/requirements.txt`:
  - `fastapi`, `uvicorn`, `httpx`, `pydantic`, `python-multipart`, `google-genai` (or `google-generativeai`).
- [ ] Set up `backend/main.py` with FastAPI, CORS middleware, and static files mount for `frontend/`.
- [ ] Add `GET /health` endpoint returning `{"status": "ok", "app": "MedGuard"}`.

**Execute & Verify:**
```bash
cd backend
uvicorn main:app --reload --port 8000
# Test: http://127.0.0.1:8000/health -> {"status":"ok","app":"MedGuard"}
```
**Done When:**
- [ ] `/health` returns `{"status":"ok"}` locally.
- [ ] Environment installs cleanly without package conflicts.
- [ ] Initial commit pushed to repository.

---

### Stage 1: Core Safety Engine — Typed Path (Hours 1 – 3.5)
**Goal:** The heart of the product. Type a medicine list, get a real, structured medical safety report as JSON.

- [ ] **Normalization Module (`backend/rxnorm.py`):**
  - Integrate NIH RxNav REST API (`approximateTerm.json` / `allProperties.json`) to normalize brand names to active ingredients (e.g., `"Brufen 400"` $\rightarrow$ `ibuprofen`, `"Coumadin"` $\rightarrow$ `warfarin`).
  - Add offline fallback dictionary / local cache for demo reliability ($<10\text{ms}$ response time).
- [ ] **Curated Seed Datasets:**
  - Create `backend/data/interactions_seed.json` with 30+ high-impact pairs (Warfarin + NSAIDs, ACEI + Potassium, Metformin + Contrast, etc.).
  - Create `backend/data/beers_elderly.json` with high-risk geriatric medications (Beers Criteria).
- [ ] **Interaction Engine (`backend/interactions.py`):**
  - Duplicate ingredient detector: Identifies different brand names sharing the same active ingredient.
  - Pairwise interaction checker: Sorts findings by severity (`high` > `moderate` > `low`).
  - Beers Criteria checker: Applies elderly cautions if `patient_age >= 65`.
  - Unknown drug flagger: Flags uncatalogued drugs as `matched: false` (`"Not Checked"`).
- [ ] Expose `POST /api/check` endpoint.

**Execute & Verify:**
```bash
curl -X POST http://127.0.0.1:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{"names":["Warfarin 5mg","Brufen 400","Advil 200mg","Lisinopril 10mg","Potassium 20mEq"],"patient_age":72}'
```
**Done When:**
- [ ] Payload correctly identifies:
  1. Duplicate ingredient (`ibuprofen` from Brufen + Advil).
  2. Severe interaction (`warfarin` + `ibuprofen` bleeding risk).
  3. Dangerous pair (`lisinopril` + `potassium` hyperkalemia risk).
- [ ] Unknown drugs are flagged as `matched: false` (never reported as "safe").
- [ ] Interactive docs visible and testable at `http://127.0.0.1:8000/docs`.

---

### Stage 2: Real UI + Clinical Safety Report (Hours 3.5 – 6.5)
**Goal:** A non-technical person or caregiver can use it easily. The report looks clinical, trustworthy, and clear.

- [ ] Create single-file `frontend/index.html` using Tailwind CSS (CDN-based, zero build step):
  - Medication input (textarea supporting comma or newline separated entries).
  - Patient age input (default: 72).
  - Prominent **"Check Safety"** button + **"Load Grandma's Case"** demo preset button.
- [ ] Build the Clinical Safety Report UI:
  - Metric summary chips (🔴 Danger count, 🟠 Caution count, ⚪ Unchecked count).
  - Categorized finding cards with severity badges, involved drugs, and clinical sources.
  - Distinct styling for `"⚪ Not Checked"` drugs.
  - Mandatory clinical safety banner: *"Decision support only. Always confirm with your physician or pharmacist."*
  - Clean loading spinner, empty states, and error handling.
- [ ] Ensure mobile responsive layout (optimized for caregivers on smartphones).

**Execute & Verify:**
- Open `http://127.0.0.1:8000/` in browser.
- Click **"Load Grandma's Case"** $\rightarrow$ Click **"Check Safety"** $\rightarrow$ verify color-coded cards.
- Inspect page on mobile viewport width.

**Done When:**
- [ ] A non-technical user can run a check with zero instructions.
- [ ] Visual hierarchy is clinical: Red alerts immediately capture attention.
- [ ] Unknown drugs are clearly distinguished from verified safe drugs.
- [ ] UI looks and functions smoothly on mobile screen dimensions.

---

### Stage 3: First Cloud Deploy 🌐 (Hours 6.5 – 8)
**Goal:** A live, publicly accessible URL that anyone can open. Completed early to eliminate deployment risk.

- [ ] Deploy backend + frontend:
  - Option A: Single container/service on Render or Railway running `uvicorn main:app --host 0.0.0.0 --port $PORT` (FastAPI serves static `frontend/`).
  - Option B: Frontend on Netlify/Vercel pointing to backend on Render/Railway.
- [ ] Verify environment variables and CORS headers for public access.
- [ ] Test the live deployment on a smartphone over mobile data (cellular, not venue Wi-Fi).

**Done When:**
- [ ] Public URL loads instantly and returns accurate conflict reports.
- [ ] Mobile data test passes with zero CORS or network errors.
- [ ] Live URL is recorded and ready for the presentation deck.
- [ ] **MWP Complete:** The project is already viable and ready to present!

---

### Stage 4: Plain-English AI Layer (Hours 8 – 11)
**Goal:** Findings read like an empathetic, clear clinician speaking to a family caregiver, not raw pharmacological jargon.

- [ ] Implement `backend/explainer.py` using Google Gemini API:
  - Input: Verified medical findings (e.g., Warfarin + Ibuprofen interaction).
  - Output: 1–2 plain-English, reassuring sentences explaining *why* it matters and what to ask the doctor.
- [ ] **Hard Guardrail:** LLM is strictly an explainer—it never invents drug contraindications.
- [ ] **Deterministic Offline Fallback:** If `GEMINI_API_KEY` is unset or API times out, fallback seamlessly to curated template text. The application must never crash.
- [ ] Wire explainer into `/api/check` response.

**Execute & Verify:**
- Run check with API key enabled $\rightarrow$ confirm plain-English text in findings.
- Temporarily disable API key / internet $\rightarrow$ confirm report falls back to template text gracefully.

**Done When:**
- [ ] Explanations are warm, concise, and jargon-free.
- [ ] Zero changes to underlying clinical facts.
- [ ] Fallback test passes with 100% reliability.

---

### Stage 5: Photo / Prescription Scan with Human Confirmation (Hours 11 – 15)
**Goal:** Allow users to snap a photo of a prescription slip, printed bill, or pill box instead of typing.

- [ ] Add `POST /api/check-image` endpoint in `backend/main.py`.
- [ ] Integrate Multimodal Vision (Gemini Vision) to extract medication names and dosages.
- [ ] **Crucial UX Safety Step — "Review Detected Medicines":**
  - Present detected drug names as editable chips/tags to the user.
  - The user can remove misread words or add missing pills in 2 seconds before the safety check runs.
- [ ] Handle photo fallback gracefully (if image is unreadable, guide user to type names).

**Execute & Verify:**
- Upload sample prescription photo / medicine strip.
- Verify detected drugs appear in the confirmation step.
- Confirm and generate safety report.

**Done When:**
- [ ] Printed prescription/strip produces correct medication tags.
- [ ] User can edit/confirm detected items before triggering the engine.
- [ ] Graceful error message if photo is blurry or unreadable.

---

### Stage 6: Polish & Demo-Proofing (Hours 15 – 19)
**Goal:** Transform a working app into a winning presentation.

- [ ] Add **1-Click Preset Buttons** on the landing page:
  - *Grandma's Triple Threat* (Duplicate Ibuprofen + Warfarin Bleed + Lisinopril Hyperkalemia).
  - *Elderly Sedation Trap* (Diazepam Beers warning).
  - *All Clear Baseline* (Safe combination for contrast).
- [ ] Add **"Print / Export Pharmacist Handout"** button for a clean 1-page physical takeaway.
- [ ] Rehearse the 2.5-minute demo script 5+ times:
  - 0:00–0:20: Pitch (Grandma's 3 doctors).
  - 0:20–0:50: Typed path & reveal of the hidden duplicate ingredient.
  - 0:50–1:20: Photo scan & human review step.
  - 1:20–1:50: Plain-English explanation + Beers elderly alert.
  - 1:50–2:10: Disclaimer & printout for doctor/pharmacist.
  - 2:10–2:30: Q&A readiness.
- [ ] Drill the 5 critical judge questions (anti-hallucination architecture, handwriting guardrails, doctor-collaboration model).
- [ ] Record a 2-minute backup screen-recording video on phone/laptop (insurance against venue Wi-Fi failure).

**Done When:**
- [ ] Demo runs smoothly under 2.5 minutes without hiccups.
- [ ] Backup video is saved locally on two devices.
- [ ] Every team member can deliver the pitch.

---

### Stage 7: Stretch Goals & Buffer (Hours 19 – 24)
*Only start if Stages 0–6 are 100% green and rehearsed.*

- [ ] **Language Toggle:** English / Hindi (huge impact for healthcare in India).
- [ ] **"Explain Like I'm 70":** One-click toggle for larger typography and simpler terms.
- [ ] **Calendar Refill / Review Export:** Download `.ics` reminder for medication reconciliation.
- [ ] Final submission lock-in and well-earned rest before judging.

---

## 🚦 Final Pre-Stage Checklist

Before moving from one stage to the next, check:
1. Does `main` branch run cleanly?
2. Has the feature been tested on mobile?
3. Is the live deployment updated and responding?
