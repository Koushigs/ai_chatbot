"""
product_formatter_STRICT_FIX.py - EXACT FESTIVAL MATCHING ONLY
Fixed: No more false positives like "holi" matching in "holiday"
"""

from product_recommendations import (
    RASHI_GEMSTONES, RASHI_RUDRAKSHA, LUCKY_NUMBER_RUDRAKSHA,
    LUCKY_COLOR_PRODUCTS, PANCHANG_PRODUCTS, FESTIVAL_DEITY_IDOLS,
    FESTIVAL_DECORATIONS, FESTIVAL_AGARBATTI, WEAK_PLANET_GEMSTONES,
    DOSHA_REMEDIES, LAGNA_YANTRAS
)
import json
import re


FESTIVAL_GOD_IDOLS = {
    "DIWALI": [
        {"name": "Lakshmi Idol (Brass)", "link": "https://shop.example.com/idols/lakshmi-brass"},
    ],
    "DUSSEHRA": [
        {"name": "Durga/Kali Idol Set", "link": "https://shop.example.com/idols/durga-kali-set"},
    ],
    "JANMASHTAMI": [
        {"name": "Krishna Idol (Brass)", "link": "https://shop.example.com/idols/krishna-brass"},
    ],
    "HOLI": [
        {"name": "Radha Krishna Idol", "link": "https://shop.example.com/idols/radha-krishna"},
    ],
    "GANESH_CHATURTHI": [
        {"name": "Ganesha Idol (Large Marble)", "link": "https://shop.example.com/idols/ganesha-large-marble"},
    ],
    "RAKSHA_BANDHAN": [
        {"name": "Krishna Idol (Small)", "link": "https://shop.example.com/idols/krishna-small"},
    ],
    "MAKAR_SANKRANTI": [
        {"name": "Surya Idol (Sun God)", "link": "https://shop.example.com/idols/surya-idol"},
    ],
    "RAMA_NAVAMI": [
        {"name": "Ram Lalla Idol", "link": "https://shop.example.com/idols/ram-lalla"},
    ],
    "BUDDHA_PURNIMA": [
        {"name": "Buddha Statue (Brass)", "link": "https://shop.example.com/idols/buddha-brass"},
    ],
}

VASTU_CLEANSING_ITEMS = [
    {"name": "Wind Chime (Metal)", "link": "https://shop.example.com/vastu/wind-chime-metal"},
]

ALL_RASHI_SIGNS = ["ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
                   "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES"]


def is_astro_specific_query(user_message: str) -> bool:
    """Detect astro queries"""
    user_msg = user_message.replace(" (For context, today's date is", "").strip()
    user_lower = user_msg.lower().strip()
    
    generic_patterns = [
        r"^hi\s*$", r"^hi[,!?.\s]*$", r"^hello\s*$", r"^hello[,!?.\s]*$",
        r"^thanks\s*$", r"^thank\s+you\s*$", r"^ok\s*$",
    ]
    
    for pattern in generic_patterns:
        if re.search(pattern, user_lower):
            return False
    
    for rashi in ALL_RASHI_SIGNS:
        if user_lower == rashi.lower():
            return True
    
    astro_keywords = [
        "horoscope", "rashi", "zodiac", "panchang", "kundali", "birth chart", "janmarashi",
        "festival", "diwali", "dussehra", "holi", "navratri", "ganesh", "rakhi", "buddha",
        "holiday", "gemstone", "rudraksha", "yantra", "lucky", "prediction"
    ]
    
    for keyword in astro_keywords:
        if keyword in user_lower:
            return True
    
    return False


def extract_rashi_from_horoscope(horoscope_response: str) -> str:
    """Extract rashi"""
    try:
        response_upper = horoscope_response.upper()
        for rashi in ALL_RASHI_SIGNS:
            if f" {rashi} " in response_upper or f"**{rashi}**" in response_upper:
                return rashi
    except Exception as e:
        print(f"Error extracting rashi: {e}")
    return None


def extract_lucky_number_from_horoscope(horoscope_response: str) -> int:
    """Extract lucky number"""
    try:
        match = re.search(r"Lucky\s+Number.*?(\d+)", horoscope_response, re.IGNORECASE | re.DOTALL)
        if match:
            num = int(match.group(1))
            if 1 <= num <= 9:
                print(f"✅ Found lucky number: {num}")
                return num
        return None
    except Exception as e:
        print(f"Error extracting lucky number: {e}")
        return None


def extract_lucky_color_from_horoscope(horoscope_response: str) -> str:
    """Extract lucky color"""
    try:
        color_map = {
            "gold": "GOLD", "red": "RED", "blue": "BLUE", "green": "GREEN",
            "yellow": "YELLOW", "white": "WHITE", "pink": "PINK", "purple": "PURPLE",
            "orange": "ORANGE",
        }
        
        match = re.search(r"Lucky\s+Color.*?([A-Za-z]+)", horoscope_response, re.IGNORECASE | re.DOTALL)
        if match:
            color_word = match.group(1).lower()
            if color_word in color_map:
                result = color_map[color_word]
                print(f"✅ Found lucky color: {result}")
                return result
        
        return "GOLD"
    except Exception as e:
        print(f"Error extracting color: {e}")
        return "GOLD"


def extract_ALL_festivals_from_response(response: str) -> list:
    """
    STRICT: Extract ONLY festivals that are EXPLICITLY mentioned in response
    Use word boundaries and exact phrases to avoid false positives
    """
    print(f"\n=== EXTRACT FESTIVALS (STRICT) ===")
    
    # Use regex with word boundaries to match exact festivals
    # This avoids matching "holi" in "holiday", etc.
    festival_patterns = [
        (r"\bdiwali\b", "DIWALI"),
        (r"\bdussehra\b", "DUSSEHRA"),
        (r"\bvijaya dashami\b", "DUSSEHRA"),
        (r"\bholi\b", "HOLI"),
        (r"\bjanmashtami\b", "JANMASHTAMI"),
        (r"\bganesh chaturthi\b", "GANESH_CHATURTHI"),
        (r"\braksha bandhan\b", "RAKSHA_BANDHAN"),
        (r"\bmakar sankranti\b", "MAKAR_SANKRANTI"),
        (r"\bram navami\b", "RAMA_NAVAMI"),
        (r"\bbuddha purnima\b", "BUDDHA_PURNIMA"),
    ]
    
    found_festivals = []
    response_lower = response.lower()
    
    for pattern, festival_key in festival_patterns:
        if re.search(pattern, response_lower, re.IGNORECASE):
            if festival_key not in found_festivals:
                found_festivals.append(festival_key)
                print(f"  ✅ Found: {festival_key} (pattern: {pattern})")
    
    print(f"Total festivals: {len(found_festivals)}")
    print(f"=== END ===\n")
    
    return found_festivals


def get_horoscope_recommendations(horoscope_response: str) -> dict:
    """Get horoscope recommendations"""
    print("\n" + "="*60)
    print("GET HOROSCOPE RECOMMENDATIONS")
    print("="*60)
    
    rashi = extract_rashi_from_horoscope(horoscope_response)
    lucky_number = extract_lucky_number_from_horoscope(horoscope_response)
    lucky_color = extract_lucky_color_from_horoscope(horoscope_response)
    
    recommendations = {"gemstone": None, "lucky_number_rudraksha": None, "lucky_color_product": None}
    
    if rashi and rashi in RASHI_GEMSTONES:
        gem_data = RASHI_GEMSTONES[rashi]
        recommendations["gemstone"] = {
            "name": f"{gem_data['gemstone']} (for {rashi})",
            "benefits": gem_data['benefits'],
            "price_range": gem_data['price_range'],
            "link": gem_data['products'][0]['link']
        }
    
    if lucky_number is not None and lucky_number in LUCKY_NUMBER_RUDRAKSHA:
        rec = LUCKY_NUMBER_RUDRAKSHA[lucky_number]
        recommendations["lucky_number_rudraksha"] = {
            "name": f"{rec['description']}",
            "link": rec['link']
        }
    
    if lucky_color and lucky_color in LUCKY_COLOR_PRODUCTS:
        recommendations["lucky_color_product"] = {
            "name": f"{lucky_color} Color Items",
            "link": LUCKY_COLOR_PRODUCTS[lucky_color][0]['link']
        }
    
    print("="*60)
    return recommendations


def get_panchang_recommendations() -> dict:
    """Get panchang recommendations"""
    return {
        "products": [
            {"name": PANCHANG_PRODUCTS[0]['name'], "link": PANCHANG_PRODUCTS[0]['link']},
            {"name": "Puja Essentials Kit", "link": "https://shop.example.com/puja/essentials-kit"},
            {"name": "Vastu Cleansing Item: Wind Chime", "link": VASTU_CLEANSING_ITEMS[0]['link']}
        ]
    }


def get_holidays_recommendations(holidays_list: str = None) -> dict:
    """Get holidays recommendations - NO RECOMMENDATIONS"""
    return {}


def get_monthly_festivals_recommendations(monthly_response: str = None) -> dict:
    """
    Get monthly festival recommendations - STRICT MATCHING ONLY
    """
    print("\n" + "="*60)
    print("GET MONTHLY FESTIVALS RECOMMENDATIONS")
    print("="*60)
    
    # Use STRICT extraction - only festivals explicitly mentioned
    festivals = extract_ALL_festivals_from_response(monthly_response if monthly_response else "")
    
    recommendations = {
        "festival_gods": [],
        "decoration_kit": None,
        "puja_kit": None
    }
    
    # Add ONLY festivals that were found
    for festival in festivals:
        if festival in FESTIVAL_GOD_IDOLS:
            god = FESTIVAL_GOD_IDOLS[festival][0]
            recommendations["festival_gods"].append({
                "festival": festival,
                "name": god['name'],
                "link": god['link']
            })
            print(f"✅ Added {festival}: {god['name']}")
    
    # If no festivals found, don't add generic
    # This is important - if user asks for "October festivals" and no matches, show nothing
    
    if recommendations["festival_gods"]:  # Only add if festivals found
        recommendations["decoration_kit"] = {
            "name": "Festival Decoration Kit (Lights, Garland, Diyas)",
            "link": "https://shop.example.com/decoration/festival-kit"
        }
        
        recommendations["puja_kit"] = {
            "name": "Complete Puja Essentials Kit (Agarbatti, Dhoop, Kumkum, Haldi)",
            "link": "https://shop.example.com/puja/essentials-complete-kit"
        }
    
    print("="*60)
    return recommendations


def get_kundali_recommendations(kundali_response: str) -> dict:
    """Get kundali recommendations"""
    recommendations = {"weak_planet_gemstone": None, "dosha_remedy": None, "lagna_yantra": None}
    try:
        response_text = kundali_response.upper()
        planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU"]
        
        for planet in planets:
            if f"WEAK {planet}" in response_text:
                if planet in WEAK_PLANET_GEMSTONES:
                    gem_data = WEAK_PLANET_GEMSTONES[planet]
                    recommendations["weak_planet_gemstone"] = {
                        "planet": planet,
                        "gemstone": gem_data['gemstone'],
                        "benefits": gem_data['benefits'],
                        "link": gem_data['link']
                    }
                    break
        
        for rashi in LAGNA_YANTRAS.keys():
            if rashi in response_text:
                recommendations["lagna_yantra"] = LAGNA_YANTRAS[rashi]
                break
        
        if not recommendations["lagna_yantra"]:
            recommendations["lagna_yantra"] = LAGNA_YANTRAS["LEO"]
    except Exception as e:
        print(f"Error in kundali: {e}")
    
    return recommendations


def get_janmarashi_recommendations(janmarashi_response: str) -> dict:
    """Get janmarashi recommendations"""
    rashi = extract_rashi_from_horoscope(janmarashi_response)
    if not rashi:
        rashi = "LEO"
    
    recommendations = {"gemstone": None, "rudraksha": None, "yantra": None}
    
    if rashi in RASHI_GEMSTONES:
        gem_data = RASHI_GEMSTONES[rashi]
        recommendations["gemstone"] = {
            "name": f"{gem_data['gemstone']} (for {rashi})",
            "benefits": gem_data['benefits'],
            "link": gem_data['products'][0]['link']
        }
    
    if rashi in RASHI_RUDRAKSHA:
        rud_data = RASHI_RUDRAKSHA[rashi]
        recommendations["rudraksha"] = {"name": f"{rud_data['description']}", "link": rud_data['link']}
    
    if rashi in LAGNA_YANTRAS:
        recommendations["yantra"] = LAGNA_YANTRAS[rashi]
    
    return recommendations


def format_recommendations_html(tool_type: str, recommendations: dict) -> str:
    """Format recommendations as HTML"""
    
    html = """
    <div style="margin-top: 20px; padding: 15px; background: #f0f8ff; border-left: 4px solid #667eea; border-radius: 5px;">
    <h3>🛍️ Recommended Products for You:</h3>
    """
    
    if tool_type == "horoscope":
        if recommendations.get("gemstone"):
            html += f"""<div style="margin: 10px 0;"><strong>💎 Gemstone:</strong> {recommendations['gemstone']['name']}<br>
            <em>{recommendations['gemstone']['benefits']}</em><br>Price: {recommendations['gemstone']['price_range']}<br>
            <a href='{recommendations['gemstone']['link']}' target='_blank' style='color: #667eea;'>→ Shop Now</a></div>"""
        
        if recommendations.get("lucky_number_rudraksha"):
            html += f"""<div style="margin: 10px 0;"><strong>🔢 Lucky Number Rudraksha:</strong> {recommendations['lucky_number_rudraksha']['name']}<br>
            <a href='{recommendations['lucky_number_rudraksha']['link']}' target='_blank' style='color: #667eea;'>→ Shop Now</a></div>"""
        
        if recommendations.get("lucky_color_product"):
            html += f"""<div style="margin: 10px 0;"><strong>🎨 Lucky Color:</strong> {recommendations['lucky_color_product']['name']}<br>
            <a href='{recommendations['lucky_color_product']['link']}' target='_blank' style='color: #667eea;'>→ Shop Now</a></div>"""
    
    elif tool_type == "panchang":
        for product in recommendations.get("products", []):
            html += f"""<div style="margin: 10px 0;"><strong>📅 {product['name']}</strong><br>
            <a href='{product['link']}' target='_blank' style='color: #667eea;'>→ Shop Now</a></div>"""
    
    elif tool_type == "holidays":
        html = ""
    
    elif tool_type == "monthly_festivals":
        if recommendations.get("festival_gods"):
            for god in recommendations['festival_gods']:
                html += f"""<div style="margin: 10px 0;"><strong>🛕 {god['festival']} - God Idol:</strong> {god['name']}<br>
                <a href='{god['link']}' target='_blank' style='color: #667eea;'>→ Shop Now</a></div>"""
        
        if recommendations.get("decoration_kit"):
            html += f"""<div style="margin: 10px 0;"><strong>✨ Decoration Kit:</strong> {recommendations['decoration_kit']['name']}<br>
            <a href='{recommendations['decoration_kit']['link']}' target='_blank' style='color: #667eea;'>→ Shop Now</a></div>"""
        
        if recommendations.get("puja_kit"):
            html += f"""<div style="margin: 10px 0;"><strong>🕯️ Puja Kit:</strong> {recommendations['puja_kit']['name']}<br>
            <a href='{recommendations['puja_kit']['link']}' target='_blank' style='color: #667eea;'>→ Shop Now</a></div>"""
    
    elif tool_type == "kundali":
        if recommendations.get("weak_planet_gemstone"):
            html += f"""<div style="margin: 10px 0;"><strong>💎 Weak Planet ({recommendations['weak_planet_gemstone']['planet']}):</strong> {recommendations['weak_planet_gemstone']['gemstone']}<br>
            <a href='{recommendations['weak_planet_gemstone']['link']}' target='_blank' style='color: #667eea;'>→ Shop Now</a></div>"""
    
    elif tool_type == "janmarashi":
        if recommendations.get("gemstone"):
            html += f"""<div style="margin: 10px 0;"><strong>💎 Gemstone:</strong> {recommendations['gemstone']['name']}<br>
            <a href='{recommendations['gemstone']['link']}' target='_blank' style='color: #667eea;'>→ Shop Now</a></div>"""
    
    if html and html != "":
        html += """<br><em style="font-size: 12px; color: #999;">💡 Note: These are astrological recommendations.</em></div>"""
    
    return html