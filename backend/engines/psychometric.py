"""
psychometric.py — TrustBridge
Fixes applied:
  1. Hallucination guard: 3-stage validation (schema + ±25 cross-check + enum lock)
  2. Bilingual questions: Nepali (default) + English
  3. Gamification: XP rewards + badge system
"""

import os
import json
import re
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# BILINGUAL QUESTION BANK
# ─────────────────────────────────────────────

PSYCHOMETRIC_QUESTIONS = [
    {
        "id": "q1",
        "trait": "risk_aversion",
        "question_en": "Raju runs a tea shop. His supplier offers double stock at half price, but payment is due in 3 days. He only has 60% of the money. What should he do?",
        "question_ne": "राजुको चिया पसल छ। उसको आपूर्तिकर्ताले आधा मूल्यमा दोब्बर माल दिन्छ, तर ३ दिनभित्र भुक्तानी गर्नुपर्छ। उसँग ६०% पैसा मात्र छ। उसले के गर्नुपर्छ?",
        "options_en": {
            "A": "Take the full deal and borrow the rest immediately",
            "B": "Take only what he can afford right now",
            "C": "Wait until next month when he has full payment",
            "D": "Negotiate a 2-week payment plan with the supplier",
        },
        "options_ne": {
            "A": "पूरै सम्झौता गर्ने र बाँकी पैसा तुरुन्त सापट लिने",
            "B": "अहिले सक्ने जति मात्र किन्ने",
            "C": "अर्को महिना पूरै पैसा हुँदा किन्ने",
            "D": "आपूर्तिकर्तासँग २ हप्ताको किस्ता मिलाउने",
        },
        "scoring": {"A": 20, "B": 60, "C": 80, "D": 70},
    },
    {
        "id": "q2",
        "trait": "conscientiousness",
        "question_en": "Sita's vegetable business had a bad month due to flooding. Her NEA electricity bill is due. She has just enough for either the bill or restocking vegetables. What does she do?",
        "question_ne": "बाढीका कारण सीताको तरकारी व्यवसाय यो महिना खराब रह्यो। NEA को बिजुली बिल तिर्नु छ। उसँग बिल वा तरकारी किन्नको लागि मात्र पैसा छ। उसले के गर्छे?",
        "options_en": {
            "A": "Pay the electricity bill first — obligations come first",
            "B": "Restock vegetables — without stock there is no income",
            "C": "Pay half the electricity bill and use rest for stock",
            "D": "Borrow from a neighbor to pay the bill, restock with savings",
        },
        "options_ne": {
            "A": "पहिले बिजुली बिल तिर्ने — दायित्व पहिले आउँछ",
            "B": "तरकारी किन्ने — माल नभई आम्दानी हुँदैन",
            "C": "आधा बिजुली बिल तिरेर बाँकीले माल किन्ने",
            "D": "छिमेकीसँग सापट लिएर बिल तिर्ने, बचतले माल किन्ने",
        },
        "scoring": {"A": 90, "B": 30, "C": 50, "D": 80},
    },
    {
        "id": "q3",
        "trait": "social_trust",
        "question_en": "A new merchant moves next to your shop and asks to borrow NPR 2,000 for one week. You know nothing about them. What do you do?",
        "question_ne": "एक नयाँ व्यापारी तपाईंको छेउमा पसल खोल्छ र एक हप्ताको लागि रु. २,००० सापट माग्छ। तपाईंलाई उनीबारे केही थाहा छैन। तपाईं के गर्नुहुन्छ?",
        "options_en": {
            "A": "Lend the full amount — community helps community",
            "B": "Lend half and see if they repay before lending more",
            "C": "Politely decline — you don't know them yet",
            "D": "Ask a mutual acquaintance to vouch for them first",
        },
        "options_ne": {
            "A": "पूरै पैसा दिने — समुदायले एकअर्कालाई सहयोग गर्छ",
            "B": "आधा दिने र फिर्ता गरेपछि मात्र थप दिने",
            "C": "विनम्रतापूर्वक मना गर्ने — अझै चिनजान छैन",
            "D": "पहिले साझा परिचित मार्फत ग्यारेन्टी लिने",
        },
        "scoring": {"A": 60, "B": 70, "C": 50, "D": 90},
    },
    {
        "id": "q4",
        "trait": "resilience",
        "question_en": "Your main supplier suddenly increases prices by 20% due to fuel costs. Your margins will drop significantly. What is your first action?",
        "question_ne": "ईन्धन मूल्य बढेकाले तपाईंको मुख्य आपूर्तिकर्ताले एक्कासि २०% मूल्य बढाए। तपाईंको नाफा धेरै घट्नेछ। तपाईंको पहिलो कदम के हो?",
        "options_en": {
            "A": "Absorb the cost for now and hope prices drop",
            "B": "Immediately find an alternative supplier",
            "C": "Gradually increase your own prices while finding alternatives",
            "D": "Talk to other merchants and negotiate collectively with the supplier",
        },
        "options_ne": {
            "A": "अहिलेलाई घाटा खेप्ने र मूल्य घट्ने आशा गर्ने",
            "B": "तुरुन्त अर्को आपूर्तिकर्ता खोज्ने",
            "C": "विकल्प खोज्दै बिस्तारै आफ्नो मूल्य पनि बढाउने",
            "D": "अरू व्यापारीसँग मिलेर आपूर्तिकर्तासँग सामूहिक वार्ता गर्ने",
        },
        "scoring": {"A": 30, "B": 60, "C": 70, "D": 90},
    },
    {
        "id": "q5",
        "trait": "planning",
        "question_en": "You earn well during Dashain/Tihar festival season. What do you do with the extra income?",
        "question_ne": "दशैं/तिहारको समयमा तपाईंको आम्दानी राम्रो हुन्छ। थप आम्दानीले तपाईं के गर्नुहुन्छ?",
        "options_en": {
            "A": "Spend it — the family deserves a good festival",
            "B": "Save all of it for slow months",
            "C": "Reinvest most in stock, save some for emergencies",
            "D": "Pay off any debts first, then save the rest",
        },
        "options_ne": {
            "A": "खर्च गर्ने — परिवारले राम्रो चाड मनाउन पाउनुपर्छ",
            "B": "सबै बचत गर्ने — सुस्त महिनाको लागि",
            "C": "धेरैजसो मालमा लगाउने, केही आपत्कालीनको लागि राख्ने",
            "D": "पहिले ऋण तिर्ने, बाँकी बचत गर्ने",
        },
        "scoring": {"A": 20, "B": 60, "C": 80, "D": 90},
    },
]

# ─────────────────────────────────────────────
# VALID ENUMS
# ─────────────────────────────────────────────

VALID_PERSONALITIES = {
    "Cautious Planner",
    "Community Builder",
    "Risk Taker",
    "Resilient Adapter",
    "Conservative Saver",
}

PERSONALITIES_NE = {
    "Cautious Planner": "सावधान योजनाकार",
    "Community Builder": "सामुदायिक निर्माता",
    "Risk Taker": "जोखिम लिने",
    "Resilient Adapter": "लचिलो अनुकूलक",
    "Conservative Saver": "रूढिवादी बचतकर्ता",
}

# ─────────────────────────────────────────────
# GAMIFICATION
# ─────────────────────────────────────────────

BADGES = [
    {
        "id": "first_step",
        "icon": "🌱",
        "name_en": "First Step",
        "name_ne": "पहिलो कदम",
        "desc_en": "Completed your first psychometric assessment",
        "desc_ne": "पहिलो मनोवैज्ञानिक मूल्याङ्कन पूरा गर्नुभयो",
        "xp": 50,
        "check": lambda r: r.get("psychometric_score", 0) > 0,
    },
    {
        "id": "trusted_neighbor",
        "icon": "🤝",
        "name_en": "Trusted Neighbor",
        "name_ne": "विश्वसनीय छिमेकी",
        "desc_en": "High social trust — community believes in you",
        "desc_ne": "उच्च सामाजिक विश्वास — समुदाय तपाईंमाथि विश्वास गर्छ",
        "xp": 30,
        "check": lambda r: r.get("trait_scores", {}).get("social_trust", 0) >= 75,
    },
    {
        "id": "dashain_planner",
        "icon": "🪔",
        "name_en": "Dashain Planner",
        "name_ne": "दशैं योजनाकार",
        "desc_en": "Excellent festival-season financial planning",
        "desc_ne": "चाडबाडमा उत्कृष्ट वित्तीय योजना",
        "xp": 25,
        "check": lambda r: r.get("trait_scores", {}).get("planning", 0) >= 80,
    },
    {
        "id": "iron_merchant",
        "icon": "⚡",
        "name_en": "Iron Merchant",
        "name_ne": "फलाम व्यापारी",
        "desc_en": "Top resilience — you bounce back from anything",
        "desc_ne": "उच्च लचिलोपन — तपाईं जुनसुकै बाधाबाट उठ्न सक्नुहुन्छ",
        "xp": 25,
        "check": lambda r: r.get("trait_scores", {}).get("resilience", 0) >= 80,
    },
    {
        "id": "credit_ready",
        "icon": "🏆",
        "name_en": "Credit Ready",
        "name_ne": "ऋण तयार",
        "desc_en": "Psychometric score above 75 — strong credit personality",
        "desc_ne": "मनोवैज्ञानिक स्कोर ७५ भन्दा बढी — बलियो ऋण व्यक्तित्व",
        "xp": 40,
        "check": lambda r: r.get("psychometric_score", 0) >= 75,
    },
    {
        "id": "no_red_flags",
        "icon": "✅",
        "name_en": "Clean Record",
        "name_ne": "सफा रेकर्ड",
        "desc_en": "No behavioral red flags detected",
        "desc_ne": "कुनै व्यवहारगत समस्या फेला परेन",
        "xp": 20,
        "check": lambda r: r.get("red_flags", "").lower() in ["none", "कुनै छैन", ""],
    },
]


def compute_gamification(result: Dict) -> Dict:
    total_xp = 0
    earned = []
    for badge in BADGES:
        try:
            if badge["check"](result):
                total_xp += badge["xp"]
                earned.append(
                    {
                        "id": badge["id"],
                        "icon": badge["icon"],
                        "name_en": badge["name_en"],
                        "name_ne": badge["name_ne"],
                        "desc_en": badge["desc_en"],
                        "desc_ne": badge["desc_ne"],
                        "xp": badge["xp"],
                    }
                )
        except Exception:
            pass
    return {"xp_earned": total_xp, "badges_unlocked": earned}


# ─────────────────────────────────────────────
# HALLUCINATION GUARD  (3 stages)
# ─────────────────────────────────────────────


def _validate_llm_output(raw: Dict, deterministic: Dict) -> Dict:
    """
    Stage 1 — Schema enforcement: wrong types → replaced with deterministic value
    Stage 2 — ±25 cross-check: LLM deviates too far → averaged with deterministic
    Stage 3 — Enum lock: invalid credit_personality → mapped from dominant trait
    """
    out = dict(raw)
    corrections = []
    INT_FIELDS = [
        "conscientiousness",
        "risk_aversion",
        "social_trust",
        "resilience",
        "planning",
        "psychometric_score",
    ]
    STR_FIELDS = ["credit_personality", "insight", "red_flags", "strengths"]

    # Stage 1: type + range
    for f in INT_FIELDS:
        try:
            v = int(float(str(out.get(f, deterministic.get(f, 50)))))
            out[f] = max(0, min(100, v))
        except Exception:
            out[f] = deterministic.get(f, 50)
            corrections.append(f"[S1] {f} unparseable → used deterministic {out[f]}")

    for f in STR_FIELDS:
        if f not in out or not isinstance(out[f], str) or not out[f].strip():
            out[f] = "none" if f == "red_flags" else ""
            corrections.append(f"[S1] {f} missing/invalid → set default")

    # Stage 2: ±25 cross-check on trait scores
    TOLERANCE = 25
    for trait in [
        "conscientiousness",
        "risk_aversion",
        "social_trust",
        "resilience",
        "planning",
    ]:
        llm_v = out.get(trait, 50)
        det_v = deterministic.get(trait, 50)
        if abs(llm_v - det_v) > TOLERANCE:
            avg = round((llm_v + det_v) / 2)
            corrections.append(f"[S2] {trait}: LLM={llm_v} det={det_v} → avg={avg}")
            out[trait] = avg

    # Re-derive psychometric_score from corrected traits
    recomputed = round(
        out["conscientiousness"] * 0.30
        + out["risk_aversion"] * 0.25
        + out["social_trust"] * 0.20
        + out["resilience"] * 0.15
        + out["planning"] * 0.10
    )
    if abs(out.get("psychometric_score", 50) - recomputed) > 15:
        corrections.append(
            f"[S2] psychometric_score {out['psychometric_score']} → {recomputed}"
        )
        out["psychometric_score"] = recomputed

    # Stage 3: enum lock
    if out.get("credit_personality") not in VALID_PERSONALITIES:
        dominant = max(
            {
                t: out.get(t, 50)
                for t in [
                    "conscientiousness",
                    "risk_aversion",
                    "social_trust",
                    "resilience",
                    "planning",
                ]
            },
            key=lambda k: out.get(k, 50),
        )
        fallback = {
            "conscientiousness": "Cautious Planner",
            "risk_aversion": "Conservative Saver",
            "social_trust": "Community Builder",
            "resilience": "Resilient Adapter",
            "planning": "Cautious Planner",
        }
        old = out.get("credit_personality", "")
        out["credit_personality"] = fallback.get(dominant, "Cautious Planner")
        corrections.append(f"[S3] '{old}' invalid → {out['credit_personality']}")

    if corrections:
        out["_hallucination_corrections"] = corrections
    return out


# ─────────────────────────────────────────────
# PUBLIC HELPERS
# ─────────────────────────────────────────────


def get_questions(lang: str = "ne") -> List[Dict]:
    out = []
    for q in PSYCHOMETRIC_QUESTIONS:
        if lang == "ne":
            out.append(
                {
                    "id": q["id"],
                    "trait": q["trait"],
                    "question": q["question_ne"],
                    "options": q["options_ne"],
                    "question_en": q["question_en"],
                    "options_en": q["options_en"],
                }
            )
        else:
            out.append(
                {
                    "id": q["id"],
                    "trait": q["trait"],
                    "question": q["question_en"],
                    "options": q["options_en"],
                }
            )
    return out


def score_responses_deterministic(responses: Dict[str, str]) -> Dict:
    scores = {
        "risk_aversion": 0,
        "conscientiousness": 0,
        "social_trust": 0,
        "resilience": 0,
        "planning": 0,
    }
    counts = {k: 0 for k in scores}
    for q in PSYCHOMETRIC_QUESTIONS:
        ans = responses.get(q["id"])
        if ans and ans in q["scoring"]:
            scores[q["trait"]] += q["scoring"][ans]
            counts[q["trait"]] += 1
    for t in scores:
        if counts[t] > 0:
            scores[t] = round(scores[t] / counts[t])
    return scores


def _analyze_with_gemini(
    merchant_name: str, responses: Dict[str, str], deterministic: Dict
) -> Dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback(deterministic, "No GEMINI_API_KEY")

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        )

        summary = []
        for q in PSYCHOMETRIC_QUESTIONS:
            ans = responses.get(q["id"], "?")
            summary.append(
                f"  [{q['trait']}] {q['question_en'][:80]}... → {ans}: {q['options_en'].get(ans, '?')}"
            )

        # Anti-hallucination prompt: give baseline, lock deviation, demand strict JSON
        prompt = f"""You are a micro-credit psychometric analyst for Nepal's informal economy.

MERCHANT: {merchant_name}
RESPONSES:
{chr(10).join(summary)}

DETERMINISTIC BASELINE (answer-key scores, 0-100):
{json.dumps(deterministic, indent=2)}

RULES — output will be machine-validated:
1. Return ONLY valid JSON. No markdown, no preamble.
2. Trait scores MUST stay within ±20 of the baseline above.
3. psychometric_score = round(conscientiousness*0.30 + risk_aversion*0.25 + social_trust*0.20 + resilience*0.15 + planning*0.10)
4. credit_personality MUST be exactly one of:
   Cautious Planner | Community Builder | Risk Taker | Resilient Adapter | Conservative Saver
5. insight: 1 sentence, max 20 words, Nepal-specific context.
6. red_flags: "none" if no concerns.

JSON:
{{
  "conscientiousness": <int>,
  "risk_aversion": <int>,
  "social_trust": <int>,
  "resilience": <int>,
  "planning": <int>,
  "psychometric_score": <int>,
  "credit_personality": "<value>",
  "insight": "<text>",
  "red_flags": "<text or none>",
  "strengths": "<text>"
}}"""

        resp = model.generate_content(prompt)
        raw = re.sub(r"```(?:json)?", "", resp.text.strip()).strip().rstrip("`")
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise ValueError("No JSON in response")
        parsed = json.loads(m.group())
        return _validate_llm_output(parsed, deterministic)

    except json.JSONDecodeError as e:
        return _fallback(deterministic, f"JSON error: {e}")
    except Exception as e:
        return _fallback(deterministic, str(e))


def _fallback(deterministic: Dict, error: str) -> Dict:
    w = round(
        deterministic.get("conscientiousness", 50) * 0.30
        + deterministic.get("risk_aversion", 50) * 0.25
        + deterministic.get("social_trust", 50) * 0.20
        + deterministic.get("resilience", 50) * 0.15
        + deterministic.get("planning", 50) * 0.10
    )
    dominant = max(deterministic, key=lambda k: deterministic.get(k, 0))
    pm = {
        "conscientiousness": "Cautious Planner",
        "risk_aversion": "Conservative Saver",
        "social_trust": "Community Builder",
        "resilience": "Resilient Adapter",
        "planning": "Cautious Planner",
    }
    return {
        **deterministic,
        "psychometric_score": w,
        "credit_personality": pm.get(dominant, "Cautious Planner"),
        "insight": "Deterministic profile — Gemini unavailable.",
        "red_flags": "none",
        "strengths": "Consistent responses.",
        "_fallback": True,
        "_error": error,
    }


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────


def run_psychometric_assessment(
    merchant_id: str, merchant_name: str, responses: Dict[str, str], lang: str = "ne"
) -> Dict:
    deterministic = score_responses_deterministic(responses)
    gemini = _analyze_with_gemini(merchant_name, responses, deterministic)

    traits = {
        t: gemini.get(t, deterministic[t])
        for t in [
            "conscientiousness",
            "risk_aversion",
            "social_trust",
            "resilience",
            "planning",
        ]
    }

    result = {
        "merchant_id": merchant_id,
        "trait_scores": traits,
        "psychometric_score": gemini.get("psychometric_score", 50),
        "credit_personality": gemini.get("credit_personality", "Cautious Planner"),
        "credit_personality_ne": PERSONALITIES_NE.get(
            gemini.get("credit_personality", ""), ""
        ),
        "insight": gemini.get("insight", ""),
        "red_flags": gemini.get("red_flags", "none"),
        "strengths": gemini.get("strengths", ""),
        "used_fallback": gemini.get("_fallback", False),
        "hallucination_corrections": gemini.get("_hallucination_corrections", []),
        "deterministic_baseline": deterministic,
    }

    gami = compute_gamification(result)
    result["xp_earned"] = gami["xp_earned"]
    result["badges_unlocked"] = gami["badges_unlocked"]
    return result
