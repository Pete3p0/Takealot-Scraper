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
import requests
from io import BytesIO

# --------- API Function ---------
def fetch_takealot_data(plid):
    url = f"https://api.takealot.com/rest/v-1-14-0/product-details/PLID{plid}?platform=desktop&display_credit=true"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            return {"PLID": plid, "Error": "It looks like this product is no longer available"}
        elif response.status_code != 200 or not response.text.strip():
            return {"PLID": plid, "Error": f"Empty or bad response. Code: {response.status_code}"}

        data = response.json()

        # Buybox prices
        price = data.get("buybox", {}).get("items", [{}])[0].get("price")
        listing_price = data.get("buybox", {}).get("items", [{}])[0].get("listing_price", "")

        # Stock availability
        stock_status = data.get("buybox", {}).get("items", [{}])[0].get("stock_availability", {}).get("status")

        # Seller (primary)
        seller_info = data.get("seller_detail", {}).get("display_name", "Fulfilled by Takealot")

        # Ratings
        star_rating = data.get("reviews", {}).get("star_rating")
        review_count = data.get("reviews", {}).get("count")

        dist = data.get("reviews", {}).get("distribution", {})
        num_1 = dist.get("num_1_star_ratings", 0)
        num_2 = dist.get("num_2_star_ratings", 0)
        num_3 = dist.get("num_3_star_ratings", 0)
        num_4 = dist.get("num_4_star_ratings", 0)
        num_5 = dist.get("num_5_star_ratings", 0)

        # Other offers – first one only
        other_offers = data.get("other_offers", [])
        if other_offers:
            alt_seller = other_offers[0].get("seller", {}).get("display_name", "")
            alt_price = other_offers[0].get("purchase_price", "")
        else:
            alt_seller = ""
            alt_price = ""

        return {
            "PLID": plid,
            "RSP": price,
            "Original Price": listing_price,
            "Seller": seller_info,
            "Stock Availability": stock_status,
            "Rating": star_rating,
            "Review Count": review_count,
            "1★": num_1,
            "2★": num_2,
            "3★": num_3,
            "4★": num_4,
            "5★": num_5,
            "Other Seller": alt_seller,
            "Other Price": alt_price
        }

    except Exception as e:
        return {
            "PLID": plid,
            "Error": str(e),
        }

# --------- Streamlit App ---------
st.title("🛒 Takealot Product Info API Extractor")

uploaded_file = st.file_uploader("📤 Upload Excel file with URLs in the 3rd column", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if df.shape[1] < 3:
        st.error("❗ Please make sure the file has at least 3 columns, with the URL in the third column.")
    else:
        st.write("📄 Preview of uploaded file:")
        st.dataframe(df.head())

        if st.button("🚀 Start Fetching Product Info"):
            url_col = df.columns[2]
            results = []

            with st.spinner("🔍 Fetching data from Takealot API..."):
                for i, row in df.iterrows():
                    url = str(row[url_col])
                    if "PLID" not in url:
                        continue
                    plid = url.split("PLID")[-1].split("?")[0]
                    result = fetch_takealot_data(plid)

                    # Append original columns
                    result["Product Code"] = row[0]
                    result["Description"] = row[1]
                    result["Link"] = url

                    results.append(result)
                    time.sleep(1.5)  # ⏳ Respectful delay

            # Convert results to DataFrame and reorder columns
            results_df = pd.DataFrame(results)
            front_cols = ["Product Code", "Description", "Link"]
            reordered = front_cols + [col for col in results_df.columns if col not in front_cols]
            results_df = results_df[reordered]

            st.success("✅ Done!")
            st.dataframe(results_df)

            # Excel download
            towrite = BytesIO()
            results_df.to_excel(towrite, index=False, engine="openpyxl")
            towrite.seek(0)
            st.download_button("📥 Download Excel", towrite, "takealot_api_results.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
