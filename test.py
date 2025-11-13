import os
from dotenv import load_dotenv
from amadeus import Client, ResponseError

# Load environment variables
load_dotenv()

# Initialize Amadeus client
amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
)

try:
    # Step 1: Search for flights (Delhi → Mumbai)
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode='DEL',
        destinationLocationCode='BOM',
        departureDate='2025-11-13',
        adults=1,
        max=3
    )

    print("✅ Available Flights:\n")
    for i, flight in enumerate(response.data, start=1):
        price = flight['price']['total']
        airline = flight['validatingAirlineCodes'][0]
        print(f"{i}. ✈️ Airline: {airline} | 💰 Price: ₹{price}")

    # Step 2: Select first flight
    selected_flight = response.data[0]

    # Step 3: Book flight
    print("\n🧾 Booking flight, please wait...")

    booking = amadeus.booking.flight_orders.post(
        data={
            "type": "flight-order",
            "flightOffers": [selected_flight],
            "travelers": [
                {
                    "id": "1",
                    "dateOfBirth": "1995-05-05",
                    "name": {"firstName": "Aman", "lastName": "Verma"},
                    "gender": "MALE",
                    "contact": {
                        "emailAddress": "aman@example.com",
                        "phones": [
                            {
                                "deviceType": "MOBILE",
                                "countryCallingCode": "91",
                                "number": "9876543210"
                            }
                        ]
                    }
                }
            ]
        }
    )

    print("\n✅ Booking Confirmed!")
    print("Booking Reference:", booking.data["id"])
    print("Airline:", selected_flight["validatingAirlineCodes"][0])
    print("Total Price: ₹", selected_flight["price"]["total"])

except ResponseError as error:
    print("❌ Error:", error)
