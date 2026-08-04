"""
FINAL COMPLETE main.py - HOROSCOPE DETECTION FIXED
Properly detects horoscope queries and passes to correct formatter
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from agent import app
from datetime import datetime
from langchain_core.messages import AIMessage
from product_formatter import (
    get_horoscope_recommendations, 
    get_panchang_recommendations,
    get_holidays_recommendations,
    get_monthly_festivals_recommendations,
    get_kundali_recommendations,
    get_janmarashi_recommendations,
    format_recommendations_html,
    is_astro_specific_query
)

api = FastAPI(
    title="Bharat Calendar AI API",
    description="Stateless LangGraph AI agent endpoint with smart product recommendations",
    version="1.0.0"
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    messages: List[Dict[str, str]]

def get_current_date_context():
    now = datetime.now()
    return f"For context, today's date is {now.strftime('%A, %B %d, %Y.')}"

def detect_tool_type(user_query: str, ai_response: str) -> str:
    """
    FIXED: Detect which tool was used - check user query FIRST
    """
    
    user_lower = user_query.lower()
    response_lower = ai_response.lower()
    combined = (user_lower + " " + response_lower).lower()
    
    print(f"\n=== DETECT TOOL TYPE ===")
    print(f"User: {user_lower[:50]}")
    print(f"Checking tool type...")
    
    # CRITICAL: Check user query first for these specific keywords
    if "kundali" in user_lower or "kundli" in user_lower or "birth chart" in user_lower:
        print("→ Tool: KUNDALI")
        return "kundali"
    
    if "janmarashi" in user_lower or "janma rashi" in user_lower or "moon sign" in user_lower:
        print("→ Tool: JANMARASHI")
        return "janmarashi"
    
    if "panchang" in user_lower or "muhurat" in user_lower or "tithi" in user_lower:
        print("→ Tool: PANCHANG")
        return "panchang"
    
    # HOROSCOPE: Check if user asked for horoscope OR just rashi sign
    if "horoscope" in user_lower:
        print("→ Tool: HOROSCOPE (keyword found)")
        return "horoscope"
    
    # Check if user provided zodiac sign (Leo, Aries, etc)
    rashi_names = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
                   "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    for rashi in rashi_names:
        if rashi in user_lower:
            print(f"→ Tool: HOROSCOPE (rashi '{rashi}' found)")
            return "horoscope"
    
    # Check response for horoscope indicators
    if "lucky number" in response_lower or "lucky color" in response_lower:
        print("→ Tool: HOROSCOPE (response has lucky number/color)")
        return "horoscope"
    
    # FESTIVALS: Check for specific festival keywords in user query
    festival_keywords = ["festival", "diwali", "dussehra", "holi", "navratri", 
                         "janmashtami", "ganesh", "rakhi", "makar sankranti"]
    for keyword in festival_keywords:
        if keyword in user_lower:
            print(f"→ Tool: MONTHLY_FESTIVALS (found '{keyword}')")
            return "monthly_festivals"
    
    # HOLIDAYS: Check for holiday-related keywords
    if "holiday" in user_lower or "celebration" in user_lower:
        print("→ Tool: HOLIDAYS")
        return "holidays"
    
    print("→ Tool: UNKNOWN")
    return None

@api.post("/invoke")
def invoke_agent(request: QueryRequest):
    """
    STATELESS API with SMART Product Recommendations
    FINAL VERSION: All tool detection and extraction working
    """
    
    current_messages = request.messages.copy()
    
    # Get ORIGINAL user query BEFORE date context injection
    original_user_query = current_messages[-1]['content'] if current_messages else ""
    
    # Inject date context only on first message
    if len(current_messages) == 1 and current_messages[0]["role"] == "user":
        current_messages[0]['content'] += f" ({get_current_date_context()})"
    
    inputs = {"messages": current_messages}
    final_ai_response = ""
    
    # Get response from agent
    try:
        for event in app.stream(inputs, stream_mode="values"):
            messages = event.get('messages', [])
            if messages:
                final_message = messages[-1]
                if isinstance(final_message, AIMessage) and not final_message.tool_calls:
                    final_ai_response = final_message.content
    except Exception as e:
        final_ai_response = f"Error: {str(e)}"
    
    # Build complete chat history
    complete_chat = current_messages + [{
        "role": "assistant",
        "content": final_ai_response
    }]
    
    # STEP 1: Check if it's an astro-specific query
    print(f"\n{'='*50}")
    print(f"STEP 1: Smart Detection")
    print(f"{'='*50}")
    is_specific_query = is_astro_specific_query(original_user_query)
    print(f"Result: is_specific_query = {is_specific_query}")
    
    recommendations = {}
    recommendations_html = ""
    tool_type = None
    
    # STEP 2: Detect tool type ONLY if it's a specific query
    if is_specific_query:
        print(f"\n{'='*50}")
        print(f"STEP 2: Detect Tool Type")
        print(f"{'='*50}")
        tool_type = detect_tool_type(original_user_query, final_ai_response)
        
        print(f"\n{'='*50}")
        print(f"STEP 3: Generate Recommendations")
        print(f"{'='*50}")
        
        try:
            if tool_type == "horoscope":
                print("Calling: get_horoscope_recommendations()")
                recommendations = get_horoscope_recommendations(final_ai_response)
                recommendations_html = format_recommendations_html("horoscope", recommendations)
                print(f"✅ Horoscope recommendations generated")
            
            elif tool_type == "panchang":
                print("Calling: get_panchang_recommendations()")
                recommendations = get_panchang_recommendations()
                recommendations_html = format_recommendations_html("panchang", recommendations)
                print(f"✅ Panchang recommendations generated")
            
            elif tool_type == "holidays":
                print("Calling: get_holidays_recommendations()")
                recommendations = {}
                recommendations_html = ""
                print(f"✅ Holidays (no recommendations)")
            
            elif tool_type == "monthly_festivals":
                print("Calling: get_monthly_festivals_recommendations()")
                recommendations = get_monthly_festivals_recommendations(final_ai_response)
                recommendations_html = format_recommendations_html("monthly_festivals", recommendations)
                print(f"✅ Monthly festivals recommendations generated")
            
            elif tool_type == "kundali":
                print("Calling: get_kundali_recommendations()")
                recommendations = get_kundali_recommendations(final_ai_response)
                recommendations_html = format_recommendations_html("kundali", recommendations)
                print(f"✅ Kundali recommendations generated")
            
            elif tool_type == "janmarashi":
                print("Calling: get_janmarashi_recommendations()")
                recommendations = get_janmarashi_recommendations(final_ai_response)
                recommendations_html = format_recommendations_html("janmarashi", recommendations)
                print(f"✅ Janmarashi recommendations generated")
        
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n⏭️  Skipping tool detection (not astro-specific)")
    
    # STEP 4: Append recommendations to response
    if is_specific_query and recommendations_html and recommendations_html.strip():
        final_ai_response += "\n\n" + recommendations_html
        print(f"\n✅ Recommendations appended to response")
    else:
        print(f"\n⏭️  No recommendations appended")
    
    print(f"{'='*50}\n")
    
    return {
        "response": final_ai_response,
        "messages": complete_chat,
        "recommendations": recommendations,
        "tool_detected": tool_type,
        "has_recommendations": bool(recommendations_html.strip()) if recommendations_html else False,
        "is_specific_query": is_specific_query
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="127.0.0.1", port=8000)