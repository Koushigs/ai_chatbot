"""
Product Recommendations Database
Provides product suggestions for each astrological tool
"""

# ============ GEMSTONE MAPPING ============
RASHI_GEMSTONES = {
    "ARIES": {
        "gemstone": "Red Coral",
        "planetary_lord": "Mars",
        "benefits": "Increases courage, energy, and determination",
        "price_range": "₹500-2000",
        "products": [
            {"name": "Red Coral Gemstone (Original)", "link": "https://shop.example.com/gemstones/red-coral-1"},
            {"name": "Red Coral Bead Mala", "link": "https://shop.example.com/malas/red-coral-mala"},
            {"name": "Red Coral Ring", "link": "https://shop.example.com/rings/red-coral-ring"}
        ]
    },
    "TAURUS": {
        "gemstone": "Diamond (or White Sapphire)",
        "planetary_lord": "Venus",
        "benefits": "Brings luxury, prosperity, and love",
        "price_range": "₹5000-50000",
        "products": [
            {"name": "Diamond Gemstone (Certified)", "link": "https://shop.example.com/gemstones/diamond-certified"},
            {"name": "White Sapphire Alternative", "link": "https://shop.example.com/gemstones/white-sapphire"},
            {"name": "Diamond Pendant", "link": "https://shop.example.com/pendants/diamond-pendant"}
        ]
    },
    "GEMINI": {
        "gemstone": "Emerald",
        "planetary_lord": "Mercury",
        "benefits": "Enhances communication, intellect, and business",
        "price_range": "₹1000-5000",
        "products": [
            {"name": "Natural Emerald Gemstone", "link": "https://shop.example.com/gemstones/emerald-natural"},
            {"name": "Emerald Ring", "link": "https://shop.example.com/rings/emerald-ring"},
            {"name": "Emerald Beads", "link": "https://shop.example.com/beads/emerald-beads"}
        ]
    },
    "CANCER": {
        "gemstone": "Pearl",
        "planetary_lord": "Moon",
        "benefits": "Promotes emotional peace and mental clarity",
        "price_range": "₹300-2000",
        "products": [
            {"name": "Natural Pearl Gemstone", "link": "https://shop.example.com/gemstones/pearl-natural"},
            {"name": "Pearl Necklace", "link": "https://shop.example.com/necklaces/pearl-necklace"},
            {"name": "Pearl Mala", "link": "https://shop.example.com/malas/pearl-mala"}
        ]
    },
    "LEO": {
        "gemstone": "Ruby",
        "planetary_lord": "Sun",
        "benefits": "Boosts confidence, leadership, and health",
        "price_range": "₹2000-10000",
        "products": [
            {"name": "Natural Ruby Gemstone (Burma)", "link": "https://shop.example.com/gemstones/ruby-burma"},
            {"name": "Ruby Ring (Gold)", "link": "https://shop.example.com/rings/ruby-gold-ring"},
            {"name": "Ruby Pendant", "link": "https://shop.example.com/pendants/ruby-pendant"}
        ]
    },
    "VIRGO": {
        "gemstone": "Emerald",
        "planetary_lord": "Mercury",
        "benefits": "Enhances communication, intellect, and business",
        "price_range": "₹1000-5000",
        "products": [
            {"name": "Natural Emerald Gemstone", "link": "https://shop.example.com/gemstones/emerald-natural"},
            {"name": "Emerald Ring", "link": "https://shop.example.com/rings/emerald-ring"},
            {"name": "Emerald Beads", "link": "https://shop.example.com/beads/emerald-beads"}
        ]
    },
    "LIBRA": {
        "gemstone": "Diamond (or Opal)",
        "planetary_lord": "Venus",
        "benefits": "Brings harmony, beauty, and prosperity",
        "price_range": "₹5000-50000",
        "products": [
            {"name": "Diamond Gemstone", "link": "https://shop.example.com/gemstones/diamond-certified"},
            {"name": "Opal Gemstone (Alternative)", "link": "https://shop.example.com/gemstones/opal-natural"},
            {"name": "Diamond Earrings", "link": "https://shop.example.com/earrings/diamond-earrings"}
        ]
    },
    "SCORPIO": {
        "gemstone": "Red Coral",
        "planetary_lord": "Mars",
        "benefits": "Increases courage, energy, and determination",
        "price_range": "₹500-2000",
        "products": [
            {"name": "Red Coral Gemstone (Original)", "link": "https://shop.example.com/gemstones/red-coral-1"},
            {"name": "Red Coral Bead Mala", "link": "https://shop.example.com/malas/red-coral-mala"},
            {"name": "Red Coral Ring", "link": "https://shop.example.com/rings/red-coral-ring"}
        ]
    },
    "SAGITTARIUS": {
        "gemstone": "Yellow Sapphire",
        "planetary_lord": "Jupiter",
        "benefits": "Brings wisdom, prosperity, and spiritual growth",
        "price_range": "₹1500-8000",
        "products": [
            {"name": "Natural Yellow Sapphire", "link": "https://shop.example.com/gemstones/yellow-sapphire-natural"},
            {"name": "Yellow Sapphire Ring", "link": "https://shop.example.com/rings/yellow-sapphire-ring"},
            {"name": "Yellow Sapphire Pendant", "link": "https://shop.example.com/pendants/yellow-sapphire"}
        ]
    },
    "CAPRICORN": {
        "gemstone": "Blue Sapphire",
        "planetary_lord": "Saturn",
        "benefits": "Enhances discipline, focus, and longevity",
        "price_range": "₹2000-15000",
        "products": [
            {"name": "Natural Blue Sapphire", "link": "https://shop.example.com/gemstones/blue-sapphire-natural"},
            {"name": "Blue Sapphire Ring", "link": "https://shop.example.com/rings/blue-sapphire-ring"},
            {"name": "Blue Sapphire Pendant", "link": "https://shop.example.com/pendants/blue-sapphire"}
        ]
    },
    "AQUARIUS": {
        "gemstone": "Blue Sapphire",
        "planetary_lord": "Saturn",
        "benefits": "Enhances discipline, focus, and longevity",
        "price_range": "₹2000-15000",
        "products": [
            {"name": "Natural Blue Sapphire", "link": "https://shop.example.com/gemstones/blue-sapphire-natural"},
            {"name": "Blue Sapphire Ring", "link": "https://shop.example.com/rings/blue-sapphire-ring"},
            {"name": "Blue Sapphire Pendant", "link": "https://shop.example.com/pendants/blue-sapphire"}
        ]
    },
    "PISCES": {
        "gemstone": "Yellow Sapphire",
        "planetary_lord": "Jupiter",
        "benefits": "Brings wisdom, prosperity, and spiritual growth",
        "price_range": "₹1500-8000",
        "products": [
            {"name": "Natural Yellow Sapphire", "link": "https://shop.example.com/gemstones/yellow-sapphire-natural"},
            {"name": "Yellow Sapphire Ring", "link": "https://shop.example.com/rings/yellow-sapphire-ring"},
            {"name": "Yellow Sapphire Pendant", "link": "https://shop.example.com/pendants/yellow-sapphire"}
        ]
    }
}

# ============ RUDRAKSHA MAPPING ============
RASHI_RUDRAKSHA = {
    "ARIES": {"mukhi": "3", "description": "3 Mukhi - Mars energy", "link": "https://shop.example.com/rudraksha/3-mukhi"},
    "TAURUS": {"mukhi": "6", "description": "6 Mukhi - Venus energy", "link": "https://shop.example.com/rudraksha/6-mukhi"},
    "GEMINI": {"mukhi": "4", "description": "4 Mukhi - Mercury energy", "link": "https://shop.example.com/rudraksha/4-mukhi"},
    "CANCER": {"mukhi": "2", "description": "2 Mukhi - Moon energy", "link": "https://shop.example.com/rudraksha/2-mukhi"},
    "LEO": {"mukhi": "1 or 12", "description": "1/12 Mukhi - Sun energy", "link": "https://shop.example.com/rudraksha/1-mukhi"},
    "VIRGO": {"mukhi": "4", "description": "4 Mukhi - Mercury energy", "link": "https://shop.example.com/rudraksha/4-mukhi"},
    "LIBRA": {"mukhi": "6", "description": "6 Mukhi - Venus energy", "link": "https://shop.example.com/rudraksha/6-mukhi"},
    "SCORPIO": {"mukhi": "3", "description": "3 Mukhi - Mars energy", "link": "https://shop.example.com/rudraksha/3-mukhi"},
    "SAGITTARIUS": {"mukhi": "5", "description": "5 Mukhi - Jupiter energy", "link": "https://shop.example.com/rudraksha/5-mukhi"},
    "CAPRICORN": {"mukhi": "7 or 14", "description": "7/14 Mukhi - Saturn energy", "link": "https://shop.example.com/rudraksha/7-mukhi"},
    "AQUARIUS": {"mukhi": "7 or 14", "description": "7/14 Mukhi - Saturn energy", "link": "https://shop.example.com/rudraksha/7-mukhi"},
    "PISCES": {"mukhi": "5", "description": "5 Mukhi - Jupiter energy", "link": "https://shop.example.com/rudraksha/5-mukhi"}
}

# ============ LUCKY NUMBER TO RUDRAKSHA ============
LUCKY_NUMBER_RUDRAKSHA = {
    1: {"description": "1 Mukhi Rudraksha", "link": "https://shop.example.com/rudraksha/1-mukhi"},
    2: {"description": "2 Mukhi Rudraksha", "link": "https://shop.example.com/rudraksha/2-mukhi"},
    3: {"description": "3 Mukhi Rudraksha", "link": "https://shop.example.com/rudraksha/3-mukhi"},
    4: {"description": "4 Mukhi Rudraksha", "link": "https://shop.example.com/rudraksha/4-mukhi"},
    5: {"description": "5 Mukhi Rudraksha", "link": "https://shop.example.com/rudraksha/5-mukhi"},
    6: {"description": "6 Mukhi Rudraksha", "link": "https://shop.example.com/rudraksha/6-mukhi"},
    7: {"description": "7 Mukhi Rudraksha", "link": "https://shop.example.com/rudraksha/7-mukhi"},
    8: {"description": "8 Mukhi Rudraksha", "link": "https://shop.example.com/rudraksha/8-mukhi"},
    9: {"description": "9 Mukhi Rudraksha", "link": "https://shop.example.com/rudraksha/9-mukhi"},
}

# ============ LUCKY COLOR PRODUCTS ============
LUCKY_COLOR_PRODUCTS = {
    "RED": [
        {"name": "Red Cloth", "link": "https://shop.example.com/colors/red-cloth"},
        {"name": "Red Candle", "link": "https://shop.example.com/colors/red-candle"},
        {"name": "Red Decoration Items", "link": "https://shop.example.com/colors/red-decor"}
    ],
    "BLUE": [
        {"name": "Blue Cloth", "link": "https://shop.example.com/colors/blue-cloth"},
        {"name": "Blue Candle", "link": "https://shop.example.com/colors/blue-candle"},
        {"name": "Blue Decoration Items", "link": "https://shop.example.com/colors/blue-decor"}
    ],
    "GREEN": [
        {"name": "Green Cloth", "link": "https://shop.example.com/colors/green-cloth"},
        {"name": "Green Plant", "link": "https://shop.example.com/colors/green-plant"},
        {"name": "Green Decoration Items", "link": "https://shop.example.com/colors/green-decor"}
    ],
    "YELLOW": [
        {"name": "Yellow Cloth", "link": "https://shop.example.com/colors/yellow-cloth"},
        {"name": "Yellow Candle", "link": "https://shop.example.com/colors/yellow-candle"},
        {"name": "Yellow Decoration Items", "link": "https://shop.example.com/colors/yellow-decor"}
    ],
    "WHITE": [
        {"name": "White Cloth", "link": "https://shop.example.com/colors/white-cloth"},
        {"name": "White Candle", "link": "https://shop.example.com/colors/white-candle"},
        {"name": "White Decoration Items", "link": "https://shop.example.com/colors/white-decor"}
    ],
    "PINK": [
        {"name": "Pink Cloth", "link": "https://shop.example.com/colors/pink-cloth"},
        {"name": "Pink Candle", "link": "https://shop.example.com/colors/pink-candle"},
        {"name": "Pink Decoration Items", "link": "https://shop.example.com/colors/pink-decor"}
    ],
    "PURPLE": [
        {"name": "Purple Cloth", "link": "https://shop.example.com/colors/purple-cloth"},
        {"name": "Purple Candle", "link": "https://shop.example.com/colors/purple-candle"},
        {"name": "Purple Decoration Items", "link": "https://shop.example.com/colors/purple-decor"}
    ],
    "ORANGE": [
        {"name": "Orange Cloth", "link": "https://shop.example.com/colors/orange-cloth"},
        {"name": "Orange Candle", "link": "https://shop.example.com/colors/orange-candle"},
        {"name": "Orange Decoration Items", "link": "https://shop.example.com/colors/orange-decor"}
    ],
    "GOLD": [
        {"name": "Gold Items", "link": "https://shop.example.com/colors/gold-items"},
        {"name": "Gold Candle", "link": "https://shop.example.com/colors/gold-candle"},
        {"name": "Gold Decoration", "link": "https://shop.example.com/colors/gold-decor"}
    ]
}

# ============ PANCHANG RECOMMENDATIONS ============
PANCHANG_PRODUCTS = [
    {"name": "Panchang Calendar (Physical)", "link": "https://shop.example.com/panchang/calendar-physical"},
    {"name": "Digital Panchang App", "link": "https://shop.example.com/panchang/app-digital"},
    {"name": "Puja Essentials Kit", "link": "https://shop.example.com/puja/essentials-kit"},
    {"name": "Wind Chime", "link": "https://shop.example.com/vastu/wind-chime"},
    {"name": "Salt Lamp", "link": "https://shop.example.com/vastu/salt-lamp"},
    {"name": "Crystal Grid Set", "link": "https://shop.example.com/vastu/crystal-grid"}
]

# ============ FESTIVAL RECOMMENDATIONS ============
FESTIVAL_DEITY_IDOLS = {
    "DIWALI": [
        {"name": "Lakshmi Ganesha Idol Set", "link": "https://shop.example.com/idols/lakshmi-ganesha-set"},
        {"name": "Lakshmi Statue (Brass)", "link": "https://shop.example.com/idols/lakshmi-brass"},
        {"name": "Ganesha Idol (Marble)", "link": "https://shop.example.com/idols/ganesha-marble"}
    ],
    "HOLI": [
        {"name": "Radha Krishna Idol", "link": "https://shop.example.com/idols/radha-krishna"},
        {"name": "Krishna Flute & Feather Set", "link": "https://shop.example.com/idols/krishna-set"},
        {"name": "Holi Special Decoration", "link": "https://shop.example.com/idols/holi-decoration"}
    ],
    "JANMASHTAMI": [
        {"name": "Krishna Idol", "link": "https://shop.example.com/idols/krishna-idol"},
        {"name": "Krishna on Swing Set", "link": "https://shop.example.com/idols/krishna-swing"},
        {"name": "Krishna Flute", "link": "https://shop.example.com/idols/krishna-flute"}
    ],
    "NAVRATRI": [
        {"name": "Durga Idol Set", "link": "https://shop.example.com/idols/durga-set"},
        {"name": "Kali Statue", "link": "https://shop.example.com/idols/kali-statue"},
        {"name": "Navratri Kalash", "link": "https://shop.example.com/idols/navratri-kalash"}
    ],
    "GANESH_CHATURTHI": [
        {"name": "Ganesha Idol (Large)", "link": "https://shop.example.com/idols/ganesha-large"},
        {"name": "Modak Mold Set", "link": "https://shop.example.com/idols/modak-mold"},
        {"name": "Ganesha Decoration Items", "link": "https://shop.example.com/idols/ganesha-decor"}
    ],
    "RAKHI": [
        {"name": "Designer Rakhi Set", "link": "https://shop.example.com/idols/rakhi-set"},
        {"name": "Krishna Hanuman Idol (for Rakhi)", "link": "https://shop.example.com/idols/krishna-hanuman"},
        {"name": "Rakhi Gift Hamper", "link": "https://shop.example.com/idols/rakhi-hamper"}
    ]
}

FESTIVAL_DECORATIONS = {
    "DIWALI": [
        {"name": "LED String Lights", "link": "https://shop.example.com/decoration/led-lights"},
        {"name": "Diya Set (50 pieces)", "link": "https://shop.example.com/decoration/diya-set"},
        {"name": "Rangoli Colors (Organic)", "link": "https://shop.example.com/decoration/rangoli-colors"}
    ],
    "HOLI": [
        {"name": "Organic Holi Colors", "link": "https://shop.example.com/decoration/holi-colors"},
        {"name": "Pichkari (Water Gun)", "link": "https://shop.example.com/decoration/pichkari"},
        {"name": "Holi Celebration Kit", "link": "https://shop.example.com/decoration/holi-kit"}
    ],
    "NAVRATRI": [
        {"name": "Navratri Garland", "link": "https://shop.example.com/decoration/navratri-garland"},
        {"name": "Kalash Decoration Set", "link": "https://shop.example.com/decoration/kalash-set"},
        {"name": "Navratri Color Cloth", "link": "https://shop.example.com/decoration/navratri-cloth"}
    ]
}

FESTIVAL_AGARBATTI = {
    "DIWALI": {"scent": "Jasmine (Mogra)", "link": "https://shop.example.com/agarbatti/mogra"},
    "NAVRATRI": {"scent": "Rose & Chandan", "link": "https://shop.example.com/agarbatti/rose-chandan"},
    "JANMASHTAMI": {"scent": "Sandal (Chandan)", "link": "https://shop.example.com/agarbatti/chandan"},
    "GENERAL": {"scent": "Nag Champa Mix", "link": "https://shop.example.com/agarbatti/nag-champa"}
}

# ============ KUNDALI WEAK PLANET RECOMMENDATIONS ============
WEAK_PLANET_GEMSTONES = {
    "SUN": {"gemstone": "Ruby", "benefits": "Boosts health, confidence, leadership", "link": "https://shop.example.com/gemstones/ruby-burma"},
    "MOON": {"gemstone": "Pearl", "benefits": "Promotes emotional peace and stability", "link": "https://shop.example.com/gemstones/pearl-natural"},
    "MARS": {"gemstone": "Red Coral", "benefits": "Increases courage and energy", "link": "https://shop.example.com/gemstones/red-coral-1"},
    "MERCURY": {"gemstone": "Emerald", "benefits": "Enhances intellect and communication", "link": "https://shop.example.com/gemstones/emerald-natural"},
    "JUPITER": {"gemstone": "Yellow Sapphire", "benefits": "Brings wisdom and prosperity", "link": "https://shop.example.com/gemstones/yellow-sapphire-natural"},
    "VENUS": {"gemstone": "Diamond", "benefits": "Brings luxury and love", "link": "https://shop.example.com/gemstones/diamond-certified"},
    "SATURN": {"gemstone": "Blue Sapphire", "benefits": "Enhances discipline and focus", "link": "https://shop.example.com/gemstones/blue-sapphire-natural"},
    "RAHU": {"gemstone": "Hessonite (Gomed)", "benefits": "Protects from Rahu's negative effects", "link": "https://shop.example.com/gemstones/hessonite"},
    "KETU": {"gemstone": "Cat's Eye (Lehsunia)", "benefits": "Protects from Ketu's negative effects", "link": "https://shop.example.com/gemstones/cats-eye"}
}

DOSHA_REMEDIES = {
    "MANGAL_DOSHA": {
        "items": [
            {"name": "Red Coral Gemstone", "link": "https://shop.example.com/gemstones/red-coral-1"},
            {"name": "Mangal Yantra", "link": "https://shop.example.com/yantras/mangal-yantra"},
            {"name": "Hanuman Puja Kit", "link": "https://shop.example.com/puja/hanuman-kit"}
        ]
    },
    "SHANI_DOSHA": {
        "items": [
            {"name": "Blue Sapphire (Neelam)", "link": "https://shop.example.com/gemstones/blue-sapphire-natural"},
            {"name": "Shani Yantra", "link": "https://shop.example.com/yantras/shani-yantra"},
            {"name": "Shani Oil (Til Tel)", "link": "https://shop.example.com/oils/shani-oil"}
        ]
    },
    "KAAL_SARP_DOSHA": {
        "items": [
            {"name": "Rahu-Ketu Yantra", "link": "https://shop.example.com/yantras/rahu-ketu-yantra"},
            {"name": "Hessonite + Cat's Eye Combo", "link": "https://shop.example.com/gemstones/rahu-ketu-combo"},
            {"name": "Kaal Sarp Dosha Puja Kit", "link": "https://shop.example.com/puja/kaal-sarp-kit"}
        ]
    }
}

LAGNA_YANTRAS = {
    "ARIES": {"yantra": "Mars (Mangal) Yantra", "link": "https://shop.example.com/yantras/mangal-yantra"},
    "TAURUS": {"yantra": "Venus (Shukra) Yantra", "link": "https://shop.example.com/yantras/shukra-yantra"},
    "GEMINI": {"yantra": "Mercury (Budh) Yantra", "link": "https://shop.example.com/yantras/budh-yantra"},
    "CANCER": {"yantra": "Moon (Chandra) Yantra", "link": "https://shop.example.com/yantras/chandra-yantra"},
    "LEO": {"yantra": "Sun (Surya) Yantra", "link": "https://shop.example.com/yantras/surya-yantra"},
    "VIRGO": {"yantra": "Mercury (Budh) Yantra", "link": "https://shop.example.com/yantras/budh-yantra"},
    "LIBRA": {"yantra": "Venus (Shukra) Yantra", "link": "https://shop.example.com/yantras/shukra-yantra"},
    "SCORPIO": {"yantra": "Mars (Mangal) Yantra", "link": "https://shop.example.com/yantras/mangal-yantra"},
    "SAGITTARIUS": {"yantra": "Jupiter (Guru) Yantra", "link": "https://shop.example.com/yantras/guru-yantra"},
    "CAPRICORN": {"yantra": "Saturn (Shani) Yantra", "link": "https://shop.example.com/yantras/shani-yantra"},
    "AQUARIUS": {"yantra": "Saturn (Shani) Yantra", "link": "https://shop.example.com/yantras/shani-yantra"},
    "PISCES": {"yantra": "Jupiter (Guru) Yantra", "link": "https://shop.example.com/yantras/guru-yantra"}
}
