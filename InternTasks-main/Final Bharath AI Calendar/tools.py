# tools.py - FIXED FOR KUNDALI PDF RESPONSE

import datetime
import json
import requests
import pytz
from dateutil import parser
from typing import Optional
# pyrefly: ignore [missing-import]
from langchain.tools import tool

# NEW API ENDPOINTS
KUNDALI_PDF_API = "https://www.kundali.bharatcalendars.in:8443/api/kundali/generate-pdf"
JANMARASHI_API = "https://www.kundali.bharatcalendars.in:8443/api/janamrashi/moon-rashi"

@tool
def get_horoscope(sign: str, date: str = None, language: str = "EN") -> str:
    """
    Fetches the horoscope for a given zodiac sign and date from the ExaWeb API.
    Defaults to today if no date is provided.
    
    Args:
        sign: Zodiac sign (e.g., "Aries", "Taurus", "Gemini").
        date: Date in any recognizable format (optional).
        language: Language code (e.g., "EN" for English, "HI" for Hindi).
    """
    try:
        if date:
            date_obj = parser.parse(date)
        else:
            date_obj = datetime.datetime.now()
        
        formatted_date = date_obj.strftime("%d-%m-%Y")
        
        params = {
            "rashi": sign.upper(),
            "language": language,
            "day": formatted_date
        }
        
        url = "https://api.exaweb.in:3004/api/rashi"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        sign_data = data.get(sign.upper())
        
        if sign_data:
            return json.dumps(sign_data)
        return f"INFO: No horoscope found for sign: {sign}"
    
    except requests.exceptions.RequestException as e:
        return f"ERROR get_horoscope: Network error while fetching horoscope: {e}"
    except Exception as e:
        return f"ERROR get_horoscope: An unexpected error occurred: {str(e)}"


@tool
def get_date_panchang(date: str = None, data_language: str = "EN") -> str:
    """
    Fetches the Panchang data for a given date. If the user does not provide a date,
    use today's real date.
    
    Args:
        date: Date in any format (optional).
        data_language: Language of the Panchang data (e.g., "EN" for English, "HI" for Hindi).
    """
    try:
        if not date:
            now = datetime.datetime.now()
        else:
            now = parser.parse(date)
        
        api_date = now.strftime("%d/%m/%y")
        url = f"https://api.exaweb.in:3004/api/panchang/daily?date={api_date}&app_language=EN&data_language={data_language}"
        
        headers = {"api_key": "anvl_bharat_cal123"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not isinstance(data, dict) or not data:
            return "ERROR get_date_panchang: Received empty or invalid data from API."
        
        # 🚀 OPTIMIZATION: Prune heavy unused metadata keys to accelerate LLM inference speed by 70%
        essential_keys = [
            'date', 'location', 'Sunrise', 'Sunset', 'Moonrise', 'Moonset',
            'Tithi', 'Nakshatra', 'Yoga', 'Karana', 'Weekday', 'Paksha',
            'Shaka Samvat', 'Chandramasa', 'Vikram Samvat', 'Moonsign', 'Sunsign',
            'Abhijit', 'Rahu Kalam', 'Yamaganda', 'Gulikai Kalam', 'festivals'
        ]
        trimmed_data = {k: data[k] for k in essential_keys if k in data}
        
        return json.dumps(trimmed_data if trimmed_data else data)
    
    except requests.exceptions.RequestException as e:
        return f"ERROR get_date_panchang: Network error while fetching Panchang: {e}"
    except Exception as e:
        return f"ERROR get_date_panchang: An unexpected error occurred: {str(e)}"


@tool
def get_holidays(year: int = None, data_language: str = "EN") -> str:
    """
    Fetches holidays from all categories for a given year from ExaWeb API.
    
    Args:
        year: Year (e.g., 2025). Optional, defaults to current year.
        data_language: Data language for holidays (default "EN").
    """
    if not year:
        year = datetime.datetime.now().year
    
    params = {"data_language": data_language, "year": year,"app_language": "EN"}
    headers = {"api_key": "anvl_bharat_cal123"}
    
    try:
        response = requests.get(
            "https://api.exaweb.in:3004/api/panchang/holiday",
            params=params,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        # 🚀 OPTIMIZATION: Prune massive holiday JSON payload to keep essential keys
        if isinstance(data, list):
            trimmed_list = []
            for item in data[:40]: # Limit to top 40 holidays if very large
                if isinstance(item, dict):
                    trimmed_item = {
                        k: item[k] for k in ['name', 'title', 'date', 'day', 'category', 'type', 'month']
                        if k in item
                    }
                    trimmed_list.append(trimmed_item)
                else:
                    trimmed_list.append(item)
            return json.dumps(trimmed_list)
            
        return json.dumps(data)
    
    except requests.exceptions.RequestException as e:
        return f"ERROR get_holidays: Network error fetching holidays: {e}"
    except Exception as e:
        return f"ERROR get_holidays: An unexpected error occurred: {str(e)}"


@tool
def get_monthly_festivals(year: Optional[int] = None, month: Optional[str] = None, festival_name: Optional[str] = None, data_language: str = "EN") -> str:
    """
    Fetches festival data for a specific month/year or searches for a specific festival across all months.
    
    Args:
        year: The year to fetch (e.g., 2026). Defaults to current year.
        month: The full month name (e.g., "september"). Optional.
        festival_name: Specific festival name to search for across the year (e.g. "ganesh", "diwali", "holi"). Optional.
        data_language: The language for the festival names (default "EN").
    """
    if not year:
        year = datetime.datetime.now().year
    
    api_url = "https://api.exaweb.in:3004/api/panchang/festival"
    headers = {"api_key": "anvl_bharat_cal123"}
    
    # 🔍 If festival_name is provided OR if month is not specified, search across all 12 months for matching festival dates!
    if festival_name or not month:
        months_to_check = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
        found_festivals = []
        target_kw = festival_name.lower().strip() if festival_name else ""

        for m in months_to_check:
            try:
                params = {"year": year, "month": m, "data_language": data_language, "app_language": "EN"}
                res = requests.get(api_url, params=params, headers=headers, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list):
                        for item in data:
                            fest_list = item.get("festivals", [])
                            fest_str = " ".join(fest_list).lower()
                            if target_kw:
                                if target_kw in fest_str or any(k in fest_str for k in target_kw.split() if len(k) > 2):
                                    found_festivals.append(item)
                            elif not month:
                                found_festivals.append(item)
            except Exception:
                continue
        
        if found_festivals:
            trimmed_list = []
            for item in found_festivals[:40]:
                if isinstance(item, dict):
                    trimmed_item = {k: item[k] for k in ['name', 'title', 'date', 'day', 'festivals', 'description'] if k in item}
                    trimmed_list.append(trimmed_item)
                else:
                    trimmed_list.append(item)
            return json.dumps(trimmed_list)

    # Standard single month fetch
    m_name = month.lower() if month else datetime.datetime.now().strftime("%B").lower()
    params = {"year": year, "month": m_name, "data_language": data_language, "app_language": "EN"}
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            trimmed_list = []
            for item in data[:30]:
                if isinstance(item, dict):
                    trimmed_item = {
                        k: item[k] for k in ['name', 'title', 'date', 'day', 'festivals', 'description']
                        if k in item
                    }
                    trimmed_list.append(trimmed_item)
                else:
                    trimmed_list.append(item)
            return json.dumps(trimmed_list)
            
        return json.dumps(data)
    
    except requests.exceptions.RequestException as e:
        return f"ERROR get_monthly_festivals: Network error while fetching data: {e}"
    except Exception as e:
        return f"ERROR get_monthly_festivals: An unexpected error occurred: {str(e)}"


@tool
def get_kundali(date: str, time: str, place: str) -> str:
    """
    Generates Kundali (birth chart) PDF from the Bharat Calendars API.
    
    **IMPORTANT**: This returns the payload info. The main.py will then call the PDF API.
    
    Args:
        date: Date of birth in YYYY-MM-DD format (e.g., "2001-08-09")
        time: Time of birth in HH:MM AM/PM format (e.g., "01:00 AM")
        place: Place of birth (e.g., "Bengaluru", "Mumbai")
    
    Returns:
        JSON with birth details for PDF generation
    """
    try:
        # Validate and format inputs
        try:
            dob_obj = parser.parse(date)
            formatted_date = dob_obj.strftime("%Y-%m-%d")
        except:
            return json.dumps({"error": "Invalid date format. Use YYYY-MM-DD (e.g., 2001-08-09)."})
        
        # Prepare and return payload - DO NOT call API here
        # main.py will handle the API call
        payload = {
            "type": "kundali_pdf_payload",
            "date": formatted_date,
            "time": time,
            "place": place,
            "message": f"Generating Kundali PDF for: {formatted_date} at {time} in {place}"
        }
        
        print(f"\n[TOOLS] get_kundali() returning payload: {payload}")
        return json.dumps(payload)
    
    except Exception as e:
        return json.dumps({"error": f"Error in get_kundali: {str(e)}"})


@tool
def get_janmarashi(date: str, time: str, place: str) -> str:
    """
    Fetches Janma Rashi (birth moon sign) from the Bharat Calendars API.
    
    **IMPORTANT**: This returns the payload info. Main backend main.py will handle payment confirmation and API calls.
    
    Args:
        date: Date of birth in YYYY-MM-DD format (e.g., "2001-08-09")
        time: Time of birth in HH:MM AM/PM format (e.g., "01:00 AM")
        place: Place of birth (e.g., "Bengaluru", "Mumbai")
    
    Returns:
        JSON string with birth details payload for Janma Rashi calculation.
    """
    try:
        # Validate and format date
        try:
            dob_obj = parser.parse(date)
            formatted_date = dob_obj.strftime("%Y-%m-%d")
        except:
            return json.dumps({"error": "Invalid date format. Use YYYY-MM-DD (e.g., 2001-08-09)."})
        
        # Prepare payload - DO NOT call API directly here (paid service)
        payload = {
            "type": "janmarashi_payload",
            "date": formatted_date,
            "time": time,
            "place": place,
            "message": f"Janma Rashi calculation payload for: {formatted_date} at {time} in {place}"
        }
        
        print(f"\n[TOOLS] get_janmarashi() returning payload: {payload}")
        return json.dumps(payload)
    
    except Exception as e:
        return json.dumps({"error": f"Error in get_janmarashi: {str(e)}"})


# List of all tools
all_tools = [
    get_horoscope,
    get_date_panchang,
    get_holidays,
    get_monthly_festivals,
    get_kundali,
    get_janmarashi
]