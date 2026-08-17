import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Product Prices
KUNDALI_PRICE = int(os.getenv("KUNDALI_PRICE", "199"))
JANMARASHI_PRICE = int(os.getenv("JANMARASHI_PRICE", "20"))

# SSL / CA Bundle configuration
BHARAT_CA_BUNDLE = os.getenv("BHARAT_CA_BUNDLE")

# External Service Endpoints
KUNDALI_PDF_API = os.getenv("KUNDALI_PDF_API", "https://debug.bharatcalendars.in:8443/api/kundali/generate-pdf")
JANMARASHI_API = os.getenv("JANMARASHI_API", "https://debug.bharatcalendars.in:8443/api/janamrashi/moon-rashi")
AFFILIATE_API_URL = os.getenv("AFFILIATE_API_URL", "https://api.bharatcalendars.in:5200/affiliate/allItems")

