# import the required packages and functions from baltimore_citations_scraper_functions.py
import pandas as pd
import time 

# Set the start_time constant
start_time = time.time()

from baltimore_citations_scraper_functions import *

# Run the scraper to obtain the Baltimore City Citations. Will take several hours.
baltimore_city_scrapper_output_citations = baltimore_city_scraper(citations_or_violations ="citations")
baltimore_city_scrapper_output_citations.to_excel("BaltimoreCity_Citations_Raw_Temp/" +"BaltimoreCity_%s_raw.xlsx"%"citations", index=False)

# Load 'BaltimoreCity_citations_raw.xlsx' (8/13/2022 update: No need to load excel file, just reuse baltimore_city_scrapper_output_citations)
citations_df_raw = baltimore_city_scrapper_output_citations

# Process the raw citations data (valid address check, ciation within last 180 days, properties with 2 or more citations filter, column prep for propstream import )
county_name = "Baltimore_City"
baltimore_city_citations_df_processed = processCitations_only(county_name, citations_df_raw, "Issue Date")

# Save the processed baltimore city citations in the 'BaltimoreCity_Citations_Processed' folder. 
baltimore_city_citations_df_processed.to_excel( "BaltimoreCity_Citations_Processed/" +"BaltimoreCity_%s_processed.xlsx"%"citations", index=False)
