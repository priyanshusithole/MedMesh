Here is the complete, professional setup guide formatted for your `README.md`. It covers prerequisites, installation, environment setup, running the server, and using the features.

---

```markdown
# MediTrace — Clinical Prescription Safety & Timing Intelligence

MediTrace is an AI-powered polypharmacy conflict detector and 24-hour dose scheduling engine designed for senior care and clinical prescription validation.

---

## Prerequisites

Before running the project, make sure you have:
- **Python 3.10+** installed on your computer ([Download Python](https://www.python.org/downloads/))
- **Git** installed ([Download Git](https://git-scm.com/))
- A modern web browser (Google Chrome, Microsoft Edge, Brave, or Firefox)
- *(Optional, for AI explanations and Photo OCR)* A free Gemini API key from [Google AI Studio](https://aistudio.google.com/)

---

## Quick Start Guide (Step-by-Step)

### 1. Clone the Repository
Open your terminal (PowerShell, Command Prompt, or Bash) and run:

```bash
git clone https://github.com/priyanshusithole/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```
*(Replace `YOUR_REPO_NAME` with your actual repository name)*.

---

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

---

### 3. Install Required Dependencies
Install all backend and AI libraries in one step:

```bash
pip install -r backend/requirements.txt
```

---

### 4. Configure Environment Variables (API Key)

1. Navigate to the `backend/` folder:
   ```bash
   cd backend
   ```
2. Create a file named `.env`:
   ```bash
   # On Windows (PowerShell):
   New-Item -Path .env -ItemType File
   ```
3. Open the `.env` file in any text editor and add your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   > **Note:** If you do not have a Gemini API key, the system will still function! The engine will automatically fall back to deterministic clinical templates for explanations.

---

### 5. Launch the Application Server

From inside the `backend/` directory, start the FastAPI server:

```bash
uvicorn main:app --reload --port 8000
```

Once started, you will see output like this:
```text
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:main:✅ Safety engine loaded (interaction + Beers datasets)
INFO:main:✅ API ready at http://127.0.0.1:8000
```

---

### 6. Open the Web Application

Open your browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

The unified interface will load immediately. Both the frontend and backend are served together from this single URL.

---

## Features to Try

1. **Step 1: Patient Details & Allergy Check**
   - Enter a patient name, age (0–110), and gender.
   - Add a known allergy (e.g. `Aspirin`).
   - Add a medicine like `Ecosprin 75mg` (Brand name for Aspirin) $\rightarrow$ The engine will flag a **Critical Allergy Contraindication**.

2. **Step 2: Medication Inputs & Prescription Scan**
   - **Text Entry:** Type any brand or generic name (e.g. `Warfarin 5mg`, `Brufen 400`, `Dolo 650`, `Telma 40`) and press **Add**.
   - **Prescription Photo OCR:** Drag and drop an image of a prescription slip or medicine strip. Gemini Vision extracts the medicine names as editable chips.

3. **Step 3: Clinical Safety Audit**
   - Click **Run Safety Audit** to view results grouped into 3 distinct categories:
     - 🔴 **1. Medicines That You Should Probably Avoid** (Severe pairwise interactions, Beers criteria geriatric warnings, and allergy clashes).
     - 🟠 **2. Two (or More) Medicines Are the Same** (Duplicate active salt detection to prevent accidental overdoses, e.g. Dolo + Calpol).
     - 🟢 **3. Everything Is Fine** (Verified safe medications with their active chemical ingredients).

4. **24-Hour Chronological Dose Schedule**
   - View an organized 4-slot daily timetable (**Morning, Afternoon, Evening, Bedtime**) optimized to separate conflicting drugs and prevent nighttime fall hazards.

5. **Multilingual Caregiver Audio Briefing**
   - Click **Listen in English** or **Listen in Hindi** to hear a synthesized speech summary generated directly in the browser.

6. **Print Clinician Handout**
   - Click **Print Clinician Handout** for a clean, print-optimized consultation sheet designed to hand to a doctor or pharmacist.

---

## Project Structure

```text
├── backend/
│   ├── main.py              # FastAPI application & REST endpoints
│   ├── rxnorm.py            # In-memory normalization & DuckDuckGo/Wikipedia web scraper
│   ├── interactions.py      # Core safety engine (pair interactions, duplicates, Beers, allergies)
│   ├── explainer.py         # Google Gemini 3.8 Flash plain-language & vision OCR layer
│   ├── scheduler.py         # 24-hour dose schedule generator
│   ├── requirements.txt     # Python package requirements
│   └── data/
│       ├── interactions_seed.json  # Curated drug-drug interaction pairs
│       └── beers_elderly.json      # AGS Beers Criteria 2023 elderly guidelines
├── frontend/
│   └── index.html           # Single-page web application (Tailwind, Lucide, Web Speech)
├── samples/
│   └── test_prescription.png# Sample test prescription image
├── .gitignore               # Excludes secrets (.env) and caches
└── README.md                # Project documentation and setup guide
```

---

## API Documentation

FastAPI automatically generates interactive Swagger documentation for developers:
- **Interactive Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`
- **Health Check Endpoint:** `http://127.0.0.1:8000/health`
```
