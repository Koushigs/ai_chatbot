"""
Product Recommendations Database
Provides live product suggestions from https://api.bharatcalendars.in:5200/affiliate/allItems for each astrological tool
"""

from affiliate_products import (
    get_gemstone_product, get_rudraksha_product, get_yantra_product,
    get_deity_idol_product, get_panchang_product, get_festival_products,
    get_color_product, product_manager
)

# Helper function to get multiple gemstone products for a Rashi
def _get_gemstone_products_for_rashi(rashi_name, main_gem):
    p1 = get_gemstone_product(main_gem)
    p2 = get_rudraksha_product("5")
    p3 = get_yantra_product(f"{rashi_name} Yantra")
    return [p1, p2, p3]

# ============ GEMSTONE MAPPING ============
RASHI_GEMSTONES = {
    "ARIES": {
        "gemstone": "Red Coral",
        "planetary_lord": "Mars",
        "benefits": "Increases courage, energy, and determination",
        "price_range": "₹500-2000",
        "products": [
            get_gemstone_product("Red Coral"),
            get_rudraksha_product("3"),
            get_yantra_product("Mars")
        ]
    },
    "TAURUS": {
        "gemstone": "Diamond (or White Sapphire)",
        "planetary_lord": "Venus",
        "benefits": "Brings luxury, prosperity, and love",
        "price_range": "₹5000-50000",
        "products": [
            get_gemstone_product("Diamond"),
            get_gemstone_product("White Sapphire"),
            get_yantra_product("Shukra")
        ]
    },
    "GEMINI": {
        "gemstone": "Emerald",
        "planetary_lord": "Mercury",
        "benefits": "Enhances communication, intellect, and business",
        "price_range": "₹1000-5000",
        "products": [
            get_gemstone_product("Emerald"),
            get_rudraksha_product("4"),
            get_yantra_product("Budh")
        ]
    },
    "CANCER": {
        "gemstone": "Pearl",
        "planetary_lord": "Moon",
        "benefits": "Promotes emotional peace and mental clarity",
        "price_range": "₹300-2000",
        "products": [
            get_gemstone_product("Pearl"),
            get_rudraksha_product("2"),
            get_yantra_product("Chandra")
        ]
    },
    "LEO": {
        "gemstone": "Ruby",
        "planetary_lord": "Sun",
        "benefits": "Boosts confidence, leadership, and health",
        "price_range": "₹2000-10000",
        "products": [
            get_gemstone_product("Ruby"),
            get_deity_idol_product("Surya"),
            get_yantra_product("Surya")
        ]
    },
    "VIRGO": {
        "gemstone": "Emerald",
        "planetary_lord": "Mercury",
        "benefits": "Enhances communication, intellect, and business",
        "price_range": "₹1000-5000",
        "products": [
            get_gemstone_product("Emerald"),
            get_rudraksha_product("4"),
            get_yantra_product("Budh")
        ]
    },
    "LIBRA": {
        "gemstone": "Diamond (or Opal)",
        "planetary_lord": "Venus",
        "benefits": "Brings harmony, beauty, and prosperity",
        "price_range": "₹5000-50000",
        "products": [
            get_gemstone_product("Diamond"),
            get_gemstone_product("Opal"),
            get_yantra_product("Shukra")
        ]
    },
    "SCORPIO": {
        "gemstone": "Red Coral",
        "planetary_lord": "Mars",
        "benefits": "Increases courage, energy, and determination",
        "price_range": "₹500-2000",
        "products": [
            get_gemstone_product("Red Coral"),
            get_rudraksha_product("3"),
            get_yantra_product("Mars")
        ]
    },
    "SAGITTARIUS": {
        "gemstone": "Yellow Sapphire",
        "planetary_lord": "Jupiter",
        "benefits": "Brings wisdom, prosperity, and spiritual growth",
        "price_range": "₹1500-8000",
        "products": [
            get_gemstone_product("Yellow Sapphire"),
            get_rudraksha_product("5"),
            get_yantra_product("Guru")
        ]
    },
    "CAPRICORN": {
        "gemstone": "Blue Sapphire",
        "planetary_lord": "Saturn",
        "benefits": "Enhances discipline, focus, and longevity",
        "price_range": "₹2000-15000",
        "products": [
            get_gemstone_product("Blue Sapphire"),
            get_rudraksha_product("7"),
            get_yantra_product("Shani")
        ]
    },
    "AQUARIUS": {
        "gemstone": "Blue Sapphire",
        "planetary_lord": "Saturn",
        "benefits": "Enhances discipline, focus, and longevity",
        "price_range": "₹2000-15000",
        "products": [
            get_gemstone_product("Blue Sapphire"),
            get_rudraksha_product("7"),
            get_yantra_product("Shani")
        ]
    },
    "PISCES": {
        "gemstone": "Yellow Sapphire",
        "planetary_lord": "Jupiter",
        "benefits": "Brings wisdom, prosperity, and spiritual growth",
        "price_range": "₹1500-8000",
        "products": [
            get_gemstone_product("Yellow Sapphire"),
            get_rudraksha_product("5"),
            get_yantra_product("Guru")
        ]
    }
}

# ============ RUDRAKSHA MAPPING ============
RASHI_RUDRAKSHA = {
    "ARIES": {"mukhi": "3", "description": "3 Mukhi - Mars energy", **get_rudraksha_product("3")},
    "TAURUS": {"mukhi": "6", "description": "6 Mukhi - Venus energy", **get_rudraksha_product("6")},
    "GEMINI": {"mukhi": "4", "description": "4 Mukhi - Mercury energy", **get_rudraksha_product("4")},
    "CANCER": {"mukhi": "2", "description": "2 Mukhi - Moon energy", **get_rudraksha_product("2")},
    "LEO": {"mukhi": "1 or 12", "description": "1/12 Mukhi - Sun energy", **get_rudraksha_product("1")},
    "VIRGO": {"mukhi": "4", "description": "4 Mukhi - Mercury energy", **get_rudraksha_product("4")},
    "LIBRA": {"mukhi": "6", "description": "6 Mukhi - Venus energy", **get_rudraksha_product("6")},
    "SCORPIO": {"mukhi": "3", "description": "3 Mukhi - Mars energy", **get_rudraksha_product("3")},
    "SAGITTARIUS": {"mukhi": "5", "description": "5 Mukhi - Jupiter energy", **get_rudraksha_product("5")},
    "CAPRICORN": {"mukhi": "7 or 14", "description": "7/14 Mukhi - Saturn energy", **get_rudraksha_product("7")},
    "AQUARIUS": {"mukhi": "7 or 14", "description": "7/14 Mukhi - Saturn energy", **get_rudraksha_product("7")},
    "PISCES": {"mukhi": "5", "description": "5 Mukhi - Jupiter energy", **get_rudraksha_product("5")}
}

# ============ LUCKY NUMBER TO RUDRAKSHA ============
LUCKY_NUMBER_RUDRAKSHA = {
    num: {
        "description": f"{num} Mukhi Rudraksha",
        **get_rudraksha_product(str(num))
    } for num in range(1, 10)
}

# ============ LUCKY COLOR PRODUCTS ============
LUCKY_COLOR_PRODUCTS = {
    "RED": [get_color_product("RED")],
    "BLUE": [get_color_product("BLUE")],
    "GREEN": [get_color_product("GREEN")],
    "YELLOW": [get_color_product("YELLOW")],
    "WHITE": [get_color_product("WHITE")],
    "PINK": [get_color_product("PINK")],
    "PURPLE": [get_color_product("PURPLE")],
    "ORANGE": [get_color_product("ORANGE")],
    "GOLD": [get_color_product("GOLD")]
}

# ============ PANCHANG RECOMMENDATIONS ============
PANCHANG_PRODUCTS = [
    get_panchang_product(),
    product_manager.search_product(["Incense", "Puja", "Havan"], default_name="Puja Essentials Kit"),
    product_manager.search_product(["Wind Chime", "Vastu", "Tree"], default_name="Vastu Wind Chime")
]

# ============ FESTIVAL RECOMMENDATIONS ============
FESTIVAL_DEITY_IDOLS = {
    "DIWALI": [
        get_deity_idol_product("Lakshmi Ganesha"),
        get_deity_idol_product("Lakshmi"),
        get_deity_idol_product("Ganesha")
    ],
    "HOLI": [
        get_deity_idol_product("Radha Krishna"),
        get_deity_idol_product("Krishna"),
        product_manager.search_product(["Holi", "Pichkari"], default_name="Holi Celebration Kit")
    ],
    "JANMASHTAMI": [
        get_deity_idol_product("Krishna"),
        get_deity_idol_product("Ram Lalla"),
        get_deity_idol_product("Krishna")
    ],
    "NAVRATRI": [
        get_deity_idol_product("Durga"),
        get_deity_idol_product("Kali"),
        product_manager.search_product(["Kalash", "Decor"], default_name="Navratri Kalash Set")
    ],
    "GANESH_CHATURTHI": [
        get_deity_idol_product("Ganesha"),
        get_deity_idol_product("Ganesh"),
        product_manager.search_product(["Ganesha", "Decor"], default_name="Ganesha Decoration Items")
    ],
    "RAKHI": [
        product_manager.search_product(["Rakhi"], default_name="Designer Rakhi Set"),
        get_deity_idol_product("Krishna"),
        product_manager.search_product(["Rakhi"], default_name="Rakhi Gift Hamper")
    ]
}

FESTIVAL_DECORATIONS = {
    "DIWALI": [
        product_manager.search_product(["Deepawali", "Diya", "Gift Box"], default_name="Deepawali Gift Box & Diyas"),
        product_manager.search_product(["Decor", "Home Decor"], default_name="Diwali Decoration Set")
    ],
    "HOLI": [
        product_manager.search_product(["Holi", "Pichkari"], default_name="Organic Holi Colors & Pichkari")
    ],
    "NAVRATRI": [
        product_manager.search_product(["Garland", "Decor"], default_name="Navratri Festival Garland Set")
    ]
}

FESTIVAL_AGARBATTI = {
    "DIWALI": {"scent": "Jasmine (Mogra)", **product_manager.search_product(["Incense", "Cones", "Havan"], default_name="Mogra Incense Cones")},
    "NAVRATRI": {"scent": "Rose & Chandan", **product_manager.search_product(["Incense", "Puja"], default_name="Rose & Chandan Incense")},
    "JANMASHTAMI": {"scent": "Sandal (Chandan)", **product_manager.search_product(["Incense", "Chandan"], default_name="Sandalwood Incense")},
    "GENERAL": {"scent": "Nag Champa Mix", **product_manager.search_product(["Incense", "Nagchampa"], default_name="Nag Champa Incense")}
}

# ============ KUNDALI WEAK PLANET RECOMMENDATIONS ============
WEAK_PLANET_GEMSTONES = {
    "SUN": {"gemstone": "Ruby", "benefits": "Boosts health, confidence, leadership", **get_gemstone_product("Ruby")},
    "MOON": {"gemstone": "Pearl", "benefits": "Promotes emotional peace and stability", **get_gemstone_product("Pearl")},
    "MARS": {"gemstone": "Red Coral", "benefits": "Increases courage and energy", **get_gemstone_product("Red Coral")},
    "MERCURY": {"gemstone": "Emerald", "benefits": "Enhances intellect and communication", **get_gemstone_product("Emerald")},
    "JUPITER": {"gemstone": "Yellow Sapphire", "benefits": "Brings wisdom and prosperity", **get_gemstone_product("Yellow Sapphire")},
    "VENUS": {"gemstone": "Diamond", "benefits": "Brings luxury and love", **get_gemstone_product("Diamond")},
    "SATURN": {"gemstone": "Blue Sapphire", "benefits": "Enhances discipline and focus", **get_gemstone_product("Blue Sapphire")},
    "RAHU": {"gemstone": "Hessonite (Gomed)", "benefits": "Protects from Rahu's negative effects", **get_gemstone_product("Hessonite")},
    "KETU": {"gemstone": "Cat's Eye (Lehsunia)", "benefits": "Protects from Ketu's negative effects", **get_gemstone_product("Cat's Eye")}
}

DOSHA_REMEDIES = {
    "MANGAL_DOSHA": {
        "items": [
            get_gemstone_product("Red Coral"),
            get_yantra_product("Mars"),
            product_manager.search_product(["Hanuman", "Puja"], default_name="Hanuman Puja Kit")
        ]
    },
    "SHANI_DOSHA": {
        "items": [
            get_gemstone_product("Blue Sapphire"),
            get_yantra_product("Shani"),
            get_deity_idol_product("Shani")
        ]
    },
    "KAAL_SARP_DOSHA": {
        "items": [
            get_yantra_product("Rahu"),
            get_gemstone_product("Hessonite"),
            product_manager.search_product(["Puja", "Incense"], default_name="Kaal Sarp Dosha Puja Kit")
        ]
    }
}

LAGNA_YANTRAS = {
    "ARIES": {"yantra": "Mars (Mangal) Yantra", **get_yantra_product("Mars")},
    "TAURUS": {"yantra": "Venus (Shukra) Yantra", **get_yantra_product("Shukra")},
    "GEMINI": {"yantra": "Mercury (Budh) Yantra", **get_yantra_product("Budh")},
    "CANCER": {"yantra": "Moon (Chandra) Yantra", **get_yantra_product("Chandra")},
    "LEO": {"yantra": "Sun (Surya) Yantra", **get_yantra_product("Surya")},
    "VIRGO": {"yantra": "Mercury (Budh) Yantra", **get_yantra_product("Budh")},
    "LIBRA": {"yantra": "Venus (Shukra) Yantra", **get_yantra_product("Shukra")},
    "SCORPIO": {"yantra": "Mars (Mangal) Yantra", **get_yantra_product("Mars")},
    "SAGITTARIUS": {"yantra": "Jupiter (Guru) Yantra", **get_yantra_product("Guru")},
    "CAPRICORN": {"yantra": "Saturn (Shani) Yantra", **get_yantra_product("Shani")},
    "AQUARIUS": {"yantra": "Saturn (Shani) Yantra", **get_yantra_product("Shani")},
    "PISCES": {"yantra": "Jupiter (Guru) Yantra", **get_yantra_product("Guru")}
}
