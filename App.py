import streamlit as st
import os
import json
import re
import requests
from dotenv import load_dotenv
from amadeus import Client, ResponseError
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from duckduckgo_search import DDGS

# Load environment variables
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
amadeus_id = os.getenv("AMADEUS_CLIENT_ID")
amadeus_secret = os.getenv("AMADEUS_CLIENT_SECRET")
aviationstack_key = os.getenv("AVIATIONSTACK_API_KEY")

# --- Streamlit App Title ---
st.title("🧠 AI Travel Research Agent")
st.subheader("Ask me to find or book a flight:")

# --- Custom CSS for Beautiful UI ---
st.markdown("""
    <style>
    body {
        background-color: #0d1117;
        color: #f0f6fc;
    }
    .stTextInput > div > div > input {
        background-color: #161b22;
        color: white;
        border-radius: 10px;
        border: 1px solid #30363d;
        padding: 10px;
    }
    .stButton button {
        background-color: #238636;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #2ea043;
        transform: scale(1.05);
    }
    .flight-card {
        background-color: #1c1f26;
        padding: 15px;
        border-radius: 12px;
        margin: 8px 0;
        box-shadow: 0px 2px 5px rgba(255,255,255,0.05);
    }
    </style>
""", unsafe_allow_html=True)

query = st.text_input("Enter your query (e.g., 'Book flight from Delhi to Mumbai tomorrow'):")

# --- Amadeus client ---
amadeus = Client(client_id=amadeus_id, client_secret=amadeus_secret)

# --- Get global airport codes using AviationStack API ---
import requests

def get_airport_code(city_name):
    """Get IATA airport code using AviationStack API or fallback dictionary."""
    api_key = os.getenv("AVIATIONSTACK_API_KEY")

    # 🌍 Predefined fallback for major global cities
    fallback_airports = {
        "paris": "CDG", "london": "LHR", "new york": "JFK", "tokyo": "HND",
        "dubai": "DXB", "sydney": "SYD", "toronto": "YYZ", "singapore": "SIN",
        "berlin": "BER", "madrid": "MAD", "rome": "FCO", "bangkok": "BKK",
        "los angeles": "LAX", "san francisco": "SFO", "chicago": "ORD",
        "hong kong": "HKG", "amsterdam": "AMS", "seoul": "ICN",
        "istanbul": "IST", "melbourne": "MEL", "shanghai": "PVG",
        "delhi": "DEL", "mumbai": "BOM", "goa": "GOI"
    }

    city_key = city_name.lower().strip()
    if city_key in fallback_airports:
        return fallback_airports[city_key]

    if not api_key:
        st.warning("⚠️ AVIATIONSTACK_API_KEY missing in .env file")
        return None

    try:
        st.info(f"🌍 Searching airport for {city_name} ...")
        url = f"http://api.aviationstack.com/v1/airports?access_key={api_key}&search={city_name}"
        response = requests.get(url).json()

        # Parse data
        if "data" in response and len(response["data"]) > 0:
            code = response["data"][0].get("iata_code")
            if code:
                st.success(f"✅ Found airport code for {city_name}: {code}")
                return code

        # Fallback if empty
        st.warning(f"⚠️ No airport found for '{city_name}', using AI correction...")
        return None

    except Exception as e:
        st.error(f"Error fetching airport code: {e}")
        return None


# --- Extract flight details using Groq ---
def extract_flight_details(user_query):
    try:
        llm = ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile")
        prompt = PromptTemplate(
            input_variables=["query"],
            template=(
                "You are an intelligent flight booking assistant. "
                "Extract these details from the user's message if present:\n"
                "- origin city (3-letter airport code or full city name)\n"
                "- destination city (3-letter airport code or full city name)\n"
                "- departure date (in YYYY-MM-DD format; if 'tomorrow', convert to date)\n\n"
                "Treat common spelling mistakes like 'tommorow' as 'tomorrow'.\n"
                "User message: {query}\n\n"
                "Respond ONLY in JSON like this:\n"
                "{{\"origin\": \"DEL\", \"destination\": \"BOM\", \"date\": \"2025-11-13\"}}"
            ),
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        result = chain.run(query=user_query)

        json_str = re.search(r'\{.*\}', result, re.DOTALL).group()
        details = json.loads(json_str)
        return details
    except Exception as e:
        st.warning(f"⚠️ Could not extract flight details: {e}")
        return None

# --- Search flights using Amadeus API ---
def search_flights(origin, destination, date):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin.upper(),
            destinationLocationCode=destination.upper(),
            departureDate=date,
            adults=1,
            max=3
        )
        if not response.data:
            return f"⚠️ No flights found between {origin} and {destination}."
        results = []
        for flight in response.data:
            airline = flight['validatingAirlineCodes'][0]
            price = flight['price']['total']
            results.append(f"✈️ Airline: {airline} | 💰 Price: ₹{price}")
        return "\n".join(results)
    except ResponseError as error:
        return f"❌ Amadeus API Error: {error}"

# --- Save booking locally ---
def save_booking(origin, destination, date, price):
    booking = {
        "origin": origin,
        "destination": destination,
        "date": date,
        "price": price
    }
    if os.path.exists("bookings.json"):
        with open("bookings.json", "r") as f:
            data = json.load(f)
    else:
        data = []
    data.append(booking)
    with open("bookings.json", "w") as f:
        json.dump(data, f, indent=4)

# --- Auto Booking Logic ---
def auto_book_flight(user_query):
    st.info("🧠 Auto Booking Mode Enabled...")
    details = extract_flight_details(user_query)
    if not details:
        st.warning("⚠️ Could not extract flight details from your message.")
        return

    origin = details.get("origin")
    destination = details.get("destination")
    date = details.get("date")

    # Try local city map first
    airport_codes = {
        "delhi": "DEL", "dlh": "DEL",
        "mumbai": "BOM", "bombay": "BOM",
        "bangalore": "BLR", "bengaluru": "BLR",
        "chennai": "MAA", "madras": "MAA",
        "hyderabad": "HYD", "pune": "PNQ",
        "goa": "GOI", "kolkata": "CCU",
        "ahmedabad": "AMD", "jaipur": "JAI",
        "lucknow": "LKO", "indore": "IDR"
    }

    origin_code = airport_codes.get(origin.lower())
    destination_code = airport_codes.get(destination.lower())

    # Then try global lookup via AviationStack
    if not origin_code:
        origin_code = get_airport_code(origin)
    if not destination_code:
        destination_code = get_airport_code(destination)

    # Fallback to uppercase values
    origin = origin_code or origin.upper()
    destination = destination_code or destination.upper()

    st.info(f"🔍 Searching for flights from {origin} to {destination} on {date}...")
    result = search_flights(origin, destination, date)

    st.info("🤖 Hi Aman! I found these amazing flights for you 🚀")

    flights = result.split("\n")
    for line in flights:
        if "Airline:" in line:
            airline = line.split("Airline:")[1].split("|")[0].strip()
            price = line.split("₹")[1].strip()
            st.markdown(f"""
            <div class="flight-card">
                <h4>✈️ {airline}</h4>
                <p>💰 Price: ₹{price}</p>
                <button style="
                    background-color:#2ea043;
                    color:white;
                    border:none;
                    padding:8px 12px;
                    border-radius:6px;
                    cursor:pointer;">Book Now</button>
            </div>
            """, unsafe_allow_html=True)

    # Auto-book cheapest flight (simulation)
    prices = [float(p) for p in re.findall(r'₹([\d.]+)', result)]
    if prices:
        cheapest = min(prices)
        save_booking(origin, destination, date, cheapest)
        st.balloons()
        st.success(f"✅ Auto-booked the cheapest flight at ₹{cheapest}")

# --- Web search (non-flight queries) ---
def web_search(query):
    with DDGS() as ddgs:
        results = [r["body"] for r in ddgs.text(query, max_results=5)]
    return "\n\n".join(results)

# --- Main Action Button ---
if st.button("Analyze / Book"):
    if "flight" in query.lower():
        auto_book_flight(query)
    else:
        if not groq_key:
            st.error("⚠️ Missing GROQ_API_KEY in .env file!")
        else:
            st.info("🔍 Searching the web...")
            data = web_search(query)
            st.info("🧠 Analyzing with Groq AI...")

            llm = ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile")
            prompt = PromptTemplate(
                input_variables=["topic", "data"],
                template="Summarize and explain key insights about '{topic}' using this web data:\n\n{data}",
            )
            chain = LLMChain(llm=llm, prompt=prompt)
            response = chain.run(topic=query, data=data)

            st.success("🧩 Summary:")
            st.write(response)

# --- View My Bookings Button ---
if st.button("📜 View My Bookings"):
    if os.path.exists("bookings.json"):
        with open("bookings.json", "r") as f:
            bookings = json.load(f)
        for b in bookings:
            st.markdown(f"<div class='flight-card'>🧾 {b['origin']} → {b['destination']} on {b['date']} | ₹{b['price']}</div>", unsafe_allow_html=True)
    else:
        st.info("No bookings found yet.")
        # --- AI Chat Mode ---
st.markdown("---")
st.header("💬 Chat with AI Travel Assistant")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Display previous messages
for chat in st.session_state["chat_history"]:
    role, message = chat
    if role == "user":
        st.markdown(f"🧑‍💻 **You:** {message}")
    else:
        st.markdown(f"🤖 **Assistant:** {message}")

# Chat input box
user_input = st.text_input("Type your message here (e.g., 'Find flights to Paris this weekend'):")

if user_input:
    st.session_state["chat_history"].append(("user", user_input))
    st.chat_message("assistant")
    st.info("🤔 Thinking...")

    llm = ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile")
    prompt = PromptTemplate(
        input_variables=["query"],
        template=("You are a friendly AI Travel Agent that helps users find flights, "
                  "destinations, and trip ideas. Answer briefly and helpfully.\n\n"
                  "User: {query}")
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.run(query=user_input)

    st.session_state["chat_history"].append(("assistant", response))
    st.success(f"🤖 {response}")

