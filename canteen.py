import streamlit as st
import pymongo
import datetime
import hmac
from bson.objectid import ObjectId

from pymongo.server_api import ServerApi

st.set_page_config(page_title="ข้อมูลโรงอาหาร", page_icon="🍽️")

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
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

st.sidebar.header("MUGE100 C10-297 Data Entry")
st.sidebar.markdown("Implementation by Chanakan Moongthin")
st.sidebar.page_link("canteen.py", label="ข้อมูลโรงอาหาร", icon="🍽️")
st.sidebar.page_link("pages/stores.py", label="ข้อมูลร้านค้า", icon="🏪")
st.sidebar.page_link("pages/food_items.py", label="ข้อมูลรายการอาหาร", icon="🍲")

@st.cache_resource()
def database_init():
    return pymongo.MongoClient(st.secrets['mongo_uri'], server_api=ServerApi('1'))

mongo = database_init()

if not mongo:
    st.error('Cannot Access Data Storage')
    st.stop()

st.title("🍽️ ข้อมูลโรงอาหาร")

# --- Database Operations ---
canteen_collection = mongo.canteen_info.canteens  # Changed to match the schema

# Function to load canteen data from MongoDB
def load_canteens() -> list:
    data = canteen_collection.find()
    return list(data)

# Function to add a new canteen to MongoDB
def add_canteen(canteen_data):
    canteen_collection.insert_one(canteen_data)

# Function to update an existing canteen in MongoDB
def update_canteen(canteen_id, canteen_data):
    canteen_collection.update_one(
        {"_id": ObjectId(canteen_id)},
        {"$set": canteen_data}
    )

# Function to delete a canteen from MongoDB
def delete_canteen(canteen_id):
    canteen_collection.delete_one({"_id": ObjectId(canteen_id)})

# --- Session State Initialization ---
if "canteen_name" not in st.session_state:
    st.session_state.canteen_name = ""
if "busy_periods" not in st.session_state:
    st.session_state.busy_periods = []
if "with_airconditioning" not in st.session_state:
    st.session_state.with_airconditioning = False
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

# --- Input Form ---
st.header("เพิ่ม/แก้ไข ข้อมูลโรงอาหาร")

# --- Input Fields ---
# Canteen name
st.session_state.canteen_name = st.text_input("กรอกชื่อโรงอาหาร", value=st.session_state.canteen_name)

# Busy periods (multiple)
st.write("**ช่วงเวลาที่มีลูกค้าเยอะ** (ระบุแค่ช่วงเวลา)")
busy_periods_col1, busy_periods_col2 = st.columns(2)
new_start_time = busy_periods_col1.time_input("เวลาเริ่มต้น", value=datetime.time(11, 0), key="new_start")
new_end_time = busy_periods_col2.time_input("เวลาสิ้นสุด", value=datetime.time(13, 0), key="new_end")
if new_end_time < new_start_time:
    st.error("เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น")

if st.button("เพิ่มช่วงเวลา", key="add_busy_period"):
    if new_end_time > new_start_time:
        st.session_state.busy_periods.append({
            "start": new_start_time.strftime("%H:%M"),
            "end": new_end_time.strftime("%H:%M")
        })

# Display added busy periods
for i, period in enumerate(st.session_state.busy_periods):
    st.write(f"- {period['start']} ถึง {period['end']}")
    if st.button("ลบ", key=f"delete_period_{i}"):
        st.session_state.busy_periods.pop(i)
        st.rerun()

# With air conditioning
st.session_state.with_airconditioning = st.checkbox(
    "มีเครื่องปรับอากาศ", value=st.session_state.with_airconditioning
)

# --- Add or Edit Entry Button ---
if st.session_state.editing_id is None:
    button_label = "เพิ่มข้อมูล"
    if st.button(button_label):
        canteens = load_canteens()
        canteen_names = [entry["name"].lower() for entry in canteens]
        if st.session_state.canteen_name.lower() in canteen_names:
            st.error("มีชื่อโรงอาหารนี้อยู่แล้ว กรุณาใช้ชื่ออื่น")
        elif not st.session_state.canteen_name:
            st.error("กรุณากรอกชื่อโรงอาหาร")
        else:
            # Create a dictionary for the new entry, using the schema
            entry = {
                "name": st.session_state.canteen_name,
                "busyPeriods": st.session_state.busy_periods,
                "withAirConditioning": st.session_state.with_airconditioning,
                "stores": [],  # Initialize with empty stores array, as per schema
            }

            add_canteen(entry)
            st.success("เพิ่มข้อมูลโรงอาหารเรียบร้อยแล้ว!")
            # Reset input values
            st.session_state.canteen_name = ""
            st.session_state.busy_periods = []
            st.session_state.with_airconditioning = False
            st.rerun()
else:
    button_label = "บันทึกการแก้ไข"
    if st.button(button_label):
        canteens = load_canteens()
        if not st.session_state.canteen_name:
            st.error("กรุณากรอกชื่อโรงอาหาร")
        else:
            canteen_names = [entry["name"].lower() for entry in canteens if entry["_id"] != ObjectId(st.session_state.editing_id)]
            if st.session_state.canteen_name.lower() in canteen_names:
                st.error("มีชื่อโรงอาหารนี้อยู่แล้ว กรุณาใช้ชื่ออื่น")
            else:
                entry = {
                    "name": st.session_state.canteen_name,
                    "busyPeriods": st.session_state.busy_periods,
                    "withAirConditioning": st.session_state.with_airconditioning
                    # Stores are not updated here, as per the schema
                }

                update_canteen(st.session_state.editing_id, entry)
                st.success("แก้ไขข้อมูลโรงอาหารเรียบร้อยแล้ว!")

                # Reset input values and editing state
                st.session_state.canteen_name = ""
                st.session_state.busy_periods = []
                st.session_state.with_airconditioning = False
                st.session_state.editing_id = None
                st.rerun()

# --- Display, Edit, and Delete ---
st.header("ข้อมูลโรงอาหารปัจจุบัน")

canteens = load_canteens()

for entry in canteens:
    col1, col2, col3 = st.columns([3, 1, 1])
    # Convert ObjectId to string for display
    entry_id_str = str(entry['_id'])

    with col1:
        st.write(f"**ชื่อโรงอาหาร:** {entry['name']}")
        st.write("**ช่วงเวลาที่มีลูกค้าเยอะ:**")
        for period in entry['busyPeriods']:
            st.write(f"- {period['start']} ถึง {period['end']}")
        st.write(
            "**มีเครื่องปรับอากาศ:** "
            + ("ใช่" if entry["withAirConditioning"] else "ไม่ใช่")
        )
        st.write(f"**จำนวนร้านค้า:** {len(entry.get('stores', []))}")

    with col2:
        if st.button("แก้ไข", key=f"edit_{entry_id_str}"):
            st.session_state.editing_id = entry_id_str
            st.session_state.canteen_name = entry["name"]
            st.session_state.busy_periods = entry["busyPeriods"]
            st.session_state.with_airconditioning = entry["withAirConditioning"]
            st.rerun()

    with col3:
        if st.button("ลบ", key=f"delete_{entry_id_str}"):
            delete_canteen(entry_id_str)
            st.session_state.editing_id = None
            st.rerun()