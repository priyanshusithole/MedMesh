"""
explainer.py  -  AI Plain-English Explanation Layer
=================================================
Purpose: Take a structured finding (from interactions.py) and generate
a warm, clear, jargon-free explanation for a non-medical caregiver.

CRITICAL ARCHITECTURAL RULE:
  The LLM (Gemini) is given the FACTS from our engine and asked to
  REPHRASE them  -  it is NEVER asked whether two drugs interact.
  All medical facts come from our curated dataset.
  The model only provides compassionate language.

  "Facts from data, words from the model."

TWO-PATH DESIGN:
  Path A  -  Gemini API available:
      Pass the finding to Gemini Flash   get warm plain-English text
      Append to the finding as "detail_plain" field
  Path B  -  Gemini API unavailable (no key, timeout, rate limit):
      Use deterministic template strings   still a good experience
      App NEVER crashes due to AI failure

TEACHING NOTE  -  What is an "API key"?
  When you use Google's Gemini (or OpenAI, etc.), you authenticate
  yourself with a secret "API key"  -  a long random string that proves
  who you are and allows Google to track/bill usage.
  We store it in an environment variable (not in code) for security.
  Why NOT in code? If you commit your API key to GitHub, it's PUBLIC.
  Anyone can find it, use it, and your account gets charged.

TEACHING NOTE  -  What is an "environment variable"?
  A key-value pair stored in the operating system's memory.
  Example: GEMINI_API_KEY=AIzaSy...
  Python reads it with: os.environ.get("GEMINI_API_KEY")
  This keeps secrets OUT of source code and configuration files.
"""

import os
import re
import sys
import asyncio
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
# to templates automatically  -  no crash, no ugly error message.

# Multi-model fallback pool: if one model's quota is reached, automatically failover to the next
_MODEL_POOL = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash"
]
_ACTIVE_MODEL_INDEX = 0

async def generate_with_fallback(contents, temperature: float = 0.3, max_tokens: int = 300) -> Optional[str]:
    """
    Executes a Gemini generation call with automatic seamless model switching.
    If a model hits a 429 quota exhaustion or rate limit, it switches to the next
    available model in the pool and updates the active model pointer.
    """
    global _ACTIVE_MODEL_INDEX
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key, transport="rest")
    except ImportError:
        logger.error("google-generativeai package not installed.")
        return None

    total_models = len(_MODEL_POOL)
    for offset in range(total_models):
        idx = (_ACTIVE_MODEL_INDEX + offset) % total_models
        model_name = _MODEL_POOL[idx]
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "top_p": 0.8,
                },
                safety_settings={
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
                }
            )
            response = await asyncio.to_thread(model.generate_content, contents)
            text = (response.text or "").strip()
            if text:
                if idx != _ACTIVE_MODEL_INDEX:
                    logger.info(f"Switched active Gemini model from {_MODEL_POOL[_ACTIVE_MODEL_INDEX]} -> {model_name}")
                    _ACTIVE_MODEL_INDEX = idx
                return text
        except Exception as err:
            logger.warning(f"Gemini model '{model_name}' encountered: {err}. Switching to next available model...")
            continue

    logger.warning("All Gemini models in fallback pool exhausted.")
    return None

def _initialize_gemini():
    """Verify Gemini API key is present."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning(
            "GEMINI_API_KEY not set  -  AI explanations will use template fallback. "
            "Set the environment variable to enable Gemini-powered explanations."
        )


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
        "high": "  This is a HIGH-PRIORITY concern. Please contact your doctor or pharmacist TODAY before taking these medicines together.",
        "moderate": "  This concern is worth discussing with your pharmacist or doctor at your next visit.",
        "low": "  This is a low-level caution. Mention it to your doctor or pharmacist when you have an opportunity."
    }.get(severity, "Please discuss this with your doctor or pharmacist.")

    return f"{context}{detail} {urgency}"


# =============================================================================
# GEMINI EXPLANATION FUNCTION
# =============================================================================

_SYSTEM_PROMPT = """You are a compassionate medical communication assistant helping family caregivers understand prescription safety alerts. 

Your role: Take a structured medical finding and rewrite the explanation in warm, clear, plain English that a non-medical family member caring for an elderly parent can understand.

Rules you MUST follow:
1. DO NOT invent any new medical claims  -  only rephrase the information provided.
2. Keep your response to 2-3 sentences maximum.
3. Always end with a gentle call to action (e.g., "Please show this to a pharmacist").
4. Use simple everyday language  -  no Latin terms, no jargon.
5. Be warm and reassuring in tone, not alarming.
6. Never say the combination is "definitely dangerous"  -  say "may cause" or "can increase risk of".
7. Do not give dosing advice.
"""

async def explain_finding(finding: dict) -> str:
    """
    Generate a plain-English explanation for a single finding with automatic multi-model failover.
    """
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
    explanation = await generate_with_fallback(user_prompt, temperature=0.4, max_tokens=200)
    if explanation:
        return explanation
    return _template_explanation(finding)


async def explain_all_findings(findings: list[dict]) -> list[dict]:
    """
    Add plain-English explanations to all findings.

    Modifies each finding dict in-place by adding a "detail_plain" key.
    This is the ONLY new key we add  -  we never modify the clinical facts.

    TEACHING NOTE  -  asyncio.gather() for concurrent AI calls:
    If we have 5 findings and each Gemini call takes 1 second, doing
    them sequentially would take 5 seconds. With asyncio.gather(), all
    5 calls run concurrently  -  total time   1 second.

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
# IMAGE / OCR UTILITY (for Stage 5  -  Photo Prescription Scan)
# =============================================================================

async def extract_medicines_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[str]:
    """
    Use Gemini Vision to extract medicine names from a prescription photo.
    Automatically identifies and excludes crossed-out or struck-through medicines.
    Uses multi-model fallback to ensure high availability.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not configured  -  cannot perform image OCR")
        return []

    try:
        import io
        from PIL import Image

        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            # Downscale oversized camera photos to 1600px max dimension for fast OCR
            if pil_image.width > 1600 or pil_image.height > 1600:
                pil_image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        except Exception as img_err:
            logger.warning(f"PIL Image conversion error: {img_err}")
            pil_image = None

        prompt = """You are an advanced optical character recognition (OCR) and handwriting transcription engine for clinical document digitization.
Your task is to transcribe and identify all pharmaceutical medicine or drug names written on this document.

RULES:
1. Identify and transcribe the medicine and drug names from the handwriting or print.
2. If text is in sloppy or cursive doctor handwriting, transcribe the most probable pharmaceutical brand or generic drug name candidate (e.g. Adderall XR, Amoxicillin, Metformin, etc.).
3. DO NOT include dosage forms like Tab, Tab., Cap, Inj., or instructions like PO, PRN, BID.
4. CROSSED-OUT RULE: If a medicine has a line drawn directly through or cutting across the letters (cancelled or struck-through), OMIT IT.
5. UNDERLINED RULE: If a line is drawn strictly UNDER or BELOW the letters (underlined for emphasis), INCLUDE IT.
6. Output ONLY the medicine names, one per line. No conversational text, no safety refusal, no explanations. If none found, return NONE."""

        content_input = [prompt, pil_image] if pil_image is not None else [prompt, {"mime_type": mime_type, "data": image_bytes}]
        raw_text = await generate_with_fallback(content_input, temperature=0.2, max_tokens=400)

        if not raw_text or raw_text.strip() == "NONE":
            return []

        medicines = []
        refusal_keywords = [
            "safety note", "consult", "cannot safely", "pharmacist",
            "doctor's office", "ambiguous", "disclaimer", "prescribing"
        ]

        for line in raw_text.splitlines():
            line_clean = line.strip()
            if not line_clean or line_clean == "NONE":
                continue
            if any(kw in line_clean.lower() for kw in refusal_keywords):
                continue
            clean = re.sub(r'^(line\s*\d+\s*:\s*|\*\s*|\d+[\.\)]\s*|-\s*)', '', line_clean, flags=re.IGNORECASE).strip()
            clean = clean.replace("**", "").replace("*", "").strip()
            # Remove dosage form prefixes
            for prefix in ["tab.", "tab ", "cap.", "cap ", "syr.", "syr ", "inj.", "inj "]:
                if clean.lower().startswith(prefix):
                    clean = clean[len(prefix):].strip()
            clean = clean.strip('.,;:')
            # Filter out non-medicine conversational lines
            if clean and len(clean) > 1 and not clean.lower().startswith("here are") and not clean.lower().startswith("based on") and not clean.lower().startswith("note:"):
                if clean not in medicines:
                    medicines.append(clean)

        logger.info(f"Image OCR extracted {len(medicines)} medicines: {medicines}")
        return medicines

    except Exception as e:
        logger.error(f"Image OCR pipeline failed: {e}")
        return []
