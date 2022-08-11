# import the functions and required modules from baltimore_citations_scraper_functions.py
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import numpy as np
import time
from datetime import timedelta, datetime
import datetime as dt

# Set the start_time constant
pd.set_option("display.max_columns", None)
start_time = time.time()

from baltimore_citations_scraper_functions import *

baltimore_city_scrapper_output_citations = baltimore_city_scraper(citations_or_violations ="citations")
baltimore_city_scrapper_output_citations.to_excel("BaltimoreCity_Citations_Raw_Temp/" +"_BaltimoreCity_%s_raw.xlsx"%"citations", index=False)
