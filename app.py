import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO
import os
from dotenv import load_dotenv
load_dotenv()
# ---------------------------
# Google Custom Search API Key และ Search Engine ID
# ---------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# ---------------------------
# Sidebar: Input
# ---------------------------
st.sidebar.title("🔍 Search Settings")

input_line = st.sidebar.text_input(
    "📌 Enter your search keywords",
    placeholder="e.g., ร้านค้า, ค้าขาย, การออกกำลังกาย"
)

site_option = st.sidebar.selectbox(
    "🌐 Restrict search to specific site:",
    ["All sites", "facebook.com", "instagram.com", "x.com"]
)

site_prefix = ""
if site_option != "All sites":
    site_prefix = f"site:{site_option}"

st.title("📄 Scraping Tool (with Google Custom Search API)")

st.markdown("""
ค้นหาข้อมูลบน Google ผ่าน Google Custom Search API แบบเฉพาะเจาะจง เช่น Facebook หรือ Instagram  
ใส่คำค้นหลายคำ โดยใช้เครื่องหมายคอมม่า (`,`) คั่นระหว่างคำ  
""")

# Initialize session state
if "results" not in st.session_state:
    st.session_state.results = []

if input_line and (not st.session_state.results or st.session_state.get("last_query", "") != input_line + site_option):
    keywords = [k.strip() for k in input_line.split(",") if k.strip()]
    query = f"{site_prefix} {' '.join(keywords)}".strip()

    st.markdown(f"### 🔎 Results for query: `{query}`")

    # Call Google Custom Search API
    try:
        with st.spinner("🔄 Searching Google via Custom Search API..."):
            params = {
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CSE_ID,
                "q": query,
                "num": 10,
                "hl": "th"
            }
            resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
            data = resp.json()
            urls = [item["link"] for item in data.get("items", [])]
    except Exception as e:
        st.error(f"❌ Error during search: {e}")
        urls = []

    results = []
    for i, url in enumerate(urls, start=1):
        try:
            response = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.title.string.strip() if soup.title else "No title found"

            meta_desc = soup.find("meta", attrs={"name": "description"}) or \
                        soup.find("meta", attrs={"property": "og:description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()
            else:
                first_p = soup.find("p")
                description = first_p.text.strip()[:300] if first_p else "No content found"

        except Exception as e:
            title = f"Error fetching title: {e}"
            description = f"Error fetching content: {e}"

        with st.expander(f"{i}. {title}"):
            st.write(f"🔗 {url}")
            st.write(f"✏️ {description}")

        results.append({
            "No.": i,
            "Title": title,
            "URL": url,
            "Content": description
        })

    st.session_state.results = results
    st.session_state.last_query = input_line + site_option

# ---------------------------
# Display & Export
# ---------------------------
if st.session_state.results:
    for r in st.session_state.results:
        with st.expander(f"{r['No.']}. {r['Title']}"):
            st.write(f"🔗 [Visit Site]({r['URL']})")
            st.write(f"✏️ {r['Content']}")

    df = pd.DataFrame(st.session_state.results)

    file_format = st.selectbox("เลือกสกุลไฟล์สำหรับดาวน์โหลด", ["CSV", "Excel"])
    data = None
    file_name = ""
    mime = ""

    if file_format == "CSV":
        data = df.to_csv(index=False).encode("utf-8")
        file_name = "search_results.csv"
        mime = "text/csv"
    elif file_format == "Excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Results")
        data = output.getvalue()
        file_name = "search_results.xlsx"
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    if data:
        st.download_button(
            label=f"📥 ดาวน์โหลด {file_name}",
            data=data,
            file_name=file_name,
            mime=mime
        )
