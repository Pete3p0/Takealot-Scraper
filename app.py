# import streamlit as st
# import pandas as pd
# from bs4 import BeautifulSoup
# import time
# from io import BytesIO
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import NoSuchElementException

# def create_driver():
#     chrome_options = Options()
#     chrome_options.add_argument('--headless')
#     chrome_options.add_argument('--disable-dev-shm-usage')
#     chrome_options.add_argument('--no-sandbox')
#     chrome_options.add_argument('--disable-gpu')
#     chrome_options.add_argument('--window-size=1920x1080')
#     chrome_options.binary_location = "/usr/bin/chromium"

#     service = Service()  # Let Selenium find chromedriver in PATH
#     return webdriver.Chrome(service=service, options=chrome_options)

# def get_takealot_prices(url, driver):
#     try:
#         driver.get(url)
#         time.sleep(5)

#         # ✅ Use absolute XPath to extract the main price only
#         try:
#             rsp_elem = driver.find_element(By.XPATH, "/html/body/div[1]/div[5]/div[1]/div[2]/aside/div[1]/div[1]/div[1]/div[1]/div/span[1]")
#             rsp = rsp_elem.text.strip().replace("R", "").replace(",", "")
#         except NoSuchElementException:
#             rsp = None

#         # ✅ Old price is in the second span, next to the RSP
#         try:
#             old_price_elem = driver.find_element(By.XPATH, "/html/body/div[1]/div[5]/div[1]/div[2]/aside/div[1]/div[1]/div[1]/div[1]/div/span[2]")
#             old_price = old_price_elem.text.strip().replace("R", "").replace(",", "")
#         except NoSuchElementException:
#             old_price = None

#         return float(rsp) if rsp else None, float(old_price) if old_price else None

#     except Exception as e:
#         st.error(f"❌ Error extracting prices: {e}")
#         return None, None

# # Streamlit UI
# st.title("🛒 Kayla's Takealot RSP Scraper")

# uploaded_file = st.file_uploader("📤 Upload Excel file with Takealot product URLs in column 3", type=["xlsx"])

# if uploaded_file:
#     df = pd.read_excel(uploaded_file)

#     if df.shape[1] < 3:
#         st.error("❗ Please ensure the file has at least 3 columns and the URLs are in the third column.")
#     else:
#         st.write("📄 Preview of uploaded file:")
#         st.dataframe(df.head())

#         if st.button("🚀 Start Scraping"):
#             rsp_list = []
#             old_price_list = []
#             url_col = df.columns[2]

#             driver = create_driver()

#             with st.spinner("🔄 Scraping prices... Please wait."):
#                 for index, row in df.iterrows():
#                     url = str(row[url_col])
#                     rsp, old_price = get_takealot_prices(url, driver)
#                     rsp_list.append(rsp)
#                     old_price_list.append(old_price)
#                     time.sleep(1.5)

#             driver.quit()

#             df['RSP'] = rsp_list
#             df['Previous Price (if any)'] = old_price_list

#             st.success("✅ Scraping complete!")
#             st.dataframe(df)

#             # Allow download
#             towrite = BytesIO()
#             df.to_excel(towrite, index=False, engine='openpyxl')
#             towrite.seek(0)
#             st.download_button("📥 Download Updated Excel", towrite, "takealot_prices.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


import streamlit as st
import pandas as pd
import time
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# ---------- Create Chrome driver for Streamlit Cloud ----------
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920x1080')
    chrome_options.binary_location = "/usr/bin/chromium"  # for Streamlit Cloud

    service = Service()  # let Selenium find chromedriver
    return webdriver.Chrome(service=service, options=chrome_options)

# ---------- Scraper logic (Selenium only, no BS4) ----------
def get_takealot_prices(url, driver):
    try:
        driver.get(url)
        time.sleep(5)  # Allow time for JS rendering

        rsp = None
        old_price = None

        # ✅ Look inside the main buybox summary section
        try:
            rsp_elem = driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'buybox-module_buybox-summary')]//span[contains(@class, 'currency-module_currency')]"
            )
            rsp = rsp_elem.text.strip().replace("R", "").replace(",", "")
        except NoSuchElementException:
            pass

        try:
            old_price_elem = driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'buybox-module_buybox-summary')]//span[contains(@class, 'strike-through')]"
            )
            old_price = old_price_elem.text.strip().replace("R", "").replace(",", "")
        except NoSuchElementException:
            pass

        return float(rsp) if rsp else None, float(old_price) if old_price else None

    except Exception as e:
        st.error(f"❌ Error extracting prices: {e}")
        return None, None

# ---------- Streamlit App ----------
st.title("🛒 Kayla's Takealot RSP Scraper")

uploaded_file = st.file_uploader("📤 Upload Excel file with Takealot product URLs in column 3", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if df.shape[1] < 3:
        st.error("❗ Please ensure the file has at least 3 columns and the URLs are in the third column.")
    else:
        st.write("📄 Preview of uploaded file:")
        st.dataframe(df.head())

        if st.button("🚀 Start Scraping"):
            rsp_list = []
            old_price_list = []
            url_col = df.columns[2]

            driver = create_driver()

            with st.spinner("🔄 Scraping prices... Please wait."):
                for index, row in df.iterrows():
                    url = str(row[url_col])
                    rsp, old_price = get_takealot_prices(url, driver)
                    rsp_list.append(rsp)
                    old_price_list.append(old_price)
                    time.sleep(1.5)  # gentle delay to avoid bot detection

            driver.quit()

            df['RSP'] = rsp_list
            df['Previous Price (if any)'] = old_price_list

            st.success("✅ Scraping complete!")
            st.dataframe(df)

            # Allow download
            towrite = BytesIO()
            df.to_excel(towrite, index=False, engine='openpyxl')
            towrite.seek(0)
            st.download_button("📥 Download Updated Excel", towrite, "takealot_prices.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
