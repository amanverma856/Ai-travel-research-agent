import os
from dotenv import load_dotenv
from amadeus import Client, ResponseError

# ✅ Load environment variables
load_dotenv()

# ✅ Initialize Amadeus client using .env variables
amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
)

try:
    response = amadeus.reference_data.locations.get(keyword='DEL', subType='AIRPORT')
    print("✅ Connection successful!")
    print(response.data[0])
except ResponseError as error:
    print("❌ Connection failed:", error)
