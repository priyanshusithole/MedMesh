"""
explainer.py — AI Plain-English Explanation Layer
=================================================
Purpose: Take a structured finding (from interactions.py) and generate
a warm, clear, jargon-free explanation for a non-medical caregiver.

CRITICAL ARCHITECTURAL RULE:
  The LLM (Gemini) is given the FACTS from our engine and asked to
  REPHRASE them — it is NEVER asked whether two drugs interact.
  All medical facts come from our curated dataset.
  The model only provides compassionate language.

  "Facts from data, words from the model."

TWO-PATH DESIGN:
  Path A — Gemini API available:
    → Pass the finding to Gemini Flash → get warm plain-English text
    → Append to the finding as "detail_plain" field
  Path B — Gemini API unavailable (no key, timeout, rate limit):
    → Use deterministic template strings → still a good experience
    → App NEVER crashes due to AI failure

TEACHING NOTE — What is an "API key"?
  When you use Google's Gemini (or OpenAI, etc.), you authenticate
  yourself with a secret "API key" — a long random string that proves
  who you are and allows Google to track/bill usage.
  We store it in an environment variable (not in code) for security.
  Why NOT in code? If you commit your API key to GitHub, it's PUBLIC.
  Anyone can find it, use it, and your account gets charged.

TEACHING NOTE — What is an "environment variable"?
  A key-value pair stored in the operating system's memory.
  Example: GEMINI_API_KEY=AIzaSy...
  Python reads it with: os.environ.get("GEMINI_API_KEY")
  This keeps secrets OUT of source code and configuration files.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# =============================================================================
# GEMINI CLIENT INITIALIZATION
# =============================================================================
# We initialize the Gemini client once at module startup.
# If the API key is missing, _gemini_model stays None and we fall back
# to templates automatically — no crash, no ugly error message.

_gemini_model = None  # Will be set to a Gemini model instance if key exists

def _initialize_gemini():
    """
    Try to set up the Gemini client. Called once at startup.

    TEACHING NOTE — Why a separate initialization function?
    We wrap setup in a function so any error during init is caught cleanly.
    If we did this at module level without try/except, an import error
    would crash the ENTIRE backend server, not just the AI feature.
    """
    global _gemini_model  # We're modifying the module-level variable

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning(
            "GEMINI_API_KEY not set — AI explanations will use template fallback. "
            "Set the environment variable to enable Gemini-powered explanations."
        )
        return

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        # gemini-3.8-flash: Latest high-speed multimodal model
        _gemini_model = genai.GenerativeModel(
            model_name="gemini-3.8-flash",
            generation_config={
                "temperature": 0.4,    # Lower = more consistent, less creative
                                       # 0.0 = deterministic, 1.0 = very creative
                                       # 0.4 is good for medical writing (factual but warm)
                "max_output_tokens": 200,  # Keep explanations short and focused
                "top_p": 0.8,
            },
            # Safety settings — we're discussing medical topics, so we need to
            # allow some content that might trigger overly cautious filters
            safety_settings={
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
            }
        )
        logger.info("Gemini model initialized successfully (gemini-1.5-flash)")

    except ImportError:
        logger.error("google-generativeai package not installed. Run: pip install google-generativeai")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}")


# Run initialization when module is imported
_initialize_gemini()


# =============================================================================
# TEMPLATE FALLBACK SYSTEM
# =============================================================================
# These deterministic templates run when Gemini is unavailable.
# They're written to be warm and accessible, not cold and clinical.

def _template_explanation(finding: dict) -> str:
    """
    Generate a template-based explanation from the finding's existing data.
    This is always available, requires no internet, and cannot fail.
    """
    severity = finding.get("severity", "unknown")
    finding_type = finding.get("type", "unknown")
    drugs = finding.get("drugs", [])
    detail = finding.get("detail", "")

    # Build a simple, readable context line based on type
    if finding_type == "duplicate":
        ingredients = finding.get("ingredients", ["this medicine"])
        context = (
            f"You have two or more different medicines that both contain "
            f"'{ingredients[0] if ingredients else 'the same ingredient'}'. "
        )
    elif finding_type == "interaction":
        drug_names = " and ".join(drugs[:2]) if len(drugs) >= 2 else "these medicines"
        context = f"There is a known medical concern when taking {drug_names} together. "
    elif finding_type == "beers_elderly":
        drug_name = drugs[0] if drugs else "this medicine"
        context = (
            f"Medical guidelines specifically caution against '{drug_name}' "
            f"for patients aged 65 and older. "
        )
    else:
        context = ""

    urgency = {
        "high": "⚠️ This is a HIGH-PRIORITY concern. Please contact your doctor or pharmacist TODAY before taking these medicines together.",
        "moderate": "📋 This concern is worth discussing with your pharmacist or doctor at your next visit.",
        "low": "ℹ️ This is a low-level caution. Mention it to your doctor or pharmacist when you have an opportunity."
    }.get(severity, "Please discuss this with your doctor or pharmacist.")

    return f"{context}{detail} {urgency}"


# =============================================================================
# GEMINI EXPLANATION FUNCTION
# =============================================================================

_SYSTEM_PROMPT = """You are a compassionate medical communication assistant helping family caregivers understand prescription safety alerts. 

Your role: Take a structured medical finding and rewrite the explanation in warm, clear, plain English that a non-medical family member caring for an elderly parent can understand.

Rules you MUST follow:
1. DO NOT invent any new medical claims — only rephrase the information provided.
2. Keep your response to 2-3 sentences maximum.
3. Always end with a gentle call to action (e.g., "Please show this to a pharmacist").
4. Use simple everyday language — no Latin terms, no jargon.
5. Be warm and reassuring in tone, not alarming.
6. Never say the combination is "definitely dangerous" — say "may cause" or "can increase risk of".
7. Do not give dosing advice.
"""

async def explain_finding(finding: dict) -> str:
    """
    Generate a plain-English explanation for a single finding.

    If Gemini is available, uses AI. Otherwise falls back to templates.
    This function is ASYNC because the Gemini API call involves network I/O.

    Args:
        finding: a finding dict from interactions.py run_safety_engine()
    Returns:
        a plain-English explanation string
    """
    if _gemini_model is None:
        # Gemini not available — use template (always works)
        return _template_explanation(finding)

    try:
        # Build a clear prompt giving Gemini the FACTS (from our data)
        # and asking it only to REPHRASE them for a caregiver audience
        user_prompt = f"""
Please rewrite this medical safety alert in plain English for a family caregiver:

Finding Type: {finding.get('type', 'unknown')}
Severity: {finding.get('severity', 'unknown')}
Medicines involved: {', '.join(finding.get('drugs', []))}
Active ingredients: {', '.join(finding.get('ingredients', []))}
Clinical title: {finding.get('title', '')}
Clinical detail: {finding.get('detail', '')}
Source: {finding.get('source', '')}

Write 2-3 warm, clear sentences for a non-medical caregiver. End with a specific action to take.
"""

        # TEACHING NOTE — generate_content_async vs generate_content:
        # generate_content_async is the async version — it doesn't block
        # the server while waiting for Gemini to respond.
        response = await _gemini_model.generate_content_async(user_prompt)
        plain_text = response.text.strip()

        if plain_text:
            return plain_text

    except Exception as e:
        logger.warning(f"Gemini explanation failed: {e} — using template fallback")

    # If Gemini call failed for any reason, fall through to template
    return _template_explanation(finding)


async def explain_all_findings(findings: list[dict]) -> list[dict]:
    """
    Add plain-English explanations to all findings.

    Modifies each finding dict in-place by adding a "detail_plain" key.
    This is the ONLY new key we add — we never modify the clinical facts.

    TEACHING NOTE — asyncio.gather() for concurrent AI calls:
    If we have 5 findings and each Gemini call takes 1 second, doing
    them sequentially would take 5 seconds. With asyncio.gather(), all
    5 calls run concurrently — total time ≈ 1 second.

    Args:
        findings: list of finding dicts from run_safety_engine()
    Returns:
        same list with "detail_plain" added to each finding
    """
    import asyncio

    if not findings:
        return findings

    # Create all explanation tasks
    tasks = [explain_finding(finding) for finding in findings]

    # Run all concurrently and wait for all to complete
    explanations = await asyncio.gather(*tasks, return_exceptions=True)

    # Attach explanations to findings
    for finding, explanation in zip(findings, explanations):
        if isinstance(explanation, Exception):
            # If one AI call raised an exception, use template for that finding
            finding["detail_plain"] = _template_explanation(finding)
        else:
            finding["detail_plain"] = explanation

    return findings


# =============================================================================
# IMAGE / OCR UTILITY (for Stage 5 — Photo Prescription Scan)
# =============================================================================

async def extract_medicines_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[str]:
    """
    Use Gemini Vision to extract medicine names from a prescription photo.

    HOW GEMINI VISION WORKS:
    Gemini is a "multimodal" model — it can understand both text AND images.
    We send the raw image bytes along with a text prompt asking it to
    extract medicine names. It returns a comma-separated list.

    WHY GEMINI AND NOT TESSERACT?
    Tesseract is traditional OCR — it only recognizes printed text.
    Doctor handwriting is notoriously difficult and Tesseract fails badly.
    Gemini Vision understands CONTEXT — it knows a prescription's structure
    and can identify medicine names even in messy handwriting.

    HUMAN-IN-THE-LOOP GUARDRAIL:
    We return the list of CANDIDATES, not a final answer.
    The frontend shows these as editable chips for the user to confirm.
    This solves the "misread handwriting" problem — humans catch AI errors.

    Args:
        image_bytes: raw bytes of the uploaded image file
        mime_type: MIME type of the image (e.g., "image/jpeg", "image/png")
    Returns:
        list of detected medicine name strings (to be confirmed by user)
    """
    if _gemini_model is None:
        logger.warning("Gemini not available — cannot perform image OCR")
        return []

    try:
        import google.generativeai as genai

        # For vision tasks, we need to use the vision-capable model
        # gemini-3.8-flash supports vision natively
        vision_model = genai.GenerativeModel("gemini-3.8-flash")

        prompt = """You are analyzing a medical prescription or medicine packaging photo.

Extract ALL medicine names, drug names, or medication names you can see.

Instructions:
- Include brand names AND generic names if visible
- Include dosage if written next to the name (e.g., "Aspirin 75mg")
- Ignore doctor names, patient names, dates, clinic names, and instructions
- If you see "1-0-1" type schedules, ignore them
- Return ONLY the medicine names, one per line
- If you cannot identify any medicines, return exactly: NONE

Do not add explanations. Just list the medicine names, one per line."""

        # Create the image part for the multimodal request
        image_part = {
            "mime_type": mime_type,
            "data": image_bytes
        }

        response = await vision_model.generate_content_async([prompt, image_part])
        result_text = response.text.strip()

        if result_text == "NONE" or not result_text:
            return []

        # Split by newlines, clean up each line
        medicines = []
        for line in result_text.split("\n"):
            line = line.strip().lstrip("•-*123456789. ").strip()
            if line and len(line) > 1:  # Filter out single characters
                medicines.append(line)

        logger.info(f"Image OCR extracted {len(medicines)} medicine names: {medicines}")
        return medicines

    except Exception as e:
        logger.error(f"Image OCR failed: {e}")
        return []
