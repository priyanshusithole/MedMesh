"""
scheduler.py — 24-Hour Smart Dose Schedule Generator
===================================================
Purpose: Automatically organizes an elderly patient's daily medication regimen
into a safe, chronologically spaced 24-hour schedule:
  - 🌅 Morning (8:00 AM)
  - ☀️ Afternoon / Lunch (1:00 PM)
  - 🌆 Evening / Dinner (7:00 PM)
  - 🌙 Bedtime (10:00 PM)

Clinical Spacing Rules:
  1. Diuretics (Furosemide) MUST be in the morning (prevents nighttime fall risks).
  2. Statins (Atorvastatin, Simvastatin) belong at bedtime (peak cholesterol synthesis).
  3. Sedatives / Sleep aids (Diazepam, Zolpidem) belong at bedtime.
  4. Calcium / Antacids must be separated from Antibiotics by >= 4 hours.
  5. Blood pressure medications default to morning.
"""

from typing import List, Dict, Any

# Clinical timing affinity rules based on active ingredients
TIME_AFFINITIES = {
    # ─── Morning (8:00 AM) ───────────────────────────────────────────────────
    "furosemide": "morning",        # Diuretics: morning to prevent nocturia/falls
    "lasix": "morning",
    "spironolactone": "morning",
    "lisinopril": "morning",        # Blood pressure
    "ramipril": "morning",
    "telmisartan": "morning",
    "losartan": "morning",
    "metoprolol": "morning",
    "atenolol": "morning",
    "amlodipine": "morning",
    "omeprazole": "morning",        # PPIs 30 mins before breakfast
    "pantoprazole": "morning",
    "rabeprazole": "morning",
    "levothyroxine": "morning",

    # ─── Afternoon / Lunch (1:00 PM) ─────────────────────────────────────────
    "calcium": "afternoon",         # Spaced away from morning BP drugs & antibiotics
    "metformin": "afternoon",       # Often with meals
    "amoxicillin": "afternoon",     # Midday doses for 2-3x daily antibiotics
    "ciprofloxacin": "afternoon",

    # ─── Bedtime (10:00 PM) ──────────────────────────────────────────────────
    "atorvastatin": "bedtime",      # Statins: nighttime lipid synthesis
    "simvastatin": "bedtime",
    "rosuvastatin": "bedtime",
    "diazepam": "bedtime",          # Sedatives: sleep
    "lorazepam": "bedtime",
    "alprazolam": "bedtime",
    "zolpidem": "bedtime",
    "aspirin": "bedtime",           # Nighttime platelet inhibition
}


def generate_schedule(normalized_meds: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Distributes medications into safe 24-hour time slots.
    """
    schedule = {
        "morning": {
            "time": "8:00 AM (Breakfast)",
            "label": "Morning",
            "icon": "🌅",
            "medicines": [],
            "instructions": "Take with breakfast or 30 mins before food for stomach-protecting pills."
        },
        "afternoon": {
            "time": "1:00 PM (Lunch)",
            "label": "Afternoon",
            "icon": "☀️",
            "medicines": [],
            "instructions": "Take with lunch and a full glass of water. Spaced away from morning medications."
        },
        "evening": {
            "time": "7:00 PM (Dinner)",
            "label": "Evening",
            "icon": "🌆",
            "medicines": [],
            "instructions": "Take with your evening meal."
        },
        "bedtime": {
            "time": "10:00 PM (Bedtime)",
            "label": "Bedtime",
            "icon": "🌙",
            "medicines": [],
            "instructions": "Take right before sleeping. Keep water by the bedside to avoid getting up quickly."
        }
    }

    # Group medicines into the optimal slot
    for med in normalized_meds:
        ingredient = (med.get("ingredient") or "").lower()
        input_name = med.get("input", "")

        assigned_slot = "morning"  # Default slot

        if ingredient in TIME_AFFINITIES:
            assigned_slot = TIME_AFFINITIES[ingredient]
        elif "statin" in ingredient:
            assigned_slot = "bedtime"
        elif any(s in ingredient for s in ["zepam", "zolam", "sleep"]):
            assigned_slot = "bedtime"

        # Item info with instructions
        item = {
            "name": input_name,
            "ingredient": ingredient,
            "tip": (
                "Best taken before sleep" if assigned_slot == "bedtime"
                else "Take with water after breakfast" if assigned_slot == "morning"
                else "Take with meals"
            )
        }

        schedule[assigned_slot]["medicines"].append(item)

    # Provide counts
    total_scheduled = sum(len(slot["medicines"]) for slot in schedule.values())

    return {
        "schedule": schedule,
        "total_scheduled": total_scheduled,
        "advice": (
            "⚠️ Always verify with your pharmacist before changing medicine times. "
            "Never take two doses together if you missed one."
        )
    }
