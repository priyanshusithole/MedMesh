"""
main.py — MedGuard FastAPI Application
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
  http://127.0.0.1:8000/health    → health check
  http://127.0.0.1:8000/docs      → interactive API documentation (auto-generated!)
  http://127.0.0.1:8000/redoc     → alternative documentation format

TEACHING NOTE — What is an "endpoint" / "route"?
  A route is a URL pattern + an HTTP method (GET, POST, etc.) that
  maps to a specific Python function.
  Example: POST /api/check → run_check() function
  When the frontend sends a POST request to /api/check, FastAPI
  automatically calls run_check() and returns whatever it returns.

TEACHING NOTE — What is "middleware"?
  Middleware is code that runs BEFORE and AFTER every request.
  It's like a security checkpoint at the airport — every passenger
  (request) passes through it before reaching their gate (endpoint).
  We use CORSMiddleware so browsers allow our frontend to call the API.
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, List
from dotenv import load_dotenv

# Ensure backend and root directories are in Python's module search path
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))
if str(_THIS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR.parent))

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
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
# LIFESPAN — Startup and Shutdown Events
# =============================================================================
# TEACHING NOTE — What is a "lifespan context manager"?
# FastAPI lets you define code to run when the server STARTS (startup)
# and when it STOPS (shutdown). The @asynccontextmanager decorator
# turns a generator function into a context manager.
# The code BEFORE `yield` runs at startup; AFTER `yield` at shutdown.
# This replaces the older @app.on_event("startup") pattern.

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("  MedGuard Backend Starting Up")
    logger.info("=" * 60)

    # Check if Gemini API key is configured
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        logger.info("✅ Gemini API key found — AI explanations enabled")
    else:
        logger.warning("⚠️  No GEMINI_API_KEY — using template explanations (still works!)")

    logger.info("✅ Safety engine loaded (interaction + Beers datasets)")
    logger.info("✅ API ready at http://127.0.0.1:8000")
    logger.info("📖 Interactive docs at http://127.0.0.1:8000/docs")
    logger.info("=" * 60)

    yield  # Server runs here (between yield = normal operation)

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
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
        "Decision support only — always confirm with a pharmacist."
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
# TEACHING NOTE — WHY CORS MATTERS:
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
async def vercel_path_rewrite_middleware(request, call_next):
    """
    On Vercel, serverless rewrites point to api/index.py.
    Vercel sets 'x-matched-path' with the true requested URL.
    This middleware restores the path so FastAPI matches the correct route.
    """
    matched_path = request.headers.get("x-matched-path")
    current_path = request.scope.get("path", "")
    if matched_path and ("index.py" in current_path or current_path in ["/api", "/api/"]):
        clean_path = matched_path.split("?")[0]
        request.scope["path"] = clean_path
    return await call_next(request)


# =============================================================================
# STATIC FILE SERVING (Serve the Frontend HTML)
# =============================================================================
# TEACHING NOTE — Static vs Dynamic content:
# "Static" = files that don't change per request (HTML, CSS, JS, images)
# "Dynamic" = content generated on-the-fly per request (our API responses)
#
# FastAPI can serve static files directly. We mount our frontend/ folder
# at the root URL so visiting http://localhost:8000/ serves index.html.
# This means one server handles BOTH the API AND the frontend — simple!
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
# PYDANTIC MODELS — Request and Response Schemas
# =============================================================================
# TEACHING NOTE — What is Pydantic?
# Pydantic is Python's most popular data validation library.
# We define our expected request/response shapes as Python classes.
# FastAPI uses these classes to:
#   1. Validate incoming JSON (wrong types → automatic 422 error with details)
#   2. Auto-generate the /docs interactive documentation
#   3. Serialize our response dicts to JSON
#
# Think of BaseModel subclasses as "contracts" — they define exactly
# what shape data must be in.
#
# Field(...) means the field is REQUIRED (no default value)
# Field(None) or Field(default=72) means it's OPTIONAL

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

    TEACHING NOTE — Why do APIs have health check endpoints?
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
    THE MAIN ENDPOINT — runs the full MedGuard safety pipeline.

    Pipeline:
    1. Validate input
    2. Normalize all drug names → ingredients (rxnorm.py)
    3. Run safety engine (interactions.py)
       a. Duplicate ingredient detection
       b. Pairwise interaction check
       c. Beers Criteria elderly warnings
    4. Add AI plain-English explanations (explainer.py) if requested
    5. Return structured report

    TEACHING NOTE — What is an HTTPException?
    When something goes wrong (empty input, etc.), we raise HTTPException.
    FastAPI catches this and returns a proper HTTP error response:
    {"detail": "error message"} with the appropriate status code.
    Status 400 = "Bad Request" (client's fault — bad input).
    Status 500 = "Internal Server Error" (server's fault — our bug).
    """
    logger.info(f"POST /api/check — {len(request.names)} medicines, age: {request.patient_age}")

    # ─── 1. Validate ──────────────────────────────────────────────────────────
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

    # ─── 2. Normalize ─────────────────────────────────────────────────────────
    # normalize_drugs is async — it runs RxNorm lookups concurrently
    logger.info(f"Normalizing {len(clean_names)} medicine names...")
    normalized_meds = await normalize_drugs(clean_names)

    # ─── 3. Run Safety Engine ─────────────────────────────────────────────────
    # This is synchronous (CPU work, no I/O) — pure Python dict lookups
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

    # ─── 4. Add AI Explanations ───────────────────────────────────────────────
    # Only if "explain": true in the request (default: true)
    if request.explain and report["findings"]:
        logger.info(f"Generating AI explanations for {len(report['findings'])} findings...")
        report["findings"] = await explain_all_findings(report["findings"])

    # ─── 5. Return Report ─────────────────────────────────────────────────────
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
    summary="Check Medication Safety from Prescription Photo",
    description=(
        "Upload a photo of a prescription slip, medicine strip, or pill bottle. "
        "Gemini Vision extracts medicine names, which are presented as editable chips "
        "for user confirmation, then passed to the safety engine."
    )
)
@app.post("/check-image", tags=["Safety Engine"], summary="Check Medication Safety from Prescription Photo Alias")
async def check_image(
    file: UploadFile = File(..., description="Prescription photo (JPEG, PNG, WebP)"),
    patient_age: Optional[int] = Form(default=None, ge=0, le=110),
    explain: bool = Form(default=True)
):
    """
    OCR pipeline endpoint for prescription photo uploads.

    TEACHING NOTE — What is UploadFile?
    FastAPI's UploadFile type handles multipart form data (file uploads).
    When a user selects a photo in the browser, the browser sends it as
    "multipart/form-data" — a special encoding for binary files.
    UploadFile gives us the filename, content type, and raw bytes.

    TEACHING NOTE — What is Form()?
    When sending files, you can't use JSON body (JSON is text-only).
    So additional fields like patient_age are sent as "form fields"
    alongside the file. Form() tells FastAPI to read them from the form
    data instead of the JSON body.

    HUMAN-IN-THE-LOOP DESIGN:
    We return {"detected_medicines": [...], "requires_confirmation": true}
    The frontend shows these as EDITABLE CHIPS.
    The user confirms/corrects them, THEN calls /api/check with the confirmed list.
    This is the safety guardrail for doctor handwriting errors.
    """
    logger.info(f"POST /api/check-image — file: {file.filename}, type: {file.content_type}")

    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Please upload JPEG, PNG, or WebP."
        )

    # Validate file size (max 10MB)
    # TEACHING NOTE — read() loads entire file into memory as bytes
    image_bytes = await file.read()
    max_size_bytes = 10 * 1024 * 1024  # 10MB in bytes
    if len(image_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail="Image file is too large. Maximum size is 10MB."
        )

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Extract medicine names using Gemini Vision
    detected_medicines = await extract_medicines_from_image(
        image_bytes,
        mime_type=file.content_type or "image/jpeg"
    )

    if not detected_medicines:
        return {
            "success": False,
            "detected_medicines": [],
            "requires_confirmation": True,
            "message": (
                "Could not extract medicine names from this image. "
                "The image may be blurry or the text unclear. "
                "Please try typing the medicine names manually."
            )
        }

    # Return detected medicines for user confirmation
    # The FRONTEND will show these as editable chips before running the check
    return {
        "success": True,
        "detected_medicines": detected_medicines,
        "requires_confirmation": True,  # Always require human review of OCR output
        "total_detected": len(detected_medicines),
        "message": (
            f"Found {len(detected_medicines)} possible medicines. "
            f"Please review and correct any errors before checking safety."
        ),
        "next_step": "Send confirmed list to POST /api/check with your corrections"
    }


# =============================================================================
# RUN DIRECTLY (for development)
# =============================================================================
# TEACHING NOTE — What is `if __name__ == "__main__"`?
# Every Python file has a __name__ variable.
# When you RUN a file directly (python main.py), __name__ = "__main__"
# When you IMPORT a file (import main), __name__ = "main"
# This block only runs when you execute: python main.py directly.
# We prefer `uvicorn main:app --reload` but this is a convenience option.

@app.api_route("/api/{full_path:path}", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/{full_path:path}", methods=["GET", "POST", "OPTIONS"])
async def debug_catchall(request, full_path: str = ""):
    logger.warning(f"UNMATCHED ROUTE: method={request.method}, path={request.scope.get('path')}, full_path={full_path}")
    return {
        "status": "unmatched_route",
        "method": request.method,
        "scope_path": request.scope.get("path"),
        "full_path": full_path,
        "headers": {k: v for k, v in request.headers.items() if "auth" not in k.lower()}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,   # Auto-reload on file changes (development only)
        log_level="info"
    )
