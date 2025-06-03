import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import time
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920x1080')
    chrome_options.binary_location = "/usr/bin/chromium"

    service = Service()  # Let Selenium find chromedriver in PATH
    return webdriver.Chrome(service=service, options=chrome_options)

def get_takealot_prices(url, driver):
    try:
        driver.get(url)
        time.sleep(6)  # Give more time for JS rendering

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # DEBUG: show full page title
        page_title = soup.title.string if soup.title else "No title"
        st.write(f"🔍 Page loaded: {page_title}")

        # DEBUG: show first 1000 chars of raw HTML
        st.text(soup.prettify()[:1000])

        # Try direct price class first
        price_element = soup.find('span', class_='currency plus currency-module_currency_29IIm')
        rsp = price_element.text.strip().replace("R", "").replace(",", "") if price_element else None

        # Try fallback selector if first fails
        if not rsp:
            alt_price = soup.select_one("span.currency")
            rsp = alt_price.text.strip().replace("R", "").replace(",", "") if alt_price else None

        # Find old price
        old_price_element = soup.find('span', class_='strike-through')
        old_price = old_price_element.text.strip().replace("R", "").replace(",", "") if old_price_element else None

        # Show extracted result
        st.write(f"💰 RSP: {rsp}, Old Price: {old_price}")

        return float(rsp) if rsp else None, float(old_price) if old_price else None

    except Exception as e:
        st.error(f"❌ Error during scraping: {e}")
        return None, None


# Streamlit UI
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
                    time.sleep(1.5)

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
