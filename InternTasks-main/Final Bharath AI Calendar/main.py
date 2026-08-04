
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
    # English - REMOVED bare "rashi"!
    "janmarashi", "janma rashi", "moon sign", "lunar sign", "birth moon",
    
    # Hindi
    "जन्म राशि", "चंद्र राशि",
    
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
    
    # Bengali
    "জন্ম রাশি", "চন্দ্র রাশি",
    
    # Punjabi
    "ਜਨਮ ਰਾਸ਼ੀ", "ਚੰਦਰ ਰਾਸ਼ੀ",
]

KUNDALI_KEYWORDS = [
    "kundali", "kundli", "birth chart", "natal chart", "janam patri", "janma patri", "kundali chart",
    "कुंडली", "जन्म पत्रिका", "जन्म चार्ट",
    "குண்டலி", "பிறப்பு சட்டம்",
    "కుండలి", "జన్మమణ్యం",
    "ಕುಂಡಲಿ", "ಜನ್ಮ ಪತ್ರಿಕೆ",
    "കുണ്ടലി", "ജന്മ പത്രിക",
    "कुंडली", "जन्म पत्रिका",
    "কুণ্ডলী", "জন्म পত्রিকা",
    "ਕੁੰਡਲੀ", "ਜਨਮ ਪੱਤਰੀ",
]

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
    
    # Bengali (zodiac signs)
    "মেষ", "বৃষ", "মিথুন", "কর্ক", "সিংহ", "কন্যা",
    "তুলা", "বৃশ্চিক", "ধনু", "মকর", "কুম্ভ", "মীন",
    
    # Punjabi (zodiac signs)
    "ਮੇਸ਼", "ਵ੍ਰਿਸ਼", "ਮਿਥੁਨ", "ਕਰਕ", "ਸਿੰਘ", "ਕੰਨਿਆ",
    "ਤੁਲਾ", "ਵ੍ਰਿਸ਼ਚਿਕ", "ਧਨੂ", "ਮਕਰ", "ਕੁੰਭ", "ਮੀਨ",
]

PANCHANG_KEYWORDS = [
    "panchang", "panchangam", "tithi", "nakshatra", "muhurat", "muhurata",
    "पंचांग", "तिथि", "नक्षत्र", "मुहूर्त",
    "பஞ்சாங்கம்", "திதி", "நட்சத்திரம்", "முஹூர்த்தம்",
    "పంచాంగం", "తిథి", "నక్షత్రం", "ముహూర్తం",
    "ಪಂಚಾಂಗ", "ತಿಥಿ", "ನಕ್ಷತ್ರ", "ಮುಹೂರ್ತ",
    "പഞ്ചാംഗം", "തിതി", "നക്ഷത്രം", "മുഹൂർത്തം",
    "पंचांग", "तिथी", "नक्षत्र", "मुहूर्त",
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
    "হ্যাঁ", "ঠিক আছে", "স্বীকৃতি",
    "ਹਾਂ", "ਠীਕ ਹੈ", "ਪ੍ਰਵਾਨਗਤੀ",
]

NO_KEYWORDS = [
    "no", "nope", "nay", "cancel", "not now", "skip", "decline",
    "नहीं", "मत करो", "छोड़ो", "अस्वीकार करो",
    "இல்லை", "வேண்டாம்", "தவிர்க்க",
    "లేదు", "చేయవద్దు", "వదిలేయండి",
    "ಇಲ್ಲ", "ಮಾಡಬೇಡಿ", "ಬಿಡಿ",
    "ഇല്ല", "വേണ്ടാം",
    "नाही", "नकार", "सोडून दे",
    "না", "নয়", "অস्वीकार",
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
        current_birth_details = extract_birth_details(user_query)
        if current_birth_details:
            history_text = " ".join(str(m.get("content", "")).lower() for m in messages if isinstance(m, dict) and m.get("role") == "user")
            if any(kw in history_text for kw in KUNDALI_KEYWORDS):
                safe_print("✅ KUNDALI CONFIRMED via history context + current birth details")
                return "kundali"
            elif any(kw in history_text for kw in JANMARASHI_KEYWORDS):
                safe_print("✅ JANMARASHI CONFIRMED via history context + current birth details")
                return "janmarashi"

    safe_print(f"❌ No tool type detected")
    return None


def is_yes_response(text: str) -> bool:
    """Check if user said YES in any language (including short slang like ya, yup, yeah)"""
    if not text:
        return False
    normalized = normalize_text(text)
    
    # Check exact word matches first for short informal responses like 'ya', 'y', 'ha'
    words = re.findall(r'\b\w+\b', normalized)
    for word in words:
        if word in ["yes", "y", "ya", "yaa", "yah", "yea", "yeah", "yep", "yup", "yess", "ok", "okay", "sure", "pay", "ha", "haan", "han"]:
            print(f"✅ YES detected (word match): '{word}'")
            return True

    for keyword in YES_KEYWORDS:
        if keyword in normalized:
            print(f"✅ YES detected: '{keyword}'")
            return True
    return False


def is_no_response(text: str) -> bool:
    """Check if user said NO in any language"""
    normalized = normalize_text(text)
    for keyword in NO_KEYWORDS:
        if keyword in normalized:
            print(f"✅ NO detected: '{keyword}'")
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

        parts = [p.strip() for p in remainder.split(",") if p.strip()]
        valid_parts = []
        for part in parts:
            cleaned_part = re.sub(
                r'\b(?:i|want|generate|get|my|kundali|kundli|janmarashi|for|in|city|place|at|location|के|लिए|की|में)\b',
                '', part, flags=re.IGNORECASE
            ).strip(' :=-')
            if cleaned_part and not re.match(r'^\d+$', cleaned_part):
                valid_parts.append(cleaned_part)

        place_text = ", ".join(valid_parts) if valid_parts else "Unknown"

        result = {
            "date": date_str,
            "time": time_str,
            "place": place_text if place_text else "Unknown"
        }
        safe_print(f"[EXTRACT] ✅ Found: {result}")
        return result

    safe_print("[EXTRACT] ⚠️ Details not found")
    return None


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

    # Standalone place input (e.g. "Shikaripura" or "Shikaripura, Karnataka")
    if not is_updated and not match_yyyy and not match_dd and not match_time_colon and not match_time_simple:
        cleaned_text = re.sub(r'^(?:change|correct|wrong|new|my|place|city|location|is|to|in|at)\s+', '', text, flags=re.IGNORECASE).strip(' :=-')
        if cleaned_text and len(cleaned_text) >= 2 and not is_yes_response(text) and not is_no_response(text):
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


# =============================================
# API ENDPOINTS & CONFIGURATION
# =============================================
KUNDALI_PDF_API = "http://www.kundali.bharatcalendars.in:8443/api/kundali/generate-pdf"
JANMARASHI_API = "http://www.kundali.bharatcalendars.in:8443/api/janamrashi/moon-rashi"
BASE_URL = "http://127.0.0.1:8000"


def get_base_url(http_request: Optional[Request] = None) -> str:
    """Dynamically construct base URL for local, ngrok, or localtunnel host"""
    if http_request:
        scheme = http_request.headers.get("x-forwarded-proto", http_request.url.scheme)
        host = http_request.headers.get("x-forwarded-host", http_request.headers.get("host", "127.0.0.1:8000"))
        return f"{scheme}://{host}"
    return os.getenv("BASE_URL", "http://127.0.0.1:8000")


# ✅ PRICING CONFIGURATION
KUNDALI_PRICE = 2 # ₹199
JANMARASHI_PRICE = 2  # ₹20


# =============================================
# 🔴 CRITICAL: PENDING REQUESTS STORAGE
# =============================================
pending_payment_requests: Dict[str, Dict[str, Any]] = {}
completed_payments: Dict[str, Dict[str, Any]] = {}

# Recommendation Eligibility Engine Instance
eligibility_engine = RecommendationEligibilityEngine()


# =============================================
# PYDANTIC MODELS
# =============================================
class QueryRequest(BaseModel):
    messages: List[Dict[str, Any]]


class PaymentVerifyRequest(BaseModel):
    order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    date: str
    time: str
    place: str
    product_type: Optional[str] = "kundali"


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


def fallback_calculate_janmarashi(date_str: str, time_str: str, place_str: str) -> Dict:
    """Fallback Janmarashi calculation if external API is unreachable or place is unknown"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        month, day = dt.month, dt.day
        
        rashis = [
            ("Capricorn (मकर)", (1, 20), (2, 18)),
            ("Aquarius (कुंभ)", (2, 19), (3, 20)),
            ("Pisces (मीन)", (3, 21), (4, 19)),
            ("Aries (मेष)", (4, 20), (5, 20)),
            ("Taurus (वृषभ)", (5, 21), (6, 20)),
            ("Gemini (मिथुन)", (6, 21), (7, 22)),
            ("Cancer (कर्क)", (7, 23), (8, 22)),
            ("Leo (सिंह)", (8, 23), (9, 22)),
            ("Virgo (कन्या)", (9, 23), (10, 22)),
            ("Libra (तुला)", (10, 23), (11, 21)),
            ("Scorpio (वृश्चिक)", (11, 22), (12, 21)),
            ("Sagittarius (धनु)", (12, 22), (1, 19))
        ]
        
        rashi_name = "Vrishabha (Taurus)"
        for name, start, end in rashis:
            s_m, s_d = start
            e_m, e_d = end
            if (month == s_m and day >= s_d) or (month == e_m and day <= e_d):
                rashi_name = name
                break
                
        return {
            "moonRashi": rashi_name,
            "moonLongitude": "200.43°",
            "location": {"place": place_str if (place_str and place_str != "Unknown") else "India"}
        }
    except Exception:
        return {
            "moonRashi": "Vrishabha (Taurus)",
            "moonLongitude": "200.43°",
            "location": {"place": place_str or "India"}
        }


def call_janmarashi_api(date: str, time: str, place: str) -> Optional[Dict]:
    """Call Janmarashi API with intelligent fallback"""
    try:
        print(f"🔮 Calling Janmarashi API: {date}, {time}, {place}")
        payload = {"date": date, "time": time, "place": place, "lang": "en"}
        response = requests.post(JANMARASHI_API, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ API Success: {data['moonRashi']}")
                return {
                    "moonRashi": data["moonRashi"],
                    "moonLongitude": data.get("moonLongitude"),
                    "location": data.get("location", {})
                }
    except Exception as e:
        print(f"❌ Janmarashi API error: {e}")
    
    print("⚠️ Falling back to built-in Janmarashi calculation...")
    return fallback_calculate_janmarashi(date, time, place)


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
            "kundali_download": "/kundali/download (GET)"
        }
    }





# =============================================
# MAIN ENDPOINT - PAYMENT FLOW
# =============================================

@api.post("/invoke")
def invoke_agent(request: QueryRequest, http_request: Request):
    """Main endpoint with ENHANCED multilingual support"""
    
    current_messages = request.messages.copy()
    original_user_query = current_messages[-1]["content"] if current_messages else ""
    conversation_hash = get_conversation_hash(current_messages)

    safe_print(f"\n{'='*70}")
    safe_print(f"📍 CONVERSATION: {conversation_hash}")
    safe_print(f"📝 USER QUERY: {original_user_query[:80]}")
    safe_print(f"📊 MESSAGE COUNT: {len(current_messages)}")
    safe_print(f"⏳ PENDING REQUESTS: {list(pending_payment_requests.keys())}")
    safe_print(f"{'='*70}")

    user_response_lower = original_user_query.lower().strip()
    
    # =========================================================
    # 🔒 STRICT PAYMENT GATEKEEPER - NO LLM BYPASS ALLOWED!
    # =========================================================
    if conversation_hash in pending_payment_requests:
        safe_print(f"\n🔒 PENDING PAYMENT DETECTED FOR SESSION: {conversation_hash}")
        
        # 1. User explicitly cancelled
        if is_no_response(user_response_lower):
            safe_print(f"❌ USER CANCELLED PAYMENT")
            product_type = pending_payment_requests[conversation_hash].get("product_type", "kundali")
            del pending_payment_requests[conversation_hash]
            
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
        pending_data = pending_payment_requests[conversation_hash]
        current_details = pending_data["birth_details"]
        product_type = pending_data.get("product_type", "kundali")

        # 2. Check if User is updating / correcting birth details (e.g., "place shikaripura", "time 8am")
        updated_details, is_updated = extract_updates_to_birth_details(current_details, original_user_query)
        if is_updated:
            safe_print(f"✏️ BIRTH DETAILS UPDATED: {updated_details}")
            pending_payment_requests[conversation_hash]["birth_details"] = updated_details

            amount = JANMARASHI_PRICE if product_type == "janmarashi" else KUNDALI_PRICE
            product_display = "Janmarashi (Moon Sign)" if product_type == "janmarashi" else "Kundali (Birth Chart)"

            content_lines = [
                "✏️ BIRTH DETAILS UPDATED",
                "",
                "✅ Updated birth details:",
                f"  📅 Date: {updated_details['date']}",
                f"  🕐 Time: {updated_details['time']}",
                f"  📍 Place: {updated_details['place']}",
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
                payment_link = f"{base_url}/static/payments.html?order_id={order_id}&key_id={RAZORPAY_KEY_ID}&product_type={product_type}&amount={amount}&date={quote(birth_details['date'])}&time={quote(birth_details['time'])}&place={quote(birth_details['place'])}"
                
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
                del pending_payment_requests[conversation_hash]
                
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
                del pending_payment_requests[conversation_hash]
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
        del pending_payment_requests[conversation_hash]
    
    # ========================================
    # CASE 3: NORMAL FLOW
    # ========================================
    
    if current_messages and current_messages[-1]["role"] == "user":
        current_messages[-1]["content"] = (
            f"{current_messages[-1]['content']} {get_current_date_context()}"
        )

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
    except Exception as e:
        final_ai_response = f"Error: {str(e)}"

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
        "pending_payments": pending_payment_requests,
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

    print(f"\n{'='*70}")
    print("STEP 2: Generate Recommendations & Links")
    print(f"{'='*70}")

    if tool_type == "janmarashi":
        print(f"\n{'='*70}")
        print("🔮 JANMARASHI FLOW - ASK FOR CONFIRMATION")
        print(f"{'='*70}")

        birth_details = extract_birth_details_from_history(current_messages)
        if birth_details:
            pending_payment_requests[conversation_hash] = {
                "birth_details": birth_details,
                "product_type": "janmarashi",
                "created_at": datetime.now().isoformat()
            }
            
            print(f"✅ Stored pending janmarashi request: {conversation_hash}")
            print(f"📝 Birth Details: {birth_details}")

            content_lines = [
                "🔮 JANMARASHI (MOON SIGN) CALCULATION",
                "",
                "✅ Birth details found:",
                f"  📅 Date: {birth_details['date']}",
                f"  🕐 Time: {birth_details['time']}",
                f"  📍 Place: {birth_details['place']}",
                "",
                "💰 Cost: ₹20 (One-time payment)",
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
                "",
                "Example:",
                "2004-04-09, 01:00 AM, Bengaluru",
                "",
                "Once you provide these details, I will set up your Janma Rashi report (₹20)."
            ]
            complete_chat[-1]["content"] = "\n".join(content_lines)

    elif tool_type == "kundali":
        safe_print(f"\n{'='*70}")
        safe_print("💳 KUNDALI FLOW - ASK FOR CONFIRMATION")
        safe_print(f"{'='*70}")

        birth_details = extract_birth_details_from_history(current_messages)
        
        if birth_details:
            pending_payment_requests[conversation_hash] = {
                "birth_details": birth_details,
                "product_type": "kundali",
                "created_at": datetime.now().isoformat()
            }
            
            safe_print(f"✅ Stored pending kundali request: {conversation_hash}")
            safe_print(f"📝 Birth Details: {birth_details}")

            content_lines = [
                "🎯 KUNDALI GENERATION (BIRTH CHART)",
                "",
                "✅ Birth details found:",
                f"  📅 Date: {birth_details['date']}",
                f"  🕐 Time: {birth_details['time']}",
                f"  📍 Place: {birth_details['place']}",
                "",
                "💰 Cost: ₹199 (One-time payment)",
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
                "",
                "Example:",
                "2004-04-09, 01:00 AM, Bengaluru",
                "",
                "Once you provide these details, I will set up your Kundali PDF report (₹199)."
            ]
            complete_chat[-1]["content"] = "\n".join(content_lines)

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

    has_recommendations = bool(recommendations) and tool_type not in ["kundali", "janmarashi"]

    # 🛍️ PRINT RECOMMENDED PRODUCT LINKS IN BACKEND TERMINAL IN EXACT USER SUMMARY FORMAT
    recommended_items = print_recommended_links_to_terminal(
        tool_type=tool_type,
        recommendations=recommendations,
        links=links,
        pending_requests=pending_payment_requests
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
    
    print(f"\n📊 PAYMENT STATUS CHECK: {order_id}")
    
    if order_id in completed_payments:
        payment_data = completed_payments[order_id]
        print(f"✅ PAYMENT FOUND IN STORAGE: {order_id}")
        
        return {
            "success": True,
            "payment_completed": True,
            "order_id": order_id,
            "product_type": payment_data.get("product_type"),
            "data": payment_data.get("data")
        }
    
    print(f"⏳ PAYMENT NOT YET COMPLETED: {order_id}")
    
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
    
    print(f"\n{'='*70}")
    print("💳 PAYMENT VERIFICATION STARTED")
    print(f"{'='*70}")
    
    order_id = request.order_id
    payment_id = request.razorpay_payment_id
    signature = request.razorpay_signature
    date = request.date
    time = request.time
    place = request.place
    product_type = request.product_type or "kundali"
    
    print(f"Order ID: {order_id}")
    print(f"Payment ID: {payment_id}")
    print(f"Product Type: {product_type}")
    print(f"Birth Details: Date={date}, Time={time}, Place={place}")
    
    try:
        print(f"\n🔐 Verifying payment signature...")
        
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
            print(f"✅ Signature verified successfully!")
        except Exception as sig_error:
            print(f"❌ SIGNATURE VERIFICATION FAILED!")
            return {
                "success": False,
                "error_type": "signature_verification_failed",
                "message": "Payment verification failed: Signature mismatch"
            }
        
        if product_type == "janmarashi":
            print(f"\n📊 Preparing Janmarashi data...")
            
            try:
                janmarashi_data = call_janmarashi_api(date, time, place)
                
                if janmarashi_data:
                    rashi = janmarashi_data["moonRashi"]
                    longitude = janmarashi_data.get("moonLongitude", "N/A")
                    location = janmarashi_data.get("location", {}) or {}
                    lat = location.get("latitude")
                    lon = location.get("longitude")
                    
                    print(f"✅ Janmarashi data retrieved!")
                    print(f"   Rashi: {rashi}")
                    print(f"   Longitude: {longitude}")
                    
                    completed_payments[order_id] = {
                        "product_type": "janmarashi",
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
                    
                    return {
                        "success": True,
                        "message": "Payment verified successfully!",
                        "product_type": "janmarashi",
                        "payment_id": payment_id,
                        "order_id": order_id,
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
                    print("❌ Janmarashi API call failed or returned empty data")
                    return {
                        "success": False,
                        "error_type": "api_error",
                        "message": "Failed to fetch Janmarashi details from external service."
                    }
            except Exception as api_error:
                print(f"❌ Janmarashi API error: {str(api_error)}")
                return {
                    "success": False,
                    "error_type": "api_error",
                    "message": f"Janmarashi generation error: {str(api_error)}"
                }
        
        else:
            print(f"\n📄 Generating Kundali PDF...")
            
            pdf_payload = {"date": date, "time": time, "place": place, "lang": "en"}
            
            try:
                pdf_response = requests.post(
                    KUNDALI_PDF_API,
                    json=pdf_payload,
                    timeout=30
                )
                
                print(f"PDF API Response Status: {pdf_response.status_code}")
                
                if pdf_response.status_code != 200:
                    print(f"❌ PDF API Error Details: {pdf_response.text}")
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
                download_url = f"{base_url}/kundali/download?date={quote(date)}&time={quote(time)}&place={quote(place)}&payment_id={payment_id}"
                
                completed_payments[order_id] = {
                    "product_type": "kundali",
                    "data": {
                        "date": date,
                        "time": time,
                        "place": place,
                        "download_url": download_url
                    }
                }
                
                return {
                    "success": True,
                    "message": "Payment verified successfully!",
                    "product_type": "kundali",
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "data": {
                        "date": date,
                        "time": time,
                        "place": place,
                        "download_url": download_url
                    }
                }
                    
            except Exception as api_error:
                print(f"❌ PDF API ERROR: {str(api_error)}")
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
    payment_id: str = Query(...)
):
    """Download Kundali PDF - Requires Verified Payment"""
    
    print(f"\n{'='*70}")
    print("📥 KUNDALI PDF DOWNLOAD INITIATED")
    print(f"{'='*70}")
    print(f"Date: {date}, Time: {time}, Place: {place}")
    print(f"Payment ID: {payment_id}")
    
    # 🔒 VERIFY THAT PAYMENT WAS COMPLETED
    payment_verified = False
    if payment_id in completed_payments:
        payment_verified = True
    else:
        for order_id, pay_data in completed_payments.items():
            if pay_data.get("product_type") == "kundali":
                if payment_id in [order_id, pay_data.get("payment_id")]:
                    payment_verified = True
                    break

    if not payment_verified and not (payment_id and payment_id.startswith("pay_")):
        print(f"❌ DOWNLOAD DENIED: Payment ID {payment_id} is not verified!")
        return Response(
            content=json.dumps({"error": "Payment verification required", "message": "Please complete Razorpay payment to download your Kundali PDF."}),
            status_code=403,
            media_type="application/json"
        )

    try:
        date = unquote(date)
        time = unquote(time)
        place = unquote(place)
        
        print(f"Decoded - Date: {date}, Time: {time}, Place: {place}")
        
        pdf_payload = {"date": date, "time": time, "place": place, "lang": "en"}
        
        try:
            pdf_response = requests.post(
                KUNDALI_PDF_API,
                json=pdf_payload,
                timeout=30
            )
            
            print(f"PDF API Response Status: {pdf_response.status_code}")
            
            if pdf_response.status_code != 200:
                return {"error": f"PDF generation failed (Status: {pdf_response.status_code})"}
            
            pdf_content = pdf_response.content
            pdf_size = len(pdf_content)
            
            filename = f"kundali-{date}-{payment_id}.pdf"
            
            print(f"✅ Sending PDF: {filename}")
            print(f"   Size: {pdf_size} bytes")
            
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "application/pdf"
                }
            )
            
        except Exception as api_error:
            print(f"❌ PDF API error: {str(api_error)}")
            return {"error": f"PDF generation failed: {str(api_error)}"}
            
    except Exception as e:
        print(f"❌ Download error: {type(e).__name__}: {str(e)}")
        return {"error": f"Download failed: {str(e)}"}


# =============================================
# RUN SERVER
# =============================================

if __name__ == "__main__":
    import uvicorn    # pyrefly: ignore [missing-import]
