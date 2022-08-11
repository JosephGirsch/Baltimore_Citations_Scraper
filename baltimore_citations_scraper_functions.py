

def baltimore_city_scraper(citations_or_violations = "violations"):
    print("You have started the %s scrapping tool."%citations_or_violations)
    scrapperColumnsDict = {"violations":["Address", "Type", "Date_Notice", "Notice_Number", "District", "Neighborhood"],
                           "citations":["Photo","Citation Number", "Description", "Address", "Issue Date", "District", "Neighborhood"]}
    
    # generate scrapper_output data frame. Takes about 60 minutes.
    scrapper_start_time = time.time()
    scrapper_output = pd.DataFrame()
    scrapper_output_index = 0
    main_page = "http://cels.baltimorehousing.org/Search_On_Map.aspx"


    # initialize chrome options, do not load images since we don't need them.
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    # Initiate the driver for chrome.
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    # driver = webdriver.Chrome(executable_path="C:\Program Files (x86)\chromedriver.exe", options=chrome_options)

    # make a get request from the page.
    driver.get(main_page)
    time.sleep(1)

    # get city names from dropdown menu.
    cities = []
    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    city_node = page_soup.find_all("select", {"id": "ctl00_ContentPlaceHolder1_lstLoc"})[0]
    opts = city_node.find_all("option")
    for opt in opts:
        if opt.text.strip() != "":
            cities.append(opt.text.strip())

    city_index = 0
    for city in cities:
        try:
            start_time_city = time.time()
            city_index = city_index+1

            # make a get request from the page.
            driver.get(main_page)
            time.sleep(1)

            # select "by neighbourhood".
            driver.find_element_by_id("ctl00_ContentPlaceHolder1_ck2").click()

            # select "Violation" or "Citation"
            if citations_or_violations.lower() == "violations":
                driver.find_element_by_id("ctl00_ContentPlaceHolder1_rbVC_0").click()
            elif citations_or_violations.lower() == "citations":
                driver.find_element_by_id("ctl00_ContentPlaceHolder1_rbVC_1").click()
            else:
                print("ERROR. YOU NEED  TO SELECT \"violations\" or \"citations\"")
                return

            # select city.
            driver.find_element_by_id("ctl00_ContentPlaceHolder1_lstLoc").send_keys(city)

            # click search.
            driver.find_element_by_id("ctl00_ContentPlaceHolder1_btSearch").click()
            time.sleep(1)

            # Pass the HTML contents to Beautiful Soup for parsing.
            page_soup = BeautifulSoup(driver.page_source, "html.parser")

            scrapper = page_soup.find_all("tbody")[0].find_all("tr")
            for address in scrapper[2:]:
                columns = address.find_all("td")
                for i, col in enumerate(scrapperColumnsDict[citations_or_violations]):
                    scrapper_output.at[scrapper_output_index, col] = columns[i].text.strip()
                scrapper_output_index = scrapper_output_index+1

            # Print the number of neighborhoods completed and processing time for each one. 
            print(f'{city_index}/{len(cities)}', "--- ", f'{len(scrapper_output)}', "cumulative addresses. -----%s seconds ---" % round((time.time() - start_time_city),2))

        except:
            print(f'error in {city}')

    # generate scrapper_output excel file.
    #scrapper_output.to_excel("BaltimoreCity_%s_raw.xlsx"%citations_or_violations, index=False)

    # quit from the web driver
    driver.quit()
    
    # print the total processing time.
    ProcessingTime = round((time.time() - scrapper_start_time)/60,2)
    print("Code %s Processing Time %s minutes" % (citations_or_violations, ProcessingTime))
    
    # Return the Dataframe
    return scrapper_output



def validAddressRows(df_VAR, addr_field):
    # Read in Excel/CSV Data as a dataframe

    """This function will process the 'Address' column in the given DataFrame
    1. drop any leading zeros
    2. After dropping the lead zero, drop all rows whose address does not start with a number.


    (DataFrame) -> (DataFrame)
    """
    
    # 0. Drop all nans
    df_VAR = df_VAR[~df_VAR[addr_field].isnull()]
    
    # 1. drop any leading zeros (also strip any resulting whitespace)
    df_VAR.loc[:,addr_field] = df_VAR[addr_field].str.lstrip('0').str.strip()
    
    # 2. drop all rows whose address does not start with a number.
    df_VAR = df_VAR[df_VAR[addr_field].str[0].str.isdigit()]
    
    # 3. drop all rows whose address contains "(Descriptive Address)"
    df_VAR = df_VAR[~df_VAR[addr_field].str.upper().str.contains(("DESCRIPTIVE ADDRESS"))]
    
    # 4. Consolidate duplicate spaces
    df_VAR[addr_field] = df_VAR[addr_field].replace('\s+', ' ', regex=True)
    
    # Return the dataframe
    return df_VAR


def recentDaysFilter(df_rmf, days_rmf, date_field_input, date_field_output, addr_field_output):
    """
    Input: A dataframe with an 'Address' column, and a 'Date Notice' column or an 'Issue date' column
    Output: The same dataframe with only the most recent 6 months worth of data, sorted by the (new) Date and Address columns. 
    """
    # Filter the merged dictionary to the most recent (days_rmf) number of days
    df_rmf[date_field_output]= pd.to_datetime(df_rmf[date_field_input])
    df_rmf = df_rmf.sort_values(by=[date_field_output, addr_field_output])
    priorDate = df_rmf[date_field_output].max() - timedelta(days=days_rmf)
    df_rmf = df_rmf.loc[(df_rmf[date_field_output]>priorDate),:] #(code confirmed correct with excel results)
    return df_rmf


def countDiffDayDuplicates(df_ddd, date_field, addr_field):
    """
    Input: A dataframe with a 'Date' and 'Address' column
    Output: Same dataframe that only keeps duplicate addresses (duplicates on the same day don't count as duplicates)
    """
    df_ddd.drop_duplicates(subset=[date_field, addr_field], keep='last', inplace=True) # duplicates on the same day don't count
    sd = df_ddd.groupby([addr_field]).agg({addr_field:'count'}).transpose().to_dict(orient='records')[0]
    df_ddd['duplicates'] = df_ddd[addr_field].map(sd) 
    df_ddd = df_ddd[df_ddd.duplicates>=2]
    return df_ddd



def processCitations_only(cnty_name, cits_df, cits_date_col):
    """
    input: a citations df. Also label the date column. Assumes "Address" columns in dfs. 
    output: a processed citations df. 
    
    Note: This function was only created in the event of scraping only the citations because the violations 
    part of the https://cels.baltimorehousing.org/Search_On_Map.aspx website are down. 
    If both citations and violations are available, use processCitationsViolations() instead. 
    """
    
    # Process Citations
    cits_df = validAddressRows(cits_df, addr_field='Address')
    cits_df = recentDaysFilter(cits_df, days_rmf=180, date_field_input=cits_date_col, date_field_output='Date',addr_field_output='Address')
    cits_df = countDiffDayDuplicates(cits_df, date_field='Date',addr_field='Address')
    #cits_df.to_excel(cnty_name+"_citations_processed.xlsx", index=False)
    cits_df['Source'] = 'Citation'
    cits_df = cits_df[['Address', 'Date','Source']]
    
    mergedDf = cits_df
    mergedDf['tempAddress'] = mergedDf['Address'].str[0:12]
    mergedDf.drop_duplicates(subset=['tempAddress'], keep='last', inplace=True) # DROP IF FIRST 12 CHARACTERS MATCH
    mergedDf= mergedDf.drop(columns=['tempAddress'])
    mergedDf.reset_index(drop=True, inplace=True)
    return mergedDf
