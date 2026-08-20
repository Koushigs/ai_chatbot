
from fastapi import FastAPI, Response, Query, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Tuple
from agent import react_agent
from datetime import datetime
# pyrefly: ignore [missing-import]
from langchain_core.messages import AIMessage
from recommendation_eligibility import RecommendationEligibilityEngine
from product_formatter import (
    get_horoscope_recommendations, get_panchang_recommendations,
    get_holidays_recommendations, get_monthly_festivals_recommendations,
    get_janmarashi_recommendations, format_recommendations_html,
    is_astro_specific_query, extract_recommended_links,
    print_recommended_links_to_terminal, safe_print,
    extract_rashi_from_horoscope, extract_rashi_from_query, extract_ALL_festivals_from_response,
    extract_lucky_number_from_horoscope, extract_lucky_color_from_horoscope
)
import requests
from config import (
    KUNDALI_PRICE, JANMARASHI_PRICE, BHARAT_CA_BUNDLE,
    KUNDALI_PDF_API, JANMARASHI_API
)
import re
from urllib.parse import urlencode, quote
import html
import uuid
import os
import hashlib
# pyrefly: ignore [missing-import]
from razorpay import Client
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import json
import sqlite3
from urllib.parse import unquote
import time
import unicodedata


# ✅ CRITICAL: LOAD .env FILE FIRST!
load_dotenv()


# =============================================
# MULTILINGUAL KEYWORD SUPPORT (COMPREHENSIVE)
# =============================================
# ALL 9 INDIAN LANGUAGES + ENGLISH

JANMARASHI_KEYWORDS = [
    # English & Common Misspellings / Typos
    "janmarashi", "janmarash", "janma rashi", "janma rash", "janmma rashi", "janmma rash", "janmmarashi", "janam rashi", "janamrashi", "janam rash", "janm rashi", "janmrashi", "janmrash",
    "janmarasi", "janma raasi", "janam raasi", "janmma raasi", "janmarashii", "janma rashii", "janmma",
    "moon sign", "lunar sign", "birth moon", "birth rashi", "lunar rashi", "my rashi", "mera rashi", "meri rashi", "rashi batao", "rashi bataye", "mera rashi batao", "meri rashi batao",
    
    # Hindi
    "जन्म राशि", "चंद्र राशि", "जैनम राशि", "जन्मराशी",
    
    # Tamil
    "பிறப்பு இராசி",
    
    # Telugu  
    "జన్మ రాశి", "చంద్ర రాశి",
    
    # Kannada
    "ಜನ್ಮ ರಾಶಿ", "ಚಂದ್ರ ರಾಶಿ",
    
    # Malayalam
    "ജന്മ രാശി",
    
    # Marathi
    "जन्म राशी", "चंद्र राशी",
    
    # Gujarati
    "જન્મ રાશિ", "ચંદ્ર રાશિ", "જન્મરાશિ", "જન્મરાશી", "જન્મ રાશી",
    
    # Bengali
    "জন্ম রাশি", "চন্দ্র রাশি",
    
    # Punjabi
    "ਜਨਮ ਰਾਸ਼ੀ", "ਚੰਦਰ ਰਾਸ਼ੀ",
    
    # Odia
    "ଜନ୍ମ ରାଶି", "ଚନ୍ଦ୍ର ରାଶି", "ଜନ୍ମରାଶି",
]

KUNDALI_KEYWORDS = [
    "kundali", "kundli", "birth chart", "natal chart", "janam patri", "janma patri", "kundali chart",
    "कुंडली", "जन्म पत्रिका", "जन्म चार्ट",
    "குண்டலி", "பிறப்பு சட்டம்",
    "కుండలి", "జన్మమణ్యం",
    "ಕುಂಡಲಿ", "ಜನ್ಮ ಪತ್ರಿಕೆ",
    "കുണ്ടലി", "ജന്മ പത്രിക",
    "कुंडली", "जन्म पत्रिका",
    "કુંડળી", "જન્મ કુંડળી", "જનમ કુંડળી", "કુંડલી", "જન્મ પત્રિકા",
    "কুণ্ডলী", "জন्म পত्রিকা",
    "ਕੁੰਡਲੀ", "ਜਨਮ ਪੱਤਰੀ",
    "କୁଣ୍ଡଲି", "ଜନ୍ମ କୁଣ୍ଡଲି", "ଜନ୍ମ ପତ୍ରିକା", "କୁଣ୍ଡଳୀ",
]

# =============================================
# 🔮 PREDICTIVE / ASTROLOGY KEYWORDS (ALL 10 SUPPORTED LANGUAGES)
# Categories: marriage, career, love, children, future
# =============================================
PREDICTIVE_CATEGORIES = {
    "marriage": [
        # English & Hinglish
        "shaadi", "shadi", "vivah", "marriage", "married", "get married", "marry", "wedding", "spouse", "husband", "wife",
        "life partner", "marriage timing", "love marriage", "arranged marriage", "second marriage",
        # Hindi
        "शादी", "विवाह", "जीवनसाथी", "दूल्हा", "दुल्हन", "पति", "पत्नी",
        # Tamil
        "திருமணம்", "கல்யாணம்", "வாழ்க்கைத்துணை",
        # Telugu
        "వివాహం", "పెళ్లి", "జీవిత భాగస్వామి",
        # Kannada
        "ಮದುವೆ", "ವಿವಾಹ", "ಜೀವನ ಸಂಗಾತಿ",
        # Malayalam
        "വിവാഹം", "കല്യാണം", "ജീവിതപങ്കാളി",
        # Marathi
        "लग्न", "विवाह", "आयुष्यमान",
        # Gujarati
        "લગ્ન", "વિવાહ", "જીવનસાથી", "શાદી",
        # Bengali
        "বিয়ে", "বিবাহ", "জীবনসঙ্গী",
        # Odia
        "ବିବାହ", "ବାହାଘର", "ଜୀବନସାଥୀ",
    ],
    "career": [
        # English & Hinglish
        "career", "naukri", "job", "employment", "promotion", "business", "work life", "profession", "placement",
        "kam dhandha", "karobar", "vyapar",
        # Hindi
        "करियर", "नौकरी", "जॉब", "व्यापार", "प्रमोशन", "रोजगार", "कारोबार",
        # Tamil
        "வேலை", "தொழில்", "பதவி உயர்வு", "வியாபாரம்",
        # Telugu
        "ఉద్యోగం", "కెరీర్", "వ్యాపారం", "ప్రమోషన్",
        # Kannada
        "ಕೆಲಸ", "ಉದ್ಯೋಗ", "ವೃತ್ತಿಜೀವನ", "ವ್ಯಾಪಾರ",
        # Malayalam
        "ജോലി", "കരിയർ", "ബിസിനസ്", "തൊഴിൽ",
        # Marathi
        "नोकरी", "करिअर", "व्यवसाय", "बढती", "रोजगार",
        # Gujarati
        "નોકરી", "કરિયર", "ધંધો", "પ્રમોશન", "રોજગાર", "કામ",
        # Bengali
        "চাকরি", "ক্যারিয়ার", "ব্যবসা", "উন্নতি", "কর্মজীবন",
        # Odia
        "ଚାକିରି", "କ୍ୟାରିଅର୍", "ବ୍ୟବସାୟ", "ପ୍ରମୋସନ୍", "କାର୍ଯ୍ୟ",
    ],
    "love": [
        # English & Hinglish
        "love life", "relationship", "romance", "boyfriend", "girlfriend", "partner", "soulmate", "love marriage",
        "pyaar", "pyar", "love", "find love",
        # Hindi
        "लव लाइफ", "प्रेम संबंध", "प्यार", "रिलेशनशिप", "प्रेम जीवन", "सच्चा प्यार",
        # Tamil
        "காதல்", "உறவு", "காதல் வாழ்க்கை",
        # Telugu
        "ప్రేమ", "సంబంధం", "ప్రేమ జీవితం",
        # Kannada
        "ಪ್ರೀತಿ", "ಸಂಬಂಧ", "ಪ್ರೀತಿಯ ಜೀವನ",
        # Malayalam
        "പ്രണയം", "ബന്ധം", "പ്രണയജീവിതം",
        # Marathi
        "प्रेम", "नातेसंबंध", "प्रेम जीवन",
        # Gujarati
        "પ્રેમ", "સંબંધ", "પ્રેમ જીવન",
        # Bengali
        "প্রেম", "সম্পর্ক", "ভালোবাসা", "প্রেম জীবন",
        # Odia
        "ପ୍ରେମ", "ସମ୍ପର୍କ", "ପ୍ରେମ ଜୀବନ",
    ],
    "children": [
        # English & Hinglish
        "children", "kids", "child", "baby", "pregnancy", "childbirth", "santan", "santana", "bachche", "bachhe", "bacha",
        # Hindi
        "बच्चे", "संतान", "संतान सुख", "संतान योग", "बच्चा", "पुत्र", "पुत्री",
        # Tamil
        "குழந்தைகள்", "குழந்தை", "குழந்தை பாக்கியம்", "மகப்பேறு",
        # Telugu
        "పిల్లలు", "సంతానం", "సంతాన యోగం",
        # Kannada
        "ಮಕ್ಕಳು", "ಸಂತಾನ", "ಸಂತಾನ ಭಾಗ್ಯ",
        # Malayalam
        "കുട്ടികൾ", "സന്താനം", "സന്താനഭാഗ്യം",
        # Marathi
        "मुले", "बाळ", "संतान", "संतान सुख",
        # Gujarati
        "બાળકો", "સંતાન", "સંતાન સુખ", "બાળક",
        # Bengali
        "সন্তান", "বাচ্চা", "সন্তান লাভ",
        # Odia
        "ଛୁଆ", "ସନ୍ତାନ", "ସନ୍ତାନ ସୁଖ", "ପିଲା",
    ],
    "future": [
        # English & Hinglish
        "future", "destiny", "fate", "bhavishya", "bhavishyat", "life prediction", "what will happen", "aage kya",
        "kismat", "bhagya", "general prediction", "future prediction",
        # Hindi
        "भविष्य", "आगे क्या होगा", "किस्मत", "भाग्य", "भविष्यफल", "मेरा भविष्य",
        # Tamil
        "எதிர்காலம்", "எதிர்கால வாழ்க்கை", "விதி", "ஜாதக பலன்",
        # Telugu
        "భవిష్యత్తు", "తలరాత", "జాతకం", "భవిష్యత్",
        # Kannada
        "ಭವಿಷ್ಯ", "ಭವಿಷ್ಯದ ಜೀವನ", "ವಿಧಿಯ ಬರಹ",
        # Malayalam
        "ഭാവി", "ഭാവി ജീവിതം", "വിധിയുടെ ഫലം",
        # Marathi
        "भविष्य", "भविष्यकाळ", "नशीब", "भाग्य",
        # Gujarati
        "ભવિષ્ય", "ભાગ્ય", "નસીબ", "ભવિષ્યફળ",
        # Bengali
        "ভবিষ্যৎ", "ভাগ্য", "ভবিষ্যৎ বাণী",
        # Odia
        "ଭବିଷ୍ୟତ", "ଭାଗ୍ୟ", "ଭବିଷ୍ୟଫଳ",
    ]
}

# Flattened list for fast top-level matching
PREDICTIVE_KEYWORDS = [kw for cat_list in PREDICTIVE_CATEGORIES.values() for kw in cat_list]


def detect_predictive_category(text: str) -> Optional[str]:
    """Detect specific predictive category (marriage, career, love, children, future) from query."""
    if not text:
        return None
    normalized = normalize_text(text)
    
    # Priority matching for explicit category intents
    for category in ["marriage", "career", "love", "children", "future"]:
        for keyword in PREDICTIVE_CATEGORIES[category]:
            if re.search(rf"(?:^|\b|\s){re.escape(keyword)}(?:$|\b|\s)", normalized) or keyword in normalized:
                return category
    return None

# 🆕 NEW: HOROSCOPE_RASHI_KEYWORDS - ALL ZODIAC SIGNS + HOROSCOPE TERMS
HOROSCOPE_RASHI_KEYWORDS = [
    # English (zodiac signs)
    "aries", "taurus", "gemini", "cancer", "leo", "virgo", 
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    "horoscope", "daily", "weekly", "monthly", "yearly", "rashifalam", "rashi", "zodiac", "sun sign",
    
    # Hindi (zodiac signs)
    "मेष", "वृष", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन",
    "राशिफल", "राशि", "भविष्य",
    
    # Tamil (zodiac signs)
    "மேஷம்", "ரிஷபம்", "மிதுனம்", "கர्कடकம्", "சிம்ஹம்", "கன்னியா",
    "துலாம்", "விருச्चिகम्", "தனुசु", "मकरम्", "कुम्भम्", "मीனम்",
    "இராசிபலன்", "இராசி",
    
    # Telugu (zodiac signs)
    "మేష", "వృష", "మిథున", "కర్క", "సింహ", "కన్య",
    "తుల", "వృశ్చిక", "ధనుస్", "మకర", "కుంభ", "మీన",
    "రాశిఫలాలు", "రాశిఫలం", "రాశి",
    
    # Kannada (zodiac signs)
    "ಮೇಷ", "ವೃಷ", "ಮಿಥುನ", "ಕರ್ಕ", "ಸಿಂಹ", "ಕನ್ನಿಸು",
    "ತುಲಾ", "ವೃಶ್ಚಿಕ", "ಧನುಸ್ಸು", "ಮಕರ", "ಕುಂಭ", "ಮೀನ",
    "ರಾಶಿಫಲ",
    
    # Malayalam (zodiac signs)
    "മേഷം", "വൃഷം", "മിഥുനം", "കർക്കടകം", "സിംഹം", "കന്നി",
    "തുലാം", "വൃശ്ചികം", "ധനുസ്സ്", "മകരം", "കുംഭം", "മീനം",
    
    # Marathi (zodiac signs)
    "मेष", "वृष", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन",
    "राशीफल",
    
    # Gujarati (zodiac signs)
    "મેષ", "વૃષભ", "મિથુન", "કર્ક", "સિંહ", "કન્યા",
    "તુલા", "વૃશ્ચિક", "ધનુ", "મકર", "કુંભ", "મીન",
    "રાશિફળ", "રાશીફળ", "રાશિ", "રાશી",
    
    # Bengali (zodiac signs)
    "মেষ", "বৃষ", "মিথুন", "কর্ক", "সিংহ", "কন্যা",
    "তুলা", "বৃশ্চিক", "ধনু", "মকর", "কুম্ভ", "মীন",
    
    # Punjabi (zodiac signs)
    "ਮੇਸ਼", "ਵ੍ਰਿਸ਼", "ਮਿਥੁਨ", "ਕਰਕ", "ਸਿੰਘ", "ਕੰਨਿਆ",
    "ਤੁਲਾ", "ਵ੍ਰਿਸ਼ਚਿਕ", "ਧਨੂ", "ਮਕਰ", "ਕੁੰਭ", "ਮੀਨ",
    
    # Odia (zodiac signs)
    "ମେଷ", "ବୃଷ", "ମିଥୁନ", "କର୍କଟ", "ସିଂହ", "କନ୍ୟା",
    "ତୁଳା", "ବିଛା", "ଧନୁ", "ମକର", "କୁମ୍ଭ", "ମୀନ",
    "ରାଶିଫଳ", "ରାଶି",
]

PANCHANG_KEYWORDS = [
    "panchang", "panchangam", "tithi", "nakshatra", "muhurat", "muhurata",
    "पंचांग", "तिथि", "नक्षत्र", "मुहूर्त",
    "பஞ்சாங்கம்", "திதி", "நட்சத்திரம்", "முஹூர்த்தம்",
    "పంచాంగం", "తిథి", "నక్షత్రం", "ముహూర్తం",
    "ಪಂಚಾಂಗ", "ತಿಥಿ", "ನಕ್ಷತ್ರ", "ಮುಹೂರ್ತ",
    "പഞ്ചാംഗം", "തിതി", "നക്ഷത്രം", "മുഹൂർത്തം",
    "पंचांग", "तिथी", "नक्षत्र", "मुहूर्त",
    "પંચાંગ", "તિથિ", "નક્ષત્ર", "મુહૂર્ત",
    "ପଞ୍ଚାଙ୍ଗ", "ତିଥି", "ନକ୍ଷତ୍ର", "ମୁହୂର୍ତ୍ତ",
    "পঞ্চাঙ্গ", "তিথি", "নক্ষত्র", "মুহূর্ত",
    "ਪੰਚਾਂਗ", "ਤਿਥੀ", "ਨਕਸ਼ਤ੍ਰ", "ਮੁਹੂਰਤ",
]

FESTIVAL_KEYWORDS = [
    "festival", "celebration", "diwali", "deepavali", "holi", "dussehra",
    "navratri", "navratras", "eid", "christmas", "new year", "makar sankranti",
    "त्योहार", "दिवाली", "होली", "दशहरा", "नवरात्रि", "ईद", "क्रिसमस",
    "திருவிழா", "தீபாவளி", "ஹோலி", "பொங்கல்",
    "పండుగ", "దివాళి", "హోళీ", "సంక్రాంతి",
    "ಉತ್ಸವ", "ದೀಪಾವಳಿ", "ಹೋಳಿ",
    "ത്യോഹാരം", "ദീപാവലി", "ഹോളി",
    "सण", "दिवाली", "होळी",
    "તહેવાર", "ઉત્સવ", "દિવાળી", "હોળી", "નવરાત્રી", "દશેરા", "ઉત્તરાયણ",
    "ପର୍ବ", "ପର୍ବପର୍ବାଣି", "ଉତ୍ସବ", "ଦୀପାବଳି", "ହୋଲି", "ଦଶହରା", "ନବରାତ୍ରି", "ଦୁର୍ଗାପୂଜା",
    "উৎসব", "দিওয়ালি", "হোলি",
    "ਤਿਉਹਾਰ", "ਦਿਵਾਲੀ", "ਹੋਲੀ",
]

HOLIDAYS_KEYWORDS = [
    "holiday", "public holiday", "national holiday", "vacation", "off", "break",
    "छुट्टी", "छुट्टियां", "सार्वजनिक छुट्टी",
    "விடுமுறை", "ஓய்வுநாள்",
    "సెలవు", "ఛుట్టి",
    "ರಜೆ", "ವೇಳೆ",
    "ഇടവേള", "പ്രതിപാദന",
    "सुट्टी", "सार्वजनिक सुट्टी",
    "રજા", "જાહેર રજા", "રજાઓ",
    "ଛୁଟି", "ସରକାରୀ ଛୁଟି", "ଛୁଟିଦିନ",
    "ছুটি", "সরকারি ছুটি",
    "ਛੁੱਟੀ", "ਛੁੱਟੀ",
]

YES_KEYWORDS = [
    "yes", "yep", "yeah", "ok", "okay", "sure", "aye", "affirmative",
    "हाँ", "जी", "ठीक है", "बिल्कुल",
    "ஆம்", "சரி", "ஒப்புக்கொள்",
    "అవును", "సరిగా", "తీర్చుకోండి",
    "ಹೌದು", "ಸರಿ", "ಸ್ವೀಕರಿಸಿ",
    "അതെ", "സാധുവായി",
    "हो", "ठीक आहे", "मंजूर आहे",
    "હા", "હાજી", "બરાબર", "ચોક્કસ",
    "હଁ", "ଠିକ୍ ଅଛି", "ନିଶ્ચିତ",
    "হ্যাঁ", "ঠিক আছে", "স্বীকৃতি",
    "ਹਾਂ", "ਠੀਕ ਹੈ", "ਪ੍ਰਵਾਨਗਤੀ",
]

NO_KEYWORDS = [
    "no", "nope", "nay", "cancel", "not now", "skip", "decline",
    "नहीं", "मत करो", "छोड़ो", "अस्वीकार करो",
    "இல்லை", "வேண்டாம்", "தவிர்க்க",
    "లేదు", "చేయవద్దు", "వదిలేయండి",
    "ಇಲ್ಲ", "ಮಾಡಬೇಡಿ", "ಬಿಡಿ",
    "ഇല്ല", "വേണ്ടാം",
    "नाही", "नकार", "सोडून दे",
    "ના", "ના પાડો", "રદ કરો",
    "ନା", "ମନା", "ବାତିଲ્",
    "না", "নয়", "অસવીકાર",
    "ਨਹੀਂ", "ਮਤ ਕਰ", "ਅਸਵੀਕਾਰ",
]


# =============================================
# NORMALIZATION & DETECTION FUNCTIONS
# =============================================

def normalize_text(text: str) -> str:
    """Normalize text for keyword matching - preserves Unicode"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.lower().strip())


def detect_tool_type_multilingual(user_query: str, ai_response: str, messages: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """
    🌍 ADVANCED MULTILINGUAL DETECTION WITH PRIORITY ORDER & MULTI-TURN HISTORY
    """
    if not user_query:
        return None
    
    normalized = normalize_text(user_query)
    
    safe_print(f"\n{'='*70}")
    safe_print("🔍 MULTILINGUAL TOOL DETECTION v3 - PRIORITY ORDER FIXED")
    safe_print(f"{'='*70}")
    safe_print(f"Original: {user_query[:100]}")
    safe_print(f"Normalized: {normalized[:100]}")
    safe_print(f"{'='*70}\n")
    
    # Check payload signatures first
    if "janmarashi_payload" in ai_response or "janmarashi_payload" in user_query:
        safe_print("✅ JANMARASHI CONFIRMED: janmarashi_payload signature found")
        return "janmarashi"

    if "kundali_pdf_payload" in ai_response or "kundali_pdf_payload" in user_query:
        safe_print("✅ KUNDALI CONFIRMED: kundali_pdf_payload signature found")
        return "kundali"

    # ==========================================
    # PRIORITY 1: KUNDALI (HIGHEST)
    # ==========================================
    for keyword in KUNDALI_KEYWORDS:
        if keyword in normalized:
            safe_print(f"✅ KUNDALI CONFIRMED: '{keyword}'")
            return "kundali"

    # ==========================================
    # PRIORITY 2: JANMARASHI
    # ==========================================
    for keyword in JANMARASHI_KEYWORDS:
        if keyword in normalized:
            safe_print(f"✅ JANMARASHI CONFIRMED: '{keyword}'")
            return "janmarashi"

    # Flexible regex matching for typos like janmma rashi, janam rashi, janm rashi, janmarasi
    if re.search(r'\bja?n+a?m+[a-z]*\s*(?:r[a-z]*sh[a-z]*|r[a-z]*s[a-z]*|sign|moon|patrika)?\b', normalized):
        safe_print("✅ JANMARASHI CONFIRMED via janm* typo regex pattern")
        return "janmarashi"

    # Check if birth details are present with rashi/moon keywords
    birth_info = extract_birth_details(user_query)
    if birth_info and any(w in normalized for w in ["rashi", "rashee", "raasi", "sign", "moon", "birth", "janma", "janam", "janmma"]):
        safe_print("✅ JANMARASHI CONFIRMED: Birth details + Rashi/Moon keywords detected")
        return "janmarashi"


    # PRIORITY 3: PREDICTIVE / ASTROLOGY QUESTIONS
    # ==========================================
    pred_category = detect_predictive_category(normalized)
    if pred_category:
        safe_print(f"✅ PREDICTIVE CONFIRMED: Category '{pred_category}'")
        return f"predictive_{pred_category}"

    # ==========================================
    # PRIORITY 3: PANCHANG
    # ==========================================
    for keyword in PANCHANG_KEYWORDS:
        if keyword in normalized:
            safe_print(f"✅ PANCHANG keyword found: '{keyword}'")
            return "panchang"
    
    # ==========================================
    # PRIORITY 4: HOROSCOPE_RASHI ← CRITICAL!
    # ==========================================
    for keyword in HOROSCOPE_RASHI_KEYWORDS:
        if keyword in normalized:
            safe_print(f"✅ HOROSCOPE_RASHI keyword found: '{keyword}'")
            return "horoscope"
    
    # ==========================================
    # PRIORITY 5: MONTHLY_FESTIVALS
    # ==========================================
    for keyword in FESTIVAL_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", normalized):
            safe_print(f"✅ MONTHLY_FESTIVALS keyword found: '{keyword}'")
            return "monthly_festivals"
    
    # ==========================================
    # PRIORITY 6: HOLIDAYS
    # ==========================================
    for keyword in HOLIDAYS_KEYWORDS:
        if keyword in normalized:
            safe_print(f"✅ HOLIDAYS keyword found: '{keyword}'")
            return "holidays"

    # ==========================================
    # FALLBACK: UNLABELED BIRTH DETAILS IN CURRENT QUERY (e.g. "2004-05-05, 7am, bengaluru")
    # Only evaluated when user_query has NO keywords for any tool!
    # ==========================================
    if messages:
        # Language switch query fallback (e.g. "give me it in english", "give it me in english", "in english")
        is_lang_switch = bool(
            re.search(r'\b(?:give|tell|show|write|translate)\s+(?:me\s+)?(?:it\s+)?in\s+(?:english|inglesh|hindi|hindu|gujarati|gujrati|odia|kannada|tamil|telugu|malayalam|marathi|bengali)\b', normalized)
            or re.search(r'^\s*(?:in|to)\s+(?:english|inglesh|hindi|gujarati|odia|kannada|tamil|telugu|malayalam|marathi|bengali)\b', normalized)
            or any(phrase in normalized for phrase in ["give me it in english", "give it me in english", "give it in english", "in english", "english"])
        )
        if is_lang_switch:
            for m in reversed(messages[:-1] if len(messages) > 1 else messages):
                if isinstance(m, dict) and m.get("role") == "user":
                    user_content = str(m.get("content", "")).lower()
                    for kw in HOROSCOPE_RASHI_KEYWORDS:
                        if kw in user_content:
                            safe_print("✅ HOROSCOPE confirmed via language switch query + history context")
                            return "horoscope"
                    for kw in PANCHANG_KEYWORDS:
                        if kw in user_content:
                            safe_print("✅ PANCHANG confirmed via language switch query + history context")
                            return "panchang"
                    for kw in FESTIVAL_KEYWORDS:
                        if kw in user_content:
                            safe_print("✅ MONTHLY_FESTIVALS confirmed via language switch query + history context")
                            return "monthly_festivals"
                    for kw in HOLIDAYS_KEYWORDS:
                        if kw in user_content:
                            safe_print("✅ HOLIDAYS confirmed via language switch query + history context")
                            return "holidays"

        current_birth_details = extract_birth_details(user_query)
        if current_birth_details:
            for m in reversed(messages):
                if isinstance(m, dict) and m.get("role") == "user":
                    user_content = str(m.get("content", "")).lower()
                    if any(kw in user_content for kw in KUNDALI_KEYWORDS):
                        safe_print("✅ KUNDALI CONFIRMED via history context + current birth details")
                        return "kundali"
                    if any(kw in user_content for kw in JANMARASHI_KEYWORDS) or re.search(r'\bja?n+a?m+[a-z]*\s*(?:r[a-z]*sh[a-z]*|r[a-z]*s[a-z]*|sign|moon|patrika)?\b', user_content) or "rashi" in user_content:
                        safe_print("✅ JANMARASHI CONFIRMED via history context + current birth details")
                        return "janmarashi"
                    if any(kw in user_content for kw in PREDICTIVE_KEYWORDS):
                        safe_print("✅ KUNDALI CONFIRMED via predictive history context + current birth details")
                        return "kundali"

    safe_print(f"❌ No tool type detected")
    return None


def normalize_city_name(city: str) -> str:
    if not city:
        return city
    # Strip noise words like report, reports, chart, pdf, details, kundali, kundli, generate, genetate
    clean_city = re.sub(
        r'(?:report|reports|chart|pdf|details|kundali|kundli|janmarashi|janma|janam|rashi|generate|ganerate|genetate|generat|genrate|create|make|show|get|calculate|મારી|જન્મ|કુંડળી|કુંડલી|બનાવો|મોર|ଜନ୍ମ|କୁଣ୍ଡଲି|ପ୍ରସ୍ତୁତ|କରନ୍ତୁ|मेरी|मेरा|जन्म|राशि|बताओ|बताएं|बताइए|बताइये|कुंडली|हिंदी|हिन्दी|ನನ್ನ|ಜನ್ಮ|ರಾಶಿ|ತಿಳಿಸಿ|ಕುಂಡಲಿ|ಲೆಕ್ಕಾಚಾರ|ಮಾಡಿ|ತೋರಿಸಿ|ಕನ್ನಡ)',
        '', city, flags=re.IGNORECASE
    ).strip(' :=-,')
    if not clean_city:
        clean_city = city.strip()
    return clean_city.title()


def extract_language(text: str) -> str:
    """
    Extract language code for Kundali PDF API (en, hi, ta, kn, ml, te, mr, gu, bn, or).
    Defaults strictly to English ('en') if no explicit language is requested.
    """
    if not text:
        return "en"
    
    t_clean = text.lower().strip()
    
    # Strip leading generic greetings like 'hi', 'hello', 'hey' to avoid false positive 'hi' (Hindi)
    t_clean = re.sub(r'^(?:hi|hello|hey|greetings|namaste)[,\s!.]+', '', t_clean)

    # 0. English (Explicit check - case-insensitive)
    if re.search(r'\b(?:english|inglesh)\b', t_clean):
        return "en"

    # 1. Kannada
    if re.search(r'\b(?:kannada|kanada|kannad)\b|[ನನ್ನಜನ್ಮಕುಂಡಲಿರಾಶಿಕ್ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಳೞ]', t_clean):
        return "kn"
    # 2. Hindi
    elif re.search(r'\b(?:hindi|hindu)\b|[अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह]', t_clean):
        return "hi"
    # 3. Tamil
    elif re.search(r'\b(?:tamil|tamizh)\b|[அஆஇஈஉஊஎஏஐஒஓஔகஙசஜஞடணதநபமயரலவழளறன]', t_clean):
        return "ta"
    # 4. Telugu
    elif re.search(r'\b(?:telugu|telgu)\b|[అఆఇఈఉఊఋఎఏఐఒఓఔకఖగఘఙచఛజఝఞటఠడఢణతథదధನಪಫಬಭಮಯರಲವశಷసಹ]', t_clean):
        return "te"
    # 5. Malayalam
    elif re.search(r'\b(?:malayalam|kerala)\b|[അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹളഴറ]', t_clean):
        return "ml"
    # 6. Marathi
    elif re.search(r'\bmarathi\b', t_clean):
        return "mr"
    # 7. Gujarati
    elif re.search(r'\b(?:gujarati|gujrati)\b|[અઆઇઈઉઊઋએઐઓઔકખగઘઙચછજઝઞટઠડઢણતથદધનપફબભમયરલવશષસહળ]', t_clean):
        return "gu"
    # 8. Bengali
    elif re.search(r'\b(?:bengali|bangla)\b|[অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভময়رلশষসহள]', t_clean):
        return "bn"
    # 9. Odia
    elif re.search(r'\b(?:odia|oriya)\b|[ଅଆଇଈଉଊଋଏଐଓୌକଖଗଘଙଚଛଜଝଞଟଠଡଢଣତଥଦଧନପଫବଭମଯରଲଵଶଷସହଳ]', t_clean):
        return "or"
    # 10. English (Default)
    return "en"


def is_yes_response(text: str) -> bool:
    """Check if user said YES in any language (including short slang like ya, yup, yeah)"""
    if not text:
        return False
    normalized = normalize_text(text)
    
    # Check exact word matches first for short informal responses like 'ya', 'y', 'ha'
    words = re.findall(r'\b\w+\b', normalized)
    for word in words:
        if word in ["yes", "y", "ya", "yaa", "yah", "yea", "yeah", "yep", "yup", "yess", "ok", "okay", "sure", "pay", "ha", "haan", "han","yas"]:
            safe_print(f"✅ YES detected (word match): '{word}'")
            return True

    for keyword in YES_KEYWORDS:
        if keyword in normalized:
            safe_print(f"✅ YES detected: '{keyword}'")
            return True
    return False


def is_no_response(text: str) -> bool:
    """Check if user said NO in any language"""
    normalized = normalize_text(text)
    for keyword in NO_KEYWORDS:
        if keyword in normalized:
            safe_print(f"✅ NO detected: '{keyword}'")
            return True
    return False


# =============================================
# ✅ EXTRACT BIRTH DETAILS (ALL LANGUAGES)
# =============================================

def extract_birth_details_from_history(messages: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """Search current query and past user messages in history for birth details."""
    if not messages:
        return None
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = str(msg.get("content", ""))
            clean_content = re.sub(r'\s*\(For context, today\'s date is.*?\)\.?', '', content, flags=re.IGNORECASE).strip()
            details = extract_birth_details(clean_content)
            if details:
                return details
    return None


def extract_birth_details(text: str) -> Optional[Dict[str, str]]:
    """
    Extract date, time, place from user input in ANY language and format.
    Supports dates: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, etc.
    Supports times: 6am, 6 am, 06:00 AM, 6:30pm, 18:00, etc.
    """
    if not text:
        return None

    safe_print(f"\n[EXTRACT] Parsing: {text[:100]}...")

    # 1. Flexible Date Parsing
    date_str = None
    match_yyyy = re.search(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    match_dd = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b", text)

    if match_yyyy:
        y, m, d = match_yyyy.group(1), match_yyyy.group(2).zfill(2), match_yyyy.group(3).zfill(2)
        date_str = f"{y}-{m}-{d}"
    elif match_dd:
        d, m, y = match_dd.group(1).zfill(2), match_dd.group(2).zfill(2), match_dd.group(3)
        date_str = f"{y}-{m}-{d}"

    # 2. Flexible Time Parsing
    time_str = None
    match_time_colon = re.search(r"\b(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM|am|pm)?\b", text)
    match_time_simple = re.search(r"\b(\d{1,2})\s*(AM|PM|am|pm)\b", text)

    if match_time_colon:
        hr = int(match_time_colon.group(1))
        mn = match_time_colon.group(2)
        ampm = match_time_colon.group(3)
        if ampm:
            time_str = f"{hr:02d}:{mn} {ampm.upper()}"
        else:
            if hr >= 12:
                hr_12 = hr if hr == 12 else hr - 12
                time_str = f"{hr_12:02d}:{mn} PM"
            else:
                hr_12 = 12 if hr == 0 else hr
                time_str = f"{hr_12:02d}:{mn} AM"
    elif match_time_simple:
        hr = int(match_time_simple.group(1))
        ampm = match_time_simple.group(2).upper()
        time_str = f"{hr:02d}:00 {ampm}"

    if date_str and time_str:
        # Check for explicit place label (e.g., Place: Mumbai, City: Delhi, Location: Bengaluru)
        explicit_place_match = re.search(r'\b(?:place|city|location|pob)\s*[:=-]\s*([^,\n\r?]+)', text, flags=re.IGNORECASE)
        
        if explicit_place_match:
            raw_place = explicit_place_match.group(1).strip()
            cleaned_place = re.sub(r'^(?:in|at|city|place|location)\s+', '', raw_place, flags=re.IGNORECASE).strip(' :=-')
            norm_p = normalize_city_name(cleaned_place)
            place_text = norm_p if norm_p else (cleaned_place if cleaned_place else "Unknown")
        else:
            # Remove matched date & time strings to isolate place text
            remainder = text
            if match_yyyy:
                remainder = remainder.replace(match_yyyy.group(0), "")
            elif match_dd:
                remainder = remainder.replace(match_dd.group(0), "")

            if match_time_colon:
                remainder = remainder.replace(match_time_colon.group(0), "")
            elif match_time_simple:
                remainder = remainder.replace(match_time_simple.group(0), "")

            # Remove language phrases from remainder to keep place string clean
            remainder = re.sub(r'\b(?:in|language|lang)\s+(?:kannada|hindi|tamil|telugu|malayalam|marathi|gujarati|bengali|odia|english)\b', '', remainder, flags=re.IGNORECASE)
            remainder = re.sub(r'\b(?:kannada|hindi|tamil|telugu|malayalam|marathi|gujarati|bengali|odia|english|ગુજરાતી|ઓડીઆ|ઓડિયા|ଓଡ଼ିଆ|हिन्दी|தமிழ்|తెలుగు|ಕನ್ನಡ|മലയാളം|मराठी|বাংলা|ਪੰਜਾਬੀ)\b', '', remainder, flags=re.IGNORECASE)
            
            # Remove field label keywords, question words, and prompt verbs from remainder
            remainder = re.sub(
                r'(?:\b(?:what|is|my|moon|sign|lunar|zodiac|birth|i|want|need|please|pls|can|you|generate|ganerate|genetate|generat|genrate|create|make|show|get|calculate|tell|send|me|for|in|at|city|place|location|date|time|dob|tob|pob|details|report|reports|chart|pdf|kundali|kundli|janmarashi|janma|janam|janmma|rashi|rashee|raasi| के|लिए|की|में|ನನ್ನ|ಜನ್ಮ|ರಾಶಿ|ಲೆಕ್ಕಾಚಾರ|ಮಾಡಿ|મારી|જન્મ|કુંડળી|કુંડલી|બનાવો|મોર|ଜନ୍ମ|କୁଣ୍ଡଲି|କୁଣ୍ଡଳୀ|ପ୍ରସ୍ତୁତ|କରନ୍ତୁ)\b|જન્મ|કુંડળી|કુંડલી|બનાવો|મારી|ଜନ୍ମ|କୁଣ୍ଡଲି|ପ୍ରସ୍ତୁତ|କରନ୍ତୁ|મોર)',
                ' ', remainder, flags=re.IGNORECASE
            )

            parts = [p.strip() for p in remainder.split(",") if p.strip()]
            valid_parts = []
            for part in parts:
                cleaned_part = re.sub(
                    r'^(?:(?:\b(?:what|is|my|moon|sign|lunar|zodiac|birth|i|want|need|please|pls|can|you|generate|ganerate|genetate|generat|genrate|create|make|show|get|calculate|tell|me|report|reports|chart|pdf|kundali|kundli|janmarashi|janma|janam|janmma|rashi|rashee|raasi|for|in|city|place|at|location|language|lang|kannada|hindi|tamil|telugu|bengali|marathi|malayalam|english|punjabi|gujarati|के|लिए|की|में|ನನ್ನ|ಜನ್ಮ|ರಾಶಿ|ಲೆಕ್ಕಾಚಾರ|ಮಾಡಿ|મારી|જન્મ|કુંડળી|કુંડલી|બનાવો|મોર|ଜନ୍ମ|କୁଣ୍ଡଲି|ପ୍ରସ୍ତୁତ|କରନ୍ତୁ)\b)|\s|[:=-]|\?)+',
                    '', part, flags=re.IGNORECASE
                ).strip(' :=-?')
                cleaned_part = re.sub(r'\b(?:what|is|my|moon|sign|lunar|zodiac|birth|report|reports|chart|pdf|details|kundali|kundli|janmarashi|generate|ganerate|genetate|generat|genrate|create|મારી|જન્મ|કુંડળી|કુંડલી|બનાવો|મોર|ଜନ୍ମ|କୁଣ୍ଡଲି|ପ୍ରସ୍ତୁତ|କରନ୍ତୁ)\b', '', cleaned_part, flags=re.IGNORECASE).strip(' :=-?')
                
                                # Check if cleaned_part is a valid city and not prompt noise
                is_noise = any(kw in cleaned_part.lower() for kw in [
                    "janmarashi",
                    "janma rashi",
                    "janmma rashi",
                    "kundali",
                    "kundli",
                    "moon sign",
                    "birth chart",
                    "natal chart",
                    "report",
                    "reports",
                    "chart",
                    "pdf",
                    "details",
                    "generate",
                    "create",
                    "calculate",
                    "tell",
                    "show",
                    "કુંડળી",
                    "કુંડલી",
                    "જન્મ",
                    "મારી",
                    "મારું",
                    "મારુ",
                    "બનાવો",
                    "બતાવો",
                    "રાશિ",
                    "રાશી",
                    "ગુજરાતી",
                    "କୁଣ୍ଡଲି",
                    "କୁଣ୍ଡଳୀ",
                    "ଜନ୍ମ",
                    "ମୋର",
                    "ପ୍ରସ୍ତୁତ",
                    "କରନ୍ତୁ",
                    "ଦେଖାନ୍ତୁ",
                    "କୁହନ୍ତୁ",
                    "ରାଶି",
                    "ଓଡ଼ିଆ",
                    "मेरी",
                    "मेरा",
                    "मुझे",
                    "जन्म",
                    "राशि",
                    "राशी",
                    "बताओ",
                    "बताएं",
                    "बताइए",
                    "बताइये",
                    "कुंडली",
                    "बनाओ",
                    "बनाएं",
                    "हिंदी",
                    "हिन्दी",
                    "ನನ್ನ",
                    "ಜನ್ಮ",
                    "ರಾಶಿ",
                    "ತಿಳಿಸಿ",
                    "ಕುಂಡಲಿ",
                    "ಲೆಕ್ಕಾಚಾರ",
                    "ಮಾಡಿ",
                    "ತೋರಿಸಿ",
                    "ಕನ್ನಡ",
                    "என்",
                    "எனது",
                    "பிறப்பு",
                    "இராசி",
                    "ராசி",
                    "குண்டலி",
                    "காட்டு",
                    "சொல்லு",
                    "தமிழ்",
                    "నా",
                    "జన్మ",
                    "రాశి",
                    "కుండలి",
                    "చూపించు",
                    "చెప్పు",
                    "తెలుగు",
                    "എന്റെ",
                    "ജനന",
                    "ജന്മ",
                    "രാശി",
                    "കുണ്ടലി",
                    "കാണിക്കുക",
                    "പറയുക",
                    "മലയാളം",
                    "माझे",
                    "माझा",
                    "माझी",
                    "जन्म",
                    "राशी",
                    "कुंडली",
                    "सांगा",
                    "दाखवा",
                    "मराठी",
                    "আমার",
                    "জন্ম",
                    "রাশি",
                    "কুণ্ডলী",
                    "বলুন",
                    "দেখান",
                    "বাংলা",
                    "ਜਨਮ",
                    "ਰਾਸ਼ੀ",
                    "ਕੁੰਡਲੀ",
                    "ਪੰਜਾਬੀ"
                ])
                if cleaned_part and not re.match(r'^\d+$', cleaned_part) and not is_noise:
                    norm_p = normalize_city_name(cleaned_part)
                    if norm_p:
                        valid_parts.append(norm_p)

            place_text = ", ".join(valid_parts) if valid_parts else "Unknown"

        result = {
            "date": date_str,
            "time": time_str,
            "place": place_text if place_text else "Unknown",
            "lang": extract_language(text)
        }
        safe_print(f"[EXTRACT] ✅ Found: {result}")
        return result

    return None

def format_time_for_api(time_str: str) -> str:
    """Ensure time format is 'HH:MM AM/PM' required by external Kundali API."""
    if not time_str:
        return "12:00 PM"
    time_str = time_str.strip()
    if re.search(r'\b(AM|PM)\b', time_str, re.IGNORECASE):
        return time_str
    match = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
    if match:
        hr = int(match.group(1))
        mn = match.group(2)
        if hr >= 12:
            hr_12 = hr if hr == 12 else hr - 12
            return f"{hr_12:02d}:{mn} PM"
        else:
            hr_12 = 12 if hr == 0 else hr
            return f"{hr_12:02d}:{mn} AM"
    return time_str


def extract_updates_to_birth_details(current_details: Dict[str, str], user_query: str) -> Tuple[Dict[str, str], bool]:
    """Check if user is providing corrections or updates to date, time, or place while payment is pending."""
    if not user_query:
        return current_details, False

    updated_details = current_details.copy()
    is_updated = False
    text = user_query.strip()

    # 1. Check Date update
    match_yyyy = re.search(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    match_dd = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b", text)
    if match_yyyy:
        y, m, d = match_yyyy.group(1), match_yyyy.group(2).zfill(2), match_yyyy.group(3).zfill(2)
        updated_details["date"] = f"{y}-{m}-{d}"
        is_updated = True
    elif match_dd:
        d, m, y = match_dd.group(1).zfill(2), match_dd.group(2).zfill(2), match_dd.group(3)
        updated_details["date"] = f"{y}-{m}-{d}"
        is_updated = True

    # 2. Check Time update
    match_time_colon = re.search(r"\b(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM|am|pm)?\b", text)
    match_time_simple = re.search(r"\b(\d{1,2})\s*(AM|PM|am|pm)\b", text)
    if match_time_colon:
        hr = int(match_time_colon.group(1))
        mn = match_time_colon.group(2)
        ampm = match_time_colon.group(3)
        if ampm:
            updated_details["time"] = f"{hr:02d}:{mn} {ampm.upper()}"
        else:
            updated_details["time"] = f"{hr:02d}:{mn} AM"
        is_updated = True
    elif match_time_simple:
        hr = int(match_time_simple.group(1))
        ampm = match_time_simple.group(2).upper()
        updated_details["time"] = f"{hr:02d}:00 {ampm}"
        is_updated = True

    # 3. Check Place update
    match_place = re.search(r'\b(?:place|location|city|place is|change place to|city is|location is)\s*[:=]?\s*([a-zA-Z\s,]+)', text, re.IGNORECASE)
    if match_place:
        raw_place = match_place.group(1).strip()
        cleaned_place = re.sub(
            r'^(?:is|to|my|the|in|at|change|correct|wrong|new|city|place|location)\s+',
            '', raw_place, flags=re.IGNORECASE
        ).strip(' :=-')
        if cleaned_place:
            updated_details["place"] = cleaned_place
            is_updated = True

    # 4. Check Language update
    new_lang = extract_language(text)
    is_lang_keyword = any(k in text.lower() for k in [
        "english", "kannada", "kanada", "hindi", "tamil", "telugu", "malayalam",
        "marathi", "gujarati", "bengali", "odia", "language", "lang"
    ])
    if is_lang_keyword or new_lang != "en":
        if updated_details.get("lang") != new_lang:
            updated_details["lang"] = new_lang
            is_updated = True
        # Ensure place is not accidentally set to a language keyword
        if updated_details.get("place", "").lower() in [
            "english", "kannada", "kanada", "hindi", "tamil", "telugu", "malayalam",
            "marathi", "gujarati", "bengali", "odia", "language", "lang"
        ]:
            updated_details["place"] = current_details.get("place", "Unknown")

    # Standalone place input (e.g. "Shikaripura" or "Shikaripura, Karnataka")
    if not is_updated and not is_lang_keyword and not match_yyyy and not match_dd and not match_time_colon and not match_time_simple:
        cleaned_text = re.sub(r'^(?:change|correct|wrong|new|my|place|city|location|is|to|in|at)\s+', '', text, flags=re.IGNORECASE).strip(' :=-')
        if cleaned_text and len(cleaned_text) >= 2 and not is_yes_response(text) and not is_no_response(text):
            if cleaned_text.lower() not in [
                "english", "kannada", "kanada", "hindi", "tamil", "telugu", "malayalam",
                "marathi", "gujarati", "bengali", "odia", "language", "lang"
            ]:
                updated_details["place"] = cleaned_text
                is_updated = True

    return updated_details, is_updated


# =============================================
# FASTAPI SETUP
# =============================================
api = FastAPI(
    title="Bharat Calendar AI API",
    description="",
    version="3.8.0"
)
app = api


api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================
# MOUNT STATIC FILES
# =============================================
if os.path.exists("static"):
    api.mount("/static", StaticFiles(directory="static"), name="static")


# =============================================
# RAZORPAY CONFIGURATION
# =============================================
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


safe_print("\n" + "="*70)
safe_print("🔐 RAZORPAY CONFIGURATION CHECK")
safe_print("="*70)
if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    safe_print("❌ ERROR: Razorpay keys NOT FOUND!")
    safe_print(f"   RAZORPAY_KEY_ID: {RAZORPAY_KEY_ID}")
    safe_print(f"   RAZORPAY_KEY_SECRET: {RAZORPAY_KEY_SECRET}")
    safe_print("\n✅ FIX: Create .env file in same folder as main.py with:")
    safe_print("   RAZORPAY_KEY_ID=your_key_here")
    safe_print("   RAZORPAY_KEY_SECRET=your_secret_here")
    safe_print("="*70)
else:
    safe_print("✅ Razorpay keys loaded successfully!")
    safe_print(f"✅ KEY ID: {RAZORPAY_KEY_ID[:20]}...")
    safe_print(f"✅ KEY SECRET: {'*' * 15}...")
    safe_print("="*70 + "\n")


razorpay_client = Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# ✅ LANGUAGE DISPLAY NAMES
LANG_DISPLAY_NAMES = {
    "en": "English",
    "kn": "Kannada",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "mr": "Marathi",
    "gu": "Gujarati",
    "bn": "Bengali",
    "or": "Odia"
}

BASE_URL = "http://127.0.0.1:8000"


def get_base_url(http_request: Optional[Request] = None) -> str:
    """Dynamically construct base URL for local, ngrok, or localtunnel host"""
    if http_request:
        scheme = http_request.headers.get("x-forwarded-proto", http_request.url.scheme)
        host = http_request.headers.get("x-forwarded-host", http_request.headers.get("host", "127.0.0.1:8000"))
        return f"{scheme}://{host}"
    return os.getenv("BASE_URL", "http://127.0.0.1:8000")



# =============================================
# SQLITE PERSISTENT STORAGE (CHATFIX-3)
# =============================================
DB_PATH = os.path.join(os.path.dirname(__file__), "payments.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_requests (
                conversation_hash TEXT,
                user_id TEXT,
                product_type TEXT,
                birth_details_json TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                order_id TEXT PRIMARY KEY,
                payment_id TEXT,
                user_id TEXT,
                product_type TEXT,
                status TEXT,
                data_json TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
    safe_print("✅ SQLite database payments.db initialized successfully!")

init_db()

def save_pending_request(conversation_hash: Optional[str], user_id: Optional[str], product_type: str, birth_details: dict, created_at: Optional[str] = None):
    if not created_at:
        created_at = datetime.now().isoformat()
    birth_details_json = json.dumps(birth_details, ensure_ascii=False)
    delete_pending_request(user_id=user_id, conversation_hash=conversation_hash)
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO pending_requests (conversation_hash, user_id, product_type, birth_details_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conversation_hash, user_id, product_type, birth_details_json, created_at)
        )
        conn.commit()

def get_pending_request(user_id: Optional[str] = None, conversation_hash: Optional[str] = None) -> Optional[dict]:
    with get_db() as conn:
        row = None
        if user_id:
            cursor = conn.execute(
                "SELECT conversation_hash, user_id, product_type, birth_details_json, created_at FROM pending_requests WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            row = cursor.fetchone()
        if not row and conversation_hash:
            cursor = conn.execute(
                "SELECT conversation_hash, user_id, product_type, birth_details_json, created_at FROM pending_requests WHERE conversation_hash = ? ORDER BY created_at DESC LIMIT 1",
                (conversation_hash,)
            )
            row = cursor.fetchone()
            
        if row:
            try:
                b_details = json.loads(row["birth_details_json"]) if row["birth_details_json"] else {}
            except Exception:
                b_details = {}
            return {
                "conversation_hash": row["conversation_hash"],
                "user_id": row["user_id"],
                "product_type": row["product_type"],
                "birth_details": b_details,
                "created_at": row["created_at"]
            }
    return None

def update_pending_request_birth_details(user_id: Optional[str], conversation_hash: Optional[str], birth_details: dict):
    birth_details_json = json.dumps(birth_details, ensure_ascii=False)
    with get_db() as conn:
        if user_id:
            conn.execute(
                "UPDATE pending_requests SET birth_details_json = ? WHERE user_id = ?",
                (birth_details_json, user_id)
            )
        if conversation_hash:
            conn.execute(
                "UPDATE pending_requests SET birth_details_json = ? WHERE conversation_hash = ?",
                (birth_details_json, conversation_hash)
            )
        conn.commit()

def delete_pending_request(user_id: Optional[str] = None, conversation_hash: Optional[str] = None):
    with get_db() as conn:
        if user_id and conversation_hash:
            conn.execute(
                "DELETE FROM pending_requests WHERE user_id = ? OR conversation_hash = ?",
                (user_id, conversation_hash)
            )
        elif user_id:
            conn.execute(
                "DELETE FROM pending_requests WHERE user_id = ?",
                (user_id,)
            )
        elif conversation_hash:
            conn.execute(
                "DELETE FROM pending_requests WHERE conversation_hash = ?",
                (conversation_hash,)
            )
        conn.commit()

def get_all_pending_requests() -> dict:
    with get_db() as conn:
        cursor = conn.execute("SELECT conversation_hash, user_id, product_type, birth_details_json, created_at FROM pending_requests")
        rows = cursor.fetchall()
        res = {}
        for r in rows:
            key = r["user_id"] if r["user_id"] else r["conversation_hash"]
            if not key:
                continue
            try:
                b_details = json.loads(r["birth_details_json"]) if r["birth_details_json"] else {}
            except Exception:
                b_details = {}
            res[key] = {
                "conversation_hash": r["conversation_hash"],
                "user_id": r["user_id"],
                "product_type": r["product_type"],
                "birth_details": b_details,
                "created_at": r["created_at"]
            }
        return res

def save_payment(order_id: str, payment_id: str, user_id: Optional[str], product_type: str, status: str, data: dict, created_at: Optional[str] = None):
    if not created_at:
        created_at = datetime.now().isoformat()
    data_json = json.dumps(data, ensure_ascii=False)
    with get_db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO payments (order_id, payment_id, user_id, product_type, status, data_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (order_id, payment_id, user_id, product_type, status, data_json, created_at)
        )
        conn.commit()

def get_payment(order_id: str) -> Optional[dict]:
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT order_id, payment_id, user_id, product_type, status, data_json, created_at FROM payments WHERE order_id = ?",
            (order_id,)
        )
        row = cursor.fetchone()
        if row:
            try:
                p_data = json.loads(row["data_json"]) if row["data_json"] else {}
            except Exception:
                p_data = {}
            return {
                "order_id": row["order_id"],
                "payment_id": row["payment_id"],
                "user_id": row["user_id"],
                "product_type": row["product_type"],
                "status": row["status"],
                "data": p_data,
                "created_at": row["created_at"]
            }
    return None

def get_payment_by_order_or_payment_id(identifier: str) -> Optional[dict]:
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT order_id, payment_id, user_id, product_type, status, data_json, created_at FROM payments WHERE order_id = ? OR payment_id = ?",
            (identifier, identifier)
        )
        row = cursor.fetchone()
        if row:
            try:
                p_data = json.loads(row["data_json"]) if row["data_json"] else {}
            except Exception:
                p_data = {}
            return {
                "order_id": row["order_id"],
                "payment_id": row["payment_id"],
                "user_id": row["user_id"],
                "product_type": row["product_type"],
                "status": row["status"],
                "data": p_data,
                "created_at": row["created_at"]
            }
    return None

def update_payment_status(order_id: str, status: str, data: Optional[dict] = None):
    with get_db() as conn:
        if data is not None:
            data_json = json.dumps(data, ensure_ascii=False)
            conn.execute(
                "UPDATE payments SET status = ?, data_json = ? WHERE order_id = ?",
                (status, data_json, order_id)
            )
        else:
            conn.execute(
                "UPDATE payments SET status = ? WHERE order_id = ?",
                (status, order_id)
            )
        conn.commit()

def get_delivered_payments_by_user(user_id: str) -> list:
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT order_id, payment_id, user_id, product_type, status, data_json, created_at FROM payments WHERE user_id = ? AND status = 'delivered' ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            try:
                p_data = json.loads(r["data_json"]) if r["data_json"] else {}
            except Exception:
                p_data = {}
            result.append({
                "order_id": r["order_id"],
                "payment_id": r["payment_id"],
                "user_id": r["user_id"],
                "product_type": r["product_type"],
                "status": r["status"],
                "date_purchased": r["created_at"],
                "created_at": r["created_at"],
                "data": p_data
            })
        return result

# Recommendation Eligibility Engine Instance
eligibility_engine = RecommendationEligibilityEngine()


# =============================================
# PYDANTIC MODELS
# =============================================
class QueryRequest(BaseModel):
    messages: List[Dict[str, Any]]
    user_id: Optional[str] = None


class PaymentVerifyRequest(BaseModel):
    order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    date: str
    time: str
    place: str
    product_type: Optional[str] = "kundali"
    lang: Optional[str] = "en"
    user_id: Optional[str] = None


# =============================================
# HELPER FUNCTIONS
# =============================================

def get_conversation_hash(messages: List[Dict[str, Any]]) -> str:
    """Create stable session hash"""
    if not messages:
        return ""
    
    first_user_message = next(
        (m["content"] for m in messages if m["role"] == "user"), 
        ""
    )
    
    if not first_user_message:
        return ""
    
    # Strip appended date context if present to maintain stable hash across turns
    clean_first_message = re.sub(r'\s*\(For context, today\'s date is.*?\)\.?', '', first_user_message, flags=re.IGNORECASE).strip()
    
    hash_obj = hashlib.md5(clean_first_message.encode())
    return hash_obj.hexdigest()[:16]


def get_current_date_context() -> str:
    """Add current date for AI context"""
    now = datetime.now()
    return f"(For context, today's date is {now.strftime('%A, %B %d, %Y')}.)"


def clean_markdown(text: str) -> str:
    """Remove markdown formatting"""
    if not text:
        return ""
    
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = text.strip()
    
    return text


def sanitize_predictive_response(text: str) -> str:
    """Strips any LLM-generated Kundali sales pitches, price/cost mentions (₹199), or payment prompts."""
    if not text:
        return ""
    
    lines = text.split("\n")
    cleaned_lines = []
    
    upsell_patterns = [
        rf"₹\s*{KUNDALI_PRICE}",
        rf"{KUNDALI_PRICE}\s*(inr|rupees|rs|\?)",
        rf"\b{KUNDALI_PRICE}\b",
        r"cost.*(kundali|report|service)",
        r"price.*(kundali|report|service)",
        r"detailed.*kundali.*report",
        r"personalized.*kundali.*report",
        r"proceed with payment",
        r"reply:?\s*yes or no",
        r"share your birth date",
        r"prepare your personalized kundali",
        r"buy.*kundali",
        r"order.*kundali",
        r"purchase.*kundali",
        r"pay.*₹",
        r"payment of ₹",
    ]
    
    for line in lines:
        line_lower = line.lower()
        if any(re.search(pat, line_lower) for pat in upsell_patterns):
            continue
        cleaned_lines.append(line)
        
    result = "\n".join(cleaned_lines).strip()
    if not result:
        result = "In Vedic astrology, planetary Dashas, transits, and house positions shape key life events. A complete birth chart analysis is required for detailed insights."
    return result


def create_razorpay_order(product_type: str, birth_details: Dict[str, str]) -> Optional[Dict]:
    """Create Razorpay order"""
    safe_print(f"\n💳 === RAZORPAY ORDER CREATION ===")
    safe_print(f"Product Type: {product_type}")
    safe_print(f"Birth Details: {birth_details}")
    
    if product_type == "janmarashi":
        amount = JANMARASHI_PRICE * 100
        safe_print(f"💰 Price: ₹{JANMARASHI_PRICE} (Janmarashi)")
    else:
        amount = KUNDALI_PRICE * 100
        safe_print(f"💰 Price: ₹{KUNDALI_PRICE} (Kundali)")
    
    try:
        order_data = {
            "amount": amount,
            "currency": "INR",
            "receipt": f"{product_type}_{uuid.uuid4().hex[:8]}",
            "notes": {
                "type": product_type,
                "birth_details": birth_details
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        safe_print(f"✅ Razorpay Order Created: {order['id']}")
        return order
    except Exception as e:
        safe_print(f"❌ Razorpay Error: {type(e).__name__}: {str(e)}")
        return None


def call_janmarashi_api(date: str, time: str, place: str, lang: str = "en") -> Optional[Dict]:
    """Call Janmarashi API"""
    try:
        safe_print(f"🔮 Calling Janmarashi API: {date}, {time}, {place}, lang={lang}")
        payload = {"date": date, "time": time, "place": place, "lang": lang.lower()}
        verify_param = BHARAT_CA_BUNDLE if BHARAT_CA_BUNDLE else True
        response = requests.post(JANMARASHI_API, json=payload, timeout=10, verify=verify_param)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                safe_print(f"✅ API Success: {data['moonRashi']}")
                return {
                    "moonRashi": data["moonRashi"],
                    "moonLongitude": data.get("moonLongitude"),
                    "location": data.get("location", {})
                }
    except Exception as e:
        safe_print(f"❌ Janmarashi API error: {e}")
    
    return None


# =============================================
# HOME ENDPOINT
# =============================================

@api.get("/")
def home():
    """Home endpoint"""
    return {
        "status": "success",
        "message": "Bharat Calendar AI API is running!",
        "version": "3.8.0",
        "endpoints": {
            "invoke": "/invoke (POST)",
            "payment_verify": "/payment/verify (POST)",
            "payment_status": "/payment/status (GET)",
            "kundali_download": "/kundali/download (GET)",
            "reports": "/reports (GET)"
        }
    }





# =============================================
# MAIN ENDPOINT - PAYMENT FLOW
# =============================================

@api.post("/invoke")
def invoke_agent(request: QueryRequest, http_request: Request):
    """Main endpoint with ENHANCED multilingual support"""
    
    user_id = request.user_id
    current_messages = request.messages.copy()
    original_user_query = current_messages[-1]["content"] if current_messages else ""
    conversation_hash = get_conversation_hash(current_messages)

    all_pending = get_all_pending_requests()

    safe_print(f"\n{'='*70}")
    safe_print(f"📍 CONVERSATION: {conversation_hash} | USER_ID: {user_id}")
    safe_print(f"📝 USER QUERY: {original_user_query[:80]}")
    safe_print(f"📊 MESSAGE COUNT: {len(current_messages)}")
    safe_print(f"⏳ PENDING REQUESTS: {list(all_pending.keys())}")
    safe_print(f"{'='*70}")

    user_response_lower = original_user_query.lower().strip()
    
    # =========================================================
    # 🔒 STRICT PAYMENT GATEKEEPER - NO LLM BYPASS ALLOWED!
    # =========================================================
    pending_data = get_pending_request(user_id=user_id, conversation_hash=conversation_hash)
    if pending_data:
        pending_key = user_id if user_id else conversation_hash
        safe_print(f"\n🔒 PENDING PAYMENT DETECTED FOR SESSION: {pending_key}")
        
        # 1. User explicitly cancelled
        if is_no_response(user_response_lower):
            safe_print(f"❌ USER CANCELLED PAYMENT")
            product_type = pending_data.get("product_type", "kundali")
            delete_pending_request(user_id=user_id, conversation_hash=conversation_hash)
            
            cancel_response = f"✅ {product_type.capitalize()} generation cancelled. Let me know if you change your mind!"
            complete_chat = current_messages + [{"role": "assistant", "content": cancel_response}]
            return {
                "messages": complete_chat,
                "recommendations": {},
                "links": {},
                "parsed_data": {},
                "tool_detected": None,
                "has_recommendations": False,
                "is_specific_query": False
            }
            
        # 2. For ANY other message while payment is pending (e.g. 'ya', 'yes', 'yup', 'sure', 'how to pay'):
        # Generate the Razorpay Order & Payment Link!
        safe_print(f"🎯 USER CONFIRMED/REQUESTED PAYMENT! (Query: '{original_user_query}')")
        current_details = pending_data["birth_details"]
        product_type = pending_data.get("product_type", "kundali")

        # 2. Check if User is updating / correcting birth details (e.g., "place shikaripura", "time 8am")
        updated_details, is_updated = extract_updates_to_birth_details(current_details, original_user_query)
        if is_updated:
            safe_print(f"✏️ BIRTH DETAILS UPDATED: {updated_details}")
            update_pending_request_birth_details(user_id=user_id, conversation_hash=conversation_hash, birth_details=updated_details)

            amount = JANMARASHI_PRICE if product_type == "janmarashi" else KUNDALI_PRICE
            product_display = "Janmarashi (Moon Sign)" if product_type == "janmarashi" else "Kundali (Birth Chart)"
            lang_display = LANG_DISPLAY_NAMES.get(updated_details.get('lang', 'en').lower(), 'English')

            content_lines = [
                "✏️ BIRTH DETAILS UPDATED",
                "",
                "✅ Updated birth details:",
                f"  📅 Date: {updated_details['date']}",
                f"  🕐 Time: {updated_details['time']}",
                f"  📍 Place: {updated_details['place']}",
                f"  🌐 Selected Language: {lang_display}",
                "",
                f"💰 Cost: ₹{amount} (One-time payment)",
                "",
                "Do you want to proceed with payment?",
                "(Reply: yes or no)"
            ]

            complete_chat = current_messages + [{"role": "assistant", "content": "\n".join(content_lines)}]
            return {
                "messages": complete_chat,
                "recommendations": {},
                "links": {},
                "parsed_data": {
                    "status": "awaiting_payment_confirmation",
                    "birth_details": updated_details,
                    "conversation_hash": conversation_hash,
                    "user_id": user_id,
                    "product_type": product_type,
                    "amount": f"₹{amount}"
                },
                "tool_detected": product_type,
                "has_recommendations": False,
                "is_specific_query": True
            }

        # 3. Check if User explicitly confirmed payment (e.g. 'yes', 'sure', 'proceed')
        if is_yes_response(user_response_lower):
            safe_print(f"🎯 USER CONFIRMED PAYMENT! (Query: '{original_user_query}')")
            birth_details = updated_details
            
            safe_print(f"Product Type: {product_type}")
            safe_print(f"Birth Details: {birth_details}")
            
            razorpay_order = create_razorpay_order(product_type, birth_details)
            
            if razorpay_order:
                order_id = razorpay_order['id']
                
                if product_type == "janmarashi":
                    amount = JANMARASHI_PRICE
                    product_display = "Janmarashi (Moon Sign)"
                else:
                    amount = KUNDALI_PRICE
                    product_display = "Kundali PDF"
                
                base_url = get_base_url(http_request)
                payment_link = f"{base_url}/static/payments.html?order_id={order_id}&key_id={RAZORPAY_KEY_ID}&product_type={product_type}&amount={amount}&date={quote(birth_details['date'])}&time={quote(birth_details['time'])}&place={quote(birth_details['place'])}&lang={quote(birth_details.get('lang', 'en'))}"
                if user_id:
                    payment_link += f"&user_id={quote(user_id)}"
                
                lang_display = LANG_DISPLAY_NAMES.get(birth_details.get('lang', 'en').lower(), 'English')
                content_lines = [
                    "🎉 PAYMENT LINK GENERATED 🎉",
                    "",
                    f"💳 Product: {product_display}",
                    f"💰 Amount: ₹{amount}",
                    "",
                    "📱 SECURE RAZORPAY PAYMENT PAGE:",
                    "",
                    "Click the link below to complete payment:",
                    f"   {payment_link}",
                    "",
                    "📋 Your Birth Details:",
                    f"   Date: {birth_details['date']}",
                    f"   Time: {birth_details['time']}",
                    f"   Place: {birth_details['place']}",
                    f"   Language: {lang_display}",
                    "",
                    f"📍 Order ID: {order_id}",
                    "",
                    "Payment Options:",
                    "✅ UPI (Recommended)",
                    "✅ Debit/Credit Card",
                    "✅ Net Banking",
                    "✅ Wallets (Paytm, PhonePe, Google Pay)"
                ]
                
                complete_chat = current_messages + [
                    {"role": "assistant", "content": "\n".join(content_lines)}
                ]
                
                # ✅ Clear pending payment request so subsequent queries (e.g. "todays panchang") aren't intercepted!
                delete_pending_request(user_id=user_id, conversation_hash=conversation_hash)
                
                return {
                    "messages": complete_chat,
                    "recommendations": {},
                    "links": {
                        "payment_link": {
                            "title": f"💳 Pay ₹{amount} - Get {product_display}",
                            "url": payment_link,
                            "order_id": order_id,
                            "type": "razorpay_payment",
                            "product_type": product_type
                        }
                    },
                    "parsed_data": {
                        "payment_status": "pending",
                        "order_id": order_id,
                        "amount": f"₹{amount}",
                        "product_type": product_type,
                        "birth_details": birth_details
                    },
                    "tool_detected": product_type,
                    "has_recommendations": False,
                    "is_specific_query": True
                }
            else:
                safe_print("❌ Razorpay order creation failed!")
                delete_pending_request(user_id=user_id, conversation_hash=conversation_hash)
                error_msg = "❌ Could not create Razorpay order. Please ensure your `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `.env` match correctly and the server has been restarted."
                complete_chat = current_messages + [{"role": "assistant", "content": error_msg}]
                return {
                    "messages": complete_chat,
                    "recommendations": {},
                    "links": {},
                    "parsed_data": {"error": "Razorpay order creation failed"},
                    "tool_detected": None,
                    "has_recommendations": False,
                    "is_specific_query": False
                }

        # 4. If query is neither Yes, No, nor an Update (e.g. user asked "todays panchang" while pending)
        safe_print(f"ℹ️ Clearing pending payment request because user asked new query: '{original_user_query}'")
        delete_pending_request(user_id=user_id, conversation_hash=conversation_hash)
    
    # ========================================
    # CASE 3: NORMAL FLOW
    # ========================================
    
    if current_messages and current_messages[-1]["role"] == "user":
        u_text = current_messages[-1]['content']
        req_lang = extract_language(u_text)
        lang_map = {
            "en": "English", "hi": "Hindi", "gu": "Gujarati", "or": "Odia",
            "kn": "Kannada", "ta": "Tamil", "te": "Telugu", "ml": "Malayalam",
            "mr": "Marathi", "bn": "Bengali"
        }
        target_lang_name = lang_map.get(req_lang, "English")
        
        is_explicit_lang_req = bool(
            re.search(r'\b(?:in|to|give|tell|translate|speak|show|write)\s+(?:english|inglesh|hindi|hindu|gujarati|gujrati|odia|oriay|kannada|kanada|tamil|telugu|malayalam|marathi|bengali)\b', u_text, flags=re.IGNORECASE)
            or any(p in u_text.lower() for p in ["in english", "in hindi", "in gujarati", "in odia", "in kannada", "give me it in english", "give it me in english", "give it in english"])
        )
        
        if is_explicit_lang_req:
            lang_directive = f" [IMPORTANT INSTRUCTION: The user explicitly requested the response in {target_lang_name}. You MUST output your complete response in {target_lang_name}. Translate any previous context or information into {target_lang_name}.]"
            current_messages[-1]["content"] = f"{u_text}{lang_directive} {get_current_date_context()}"
        else:
            current_messages[-1]["content"] = f"{u_text} {get_current_date_context()}"

    inputs = {"messages": current_messages}
    final_ai_response = ""

    print(f"\n{'='*70}")
    print("STEP 1: Getting AI Response from LangChain")
    print(f"{'='*70}")

    try:
        for event in react_agent.stream(inputs, stream_mode="values"):
            msgs = event.get("messages", [])
            if msgs:
                last_msg = msgs[-1]
                if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
                    final_ai_response = last_msg.content
    except (Exception, KeyboardInterrupt) as e:
        safe_print(f"⚠️ Agent execution interrupted: {e}")
        final_ai_response = "Request was cancelled or server was restarted."

    safe_print(f"AI Response (raw): {final_ai_response[:150]}...")
    
    clean_response = clean_markdown(final_ai_response)
    safe_print(f"AI Response (clean): {clean_response[:150]}...")

    complete_chat: List[Dict[str, str]] = current_messages + [
        {"role": "assistant", "content": clean_response}
    ]

    # ✅ USE ENHANCED MULTILINGUAL DETECTION WITH HISTORY
    tool_type = detect_tool_type_multilingual(original_user_query, final_ai_response, current_messages)
    recommendations: Dict[str, Any] = {}
    parsed_data: Dict[str, Any] = {}
    links: Dict[str, Any] = {}

    # Extract entities
    extracted_entities = {
        "rashi": extract_rashi_from_horoscope(final_ai_response, original_user_query),
        "rashi_in_query": bool(extract_rashi_from_query(original_user_query)),
        "festivals": extract_ALL_festivals_from_response(final_ai_response, original_user_query),
        "lucky_number": extract_lucky_number_from_horoscope(final_ai_response),
        "lucky_color": extract_lucky_color_from_horoscope(final_ai_response),
    }

    session_context = {
        "conversation_hash": conversation_hash,
        "user_id": user_id,
        "pending_payments": get_all_pending_requests(),
        "message_count": len(current_messages)
    }

    # Evaluate Recommendation Eligibility Engine
    decision = eligibility_engine.evaluate(
        user_query=original_user_query,
        tool_type=tool_type,
        extracted_entities=extracted_entities,
        ai_response=final_ai_response,
        session_context=session_context
    )

    safe_print(f"\n🧠 RECOMMENDATION ELIGIBILITY DECISION:")
    safe_print(f"   Should Recommend: {decision['should_recommend']}")
    safe_print(f"   Score: {decision['score']}")
    safe_print(f"   Reason: {decision['reason']}")

    safe_print(f"\n{'='*70}")
    safe_print("STEP 2: Generate Recommendations & Links")
    safe_print(f"{'='*70}")

    if tool_type == "janmarashi":
        safe_print(f"\n{'='*70}")
        safe_print("🔮 JANMARASHI FLOW - ASK FOR CONFIRMATION")
        safe_print(f"{'='*70}")

        birth_details = extract_birth_details_from_history(current_messages)
        if birth_details:
            save_pending_request(
                conversation_hash=conversation_hash,
                user_id=user_id,
                product_type="janmarashi",
                birth_details=birth_details
            )
            
            safe_print(f"✅ Stored pending janmarashi request: hash={conversation_hash}, user_id={user_id}")
            safe_print(f"📝 Birth Details: {birth_details}")

            lang_display = LANG_DISPLAY_NAMES.get(birth_details.get('lang', 'en').lower(), 'English')
            content_lines = [
                "🔮 JANMARASHI (MOON SIGN) CALCULATION",
                "",
                "✅ Birth details found:",
                f"  📅 Date: {birth_details['date']}",
                f"  🕐 Time: {birth_details['time']}",
                f"  📍 Place: {birth_details['place']}",
                f"  🌐 Selected Language: {lang_display}",
                "",
                f"💰 Cost: ₹{JANMARASHI_PRICE} (One-time payment)",
                "",
                "You will receive:",
                "  🌙 Your Janma Rashi (Moon Sign)",
                "  📊 Moon Longitude details",
                "  💎 Rashi-specific recommendations",
                "",
                "Do you want to proceed with payment?",
                "(Reply: yes or no)"
            ]
            
            complete_chat[-1]["content"] = "\n".join(content_lines)
            parsed_data = {
                "status": "awaiting_payment_confirmation",
                "birth_details": birth_details,
                "conversation_hash": conversation_hash,
                "user_id": user_id,
                "product_type": "janmarashi",
                "amount": f"₹{JANMARASHI_PRICE}"
            }
        else:
            content_lines = [
                "I’m happy to calculate your Janma Rashi (Moon Sign) for you! 🌙",
                "",
                "To calculate your Janma Rashi, please provide your birth details:",
                "1. Date of birth (e.g., 2004-04-09 or 09-04-2004)",
                "2. Time of birth (e.g., 01:00 AM or 6am)",
                "3. Place of birth (e.g., Bengaluru, Delhi, Mumbai)",
                "4. Preferred language (e.g., English, Kannada, Hindi, Tamil, Telugu, Malayalam, Marathi, Gujarati, Bengali, Odia)",
                "",
                "Example:",
                "2004-04-09, 01:00 AM, Bengaluru, English",
                "",
                f"Once you provide these details, I will set up your Janma Rashi report (₹{JANMARASHI_PRICE})."
            ]
            complete_chat[-1]["content"] = "\n".join(content_lines)

    elif tool_type == "kundali":
        safe_print(f"\n{'='*70}")
        safe_print("💳 KUNDALI FLOW - ASK FOR CONFIRMATION")
        safe_print(f"{'='*70}")

        # Check if user query references an existing completed payment ID
        existing_pay_id = None
        existing_record = None
        pid_match = re.search(r'(pay_[A-Za-z0-9]+|order_[A-Za-z0-9]+)', original_user_query)
        if pid_match:
            candidate_id = pid_match.group(1)
            pdata = get_payment_by_order_or_payment_id(candidate_id)
            if pdata and pdata.get("product_type") == "kundali":
                existing_pay_id = candidate_id
                existing_record = pdata

        if existing_pay_id and existing_record:
            safe_print(f"✅ Found existing verified Kundali payment for query: {existing_pay_id}")
            d_url = existing_record.get("data", {}).get("download_url")
            if not d_url:
                b_url = get_base_url(http_request)
                p_data = existing_record.get("data", {})
                dt = quote(p_data.get("date", ""))
                tm = quote(p_data.get("time", ""))
                pl = quote(p_data.get("place", ""))
                lg = quote(p_data.get("lang", "en"))
                d_url = f"{b_url}/kundali/download?date={dt}&time={tm}&place={pl}&payment_id={existing_pay_id}&lang={lg}"
            
            content_lines = [
                "✅ **Payment Verified!**",
                "",
                "Your Kundali (birth chart) PDF is ready for download.",
                "",
                f"🔗 **Download Link:** [Download Kundali PDF]({d_url})",
                "",
                f"Direct URL: {d_url}"
            ]
            complete_chat[-1]["content"] = "\n".join(content_lines)
            links["download_url"] = d_url
        elif pid_match and any(w in original_user_query.lower() for w in ['paid', 'download', 'payment id', 'pay_', 'order_']):
            candidate_id = pid_match.group(1)
            content_lines = [
                f"⚠️ Payment ID `{candidate_id}` was not found in completed payments.",
                "",
                "If you recently completed payment, please ensure the payment verification step was completed."
            ]
            complete_chat[-1]["content"] = "\n".join(content_lines)
        else:
            birth_details = extract_birth_details_from_history(current_messages)
            if birth_details:
                save_pending_request(
                    conversation_hash=conversation_hash,
                    user_id=user_id,
                    product_type="kundali",
                    birth_details=birth_details
                )
                
                safe_print(f"✅ Stored pending kundali request: hash={conversation_hash}, user_id={user_id}")
                safe_print(f"📝 Birth Details: {birth_details}")

                lang_display = LANG_DISPLAY_NAMES.get(birth_details.get('lang', 'en').lower(), 'English')
                content_lines = [
                    "🎯 KUNDALI GENERATION (BIRTH CHART)",
                    "",
                    "✅ Birth details found:",
                    f"  📅 Date: {birth_details['date']}",
                    f"  🕐 Time: {birth_details['time']}",
                    f"  📍 Place: {birth_details['place']}",
                    f"  🌐 Selected Language: {lang_display}",
                    "",
                    f"💰 Cost: ₹{KUNDALI_PRICE} (One-time payment)",
                    "",
                    "You will receive:",
                    "  📄 Detailed birth chart PDF",
                    "  🔍 Complete astrological analysis",
                    "  💎 Personalized insights",
                    "",
                    "Do you want to proceed with payment?",
                    "(Reply: yes or no)"
                ]
                
                complete_chat[-1]["content"] = "\n".join(content_lines)
                parsed_data = {
                    "status": "awaiting_payment_confirmation",
                    "birth_details": birth_details,
                    "conversation_hash": conversation_hash,
                    "user_id": user_id,
                    "product_type": "kundali",
                    "amount": f"₹{KUNDALI_PRICE}"
                }

            else:
                content_lines = [
                    "I’m happy to generate your Kundali (birth chart) for you! 📊",
                    "",
                    "To create your detailed Kundali report, please provide your birth details:",
                    "1. Date of birth (e.g., 2004-04-09 or 09-04-2004)",
                    "2. Time of birth (e.g., 01:00 AM or 6am)",
                    "3. Place of birth (e.g., Bengaluru, Delhi, Mumbai)",
                    "4. Preferred language (e.g., English, Kannada, Hindi, Tamil, Telugu, Malayalam, Marathi, Gujarati, Bengali, Odia)",
                    "",
                    "Example:",
                    "2004-04-09, 01:00 AM, Bengaluru, English",
                    "",
                    f"Once you provide these details, I will set up your Kundali PDF report (₹{KUNDALI_PRICE})."
                ]
                complete_chat[-1]["content"] = "\n".join(content_lines)

    elif tool_type and tool_type.startswith("predictive"):
        safe_print(f"\n{'='*70}")
        safe_print(f"🔮 PREDICTIVE FLOW - CATEGORY: {tool_type}")
        safe_print(f"{'='*70}")

        category = tool_type.replace("predictive_", "")
        
        offer_texts = {
            "marriage": f"For a detailed marriage-timing analysis based on your exact birth chart, I can prepare your personalized Kundali report (₹{KUNDALI_PRICE}). Share your birth date, time, and place.",
            "career": f"For a detailed career analysis based on your exact birth chart, I can prepare your personalized Kundali report (₹{KUNDALI_PRICE}). Share your birth date, time, and place.",
            "love": f"For a detailed relationship analysis based on your exact birth chart, I can prepare your personalized Kundali report (₹{KUNDALI_PRICE}). Share your birth date, time, and place.",
            "children": f"For a detailed children and family analysis based on your exact birth chart, I can prepare your personalized Kundali report (₹{KUNDALI_PRICE}). Share your birth date, time, and place.",
            "future": f"For a detailed personalized Kundali analysis based on your exact birth chart, I can prepare your personalized Kundali report (₹{KUNDALI_PRICE}). Share your birth date, time, and place."
        }
        
        offer_text = offer_texts.get(category, offer_texts["future"])

        # Sanitize LLM response to ensure NO duplicated sales/upsell/pricing text from LLM
        clean_response = sanitize_predictive_response(clean_response)

        if decision.get("should_recommend", True):
            links["report_upsell"] = {
                "type": "kundali_offer",
                "price": KUNDALI_PRICE,
                "cta": "Get your detailed Kundali report"
            }
            eligibility_engine.record_recommendation_served(conversation_hash, len(current_messages))
            safe_print(f"✅ Kundali report_upsell attached & recorded for conversation: {conversation_hash}")

            birth_details = extract_birth_details_from_history(current_messages)
            if birth_details:
                save_pending_request(
                    conversation_hash=conversation_hash,
                    user_id=user_id,
                    product_type="kundali",
                    birth_details=birth_details
                )
                safe_print(f"✅ Stored pending kundali request via predictive flow: hash={conversation_hash}, user_id={user_id}")

                lang_display = LANG_DISPLAY_NAMES.get(birth_details.get('lang', 'en').lower(), 'English')
                content_lines = [
                    clean_response,
                    "",
                    offer_text,
                    "",
                    "✅ Birth details found:",
                    f"  📅 Date: {birth_details['date']}",
                    f"  🕐 Time: {birth_details['time']}",
                    f"  📍 Place: {birth_details['place']}",
                    f"  🌐 Selected Language: {lang_display}",
                    "",
                    f"💰 Cost: ₹{KUNDALI_PRICE} (One-time payment)",
                    "",
                    "Do you want to proceed with payment?",
                    "(Reply: yes or no)"
                ]
                complete_chat[-1]["content"] = "\n".join(content_lines)
                parsed_data = {
                    "status": "awaiting_payment_confirmation",
                    "birth_details": birth_details,
                    "conversation_hash": conversation_hash,
                    "user_id": user_id,
                    "product_type": "kundali",
                    "amount": f"₹{KUNDALI_PRICE}"
                }
            else:
                complete_chat[-1]["content"] = f"{clean_response}\n\n{offer_text}"
        else:
            safe_print(f"ℹ️ Predictive Kundali recommendation suppressed due to eligibility/cooldown engine.")
            complete_chat[-1]["content"] = clean_response

    elif decision["should_recommend"]:
        try:
            if tool_type == "horoscope":
                recommendations = get_horoscope_recommendations(final_ai_response, original_user_query)

            elif tool_type == "panchang":
                recommendations = get_panchang_recommendations()

            elif tool_type == "monthly_festivals":
                recommendations = get_monthly_festivals_recommendations(final_ai_response, original_user_query)

            elif tool_type == "holidays":
                recommendations = get_holidays_recommendations(final_ai_response)

            else:
                if extracted_entities.get("rashi"):
                    recommendations = get_horoscope_recommendations(final_ai_response, original_user_query)
                elif extracted_entities.get("festivals"):
                    recommendations = get_monthly_festivals_recommendations(final_ai_response, original_user_query)
                else:
                    recommendations = get_panchang_recommendations()

            if recommendations:
                eligibility_engine.record_recommendation_served(conversation_hash, len(current_messages))

        except Exception as e:
            safe_print(f"❌ Error in tool processing: {e}")
    else:
        recommendations = {}

    has_recommendations = bool(recommendations) and tool_type not in ["kundali", "janmarashi"] and not (tool_type and tool_type.startswith("predictive"))

    # 🛍️ PRINT RECOMMENDED PRODUCT LINKS IN BACKEND TERMINAL IN EXACT USER SUMMARY FORMAT
    recommended_items = print_recommended_links_to_terminal(
        tool_type=tool_type,
        recommendations=recommendations,
        links=links,
        pending_requests=get_all_pending_requests()
    )

    max_prods = decision.get("max_products", 3)
    if recommended_items:
        links["recommended_products"] = [
            {
                "title": item["name"],
                "name": item["name"],
                "url": item["link"],
                "link": item["link"],
                "price": item["price"],
                "category": item["category"],
                "image": item.get("image", "")
            }
            for item in recommended_items[:max_prods]
        ]
    else:
        links["recommended_products"] = []

    return {
        "messages": complete_chat,
        "recommendations": recommendations,
        "links": links,
        "parsed_data": parsed_data,
        "tool_detected": tool_type,
        "has_recommendations": has_recommendations,
        "is_specific_query": is_astro_specific_query(original_user_query) if is_astro_specific_query else False
    }


# =============================================
# PAYMENT STATUS ENDPOINT
# =============================================

@api.get("/payment/status")
def get_payment_status(order_id: str = Query(...)):
    """Check payment status"""
    
    safe_print(f"\n📊 PAYMENT STATUS CHECK: {order_id}")
    
    payment_data = get_payment(order_id)
    if payment_data:
        safe_print(f"✅ PAYMENT FOUND IN STORAGE: {order_id}")
        
        status = payment_data.get("status", "delivered")
        
        if status == "pending_delivery" and payment_data.get("product_type") == "janmarashi":
            safe_print(f"🔄 Retrying real Janmarashi API for pending order: {order_id}")
            stored_data = payment_data.get("data", {})
            date = stored_data.get("date")
            time_val = stored_data.get("time")
            place = stored_data.get("place")
            lang = stored_data.get("lang", "en")
            
            janmarashi_data = call_janmarashi_api(date, time_val, place, lang)
            if janmarashi_data:
                rashi = janmarashi_data["moonRashi"]
                longitude = janmarashi_data.get("moonLongitude", "N/A")
                location = janmarashi_data.get("location", {}) or {}
                lat = location.get("latitude")
                lon = location.get("longitude")
                
                safe_print(f"✅ Retry succeeded! Updating status to delivered for order {order_id}")
                updated_data = {
                    "rashi": rashi,
                    "moonLongitude": longitude,
                    "latitude": lat,
                    "longitude": lon,
                    "date": date,
                    "time": time_val,
                    "place": place,
                    "lang": lang
                }
                update_payment_status(order_id, status="delivered", data=updated_data)
                
                return {
                    "success": True,
                    "payment_completed": True,
                    "status": "delivered",
                    "delivery": "delivered",
                    "order_id": order_id,
                    "product_type": payment_data.get("product_type"),
                    "data": updated_data
                }
            else:
                safe_print(f"⏳ Retry failed for order {order_id}. Remaining pending_delivery.")
                return {
                    "success": True,
                    "payment_completed": True,
                    "status": "pending_delivery",
                    "delivery": "pending",
                    "order_id": order_id,
                    "product_type": payment_data.get("product_type"),
                    "message": "Payment received! Your Janma Rashi is being calculated — check back in a few minutes."
                }
        
        return {
            "success": True,
            "payment_completed": True,
            "status": status,
            "order_id": order_id,
            "product_type": payment_data.get("product_type"),
            "data": payment_data.get("data")
        }
    
    safe_print(f"⏳ PAYMENT NOT YET COMPLETED: {order_id}")
    
    return {
        "success": False,
        "payment_completed": False,
        "order_id": order_id,
        "message": "Payment not yet completed"
    }


# =============================================
# PAYMENT VERIFICATION ENDPOINT
# =============================================

@api.post("/payment/verify")
def verify_payment(request: PaymentVerifyRequest, http_request: Request):
    """Verify Razorpay payment"""
    
    safe_print(f"\n{'='*70}")
    safe_print("💳 PAYMENT VERIFICATION STARTED")
    safe_print(f"{'='*70}")
    
    order_id = request.order_id
    payment_id = request.razorpay_payment_id
    signature = request.razorpay_signature
    date = request.date
    time = request.time
    place = request.place
    product_type = request.product_type or "kundali"
    user_id = request.user_id
    
    safe_print(f"Order ID: {order_id}")
    safe_print(f"Payment ID: {payment_id}")
    safe_print(f"User ID: {user_id}")
    safe_print(f"Product Type: {product_type}")
    safe_print(f"Birth Details: Date={date}, Time={time}, Place={place}")
    
    try:
        safe_print(f"\n🔐 Verifying payment signature...")
        
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            safe_print(f"✅ Signature verified successfully!")
        except Exception as sig_error:
            safe_print(f"❌ SIGNATURE VERIFICATION FAILED!")
            return {
                "success": False,
                "error_type": "signature_verification_failed",
                "message": "Payment verification failed: Signature mismatch"
            }
        
        if not user_id:
            pending_req = get_pending_request(user_id=None, conversation_hash=None)
            if pending_req and pending_req.get("user_id"):
                user_id = pending_req["user_id"]

        if product_type == "janmarashi":
            safe_print(f"\n📊 Preparing Janmarashi data...")
            lang = getattr(request, 'lang', 'en') or 'en'
            
            try:
                janmarashi_data = call_janmarashi_api(date, time, place, lang)
                
                if janmarashi_data:
                    rashi = janmarashi_data["moonRashi"]
                    longitude = janmarashi_data.get("moonLongitude", "N/A")
                    location = janmarashi_data.get("location", {}) or {}
                    lat = location.get("latitude")
                    lon = location.get("longitude")
                    
                    safe_print(f"✅ Janmarashi data retrieved!")
                    safe_print(f"   Rashi: {rashi}")
                    safe_print(f"   Longitude: {longitude}")
                    
                    pay_data = {
                        "rashi": rashi,
                        "moonLongitude": longitude,
                        "latitude": lat,
                        "longitude": lon,
                        "date": date,
                        "time": time,
                        "place": place,
                        "lang": lang
                    }
                    save_payment(
                        order_id=order_id,
                        payment_id=payment_id,
                        user_id=user_id,
                        product_type="janmarashi",
                        status="delivered",
                        data=pay_data
                    )
                    delete_pending_request(user_id=user_id)
                    
                    return {
                        "success": True,
                        "message": "Payment verified successfully!",
                        "product_type": "janmarashi",
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "status": "delivered",
                        "data": {
                            "rashi": rashi,
                            "moonLongitude": longitude,
                            "latitude": lat,
                            "longitude": lon,
                            "date": date,
                            "time": time,
                            "place": place
                        }
                    }
                else:
                    safe_print("⏳ Janmarashi API call failed. Storing order as pending_delivery.")
                    pay_data = {
                        "date": date,
                        "time": time,
                        "place": place,
                        "lang": lang
                    }
                    save_payment(
                        order_id=order_id,
                        payment_id=payment_id,
                        user_id=user_id,
                        product_type="janmarashi",
                        status="pending_delivery",
                        data=pay_data
                    )
                    delete_pending_request(user_id=user_id)
                    return {
                        "success": True,
                        "delivery": "pending",
                        "status": "pending_delivery",
                        "message": "Payment received! Your Janma Rashi is being calculated — check back in a few minutes.",
                        "product_type": "janmarashi",
                        "payment_id": payment_id,
                        "order_id": order_id
                    }
            except Exception as api_error:
                safe_print(f"⚠️ Janmarashi API exception ({api_error}). Storing order as pending_delivery.")
                pay_data = {
                    "date": date,
                    "time": time,
                    "place": place,
                    "lang": lang
                }
                save_payment(
                    order_id=order_id,
                    payment_id=payment_id,
                    user_id=user_id,
                    product_type="janmarashi",
                    status="pending_delivery",
                    data=pay_data
                )
                delete_pending_request(user_id=user_id)
                return {
                    "success": True,
                    "delivery": "pending",
                    "status": "pending_delivery",
                    "message": "Payment received! Your Janma Rashi is being calculated — check back in a few minutes.",
                    "product_type": "janmarashi",
                    "payment_id": payment_id,
                    "order_id": order_id
                }
        
        else:
            print(f"\n📄 Generating Kundali PDF...")
            
            lang = (getattr(request, 'lang', 'en') or "en").lower()
            formatted_time = format_time_for_api(time)
            pdf_payload = {"date": date, "time": formatted_time, "place": place, "lang": lang}
            
            try:
                verify_param = BHARAT_CA_BUNDLE if BHARAT_CA_BUNDLE else True
                pdf_response = requests.post(
                    KUNDALI_PDF_API,
                    json=pdf_payload,
                    timeout=30,
                    verify=verify_param
                )
                
                print(f"PDF API Response Status: {pdf_response.status_code}")
                
                if pdf_response.status_code != 200:
                    print(f"❌ PDF API Error Details: {pdf_response.text}")
                    pay_data = {
                        "date": date,
                        "time": time,
                        "place": place,
                        "lang": lang
                    }
                    save_payment(
                        order_id=order_id,
                        payment_id=payment_id,
                        user_id=user_id,
                        product_type="kundali",
                        status="pending_delivery",
                        data=pay_data
                    )
                    delete_pending_request(user_id=user_id)
                    return {
                        "success": False,
                        "error_type": "pdf_generation_failed",
                        "message": f"PDF generation failed (Status: {pdf_response.status_code})"
                    }
                
                pdf_size = len(pdf_response.content)
                print(f"✅ PDF generated successfully! Size: {pdf_size} bytes")
                
                try:
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    pdf_filename = f"kundali-{date}-{payment_id}.pdf"
                    pdf_path = os.path.join(temp_dir, pdf_filename)
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_response.content)
                    print(f"✅ PDF saved temporarily: {pdf_path}")
                except Exception as save_err:
                    print(f"⚠️ Note: Local temp PDF save skipped ({save_err})")
                
                base_url = get_base_url(http_request)
                download_url = f"{base_url}/kundali/download?date={quote(date)}&time={quote(time)}&place={quote(place)}&payment_id={payment_id}&lang={quote(lang)}"
                
                pay_data = {
                    "date": date,
                    "time": time,
                    "place": place,
                    "lang": lang,
                    "download_url": download_url
                }
                save_payment(
                    order_id=order_id,
                    payment_id=payment_id,
                    user_id=user_id,
                    product_type="kundali",
                    status="delivered",
                    data=pay_data
                )
                delete_pending_request(user_id=user_id)
                
                return {
                    "success": True,
                    "message": "Payment verified successfully!",
                    "product_type": "kundali",
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "status": "delivered",
                    "data": {
                        "date": date,
                        "time": time,
                        "place": place,
                        "download_url": download_url
                    }
                }
                    
            except Exception as api_error:
                print(f"❌ PDF API ERROR: {str(api_error)}")
                pay_data = {
                    "date": date,
                    "time": time,
                    "place": place,
                    "lang": lang
                }
                save_payment(
                    order_id=order_id,
                    payment_id=payment_id,
                    user_id=user_id,
                    product_type="kundali",
                    status="pending_delivery",
                    data=pay_data
                )
                delete_pending_request(user_id=user_id)
                return {
                    "success": False,
                    "error_type": "api_error",
                    "message": f"PDF generation error"
                }
            
    except Exception as e:
        print(f"❌ VERIFICATION ERROR: {type(e).__name__}: {str(e)}")
        return {
            "success": False,
            "error_type": "unknown_error",
            "message": f"Payment verification failed"
        }


# =============================================
# KUNDALI DOWNLOAD ENDPOINT
# =============================================

@api.get("/kundali/download")
def download_kundali(
    date: str = Query(...),
    time: str = Query(...),
    place: str = Query(...),
    payment_id: str = Query(...),
    lang: str = Query("en")
):
    """Download Kundali PDF - Requires Verified Payment"""
    
    safe_print(f"\n{'='*70}")
    safe_print("📥 KUNDALI PDF DOWNLOAD INITIATED")
    safe_print(f"{'='*70}")
    safe_print(f"Date: {date}, Time: {time}, Place: {place}")
    safe_print(f"Payment ID: {payment_id}")
    
    # 🔒 VERIFY THAT PAYMENT WAS COMPLETED
    pdata = get_payment_by_order_or_payment_id(payment_id)
    payment_verified = (pdata is not None and pdata.get("product_type") == "kundali")

    if not payment_verified:
        safe_print(f"❌ DOWNLOAD DENIED: Payment ID {payment_id} is not verified!")
        return Response(
            content=json.dumps({"error": "Payment verification required", "message": "Please complete Razorpay payment to download your Kundali PDF."}),
            status_code=403,
            media_type="application/json"
        )

    try:
        date = unquote(date)
        time = unquote(time)
        place = unquote(place)
        
        safe_print(f"Decoded - Date: {date}, Time: {time}, Place: {place}")
        
        formatted_time = format_time_for_api(time)
        pdf_payload = {"date": date, "time": formatted_time, "place": place, "lang": (lang or "en").lower()}
        
        try:
            verify_param = BHARAT_CA_BUNDLE if BHARAT_CA_BUNDLE else True
            pdf_response = requests.post(
                KUNDALI_PDF_API,
                json=pdf_payload,
                timeout=30,
                verify=verify_param
            )
            
            safe_print(f"PDF API Response Status: {pdf_response.status_code}")
            
            if pdf_response.status_code != 200:
                return {"error": f"PDF generation failed (Status: {pdf_response.status_code})"}
            
            pdf_content = pdf_response.content
            pdf_size = len(pdf_content)
            
            filename = f"kundali-{date}-{payment_id}.pdf"
            
            safe_print(f"✅ Sending PDF: {filename}")
            safe_print(f"   Size: {pdf_size} bytes")
            
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "application/pdf"
                }
            )
            
        except Exception as api_error:
            safe_print(f"❌ PDF API error: {str(api_error)}")
            return {"error": f"PDF generation failed: {str(api_error)}"}
            
    except Exception as e:
        safe_print(f"❌ Download error: {type(e).__name__}: {str(e)}")
        return {"error": f"Download failed: {str(e)}"}


# =============================================
# USER REPORTS ENDPOINT (CHATFIX-3)
# =============================================

@api.get("/reports")
def get_user_reports(user_id: str = Query(...)):
    """Retrieve all delivered reports for a specific user_id"""
    safe_print(f"\n📑 GET REPORTS FOR USER: {user_id}")
    if not user_id:
        return {
            "success": True,
            "user_id": user_id,
            "reports": []
        }
    reports = get_delivered_payments_by_user(user_id)
    return {
        "success": True,
        "user_id": user_id,
        "reports": reports
    }


# =============================================
# RUN SERVER
# =============================================

if __name__ == "__main__":
    import uvicorn    # pyrefly: ignore [missing-import]
