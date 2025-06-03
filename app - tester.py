import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import time
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

# Ensure ChromeDriver is installed
chromedriver_autoinstaller.install()

# Function to extract prices using a persistent Selenium driver
# def get_takealot_prices(url, driver):
#     try:
#         driver.get(url)
#         time.sleep(5)  # Give the page time to render

#         soup = BeautifulSoup(driver.page_source, 'html.parser')

#         # Adjust these classes based on current site HTML
#         price_element = soup.find('span', {'class': 'currency plus currency-module_currency_29IIm'})
#         old_price_element = soup.find('span', {'class': 'strike-through'})

#         rsp = price_element.text.strip().replace("R", "").replace(",", "") if price_element else None
#         old_price = old_price_element.text.strip().replace("R", "").replace(",", "") if old_price_element else None

#         return float(rsp) if rsp else None, float(old_price) if old_price else None
#     except Exception:
#         return None, None

def get_takealot_prices(url, driver):
    try:
        driver.get(url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find the right-hand panel container
        price_box = soup.find('div', class_='buybox-offer-module_buybox-offer_1JNpe buybox-offer-module_active_3I1Yj')

        # Now safely extract price and old price from within that
        if price_box:
            price_element = price_box.find('span', class_='currency plus currency-module_currency_29IIm')
            old_price_element = price_box.find('span', class_='strike-through')
        else:
            price_element = None
            old_price_element = None

        rsp = price_element.text.strip().replace("R", "").replace(",", "") if price_element else None
        old_price = old_price_element.text.strip().replace("R", "").replace(",", "") if old_price_element else None

        return float(rsp) if rsp else None, float(old_price) if old_price else None

    except Exception as e:
        st.error(f"Error extracting prices: {e}")
        return None, None


# Streamlit UI
st.title("🔍 Takealot RSP Scraper (Fast Selenium Version)")

uploaded_file = st.file_uploader("📤 Upload Excel file with product URLs in column 3", type=["xlsx"])

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

            # Setup Selenium driver once
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--log-level=3')
            options.add_argument("user-agent=Mozilla/5.0")
            driver = webdriver.Chrome(options=options)

            with st.spinner("🔄 Scraping prices... Please be patient."):
                for index, row in df.iterrows():
                    url = str(row[url_col])
                    rsp, old_price = get_takealot_prices(url, driver)
                    rsp_list.append(rsp)
                    old_price_list.append(old_price)
                    time.sleep(1.5)  # Anti-bot pacing

            driver.quit()

            df['RSP'] = rsp_list
            df['Previous Price (if any)'] = old_price_list

            st.success("✅ Scraping complete!")
            st.dataframe(df)

            # Prepare for download
            towrite = BytesIO()
            df.to_excel(towrite, index=False, engine='openpyxl')
            towrite.seek(0)
            st.download_button("📥 Download Updated Excel", towrite, "takealot_prices.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
