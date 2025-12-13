#  AI Travel Booking Agent

A fully functional AI-powered travel booking agent built with Streamlit, Groq LLM (llama-3.3-70b-versatile), and PDF ticket generation.

##  Features

-  **Groq LLM Integration** - Powered by llama-3.3-70b-versatile for intelligent flight booking
-  **Streamlit UI** - Beautiful and intuitive web interface
-  **PDF Ticket Generator** - Automatic PDF generation for confirmed bookings
-  **Local JSON Storage** - All bookings saved locally in `bookings.json`
-  **View My Bookings** - Easy access to all your booking history
-  **Floating Chat Assistant** - Interactive AI assistant in the sidebar for travel help

##  Quick Start

### Prerequisites

- Python 3.8 or higher
- Groq API Key ([Get one here](https://console.groq.com/))

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd ai_research_agent
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Run the application:**
   ```bash
   streamlit run App.py
   ```

   The app will open in your default browser at `http://localhost:8501`

## 📖 Usage

### Booking a Flight

1. Enter your travel query in natural language, for example:
   - "Book flight from Patna to Bengaluru tomorrow"
   - "I need a flight from Delhi to Mumbai on 2025-12-25"
   - "Flight from Bangalore to Chennai today"

2. Click **" Search & Book"** button

3. The AI will extract flight details and show available flights

4. Click **"Book Now"** on your preferred flight

5. Download your ticket PDF immediately after booking

### Using the Chat Assistant

- The chat assistant is available in the sidebar (right side)
- Ask questions about:
  - Travel tips and recommendations
  - Booking processes
  - Flight information
  - General travel queries

### Viewing Your Bookings

- Click **" View My Bookings"** to see all your confirmed bookings
- Download PDF tickets for any previous booking
- View booking details including:
  - Booking ID
  - Route (Origin → Destination)
  - Date
  - Airline
  - Price

##  Project Structure

```
ai_research_agent/
├── App.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── bookings.json         # Local booking storage (auto-generated)
├── .env                  # Environment variables (create this)
└── README.md            # This file
```

##  Technical Details

### Technologies Used

- **Streamlit** - Web framework for the UI
- **Groq LLM** - Language model for flight extraction and chat
- **FPDF** - PDF generation for tickets
- **Python-dotenv** - Environment variable management
- **LangChain** - LLM integration framework

### Key Functions

- `extract_flight_details()` - Extracts flight information from natural language using Groq LLM
- `get_dummy_flights()` - Returns available flight options (can be replaced with real API)
- `save_booking()` - Saves booking to local JSON file
- `generate_pdf()` - Creates PDF ticket for confirmed bookings
- `get_chat_response()` - Handles chat assistant interactions

##  Features in Detail

### Natural Language Processing
The app uses Groq's llama-3.3-70b-versatile model to understand natural language queries and extract:
- Origin city
- Destination city
- Travel date (supports "today", "tomorrow", and specific dates)

### PDF Ticket Generation
Each booking automatically generates a professional PDF ticket containing:
- Booking ID
- Route information
- Date and time
- Airline details
- Price
- Booking timestamp

### Local Storage
All bookings are stored in `bookings.json` with the following structure:
```json
{
  "id": "BOOKING_ID",
  "origin": "CITY",
  "destination": "CITY",
  "date": "YYYY-MM-DD",
  "airline": "AIRLINE_NAME",
  "price": 5500,
  "time": "YYYY-MM-DD HH:MM:SS"
}
```

##  Environment Variables

Create a `.env` file with:
```env
GROQ_API_KEY=your_api_key_here
```

##  Notes

- The current implementation uses dummy flight data. To integrate with real flight APIs, modify the `get_dummy_flights()` function.
- Bookings are stored locally in JSON format. For production use, consider using a database.
- The chat assistant maintains conversation context for the last 5 messages.

##  Troubleshooting

**Issue: "GROQ_API_KEY not found"**
- Make sure you've created a `.env` file with your API key
- Verify the key is correct and has proper permissions

**Issue: "Module not found"**
- Run `pip install -r requirements.txt` to install all dependencies
- Make sure your virtual environment is activated

**Issue: PDF generation fails**
- Ensure `fpdf2` is installed: `pip install fpdf2`

##  Future Enhancements

- Integration with real flight booking APIs (Amadeus, Skyscanner, etc.)
- Hotel booking capabilities
- Multi-user support with authentication
- Email notifications for bookings
- Payment gateway integration
- Database storage instead of JSON

##  License

This project is open source and available for educational purposes.

##  Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

---

**Built with using Streamlit, Groq LLM, and FPDF**
