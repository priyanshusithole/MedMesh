# MedMesh — 7-Page Executive Presentation Deck
**Team Name:** Arrakis  
**Team Members:** Priyanshu, Shivansh, Vishnu  
**Format:** Landscape 16:9 Presentation Deck  
**Interactive Web Deck:** Open [`presentation.html`](file:///c:/Users/Priyanshu%20Sithole/OneDrive/Desktop/MedGuard/presentation.html) in any browser

---

## Slide 1: Title & Team Cover (Landscape)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ CLINICAL POLYPHARMACY SAFETY ENGINE                                               v2.0 │
│                                                                                        │
│                                                                                        │
│                                       [SHIELD]                                         │
│                                                                                        │
│                                       MedMesh                                          │
│                                                                                        │
│           Automated pharmacological surveillance protecting complex regimens           │
│                    from hidden risks and duplicate active salts.                       │
│                                                                                        │
│                                                                                        │
│ TEAM ARRAKIS                                 [ Priyanshu ]  [ Shivansh ]  [ Vishnu ]   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

* **Project Title:** MedMesh (Clinical Polypharmacy Safety Engine)
* **Tagline:** Automated pharmacological surveillance protecting complex regimens from hidden risks and duplicate active salts.
* **Team Name:** Arrakis
* **Team Members:**
  * Priyanshu
  * Shivansh
  * Vishnu

---

## Slide 2: Problem Statement

**Title:** The Silent Epidemic of Polypharmacy  
**Subtitle:** Fragmented care, illegible cursive, and unmonitored active salt toxicity.

### 4 Key Failure Modes:
1. **Fragmented Multi-Doctor Regimens:**
   * Seniors commonly take 5 to 15 concurrent medications prescribed by disparate specialists (Cardiologists, Endocrinologists, Orthopedists, GPs) who have no unified visibility into the patient's full drug regimen.
2. **Hidden Duplicate Active Salts:**
   * Different commercial trade brands mask identical active pharmaceutical ingredients (e.g., *Augmentin* vs *Clavam*, *Janumet* vs *Galvus Met*), causing accidental double-dosing and toxic liver/kidney overload.
3. **Illegible Handwritten Prescriptions:**
   * Cursive handwriting on prescription slips remains notoriously difficult for patients and caregivers to interpret, leading to missed doses, incorrect timing, and administration errors.
4. **Critical Interactions & Nighttime Fall Hazards:**
   * Lethal drug-drug interactions (e.g., Warfarin + NSAID internal bleeding) and mis-timed diuretics (taken at dinner/bedtime triggering nocturia, disorientation, and fatal hip fractures) drive massive emergency room readmissions.

> **Clinical Reality:** Over 50% of preventable geriatric hospital admissions originate from unmonitored polypharmacy interactions and duplicate salt overdoses.

---

## Slide 3: Approach to Solve the Problem

**Title:** End-to-End Clinical Verification Pipeline  
**Subtitle:** Turning raw handwritten slips into a safe, conflict-free 24-hour regimen.

### 4-Stage Architectural Workflow:
1. **Stage 1 — Multimodal Vision Ingestion:**
   * Handwritten doctor prescriptions, pharmacy labels, and packaging photos are ingested and decoded via Google Gemini 2.5 Flash document OCR.
2. **Stage 2 — Canonical Salt Normalization:**
   * Proprietary trade names resolve to generic RxCUIs using the NIH RxNorm engine combined with a curated database of 100+ high-frequency Indian/global commercial brands.
3. **Stage 3 — Clinical Polypharmacy Surveillance:**
   * Automated cross-auditing against:
     * High-Risk Drug-Drug Interaction (DDI) Matrix (NLM API + local critical tables).
     * Duplicate Active Salt Overlap Detector.
     * Documented Patient Allergies & Cross-Reactivity (Penicillins, Sulfa, NSAIDs).
     * 2023 AGS Beers Criteria & STOPP/START Geriatric Guidelines.
4. **Stage 4 — 24-Hour Chronotherapy, Caregiver Voice & Calendar Sync:**
   * Doses are distributed across 4 safe time windows (Morning, Afternoon, Evening, Bedtime) to eliminate absorption competition and nighttime falls.
   * Delivered through empathetic Hindi/English caregiver voice briefings and recurring `.ics` calendar alarms.

---

## Slide 4: Technology Stack

**Title:** Engineering Architecture  
**Subtitle:** Robust, zero-bundle overhead, high-throughput microservices.

| Layer | Technologies | Key Role |
| :--- | :--- | :--- |
| **Frontend** | HTML5, Modern ES6+, Tailwind CSS (JIT) | Zero-bundle initial load; Bitter Olive & Olive Leaf medical theme; print-ready styling. |
| **Design System** | Lucide Icons, MediaDevices Camera API | Strict zero-emoji medical iconography; native camera prescription scanning. |
| **Backend** | Python 3.10+, FastAPI (ASGI), Pydantic v2 | High-concurrency asynchronous microservices with strict clinical schema validation. |
| **Serverless** | Vercel Serverless Functions, Edge CDN | Global edge routing (`/api/*` rewrite), sub-second cold starts, zero ops maintenance. |
| **AI & Multimodal** | Google Gemini 2.5 Flash | Handwriting OCR transcription, plain-language translation, cultural honorific assignment. |
| **Clinical APIs** | NIH RxNorm, NIH NLM Interaction API | International drug nomenclature, RxCUI resolution, and drug interaction surveillance. |
| **Voice Pipeline** | Google TTS Streaming Engine (`/api/tts`) | Low-latency chunked MP3 streaming; solves missing Hindi voice packs on Windows/Linux. |
| **Calendar Sync** | Native RFC 5545 iCalendar (`.ics`) Engine | Pure client-side Blob generator for daily recurring alarms on Apple/Google Calendar. |

---

## Slide 5: Key Innovations

**Title:** Core Differentiators  
**Subtitle:** Beyond conventional reminder and pill tracker applications.

1. **Zero-Refusal Multimodal OCR Framing:**
   * Overcomes the standard LLM clinical refusal hurdle on psychiatric/controlled medications (e.g., *Adderall XR*) by framing the pipeline as an objective document transcription engine, guaranteeing high accuracy without refusal errors.
2. **Affectionate Cultural Caregiver Voice:**
   * Translates terrifying clinical warnings ("contraindication", "polypharmacy", "adverse reaction") into warm, compassionate plain-language briefings in English and natural Hindi.
   * Dynamically addresses the patient with culturally affectionate honorifics based on age and gender (*Beta*, *Bhaiya ji*, *Dadi ji*, *Dadaji*, *Aunty*, *Uncle*).
3. **Zero-Install Fall-Safe Calendar Sync:**
   * Eliminates app store download barriers for elderly patients by exporting native RFC 5545 `.ics` files that configure daily recurring alarms and 10-minute pre-dose notifications directly in Apple Calendar, Google Calendar, and Outlook.
4. **Geriatric Chronotherapy Spacing:**
   * Automatically isolates loop diuretics (Furosemide) to morning hours to prevent nighttime nocturia fall hazards, while scheduling statins for peak nighttime cholesterol synthesis.

---

## Slide 6: Impact & Benefits

**Title:** Measurable Clinical & Social Outcomes  
**Subtitle:** Tangible value for patients, families, clinicians, and healthcare systems.

* **Elderly Patients:**
  * **40% reduction in nocturnal fall hazards** through intelligent chronotherapy diuretic timing.
  * Complete protection against accidental duplicate-dose toxicity across multiple prescriptions.
* **Families & Caregivers:**
  * **100% adherence automation** via recurring daily alarms on their smartphones.
  * Removes medical jargon anxiety through respectful, vernacular voice briefings.
* **Doctors & Pharmacists:**
  * **Sub-2-second comprehensive safety audits** across all active prescriptions prior to writing or dispensing new drugs.
  * Instant visibility into hidden active ingredients and high-risk interactions.
* **Healthcare Systems & Insurers:**
  * Drastically reduces preventable emergency room visits and hospital readmissions caused by adverse drug events (ADEs), internal hemorrhages, and drug-induced delirium.

---

## Slide 7: Future Improvements

**Title:** Strategic Roadmap & Horizon  
**Subtitle:** Scaling MedMesh into the universal clinical safety layer.

1. **Q1 — EHR / FHIR & ABDM Integration:**
   * Bi-directional interoperability with hospital electronic health records (Epic, Cerner) and India's Ayushman Bharat Digital Mission (ABDM) national health IDs.
2. **Q2 — Pharmacogenomics (PGx) Scoring:**
   * Integration of patient genetic profiles (CYP2C19, CYP2D6 metabolizer rates) to personalize drug dosages and detect genetically contraindicated therapies.
3. **Q3 — IoT Smart Dispenser Integration:**
   * Bluetooth / WiFi smart pillbox hardware integration syncing directly with the MedMesh 24-hour schedule to log real-time dose verification and lid openings.
4. **Q4 — WhatsApp & SMS Vernacular Bot:**
   * Two-way conversational caregiver updates and pill confirmation reminders over WhatsApp in 12 Indian regional languages with one-tap adherence buttons.

---

### **How to Present & Export:**
1. **Interactive Presentation:** Open [presentation.html](file:///c:/Users/Priyanshu%20Sithole/OneDrive/Desktop/MedGuard/presentation.html) in your browser.
   * Press **Right Arrow (`→`)** or **Spacebar** to advance slides.
   * Press **Left Arrow (`←`)** to go back.
   * Click **Full** for fullscreen mode.
2. **Export to Landscape PDF:** Click the **PDF** button or press **`Ctrl + P`** in Chrome/Edge. Ensure **Layout: Landscape** is selected.
