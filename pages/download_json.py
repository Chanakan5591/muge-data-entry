import streamlit as st
import json

st.set_page_config(page_title="ดาวน์โหลดข้อมูล JSON", page_icon="⬇️")

st.sidebar.header("MUGE100 C10-297 Data Entry")
st.sidebar.markdown("Implementation by Chanakan Moongthin")
st.sidebar.page_link("canteen.py", label="ข้อมูลโรงอาหาร", icon="🍽️")
st.sidebar.page_link("pages/stores.py", label="ข้อมูลร้านค้า", icon="🏪")
st.sidebar.page_link("pages/food_items.py", label="ข้อมูลรายการอาหาร", icon="🍲")
st.sidebar.page_link("pages/download_json.py", label="ดาวน์โหลดข้อมูล JSON", icon="⬇️")


st.title("⬇️ ดาวน์โหลดข้อมูล JSON")

# Function to load canteen data from JSON file
def load_canteen_data(filepath="canteen_data.json"):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Function to convert data to JSON string for download
def convert_data_to_json(data):
    return json.dumps(data, indent=4, ensure_ascii=False)

# Load existing canteen data
canteen_data = load_canteen_data()

# Display JSON content
st.header("เนื้อหาไฟล์ JSON")
st.json(canteen_data)

# Download button
canteen_data_json = convert_data_to_json(canteen_data)
st.download_button(
    label="ดาวน์โหลดไฟล์ JSON",
    data=canteen_data_json,
    file_name="canteen_data.json",
    mime="application/json"
)