"""
product_formatter.py - Dynamic Affiliate Product Formatter
Matches user queries to live products fetched from https://api.bharatcalendars.in:5200/affiliate/allItems
"""

from product_recommendations import (
    RASHI_GEMSTONES, RASHI_RUDRAKSHA, LUCKY_NUMBER_RUDRAKSHA,
    LUCKY_COLOR_PRODUCTS, PANCHANG_PRODUCTS, FESTIVAL_DEITY_IDOLS,
    FESTIVAL_DECORATIONS, FESTIVAL_AGARBATTI, WEAK_PLANET_GEMSTONES,
    DOSHA_REMEDIES, LAGNA_YANTRAS
)
from affiliate_products import (
    get_deity_idol_product, get_panchang_product, get_festival_products,
    get_gemstone_product, get_rudraksha_product, get_yantra_product,
    product_manager
)
from typing import Optional, Dict, List, Tuple
import json
import re


FESTIVAL_GOD_IDOLS = {
    "DIWALI": [get_deity_idol_product("Lakshmi")],
    "DUSSEHRA": [get_deity_idol_product("Durga")],
    "JANMASHTAMI": [get_deity_idol_product("Krishna")],
    "HOLI": [get_deity_idol_product("Krishna")],
    "GANESH_CHATURTHI": [get_deity_idol_product("Ganesha")],
    "RAKSHA_BANDHAN": [get_deity_idol_product("Krishna")],
    "MAKAR_SANKRANTI": [get_deity_idol_product("Surya")],
    "RAMA_NAVAMI": [get_deity_idol_product("Ram Lalla")],
    "BUDDHA_PURNIMA": [get_deity_idol_product("Buddha")],
    "NAVRATRI": [get_deity_idol_product("Durga")],
}

VASTU_CLEANSING_ITEMS = [
    product_manager.search_product(["Wind Chime", "Vastu", "Tree"], default_name="Vastu Cleansing Wind Chime")
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


def extract_rashi_from_query(user_query: str) -> Optional[str]:
    """Check if user's query explicitly specifies a Rashi sign."""
    if not user_query:
        return None
    user_upper = user_query.upper()
    for rashi in ALL_RASHI_SIGNS:
        if re.search(rf"\b{rashi}\b", user_upper, re.IGNORECASE):
            return rashi
            
    synonym_map = {
        "MESH": "ARIES", "MESHA": "ARIES", "मेष": "ARIES",
        "VRISHABH": "TAURUS", "VRISHABHA": "TAURUS", "VRISH": "TAURUS", "वृषभ": "TAURUS",
        "MITHUN": "GEMINI", "MITHUNA": "GEMINI", "मिथुन": "GEMINI",
        "KARK": "CANCER", "KARKA": "CANCER", "कर्क": "CANCER",
        "SIMHA": "LEO", "SINGH": "LEO", "सिंह": "LEO",
        "KANYA": "VIRGO", "कन्या": "VIRGO",
        "TULA": "LIBRA", "तुला": "LIBRA",
        "VRISCHIK": "SCORPIO", "VRISCHIKA": "SCORPIO", "वृश्चिक": "SCORPIO",
        "DHANU": "SAGITTARIUS", "DHANUS": "SAGITTARIUS", "धनु": "SAGITTARIUS",
        "MAKAR": "CAPRICORN", "MAKARA": "CAPRICORN", "मकर": "CAPRICORN",
        "KUMBH": "AQUARIUS", "KUMBHA": "AQUARIUS", "कुंभ": "AQUARIUS",
        "MEEN": "PISCES", "MEENA": "PISCES", "मीन": "PISCES"
    }
    for synonym, rashi_std in synonym_map.items():
        if re.search(rf"\b{re.escape(synonym)}\b", user_upper, re.IGNORECASE):
            return rashi_std
    return None


def extract_rashi_from_horoscope(horoscope_response: str, user_query: str = "") -> str:
    """Extract rashi using word boundary regex from response or user query"""
    try:
        query_rashi = extract_rashi_from_query(user_query)
        if query_rashi:
            print(f"[OK] Extracted Rashi from query: {query_rashi}")
            return query_rashi
            
        combined_text = (user_query + " " + horoscope_response).upper()
        for rashi in ALL_RASHI_SIGNS:
            if re.search(rf"\b{rashi}\b", combined_text, re.IGNORECASE):
                print(f"[OK] Extracted Rashi: {rashi}")
                return rashi
    except Exception as e:
        print(f"Error extracting rashi: {e}")
    return None


def extract_lucky_number_from_horoscope(horoscope_response: str) -> int:
    """Extract lucky number and reduce to single digit 1-9 if needed"""
    try:
        match = re.search(r"Lucky\s+Number[^\d]*(\d+)", horoscope_response, re.IGNORECASE | re.DOTALL)
        if match:
            num = int(match.group(1))
            while num > 9:
                num = sum(int(digit) for digit in str(num))
            if 1 <= num <= 9:
                print(f"[OK] Found lucky number: {num}")
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
        
        match = re.search(r"Lucky\s+Color[^A-Za-z]*([A-Za-z]+)", horoscope_response, re.IGNORECASE | re.DOTALL)
        if match:
            color_word = match.group(1).lower()
            if color_word in color_map:
                result = color_map[color_word]
                print(f"[OK] Found lucky color: {result}")
                return result
        
        for color_key, color_val in color_map.items():
            if re.search(rf"\b{color_key}\b", horoscope_response, re.IGNORECASE):
                return color_val

        return "GOLD"
    except Exception as e:
        print(f"Error extracting color: {e}")
        return "GOLD"


def extract_ALL_festivals_from_response(response: str, user_query: str = "") -> list:
    """Extract festivals explicitly mentioned in response or user query"""
    print(f"\n=== EXTRACT FESTIVALS ===")
    
    festival_patterns = [
        (r"\bdiwali\b|\bdeepavali\b", "DIWALI"),
        (r"\bdussehra\b|\bvijaya dashami\b|\bdasara\b", "DUSSEHRA"),
        (r"\bholi\b", "HOLI"),
        (r"\bjanmashtami\b|\bkrishna janmashtami\b", "JANMASHTAMI"),
        (r"\bganesh\b|\bganesha\b|\bvinayaka\b", "GANESH_CHATURTHI"),
        (r"\brakhi\b|\braksha bandhan\b", "RAKSHA_BANDHAN"),
        (r"\bmakar sankranti\b|\bsankranti\b|\bpongal\b", "MAKAR_SANKRANTI"),
        (r"\bram navami\b|\brama navami\b", "RAMA_NAVAMI"),
        (r"\bbuddha purnima\b|\bbuddha jayanti\b", "BUDDHA_PURNIMA"),
        (r"\bnavratri\b|\bnavratras\b|\bnavarathri\b|\bnavarathir\b|\bnavrathri\b|\bdurga puja\b", "NAVRATRI"),
    ]
    
    found_festivals = []
    combined_text = (user_query + " " + (response or "")).lower()
    
    for pattern, festival_key in festival_patterns:
        if re.search(pattern, combined_text, re.IGNORECASE):
            if festival_key not in found_festivals:
                found_festivals.append(festival_key)
                print(f"  [OK] Found: {festival_key} (pattern: {pattern})")
    
    print(f"Total festivals: {len(found_festivals)}")
    print(f"=== END ===\n")
    
    return found_festivals


def get_horoscope_recommendations(horoscope_response: str, user_query: str = "") -> dict:
    """Get horoscope recommendations"""
    print("\n" + "="*60)
    print("GET HOROSCOPE RECOMMENDATIONS")
    print("="*60)
    
    rashi = extract_rashi_from_horoscope(horoscope_response, user_query)
    lucky_number = extract_lucky_number_from_horoscope(horoscope_response)
    lucky_color = extract_lucky_color_from_horoscope(horoscope_response)
    
    recommendations = {"gemstone": None, "lucky_number_rudraksha": None, "lucky_color_product": None}
    
    if rashi and rashi in RASHI_GEMSTONES:
        gem_data = RASHI_GEMSTONES[rashi]
        product = gem_data['products'][0]
        real_title = product.get("name") or gem_data['gemstone']
        recommendations["gemstone"] = {
            "name": f"{real_title} (for {rashi})",
            "benefits": gem_data['benefits'],
            "price_range": product.get("price") or gem_data['price_range'],
            "link": product['link'],
            "title": real_title,
            "image": product.get("image", "")
        }
    
    if lucky_number is not None and lucky_number in LUCKY_NUMBER_RUDRAKSHA:
        rec = LUCKY_NUMBER_RUDRAKSHA[lucky_number]
        real_rud_title = rec.get("name") or rec['description']
        rud_item = {
            "name": f"{real_rud_title}",
            "link": rec['link'],
            "title": real_rud_title,
            "price": rec.get("price", ""),
            "image": rec.get("image", "")
        }
        recommendations["lucky_number_rudraksha"] = rud_item
        recommendations["rudraksha"] = rud_item
    elif rashi and rashi in RASHI_RUDRAKSHA:
        rud_data = RASHI_RUDRAKSHA[rashi]
        real_rud_title = rud_data.get("name") or rud_data['description']
        rud_item = {
            "name": f"{real_rud_title} (for {rashi})",
            "link": rud_data['link'],
            "title": real_rud_title,
            "price": rud_data.get("price", ""),
            "image": rud_data.get("image", "")
        }
        recommendations["lucky_number_rudraksha"] = rud_item
        recommendations["rudraksha"] = rud_item
    
    if lucky_color and lucky_color in LUCKY_COLOR_PRODUCTS:
        col_prod = LUCKY_COLOR_PRODUCTS[lucky_color][0]
        real_col_title = col_prod.get("name") or f"{lucky_color} Color Item"
        recommendations["lucky_color_product"] = {
            "name": f"{real_col_title}",
            "link": col_prod['link'],
            "title": real_col_title,
            "price": col_prod.get("price", ""),
            "image": col_prod.get("image", "")
        }
    
    print("="*60)
    return recommendations


def get_panchang_recommendations() -> dict:
    """Get panchang recommendations - ONLY Panchang Calendar/Almanac product"""
    return {
        "products": [
            {
                "name": PANCHANG_PRODUCTS[0]['name'],
                "link": PANCHANG_PRODUCTS[0]['link'],
                "price": PANCHANG_PRODUCTS[0].get('price', ''),
                "image": PANCHANG_PRODUCTS[0].get('image', '')
            }
        ]
    }


def get_holidays_recommendations(holidays_list: str = None) -> dict:
    """Get holidays recommendations - NO RECOMMENDATIONS"""
    return {}


def get_monthly_festivals_recommendations(monthly_response: str = None, user_query: str = "") -> dict:
    """Get monthly festival recommendations"""
    print("\n" + "="*60)
    print("GET MONTHLY FESTIVALS RECOMMENDATIONS")
    print("="*60)
    
    festivals = extract_ALL_festivals_from_response(monthly_response, user_query)
    
    recommendations = {
        "festival_gods": [],
        "decoration_kit": None,
        "puja_kit": None
    }
    
    for festival in festivals:
        if festival in FESTIVAL_GOD_IDOLS:
            god = FESTIVAL_GOD_IDOLS[festival][0]
            recommendations["festival_gods"].append({
                "festival": festival,
                "name": god['name'],
                "link": god['link'],
                "price": god.get("price", ""),
                "image": god.get("image", "")
            })
            print(f"[OK] Added {festival}: {god['name']}")
    
    if recommendations["festival_gods"]:
        fest_prods = get_festival_products(festivals[0] if festivals else "DIWALI")
        recommendations["decoration_kit"] = {
            "name": fest_prods["decor"]["name"],
            "link": fest_prods["decor"]["link"],
            "price": fest_prods["decor"].get("price", ""),
            "image": fest_prods["decor"].get("image", "")
        }
        
        recommendations["puja_kit"] = {
            "name": fest_prods["puja"]["name"],
            "link": fest_prods["puja"]["link"],
            "price": fest_prods["puja"].get("price", ""),
            "image": fest_prods["puja"].get("image", "")
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
                        "name": gem_data['name'],
                        "link": gem_data['link'],
                        "price": gem_data.get("price", ""),
                        "image": gem_data.get("image", "")
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


def get_janmarashi_recommendations(janmarashi_response: str, user_query: str = "") -> dict:
    """Get janmarashi recommendations"""
    rashi = extract_rashi_from_horoscope(janmarashi_response, user_query)
    if not rashi:
        rashi = "LEO"
    
    recommendations = {"gemstone": None, "rudraksha": None, "yantra": None}
    
    if rashi in RASHI_GEMSTONES:
        gem_data = RASHI_GEMSTONES[rashi]
        product = gem_data['products'][0]
        recommendations["gemstone"] = {
            "name": f"{gem_data['gemstone']} (for {rashi})",
            "benefits": gem_data['benefits'],
            "link": product['link'],
            "title": product['name'],
            "price": product.get("price", ""),
            "image": product.get("image", "")
        }
    
    if rashi in RASHI_RUDRAKSHA:
        rud_data = RASHI_RUDRAKSHA[rashi]
        recommendations["rudraksha"] = {
            "name": f"{rud_data['description']}",
            "link": rud_data['link'],
            "title": rud_data.get('name'),
            "price": rud_data.get("price", ""),
            "image": rud_data.get("image", "")
        }
    
    if rashi in LAGNA_YANTRAS:
        recommendations["yantra"] = LAGNA_YANTRAS[rashi]
    
    return recommendations


def format_recommendations_html(tool_type: str, recommendations: dict) -> str:
    """Format recommendations as rich HTML with images and real prices (Strictly Deduplicated)"""
    items = extract_recommended_links(tool_type, recommendations)
    if not items:
        return ""
    
    html = """
    <div style="margin-top: 20px; padding: 15px; background: #f0f8ff; border-left: 4px solid #667eea; border-radius: 8px;">
    <h3 style="margin-top:0; color:#2b6cb0;">🛍️ Recommended Products for You:</h3>
    """
    
    for item in items:
        display_name = item.get("name") or "Product"
        short_name = display_name[:36] + "..." if len(display_name) > 36 else display_name
        image_url = item.get("image", "")
        img_html = f"<img src='{image_url}' alt='{display_name}' style='width:40px; height:40px; max-width:40px; max-height:40px; object-fit:cover; border-radius:8px; margin-right:12px; flex-shrink:0;' />" if image_url else ""
        price = item.get("price", "")
        price_html = f"<span style='color: #2b6cb0; font-weight:bold; font-size:12px;'>{price}</span>" if price and price != "N/A" else ""
        link = item.get("link", "https://www.amazon.in/")
        
        html += f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin: 8px 0; padding:8px 12px; background:#ffffff; border:1px solid #eef0ff; border-radius:10px; width:100%; box-sizing:border-box;">
            <div style="display:flex; align-items:center; gap:12px; flex:1; min-width:0; overflow:hidden;">
                {img_html}
                <div style="display:flex; flex-direction:column; justify-content:center; overflow:hidden; flex:1; min-width:0;">
                    <span title="{display_name}" style="font-size:13px; font-weight:600; color:#333; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; display:block;">{short_name}</span>
                    {price_html}
                </div>
            </div>
            <a href='{link}' target='_blank' style='display:inline-flex; align-items:center; gap:4px; color: #fff; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding:6px 14px; border-radius:18px; text-decoration:none; font-size:11px; font-weight:bold; flex-shrink:0;'>🛒 Buy Now</a>
        </div>
        """
    
    html += """<em style="font-size: 11px; color: #718096; display:block; margin-top:8px;">💡 Note: Products fetched live from Bharat Calendars Affiliate Store.</em></div>"""
    return html


def _is_quality_product(prod: dict) -> bool:
    """Validate product quality: must have non-empty affiliate link, image, and price."""
    if not isinstance(prod, dict):
        return False
    link = prod.get("link") or prod.get("url")
    price = prod.get("price") or prod.get("price_range")
    image = prod.get("image")
    has_link = bool(link and str(link).strip())
    has_price = bool(price and str(price).strip() and str(price) != "N/A")
    has_image = bool(image and str(image).strip())
    return has_link and has_price and has_image


def extract_recommended_links(tool_type: str, recommendations: dict) -> list:
    """
    Extract flat list of recommended product link dicts matching quality criteria.
    Deduplicates URLs and dynamically returns up to 3 relevant product links.
    """
    items = []
    if not recommendations or not isinstance(recommendations, dict):
        return items

    if tool_type == "horoscope":
        for key in ["gemstone", "lucky_number_rudraksha", "lucky_color_product", "rudraksha"]:
            prod = recommendations.get(key)
            if prod and isinstance(prod, dict) and _is_quality_product(prod):
                items.append({
                    "name": prod.get("title") or prod.get("name") or "Product",
                    "link": prod.get("link"),
                    "price": prod.get("price_range") or prod.get("price") or "N/A",
                    "category": key,
                    "image": prod.get("image", "")
                })

    elif tool_type == "panchang":
        for prod in recommendations.get("products", []):
            if isinstance(prod, dict) and _is_quality_product(prod):
                items.append({
                    "name": prod.get("title") or prod.get("name") or "Product",
                    "link": prod.get("link"),
                    "price": prod.get("price") or "N/A",
                    "category": "panchang_product",
                    "image": prod.get("image", "")
                })

    elif tool_type == "monthly_festivals":
        for god in recommendations.get("festival_gods", []):
            if isinstance(god, dict) and _is_quality_product(god):
                items.append({
                    "name": god.get("title") or god.get("name") or "God Idol",
                    "link": god.get("link"),
                    "price": god.get("price") or "N/A",
                    "category": f"God Idol ({god.get('festival', '')})",
                    "image": god.get("image", "")
                })
        for key in ["decoration_kit", "puja_kit"]:
            prod = recommendations.get(key)
            if prod and isinstance(prod, dict) and _is_quality_product(prod):
                items.append({
                    "name": prod.get("title") or prod.get("name") or "Kit",
                    "link": prod.get("link"),
                    "price": prod.get("price") or "N/A",
                    "category": key,
                    "image": prod.get("image", "")
                })

    elif tool_type == "kundali":
        for key in ["weak_planet_gemstone", "dosha_remedy", "lagna_yantra"]:
            prod = recommendations.get(key)
            if prod and isinstance(prod, dict) and _is_quality_product(prod):
                items.append({
                    "name": prod.get("title") or prod.get("name") or prod.get("gemstone") or "Product",
                    "link": prod.get("link"),
                    "price": prod.get("price") or "N/A",
                    "category": key,
                    "image": prod.get("image", "")
                })

    elif tool_type == "janmarashi":
        for key in ["gemstone", "rudraksha", "yantra"]:
            prod = recommendations.get(key)
            if prod and isinstance(prod, dict) and _is_quality_product(prod):
                items.append({
                    "name": prod.get("title") or prod.get("name") or "Product",
                    "link": prod.get("link"),
                    "price": prod.get("price") or "N/A",
                    "category": key,
                    "image": prod.get("image", "")
                })
    else:
        def _search_links(data):
            if isinstance(data, dict):
                if _is_quality_product(data):
                    items.append({
                        "name": data.get("name") or data.get("title") or "Product",
                        "link": data.get("link"),
                        "price": data.get("price") or data.get("price_range") or "N/A",
                        "category": "product",
                        "image": data.get("image", "")
                    })
                else:
                    for v in data.values():
                        _search_links(v)
            elif isinstance(data, list):
                for elem in data:
                    _search_links(elem)

        _search_links(recommendations)

    # ✅ STRICT DEDUPLICATION BY PRODUCT LINK / URL
    unique_items = []
    seen_links = set()
    for item in items:
        link = item.get("link")
        if link and link not in seen_links:
            seen_links.add(link)
            unique_items.append(item)
            if len(unique_items) >= 3:
                break
    return unique_items



def safe_print(text: str = ""):
    """Print text safely on any platform/terminal without UnicodeEncodeError"""
    try:
        print(text)
    except Exception:
        try:
            fallback = text.replace('🛒', '[+]').replace('✅', '[OK]')
            print(fallback.encode('ascii', errors='replace').decode('ascii', errors='replace'))
        except Exception:
            pass


def print_recommended_links_to_terminal(tool_type: str, recommendations: dict, links: dict = None, pending_requests: dict = None) -> list:
    """
    Print summary log in exact format requested by user.
    """
    items = extract_recommended_links(tool_type, recommendations)
    count = len(items)
    has_recs = count > 0
    has_payment_links = bool(links and any("payment" in str(k).lower() for k in links.keys()))
    pending_count = len(pending_requests) if pending_requests is not None else 0
    
    safe_print(f"\n{'='*70}")
    safe_print("✅ SUMMARY:")
    safe_print(f"   Tool: {tool_type}")
    
    if has_recs:
        safe_print(f"   Recommendations: True ({count} product links generated)")
        for idx, item in enumerate(items, 1):
            name = item.get("name") or item.get("title") or "Product"
            safe_print(f"      🛒 {idx}. {name}")
    else:
        safe_print("   Recommendations: False")
        
    safe_print(f"   Payment Links: {has_payment_links}")
    safe_print(f"   Pending Requests: {pending_count}")
    safe_print(f"{'='*70}\n")
    
    return items

