"""
psychometric.py — TrustBridge
- 30 questions across 5 traits (6 per trait)
- 5 randomly sampled per merchant per session (1 per trait)
- No merchant names in questions — uses he/she/they
- Hallucination guard: 3-stage validation
- Bilingual: Nepali default + English
- Gamification: XP + badges
"""

import os
import json
import re
import random
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# QUESTION BANK — 30 questions, 6 per trait
# No names used — he/she/they only
# ─────────────────────────────────────────────

QUESTION_BANK = [
    # ── RISK_AVERSION (6) ──────────────────────────────────────────
    {
        "id": "ra1",
        "trait": "risk_aversion",
        "question_en": "A supplier offers double stock at half price, but full payment is due in 3 days. He/she only has 60% of the money. What should he/she do?",
        "question_ne": "एक आपूर्तिकर्ताले आधा मूल्यमा दोब्बर माल दिन्छ, तर ३ दिनभित्र पूरै भुक्तानी गर्नुपर्छ। उसँग ६०% पैसा मात्र छ। उसले के गर्नुपर्छ?",
        "options_en": {
            "A": "Take the full deal and borrow the rest immediately",
            "B": "Take only what he/she can afford right now",
            "C": "Wait until next month when full payment is ready",
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
        "id": "ra2",
        "trait": "risk_aversion",
        "question_en": "A merchant hears that a new product is selling well in another district. He/she would need to invest NPR 30,000 with no guarantee. What does he/she do?",
        "question_ne": "एक व्यापारीले सुन्छ कि अर्को जिल्लामा नयाँ उत्पादन राम्रो बिक्री भइरहेको छ। उसले NPR ३०,००० लगानी गर्नुपर्छ, कुनै ग्यारेन्टी छैन। उसले के गर्छ?",
        "options_en": {
            "A": "Invest the full amount — opportunity doesn't wait",
            "B": "Send a small test order first to check demand",
            "C": "Wait and watch how others do before investing",
            "D": "Ask another merchant to co-invest and share risk",
        },
        "options_ne": {
            "A": "पूरै लगानी गर्ने — अवसर पर्खँदैन",
            "B": "पहिले सानो अर्डर पठाएर माग जाँच्ने",
            "C": "अरूले कसरी गर्छन् हेरेर मात्र लगानी गर्ने",
            "D": "अर्को व्यापारीसँग मिलेर जोखिम बाँड्ने",
        },
        "scoring": {"A": 15, "B": 75, "C": 60, "D": 80},
    },
    {
        "id": "ra3",
        "trait": "risk_aversion",
        "question_en": "He/she has saved NPR 50,000 over 6 months. A relative offers a business opportunity promising 40% returns in 2 months. What does he/she do?",
        "question_ne": "उसले ६ महिनामा NPR ५०,००० बचत गरेको छ। एक आफन्तले २ महिनामा ४०% नाफा दिने व्यापारिक अवसर दिन्छ। उसले के गर्छ?",
        "options_en": {
            "A": "Invest all of it — family can be trusted",
            "B": "Invest half and keep half as backup",
            "C": "Politely decline — too good to be true",
            "D": "Ask for written documentation before investing anything",
        },
        "options_ne": {
            "A": "सबै लगानी गर्ने — परिवारलाई विश्वास गर्न सकिन्छ",
            "B": "आधा लगाउने, आधा बचत राख्ने",
            "C": "विनम्रतापूर्वक अस्वीकार गर्ने — धेरै राम्रो लाग्छ",
            "D": "लगानी अघि लिखित कागजात माग्ने",
        },
        "scoring": {"A": 20, "B": 55, "C": 70, "D": 90},
    },
    {
        "id": "ra4",
        "trait": "risk_aversion",
        "question_en": "His/her shop lease is expiring. He/she can renew at higher rent or move to a cheaper but less busy location. What does he/she choose?",
        "question_ne": "उसको पसलको भाडा सम्झौता सकिँदैछ। उसले महँगो तर व्यस्त ठाउँमा नवीकरण गर्न सक्छ वा सस्तो तर कम भिड भएको ठाउँमा सर्न सक्छ। उसले के छान्छ?",
        "options_en": {
            "A": "Renew at current location — established customer base is worth it",
            "B": "Move to the cheaper location and market aggressively",
            "C": "Negotiate the current rent down before deciding",
            "D": "Temporarily close and reassess in 3 months",
        },
        "options_ne": {
            "A": "अहिलेकै ठाउँमा नवीकरण गर्ने — स्थापित ग्राहक आधार मूल्यवान छ",
            "B": "सस्तो ठाउँमा सर्ने र जोडतोड मार्केटिङ गर्ने",
            "C": "निर्णय गर्नु अघि हालको भाडा घटाउन वार्ता गर्ने",
            "D": "अस्थायी रूपमा बन्द गरेर ३ महिनापछि पुनर्विचार गर्ने",
        },
        "scoring": {"A": 70, "B": 50, "C": 85, "D": 20},
    },
    {
        "id": "ra5",
        "trait": "risk_aversion",
        "question_en": "He/she hears that a popular item will face a price hike next week. He/she can buy extra stock now but it will tie up most of his/her cash. What does he/she do?",
        "question_ne": "उसले सुन्छ कि अर्को हप्ता एक लोकप्रिय वस्तुको मूल्य बढ्छ। उसले अहिले नै अतिरिक्त स्टक किन्न सक्छ तर यसले उसको अधिकांश नगद बाँधिन्छ। उसले के गर्छ?",
        "options_en": {
            "A": "Buy maximum stock — the savings will be significant",
            "B": "Buy moderate extra stock, keep some cash free",
            "C": "Buy nothing extra — cash flow is more important",
            "D": "Pool resources with neighboring merchants to bulk buy",
        },
        "options_ne": {
            "A": "अधिकतम स्टक किन्ने — बचत उल्लेखनीय हुनेछ",
            "B": "मध्यम अतिरिक्त स्टक किन्ने, केही नगद मुक्त राख्ने",
            "C": "कुनै अतिरिक्त नकिन्ने — नगद प्रवाह बढी महत्त्वपूर्ण छ",
            "D": "थोक खरिदको लागि छिमेकी व्यापारीहरूसँग स्रोत जोड्ने",
        },
        "scoring": {"A": 25, "B": 80, "C": 65, "D": 85},
    },
    {
        "id": "ra6",
        "trait": "risk_aversion",
        "question_en": "His/her business has been stable for 2 years. A bank offers a loan at 18% interest to expand. He/she does not urgently need it. What does he/she do?",
        "question_ne": "उसको व्यवसाय २ वर्षदेखि स्थिर छ। एक बैंकले विस्तारको लागि १८% ब्याजमा ऋण दिन्छ। उसलाई यो तत्काल चाहिएको छैन। उसले के गर्छ?",
        "options_en": {
            "A": "Take the loan and expand aggressively now",
            "B": "Take a smaller amount than offered as a buffer",
            "C": "Decline and continue growing organically",
            "D": "Wait 6 months and re-evaluate if expansion still makes sense",
        },
        "options_ne": {
            "A": "ऋण लिएर अहिले नै आक्रामक रूपमा विस्तार गर्ने",
            "B": "प्रस्तावित भन्दा सानो रकम लिने",
            "C": "अस्वीकार गरेर जैविक रूपमा बढ्न जारी राख्ने",
            "D": "६ महिना पर्खेर विस्तार अझै उचित छ कि छैन पुनर्मूल्याङ्कन गर्ने",
        },
        "scoring": {"A": 30, "B": 65, "C": 75, "D": 85},
    },
    # ── CONSCIENTIOUSNESS (6) ──────────────────────────────────────
    {
        "id": "co1",
        "trait": "conscientiousness",
        "question_en": "His/her business had a bad month due to flooding. The electricity bill is due. He/she has just enough for either the bill or restocking. What does he/she do?",
        "question_ne": "बाढीका कारण उसको व्यवसाय यो महिना खराब रह्यो। बिजुली बिल तिर्नु छ। उसँग बिल वा माल किन्नको लागि मात्र पैसा छ। उसले के गर्छ?",
        "options_en": {
            "A": "Pay the electricity bill first — obligations come first",
            "B": "Restock — without stock there is no income",
            "C": "Pay half the bill and use rest for stock",
            "D": "Borrow to pay the bill, restock with savings",
        },
        "options_ne": {
            "A": "पहिले बिजुली बिल तिर्ने — दायित्व पहिले आउँछ",
            "B": "माल किन्ने — माल नभई आम्दानी हुँदैन",
            "C": "आधा बिल तिरेर बाँकीले माल किन्ने",
            "D": "सापट लिएर बिल तिर्ने, बचतले माल किन्ने",
        },
        "scoring": {"A": 90, "B": 30, "C": 50, "D": 80},
    },
    {
        "id": "co2",
        "trait": "conscientiousness",
        "question_en": "He/she owes a supplier NPR 15,000 due tomorrow. A good customer offers to pay an outstanding debt of NPR 20,000 next week instead. What does he/she do?",
        "question_ne": "उसले भोलि NPR १५,००० आपूर्तिकर्तालाई तिर्नुपर्छ। एक राम्रो ग्राहकले बक्यौता NPR २०,००० अर्को हप्ता तिर्ने प्रस्ताव गर्छ। उसले के गर्छ?",
        "options_en": {
            "A": "Pay the supplier from other savings — commitments must be kept",
            "B": "Ask the supplier for a one-week extension",
            "C": "Delay both — wait for the customer to pay first",
            "D": "Pay the supplier partially and explain the situation",
        },
        "options_ne": {
            "A": "अन्य बचतबाट आपूर्तिकर्तालाई तिर्ने — वाचा पालन गर्नुपर्छ",
            "B": "आपूर्तिकर्तासँग एक हप्ताको म्याद माग्ने",
            "C": "दुवै ढिलाइ गर्ने — ग्राहकले तिरेपछि मात्र",
            "D": "आपूर्तिकर्तालाई आंशिक तिर्ने र अवस्था बताउने",
        },
        "scoring": {"A": 95, "B": 75, "C": 20, "D": 65},
    },
    {
        "id": "co3",
        "trait": "conscientiousness",
        "question_en": "He/she discovered he/she accidentally overcharged a regular customer NPR 500 last week. The customer hasn't noticed. What does he/she do?",
        "question_ne": "उसले गत हप्ता एक नियमित ग्राहकलाई गल्तीले NPR ५०० बढी लिएको पत्ता लगाउँछ। ग्राहकले थाहा पाएको छैन। उसले के गर्छ?",
        "options_en": {
            "A": "Proactively refund the NPR 500 on the next visit",
            "B": "Wait — if the customer notices, refund then",
            "C": "Keep it — these small errors balance out over time",
            "D": "Offer a discount on their next purchase instead",
        },
        "options_ne": {
            "A": "अर्को भ्रमणमा सक्रिय रूपमा NPR ५०० फिर्ता गर्ने",
            "B": "पर्खने — ग्राहकले थाहा पाए फिर्ता गर्ने",
            "C": "राख्ने — यी सानातिना त्रुटिहरू समयसँगै सन्तुलित हुन्छन्",
            "D": "अर्को खरिदमा छूट दिने",
        },
        "scoring": {"A": 95, "B": 50, "C": 10, "D": 70},
    },
    {
        "id": "co4",
        "trait": "conscientiousness",
        "question_en": "He/she keeps financial records on paper. An accountant suggests switching to a mobile app. What is his/her reaction?",
        "question_ne": "उसले कागजमा वित्तीय रेकर्ड राख्छ। एक लेखापालले मोबाइल एपमा स्विच गर्न सुझाव दिन्छ। उसको प्रतिक्रिया के हो?",
        "options_en": {
            "A": "Switch immediately — digital is always better",
            "B": "Try the app for one month alongside paper records",
            "C": "Stick with paper — it works and there's no need to change",
            "D": "Ask other merchants about their experience first",
        },
        "options_ne": {
            "A": "तुरुन्त स्विच गर्ने — डिजिटल सधैं राम्रो हुन्छ",
            "B": "एक महिना कागजी रेकर्डसँगै एप प्रयास गर्ने",
            "C": "कागजमै रहने — यो काम गर्छ, परिवर्तन आवश्यक छैन",
            "D": "पहिले अरू व्यापारीको अनुभव सोध्ने",
        },
        "scoring": {"A": 55, "B": 90, "C": 30, "D": 75},
    },
    {
        "id": "co5",
        "trait": "conscientiousness",
        "question_en": "His/her employee made a costly mistake that lost NPR 8,000 in stock. It was the employee's first mistake in 2 years. What does he/she do?",
        "question_ne": "उसको कर्मचारीले गल्ती गरेर NPR ८,००० को स्टक नोक्सान गर्यो। यो २ वर्षमा पहिलो गल्ती थियो। उसले के गर्छ?",
        "options_en": {
            "A": "Deduct the loss from the employee's salary",
            "B": "Have a clear discussion and set better processes",
            "C": "Fire the employee — a costly mistake is unacceptable",
            "D": "Absorb the loss and say nothing — mistakes happen",
        },
        "options_ne": {
            "A": "कर्मचारीको तलबबाट नोक्सान काट्ने",
            "B": "स्पष्ट छलफल गरी राम्रो प्रक्रिया बनाउने",
            "C": "बर्खास्त गर्ने — महँगो गल्ती अस्वीकार्य छ",
            "D": "नोक्सान आफैं बेहोर्ने र केही नभन्ने — गल्ती हुन्छ",
        },
        "scoring": {"A": 40, "B": 90, "C": 20, "D": 50},
    },
    {
        "id": "co6",
        "trait": "conscientiousness",
        "question_en": "He/she has been offered a government contract but it requires certified accounts for the past 2 years, which he/she hasn't maintained. What does he/she do?",
        "question_ne": "उसलाई सरकारी ठेक्का प्रस्ताव भएको छ तर पछिल्लो २ वर्षको प्रमाणित लेखाजोखा चाहिन्छ, जुन उसले राखेको छैन। उसले के गर्छ?",
        "options_en": {
            "A": "Reconstruct the records as best as possible and submit",
            "B": "Decline this contract and start proper records for the future",
            "C": "Ask an accountant to help fix the records",
            "D": "Apply anyway and explain the situation honestly",
        },
        "options_ne": {
            "A": "सकेसम्म राम्रोसँग रेकर्ड पुनर्निर्माण गरी पेश गर्ने",
            "B": "यो ठेक्का अस्वीकार गरी भविष्यमा राम्रो रेकर्ड राख्न थाल्ने",
            "C": "रेकर्ड मिलाउन लेखापालको मद्दत माग्ने",
            "D": "जे भए पनि आवेदन दिने र इमानदारीपूर्वक अवस्था बताउने",
        },
        "scoring": {"A": 35, "B": 80, "C": 60, "D": 85},
    },
    # ── SOCIAL_TRUST (6) ───────────────────────────────────────────
    {
        "id": "st1",
        "trait": "social_trust",
        "question_en": "A new merchant moves next door and asks to borrow NPR 2,000 for one week. Nothing is known about them. What does he/she do?",
        "question_ne": "एक नयाँ व्यापारी छेउमा पसल खोल्छ र एक हप्ताको लागि NPR २,००० सापट माग्छ। उनीबारे केही थाहा छैन। उसले के गर्छ?",
        "options_en": {
            "A": "Lend the full amount — community helps community",
            "B": "Lend half and see if they repay before lending more",
            "C": "Politely decline — not enough trust yet",
            "D": "Ask a mutual acquaintance to vouch for them first",
        },
        "options_ne": {
            "A": "पूरै पैसा दिने — समुदायले एकअर्कालाई सहयोग गर्छ",
            "B": "आधा दिने र फिर्ता गरेपछि मात्र थप दिने",
            "C": "विनम्रतापूर्वक मना गर्ने — अझै पर्याप्त विश्वास छैन",
            "D": "पहिले साझा परिचित मार्फत ग्यारेन्टी लिने",
        },
        "scoring": {"A": 60, "B": 70, "C": 50, "D": 90},
    },
    {
        "id": "st2",
        "trait": "social_trust",
        "question_en": "He/she wants to expand. A fellow merchant offers to co-invest equally and share profits. They have been neighbors for 1 year but never did business together. What does he/she do?",
        "question_ne": "उसले विस्तार गर्न चाहन्छ। एक साथी व्यापारीले समान लगानी गरी नाफा बाँड्न प्रस्ताव गर्छ। तिनीहरू १ वर्षदेखि छिमेकी छन् तर सँगै व्यवसाय गरेका छैनन्। उसले के गर्छ?",
        "options_en": {
            "A": "Accept immediately — they seem reliable",
            "B": "Accept but insist on a written agreement first",
            "C": "Start with a small joint project to test the partnership",
            "D": "Decline and expand alone — partnerships are complicated",
        },
        "options_ne": {
            "A": "तुरुन्त स्वीकार गर्ने — भरपर्दो देखिन्छ",
            "B": "स्वीकार गर्ने तर पहिले लिखित सम्झौता माग्ने",
            "C": "सानो संयुक्त परियोजनाबाट साझेदारी परीक्षण गर्ने",
            "D": "अस्वीकार गरेर एक्लै विस्तार गर्ने — साझेदारी जटिल हुन्छ",
        },
        "scoring": {"A": 50, "B": 85, "C": 90, "D": 30},
    },
    {
        "id": "st3",
        "trait": "social_trust",
        "question_en": "He/she sees a competitor's customer complaining loudly that they were sold expired goods. What does he/she do?",
        "question_ne": "उसले देख्छ कि एक प्रतिस्पर्धीको ग्राहक म्याद सकिएको सामान बेचेको भनेर जोरले गुनासो गर्दैछ। उसले के गर्छ?",
        "options_en": {
            "A": "Stay out of it — not his/her business",
            "B": "Quietly tell the customer they can check his/her shop for fresh stock",
            "C": "Intervene and help the customer confront the competitor",
            "D": "Report the competitor to the local market committee",
        },
        "options_ne": {
            "A": "टाढै रहने — आफ्नो काम होइन",
            "B": "ग्राहकलाई चुपचाप आफ्नो पसलमा ताजा माल हेर्न भन्ने",
            "C": "हस्तक्षेप गरेर ग्राहकलाई प्रतिस्पर्धीसँग सामना गर्न मद्दत गर्ने",
            "D": "स्थानीय बजार समितिमा प्रतिस्पर्धीको उजुरी गर्ने",
        },
        "scoring": {"A": 30, "B": 65, "C": 55, "D": 85},
    },
    {
        "id": "st4",
        "trait": "social_trust",
        "question_en": "A trusted supplier asks him/her to vouch for a new merchant he/she barely knows. The vouch could affect his/her own credit reputation. What does he/she do?",
        "question_ne": "एक विश्वसनीय आपूर्तिकर्ताले उसलाई एक नयाँ व्यापारीको लागि सिफारिस गर्न भन्छ जसलाई उसले कमै चिन्छ। सिफारिसले उसको आफ्नै ऋण प्रतिष्ठालाई असर गर्न सक्छ। उसले के गर्छ?",
        "options_en": {
            "A": "Vouch without hesitation — the supplier's trust is enough",
            "B": "Meet the new merchant first and then decide",
            "C": "Decline — not enough information to take that risk",
            "D": "Offer a limited vouch for a small amount only",
        },
        "options_ne": {
            "A": "नहिचकिचाई सिफारिस गर्ने — आपूर्तिकर्ताको विश्वास पर्याप्त छ",
            "B": "पहिले नयाँ व्यापारीलाई भेटेर निर्णय गर्ने",
            "C": "अस्वीकार गर्ने — त्यो जोखिम लिन पर्याप्त जानकारी छैन",
            "D": "सानो रकमको लागि मात्र सीमित सिफारिस दिने",
        },
        "scoring": {"A": 35, "B": 85, "C": 60, "D": 80},
    },
    {
        "id": "st5",
        "trait": "social_trust",
        "question_en": "He/she learns that a long-time customer has been sharing his/her pricing information with a competitor. How does he/she react?",
        "question_ne": "उसलाई थाहा हुन्छ कि एक पुरानो ग्राहकले उसको मूल्य निर्धारण जानकारी प्रतिस्पर्धीसँग साझा गर्दैछ। उसको प्रतिक्रिया के हो?",
        "options_en": {
            "A": "Confront the customer directly and end the relationship",
            "B": "Stop sharing sensitive information but keep serving them",
            "C": "Discuss it calmly and give them a chance to explain",
            "D": "Ignore it — in business, information flows freely",
        },
        "options_ne": {
            "A": "ग्राहकसँग सिधै भिड्ने र सम्बन्ध तोड्ने",
            "B": "संवेदनशील जानकारी साझा गर्न बन्द गर्ने तर सेवा जारी राख्ने",
            "C": "शान्तसँग छलफल गरी स्पष्टीकरण दिने मौका दिने",
            "D": "बेवास्ता गर्ने — व्यवसायमा जानकारी स्वतन्त्र रूपमा बग्छ",
        },
        "scoring": {"A": 45, "B": 70, "C": 90, "D": 20},
    },
    {
        "id": "st6",
        "trait": "social_trust",
        "question_en": "A merchants' association asks him/her to contribute NPR 1,000 monthly to a collective emergency fund. No individual guarantee of getting it back. What does he/she do?",
        "question_ne": "एक व्यापारी संघले उसलाई सामूहिक आपतकालीन कोषमा मासिक NPR १,००० योगदान गर्न भन्छ। फिर्ता पाउने व्यक्तिगत ग्यारेन्टी छैन। उसले के गर्छ?",
        "options_en": {
            "A": "Join immediately — collective security benefits everyone",
            "B": "Join but ask to see the fund's management rules first",
            "C": "Decline — no guarantee means too much risk",
            "D": "Contribute a smaller amount as a gesture of goodwill",
        },
        "options_ne": {
            "A": "तुरुन्त सामेल हुने — सामूहिक सुरक्षाले सबैलाई फाइदा हुन्छ",
            "B": "सामेल हुने तर पहिले कोषको व्यवस्थापन नियम हेर्ने",
            "C": "अस्वीकार गर्ने — ग्यारेन्टी नभएकाले धेरै जोखिम छ",
            "D": "सद्भावनाको संकेतको रूपमा सानो रकम योगदान गर्ने",
        },
        "scoring": {"A": 70, "B": 90, "C": 25, "D": 60},
    },
    # ── RESILIENCE (6) ─────────────────────────────────────────────
    {
        "id": "re1",
        "trait": "resilience",
        "question_en": "His/her main supplier suddenly increases prices by 20% due to fuel costs. Margins will drop significantly. What is his/her first action?",
        "question_ne": "ईन्धन मूल्य बढेकाले उसको मुख्य आपूर्तिकर्ताले एक्कासि २०% मूल्य बढाए। नाफा धेरै घट्नेछ। उसको पहिलो कदम के हो?",
        "options_en": {
            "A": "Absorb the cost and hope prices drop",
            "B": "Find an alternative supplier immediately",
            "C": "Gradually raise prices while finding alternatives",
            "D": "Negotiate collectively with other merchants",
        },
        "options_ne": {
            "A": "घाटा खेप्ने र मूल्य घट्ने आशा गर्ने",
            "B": "तुरुन्त अर्को आपूर्तिकर्ता खोज्ने",
            "C": "विकल्प खोज्दै बिस्तारै मूल्य बढाउने",
            "D": "अरू व्यापारीसँग मिलेर सामूहिक वार्ता गर्ने",
        },
        "scoring": {"A": 30, "B": 60, "C": 70, "D": 90},
    },
    {
        "id": "re2",
        "trait": "resilience",
        "question_en": "A highway blockade cuts off his/her supply chain for 2 weeks. Stock is running low. What does he/she do?",
        "question_ne": "राजमार्ग अवरोधले उसको आपूर्ति श्रृंखला २ हप्ताको लागि काट्छ। स्टक कम हुँदैछ। उसले के गर्छ?",
        "options_en": {
            "A": "Close temporarily until the blockade ends",
            "B": "Source locally at higher prices to stay open",
            "C": "Ration remaining stock and inform regular customers",
            "D": "Partner with other merchants to pool remaining supplies",
        },
        "options_ne": {
            "A": "अवरोध नसकिँदासम्म अस्थायी रूपमा बन्द गर्ने",
            "B": "खुला रहन उच्च मूल्यमा स्थानीय रूपमा सोर्स गर्ने",
            "C": "बाँकी स्टक राशन गर्ने र नियमित ग्राहकलाई जानकारी दिने",
            "D": "बाँकी आपूर्ति जोड्न अरू व्यापारीसँग साझेदारी गर्ने",
        },
        "scoring": {"A": 20, "B": 65, "C": 80, "D": 90},
    },
    {
        "id": "re3",
        "trait": "resilience",
        "question_en": "A new competitor opens nearby and starts undercutting prices by 15%. His/her sales drop 30% in the first month. What does he/she do?",
        "question_ne": "एक नयाँ प्रतिस्पर्धी नजिकै खुल्छ र मूल्य १५% घटाउँछ। पहिलो महिनामा बिक्री ३०% घट्छ। उसले के गर्छ?",
        "options_en": {
            "A": "Match or beat the competitor's prices immediately",
            "B": "Focus on service quality and loyal customer retention",
            "C": "Diversify product range to areas the competitor doesn't cover",
            "D": "Wait and see — new competitors often struggle early on",
        },
        "options_ne": {
            "A": "तुरुन्त प्रतिस्पर्धीको मूल्य बराबर वा कम गर्ने",
            "B": "सेवाको गुणस्तर र वफादार ग्राहक कायम राख्नमा ध्यान दिने",
            "C": "प्रतिस्पर्धीले नभएका क्षेत्रमा उत्पादन विविधीकरण गर्ने",
            "D": "पर्खने — नयाँ प्रतिस्पर्धी प्रायः सुरुमा संघर्ष गर्छन्",
        },
        "scoring": {"A": 35, "B": 80, "C": 90, "D": 50},
    },
    {
        "id": "re4",
        "trait": "resilience",
        "question_en": "His/her shop was damaged in a flood and will take 3 weeks to repair. He/she has some savings. What does he/she do?",
        "question_ne": "उसको पसल बाढीमा क्षतिग्रस्त भयो र मर्मत गर्न ३ हप्ता लाग्नेछ। उसँग केही बचत छ। उसले के गर्छ?",
        "options_en": {
            "A": "Wait for repairs and use savings to survive",
            "B": "Set up a temporary stall nearby to keep trading",
            "C": "Use the downtime to plan improvements for the reopening",
            "D": "Both B and C — keep trading and plan the upgrade",
        },
        "options_ne": {
            "A": "मर्मतको प्रतीक्षा गर्ने र बाँच्न बचत प्रयोग गर्ने",
            "B": "व्यापार जारी राख्न नजिकै अस्थायी स्टल राख्ने",
            "C": "पुनः उद्घाटनको लागि सुधार योजना बनाउन खाली समय प्रयोग गर्ने",
            "D": "B र C दुवै — व्यापार जारी राख्ने र स्तरवृद्धि योजना बनाउने",
        },
        "scoring": {"A": 30, "B": 70, "C": 65, "D": 95},
    },
    {
        "id": "re5",
        "trait": "resilience",
        "question_en": "He/she loses his/her biggest customer who accounted for 40% of monthly revenue. What is his/her immediate response?",
        "question_ne": "उसले मासिक राजस्वको ४०% योगदान गर्ने आफ्नो सबैभन्दा ठूलो ग्राहक गुमाउँछ। उसको तत्काल प्रतिक्रिया के हो?",
        "options_en": {
            "A": "Panic and try to win back the customer at any cost",
            "B": "Immediately start approaching 5 new potential customers",
            "C": "Cut costs first, then gradually rebuild the customer base",
            "D": "Analyse why the customer left and fix the root cause",
        },
        "options_ne": {
            "A": "घबराएर जुनसुकै मूल्यमा ग्राहक फिर्ता ल्याउने प्रयास गर्ने",
            "B": "तुरुन्त ५ नयाँ सम्भावित ग्राहकहरूलाई सम्पर्क गर्न थाल्ने",
            "C": "पहिले खर्च घटाउने, त्यसपछि बिस्तारै ग्राहक आधार पुनर्निर्माण गर्ने",
            "D": "ग्राहक किन गए विश्लेषण गरेर मूल कारण ठीक गर्ने",
        },
        "scoring": {"A": 20, "B": 70, "C": 65, "D": 90},
    },
    {
        "id": "re6",
        "trait": "resilience",
        "question_en": "He/she has failed at a business venture twice before. A new opportunity appears. What is his/her mindset?",
        "question_ne": "उसले पहिले दुई पटक व्यवसायमा असफल भएको छ। एक नयाँ अवसर देखिन्छ। उसको मानसिकता के हो?",
        "options_en": {
            "A": "Avoid it — failure pattern is a clear warning sign",
            "B": "Research carefully and only proceed with strong evidence",
            "C": "Try again — failure is the best teacher",
            "D": "Find a mentor who succeeded in the same area before starting",
        },
        "options_ne": {
            "A": "बच्ने — असफलताको ढाँचा स्पष्ट चेतावनी संकेत हो",
            "B": "सावधानीपूर्वक अनुसन्धान गरी बलियो प्रमाण भएमा मात्र अघि बढ्ने",
            "C": "फेरि प्रयास गर्ने — असफलता उत्कृष्ट शिक्षक हो",
            "D": "शुरू गर्नु अघि त्यही क्षेत्रमा सफल मेन्टर खोज्ने",
        },
        "scoring": {"A": 25, "B": 80, "C": 65, "D": 90},
    },
    # ── PLANNING (6) ───────────────────────────────────────────────
    {
        "id": "pl1",
        "trait": "planning",
        "question_en": "He/she earns well during Dashain/Tihar. What does he/she do with the extra income?",
        "question_ne": "दशैं/तिहारमा उसको आम्दानी राम्रो हुन्छ। थप आम्दानीले उसले के गर्छ?",
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
    {
        "id": "pl2",
        "trait": "planning",
        "question_en": "His/her business has no formal plan. A microfinance officer asks if he/she has a 1-year plan. What does he/she say?",
        "question_ne": "उसको व्यवसायमा कुनै औपचारिक योजना छैन। एक लघुवित्त अधिकारीले १ वर्षको योजना छ कि छैन सोध्छ। उसले के भन्छ?",
        "options_en": {
            "A": "Improvise an answer on the spot",
            "B": "Admit there is no formal plan but describe goals verbally",
            "C": "Say yes and then create one urgently before the next meeting",
            "D": "Ask the officer to help create a simple plan together",
        },
        "options_ne": {
            "A": "तत्काल जवाफ बनाएर बोल्ने",
            "B": "औपचारिक योजना नभएको स्वीकार गरी मौखिक रूपमा लक्ष्य बताउने",
            "C": "हो भन्ने र अर्को बैठकअघि तुरुन्त एउटा बनाउने",
            "D": "अधिकारीलाई सँगै सरल योजना बनाउन मद्दत माग्ने",
        },
        "scoring": {"A": 25, "B": 70, "C": 50, "D": 90},
    },
    {
        "id": "pl3",
        "trait": "planning",
        "question_en": "He/she knows the dry season will reduce income by 40% for 3 months. It is still 2 months away. What does he/she do now?",
        "question_ne": "उसलाई थाहा छ कि सुख्खा मौसमले ३ महिना आम्दानी ४०% घटाउनेछ। अझै २ महिना बाँकी छ। उसले अहिले के गर्छ?",
        "options_en": {
            "A": "Nothing — deal with it when it comes",
            "B": "Start saving aggressively from this month",
            "C": "Diversify into a product that sells well in dry season",
            "D": "Both B and C — save and diversify simultaneously",
        },
        "options_ne": {
            "A": "केही नगर्ने — आउँदा समाधान गर्ने",
            "B": "यही महिनाबाट आक्रामक रूपमा बचत थाल्ने",
            "C": "सुख्खा मौसममा राम्रो बिक्ने उत्पादनमा विविधीकरण गर्ने",
            "D": "B र C दुवै — एकसाथ बचत र विविधीकरण गर्ने",
        },
        "scoring": {"A": 10, "B": 70, "C": 75, "D": 95},
    },
    {
        "id": "pl4",
        "trait": "planning",
        "question_en": "He/she wants to hire a part-time helper but is not sure if income will support it. What does he/she do?",
        "question_ne": "उसले पार्ट-टाइम सहायक राख्न चाहन्छ तर आम्दानीले धान्छ कि धान्दैन भन्ने निश्चित छैन। उसले के गर्छ?",
        "options_en": {
            "A": "Hire immediately and adjust if income doesn't support it",
            "B": "Track income and expenses for 2 months before deciding",
            "C": "Hire only during the busy festival season as a trial",
            "D": "Ask the helper to work on a revenue-share basis first",
        },
        "options_ne": {
            "A": "तुरुन्त राख्ने र आम्दानीले नधानेमा समायोजन गर्ने",
            "B": "निर्णय गर्नु अघि २ महिना आय-खर्च ट्र्याक गर्ने",
            "C": "परीक्षणको रूपमा व्यस्त चाडबाड मौसममा मात्र राख्ने",
            "D": "पहिले राजस्व-साझेदारी आधारमा काम गराउने",
        },
        "scoring": {"A": 30, "B": 85, "C": 75, "D": 80},
    },
    {
        "id": "pl5",
        "trait": "planning",
        "question_en": "He/she has NPR 10,000 extra at year end. Which does he/she prioritize?",
        "question_ne": "वर्षको अन्तमा उसँग NPR १०,००० अतिरिक्त छ। उसले के प्राथमिकता दिन्छ?",
        "options_en": {
            "A": "Family celebration — they worked hard this year",
            "B": "Emergency fund — keep it untouched for crises",
            "C": "Invest in a small upgrade to the shop",
            "D": "Split: 50% emergency fund, 30% reinvest, 20% family",
        },
        "options_ne": {
            "A": "पारिवारिक उत्सव — यो वर्ष कडा परिश्रम गरे",
            "B": "आपतकालीन कोष — संकटको लागि नछुनू",
            "C": "पसलमा सानो स्तरवृद्धिमा लगानी गर्ने",
            "D": "विभाजन: ५०% आपतकालीन, ३०% पुनः लगानी, २०% परिवार",
        },
        "scoring": {"A": 20, "B": 70, "C": 65, "D": 95},
    },
    {
        "id": "pl6",
        "trait": "planning",
        "question_en": "He/she has been offered a stall at a seasonal fair 3 months away. It requires NPR 5,000 upfront today. What does he/she do?",
        "question_ne": "उसलाई ३ महिनापछि मौसमी मेलामा स्टल प्रस्ताव भएको छ। आज NPR ५,००० अग्रिम चाहिन्छ। उसले के गर्छ?",
        "options_en": {
            "A": "Pay immediately — fair spots sell out fast",
            "B": "Calculate expected profit first, then decide",
            "C": "Ask if payment can be split closer to the date",
            "D": "Decline — too uncertain that far in advance",
        },
        "options_ne": {
            "A": "तुरुन्त तिर्ने — मेलाका ठाउँ छिटो बिक्छन्",
            "B": "पहिले अपेक्षित नाफा गणना गरेर निर्णय गर्ने",
            "C": "मितिको नजिक भुक्तानी विभाजन गर्न सकिन्छ कि सोध्ने",
            "D": "अस्वीकार गर्ने — यति टाढाको कुरा धेरै अनिश्चित छ",
        },
        "scoring": {"A": 50, "B": 90, "C": 80, "D": 30},
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
# RANDOM SAMPLING — 1 question per trait
# ─────────────────────────────────────────────

TRAITS = [
    "risk_aversion",
    "conscientiousness",
    "social_trust",
    "resilience",
    "planning",
]


def sample_questions(seed: str = None) -> List[Dict]:
    """
    Returns 5 questions — one per trait — randomly sampled.
    Pass merchant_id as seed for reproducibility within a session.
    """
    rng = random.Random(seed)
    selected = []
    for trait in TRAITS:
        pool = [q for q in QUESTION_BANK if q["trait"] == trait]
        selected.append(rng.choice(pool))
    return selected


# ─────────────────────────────────────────────
# GAMIFICATION
# ─────────────────────────────────────────────

BADGES = [
    {
        "id": "first_step",
        "icon": "🌱",
        "name_en": "First Step",
        "name_ne": "पहिलो कदम",
        "desc_en": "Completed psychometric assessment",
        "desc_ne": "मनोवैज्ञानिक मूल्याङ्कन पूरा गर्नुभयो",
        "xp": 50,
        "check": lambda r: r.get("psychometric_score", 0) > 0,
    },
    {
        "id": "trusted_neighbor",
        "icon": "🤝",
        "name_en": "Trusted Neighbor",
        "name_ne": "विश्वसनीय छिमेकी",
        "desc_en": "High social trust score",
        "desc_ne": "उच्च सामाजिक विश्वास स्कोर",
        "xp": 30,
        "check": lambda r: r.get("trait_scores", {}).get("social_trust", 0) >= 75,
    },
    {
        "id": "dashain_planner",
        "icon": "🪔",
        "name_en": "Dashain Planner",
        "name_ne": "दशैं योजनाकार",
        "desc_en": "Excellent festival-season planning",
        "desc_ne": "चाडबाडमा उत्कृष्ट वित्तीय योजना",
        "xp": 25,
        "check": lambda r: r.get("trait_scores", {}).get("planning", 0) >= 80,
    },
    {
        "id": "iron_merchant",
        "icon": "⚡",
        "name_en": "Iron Merchant",
        "name_ne": "फलाम व्यापारी",
        "desc_en": "Top resilience score",
        "desc_ne": "उच्च लचिलोपन स्कोर",
        "xp": 25,
        "check": lambda r: r.get("trait_scores", {}).get("resilience", 0) >= 80,
    },
    {
        "id": "credit_ready",
        "icon": "🏆",
        "name_en": "Credit Ready",
        "name_ne": "ऋण तयार",
        "desc_en": "Psychometric score above 75",
        "desc_ne": "मनोवैज्ञानिक स्कोर ७५ भन्दा बढी",
        "xp": 40,
        "check": lambda r: r.get("psychometric_score", 0) >= 75,
    },
    {
        "id": "no_red_flags",
        "icon": "✅",
        "name_en": "Clean Record",
        "name_ne": "सफा रेकर्ड",
        "desc_en": "No behavioral red flags",
        "desc_ne": "कुनै व्यवहारगत समस्या फेला परेन",
        "xp": 20,
        "check": lambda r: r.get("red_flags", "").lower() in ["none", "कुनै छैन", ""],
    },
]


def compute_gamification(result: Dict) -> Dict:
    total_xp, earned = 0, []
    for badge in BADGES:
        try:
            if badge["check"](result):
                total_xp += badge["xp"]
                earned.append(
                    {
                        k: badge[k]
                        for k in [
                            "id",
                            "icon",
                            "name_en",
                            "name_ne",
                            "desc_en",
                            "desc_ne",
                            "xp",
                        ]
                    }
                )
        except Exception:
            pass
    return {"xp_earned": total_xp, "badges_unlocked": earned}


# ─────────────────────────────────────────────
# HALLUCINATION GUARD
# ─────────────────────────────────────────────


def _validate_llm_output(raw: Dict, deterministic: Dict) -> Dict:
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

    for f in INT_FIELDS:
        try:
            v = int(float(str(out.get(f, deterministic.get(f, 50)))))
            out[f] = max(0, min(100, v))
        except Exception:
            out[f] = deterministic.get(f, 50)
            corrections.append(f"[S1] {f} unparseable → deterministic")

    for f in STR_FIELDS:
        if f not in out or not isinstance(out[f], str) or not out[f].strip():
            out[f] = "none" if f == "red_flags" else ""
            corrections.append(f"[S1] {f} missing → default")

    for trait in [
        "conscientiousness",
        "risk_aversion",
        "social_trust",
        "resilience",
        "planning",
    ]:
        llm_v, det_v = out.get(trait, 50), deterministic.get(trait, 50)
        if abs(llm_v - det_v) > 25:
            avg = round((llm_v + det_v) / 2)
            corrections.append(f"[S2] {trait}: {llm_v}→{avg}")
            out[trait] = avg

    recomputed = round(
        out["conscientiousness"] * 0.30
        + out["risk_aversion"] * 0.25
        + out["social_trust"] * 0.20
        + out["resilience"] * 0.15
        + out["planning"] * 0.10
    )
    if abs(out.get("psychometric_score", 50) - recomputed) > 15:
        corrections.append(f"[S2] psych_score → {recomputed}")
        out["psychometric_score"] = recomputed

    if out.get("credit_personality") not in VALID_PERSONALITIES:
        dominant = max(
            [
                "conscientiousness",
                "risk_aversion",
                "social_trust",
                "resilience",
                "planning",
            ],
            key=lambda k: out.get(k, 50),
        )
        fallback = {
            "conscientiousness": "Cautious Planner",
            "risk_aversion": "Conservative Saver",
            "social_trust": "Community Builder",
            "resilience": "Resilient Adapter",
            "planning": "Cautious Planner",
        }
        out["credit_personality"] = fallback.get(dominant, "Cautious Planner")
        corrections.append(f"[S3] invalid personality → {out['credit_personality']}")

    if corrections:
        out["_hallucination_corrections"] = corrections
    return out


# ─────────────────────────────────────────────
# PUBLIC HELPERS
# ─────────────────────────────────────────────


def get_questions(lang: str = "ne", seed: str = None) -> List[Dict]:
    """Returns 5 sampled questions (1 per trait). Pass merchant_id as seed."""
    sampled = sample_questions(seed)
    out = []
    for q in sampled:
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
    scores = {t: 0 for t in TRAITS}
    counts = {t: 0 for t in TRAITS}
    q_map = {q["id"]: q for q in QUESTION_BANK}
    for qid, ans in responses.items():
        q = q_map.get(qid)
        if q and ans in q["scoring"]:
            scores[q["trait"]] += q["scoring"][ans]
            counts[q["trait"]] += 1
    for t in scores:
        if counts[t] > 0:
            scores[t] = round(scores[t] / counts[t])
        else:
            scores[t] = 50  # neutral default for unanswered trait
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
        q_map = {q["id"]: q for q in QUESTION_BANK}
        summary = []
        for qid, ans in responses.items():
            q = q_map.get(qid)
            if q:
                summary.append(
                    f"  [{q['trait']}] {q['question_en'][:80]}... → {ans}: {q['options_en'].get(ans, '?')}"
                )

        prompt = f"""You are a micro-credit psychometric analyst for Nepal's informal economy.

MERCHANT: {merchant_name}
RESPONSES:
{chr(10).join(summary)}

DETERMINISTIC BASELINE (answer-key scores, 0-100):
{json.dumps(deterministic, indent=2)}

RULES:
1. Return ONLY valid JSON. No markdown.
2. Trait scores MUST stay within ±20 of the baseline.
3. psychometric_score = round(conscientiousness*0.30 + risk_aversion*0.25 + social_trust*0.20 + resilience*0.15 + planning*0.10)
4. credit_personality MUST be exactly one of: Cautious Planner | Community Builder | Risk Taker | Resilient Adapter | Conservative Saver
5. insight: 1 sentence, max 20 words, Nepal context.
6. red_flags: "none" if no concerns.

JSON:
{{"conscientiousness":<int>,"risk_aversion":<int>,"social_trust":<int>,"resilience":<int>,"planning":<int>,"psychometric_score":<int>,"credit_personality":"<value>","insight":"<text>","red_flags":"<text>","strengths":"<text>"}}"""

        resp = model.generate_content(prompt)
        raw = re.sub(r"```(?:json)?", "", resp.text.strip()).strip().rstrip("`")
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise ValueError("No JSON in response")
        return _validate_llm_output(json.loads(m.group()), deterministic)
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
    traits = {t: gemini.get(t, deterministic[t]) for t in TRAITS}

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
        "questions_served": [q["id"] for q in sample_questions(merchant_id)],
    }
    gami = compute_gamification(result)
    result["xp_earned"] = gami["xp_earned"]
    result["badges_unlocked"] = gami["badges_unlocked"]
    return result
