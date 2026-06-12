import requests
from dotenv import load_dotenv
from pathlib import Path
import os
import pandas as pd
import json

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
EMAIL = "b.caissotti.di.chiusano@student.uva.nl"
PASSWORD = os.getenv("PASSWORD")


# Get token
#response = requests.post(
#    "https://api.wattnet.eu/token-request/get_token",
#    json={
#        "email": EMAIL,
#        "password": PASSWORD
#    }
#)

#token = response.json()["access_token"]
token=None

IFCA_LAT = 43.47160739353177
IFCA_LON = -3.8022087210355364
START_DATE = "2024-12-14T00:00:00Z"
END_DATE = "2025-04-13T23:59:59Z"

#scopes = ["operational", "life-cycle"]
#footprint_types = ["carbon", "water"]

#for ft in footprint_types:
    #for scope in scopes:
# Query  footprints
response = requests.get(
    "https://api.wattnet.eu/v1/footprints",
    headers={
        "Authorization": f"Bearer {token}"
    },
    params={
        "lat": IFCA_LAT,
        "lon": IFCA_LON,
        "footprint_type": ft,
        "scope": scope,
        "start": START_DATE,
        "end": END_DATE
    }
)

    #column_name = f"{ft}_{scope}"
    
# TODO: also want to get water
print(response.status_code)

print(response.json())
response_data = response.json()[0]

series = response_data["series"]
cf = series[0]["values"]
df = pd.DataFrame(cf, columns=["timestamp", "carbon_footprint", "water_footprint"])
df.to_csv("datasets/entsoe_wattnet/carbon_footprints.csv", index=False)