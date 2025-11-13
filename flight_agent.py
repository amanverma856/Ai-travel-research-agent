import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv

load_dotenv()

amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
)

# 🔍 Helper: Convert city name to IATA airport code
def get_airport_code(city_name):
    try:
        response = amadeus.reference_data.locations.get(
            keyword=city_name,
            subType="CITY,AIRPORT"
        )
        if response.data:
            return response.data[0]["iataCode"]
        else:
            return None
    except ResponseError:
        return None

def book_flight(origin, destination, date="2025-11-20"):
    try:
        # Convert names to IATA codes if needed
        origin_code = origin.upper() if len(origin) == 3 else get_airport_code(origin)
        destination_code = destination.upper() if len(destination) == 3 else get_airport_code(destination)

        if not origin_code or not destination_code:
            return f"⚠️ Could not find valid airport codes for {origin} or {destination}."

        # Step 1: Search flights
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin_code,
            destinationLocationCode=destination_code,
            departureDate=date,
            adults=1,
            max=1
        )

        if not response.data:
            return f"⚠️ No flights found between {origin_code} and {destination_code}."

        flight_offer = response.data[0]
        price = flight_offer["price"]["total"]
        airline = flight_offer["validatingAirlineCodes"][0]

        # Step 2: Traveler info (sandbox)
        traveler = {
            "id": "1",
            "dateOfBirth": "1990-01-01",
            "name": {"firstName": "Aman", "lastName": "Verma"},
            "gender": "MALE",
            "contact": {
                "emailAddress": "aman@example.com",
                "phones": [{
                    "deviceType": "MOBILE",
                    "countryCallingCode": "91",
                    "number": "9999999999"
                }]
            },
            "documents": [{
                "documentType": "PASSPORT",
                "birthPlace": "IN",
                "issuanceLocation": "IN",
                "issuanceDate": "2020-01-01",
                "number": "X1234567",
                "expiryDate": "2030-01-01",
                "issuanceCountry": "IN",
                "validityCountry": "IN",
                "nationality": "IN",
                "holder": True
            }]
        }

        # Step 3: Try booking
        booking = amadeus.booking.flight_orders.post([flight_offer], [traveler])
        return f"✅ Booking successful (sandbox)! Airline: {airline} | Price: ₹{price}"

    except ResponseError as e:
        if hasattr(e, 'response') and e.response and e.response.body:
            return f"❌ Amadeus API Error: {e.response.status_code}\nDetails: {e.response.body}"
        else:
            return f"❌ Amadeus API Error: {str(e)}"
    except Exception as e:
        return f"⚠️ Unexpected Error: {str(e)}"
