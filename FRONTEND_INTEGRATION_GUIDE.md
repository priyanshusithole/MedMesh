# 🏥 MedGuard — Frontend Developer Integration Guide

Welcome! This document contains everything you need to build the frontend for **MedGuard**, an AI-powered polypharmacy conflict detector and smart dose scheduler for elderly patients.

The backend is built with **FastAPI** and is currently running locally at:
👉 `http://127.0.0.1:8000`  
📖 Interactive API Playground (Swagger UI): `http://127.0.0.1:8000/docs`

---

## 📁 1. Project Directory Structure & Where to Put Your Files

Place your frontend files directly inside the `frontend/` folder in the project root:

```text
MedGuard/
├── backend/
│   ├── main.py              # FastAPI server
│   └── ...
└── frontend/                # 👈 YOUR WORK GOES HERE!
    ├── index.html           # Main HTML file
    ├── styles.css           # (Optional) or use Tailwind / inline CSS
    └── app.js               # (Optional) or script tag inside index.html
```

> **Automatic Serving:**  
> The backend is already configured to automatically serve whatever is in `frontend/index.html` at the root URL `http://127.0.0.1:8000/`. When you open `http://127.0.0.1:8000/`, your web app loads instantly!

---

## 🔌 2. API Endpoints Specification

### 🟢 1. Main Safety Check & Schedule Endpoint

* **URL:** `http://127.0.0.1:8000/api/check`
* **Method:** `POST`
* **Headers:** `Content-Type: application/json`

#### Request Payload:
```json
{
  "names": [
    "Warfarin 5mg",
    "Brufen 400",
    "Aspirin 100mg",
    "Lisinopril 10mg",
    "Diazepam 5mg"
  ],
  "patient_age": 72,
  "explain": true
}
```

| Field | Type | Required | Description & Constraints |
|---|---|:---:|---|
| `names` | `Array of strings` | **YES** | At least 1 medicine name, max 30. Accepts brand or generic names, with or without dosage. |
| `patient_age` | `integer` | NO | Patient's age (**0 to 110**). If $\ge 65$, Beers Criteria elderly warnings automatically trigger. |
| `explain` | `boolean` | NO | Default `true`. Generates caregiver-friendly plain English explanations. |

---

#### Response Payload (Example):
```json
{
  "medicines": [
    {
      "input": "Warfarin 5mg",
      "ingredient": "warfarin",
      "rxcui": null,
      "matched": true
    },
    {
      "input": "Brufen 400",
      "ingredient": "ibuprofen",
      "rxcui": null,
      "matched": true
    }
  ],
  "unmatched": [],
  "findings": [
    {
      "severity": "high",
      "type": "interaction",
      "drugs": ["Warfarin 5mg", "Brufen 400"],
      "ingredients": ["warfarin", "ibuprofen"],
      "title": "Major Bleeding Risk: Warfarin + Ibuprofen",
      "detail": "Ibuprofen inhibits platelet aggregation and damages stomach lining. Combined with Warfarin, this dramatically increases the risk of serious internal bleeding.",
      "detail_plain": "Taking Brufen and Warfarin together greatly increases the risk of stomach ulcers and severe bleeding.",
      "source": "FDA Black Box Warning / DDInter"
    },
    {
      "severity": "high",
      "type": "beers_elderly",
      "drugs": ["Diazepam 5mg"],
      "ingredients": ["diazepam"],
      "title": "Beers Alert: Diazepam – High Fall & Confusion Risk for Elderly",
      "detail": "Benzodiazepines cause sedation and slow reaction times in older adults...",
      "detail_plain": "Diazepam can cause excessive sleepiness and loss of balance, making elderly patients much more likely to fall.",
      "source": "AGS Beers Criteria 2023"
    }
  ],
  "summary": {
    "high": 2,
    "moderate": 0,
    "low": 0,
    "total": 2,
    "ok": false
  },
  "patient_age": 72,
  "disclaimer": "⚠️ MedGuard provides decision support only...",
  "schedule": {
    "schedule": {
      "morning": {
        "time": "8:00 AM (Breakfast)",
        "label": "Morning",
        "icon": "🌅",
        "medicines": [
          {
            "name": "Lisinopril 10mg",
            "ingredient": "lisinopril",
            "tip": "Take with water after breakfast"
          }
        ],
        "instructions": "Take with breakfast or 30 mins before food."
      },
      "afternoon": {
        "time": "1:00 PM (Lunch)",
        "label": "Afternoon",
        "icon": "☀️",
        "medicines": [],
        "instructions": "Take with lunch and water."
      },
      "evening": {
        "time": "7:00 PM (Dinner)",
        "label": "Evening",
        "icon": "🌆",
        "medicines": [],
        "instructions": "Take with evening meal."
      },
      "bedtime": {
        "time": "10:00 PM (Bedtime)",
        "label": "Bedtime",
        "icon": "🌙",
        "medicines": [
          {
            "name": "Diazepam 5mg",
            "ingredient": "diazepam",
            "tip": "Best taken right before sleep"
          }
        ],
        "instructions": "Take right before sleeping. Keep water by bedside."
      }
    },
    "total_scheduled": 2,
    "advice": "⚠️ Always verify with your pharmacist before changing medicine times."
  }
}
```

---

### 📷 2. Prescription Photo Upload (OCR)

* **URL:** `http://127.0.0.1:8000/api/check-image`
* **Method:** `POST`
* **Headers:** `multipart/form-data`
* **Form Fields:**
  - `file`: Image file (`JPEG`, `PNG`, `WebP`, max 10MB)
  - `patient_age`: Optional integer (0 to 110)
  - `explain`: Optional boolean (default `true`)

#### Response Payload:
```json
{
  "success": true,
  "detected_medicines": ["Dolo 650", "Ecosprin 75", "Pantocid 40"],
  "requires_confirmation": true,
  "total_detected": 3,
  "message": "Found 3 possible medicines. Please review and correct any errors before checking safety."
}
```

> **Human-in-the-Loop UX:**  
> When the OCR returns `detected_medicines`, display them on screen as **editable tag chips**. The user can edit spelling, add missing pills, or delete mistakes, and then click **"Run Safety Check"** which sends the confirmed list to `POST /api/check`.

---

## 🎨 3. Key UI Sections to Build

```
┌─────────────────────────────────────────────────────────────┐
│ 🏥 MedGuard — Senior Prescription Safety & Timing Guardian   │
├─────────────────────────────────────────────────────────────┤
│ 1. INPUT SECTION:                                           │
│    [+ Add Medicine Input Box]  [Patient Age: (0-110)]       │
│    [📷 Upload Prescription Photo]                           │
│    [⚡ 1-Click Demo Scenarios]:                             │
│       • "Grandma's Triple Threat" (Severe Conflict Demo)    │
│       • "Indian Paracetamol Overdose" (Duplicate Demo)      │
│       • "All Clear Regimen" (Safe Baseline Demo)            │
│    [RUN SAFETY AUDIT BUTTON]                                │
├─────────────────────────────────────────────────────────────┤
│ 2. SAFETY STATUS HERO (Traffic Light):                      │
│    🔴 CRITICAL WARNING (if summary.high > 0)                │
│    🟠 CAUTION ADVISORY (if summary.moderate > 0 & high == 0)│
│    🟢 ALL CLEAR REGIMEN (if summary.ok == true)             │
├─────────────────────────────────────────────────────────────┤
│ 3. DETECTED HAZARD CARDS:                                   │
│    • Duplicate Ingredients (Flagged in Red/Amber)           │
│    • Dangerous Interactions (Warfarin + Brufen Bleeding)    │
│    • Beers Criteria Elderly Warning (Diazepam fall risks)   │
│    • ⚪ Not Checked (For unrecognized/unverified drugs)     │
├─────────────────────────────────────────────────────────────┤
│ 4. ⏰ 24-HOUR SMART DOSE SCHEDULE:                          │
│    4 Cards: 🌅 Morning  |  ☀️ Afternoon  |  🌆 Evening  |  🌙 Bedtime│
│    Shows which medicines to take when to avoid conflicts.   │
├─────────────────────────────────────────────────────────────┤
│ 5. 🎙️ CAREGIVER AUDIO BRIEF (Point 2 - WOW Factor):        │
│    [🔊 Listen in English]   [🔊 Listen in Hindi]            │
├─────────────────────────────────────────────────────────────┤
│ 6. 🖨️ PRINT DOCTOR CONSULTATION SHEET:                      │
│    [Print Pharmacist Handout] (clean CSS print stylesheet)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎙️ 4. Ready-to-Use Code: Caregiver Audio Brief (Point 2)

Copy-paste this into your JavaScript to give users the 1-click **Voice Briefing** using the browser's built-in Web Speech API (no external libraries required!):

```javascript
// Function to speak summary in English or Hindi
function speakCaregiverBrief(report, lang = 'en') {
  if (!('speechSynthesis' in window)) {
    alert("Audio speech is not supported in this browser.");
    return;
  }

  window.speechSynthesis.cancel(); // Stop any ongoing speech

  let textToSpeak = "";

  if (lang === 'hi') {
    // Hindi / Hinglish translation
    if (report.summary.high > 0) {
      textToSpeak = `Dhyan dijiye. Is prescription mein ${report.summary.high} gambhir khatre mile hain. Dawaiyon ka dose ya combination lene se pehle apne doctor ya pharmacist se turant salah lein.`;
    } else {
      textToSpeak = `Aapki dawaiyon mein koi bada khatra nahi mila hai. Samay par dawai lein.`;
    }
  } else {
    // English
    if (report.summary.high > 0) {
      textToSpeak = `Attention caregiver. We detected ${report.summary.high} high-risk medication conflict in this regimen. Please consult your physician or pharmacist before taking these together.`;
    } else {
      textToSpeak = `All clear. No dangerous drug interactions or duplicate ingredients were detected.`;
    }
  }

  const utterance = new SpeechSynthesisUtterance(textToSpeak);
  utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-US';
  utterance.rate = 0.95; // Slightly slower, calm delivery
  window.speechSynthesis.speak(utterance);
}
```

---

## ⚡ 5. Ready-to-Use 1-Click Demo Scenarios

Provide 3 quick buttons on the UI so anyone demoing can test with 1 click:

```javascript
const DEMO_PRESETS = {
  grandma: {
    title: "Grandma's Triple Threat",
    names: ["Warfarin 5mg", "Brufen 400", "Aspirin 100mg", "Lisinopril 10mg", "Diazepam 5mg"],
    patient_age: 72
  },
  indianDuplicate: {
    title: "Indian Brand Paracetamol Overdose",
    names: ["Dolo 650", "Calpol 500", "Paracip 500", "Pacimol 500"],
    patient_age: 69
  },
  safe: {
    title: "All Clear Baseline",
    names: ["Metformin 500mg", "Amlodipine 5mg", "Atorvastatin 10mg"],
    patient_age: 60
  }
};

function loadPreset(presetKey) {
  const preset = DEMO_PRESETS[presetKey];
  // Fill your medicine input tags with preset.names
  // Set age input with preset.patient_age
  // Trigger checkMedications()
}
```

---

## 💡 Frontend Styling Recommendations

- **Color Palette:**
  - 🔴 **High Hazard:** Red / Rose (`#ef4444`, bg: `#fef2f2`, border: `#fecaca`)
  - 🟠 **Moderate Alert:** Amber / Orange (`#f59e0b`, bg: `#fffbeb`, border: `#fde68a`)
  - 🟢 **Safe / Clear:** Emerald / Green (`#10b981`, bg: `#ecfdf5`, border: `#a7f3d0`)
  - ⚪ **Not Checked / Unmatched:** Slate / Gray (`#64748b`, bg: `#f8fafc`, border: `#e2e8f0`)
  - 🏥 **Primary Brand:** Medical Blue / Cyan (`#0284c7`, `#0369a1`)
- **Frameworks:** You can use plain HTML/Tailwind CDN, React, Vue, or vanilla JS — whichever you are fastest and most comfortable with!

If you have any questions about the data format, reach out to the backend team!

