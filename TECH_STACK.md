# Tech Stack — MedMesh

## Frontend Framework & Hosting

### Framework & UI
- **Framework:** Vanilla HTML5/CSS3/JavaScript (no framework overhead)
- **CSS Framework:** Tailwind CSS (via CDN)
- **Typography:** Inter font family (Google Fonts)
- **Architecture:** Single-Page Application (SPA) with tab-based navigation
- **Styling:** Custom color system with brand, neutral, and status palettes

### Hosting & Deployment
- **Platform:** Vercel (serverless deployment)
- **Entry Points:**
  - `index.html` — Main application entry
  - `login.html` — Authentication portal
  - `presentation.html` — Demo presentation mode

## Backend & Database

### Backend Framework
- **Framework:** FastAPI (Python 3.x)
- **Server:** Uvicorn (ASGI server)
- **Architecture:** RESTful API with automatic OpenAPI documentation

### Data Storage
- **Local Datasets (JSON):**
  - `interactions_seed.json` — Curated drug-drug interaction pairs
  - `beers_elderly.json` — AGS Beers Criteria 2023 for elderly patients
- **External APIs:**
  - NIH RxNav REST API — Drug name normalization and ingredient mapping
- **No traditional database** — Uses file-based data for deterministic clinical rules

## AI & Machine Learning

### AI Provider
- **Primary AI:** Google Gemini (Multi-model fallback)
  - Models in rotation:
    - `gemini-3.5-flash-lite`
    - `gemini-flash-lite-latest`
    - `gemini-3.1-flash-lite`
    - `gemini-3.8-flash`
- **API Library:** `google-generativeai` (v0.8.0+)
- **Usage Pattern:** Two-path design
  - **Path A:** Gemini API → Warm plain-English explanations
  - **Path B:** Deterministic templates (fallback when API unavailable)

### Computer Vision & OCR
- **Library:** Google Gemini Vision (multi-modal)
- **Functionality:** Multi-prescription photo OCR
  - Reads printed prescriptions
  - Handles cursive doctor handwriting
  - Extracts medication names from images

### Core AI Features
1. **Plain-English Explanation Engine:** Converts clinical findings into compassionate caregiver-friendly language
2. **Prescription Image Analysis:** OCR + medication extraction from photos
3. **Deterministic Safety Engine:** All medical logic is rule-based, AI only enhances communication

## Authentication

### Authentication Provider
- **No external auth provider configured**
- **Architecture Pattern:** Page-based access control
  - `login.html` — Caregiver/patient portal entry
  - Static HTML pages (no server-side session management)

### Note
The project focuses on clinical functionality rather than complex user authentication. The `login.html` serves as a portal entry point but doesn't appear to connect to an external identity provider.

## Dependencies

### Backend (Python)
| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥0.110.0 | Web framework |
| `uvicorn[standard]` | ≥0.28.0 | ASGI server |
| `httpx` | ≥0.27.0 | Async HTTP client (RxNav API) |
| `pydantic` | ≥2.6.0 | Data validation |
| `google-generativeai` | ≥0.8.0 | Gemini AI integration |
| `pillow` | ≥10.2.0 | Image processing (OCR preprocessing) |
| `python-multipart` | ≥0.0.9 | File upload handling |
| `python-dotenv` | ≥1.0.0 | Environment variable management |
| `beautifulsoup4` | ≥4.12.0 | Web scraping |
| `lxml` | ≥5.0.0 | HTML/XML parsing |
| `aiofiles` | ≥23.2.0 | Async file operations |

### Frontend (Bundled via CDN)
- `tailwindcss` — UI styling (CDN)
- `inter-font` — Typography (Google Fonts CDN)

## Project Structure

```
MedMesh-main/
├── api/
│   └── index.py                     # Vercel serverless entrypoint
│                                     Maps /api/* routes to FastAPI backend
├── backend/
│   ├── main.py                      # FastAPI application entry
│   │   ├── CORS middleware setup
│   │   ├── Endpoint definitions
│   │   └── Module orchestration
│   ├── rxnorm.py                    # Drug name normalization layer
│   │   ├── Local brand-name cache (100+ common drugs)
│   │   ├── NIH RxNav API integration
│   │   └── Graceful degradation (returns raw input if all fail)
│   ├── interactions.py              # Core safety engine (deterministic)
│   │   ├── Duplicate ingredient detection
│   │   ├── Pairwise drug-drug interaction checking
│   │   └── AGS Beers Criteria (elderly safety) checks
│   ├── explainer.py                 # AI explanation layer
│   │   ├── Gemini API integration
│   │   ├── Model fallback pool
│   │   ├── Plain-English explanation generation
│   │   └── Prescription image OCR/extraction
│   ├── scheduler.py                 # 24-hour dose schedule generator
│   │   ├── Clinical timing rules (diuretics, statins, etc.)
│   │   ├── 4-phase distribution (morning/afternoon/evening/bedtime)
│   │   └── Spacing constraint enforcement
│   ├── requirements.txt             # Python dependencies
│   └── data/
│       ├── interactions_seed.json   # Drug interaction pairs database
│       └── beers_elderly.json       # AGS Beers Criteria 2023 dataset
├── frontend/
│   ├── assets/                      # Static illustrations
│   ├── index.html                   # Main application
│   ├── login.html                   # Caregiver portal
│   └── presentation.html            # Demo presentation mode
├── public/
│   └── assets/                      # Production static assets
├── samples/
│   ├── demo_medlist.json            # Sample prescription data
│   └── test_prescription.png        # Sample OCR test image
├── index.html                       # Production entrypoint
├── login.html                       # Production portal entry
├── vercel.json                      # Vercel routing configuration
└── requirements.txt                 # Root deployment requirements
```

## OCR/Classification Logic Location

### OCR Pipeline
1. **Image Upload** → `frontend/index.html` (file input)
2. **API Endpoint** → `POST /api/check` → `backend/main.py`
3. **OCR Processing** → `backend/explainer.py`
   - Uses Gemini Vision multi-modal API
   - Extracts text from prescription images
4. **Medication Extraction** → `backend/explainer.py`
   - Parses OCR output for drug names
   - Normalizes brand names to active ingredients

### Classification Logic (Safety Checks)
Located in `backend/interactions.py`:
- **Duplicate Detection:** Compares normalized ingredients for same molecule
- **Interaction Checking:** Uses `itertools.combinations()` for pairwise checking against `interactions_seed.json`
- **Geriatric Screening:** Checks individual drugs against `beers_elderly.json` for age ≥65

## Deployment Architecture

### Vercel Serverless Setup
```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "/api/index.py?__path=:path*" },
    { "source": "/health", "destination": "/api/index.py?__path=health" },
    { "source": "/docs", "destination": "/api/index.py?__path=openapi.json" }
  ]
}
```

### Runtime Pattern
1. Vercel receives request
2. Routes to `api/index.py` (FastAPI entrypoint)
3. FastAPI processes through backend modules
4. Returns JSON responses for SPA consumption

## Key Design Principles

1. **Deterministic Safety Engine:** All clinical logic is rule-based, not AI-generated
2. **Graceful Degradation:** App works without Gemini API key (uses templates)
3. **Multi-Path AI:** Automatic model fallback if one quota is exhausted
4. **Offline-First Drug Cache:** 100+ common drugs available without network
5. **Static Frontend:** No build step, deployable to any static hosting
