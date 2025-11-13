import os
from dotenv import load_dotenv
from amadeus import Client, ResponseError

# Load environment variables
load_dotenv()

amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
)

try:
    print("🔍 Searching for cheapest flight from DEL to BOM...")
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode='DEL',
        destinationLocationCode='BOM',
        departureDate='2025-11-20',
        adults=1,
        max=3
    )

    print("✅ Available Flights:\n")
    for i, flight in enumerate(response.data, start=1):
        airline = flight["validatingAirlineCodes"][0]
        price = flight["price"]["total"]
        print(f"{i}. ✈️ Airline: {airline} | 💰 Price: ₹{price}")

    # ✅ Select the first flight
    flight_offer = response.data[0]

    print("\n🧾 Booking flight, please wait...")

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

    # ✅ New SDK (v12) expects two positional arguments
    booking = amadeus.booking.flight_orders.post(
        [flight_offer],  # first argument: flight offers list
        [traveler]       # second argument: traveler list
    )

    print("✅ Booking successful (sandbox simulation):")
    print(booking.data)

except ResponseError as error:
    print("❌ Amadeus API Error:", error)
except Exception as error:
    print("⚠️ General Error:", error)
