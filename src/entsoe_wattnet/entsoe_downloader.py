from entsoe import EntsoePandasClient
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path

# ENTSOE API client setup
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
client = EntsoePandasClient(api_key=os.getenv("ENTSOE_API_TOKEN"))

start = pd.Timestamp('20241214', tz='Europe/Brussels') # 14 December 2024
end = pd.Timestamp('20250413', tz='Europe/Brussels') # 13 April 2025

country_code = 'ES'

# Water reservoirs and hydro storage (Series):
#client.query_aggregate_water_reservoirs_and_hydro_storage(country_code, start=start, end=end)

# Generation methods (DataFrame):
generation = client.query_generation(country_code, start=start, end=end, psr_type=None)
#generation_per_plant = client.query_generation_per_plant(country_code, start=start, end=end, psr_type=None, include_eic=False)

# Flows methods (DataFrame):
crossborder_flows_export = client.query_physical_crossborder_allborders(country_code, start, end, export=True)
crossborder_flows_import = client.query_physical_crossborder_allborders(country_code, start, end, export=False)

# Saving data to CSV files
generation.to_csv('generation.csv')
#generation_per_plant.to_csv('generation_per_plant.csv')
crossborder_flows_export.to_csv('crossborder_flows_export.csv')
crossborder_flows_import.to_csv('crossborder_flows_import.csv')

