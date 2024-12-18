import streamlit as st
import pymongo
from pymongo.server_api import ServerApi
import datetime
import hmac
from bson.objectid import ObjectId

st.set_page_config(page_title="ข้อมูลร้านค้า", page_icon="🏪")

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
    return pymongo.MongoClient(st.secrets["mongo_uri"], server_api=ServerApi("1"))

mongo = database_init()

if not mongo:
    st.error("Cannot Access Data Storage")
    st.stop()

st.title("🏪 ข้อมูลร้านค้า")

# --- Database Operations ---
canteen_collection = mongo.canteen_info.canteens
store_collection = mongo.canteen_info.stores

# Function to load canteen data from MongoDB
def load_canteens():
    data = canteen_collection.find()
    return list(data)

def load_stores():
    data = store_collection.find()
    return list(data)

# Function to update canteen data in MongoDB
def update_canteen(canteen_id, updated_canteen):
    canteen_collection.update_one({"_id": ObjectId(canteen_id)}, {"$set": updated_canteen})

def update_store(store_id, updated_store):
    store_collection.update_one({"_id": ObjectId(store_id)}, {"$set": updated_store})

def delete_store(store_id):
    store_collection.delete_one({"_id": ObjectId(store_id)})

# --- Load and Extract Data ---
canteens = load_canteens()
stores = load_stores()
existing_canteen_names = [entry["name"] for entry in canteens]

# --- Input Form ---
st.header("เพิ่ม/แก้ไข ข้อมูลร้านค้า")

# --- Session State Initialization ---
if "editing_store_id" not in st.session_state:
    st.session_state.editing_store_id = None
if "selected_canteen_id" not in st.session_state:
    st.session_state.selected_canteen_id = None
if "store_name" not in st.session_state:
    st.session_state.store_name = ""
if "store_description" not in st.session_state:
    st.session_state.store_description = ""
if "opening_hours" not in st.session_state:
    st.session_state.opening_hours = []
if "opening_hours_mode" not in st.session_state:
    st.session_state.opening_hours_mode = "everyday"  # Default mode

def init_session_state(store=None):
    st.session_state.store_name = store["name"] if store else ""
    st.session_state.store_description = store["description"] if store else ""

    if store and store.get("openingHours"):
        # Determine opening_hours_mode based on data
        opening_hours = store.get("openingHours")
        days_count = len(opening_hours)

        if days_count == 5:
            # Check if all 5 days are present and have the same start and end times
            first_day_start = opening_hours[0]["start"]
            first_day_end = opening_hours[0]["end"]
            all_same_times = all(
                d["start"] == first_day_start and d["end"] == first_day_end
                for d in opening_hours
            )
            if all_same_times:
                st.session_state.opening_hours_mode = "everyday"
            else:
                st.session_state.opening_hours_mode = "per_day"
        else:
            st.session_state.opening_hours_mode = "per_day"  # Default to per_day if not exactly 5 days

        st.session_state.opening_hours = opening_hours
    else:
        st.session_state.opening_hours_mode = "everyday"  # Default mode
        st.session_state.opening_hours = []

# Initialize session state if not already initialized
if st.session_state.editing_store_id:
    # Find the store being edited
    for store in stores:
        if str(store["_id"]) == st.session_state.editing_store_id:
            st.session_state.selected_canteen_id = str(store["canteenId"])
            init_session_state(store)
            break
else:
    init_session_state()
# Select Canteen
canteen_options = {str(c["_id"]): c["name"] for c in canteens}
st.session_state.selected_canteen_id = st.selectbox(
    "เลือกโรงอาหาร",
    options=canteen_options.keys(),
    index=list(canteen_options.keys()).index(st.session_state.selected_canteen_id) if st.session_state.selected_canteen_id in canteen_options else 0,
    format_func=lambda x: canteen_options[x],
)

if not st.session_state.selected_canteen_id:
    st.info("กรุณาเลือกโรงอาหารก่อน")
else:
    # Store Name
    st.session_state.store_name = st.text_input(
        "ชื่อร้านค้า", value=st.session_state.store_name
    )

    # Store Description
    st.session_state.store_description = st.text_area(
        "คำอธิบายร้านค้า", value=st.session_state.store_description
    )

    # Opening Hours Mode
    st.session_state.opening_hours_mode = st.radio(
        "เลือกรูปแบบเวลาเปิดปิด",
        ["everyday", "per_day"],
        index=0 if st.session_state.opening_hours_mode == "everyday" else 1,
        format_func=lambda x: "ทุกวัน" if x == "everyday" else "เฉพาะแต่ละวัน",
    )

    # Opening Hours
    st.write("**เวลาเปิดปิด**")

    days_of_week = [
        "MONDAY",
        "TUESDAY",
        "WEDNESDAY",
        "THURSDAY",
        "FRIDAY",
    ]

    if st.session_state.opening_hours_mode == "everyday":
        # If mode is "everyday", create entries for all days
        opening_hours_col1, opening_hours_col2 = st.columns(2)

        # --- FIX for everyday mode ---
        # Get default values from the first day in opening_hours if editing
        default_start = datetime.time(8, 0)
        default_end = datetime.time(17, 0)
        if st.session_state.opening_hours and len(st.session_state.opening_hours) > 0:
            default_start = datetime.datetime.strptime(
                st.session_state.opening_hours[0]["start"], "%H:%M"
            ).time()
            default_end = datetime.datetime.strptime(
                st.session_state.opening_hours[0]["end"], "%H:%M"
            ).time()

        new_start_time = opening_hours_col1.time_input(
            "เวลาเริ่มต้น (ทุกวัน)", value=default_start, key="new_start_everyday"
        )
        new_end_time = opening_hours_col2.time_input(
            "เวลาสิ้นสุด (ทุกวัน)", value=default_end, key="new_end_everyday"
        )

        st.session_state.opening_hours = [
            {
                "dayOfWeek": day,
                "start": new_start_time.strftime("%H:%M"),
                "end": new_end_time.strftime("%H:%M"),
            }
            for day in days_of_week
        ]

    else:  # per_day mode (This part was already working correctly)
        for day in days_of_week:
            # Find existing entry for the day
            existing_entry = next(
                (
                    entry
                    for entry in st.session_state.opening_hours
                    if entry["dayOfWeek"] == day
                ),
                None,
            )

            st.write(f"**{day}**")
            opening_hours_col1, opening_hours_col2 = st.columns(2)

            # Use existing values or defaults
            default_start = (
                datetime.datetime.strptime(existing_entry["start"], "%H:%M").time()
                if existing_entry
                else datetime.time(8, 0)
            )
            default_end = (
                datetime.datetime.strptime(existing_entry["end"], "%H:%M").time()
                if existing_entry
                else datetime.time(17, 0)
            )

            # Use store_id in the key to make them unique
            store_id = st.session_state.editing_store_id
            new_start_time = opening_hours_col1.time_input(
                "เวลาเริ่มต้น", value=default_start, key=f"new_start_{day}_{store_id}"
            )
            new_end_time = opening_hours_col2.time_input(
                "เวลาสิ้นสุด", value=default_end, key=f"new_end_{day}_{store_id}"
            )

            # Update or add the entry in session state
            new_opening_hour = {
                "dayOfWeek": day,
                "start": new_start_time.strftime("%H:%M"),
                "end": new_end_time.strftime("%H:%M"),
            }

            if existing_entry:
                # Update existing entry
                existing_entry_index = st.session_state.opening_hours.index(
                    existing_entry
                )
                st.session_state.opening_hours[existing_entry_index] = new_opening_hour
            else:
                # Add new entry
                st.session_state.opening_hours.append(new_opening_hour)
    # Display opening hours
    for opening_hour in st.session_state.opening_hours:
        st.write(
            f"- {opening_hour['dayOfWeek']}: {opening_hour['start']} ถึง {opening_hour['end']}"
        )

    # --- Add or Edit Store Button ---
    if st.session_state.editing_store_id is None:
        button_label = "เพิ่มร้านค้า"
        if st.button(button_label):
            if not st.session_state.store_name:
                st.error("กรุณากรอกชื่อร้านค้า")
            elif not st.session_state.store_description:
                st.error("กรุณากรอกคำอธิบายร้านค้า")
            elif not st.session_state.opening_hours:
                st.error("กรุณาเพิ่มเวลาเปิดปิด")
            else:
                new_store = {
                    "name": st.session_state.store_name,
                    "description": st.session_state.store_description,
                    "canteenId": ObjectId(st.session_state.selected_canteen_id),
                    "openingHours": st.session_state.opening_hours,
                    "menu": [],
                }
                result = store_collection.insert_one(new_store)
                new_store_id = result.inserted_id

                st.success(
                    f"เพิ่มร้านค้า {st.session_state.store_name} ใน {canteen_options[st.session_state.selected_canteen_id]} เรียบร้อยแล้ว!"
                )

                # Reset input values
                st.session_state.store_name = ""
                st.session_state.store_description = ""
                st.session_state.opening_hours = []
                st.session_state.opening_hours_mode = "everyday"
                st.rerun()
    else:
        # Save Changes button for editing mode
        if st.button("บันทึกการเปลี่ยนแปลง"):
            updated_store = {
                "name": st.session_state.store_name,
                "description": st.session_state.store_description,
                "canteenId": ObjectId(st.session_state.selected_canteen_id),
                "openingHours": st.session_state.opening_hours,
                "menu": [],  # You might want to update the menu as well
            }
            update_store(st.session_state.editing_store_id, updated_store)

            st.success(
                f"อัปเดตร้านค้า {st.session_state.store_name} ใน {canteen_options[st.session_state.selected_canteen_id]} เรียบร้อยแล้ว!"
            )

            # Reset editing mode
            st.session_state.editing_store_id = None
            init_session_state()  # Reset session state to default values
            st.rerun()

    st.header(f"ข้อมูลร้านค้าใน {canteen_options[st.session_state.selected_canteen_id]}")

    stores = load_stores()

    for store in stores:
        if str(store["canteenId"]) == st.session_state.selected_canteen_id:
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.write(f"**ชื่อร้าน:** {store['name']}")
                if "description" in store:
                    st.write(f"**คำอธิบาย:** {store['description']}")
                st.write("**เวลาเปิดปิด:**")
                for opening_hour in store.get("openingHours", []):
                    st.write(
                        f"- {opening_hour['dayOfWeek']}: {opening_hour['start']} ถึง {opening_hour['end']}"
                    )
                st.write(f"**จำนวนรายการอาหาร:** {len(store.get('menu', []))}")

            with col2:
                edit_button_key = f"edit_store_{store.get('_id', 'no_id')}"
                if st.button("แก้ไข", key=edit_button_key):
                    st.session_state.editing_store_id = str(store["_id"])
                    st.rerun()

            with col3:
                delete_button_key = f"delete_store_{store.get('_id', 'no_id')}"
                if st.button("ลบ", key=delete_button_key):
                    delete_store(str(store["_id"]))
                    st.rerun()