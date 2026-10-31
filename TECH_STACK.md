# Complete Tech Stack: MedMesh

**Clinical Polypharmacy Safety Engine**  
*Automated pharmacological surveillance protecting complex regimens from hidden risks and duplicate active salts.*

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Client Browser (Frontend)                       │
│  Tailwind CSS (JIT) • ES6+ Vanilla JS • HTML5 Camera/Audio • .ICS Blob  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS / REST / MP3 Streaming
┌───────────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend (Vercel Serverless)                 │
│         Pydantic v2 • Asynchronous Endpoints (ASGI) • HTTPX            │
├───────────────────────────────────┬────────────────────────────────────┤
│ Clinical Safety Engines           │ AI & Multimodal Intelligence       │
│ • NIH RxNorm Drug Normalization   │ • Google Gemini 2.5 Flash          │
│ • 100+ Local Brand Name Mappings  │   - Doctor Handwriting OCR         │
│ • High-Risk DDI Matrix (NLM + DB) │   - Cultural Plain Language Voice  │
│ • AGS Beers & STOPP/START Rules   │ • Dynamic Respectful Honorifics    │
│ • 24-Hr Fall-Safe Chronotherapy   │ • Google TTS Streaming Pipeline    │
│ • Duplicate Active Salt Detector  │   (Cross-Platform Hindi & English) │
│ • Allergy Cross-Reaction Engine   │                                    │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## 1. Frontend & Client-Side Architecture

* **Core Stack:** **HTML5, CSS3, Modern JavaScript (ES6+)**
  * **Zero-Bundle Architecture:** Eliminates heavy build tools (Webpack/Vite/npm), ensuring instant sub-second page loads across low-bandwidth clinical devices and smartphones.
* **Styling & Design System:** **Tailwind CSS (JIT via CDN)**
  * Custom medical-grade earth palette:
    * **Bitter Olive:** `#3e3f16`
    * **Olive Leaf:** `#8A9A5B`
    * **Accent Olive:** `#758449`
    * Emerald, Teal, and Slate accents for severity status alerts.
  * Native print stylesheet support (`@media print`) for clean, printable clinical summary sheets and doctor-facing reports.
* **Iconography:** **Lucide Icons (`lucide.min.js`)**
  * Strict zero-emoji policy; uses clean, professional SVG icons for clinical statuses, severity alerts, and navigation.
* **Prescription Capture & Vision Ingestion:** **HTML5 MediaDevices API (`getUserMedia`) & File/Blob API**
  * Native camera integration with viewfinder overlay for live prescription capture.
  * Drag-and-drop multi-file uploader for batch-processing handwritten prescriptions and blister packs.
* **Audio Playback:** **HTML5 Audio Engine (`new Audio()`)**
  * In-memory streaming audio pipeline for smooth playback of affectionate caregiver audio briefings without device-side dependencies.
* **Calendar Export Engine:** **Client-Side RFC 5545 iCalendar (`.ics`) Generator**
  * Creates floating-time recurring daily alarms (`RRULE:FREQ=DAILY;INTERVAL=1`) with 10-minute pre-dose alerts (`VALARM`) using native `Blob` and `URL.createObjectURL`. Compatible with Apple Calendar, Google Calendar, and Microsoft Outlook.
* **Session & State Management:** **Web Storage API (`localStorage`)**
  * Stores patient profiles, unique Patient IDs (`MED-XXXX`), allergies, and dose adherence history locally with zero vendor lock-in.

---

## 2. Backend & Serverless Infrastructure

* **Runtime & Language:** **Python 3.10+**
* **Web Framework:** **FastAPI (`fastapi>=0.110.0`)**
  * High-performance ASGI framework executing non-blocking asynchronous routes (`async def`) for concurrent audits, prescription OCR, and TTS streaming.
* **Data Validation & Schemas:** **Pydantic v2 (`pydantic>=2.6.0`)**
  * Strict typing and schema validation for incoming clinical requests and outgoing audit reports (`AuditRequest`, `ScheduleRequest`, `AuditResponse`).
* **Asynchronous Networking:** **HTTPX (`httpx>=0.27.0`)**
  * High-concurrency client for dispatching asynchronous requests to medical databases and external APIs.
* **Image Processing:** **Pillow (`pillow>=10.2.0`) & Python-Multipart (`python-multipart>=0.0.9`)**
  * Ingests, normalizes, and encodes prescription images into base64 payloads for multimodal model consumption.
* **Local ASGI Server:** **Uvicorn (`uvicorn[standard]>=0.28.0`)**
* **Serverless Deployment Layer:** **Vercel Serverless Functions (`api/index.py`, `vercel.json`)**
  * URL rewrites map all `/api/*` requests to the Python serverless entry point, while static frontend assets are served globally via edge CDN.

---

## 3. Artificial Intelligence & Computer Vision

* **Multimodal Model:** **Google Gemini 2.5 Flash (`google-generativeai>=0.8.0`)**
  * **Doctor Handwriting OCR Engine:** Transcribes messy doctor cursive, multi-prescription layouts, and packaging labels into normalized JSON objects (`name`, `dosage`, `frequency`, `instructions`).
  * **Affectionate Cultural Caregiver Voice Generator:** Transforms complex pharmacological contraindications into clear, empathetic briefings in both **Plain English** and **Natural Hindi**.
  * **Dynamic Cultural Honorific Engine:** Automatically detects the patient's age and gender to address them with respectful cultural titles (*Beta*, *Bhaiya ji*, *Dadi ji*, *Dadaji*, *Aunty*, *Uncle*).

---

## 4. Pharmacological Knowledge Bases & Clinical Engines

* **Drug Normalization & Brand-to-Salt Resolver:**
  * **NIH RxNorm API (`https://rxnav.nlm.nih.gov/REST`):** Standardizes brand and trade names into RxCUIs and canonical active ingredients.
  * **Curated Local Brand Database (`backend/data/brand_mappings.json`):** Over 100+ mapped high-frequency Indian and international brand names (e.g., *Janumet*, *Augmentin*, *Glycomet*, *Ciprox TZ*, *Ecosprin*, *Lipitor*).
* **Drug-Drug Interaction (DDI) Surveillance:**
  * **NIH NLM Interaction API (`/REST/interaction/list.json`):** Identifies clinical interactions between RxCUIs.
  * **Curated High-Risk Interaction Table (`backend/interactions.py`):** Catches severe drug interactions including:
    * *Warfarin + NSAIDs / Aspirin* (Fatal bleeding risk)
    * *ACE Inhibitors / ARBs + Potassium-Sparing Diuretics* (Severe hyperkalemia / cardiac arrest)
    * *SSRIs + Tramadol / MAOIs* (Serotonin syndrome)
    * *Fluoroquinolones + Corticosteroids* (Tendon rupture)
    * *Nitrates + PDE5 Inhibitors* (Refractory hypotension)
* **Geriatric Polypharmacy & Chronotherapy Engine (`backend/scheduler.py`):**
  * **AGS Beers Criteria (2023 update) & STOPP/START Guidelines:** Detects anticholinergic burdens and medications that increase fall risk in older adults.
  * **24-Hour Spacing Distribution:**
    * **Morning (8:00 AM):** Blood pressure medications, morning-timed loop diuretics (prevents nocturia and midnight falls).
    * **Afternoon (1:00 PM):** Multivitamins and food-dependent supplements.
    * **Evening (7:00 PM):** Evening meals.
    * **Bedtime (10:00 PM):** Statins (peak circadian cholesterol synthesis) and sleep aids.
* **Duplicate Active Salt Surveillance:**
  * Flags duplicate active ingredients across multi-doctor prescriptions to prevent accidental overdoses from differing brand names.
* **Allergy Contraindication Engine:**
  * Cross-references patient allergy profiles against medication active ingredients and broader chemical classes (e.g., Penicillins, Sulfa drugs, NSAIDs, Cephalosporins).

---

## 5. Voice & Text-to-Speech (TTS) Pipeline

* **Streaming Google Translate TTS Engine:**
  * Chunked, non-blocking audio generation streamed via FastAPI:
    ```python
    StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")
    ```
  * Solves missing Hindi voice packs on Windows, macOS, and Linux by delivering a raw MP3 stream directly to the browser.
* **Client Fallback:** **Web Speech API (`window.speechSynthesis`)**
  * Offline fallback for instant English voice playback when network access is constrained.

---

## 6. DevOps, Tooling & Environment

* **Version Control:** **Git & GitHub** (`https://github.com/priyanshusithole/MedMesh.git`)
* **Continuous Deployment (CI/CD):** **Vercel Git Integration** (atomic zero-downtime builds on every push to `main`).
* **Configuration & Secrets:** **Python-Dotenv (`python-dotenv>=1.0.0`)** for managing keys (`GEMINI_API_KEY`).
* **Web Scraping & Medical Parsing:** **BeautifulSoup4 (`beautifulsoup4>=4.12.0`) & lxml (`lxml>=5.0.0`)** for clinical monograph parsing and data ingestion.

