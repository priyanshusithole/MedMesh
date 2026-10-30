"""
rxnorm.py — Drug Name Normalization Module
==========================================
Purpose: Convert any brand name / dose string (e.g. "Brufen 400mg")
into its lowercase active ingredient(s) (e.g. "ibuprofen").

HOW IT WORKS (3-layer approach):
  Layer 1 — Local hardcoded cache (instant, 0ms, always works)
  Layer 2 — NIH RxNav REST API (authoritative, free, no key required)
  Layer 3 — Graceful degradation (return raw input if both fail)

WHY THIS DESIGN:
  - Demo reliability: If venue wifi dies, Layer 1 covers our demo drugs
  - Credibility: When Layer 1 misses, Layer 2 uses REAL NIH data
  - Resilience: Layer 3 ensures the app never crashes — it flags
    unknown drugs as "not matched" instead of throwing an error

TEACHING NOTE — What is an "async" function?
  When Python calls the internet (httpx.get), it has to WAIT.
  With `async def`, Python can handle OTHER requests while waiting.
  Without async, one slow internet call would freeze the WHOLE server.
  Think of it like a waiter taking multiple tables' orders, vs.
  waiting at one table until they finish eating before moving on.
"""

import httpx          # Async HTTP client — makes calls to RxNav API
import logging        # Python's built-in logging system

# Configure logging — this prints diagnostic messages to the terminal
# Format: timestamp [LEVEL] module: message
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # __name__ = "rxnorm" (this file's name)

# =============================================================================
# LAYER 1: LOCAL FALLBACK CACHE
# =============================================================================
# This dictionary maps commonly used brand names (in lowercase) to their
# active ingredient(s). It covers our demo scenario 100% reliably.
#
# WHY LOWERCASE KEYS? We always lowercase the input before lookup.
# "Brufen 400" → "brufen 400" → match → "ibuprofen"
# This makes matching case-insensitive without complex regex.
#
# WHY A DICTIONARY? O(1) lookup time — instant, no network needed.
#
LOCAL_DRUG_CACHE: dict[str, str] = {
    # ─── Analgesics & Antipyretics (Paracetamol Brands - Indian & Global) ─────
    "paracetamol": "paracetamol",
    "acetaminophen": "paracetamol",
    "tylenol": "paracetamol",
    "dolo": "paracetamol",
    "dolo 650": "paracetamol",
    "calpol": "paracetamol",
    "calpol 500": "paracetamol",
    "calpol 650": "paracetamol",
    "pacimol": "paracetamol",
    "pacimol 500": "paracetamol",
    "pacimol 650": "paracetamol",
    "paracip": "paracetamol",
    "paracip 500": "paracetamol",
    "paracip 650": "paracetamol",
    "crocin": "paracetamol",
    "crocin advance": "paracetamol",
    "metacin": "paracetamol",
    "sumo l": "paracetamol",
    "pyremol": "paracetamol",
    "fevaast": "paracetamol",

    # ─── NSAIDs (Non-Steroidal Anti-Inflammatory Drugs) ───────────────────────
    "ibuprofen": "ibuprofen",
    "brufen": "ibuprofen",
    "advil": "ibuprofen",
    "nurofen": "ibuprofen",
    "motrin": "ibuprofen",
    "ibugesic": "ibuprofen",
    "combiflam": "ibuprofen",         # Common Indian brand (ibuprofen + paracetamol)
    "flexon": "ibuprofen",            # Ibuprofen + Paracetamol
    "naproxen": "naproxen",
    "aleve": "naproxen",
    "naprosyn": "naproxen",
    "diclofenac": "diclofenac",
    "voltaren": "diclofenac",
    "voveran": "diclofenac",          # Common Indian brand
    "voveran sr": "diclofenac",
    "dynapar": "diclofenac",          # Common Indian brand
    "aspirin": "aspirin",
    "ecosprin": "aspirin",            # Common Indian brand
    "ecosprin 75": "aspirin",
    "ecosprin 150": "aspirin",
    "disprin": "aspirin",
    "mefenamic acid": "mefenamic acid",
    "meftal": "mefenamic acid",
    "meftal spas": "mefenamic acid",

    # ─── Blood Thinners / Anticoagulants ──────────────────────────────────────
    "warfarin": "warfarin",
    "coumadin": "warfarin",
    "warf": "warfarin",
    "clopidogrel": "clopidogrel",
    "plavix": "clopidogrel",
    "clopilet": "clopidogrel",        # Common Indian brand
    "clavix": "clopidogrel",          # Common Indian brand
    "deplatt": "clopidogrel",

    # ─── Blood Pressure / Hypertension (Indian & Global) ─────────────────────
    "telmisartan": "telmisartan",
    "telma": "telmisartan",           # Extremely common in India
    "telma 40": "telmisartan",
    "telmikind": "telmisartan",
    "telpres": "telmisartan",
    "cresar": "telmisartan",
    "losartan": "losartan",
    "losar": "losartan",
    "repace": "losartan",
    "lisinopril": "lisinopril",
    "zestril": "lisinopril",
    "prinivil": "lisinopril",
    "enalapril": "enalapril",
    "vasotec": "enalapril",
    "envas": "enalapril",             # Indian brand
    "ramipril": "ramipril",
    "altace": "ramipril",
    "cardace": "ramipril",            # Common Indian brand
    "hopace": "ramipril",

    # ─── Potassium Supplements ────────────────────────────────────────────────
    "potassium": "potassium",
    "potassium chloride": "potassium",
    "klor-con": "potassium",
    "slow-k": "potassium",
    "potklor": "potassium",           # Indian syrup/tablet brand

    # ─── Statins (Cholesterol) ────────────────────────────────────────────────
    "atorvastatin": "atorvastatin",
    "lipitor": "atorvastatin",
    "atorva": "atorvastatin",         # Indian brand
    "atorlip": "atorvastatin",        # Indian brand
    "tonact": "atorvastatin",         # Indian brand
    "simvastatin": "simvastatin",
    "zocor": "simvastatin",
    "simvotin": "simvastatin",
    "rosuvastatin": "rosuvastatin",
    "crestor": "rosuvastatin",
    "rozat": "rosuvastatin",          # Indian brand
    "rosuvas": "rosuvastatin",        # Indian brand

    # ─── Beta-Blockers (Heart Rate / Blood Pressure) ──────────────────────────
    "metoprolol": "metoprolol",
    "lopressor": "metoprolol",
    "toprol": "metoprolol",
    "betaloc": "metoprolol",          # Indian brand
    "metolar": "metoprolol",          # Indian brand
    "starpress": "metoprolol",
    "atenolol": "atenolol",
    "tenormin": "atenolol",
    "aten": "atenolol",               # Indian brand

    # ─── Calcium Channel Blockers ─────────────────────────────────────────────
    "amlodipine": "amlodipine",
    "norvasc": "amlodipine",
    "amlopres": "amlodipine",         # Indian brand
    "stamlo": "amlodipine",           # Indian brand
    "amlong": "amlodipine",           # Indian brand
    "verapamil": "verapamil",
    "calan": "verapamil",
    "diltiazem": "diltiazem",
    "cardizem": "diltiazem",
    "dilzem": "diltiazem",
    "nifedipine": "nifedipine",
    "adalat": "nifedipine",
    "depin": "nifedipine",

    # ─── Antibiotics ──────────────────────────────────────────────────────────
    "amoxicillin": "amoxicillin",
    "amoxil": "amoxicillin",
    "mox": "amoxicillin",
    "novamox": "amoxicillin",         # Indian brand
    "augmentin": "amoxicillin",       # Amoxicillin + Clavulanate
    "moxikind": "amoxicillin",
    "azithromycin": "azithromycin",
    "zithromax": "azithromycin",
    "azee": "azithromycin",           # Indian brand
    "azithral": "azithromycin",       # Indian brand
    "clarithromycin": "clarithromycin",
    "biaxin": "clarithromycin",
    "klacid": "clarithromycin",
    "erythromycin": "erythromycin",
    "ciprofloxacin": "ciprofloxacin",
    "cipro": "ciprofloxacin",
    "ciplox": "ciprofloxacin",        # Indian brand
    "cifran": "ciprofloxacin",        # Indian brand
    "ofloxacin": "ofloxacin",
    "zanocin": "ofloxacin",
    "oflin": "ofloxacin",
    "metronidazole": "metronidazole",
    "flagyl": "metronidazole",
    "metrogyl": "metronidazole",      # Indian brand
    "gentamicin": "gentamicin",
    "garamycin": "gentamicin",

    # ─── Antifungals ──────────────────────────────────────────────────────────
    "fluconazole": "fluconazole",
    "diflucan": "fluconazole",
    "forcan": "fluconazole",          # Indian brand
    "zocon": "fluconazole",           # Indian brand

    # ─── Antidepressants / SSRIs ──────────────────────────────────────────────
    "sertraline": "sertraline",
    "zoloft": "sertraline",
    "serta": "sertraline",            # Indian brand
    "daxid": "sertraline",
    "fluoxetine": "fluoxetine",
    "prozac": "fluoxetine",
    "flunil": "fluoxetine",           # Indian brand
    "amitriptyline": "amitriptyline",
    "elavil": "amitriptyline",
    "tryptomer": "amitriptyline",     # Indian brand
    "doxepin": "doxepin",
    "sinequan": "doxepin",
    "escitalopram": "escitalopram",
    "lexapro": "escitalopram",
    "nexito": "escitalopram",         # Indian brand
    "cipralex": "escitalopram",

    # ─── Benzodiazepines / Sedatives / Sleep Aids ─────────────────────────────
    "diazepam": "diazepam",
    "valium": "diazepam",
    "calmpose": "diazepam",           # Indian brand
    "lorazepam": "lorazepam",
    "ativan": "lorazepam",
    "lorlip": "lorazepam",
    "trapex": "lorazepam",
    "alprazolam": "alprazolam",
    "xanax": "alprazolam",
    "alprax": "alprazolam",           # Indian brand
    "restyl": "alprazolam",           # Indian brand
    "trika": "alprazolam",
    "zolpidem": "zolpidem",
    "ambien": "zolpidem",
    "nitrest": "zolpidem",            # Indian brand
    "clonazepam": "clonazepam",
    "klonopin": "clonazepam",
    "clona": "clonazepam",
    "lonazep": "clonazepam",          # Indian brand

    # ─── Opioids / Pain Relievers ─────────────────────────────────────────────
    "tramadol": "tramadol",
    "ultram": "tramadol",
    "tramazac": "tramadol",           # Indian brand
    "ultram": "tramadol",
    "codeine": "codeine",
    "oxycodone": "oxycodone",
    "oxycontin": "oxycodone",

    # ─── Antihistamines ───────────────────────────────────────────────────────
    "diphenhydramine": "diphenhydramine",
    "benadryl": "diphenhydramine",
    "promethazine": "promethazine",
    "phenergan": "promethazine",
    "chlorphenamine": "chlorphenamine",
    "chlorpheniramine": "chlorphenamine",
    "piriton": "chlorphenamine",
    "cetirizine": "cetirizine",
    "zyrtec": "cetirizine",
    "cetzine": "cetirizine",          # Indian brand
    "alerid": "cetirizine",           # Very common Indian brand (Cipla)
    "alerid 10": "cetirizine",
    "alerid 10mg": "cetirizine",
    "zyncet": "cetirizine",           # Indian brand
    "cetrizet": "cetirizine",         # Indian brand
    "alerdice": "cetirizine",
    "levocetirizine": "levocetirizine",
    "xyzal": "levocetirizine",
    "levocet": "levocetirizine",
    "1-al": "levocetirizine",         # Indian brand

    # ─── Diabetes Medications ─────────────────────────────────────────────────
    "metformin": "metformin",
    "glucophage": "metformin",
    "glycomet": "metformin",          # Indian brand
    "glycomet sr": "metformin",
    "obimet": "metformin",
    "glibenclamide": "glibenclamide",
    "glyburide": "glibenclamide",
    "daonil": "glibenclamide",
    "glipizide": "glipizide",
    "glucotrol": "glipizide",
    "glimepiride": "glimepiride",
    "amaryl": "glimepiride",
    "gemer": "glimepiride",
    "insulin": "insulin",

    # ─── Proton Pump Inhibitors (Acid / Stomach) ──────────────────────────────
    "omeprazole": "omeprazole",
    "prilosec": "omeprazole",
    "omez": "omeprazole",             # Indian brand
    "pantoprazole": "pantoprazole",
    "protonix": "pantoprazole",
    "pantop": "pantoprazole",         # Indian brand
    "pantocid": "pantoprazole",       # Indian brand
    "pan": "pantoprazole",
    "pan 40": "pantoprazole",
    "pan d": "pantoprazole",          # Pantoprazole + Domperidone
    "rabeprazole": "rabeprazole",
    "aciphex": "rabeprazole",
    "rabeloc": "rabeprazole",         # Indian brand
    "happi": "rabeprazole",

    # ─── Diuretics ────────────────────────────────────────────────────────────
    "furosemide": "furosemide",
    "lasix": "furosemide",
    "spironolactone": "spironolactone",
    "aldactone": "spironolactone",

    # ─── Heart / Cardiac ──────────────────────────────────────────────────────
    "digoxin": "digoxin",
    "lanoxin": "digoxin",
    "amiodarone": "amiodarone",
    "cordarone": "amiodarone",
    "methotrexate": "methotrexate",

    # ─── Nitrates ─────────────────────────────────────────────────────────────
    "isosorbide mononitrate": "isosorbide mononitrate",
    "imdur": "isosorbide mononitrate",
    "ismo": "isosorbide mononitrate",
    "monotrate": "isosorbide mononitrate", # Indian brand
    "nitroglycerin": "nitroglycerin",
    "nitrostat": "nitroglycerin",
    "sorbitrate": "nitroglycerin",    # Indian brand

    # ─── Calcium & Supplements ────────────────────────────────────────────────
    "calcium": "calcium",
    "calcium carbonate": "calcium",
    "shelcal": "calcium",             # Indian brand
    "shelcal 500": "calcium",
    "cipcal": "calcium",

    # ─── ED / Pulmonary Hypertension ──────────────────────────────────────────
    "sildenafil": "sildenafil",
    "viagra": "sildenafil",
    "revatio": "sildenafil",
    "manforce": "sildenafil",         # Indian brand
    "penegra": "sildenafil",

    # ─── Others ───────────────────────────────────────────────────────────────
    "lithium": "lithium",
    "phenytoin": "phenytoin",
    "dilantin": "phenytoin",
    "eptoin": "phenytoin",            # Indian brand
    "allopurinol": "allopurinol",
    "zyloprim": "allopurinol",
    "zyloric": "allopurinol",
}


def _normalize_raw_input(raw: str) -> str:
    """
    Pre-process raw user input before cache or API lookup.

    What this does step by step:
      1. Lowercase: "Brufen 400MG" → "brufen 400mg"
      2. Strip whitespace: "  brufen  " → "brufen"
      3. Remove dosage numbers with units: "brufen 400mg" → "brufen"
         This handles variants like "400", "400mg", "400 mg", "400MG"

    TEACHING NOTE: This is called "string normalization" — making messy,
    varied human input consistent before processing. It's one of the
    most important techniques in any real-world data pipeline.
    """
    import re

    text = raw.lower().strip()

    # Remove dosage patterns: numbers optionally followed by units
    # Regex explanation:
    #   \s* → optional whitespace
    #   \d+ → one or more digits (e.g., 400)
    #   (\.\d+)? → optional decimal (e.g., .5 in "0.5mg")
    #   \s* → optional whitespace
    #   (mg|mcg|g|ml|iu|units|tab|tabs|cap|caps)? → optional unit
    text = re.sub(r"\s*\d+(\.\d+)?\s*(mg|mcg|g|ml|iu|units?|tabs?|caps?)?", "", text)

    # Clean up leftover hyphens/slashes and collapse extra spaces
    text = re.sub(r"[-/]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _lookup_cache(normalized_input: str) -> str | None:
    """
    Look up the normalized input string in our local cache.

    TEACHING NOTE: We try multiple "views" of the input:
      - Exact match: "brufen" → found → "ibuprofen"
      - Partial match: Check if any cache key appears inside the input
        (handles "brufen plus" → "brufen" key → "ibuprofen")
    This handles compound brand names that include the drug name.
    """
    # Try exact match first (fastest)
    if normalized_input in LOCAL_DRUG_CACHE:
        return LOCAL_DRUG_CACHE[normalized_input]

    # Try partial match: does any known key appear in the input?
    for key, ingredient in LOCAL_DRUG_CACHE.items():
        if key in normalized_input:
            return ingredient

    return None  # Not found in cache


async def _lookup_rxnorm_api(drug_name: str) -> str | None:
    """
    Query the NIH RxNav API to find a drug's active ingredient.

    TEACHING NOTE — How RxNav works:
      Step 1: approximateTerm.json
              → Input: any free-text drug name
              → Output: list of candidate RxCUIs (drug identifiers)
              → Example: "Brufen 400" → RxCUI "5640"

      Step 2: allProperties.json
              → Input: an RxCUI
              → Output: all known properties including "INGREDIENTS"
              → Example: RxCUI "5640" → "ibuprofen"

    WHY httpx AND NOT requests?
      httpx supports `async with` syntax — it plays nicely with
      FastAPI's async event loop. The `requests` library would
      BLOCK the event loop and freeze other requests.

    TEACHING NOTE — try/except:
      Network calls can ALWAYS fail (timeout, DNS error, API down).
      We wrap everything in try/except so a failed lookup returns
      None (graceful failure) instead of crashing the whole server.
    """
    base_url = "https://rxnav.nlm.nih.gov/REST"

    try:
        # We use an async HTTP client (context manager pattern)
        async with httpx.AsyncClient(timeout=5.0) as client:  # 5 second timeout

            # ─── Step 1: Get candidate RxCUIs from free text ──────────────
            resp = await client.get(
                f"{base_url}/approximateTerm.json",
                params={"term": drug_name, "maxEntries": 5}
            )
            resp.raise_for_status()  # Raises exception if HTTP error (404, 500, etc.)

            data = resp.json()

            # Navigate the JSON structure to get candidates
            # The API returns: {"approximateGroup": {"candidate": [...]}}
            candidates = (
                data.get("approximateGroup", {})
                    .get("candidate", [])
            )

            if not candidates:
                logger.info(f"RxNorm: No candidates found for '{drug_name}'")
                return None

            # Take the best match (highest score = first candidate)
            rxcui = candidates[0].get("rxcui")
            if not rxcui:
                return None

            logger.info(f"RxNorm: '{drug_name}' → RxCUI {rxcui}")

            # ─── Step 2: Get ingredient(s) from RxCUI ─────────────────────
            resp2 = await client.get(
                f"{base_url}/rxcui/{rxcui}/allProperties.json",
                params={"prop": "ATTRIBUTES"}
            )
            resp2.raise_for_status()

            data2 = resp2.json()
            props = (
                data2.get("propConceptGroup", {})
                     .get("propConcept", [])
            )

            # Search for the "INGREDIENTS" property in the response
            # The API returns many properties; we want the ingredient one
            for prop in props:
                if prop.get("propName") == "INGREDIENTS":
                    ingredient = prop.get("propValue", "").lower().strip()
                    if ingredient:
                        logger.info(f"RxNorm: RxCUI {rxcui} → ingredient '{ingredient}'")
                        return ingredient

            # If no INGREDIENTS property, try using the concept name itself
            # (works for single-ingredient drugs where name == ingredient)
            resp3 = await client.get(f"{base_url}/rxcui/{rxcui}/properties.json")
            resp3.raise_for_status()
            data3 = resp3.json()
            name = (
                data3.get("properties", {})
                     .get("name", "")
                     .lower()
                     .strip()
            )
            if name:
                logger.info(f"RxNorm: RxCUI {rxcui} → name '{name}' used as ingredient")
                return name

            return None

    except httpx.TimeoutException:
        logger.warning(f"RxNorm API timeout for '{drug_name}' — falling back to cache")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"RxNorm API HTTP error for '{drug_name}': {e}")
        return None
    except Exception as e:
        logger.warning(f"RxNorm API unexpected error for '{drug_name}': {e}")
        return None


# =============================================================================
# LAYER 2.5: LIVE WEB SCRAPER (For Indian / Regional / Newly Released Drugs)
# =============================================================================
# TEACHING NOTE — Why a Web Scraper Fallback?
# New medicines and regional brand names (especially from Indian pharma)
# are often not in US RxNav. When both local cache and RxNav miss,
# this scraper checks web drug indexes (like 1mg / generic composition search)
# to extract the active chemical salt automatically.
#
# Once scraped, we automatically cache it in LOCAL_DRUG_CACHE so future
# lookups take 0ms!

async def _scrape_drug_composition(drug_name: str) -> str | None:
    """
    Search and scrape the active salt/composition of an unknown drug from the web.
    Uses BeautifulSoup to extract salt patterns.
    """
    import re
    from bs4 import BeautifulSoup
    import urllib.parse

    clean_term = _normalize_raw_input(drug_name)
    query = f"{clean_term} tablet composition salt active ingredient"
    search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
            resp = await client.get(search_url, headers=headers)
            if resp.status_code != 200:
                logger.info(f"Scraper: DuckDuckGo returned status {resp.status_code}")
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            snippets = []

            # Extract search result snippets
            for tag in soup.select(".result__snippet"):
                text = tag.get_text(separator=" ", strip=True)
                snippets.append(text)

            combined_text = " ".join(snippets).lower()

            # Check if any known active ingredient from our cache is mentioned in the snippets
            known_ingredients = sorted(set(LOCAL_DRUG_CACHE.values()), key=len, reverse=True)

            if combined_text:
                for ingredient in known_ingredients:
                    patterns = [
                        rf"contains\s+(?:the\s+active\s+ingredient\s+)?{re.escape(ingredient)}",
                        rf"composition[:\s]+[^\.\n]*{re.escape(ingredient)}",
                        rf"salt(?:\s+composition)?[:\s]+[^\.\n]*{re.escape(ingredient)}",
                        rf"active\s+ingredient[:\s]+{re.escape(ingredient)}",
                        rf"{re.escape(ingredient)}\s+(?:\d+\s*mg|tablet|capsule|syrup)",
                    ]
                    for pat in patterns:
                        if re.search(pat, combined_text, re.IGNORECASE):
                            logger.info(f"🌐 Web Scraper matched: '{drug_name}' contains '{ingredient}'")
                            return ingredient

            # ─── Backup Web Fallback: Wikipedia Medical API (No bot-blocking) ───
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_term)}&utf8=&format=json"
            wiki_resp = await client.get(wiki_url)
            if wiki_resp.status_code == 200:
                wiki_data = wiki_resp.json()
                wiki_snippets = [item.get("snippet", "") for item in wiki_data.get("query", {}).get("search", [])]
                wiki_text = " ".join(wiki_snippets).lower()

                for ingredient in known_ingredients:
                    if ingredient in wiki_text:
                        logger.info(f"🌐 Wikipedia Medical Intelligence matched: '{drug_name}' → '{ingredient}'")
                        return ingredient

    except Exception as e:
        logger.warning(f"Web scraper error for '{drug_name}': {e}")
        return None

    except Exception as e:
        logger.warning(f"Web scraper error for '{drug_name}': {e}")
        return None

    return None


async def normalize_drug(raw_name: str) -> dict:
    """
    PRIMARY PUBLIC FUNCTION — normalize a single drug name.

    This is the function that main.py calls. It orchestrates the
    3-layer lookup and returns a structured result dictionary.

    Returns a dict with:
      - input:      the original user-typed string (for display)
      - normalized: the cleaned string we searched with
      - ingredient: the active ingredient found (or None)
      - rxcui:      the RxNorm identifier (or None)
      - matched:    True if we found the ingredient, False if unknown

    TEACHING NOTE — Why return a dict instead of just the ingredient?
    We need to track BOTH the original input (to show the user what
    they typed) AND the processed result. Returning a dict (structured
    data) keeps all related information bundled together cleanly.
    """
    if not raw_name or not raw_name.strip():
        return {"input": raw_name, "normalized": "", "ingredient": None,
                "rxcui": None, "matched": False}

    original = raw_name.strip()
    normalized = _normalize_raw_input(original)

    # ─── Layer 1: Local cache ──────────────────────────────────────────────────
    cached = _lookup_cache(normalized)
    if cached:
        logger.info(f"Cache hit: '{original}' → '{cached}'")
        return {
            "input": original,
            "normalized": normalized,
            "ingredient": cached,
            "rxcui": None,          # We don't store RxCUIs in local cache
            "matched": True
        }

    # ─── Layer 2: RxNorm API ──────────────────────────────────────────────────
    logger.info(f"Cache miss for '{original}', trying RxNorm API...")
    api_ingredient = await _lookup_rxnorm_api(original)

    if api_ingredient:
        # Cache this result locally for future calls in this session
        LOCAL_DRUG_CACHE[normalized] = api_ingredient
        return {
            "input": original,
            "normalized": normalized,
            "ingredient": api_ingredient,
            "rxcui": None,
            "matched": True
        }

    # ─── Layer 2.5: Live Web Scraper (DuckDuckGo / Medical Composition) ───────
    logger.info(f"RxNorm miss for '{original}', querying web drug intelligence...")
    scraped_ingredient = await _scrape_drug_composition(original)

    if scraped_ingredient:
        # Auto-cache scraped result so subsequent lookups are instant
        LOCAL_DRUG_CACHE[normalized] = scraped_ingredient
        logger.info(f"Cached web-scraped ingredient: '{normalized}' → '{scraped_ingredient}'")
        return {
            "input": original,
            "normalized": normalized,
            "ingredient": scraped_ingredient,
            "rxcui": None,
            "matched": True,
            "source": "web_scraped"
        }

    # ─── Layer 3: Graceful degradation ────────────────────────────────────────
    # Unknown drug — return matched=False so the engine flags it as "Not Checked"
    # CRITICAL: We NEVER return matched=True for unknowns.
    #           Falsely calling something "safe" (green) is dangerous.
    logger.warning(f"Could not normalize '{original}' — flagging as unmatched")
    return {
        "input": original,
        "normalized": normalized,
        "ingredient": None,
        "rxcui": None,
        "matched": False
    }


async def normalize_drugs(names: list[str]) -> list[dict]:
    """
    Normalize a LIST of drug names concurrently.

    TEACHING NOTE — Why asyncio.gather()?
    If we have 5 drugs and each RxNorm call takes ~500ms, doing them
    one-by-one would take 2.5 seconds. With asyncio.gather(), all 5
    calls run CONCURRENTLY (at the same time), finishing in ~500ms.

    This is the power of async programming — I/O-bound tasks (waiting
    for network) can run in parallel without needing multiple CPU threads.
    """
    import asyncio

    # Create a list of "coroutines" (async tasks that haven't started yet)
    # Then gather() runs them all concurrently and waits for all to finish
    tasks = [normalize_drug(name) for name in names]
    results = await asyncio.gather(*tasks)  # * unpacks the list into arguments

    return list(results)
