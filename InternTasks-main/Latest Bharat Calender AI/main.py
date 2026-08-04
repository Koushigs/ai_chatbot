# main.py - CLEAN PLAIN TEXT + BEAUTIFUL RECOMMENDATIONS

from fastapi import FastAPI, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from agent import app
from datetime import datetime
from langchain_core.messages import AIMessage
from product_formatter import (
    get_horoscope_recommendations, get_panchang_recommendations,
    get_holidays_recommendations, get_monthly_festivals_recommendations,
    get_janmarashi_recommendations, format_recommendations_html,
    is_astro_specific_query
)
import requests
import re
from urllib.parse import urlencode
import html


api = FastAPI(
    title="Bharat Calendar AI API",
    description="",
    version="3.3.4"
)


api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


KUNDALI_PDF_API = "https://www.kundali.bharatcalendars.in:5000/api/kundali/generate-pdf"
JANMARASHI_API = "https://www.kundali.bharatcalendars.in:5000/api/janamrashi/moon-rashi"
BASE_URL = "http://127.0.0.1:8000"


class QueryRequest(BaseModel):
    messages: List[Dict[str, Any]]


def get_current_date_context() -> str:
    now = datetime.now()
    return f"(For context, today's date is {now.strftime('%A, %B %d, %Y')}.)"


def clean_markdown(text: str) -> str:
    """✅ Remove ALL markdown formatting for clean plain text display"""
    if not text:
        return ""
    
    # Remove **bold**, *italic*, __bold__, _italic_
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    
    # Remove headers #, ##, ### 
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Remove inline code `code`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Clean multiple newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text


def extract_birth_details(text: str) -> Optional[Dict[str, str]]:
    print(f"\n[EXTRACT] Parsing text for birth details: {text[:100]}...")

    date_pattern = r"(\d{4}-\d{2}-\d{2})"
    time_pattern = r"(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))"
    place_pattern = r",\s*([A-Za-z\s]+?)(?:\(|,|$)"

    date_match = re.search(date_pattern, text)
    time_match = re.search(time_pattern, text)
    place_match = re.search(place_pattern, text)

    if date_match and time_match and place_match:
        result = {
            "date": date_match.group(1),
            "time": time_match.group(1),
            "place": place_match.group(1).strip()
        }
        print(f"[EXTRACT] ✅ Found: {result}")
        return result

    print("[EXTRACT] ⚠️ Could not fully extract details")
    return None


def call_janmarashi_api(date: str, time: str, place: str) -> Optional[Dict]:
    try:
        print(f"🔮 Calling Janmarashi API: {date}, {time}, {place}")
        payload = {"date": date, "time": time, "place": place}
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
    return None


def get_rashi_recommendations(rashi: str) -> Dict[str, Any]:
    recommendations_map = {
        "Leo": {
            "gemstone": {
                "name": "Ruby (for LEO)",
                "benefits": "Boosts confidence, leadership, and health",
                "price_range": "₹2000-10000",
                "link": "https://shop.example.com/gemstones/ruby-burma"
            },
            "lucky_number_rudraksha": {
                "name": "7 Mukhi Rudraksha",
                "link": "https://shop.example.com/rudraksha/7-mukhi"
            },
            "lucky_color_product": {
                "name": "GOLD Color Items",
                "link": "https://shop.example.com/colors/gold-items"
            }
        },
        "Pisces": {
            "gemstone": {
                "name": "Yellow Sapphire (for Pisces)",
                "benefits": "Enhances wisdom, prosperity, and spiritual growth",
                "price_range": "₹3000-15000",
                "link": "https://shop.example.com/gemstones/yellow-sapphire"
            },
            "lucky_color_product": {
                "name": "Yellow Color Items (for Pisces)",
                "link": "https://shop.example.com/colors/yellow-items"
            }
        },
        "Scorpio": {
            "gemstone": {
                "name": "Red Coral (for Scorpio)",
                "benefits": "Enhances courage, vitality, and protection",
                "price_range": "₹1500-8000",
                "link": "https://shop.example.com/gemstones/red-coral"
            },
            "lucky_color_product": {
                "name": "Red Color Items (for Scorpio)",
                "link": "https://shop.example.com/colors/red-items"
            }
        }
    }
    return recommendations_map.get(rashi, {
        "gemstone": {
            "name": f"Gemstone (for {rashi})",
            "link": "https://shop.example.com/gemstones"
        }
    })


def detect_tool_type(user_query: str, ai_response: str) -> Optional[str]:
    user_lower = user_query.lower()

    print(f"\n{'='*60}")
    print("DETECT TOOL TYPE")
    print(f"User Query: {user_lower[:80]}...")

    if "kundali" in user_lower or "kundli" in user_lower or "birth chart" in user_lower:
        print("✅ DETECTED: KUNDALI")
        return "kundali"

    if "janmarashi" in user_lower or "janma rashi" in user_lower or "moon sign" in user_lower:
        print("✅ DETECTED: JANMARASHI")
        return "janmarashi"

    rashi_names = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    ]
    for rashi in rashi_names:
        if rashi in user_lower:
            print(f"✅ DETECTED: HOROSCOPE ({rashi})")
            return "horoscope"

    if "panchang" in user_lower or "muhurat" in user_lower:
        print("✅ DETECTED: PANCHANG")
        return "panchang"

    festival_keywords = ["festival", "diwali", "dussehra", "holi", "navratri"]
    for keyword in festival_keywords:
        if keyword in user_lower:
            print("✅ DETECTED: MONTHLY_FESTIVALS")
            return "monthly_festivals"

    if "holiday" in user_lower:
        print("✅ DETECTED: HOLIDAYS")
        return "holidays"

    print("⚠️ UNKNOWN TOOL TYPE")
    return None


@api.post("/invoke")
def invoke_agent(request: QueryRequest):
    

    current_messages = request.messages.copy()
    original_user_query = current_messages[-1]["content"] if current_messages else ""

    if len(current_messages) == 1 and current_messages[0]["role"] == "user":
        current_messages[0]["content"] = (
            f"{current_messages[0]['content']} {get_current_date_context()}"
        )

    inputs = {"messages": current_messages}
    final_ai_response = ""

    print(f"\n{'='*60}")
    print("STEP 1: Getting AI Response")
    print(f"{'='*60}")

    try:
        for event in app.stream(inputs, stream_mode="values"):
            msgs = event.get("messages", [])
            if msgs:
                last_msg = msgs[-1]
                if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
                    final_ai_response = last_msg.content
    except Exception as e:
        final_ai_response = f"Error: {str(e)}"

    print(f"AI Response (raw): {final_ai_response[:150]}...")
    
    # ✅ CLEAN: Remove markdown formatting for beautiful plain text
    clean_response = clean_markdown(final_ai_response)
    print(f"AI Response (clean): {clean_response[:150]}...")

    complete_chat: List[Dict[str, str]] = current_messages + [
        {"role": "assistant", "content": clean_response}
    ]

    tool_type = detect_tool_type(original_user_query, final_ai_response)
    recommendations: Dict[str, Any] = {}
    parsed_data: Dict[str, Any] = {}
    links: Dict[str, Any] = {}

    print(f"\n{'='*60}")
    print("STEP 2: Generate Content + Recommendations + Links")
    print(f"{'='*60}")

    if tool_type:
        try:
            if tool_type == "horoscope":
                recommendations = get_horoscope_recommendations(final_ai_response)

            elif tool_type == "panchang":
                recommendations = get_panchang_recommendations()

            elif tool_type == "monthly_festivals":
                recommendations = get_monthly_festivals_recommendations(final_ai_response)

            elif tool_type == "holidays":
                recommendations = get_holidays_recommendations(final_ai_response)

            elif tool_type == "janmarashi":
                print(f"\n{'='*60}")
                print("🔮 JANMARASHI - BEAUTIFULLY FORMATTED")
                print(f"{'='*60}")

                birth_details = extract_birth_details(original_user_query)
                if birth_details:
                    janmarashi_data = call_janmarashi_api(
                        birth_details["date"],
                        birth_details["time"],
                        birth_details["place"]
                    )

                    if janmarashi_data:
                        rashi = janmarashi_data["moonRashi"]
                        place_full = janmarashi_data["location"].get("place", birth_details["place"])
                        longitude = janmarashi_data.get("moonLongitude", "N/A")
                        lat = janmarashi_data["location"].get("latitude", "N/A")
                        long = janmarashi_data["location"].get("longitude", "N/A")

                        content_lines = [
                            f"Your Janma Rashi (Moon Sign): {rashi}",
                            "",
                            "Birth Details:",
                            f"  Date: {birth_details['date']}",
                            f"  Time: {birth_details['time']}",
                            f"  Place: {place_full}",
                            f"  Latitude: {lat}",
                            f"  Longitude: {long}",
                            "",
                            f"Moon Longitude: {longitude}°",
                            "",
                            f"{rashi} Characteristics:",
                            "  Element: Water",
                            "  Ruling Planet: Jupiter",
                            "  Lucky Colors: Yellow, White",
                            "  Lucky Stone: Yellow Sapphire"
                        ]

                        complete_chat[-1]["content"] = "\n".join(content_lines)

                        rashi_recos = get_rashi_recommendations(rashi)
                        recommendations = rashi_recos
                else:
                    content_lines = [
                        "Please provide birth details:",
                        "  Date (YYYY-MM-DD)",
                        "  Time (HH:MM AM/PM)",
                        "  Place",
                        "",
                        "Example: Generate janmarashi for 2001-08-09, 01:00 AM, Bengaluru"
                    ]
                    complete_chat[-1]["content"] = "\n".join(content_lines)

            elif tool_type == "kundali":
                print(f"\n{'='*60}")
                print("📊 KUNDALI - BEAUTIFULLY FORMATTED")
                print(f"{'='*60}")

                birth_details = extract_birth_details(original_user_query)
                if birth_details:
                    query = urlencode({
                        "date": birth_details["date"],
                        "time": birth_details["time"],
                        "place": birth_details["place"]
                    })
                    download_url = f"{BASE_URL}/kundali/download?{query}"

                    content_lines = [
                        "Your Kundali is Ready!",
                        "",
                        "Birth Details:",
                        f"  Date: {birth_details['date']}",
                        f"  Time: {birth_details['time']}",
                        f"  Place: {birth_details['place']}",
                        "",
                        "Use the separate 'links' section below to download your Kundali PDF."
                    ]
                    complete_chat[-1]["content"] = "\n".join(content_lines)

                    links = {
                        "kundali_pdf": {
                            "title": "📄 Download Kundali PDF",
                            "url": download_url
                        }
                    }

                    recommendations = {}
                else:
                    content_lines = [
                        "Please provide Kundali details:",
                        "  Date (YYYY-MM-DD)",
                        "  Time (HH:MM AM/PM)",
                        "  Place",
                        "",
                        "Example: Generate kundali for 2001-08-09, 01:00 AM, Bengaluru"
                    ]
                    complete_chat[-1]["content"] = "\n".join(content_lines)

        except Exception as e:
            print(f"❌ Error: {e}")

    has_recommendations = bool(recommendations) and tool_type != "kundali"

    print(f"\n{'='*60}")
    print(f"✅ Tool: {tool_type} | Recommendations: {has_recommendations} | Links: {bool(links)}")
    print(f"✅ Final clean content length: {len(complete_chat[-1]['content'])} chars")

    return {
        "messages": complete_chat,
        "recommendations": recommendations,
        "links": links,
        "parsed_data": parsed_data,
        "tool_detected": tool_type,
        "has_recommendations": has_recommendations,
        "is_specific_query": is_astro_specific_query(original_user_query)
    }


@api.get("/kundali/download")
def download_kundali(
    date: str = Query(..., description="YYYY-MM-DD"),
    time: str = Query(..., description="HH:MM AM/PM"),
    place: str = Query(..., description="Place of birth")
):
    payload = {"date": date, "time": time, "place": place}
    try:
        print("\n📥 /kundali/download:", payload)
        pdf_response = requests.post(
            KUNDALI_PDF_API,
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        if pdf_response.status_code == 200 and len(pdf_response.content) > 100:
            filename = f"kundali_{date.replace('-', '')}.pdf"
            return Response(
                content=pdf_response.content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        return Response(
            content=f"PDF generation failed (status {pdf_response.status_code})",
            media_type="text/plain",
            status_code=500
        )
    except Exception as e:
        return Response(
            content=f"Error: {e}",
            media_type="text/plain",
            status_code=500
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="127.0.0.1", port=8000)
