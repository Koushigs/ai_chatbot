import datetime
import json
import requests
import pytz
from dateutil import parser
from typing import Optional, Literal
from langchain.tools import tool


@tool
def get_horoscope(sign: str, date: str = None, language: str = "EN") -> str:
    """
    Fetches the horoscope for a given zodiac sign and date from the ExaWeb API.
    Defaults to today if no date is provided.

    Args:
        sign: Zodiac sign (e.g., Aries, Taurus, Gemini).
        date: Date in any recognizable format (optional).
        language: Language code (e.g., 'EN' for English, 'HI' for Hindi).
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

        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        data = response.json()
        sign_data = data.get(sign.upper())

        if sign_data:
            return json.dumps(sign_data)
        
        return f"INFO: No horoscope found for sign: {sign}"

    except requests.exceptions.RequestException as e:
        return f"ERROR: [get_horoscope]: Network error while fetching horoscope: {e}"
    except Exception as e:
        return f"ERROR: [get_horoscope]: An unexpected error occurred: {str(e)}"



@tool
def get_date_panchang(date: str = None, data_language: str = "EN") -> str:
    """
    Fetches the Panchang data for a given date.
    If the user does not provide a date, use today's real date.

    Args:
        date: Date in any format (optional).
        data_language: Language of the Panchang data (e.g., 'EN' for English, 'HI' for Hindi).
    """
    try:
        if not date:
            now = datetime.datetime.now()
        else:
            now = parser.parse(date)
        
        api_date = now.strftime("%d/%m/%y")
        
        url = (
            f"https://api.exaweb.in:3004/api/panchang/daily?"
            f"date={api_date}&app_language=EN&data_language={data_language}"
        )
        headers = {"api_key": "anvl_bharat_cal123"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict) or not data:
            return "ERROR: [get_date_panchang]: Received empty or invalid data from API."

        # Simplified formatting for clarity
        return json.dumps(data)

    except requests.exceptions.RequestException as e:
        return f"ERROR: [get_date_panchang]: Network error while fetching Panchang: {e}"
    except Exception as e:
        return f"ERROR: [get_date_panchang]: An unexpected error occurred: {str(e)}"



@tool
def get_holidays(year: int = None, data_language: str = "EN") -> str:
    """
    Fetches holidays from all categories for a given year from ExaWeb API.

    Args:
        year: Year (e.g., 2025). Optional — defaults to current year.
        data_language: Data language for holidays (default: "EN").
    """
    if not year:
        year = datetime.datetime.now().year
        
    params = {"data_language": data_language, "year": year}
    headers = {"api_key": "anvl_bharat_cal123"}

    try:
        response = requests.get(
            "https://api.exaweb.in:3004/api/panchang/holiday",
            params=params,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        return json.dumps(data)

    except requests.exceptions.RequestException as e:
        return f"ERROR: [get_holidays]: Network error fetching holidays: {e}"
    except Exception as e:
        return f"ERROR: [get_holidays]: An unexpected error occurred: {str(e)}"



@tool
def get_monthly_festivals(year: Optional[int] = None, month: Optional[str] = None, data_language: str = "EN") -> str:
    """
    Fetches festival data for a specific month and year from the ExaWeb API.
    
    Args:
        year: The year to fetch (e.g., 2025). Defaults to current year.
        month: The full month name to fetch (e.g., "june"). Defaults to current month.
        data_language: The language for the festival names (default: "EN").
    """
    if not year:
        year = datetime.datetime.now().year
    if not month:
        month = datetime.datetime.now().strftime("%B").lower()
    else:
        month = month.lower()

    api_url = "https://api.exaweb.in:3004/api/panchang/festival"
    params = {"year": year, "month": month, "data_language": data_language}
    headers = {"api_key": "anvl_bharat_cal123"}

    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        return json.dumps(data)

    except requests.exceptions.RequestException as e:
        return f"ERROR: [get_monthly_festivals]: Network error while fetching data: {e}"
    except Exception as e:
        return f"ERROR: [get_monthly_festivals]: An unexpected error occurred: {str(e)}"
@tool
def get_kundali(name: str, date_of_birth: str, time_of_birth: str, place_of_birth: str, language: str = "EN") -> str:
    """
    Fetches Kundali (birth chart) data from the ExaWeb API.
    
    Args:
        name: Person's full name
        date_of_birth: Date of birth in DD-MM-YYYY format
        time_of_birth: Time of birth in HH:MM format (24-hour)
        place_of_birth: Place/city of birth
        language: Language code ('EN', 'HI', etc.)
    """
    try:
        try:
            dob_obj = parser.parse(date_of_birth)
            formatted_dob = dob_obj.strftime("%d-%m-%Y")
        except:
            return "ERROR: Invalid date format. Use DD-MM-YYYY (e.g., 15-08-1990)."
        
        try:
            time_parts = time_of_birth.split(':')
            if len(time_parts) != 2:
                raise ValueError()
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except:
            return "ERROR: Invalid time format. Use HH:MM in 24-hour format (e.g., 10:30)."
        
        params = {
            "name": name,
            "dob": formatted_dob,
            "tob": time_of_birth,
            "place": place_of_birth,
            "language": language
        }
        
        url = "https://api.exaweb.in:3004/api/kundali"
        headers = {"api_key": "anvl_bharat_cal123"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data:
            return json.dumps(data)
        return "No Kundali data found for the given details."
        
    except requests.exceptions.RequestException as e:
        return f"ERROR: Network error while fetching Kundali: {str(e)}"
    except Exception as e:
        return f"ERROR: {str(e)}"


@tool
def get_janmarashi(date_of_birth: str, time_of_birth: str = None, language: str = "EN") -> str:
    """
    Fetches Janma Rashi (birth moon sign) from the ExaWeb API.
    
    Args:
        date_of_birth: Date of birth in DD-MM-YYYY format
        time_of_birth: Time of birth in HH:MM format (optional)
        language: Language code ('EN', 'HI', etc.)
    """
    try:
        try:
            dob_obj = parser.parse(date_of_birth)
            formatted_dob = dob_obj.strftime("%d-%m-%Y")
        except:
            return "ERROR: Invalid date format. Use DD-MM-YYYY (e.g., 15-08-1990)."
        
        params = {
            "dob": formatted_dob,
            "language": language
        }
        
        if time_of_birth:
            try:
                time_parts = time_of_birth.split(':')
                if len(time_parts) == 2:
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        params["tob"] = time_of_birth
            except:
                pass
        
        url = "https://api.exaweb.in:3004/api/janmarashi"
        headers = {"api_key": "anvl_bharat_cal123"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data:
            return json.dumps(data)
        return "No Janma Rashi data found for the given date."
        
    except requests.exceptions.RequestException as e:
        return f"ERROR: Network error while fetching Janma Rashi: {str(e)}"
    except Exception as e:
        return f"ERROR: {str(e)}"


# List of all tools available in the module

all_tools = [
    get_horoscope, 
    get_date_panchang, 
    get_holidays, 
    get_monthly_festivals,
    get_kundali,          
    get_janmarashi 
]

