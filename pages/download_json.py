import streamlit as st
import hmac
import json
from pymongo import MongoClient
from pymongo.server_api import ServerApi
st.set_page_config(page_title="ดาวน์โหลดข้อมูล JSON", page_icon="⬇️")


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            st.session_state["password"] = None  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.


@st.cache_resource()
def database_init():
    """Initialize the MongoDB connection."""
    return MongoClient(st.secrets['mongo_uri'], server_api=ServerApi('1'))


mongo = database_init()

if not mongo:
    st.error("Cannot Access Data Storage")
    st.stop()

# MongoDB collection reference
canteen_collection = mongo.muge_canteen.canteen_data


def load_canteen_data():
    """Fetch canteen data from MongoDB."""
    data = canteen_collection.find()
    return list(data)


st.sidebar.header("MUGE100 C10-297 Data Entry")
st.sidebar.markdown("Implementation by Chanakan Moongthin")
st.sidebar.page_link("canteen.py", label="ข้อมูลโรงอาหาร", icon="🍽️")
st.sidebar.page_link("pages/stores.py", label="ข้อมูลร้านค้า", icon="🏪")
st.sidebar.page_link("pages/food_items.py", label="ข้อมูลรายการอาหาร", icon="🍲")
st.sidebar.page_link("pages/download_json.py", label="ดาวน์โหลดข้อมูล JSON", icon="⬇️")

# Main Content
st.title("⬇️ ดาวน์โหลดข้อมูล JSON")

# Load data from the database
canteen_data = load_canteen_data()

if not canteen_data:
    st.warning("ไม่มีข้อมูลโรงอาหารในระบบ")
else:
    # Convert data to JSON format
    for entry in canteen_data:
        # Remove MongoDB-specific '_id' field for JSON compatibility
        if "_id" in entry:
            entry.pop("_id")

    json_data = json.dumps(canteen_data, ensure_ascii=False, indent=4)

    # Display JSON data in a text area
    st.subheader("Preview Data")
    st.code(json_data, language="json")

    # Provide download option
    st.download_button(
        label="📥 ดาวน์โหลด JSON",
        data=json_data,
        file_name="canteen_data.json",
        mime="application/json",
    )
