import os
import json
import re
from typing import Dict, List
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Localized situational questions (Nepali business context)
PSYCHOMETRIC_QUESTIONS = [
    {
        "id": "q1",
        "trait": "risk_aversion",
        "question": "Raju runs a tea shop. His supplier offers double stock at half price, but payment is due in 3 days. He only has 60% of the money. What should he do?",
        "options": {
            "A": "Take the full deal and borrow the rest immediately",
            "B": "Take only what he can afford right now",
            "C": "Wait until next month when he has full payment",
            "D": "Negotiate a 2-week payment plan with the supplier"
        },
        "scoring": {"A": 20, "B": 60, "C": 80, "D": 70}
    },
    {
        "id": "q2",
        "trait": "conscientiousness",
        "question": "Sita's vegetable business had a bad month due to flooding. Her NEA electricity bill is due. She has just enough money for either the bill or restocking vegetables. What does she do?",
        "options": {
            "A": "Pay the electricity bill first — obligations come first",
            "B": "Restock vegetables — without stock there is no income",
            "C": "Pay half the electricity bill and use rest for stock",
            "D": "Borrow from a neighbor to pay the bill, restock with savings"
        },
        "scoring": {"A": 90, "B": 30, "C": 50, "D": 80}
    },
    {
        "id": "q3",
        "trait": "social_trust",
        "question": "A new merchant moves next to your shop and asks to borrow NPR 2,000 for one week. You know nothing about them. What do you do?",
        "options": {
            "A": "Lend the full amount — community helps community",
            "B": "Lend half and see if they repay before lending more",
            "C": "Politely decline — you don't know them yet",
            "D": "Ask a mutual acquaintance to vouch for them first"
        },
        "scoring": {"A": 60, "B": 70, "C": 50, "D": 90}
    },
    {
        "id": "q4",
        "trait": "resilience",
        "question": "Your main supplier suddenly increases prices by 20% due to fuel costs. Your margins will drop significantly. What is your first action?",
        "options": {
            "A": "Absorb the cost for now and hope prices drop",
            "B": "Immediately find an alternative supplier",
            "C": "Gradually increase your own prices while finding alternatives",
            "D": "Talk to other merchants and negotiate collectively with the supplier"
        },
        "scoring": {"A": 30, "B": 60, "C": 70, "D": 90}
    },
    {
        "id": "q5",
        "trait": "planning",
        "question": "You earn well during Dashain/Tihar festival season. What do you do with the extra income?",
        "options": {
            "A": "Spend it — the family deserves a good festival",
            "B": "Save all of it for slow months",
            "C": "Reinvest most in stock, save some for emergencies",
            "D": "Pay off any debts first, then save the rest"
        },
        "scoring": {"A": 20, "B": 60, "C": 80, "D": 90}
    }
]


def get_questions() -> List[Dict]:
    """Return questions for the frontend to display."""
    return [
        {
            "id": q["id"],
            "trait": q["trait"],
            "question": q["question"],
            "options": q["options"]
        }
        for q in PSYCHOMETRIC_QUESTIONS
    ]


def score_responses_deterministic(responses: Dict[str, str]) -> Dict:
    """
    Fast deterministic scoring (no API call needed for basic scoring).
    Used as fallback or for rapid prototyping.
    """
    trait_scores = {
        "risk_aversion": 0,
        "conscientiousness": 0,
        "social_trust": 0,
        "resilience": 0,
        "planning": 0
    }
    trait_counts = {k: 0 for k in trait_scores}

    for q in PSYCHOMETRIC_QUESTIONS:
        answer = responses.get(q["id"])
        if answer and answer in q["scoring"]:
            trait = q["trait"]
            trait_scores[trait] += q["scoring"][answer]
            trait_counts[trait] += 1

    # Normalize each trait to 0-100
    for trait in trait_scores:
        if trait_counts[trait] > 0:
            trait_scores[trait] = round(
                trait_scores[trait] / trait_counts[trait]
            )

    return trait_scores


def analyze_with_gemini(
    merchant_name: str,
    responses: Dict[str, str],
    trait_scores: Dict[str, int]
) -> Dict:
    """
    Use Gemini to provide deeper analysis and natural language explanation.
    Falls back gracefully if API is unavailable.
    """
    try:
        model = genai.GenerativeModel(
            os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        )

        # Build response summary for Gemini
        response_summary = []
        for q in PSYCHOMETRIC_QUESTIONS:
            answer = responses.get(q["id"], "no answer")
            option_text = q["options"].get(answer, "unknown")
            response_summary.append(
                f"Q ({q['trait']}): {q['question'][:80]}... → {answer}: {option_text}"
            )

        prompt = f"""You are a financial inclusion specialist scoring a merchant's psychometric profile for micro-credit assessment in Nepal.

Merchant: {merchant_name}

Their situational responses:
{chr(10).join(response_summary)}

Initial trait scores (0-100):
{json.dumps(trait_scores, indent=2)}

Analyze these responses and return ONLY a valid JSON object. No preamble, no markdown, no explanation outside the JSON.

Return exactly this structure:
{{
  "conscientiousness": <integer 0-100>,
  "risk_aversion": <integer 0-100>,
  "social_trust": <integer 0-100>,
  "resilience": <integer 0-100>,
  "planning": <integer 0-100>,
  "psychometric_score": <weighted average integer 0-100>,
  "credit_personality": "<one of: Cautious Planner, Community Builder, Risk Taker, Resilient Adapter, Conservative Saver>",
  "insight": "<1 sentence insight about this merchant's financial personality in context of Nepal>",
  "red_flags": "<any concerning patterns, or 'none'>",
  "strengths": "<key strength for lending decisions>"
}}"""

        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Clean any markdown fences
        raw = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)

        # Validate required fields exist
        required = [
            "conscientiousness", "risk_aversion", "social_trust",
            "resilience", "planning", "psychometric_score"
        ]
        for field in required:
            if field not in result:
                result[field] = trait_scores.get(field, 50)

        return result

    except Exception as e:
        # Graceful fallback: use deterministic scores + placeholder text
        weighted = round(
            trait_scores.get("conscientiousness", 50) * 0.30 +
            trait_scores.get("risk_aversion", 50) * 0.25 +
            trait_scores.get("social_trust", 50) * 0.20 +
            trait_scores.get("resilience", 50) * 0.15 +
            trait_scores.get("planning", 50) * 0.10
        )
        return {
            **trait_scores,
            "psychometric_score": weighted,
            "credit_personality": "Cautious Planner",
            "insight": "Profile computed from deterministic scoring (Gemini unavailable).",
            "red_flags": "none",
            "strengths": "Consistent responses across situational questions.",
            "error": str(e)
        }


def run_psychometric_assessment(
    merchant_id: str,
    merchant_name: str,
    responses: Dict[str, str]
) -> Dict:
    """Main function called by the API endpoint."""
    trait_scores = score_responses_deterministic(responses)
    gemini_result = analyze_with_gemini(merchant_name, responses, trait_scores)

    return {
        "merchant_id": merchant_id,
        "trait_scores": {
            "conscientiousness": gemini_result.get("conscientiousness", trait_scores["conscientiousness"]),
            "risk_aversion": gemini_result.get("risk_aversion", trait_scores["risk_aversion"]),
            "social_trust": gemini_result.get("social_trust", trait_scores["social_trust"]),
            "resilience": gemini_result.get("resilience", trait_scores["resilience"]),
            "planning": gemini_result.get("planning", trait_scores["planning"])
        },
        "psychometric_score": gemini_result.get("psychometric_score", 50),
        "credit_personality": gemini_result.get("credit_personality", "Unknown"),
        "insight": gemini_result.get("insight", ""),
        "red_flags": gemini_result.get("red_flags", "none"),
        "strengths": gemini_result.get("strengths", "")
    }
