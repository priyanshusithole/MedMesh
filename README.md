# MedMesh — Clinical Polypharmacy Safety Engine

MedMesh is an AI-powered polypharmacy conflict detector, geriatric safety advisor, and smart 24-hour dose scheduling engine designed for senior care and clinical prescription validation.

---

## Key Capabilities

1. **Automated Polypharmacy Surveillance:** Cross-checks multi-doctor prescriptions against clinical drug-drug interaction databases and the AGS Beers Criteria 2023 for senior fall and cognitive risks.
2. **Duplicate Active Salt Detection:** Detects duplicate therapies where different pharmaceutical brand names share the same active molecule (e.g. Dolo + Calpol, Pan + Pantocid).
3. **Documented Allergy Contraindication Engine:** Automatically evaluates patient allergy profiles and cross-reacting drug classes (e.g. Aspirin vs Ecosprin, Penicillin vs Amoxicillin).
4. **24-Hour Fall-Safe Chronological Scheduler:** Distributes complex daily regimens into conflict-free morning, afternoon, evening, and bedtime slots.
5. **Affectionate Multilingual Voice Briefings:** Native audio summaries in English and Hindi customized with age and gender honorifics for families and caregivers.
6. **Multi-Prescription Photo OCR:** High-throughput document digitizer reading both printed and cursive doctor handwriting in seconds.

---

## Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/priyanshusithole/MedMesh.git
cd MedMesh
```

### 2. Set Up a Virtual Environment (Recommended)

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

#### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables (Optional for AI & OCR)
1. In the `backend/` directory, create a `.env` file:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   > **Note:** If no Gemini API key is configured, the safety engine automatically runs with deterministic clinical templates.

### 5. Launch the Server
From the project root:
```bash
uvicorn backend.main:app --reload --port 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## Project Structure

```text
├── api/
│   └── index.py             # Vercel serverless entrypoint
├── backend/
│   ├── main.py              # FastAPI application & REST endpoints
│   ├── rxnorm.py            # Drug name normalization & web scraping layer
│   ├── interactions.py      # Core safety engine (pair interactions, duplicates, Beers, allergies)
│   ├── explainer.py         # Google Gemini vision OCR & explanation fallback pool
│   ├── scheduler.py         # 24-hour chronological dose schedule generator
│   ├── requirements.txt     # Python backend dependencies
│   └── data/
│       ├── interactions_seed.json  # Curated drug-drug interaction pairs
│       └── beers_elderly.json      # AGS Beers Criteria 2023 elderly guidelines
├── frontend/
│   ├── index.html           # Main Single-Page Web Application
│   └── login.html           # Caregiver & Patient Authentication Portal
├── public/
│   └── assets/              # Static illustration assets
├── samples/
│   ├── demo_medlist.json    # Sample multi-medication regimen
│   └── test_prescription.png# Sample test prescription image
├── index.html               # Production web app entrypoint
├── login.html               # Production portal entrypoint
├── requirements.txt         # Root deployment dependencies
├── vercel.json              # Vercel routing and serverless configuration
├── .gitignore               # Excludes secrets, caches, and internal notes
└── README.md                # Project documentation and setup guide
```

---

## API Documentation
Interactive API docs are generated automatically by FastAPI:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
- **Health Check:** `http://127.0.0.1:8000/api/health`

---

## Production Deployment
MedMesh is continuously deployed on Vercel:
**[https://med-mesh.vercel.app](https://med-mesh.vercel.app)**
