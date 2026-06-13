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
token="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJubkxEVEtJVkJBN3o5N3Zrbi1RWE5zQXFwSUNVQlQtam5fZ25mX2Z4TWdZIn0.eyJleHAiOjE3ODEzNTcxNDgsImlhdCI6MTc4MTI3MDc0OCwianRpIjoidHJydGNjOjAzY2FiNjFmLTkzZmUtNTVlZi00NDJhLTg4MzBkMDVkNzYyMSIsImlzcyI6Imh0dHBzOi8vYXV0aC53YXR0bmV0LmV1L3JlYWxtcy93YXR0bmV0IiwiYXVkIjpbIm9hdXRoMi1wcm94eSIsImFjY291bnQiXSwic3ViIjoiOTQ0NWUzODYtOGQzOS00ZDYxLTlmYzctZWEwMmIzNGY0MTEwIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoib2F1dGgyLXByb3h5IiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL2FwaS53YXR0bmV0LmV1Il0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLXdhdHRwcmludCIsIm9mZmxpbmVfYWNjZXNzIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6ImVtYWlsIHByb2ZpbGUiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiY2xpZW50SG9zdCI6IjE3Mi4xNi4zNS4xMjEiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJzZXJ2aWNlLWFjY291bnQtb2F1dGgyLXByb3h5IiwiY2xpZW50QWRkcmVzcyI6IjE3Mi4xNi4zNS4xMjEiLCJjbGllbnRfaWQiOiJvYXV0aDItcHJveHkifQ.lBEesQHpTsS9uJ_JTmAncRYRxqvelQL8FS5YzNwyMhsb5PZXR8pTRdr62FEQlDNDvM37U07WYiDStzfb_dV7xGUtAHedfj6tHYvg2p8mOBnlgyvkQemoVokTOCQM0yvAIJflEHJtQ0g3KTMNRr_m1A_Br-Sp0ilq7KJy6A9s_zUs6qZkPy2KOiSGlzQ8xTv96rOiBb-pPBxs0OUGCzzuyVlSNUHXlDyyRgB06Ip4L08piaRoUzbaMcw3NMbyGseJdE1qVgIZlm2sOd8j1qDJ9hhB_vCwwVgaLggo2g9BDZTHCgTsYX0pyJUWHx9DgrvfZo5eMM74pc4Ci4iNP4L-MQ"


IFCA_LAT = 43.47160739353177
IFCA_LON = -3.8022087210355364
START_DATE = "2024-12-14T00:00:00Z"
END_DATE = "2025-04-13T23:59:59Z"

scopes = ["operational", "life-cycle"]
footprint_types = ["carbon", "water"]
g_or_l = [True, False]
columns = {}
timestamps = None

for ft in footprint_types:
    for scope in scopes:
        for g in g_or_l:
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
                    "end": END_DATE,
                    "use_global": g
                }
            )
            
            print(f"{response.status_code} - {ft}_{scope}_{'global' if g else 'local'}")
            response_data = response.json()[0]
            cf = response_data["series"][0]["values"]
            
            # Extract timestamps from first call
            if timestamps is None:
                timestamps = [row[0] for row in cf]
            
            # Extract values only
            values = [row[1] for row in cf]
            
            # Column naming
            column_name = f"{ft}_{scope}_{'global' if g else 'local'}"
            columns[column_name] = values

# Create DataFrame
df = pd.DataFrame(columns)
df.insert(0, 'timestamp', timestamps)

# Save to CSV
df.to_csv('wattnet_footprints.csv', index=False)

print(f"Saved {len(df)} rows × {len(df.columns)} columns")
print(df.head())