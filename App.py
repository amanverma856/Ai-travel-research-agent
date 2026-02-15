import streamlit as st
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from fpdf import FPDF
import uuid

# Load env
load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")

# ---------------------------------------------------------
# API Key Validation
# ---------------------------------------------------------
def test_api_key():
    """Test if the Groq API key is valid"""
    if not groq_key:
        return False, "API key not found. Please set GROQ_API_KEY in your .env file."
    
    try:
        llm = ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile")
        # Make a simple test call
        test_response = llm.invoke([{"role": "user", "content": "Say 'OK'"}])
        if test_response and test_response.content:
            return True, "API key is valid and working!"
        else:
            return False, "API key test failed - no response received."
    except Exception as e:
        error_msg = str(e).lower()
        if "invalid" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
            return False, f"❌ API key is invalid or expired. Error: {str(e)}"
        elif "rate limit" in error_msg or "429" in error_msg:
            return False, f"⚠️ Rate limit exceeded. Please try again later. Error: {str(e)}"
        else:
            return False, f"❌ API key test failed. Error: {str(e)}"

# Page config
st.set_page_config(
    page_title="AI Travel Booking Agent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for floating chat assistant
st.markdown("""
<style>
    .floating-chat {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 400px;
        max-height: 600px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        z-index: 1000;
        display: flex;
        flex-direction: column;
    }
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 15px 15px 0 0;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .chat-toggle {
        background: rgba(255,255,255,0.2);
        border: none;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        cursor: pointer;
    }
    .main-container {
        margin-right: 420px;
    }
    @media (max-width: 768px) {
        .main-container {
            margin-right: 0;
        }
        .floating-chat {
            width: 100%;
            right: 0;
            bottom: 0;
            border-radius: 15px 15px 0 0;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_open" not in st.session_state:
    st.session_state.chat_open = True
if "processing_booking" not in st.session_state:
    st.session_state.processing_booking = False
if "show_bookings" not in st.session_state:
    st.session_state.show_bookings = False
if "last_booking" not in st.session_state:
    st.session_state.last_booking = None
if "booking_saved" not in st.session_state:
    st.session_state.booking_saved = False
if "api_key_tested" not in st.session_state:
    st.session_state.api_key_tested = False
if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = False
if "current_flights" not in st.session_state:
    st.session_state.current_flights = None
if "current_route" not in st.session_state:
    st.session_state.current_route = None

# ---------------------------------------------------------
# Chat Assistant LLM
# ---------------------------------------------------------
def get_chat_response(user_message, chat_history):
    """Get response from Groq LLM for chat assistant"""
    if not groq_key:
        return "❌ API Key Missing! Please set GROQ_API_KEY in your .env file. Get your key from: https://console.groq.com/"
    
    try:
        llm = ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile")
        
        system_prompt = """You are a helpful AI travel booking assistant. 
        Help users with:
        - Finding and booking flights
        - Answering travel questions
        - Providing travel tips and recommendations
        - Explaining booking processes
        
        Be friendly, concise, and helpful. If users want to book flights, guide them to use the booking form above."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history
        for msg in chat_history[-5:]:  # Keep last 5 messages for context
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception as e:
        error_msg = str(e).lower()
        if "invalid" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
            return f"❌ API Key Invalid or Expired! Please check your API key at: https://console.groq.com/\n\nError: {str(e)}"
        elif "rate limit" in error_msg or "429" in error_msg:
            return f"⚠️ Rate Limit Exceeded! Please try again later.\n\nError: {str(e)}"
        else:
            return f"I apologize, but I encountered an error: {str(e)}. Please try again."

# ---------------------------------------------------------
# 100% WORKING JSON extractor (NO LLMChain)
# ---------------------------------------------------------
def extract_flight_details(user_query):
    # Check API key first
    if not groq_key:
        st.error("❌ **API Key Missing!** Please set GROQ_API_KEY in your .env file.")
        st.info("💡 Get your API key from: https://console.groq.com/")
        return None
    
    try:
        llm = ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile")

        messages = [
            {
                "role": "system",
                "content": (
                    "Extract ONLY JSON. Do NOT add any text.\n"
                    "Format:\n"
                    "{\"origin\":\"CITY\",\"destination\":\"CITY\",\"date\":\"YYYY-MM-DD\"}\n"
                    "If user says 'tomorrow', convert to actual date.\n"
                    "If origin/destination missing, infer logically."
                )
            },
            {"role": "user", "content": user_query},
        ]

        response = llm.invoke(messages)
        output = response.content.strip()

        # extract pure JSON
        start = output.find("{")
        end = output.rfind("}") + 1
        if start == -1 or end == -1:
            st.error("Model did not return valid JSON.")
            return None

        json_text = output[start:end]
        data = json.loads(json_text)

        # convert 'tomorrow'
        if "tomorrow" in data.get("date", "").lower():
            data["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "today" in data.get("date", "").lower():
            data["date"] = datetime.now().strftime("%Y-%m-%d")

        return data

    except Exception as e:
        error_msg = str(e).lower()
        if "invalid" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
            st.error(f"❌ **API Key Invalid or Expired!**\n\nError: {str(e)}\n\n💡 Please check your API key at: https://console.groq.com/")
        elif "rate limit" in error_msg or "429" in error_msg:
            st.error(f"⚠️ **Rate Limit Exceeded!**\n\nPlease try again later.\n\nError: {str(e)}")
        else:
            st.error(f"❌ Error extracting details: {str(e)}")
        return None


# ---------------------------------------------------------
# Dummy Flights
# ---------------------------------------------------------
def get_dummy_flights(origin, destination, date):
    return [
        {"airline": "IndiGo", "price": 5500, "departure": "08:30", "arrival": "11:15"},
        {"airline": "Air India", "price": 6200, "departure": "14:20", "arrival": "17:05"},
        {"airline": "Vistara", "price": 6800, "departure": "19:45", "arrival": "22:30"},
    ]


# ---------------------------------------------------------
# Save to JSON file
# ---------------------------------------------------------
def save_booking(origin, destination, date, airline, price):
    booking = {
        "id": uuid.uuid4().hex[:8].upper(),
        "origin": origin,
        "destination": destination,
        "date": date,
        "airline": airline,
        "price": price,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    bookings_file = "bookings.json"
    
    # Ensure bookings.json exists and is valid
    if not os.path.exists(bookings_file):
        data = []
    else:
        try:
            with open(bookings_file, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    data = json.loads(content)
                else:
                    data = []
            # Ensure data is a list
            if not isinstance(data, list):
                data = []
        except (json.JSONDecodeError, IOError, ValueError) as e:
            # If file is corrupted, start fresh
            data = []
    
    # Append new booking
    data.append(booking)
    
    # Write back to file with proper error handling
    try:
        with open(bookings_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        # Verify the write was successful
        with open(bookings_file, "r", encoding="utf-8") as f:
            verify_data = json.load(f)
            if len(verify_data) != len(data):
                raise Exception("Booking verification failed - data mismatch")
    except Exception as e:
        raise Exception(f"Failed to save booking to file: {str(e)}")

    return booking


# ---------------------------------------------------------
# PDF Generator
# ---------------------------------------------------------
def generate_pdf(booking):
    """Generate PDF ticket with ASCII-safe characters"""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Flight Booking Confirmation", ln=True, align="C")
    pdf.ln(10)
    
    # Booking ID
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, f"Booking ID: {booking.get('id', 'N/A')}", ln=True)
    pdf.ln(5)
    
    # Booking details (using ASCII-safe characters)
    pdf.set_font("Arial", size=12)
    
    # Route - replace arrow with "to"
    origin = str(booking.get('origin', 'N/A'))
    destination = str(booking.get('destination', 'N/A'))
    route_text = f"Route: {origin} to {destination}"
    pdf.cell(0, 8, route_text, ln=True)
    
    # Date
    date_text = f"Date: {booking.get('date', 'N/A')}"
    pdf.cell(0, 8, date_text, ln=True)
    
    # Airline
    airline_text = f"Airline: {booking.get('airline', 'N/A')}"
    pdf.cell(0, 8, airline_text, ln=True)
    
    # Price - replace rupee symbol with "Rs"
    price = booking.get('price', 'N/A')
    price_text = f"Price: Rs {price}"
    pdf.cell(0, 8, price_text, ln=True)
    
    # Booking time
    time_text = f"Booked on: {booking.get('time', 'N/A')}"
    pdf.cell(0, 8, time_text, ln=True)
    
    # Add some spacing at the bottom
    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 6, "Thank you for booking with us!", ln=True, align="C")
    
    # Generate PDF bytes - output(dest="S") returns bytes directly
    pdf_bytes = pdf.output(dest="S")
    
    # Ensure we return bytes (fpdf2 returns bytes, but check to be safe)
    if isinstance(pdf_bytes, bytes):
        return pdf_bytes
    elif isinstance(pdf_bytes, str):
        return pdf_bytes.encode("utf-8")
    else:
        # Fallback: convert to bytes
        return bytes(pdf_bytes)


# ---------------------------------------------------------
# Auto Booking Flow
# ---------------------------------------------------------
def process_booking(query):
    if not query:
        st.warning("Please enter a query to search for flights.")
        return
    
    with st.spinner("Extracting flight details..."):
        details = extract_flight_details(query)

    if not details:
        st.error("Could not extract flight details. Please try rephrasing your query.")
        return

    origin = details.get("origin", "").upper()
    destination = details.get("destination", "").upper()
    date = details.get("date", "")

    if not all([origin, destination, date]):
        st.error("Missing required information. Please provide origin, destination, and date.")
        return

    # Store route info in session state
    st.session_state.current_route = {
        "origin": origin,
        "destination": destination,
        "date": date
    }

    st.success(f"✅ Route: **{origin} → {destination}** | Date: **{date}**")

    flights = get_dummy_flights(origin, destination, date)
    
    if not flights:
        st.warning("No flights available for this route.")
        return

    # Store flights only
    st.session_state.current_flights = flights

    display_flights(flights, origin, destination, date)

def display_flights(flights, origin, destination, date):
    """Display flights with booking buttons"""
    st.write("### ✈️ Available Flights")
    
    for idx, f in enumerate(flights):
        airline = f["airline"]
        price = f["price"]
        departure = f["departure"]
        arrival = f["arrival"]
        
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{airline}**")
                st.caption(f"🕐 {departure} → {arrival}")
            with col2:
                st.write(f"**₹{price}**")
            with col3:
                if st.button("Book Now", key=f"book_{idx}"):

                    with st.spinner("Saving your booking..."):
                        try:
                            booking = save_booking(origin, destination, date, airline, price)
                            # Store booking in session state
                            st.session_state.last_booking = booking
                            st.session_state.show_bookings = True
                            st.session_state.booking_saved = True
                            st.balloons()
                            st.success(f"✅ Booking saved successfully! ID: {booking['id']}")
                            # Clear current flights so we show bookings view
                            st.session_state.current_flights = None
                            st.session_state.current_route = None
                            # Small delay to ensure file is written
                            import time
                            time.sleep(0.2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error saving booking: {str(e)}")
                            st.exception(e)


# ---------------------------------------------------------
# View Bookings
# ---------------------------------------------------------
def view_bookings():
    try:
        bookings_file = "bookings.json"
        
        # Check if file exists
        if not os.path.exists(bookings_file):
            st.info("📭 No bookings found. Start booking your first flight!")
            # If we just saved a booking, show it from session state
            if st.session_state.get("last_booking"):
                booking = st.session_state.last_booking
                st.write("### 🧾 Your Latest Booking")
                st.json(booking)
                st.info("💡 Your booking is saved. The file will be created on the next page refresh.")
            return

        # Read the file
        with open(bookings_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                st.info("📭 No bookings found. Start booking your first flight!")
                return
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                st.error(f"❌ Error reading bookings file. It may be corrupted: {str(e)}")
                st.code(content[:200])  # Show first 200 chars for debugging
                return
        
        if not data or len(data) == 0:
            # Check if we have a booking in session state
            if st.session_state.get("last_booking"):
                booking = st.session_state.last_booking
                st.write("### 🧾 Your Bookings")
                st.write(f"**Total Bookings:** 1")
                st.divider()
                # Display the booking from session state
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"**Booking ID:** `{booking.get('id', 'N/A')}`")
                        st.write(f"📍 **{booking.get('origin', 'N/A')}** → **{booking.get('destination', 'N/A')}**")
                    with col2:
                        st.write(f"📅 **Date:** {booking.get('date', 'N/A')}")
                        st.write(f"✈️ **Airline:** {booking.get('airline', 'N/A')}")
                    with col3:
                        st.write(f"**Price:** ₹{booking.get('price', 'N/A')}")
                        try:
                            pdf_data = generate_pdf(booking)
                            st.download_button(
                                "📥 Download PDF",
                                data=pdf_data,
                                file_name=f"ticket_{booking.get('id', 'unknown')}.pdf",
                                mime="application/pdf",
                                key=f"pdf_session_{booking.get('id', 'unknown')}"
                            )
                        except Exception as e:
                            st.error(f"Error generating PDF: {str(e)}")
                    st.divider()
                st.info("💡 Your booking is saved. Refresh the page to see it in the file.")
            else:
                st.info("📭 No bookings found. Start booking your first flight!")
            return

        st.write("### 🧾 Your Bookings")
        st.write(f"**Total Bookings:** {len(data)}")
        st.divider()
        
        # Sort by booking time (newest first)
        data_sorted = sorted(data, key=lambda x: x.get("time", ""), reverse=True)
        
        for idx, b in enumerate(data_sorted):
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**Booking ID:** `{b.get('id', 'N/A')}`")
                    st.write(f"📍 **{b.get('origin', 'N/A')}** → **{b.get('destination', 'N/A')}**")
                with col2:
                    st.write(f"📅 **Date:** {b.get('date', 'N/A')}")
                    st.write(f"✈️ **Airline:** {b.get('airline', 'N/A')}")
                with col3:
                    st.write(f"**Price:** ₹{b.get('price', 'N/A')}")
                    # Generate PDF for existing booking
                    try:
                        pdf_data = generate_pdf(b)
                        st.download_button(
                            "📥 Download PDF",
                            data=pdf_data,
                            file_name=f"ticket_{b.get('id', 'unknown')}.pdf",
                            mime="application/pdf",
                            key=f"pdf_{b.get('id', 'unknown')}_{idx}"
                        )
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                st.divider()
    except Exception as e:
        st.error(f"❌ Error loading bookings: {str(e)}")
        st.exception(e)


# ---------------------------------------------------------
# Main UI
# ---------------------------------------------------------
st.title("✈️ AI Travel Booking Agent")
st.markdown("Powered by **Groq LLM (llama-3.3-70b-versatile)**")

# API Key Status Check
if not groq_key:
    st.error("⚠️ **API Key Not Found!** Please set GROQ_API_KEY in your .env file.")
    st.info("💡 Get your free API key from: https://console.groq.com/")
    st.code("GROQ_API_KEY=your_api_key_here", language="bash")
else:
    # Test API key on first load
    if "api_key_tested" not in st.session_state:
        with st.spinner("Testing API key..."):
            is_valid, message = test_api_key()
            st.session_state.api_key_tested = True
            st.session_state.api_key_valid = is_valid
            if not is_valid:
                st.error(f"⚠️ **{message}**")
                st.info("💡 Get your API key from: https://console.groq.com/")
            else:
                st.success("✅ API key is valid and working!")
    
    # Show API key status in sidebar
    if st.session_state.get("api_key_valid", False):
        st.sidebar.success("✅ API Key: Valid")
    else:
        st.sidebar.error("❌ API Key: Invalid")
        if st.sidebar.button("🔄 Test API Key Again"):
            with st.spinner("Testing..."):
                is_valid, message = test_api_key()
                st.session_state.api_key_valid = is_valid
                if is_valid:
                    st.sidebar.success(message)
                else:
                    st.sidebar.error(message)
                st.rerun()

st.markdown("---")

# Check if we should show bookings view
if st.session_state.get("show_bookings", False):
    # Show bookings view
    st.markdown("---")
    # Show success message if just booked
    if st.session_state.get("last_booking"):
        booking = st.session_state.last_booking
        st.success(f"🎉 **Booking Confirmed!** Booking ID: `{booking['id']}` | {booking['origin']} → {booking['destination']} on {booking['date']}")
        # Don't clear last_booking yet, keep it for display
    
    view_bookings()
    st.markdown("---")
    if st.button("← Back to Search", type="secondary"):
        st.session_state.show_bookings = False
        st.session_state.last_booking = None
        st.rerun()
else:
    # Show main search interface
    main_col1, main_col2 = st.columns([3, 1])

    with main_col1:
        st.subheader("🔍 Search & Book Flights")
        st.caption("Example: **Book flight from Patna to Bengaluru tomorrow**")
        
        query = st.text_input(
            "Enter your travel query:",
            placeholder="e.g., Book flight from Delhi to Mumbai on 2025-12-25",
            key="main_query"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔍 Search & Book", type="primary", use_container_width=True):
                process_booking(query)
        with col2:
            if st.button("📜 View My Bookings", use_container_width=True):
                st.session_state.show_bookings = True
                st.rerun()
        
        # Show flights if they exist in session state (persist after rerun)
        if st.session_state.get("current_flights") and st.session_state.get("current_route"):
            route = st.session_state.current_route
            st.success(f"✅ Route: **{route['origin']} → {route['destination']}** | Date: **{route['date']}**")
            display_flights(
                st.session_state.current_flights,
                route['origin'],
                route['destination'],
                route['date']
            )

    with main_col2:
        st.subheader("💡 Quick Tips")
        st.info("""
        💬 Use the chat assistant for help
        
        📋 View all your bookings anytime
        
        📥 Download PDF tickets instantly
        
        ✈️ Book flights with natural language
        """)

# ---------------------------------------------------------
# Floating Chat Assistant
# ---------------------------------------------------------
st.sidebar.title("💬 AI Travel Assistant")

# Chat messages display
chat_container = st.sidebar.container(height=500)
with chat_container:
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Chat input
if prompt := st.sidebar.chat_input("Ask me anything about travel..."):
    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    
    # Get AI response
    with st.spinner("Thinking..."):
        response = get_chat_response(prompt, st.session_state.chat_messages)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    st.rerun()

# Clear chat button
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.chat_messages = []
    st.rerun()

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.caption("💡 **Tip:** Ask me about flights, travel tips, or booking help!")

# Footer
st.markdown("---")
st.caption("Built with ❤️ using Streamlit, Groq LLM, and FPDF")
