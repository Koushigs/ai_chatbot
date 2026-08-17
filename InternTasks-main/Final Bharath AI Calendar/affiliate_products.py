"""
affiliate_products.py - Affiliate Products API Integration
Fetches and matches live product recommendations from https://api.bharatcalendars.in:5200/affiliate/allItems
"""

import urllib.request
import json
import re
import os
import time
from config import BHARAT_CA_BUNDLE, AFFILIATE_API_URL

API_URL = AFFILIATE_API_URL
CACHE_FILE = os.path.join(os.path.dirname(__file__), "affiliate_products_cache.json")
CACHE_TTL = 3600  # 1 hour cache TTL


class AffiliateProductManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AffiliateProductManager, cls).__new__(cls)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        self.items = []
        self.last_fetch_time = 0
        self.load_products()

    def load_products(self):
        """Fetch items from API with local file cache fallback"""
        now = time.time()
        
        # 1. Try fetching live from API
        try:
            import ssl
            if BHARAT_CA_BUNDLE:
                ssl_context = ssl.create_default_context(cafile=BHARAT_CA_BUNDLE)
            else:
                ssl_context = ssl.create_default_context()
            
            req = urllib.request.Request(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10, context=ssl_context) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if isinstance(data, list) and len(data) > 0:
                    self.items = data
                    self.last_fetch_time = now
                    # Save to local file cache if writable
                    try:
                        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                            json.dump({"timestamp": now, "items": data}, f, ensure_ascii=False, indent=2)
                    except Exception as ce:
                        pass
                    print(f"[OK] [Affiliate API] Successfully loaded {len(self.items)} products from live API.")
                    return
        except Exception as e:
            print(f"[WARN] [Affiliate API] Error fetching live API ({e}). Falling back to cache...")

        # 2. Fallback to local cache file if live API failed or timed out
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.items = cache_data.get("items", [])
                    self.last_fetch_time = now
                    print(f"[OK] [Affiliate API] Loaded {len(self.items)} products from local cache fallback.")
                    return
            except Exception as ce:
                print(f"[ERROR] [Affiliate API] Error loading local cache: {ce}")

        self.last_fetch_time = now
        self.items = []

    def get_all_items(self):
        """Get all items, refreshing if cache expired or items empty"""
        if not self.items or (time.time() - self.last_fetch_time > CACHE_TTL):
            self.load_products()
        return self.items

    def search_product(self, primary_keywords, secondary_keywords=None, fallback_keywords=None, default_name="Product", default_link="https://www.amazon.in/"):
        """
        Smart product matcher:
        Returns dict with keys: name, link, price, image, id
        """
        items = self.get_all_items()
        if not items:
            return {
                "name": default_name,
                "link": default_link,
                "price": "",
                "image": ""
            }

        # First pass: All primary_keywords must match in text
        best_item = self._find_matching_item(items, primary_keywords, require_all=True, secondary=secondary_keywords)

        # Second pass: Any primary_keywords match with secondary
        if not best_item:
            best_item = self._find_matching_item(items, primary_keywords, require_all=False, secondary=secondary_keywords)

        # Third pass: fallback keywords
        if not best_item and fallback_keywords:
            best_item = self._find_matching_item(items, fallback_keywords, require_all=False)

        # Fourth pass: secondary keywords (category-aware fallback)
        if not best_item and secondary_keywords:
            best_item = self._find_matching_item(items, secondary_keywords, require_all=False)

        # Fifth pass: generic fallback to incense/diya/brass/tree
        if not best_item:
            best_item = self._find_matching_item(items, ["incense", "diya", "brass", "tree", "decor"], require_all=False)

        if best_item:
            title = best_item.get("title", default_name)
            link = best_item.get("link", default_link)
            price = best_item.get("discountedPrice") or best_item.get("price") or ""
            images = best_item.get("images", [])
            image = images[0] if images else ""

            return {
                "name": title,
                "link": link,
                "price": price,
                "image": image,
                "id": best_item.get("_id")
            }

        return {
            "name": default_name,
            "link": default_link,
            "price": "",
            "image": ""
        }

    def search_multiple_products(self, primary_keywords, secondary_keywords=None, max_results=3, default_name="Product"):
        """Search and return up to max_results distinct matching products"""
        items = self.get_all_items()
        if not items:
            return [{
                "name": default_name,
                "link": "https://www.amazon.in/",
                "price": "",
                "image": ""
            }]

        scored_items = []
        for item in items:
            text = (item.get("title", "") + " " + item.get("description", "")).lower()
            score = 0
            matched_count = 0
            for kw in primary_keywords:
                kw_l = kw.lower()
                if kw_l in text:
                    matched_count += 1
                    if re.search(r'\b' + re.escape(kw_l) + r'\b', text):
                        score += 5
                    else:
                        score += 2

            if matched_count > 0:
                if secondary_keywords:
                    for skw in secondary_keywords:
                        skw_l = skw.lower()
                        if skw_l in text:
                            score += 1
                scored_items.append((score, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        results = []
        seen_ids = set()

        for score, best_item in scored_items:
            item_id = best_item.get("_id")
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            title = best_item.get("title", default_name)
            link = best_item.get("link", "https://www.amazon.in/")
            price = best_item.get("discountedPrice") or best_item.get("price") or ""
            images = best_item.get("images", [])
            image = images[0] if images else ""

            results.append({
                "name": title,
                "link": link,
                "price": price,
                "image": image,
                "id": item_id
            })

            if len(results) >= max_results:
                break

        if not results:
            first = items[0]
            results.append({
                "name": first.get("title", default_name),
                "link": first.get("link", "https://www.amazon.in/"),
                "price": first.get("discountedPrice") or first.get("price") or "",
                "image": first.get("images", [""])[0] if first.get("images") else "",
                "id": first.get("_id")
            })

        return results

    def _find_matching_item(self, items, keywords, require_all=False, secondary=None):
        best_item = None
        highest_score = 0

        for item in items:
            text = (item.get("title", "") + " " + item.get("description", "")).lower()
            score = 0
            matched_count = 0

            for kw in keywords:
                kw_l = kw.lower()
                if kw_l in text:
                    matched_count += 1
                    if re.search(r'\b' + re.escape(kw_l) + r'\b', text):
                        score += 5
                    else:
                        score += 2

            if require_all and matched_count < len(keywords):
                continue

            if matched_count > 0:
                if secondary:
                    for skw in secondary:
                        skw_l = skw.lower()
                        if skw_l in text:
                            score += 1

                if score > highest_score:
                    highest_score = score
                    best_item = item

        return best_item


product_manager = AffiliateProductManager()


GEMSTONE_FALLBACK_MAP = {
    "RUBY": ["Pyrite", "Chakra", "Crystal", "Gemstone", "Red"],
    "PEARL": ["Opalite", "Rose Quartz", "White", "Pyramid", "Crystal"],
    "EMERALD": ["Aventurine", "Pyrite", "Green", "Bracelet", "Gemstone"],
    "DIAMOND": ["Opalite", "Crystal", "Pyramid", "Quartz"],
    "WHITE SAPPHIRE": ["Opalite", "Crystal", "Pyramid", "Quartz"],
    "YELLOW SAPPHIRE": ["Citrine", "Pyrite", "Yellow", "Gold", "Bracelet"],
    "BLUE SAPPHIRE": ["Hakik", "Shani", "Black", "Mala", "Rudraksha"],
    "RED CORAL": ["Red Coral", "Coral", "Red", "Ring", "Chakra"],
    "HESSONITE": ["Rahu", "Chakra", "Orgonite", "Pyramid", "Black"],
    "CAT'S EYE": ["Chakra", "Pyramid", "Orgonite", "Crystal"],
    "OPAL": ["Opalite", "Crystal", "Pyramid"]
}

def get_gemstone_product(gem_name: str) -> dict:
    """Get gemstone product from affiliate database with category-aware gemstone fallback mapping"""
    gem_upper = gem_name.upper()
    fallback_kws = ["Gemstone", "Crystal", "Chakra", "Mala", "Stone"]
    
    for key, kws in GEMSTONE_FALLBACK_MAP.items():
        if key in gem_upper:
            fallback_kws = kws
            break

    return product_manager.search_product(
        primary_keywords=[gem_name],
        secondary_keywords=["Gemstone", "Crystal", "Chakra", "Mala", "Stone", "Ring"],
        fallback_keywords=fallback_kws
    )


MUKHI_WORD_MAP = {
    "1": ["1 Mukhi", "One Mukhi", "1-Mukhi", "1 Mukha", "1 Face"],
    "2": ["2 Mukhi", "Two Mukhi", "2-Mukhi", "2 Mukha", "2 Face"],
    "3": ["3 Mukhi", "Three Mukhi", "3-Mukhi", "3 Mukha", "3 Face"],
    "4": ["4 Mukhi", "Four Mukhi", "4-Mukhi", "4 Mukha", "4 Face"],
    "5": ["5 Mukhi", "Five Mukhi", "Panchmukhi", "5-Mukhi", "5face", "5 Face"],
    "6": ["6 Mukhi", "Six Mukhi", "6-Mukhi", "6 Mukha", "6 Face", "6 Faced"],
    "7": ["7 Mukhi", "Seven Mukhi", "7-Mukhi", "7 Mukha", "7 Faced"],
    "8": ["8 Mukhi", "Eight Mukhi", "8-Mukhi", "8 Mukha", "8 Face"],
    "9": ["9 Mukhi", "Nine Mukhi", "9-Mukhi", "9 Mukha", "9 Face"],
}

def get_rudraksha_product(mukhi: str) -> dict:
    """Get rudraksha product from affiliate database matching exact Mukhi phrase"""
    m_clean = str(mukhi).strip().split()[0]
    search_kws = MUKHI_WORD_MAP.get(m_clean, [f"{m_clean} Mukhi", f"{m_clean} Face"])
    
    return product_manager.search_product(
        primary_keywords=search_kws,
        secondary_keywords=["Rudraksha", "Mala", "Bead", "Certified"],
        fallback_keywords=["Rudraksha", "Panchmukhi", "Mala", "Bead"]
    )


def get_yantra_product(yantra_name: str) -> dict:
    """Get yantra product from affiliate database"""
    return product_manager.search_product(["Yantra", yantra_name], secondary_keywords=["Copper", "Gold", "Plate"])


def get_deity_idol_product(deity_name: str) -> dict:
    """Get deity idol product from affiliate database"""
    return product_manager.search_product([deity_name], secondary_keywords=["Idol", "Murti", "Statue", "Brass"])


def get_panchang_product() -> dict:
    """Get panchang product from affiliate database"""
    return product_manager.search_product(["Panchang", "Calendar"], fallback_keywords=["Panchangam", "Almanac"], default_name="Bharath Calendar Panchang 2025")


def get_festival_products(festival_key: str) -> dict:
    """Get festival deity idol, decoration kit, and puja kit from affiliate products"""
    fest_upper = festival_key.upper()
    
    if "DIWALI" in fest_upper:
        deity = product_manager.search_product(["Lakshmi"], secondary_keywords=["Ganesha", "Idol", "Set"], default_name="Lakshmi Ganesha Idol Set")
        decor = product_manager.search_product(["Deepawali", "Diwali"], secondary_keywords=["Gift Box", "Diya", "Puja"], fallback_keywords=["Diya", "Brass"], default_name="Diwali Decor & Diya Kit")
        puja = product_manager.search_product(["Incense", "Havan", "Phool", "Diya", "Agarbatti"], fallback_keywords=["Dhoop", "Puja"], default_name="Diwali Puja Essentials Kit")

    elif "HOLI" in fest_upper:
        deity = product_manager.search_product(["Radha", "Krishna"], secondary_keywords=["Idol"], default_name="Radha Krishna Idol")
        decor = product_manager.search_product(["Holi", "Pichkari"], secondary_keywords=["Water Gun", "Gulal"], fallback_keywords=["Holi"], default_name="Holi Pichkari & Celebration Kit")
        puja = product_manager.search_product(["Phool", "Incense", "Havan", "Diya"], fallback_keywords=["Puja"], default_name="Holi Puja Kit")

    elif "RAKHI" in fest_upper or "RAKSHA" in fest_upper:
        deity = product_manager.search_product(["Krishna"], secondary_keywords=["Idol"], default_name="Lord Krishna Idol")
        decor = product_manager.search_product(["Rakhi"], secondary_keywords=["Brother", "Designer", "Roli", "Card"], default_name="Designer Rakhi Set")
        puja = product_manager.search_product(["Rakhi"], secondary_keywords=["Gift", "Combo", "Sister", "Bhabhi"], default_name="Rakhi Roli Chawal & Gift Kit")

    elif "GANESH" in fest_upper:
        deity = product_manager.search_product(["Ganesh", "Ganesha"], secondary_keywords=["Idol", "Murti", "Statue"], default_name="Ganesha Idol")
        decor = product_manager.search_product(["Ganesh", "Decor", "Decoration"], fallback_keywords=["Mandir", "Showpiece"], default_name="Ganesha Decoration Items")
        puja = product_manager.search_product(["Incense", "Havan", "Phool", "Diya", "Agarbatti"], fallback_keywords=["Dhoop", "Puja"], default_name="Puja Essentials Kit")

    elif "NAVRATRI" in fest_upper or "DUSSEHRA" in fest_upper:
        deity = product_manager.search_product(["Durga", "Kali", "Maa"], secondary_keywords=["Idol", "Brass"], default_name="Maa Durga Idol")
        decor = product_manager.search_product(["Tree", "Kalpavriksha", "Brass", "Vastu"], secondary_keywords=["Showpiece", "Decor"], default_name="Navratri Festival Decor Tree")
        puja = product_manager.search_product(["Incense", "Havan", "Phool", "Diya", "Agarbatti"], fallback_keywords=["Dhoop", "Puja"], default_name="Navratri Puja Essentials")

    elif "JANMASHTAMI" in fest_upper:
        deity = product_manager.search_product(["Krishna"], secondary_keywords=["Idol", "Standing", "Resin"], default_name="Lord Krishna Idol")
        decor = product_manager.search_product(["Krishna", "Flute", "Jhula", "Decor"], secondary_keywords=["Idol"], default_name="Janmashtami Krishna Decor")
        puja = product_manager.search_product(["Incense", "Havan", "Phool", "Diya", "Agarbatti"], fallback_keywords=["Dhoop"], default_name="Janmashtami Puja Kit")

    elif "SANKRANTI" in fest_upper or "MAKAR" in fest_upper:
        deity = product_manager.search_product(["Surya", "Sun"], secondary_keywords=["Brass", "Idol"], default_name="Surya Dev Brass Idol")
        decor = product_manager.search_product(["Surya", "Tree", "Brass"], secondary_keywords=["Decor"], default_name="Makar Sankranti Brass Decor")
        puja = product_manager.search_product(["Incense", "Havan", "Phool", "Diya"], default_name="Puja Essentials Kit")

    elif "RAM" in fest_upper or "RAMA" in fest_upper:
        deity = product_manager.search_product(["Ram", "Rama", "Ram Lalla"], secondary_keywords=["Idol", "Statue"], default_name="Ram Lalla Idol")
        decor = product_manager.search_product(["Mandir", "Decor", "Model"], fallback_keywords=["Brass"], default_name="Ram Mandir Model & Decor")
        puja = product_manager.search_product(["Incense", "Havan", "Phool", "Diya"], default_name="Rama Navami Puja Kit")

    elif "BUDDHA" in fest_upper:
        deity = product_manager.search_product(["Buddha"], secondary_keywords=["Statue", "Idol"], default_name="Buddha Statue")
        decor = product_manager.search_product(["Buddha"], secondary_keywords=["Decor", "Zen"], default_name="Buddha Decor Items")
        puja = product_manager.search_product(["Incense", "Cones", "Nagchampa"], default_name="Meditation Incense Cones")

    else:
        deity = product_manager.search_product(["Idol", "Statue"], default_name="Deity Idol")
        decor = product_manager.search_product(["Tree", "Decor", "Brass"], default_name="Festival Decor Kit")
        puja = product_manager.search_product(["Incense", "Havan", "Phool", "Diya"], default_name="Puja Essentials Kit")

    return {
        "deity": deity,
        "decor": decor,
        "puja": puja
    }


def get_color_product(color_name: str) -> dict:
    """Get item matching lucky color"""
    c_upper = color_name.upper()
    if "RED" in c_upper:
        return product_manager.search_product(["Red"], secondary_keywords=["Coral", "Rakhi", "Decor", "Cloth"], default_name="Red Auspicious Item")
    elif "GOLD" in c_upper or "YELLOW" in c_upper:
        return product_manager.search_product(["Gold", "Golden", "Yellow"], secondary_keywords=["Plated", "Brass", "Idol"], default_name="Gold Auspicious Item")
    elif "BLUE" in c_upper:
        return product_manager.search_product(["Blue"], secondary_keywords=["Yoga", "Mat", "Decor"], default_name="Blue Auspicious Item")
    elif "GREEN" in c_upper:
        return product_manager.search_product(["Green", "Chakra"], secondary_keywords=["Tree", "Plant", "Decor"], default_name="Green Auspicious Item")
    elif "WHITE" in c_upper:
        return product_manager.search_product(["White"], secondary_keywords=["Pearl", "Statue", "Idol"], default_name="White Auspicious Item")
    else:
        return product_manager.search_product(["Crystal", "Tree", "Decor"], default_name=f"{color_name} Auspicious Item")
