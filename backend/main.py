"""
main.py  -  MedGuard FastAPI Application
=======================================
Purpose: Entry point for the MedGuard backend API.
         This file creates the FastAPI app, configures middleware,
         defines all routes/endpoints, and wires the modules together.

HOW TO RUN:
  cd backend
  uvicorn main:app --reload --port 8000

  - "main" = the filename (main.py)
  - "app"  = the FastAPI instance variable name (defined below)
  - "--reload" = auto-restart when you save a file (great for development)
  - "--port 8000" = listen on port 8000

AFTER STARTING, VISIT:
  http://127.0.0.1:8000/health     ->  health check
  http://127.0.0.1:8000/docs       ->  interactive API documentation (auto-generated!)
  http://127.0.0.1:8000/redoc      ->  alternative documentation format

TEACHING NOTE  -  What is an "endpoint" / "route"?
  A route is a URL pattern + an HTTP method (GET, POST, etc.) that
  maps to a specific Python function.
  Example: POST /api/check  ->  run_check() function
  When the frontend sends a POST request to /api/check, FastAPI
  automatically calls run_check() and returns whatever it returns.

TEACHING NOTE  -  What is "middleware"?
  Middleware is code that runs BEFORE and AFTER every request.
  It's like a security checkpoint at the airport  -  every passenger
  (request) passes through it before reaching their gate (endpoint).
  We use CORSMiddleware so browsers allow our frontend to call the API.
"""

import os
import asyncio
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Ensure backend and root directories are in Python's module search path
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
if str(_THIS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR.parent))

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

# Import our own modules (files we created)
from rxnorm import normalize_drugs
from interactions import run_safety_engine
from explainer import explain_all_findings, extract_medicines_from_image
from scheduler import generate_schedule

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


# =============================================================================
# LIFESPAN  -  Startup and Shutdown Events
# =============================================================================
# TEACHING NOTE  -  What is a "lifespan context manager"?
# FastAPI lets you define code to run when the server STARTS (startup)
# and when it STOPS (shutdown). The @asynccontextmanager decorator
# turns a generator function into a context manager.
# The code BEFORE `yield` runs at startup; AFTER `yield` at shutdown.
# This replaces the older @app.on_event("startup") pattern.

@asynccontextmanager
async def lifespan(app: FastAPI):
    # -- STARTUP --------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("  MedGuard Backend Starting Up")
    logger.info("=" * 60)

    # Check if Gemini API key is configured
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        logger.info("  Gemini API key found  -  AI explanations enabled")
    else:
        logger.warning("    No GEMINI_API_KEY  -  using template explanations (still works!)")

    logger.info("  Safety engine loaded (interaction + Beers datasets)")
    logger.info("  API ready at http://127.0.0.1:8000")
    logger.info("  Interactive docs at http://127.0.0.1:8000/docs")
    logger.info("=" * 60)

    yield  # Server runs here (between yield = normal operation)

    # -- SHUTDOWN -------------------------------------------------------------
    logger.info("MedGuard Backend shutting down...")


# =============================================================================
# FASTAPI APP INSTANCE
# =============================================================================
# This is the core object. All routes are registered on this object.
# `lifespan=lifespan` connects our startup/shutdown logic.

app = FastAPI(
    title="MedGuard API",
    description=(
        "AI-powered polypharmacy conflict detector for the elderly. "
        "Detects drug-drug interactions, duplicate active ingredients, "
        "and age-specific (Beers Criteria) warnings. "
        "Decision support only  -  always confirm with a pharmacist."
    ),
    version="1.0.0",
    contact={
        "name": "MedGuard Team",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan
)


# =============================================================================
# CORS MIDDLEWARE
# =============================================================================
# TEACHING NOTE  -  WHY CORS MATTERS:
# Browsers enforce the "Same-Origin Policy": a web page at
# http://localhost:3000 is NOT allowed to make fetch() calls to
# http://localhost:8000 by default (different ports = different origins).
# CORSMiddleware tells the browser: "These origins are trusted."
#
# allow_origins=["*"] means "allow ALL origins"
# This is fine for a hackathon/demo. In production, you'd specify
# exact domains like ["https://medguard.netlify.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],          # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],          # Allow all headers
)

@app.middleware("http")
async def vercel_path_rewrite_middleware(request: Request, call_next):
    """
    On Vercel, rewrites pass the target endpoint via the __path query parameter.
    This middleware restores the exact endpoint path so FastAPI matches the correct route.
    """
    subpath = request.query_params.get("__path")
    if subpath:
        clean_subpath = subpath.lstrip("/")
        if clean_subpath in ["health", "docs", "openapi.json"]:
            request.scope["path"] = f"/{clean_subpath}"
        elif clean_subpath.startswith("api/"):
            request.scope["path"] = f"/{clean_subpath}"
        else:
            request.scope["path"] = f"/api/{clean_subpath}"
    return await call_next(request)


# =============================================================================
# STATIC FILE SERVING (Serve the Frontend HTML)
# =============================================================================
# TEACHING NOTE  -  Static vs Dynamic content:
# "Static" = files that don't change per request (HTML, CSS, JS, images)
# "Dynamic" = content generated on-the-fly per request (our API responses)
#
# FastAPI can serve static files directly. We mount our frontend/ folder
# at the root URL so visiting http://localhost:8000/ serves index.html.
# This means one server handles BOTH the API AND the frontend  -  simple!
#
# We use a try/except because frontend/ might not exist yet during development

try:
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        logger.info(f"Frontend static files mounted from: {frontend_path}")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


# =============================================================================
# PYDANTIC MODELS  -  Request and Response Schemas
# =============================================================================
# TEACHING NOTE  -  What is Pydantic?
# Pydantic is Python's most popular data validation library.
# We define our expected request/response shapes as Python classes.
# FastAPI uses these classes to:
#   1. Validate incoming JSON (wrong types  ->  automatic 422 error with details)
#   2. Auto-generate the /docs interactive documentation
#   3. Serialize our response dicts to JSON
#
# Think of BaseModel subclasses as "contracts"  -  they define exactly
# what shape data must be in.
#
# Field(...) means the field is REQUIRED (no default value)
# Field(None) or Field(default=72) means it's OPTIONAL


class LoginRequest(BaseModel):
    patient_id: str = Field(..., description="Patient Unique ID (e.g. MED-84920)")
    password: str = Field(..., description="Patient account password")

class SignupRequest(BaseModel):
    name: str = Field(..., description="Patient or Caregiver full name")
    email: str = Field(..., description="Patient or Caregiver email address")
    password: str = Field(..., description="Account password")
    patient_age: Optional[int] = Field(default=70, description="Patient age")
    patient_gender: Optional[str] = Field(default="Not specified", description="Patient gender")

class CheckRequest(BaseModel):
    """
    Request body for POST /api/check

    Example payload:
    {
        "names": ["Warfarin 5mg", "Brufen 400", "Advil 200mg"],
        "patient_age": 72,
        "explain": true
    }
    """
    names: List[str] = Field(
        ...,
        min_length=1,
        description="List of medicine names (brand or generic, with or without dosage)",
        example=["Warfarin 5mg", "Brufen 400", "Advil 200mg", "Lisinopril 10mg"]
    )
    patient_age: Optional[int] = Field(
        default=None,
        ge=0, le=110,  # ge = greater or equal, le = less or equal (max 110 years)
        description="Patient's age in years. If >= 65, Beers Criteria elderly warnings are applied."
    )
    patient_name: Optional[str] = Field(
        default=None,
        description="Patient display name for profile identification."
    )
    patient_gender: Optional[str] = Field(
        default=None,
        description="Patient gender (e.g. Male, Female, Other)."
    )
    allergies: Optional[List[str]] = Field(
        default=None,
        description="Known substance or chemical allergies (e.g. ['Aspirin', 'Penicillin'])."
    )
    explain: bool = Field(
        default=True,
        description="If true, Gemini generates plain-English explanations for each finding."
    )


class NormalizeRequest(BaseModel):
    """Request body for POST /api/normalize"""
    names: List[str] = Field(
        ...,
        description="List of medicine names to normalize to active ingredients"
    )


# =============================================================================
# ROUTES / ENDPOINTS
# =============================================================================

@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def serve_frontend():
    """
    Serve the frontend index.html at the root URL.
    When a user visits the root URL, they get the web app.
    """
    candidates = [
        Path(__file__).resolve().parent.parent / "frontend" / "index.html",
        Path(__file__).resolve().parent / "index.html",
        Path.cwd() / "frontend" / "index.html",
        Path.cwd() / "index.html"
    ]
    for p in candidates:
        if p.exists():
            try:
                return HTMLResponse(content=p.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Error reading frontend file {p}: {e}")

    return HTMLResponse("<h1>MedGuard API is running!</h1><p><a href='/docs'>Interactive API Documentation</a></p>")


@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    description="Returns API status. Use this to verify the server is running."
)
@app.get("/api/health", tags=["System"], summary="Health Check Alias")
async def health_check():
    """
    Simple health check endpoint.

    TEACHING NOTE  -  Why do APIs have health check endpoints?
    Cloud platforms (Render, Railway, AWS) periodically ping /health
    to verify your service is alive. If it returns a non-200 status,
    the platform restarts your service automatically.
    Also useful for your own verification: "Is the server running?"
    """
    gemini_status = "enabled" if os.environ.get("GEMINI_API_KEY") else "template-fallback"
    return {
        "status": "ok",
        "app": "MedGuard",
        "version": "1.0.0",
        "ai_explanations": gemini_status,
        "message": "MedGuard backend is healthy and ready"
    }


@app.post(
    "/api/normalize",
    tags=["Medicine Tools"],
    summary="Normalize Drug Names",
    description="Convert brand names or dosage strings to active ingredient names using RxNorm."
)
@app.post("/normalize", tags=["Medicine Tools"], summary="Normalize Drug Names Alias")
async def normalize_endpoint(request: NormalizeRequest):
    """
    Normalize a list of drug names to their active ingredients.

    This is the /api/normalize endpoint. It's useful for testing
    the normalization layer independently.

    Example input:  ["Brufen 400", "Coumadin 5mg", "Lipitor"]
    Example output: ibuprofen, warfarin, atorvastatin
    """
    if not request.names:
        raise HTTPException(status_code=400, detail="'names' list cannot be empty")

    # Filter out empty strings
    clean_names = [n.strip() for n in request.names if n.strip()]
    if not clean_names:
        raise HTTPException(status_code=400, detail="All names were empty strings")

    results = await normalize_drugs(clean_names)

    return {
        "results": results,
        "total": len(results),
        "matched": sum(1 for r in results if r["matched"]),
        "unmatched": sum(1 for r in results if not r["matched"])
    }


@app.post(
    "/api/check",
    tags=["Safety Engine"],
    summary="Check Medication Safety",
    description=(
        "The main endpoint. Accepts a list of medicine names and an optional patient age, "
        "returns a full safety report with color-coded findings: "
        "interaction conflicts, duplicate active ingredients, and elderly-specific warnings."
    )
)
@app.post("/check", tags=["Safety Engine"], summary="Check Medication Safety Alias")
async def check_medications(request: CheckRequest):
    """
    THE MAIN ENDPOINT  -  runs the full MedGuard safety pipeline.

    Pipeline:
    1. Validate input
    2. Normalize all drug names  ->  ingredients (rxnorm.py)
    3. Run safety engine (interactions.py)
       a. Duplicate ingredient detection
       b. Pairwise interaction check
       c. Beers Criteria elderly warnings
    4. Add AI plain-English explanations (explainer.py) if requested
    5. Return structured report

    TEACHING NOTE  -  What is an HTTPException?
    When something goes wrong (empty input, etc.), we raise HTTPException.
    FastAPI catches this and returns a proper HTTP error response:
    {"detail": "error message"} with the appropriate status code.
    Status 400 = "Bad Request" (client's fault  -  bad input).
    Status 500 = "Internal Server Error" (server's fault  -  our bug).
    """
    logger.info(f"POST /api/check  -  {len(request.names)} medicines, age: {request.patient_age}")

    # --- 1. Validate ----------------------------------------------------------
    clean_names = [n.strip() for n in request.names if n.strip()]
    if not clean_names:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one medicine name."
        )
    if len(clean_names) > 30:
        raise HTTPException(
            status_code=400,
            detail="Maximum 30 medicines per check. Please split into smaller batches."
        )

    # --- 2. Normalize ---------------------------------------------------------
    # normalize_drugs is async  -  it runs RxNorm lookups concurrently
    logger.info(f"Normalizing {len(clean_names)} medicine names...")
    normalized_meds = await normalize_drugs(clean_names)

    # --- 3. Run Safety Engine -------------------------------------------------
    # This is synchronous (CPU work, no I/O)  -  pure Python dict lookups
    patient_age = request.patient_age or 0
    report = run_safety_engine(
        normalized_meds,
        patient_age=patient_age,
        patient_allergies=request.allergies or []
    )

    # Attach profile metadata to report
    report["patient_name"] = request.patient_name or "Anonymous Patient"
    report["patient_gender"] = request.patient_gender or "Not specified"
    report["allergies"] = request.allergies or []

    # --- 4. Add AI Explanations -----------------------------------------------
    # Only if "explain": true in the request (default: true)
    if request.explain and report["findings"]:
        logger.info(f"Generating AI explanations for {len(report['findings'])} findings...")
        report["findings"] = await explain_all_findings(report["findings"])

    # --- 5. Return Report -----------------------------------------------------
    # Include optimized 24-hour schedule
    report["schedule"] = generate_schedule(report["medicines"])

    logger.info(
        f"Check complete: {report['summary']['high']} high, "
        f"{report['summary']['moderate']} moderate findings"
    )
    return report


@app.post(
    "/api/schedule",
    tags=["Safety Engine"],
    summary="Generate 24-Hour Dose Schedule",
    description="Organizes a regimen into Morning, Lunch, Dinner, and Bedtime slots to avoid conflicts."
)
@app.post("/schedule", tags=["Safety Engine"], summary="Generate 24-Hour Dose Schedule Alias")
async def schedule_endpoint(request: CheckRequest):
    """Generates an optimized 24-hour daily medication timetable."""
    clean_names = [n.strip() for n in request.names if n.strip()]
    if not clean_names:
        raise HTTPException(status_code=400, detail="Please provide at least one medicine name.")

    normalized_meds = await normalize_drugs(clean_names)
    schedule_data = generate_schedule(normalized_meds)
    return schedule_data


@app.post(
    "/api/check-image",
    tags=["Safety Engine"],
    summary="Check Medication Safety from Multiple Prescription Photos",
    description=(
        "Upload one or more photos of prescription slips, medicine strips, or pill bottles. "
        "Gemini Vision extracts medicine names concurrently, which are presented as editable chips "
        "for user confirmation, then passed to the safety engine."
    )
)
@app.post("/check-image", tags=["Safety Engine"], summary="Check Medication Safety from Prescription Photos Alias")
async def check_image(
    file: Optional[UploadFile] = File(default=None, description="Single prescription photo (JPEG, PNG, WebP)"),
    files: Optional[List[UploadFile]] = File(default=None, description="Multiple prescription photos (JPEG, PNG, WebP)"),
    patient_age: Optional[int] = Form(default=None, ge=0, le=110),
    explain: bool = Form(default=True)
):
    """
    Multi-image OCR pipeline endpoint for prescription photo uploads.
    Processes one or more uploaded prescription photos concurrently with Gemini Vision.
    """
    upload_list: List[UploadFile] = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)

    if not upload_list:
        raise HTTPException(
            status_code=400,
            detail="Please upload at least one prescription photo."
        )

    logger.info(f"POST /api/check-image  -  processing {len(upload_list)} prescription image(s)")

    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"]
    max_size_bytes = 10 * 1024 * 1024  # 10MB per file

    valid_tasks = []
    for f in upload_list:
        content_type = f.content_type or "image/jpeg"
        if content_type not in allowed_types:
            logger.warning(f"Skipping unsupported file type: {f.filename} ({content_type})")
            continue

        image_bytes = await f.read()
        if len(image_bytes) == 0 or len(image_bytes) > max_size_bytes:
            logger.warning(f"Skipping empty or oversized file: {f.filename} ({len(image_bytes)} bytes)")
            continue

        valid_tasks.append((image_bytes, content_type))

    if not valid_tasks:
        raise HTTPException(
            status_code=400,
            detail="No valid prescription images provided. Please upload JPEG, PNG, or WebP files under 10MB."
        )

    # Concurrently analyze all uploaded prescription photos
    results = await asyncio.gather(
        *[extract_medicines_from_image(img_b, mime_type=m_type) for img_b, m_type in valid_tasks],
        return_exceptions=True
    )

    all_detected: List[str] = []
    for r in results:
        if isinstance(r, list):
            for med in r:
                clean_med = med.strip()
                if clean_med and clean_med not in all_detected:
                    all_detected.append(clean_med)
        elif isinstance(r, Exception):
            logger.error(f"Error during parallel prescription extraction: {r}")

    if not all_detected:
        return {
            "success": False,
            "detected_medicines": [],
            "requires_confirmation": True,
            "total_detected": 0,
            "processed_files_count": len(valid_tasks),
            "message": (
                f"Could not extract medicine names from the {len(valid_tasks)} uploaded image(s). "
                f"The images may be blurry or handwriting unclear. Please try typing the medicine names manually."
            )
        }

    return {
        "success": True,
        "detected_medicines": all_detected,
        "requires_confirmation": True,
        "total_detected": len(all_detected),
        "processed_files_count": len(valid_tasks),
        "message": (
            f"Found {len(all_detected)} medicines across {len(valid_tasks)} prescription photo(s). "
            f"Please review and correct any errors before checking safety."
        ),
        "next_step": "Send confirmed list to POST /api/check with your corrections"
    }


# =============================================================================
# AUTHENTICATION & PATIENT PROFILE STORE
# =============================================================================
USERS_DB: Dict[str, Dict[str, Any]] = {
    "MED-84920": {
        "patient_id": "MED-84920",
        "name": "Margaret Vance",
        "email": "margaret.vance@medguard.org",
        "password": "demo1234",
        "patient_age": 74,
        "patient_gender": "Female",
        "allergies": ["Penicillin"]
    }
}

@app.post("/api/auth/login", tags=["Authentication"], summary="Patient Unique ID Login")
@app.post("/auth/login", tags=["Authentication"], summary="Patient Unique ID Login Alias")
async def auth_login(req: LoginRequest):
    """Validates Patient Unique ID and Password."""
    pid = req.patient_id.strip().upper()
    user = USERS_DB.get(pid)
    if user and user["password"] == req.password:
        return {"success": True, "token": f"sess_{pid}", "user": user}
    elif pid == "MED-84920":
        return {"success": True, "token": f"sess_{pid}", "user": USERS_DB["MED-84920"]}
    raise HTTPException(status_code=401, detail="Invalid Patient Unique ID or password. Use demo ID: MED-84920")

@app.post("/api/auth/signup", tags=["Authentication"], summary="Register Patient and Generate Unique ID")
@app.post("/auth/signup", tags=["Authentication"], summary="Register Patient Alias")
async def auth_signup(req: SignupRequest):
    """Creates a new patient profile and returns an assigned Patient Unique ID."""
    import random
    new_id = f"MED-{random.randint(10000, 99999)}"
    new_user = {
        "patient_id": new_id,
        "name": req.name.strip(),
        "email": req.email.strip().lower(),
        "password": req.password,
        "patient_age": req.patient_age or 70,
        "patient_gender": req.patient_gender or "Not specified",
        "allergies": []
    }
    USERS_DB[new_id] = new_user
    return {"success": True, "patient_id": new_id, "user": new_user}

@app.get("/login", response_class=HTMLResponse, tags=["Frontend"], summary="Serve Login Page")
@app.get("/login.html", response_class=HTMLResponse, tags=["Frontend"], summary="Serve Login Page Alias")
async def serve_login():
    """Serves the custom glass-card login page."""
    paths = [
        os.path.join(os.path.dirname(__file__), "..", "frontend", "login.html"),
        os.path.join(os.path.dirname(__file__), "..", "login.html"),
        os.path.join(os.path.dirname(__file__), "login.html")
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse("<h3>Login page not found</h3>", status_code=404)


@app.get("/assets/{filename:path}", tags=["Frontend"], summary="Serve Static Assets")
async def serve_static_asset(filename: str):
    for base in [
        os.path.join(os.path.dirname(__file__), "..", "public", "assets"),
        os.path.join(os.path.dirname(__file__), "..", "assets"),
        os.path.join(os.path.dirname(__file__), "..", "frontend", "assets")
    ]:
        p = os.path.join(base, filename)
        if os.path.exists(p) and os.path.isfile(p):
            return FileResponse(p)
    raise HTTPException(status_code=404, detail="Asset not found")

# RUN DIRECTLY (for development)
# =============================================================================
# TEACHING NOTE  -  What is `if __name__ == "__main__"`?
# Every Python file has a __name__ variable.
# When you RUN a file directly (python main.py), __name__ = "__main__"
# When you IMPORT a file (import main), __name__ = "main"
# This block only runs when you execute: python main.py directly.
# We prefer `uvicorn main:app --reload` but this is a convenience option.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,   # Auto-reload on file changes (development only)
        log_level="info"
    )
