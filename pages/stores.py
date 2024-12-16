import streamlit as st
import pymongo
from pymongo.server_api import ServerApi
import datetime
import hmac

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
st.sidebar.page_link("pages/download_json.py", label="ดาวน์โหลดข้อมูล JSON", icon="⬇️")

@st.cache_resource()
def database_init():
    return pymongo.MongoClient(st.secrets['mongo_uri'], server_api=ServerApi('1'))

       
mongo = database_init()

if not mongo:
    st.error('Cannot Access Data Storage')
    st.stop()

st.title("🏪 ข้อมูลร้านค้า")

# Function to load canteen data from MongoDB
def load_canteens():
    db = mongo.canteen_info
    data = db.canteens.find()
    data = list(data)
    return data

# Function to save canteen data to MongoDB
def save_canteens(canteens):
    db = mongo.canteen_info
    canteen_collection = db.canteens

    for entry in canteens:
        canteen_collection.replace_one(
            {"id": entry['id']},
            entry,
            upsert=True
        )

# Load existing canteen data
canteens = load_canteens()

# --- Extract Existing Canteen Names ---
existing_canteen_names = [entry["canteen_name"] for entry in canteens]

# --- Input Form ---
st.header("เพิ่ม/แก้ไข ข้อมูลร้านค้า")

# Use session state to store input values and manage widget keys
if "editing_store_index" not in st.session_state:
    st.session_state.editing_store_index = None

def init_session_state(store=None):
    st.session_state.store_name = store["name"] if store else ""
    st.session_state.opening_option = store["opening_hours"]["frequency"] if store else "everyday" # Changed to English
    st.session_state.opening_days = list(store["opening_hours"]["days"].keys()) if store and st.session_state.opening_option == "specific_days" else [] # Changed to English
    st.session_state.opening_start_date = datetime.datetime.strptime(store["opening_hours"]["start_date"], "%Y-%m-%d").date() if store and "start_date" in store["opening_hours"] else datetime.date.today()
    st.session_state.opening_end_date = datetime.datetime.strptime(store["opening_hours"]["end_date"], "%Y-%m-%d").date() if store and "end_date" in store["opening_hours"] else datetime.date.today()
    if store:
        st.session_state.opening_hours_dict = {
            day: {
                "start_time": datetime.datetime.strptime(hours["start_time"], "%H:%M").time(),
                "end_time": datetime.datetime.strptime(hours["end_time"], "%H:%M").time()
            } for day, hours in store["opening_hours"]["days"].items()
        } if store and st.session_state.opening_option in ["specific_days", "date_range"] else { # Changed to English
            "everyday": {
                "start_time": datetime.datetime.strptime(store["opening_hours"]["days"]["everyday"]["start_time"], "%H:%M").time(),
                "end_time": datetime.datetime.strptime(store["opening_hours"]["days"]["everyday"]["end_time"], "%H:%M").time()
            } if store and "everyday" in store["opening_hours"]["days"] else {
                "start_time": datetime.time(7, 0),
                "end_time": datetime.time(16, 0)
            }
        }
    else:
        st.session_state.opening_hours_dict = {
            "everyday": {
                "start_time": datetime.time(7, 0),
                "end_time": datetime.time(16, 0)
            }
        }

# Initialize session state based on whether we are editing or adding
if st.session_state.editing_store_index is not None:
    canteen_index = next((i for i, c in enumerate(canteens) if c["canteen_name"] == st.session_state.selected_canteen), None)
    store_to_edit = canteens[canteen_index]["stores"][st.session_state.editing_store_index]
    init_session_state(store_to_edit)
else:
    init_session_state()

# --- Unique keys for selectbox and text input ---
store_name_key = f"store_name_{st.session_state.editing_store_index}"
opening_option_key = f"opening_option_{st.session_state.editing_store_index}"

# --- Input Fields ---
st.session_state.selected_canteen = st.selectbox(
    "เลือกโรงอาหาร",
    options=existing_canteen_names,
    index=0
)

if not st.session_state.selected_canteen:
    st.info("กรุณาเลือกโรงอาหารก่อน")
else:
    canteen_index = next((i for i, c in enumerate(canteens) if c["canteen_name"] == st.session_state.selected_canteen), None)

    # --- Input Fields for Store ---
    st.session_state.store_name = st.text_input("ชื่อร้านค้า", value=st.session_state.store_name, key=store_name_key)

    # --- Frequency Selection (Modified) ---
    frequencies_thai = ["ทุกวัน", "วันเว้นวัน", "เฉพาะบางวัน", "ช่วงวันที่"]
    frequencies_english = ["everyday", "every_other_day", "specific_days", "date_range"]
    frequencies_map = dict(zip(frequencies_english, frequencies_thai)) # Mapping for display

    
    st.session_state.opening_option_thai = st.selectbox(
        "ความถี่", frequencies_thai, key=opening_option_key, index=frequencies_thai.index(frequencies_map.get(st.session_state.opening_option, "ทุกวัน")) # Default to "ทุกวัน" if not found
    )
    st.session_state.opening_option = [key for key, value in frequencies_map.items() if value == st.session_state.opening_option_thai][0] # Convert back to English for internal use

    days_of_week = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    days_of_week_map = {
        "จันทร์": "monday",
        "อังคาร": "tuesday",
        "พุธ": "wednesday",
        "พฤหัสบดี": "thursday",
        "ศุกร์": "friday",
        "เสาร์": "saturday",
        "อาทิตย์": "sunday"
    }

    if st.session_state.opening_option == "specific_days":
        opening_days_thai = st.multiselect(
            "เลือกวัน",
            days_of_week,
            default=[day for day in days_of_week if days_of_week_map[day] in st.session_state.opening_days]
        )

        st.session_state.opening_days = [days_of_week_map[day] for day in opening_days_thai if day in days_of_week_map]
        
        if st.session_state.opening_days:
            for day in st.session_state.opening_days:
                day_thai = [thai_day for thai_day, eng_day in days_of_week_map.items() if eng_day == day][0]
                with st.expander(f"ตั้งค่าเวลาเปิดปิดของวัน{day_thai}"):
                    if day not in st.session_state.opening_hours_dict:
                        st.session_state.opening_hours_dict[day] = {
                            "start_time": datetime.time(7, 0),
                            "end_time": datetime.time(16, 0)
                        }

                    st.session_state.opening_hours_dict[day]["start_time"] = st.time_input(
                        f"เวลาเปิด ({day_thai})",
                        value=st.session_state.opening_hours_dict[day]["start_time"],
                        key=f"start_time_{day}_{st.session_state.editing_store_index}"
                    )
                    st.session_state.opening_hours_dict[day]["end_time"] = st.time_input(
                        f"เวลาปิด ({day_thai})",
                        value=st.session_state.opening_hours_dict[day]["end_time"],
                        key=f"end_time_{day}_{st.session_state.editing_store_index}"
                    )

                    if st.session_state.opening_hours_dict[day]["end_time"] < st.session_state.opening_hours_dict[day]["start_time"]:
                        st.error(f"เวลาปิดของวัน{day_thai} ต้องมากกว่าเวลาเปิด")
    elif st.session_state.opening_option == "date_range":
        st.session_state.opening_start_date = st.date_input(
            "วันที่เริ่มต้น", value=st.session_state.opening_start_date
        )
        st.session_state.opening_end_date = st.date_input(
            "วันที่สิ้นสุด", value=st.session_state.opening_end_date
        )
        if st.session_state.opening_end_date < st.session_state.opening_start_date:
            st.error("วันที่สิ้นสุดต้องมากกว่าวันที่เริ่มต้น")

        for day in days_of_week_map.values():
            day_thai = [thai_day for thai_day, eng_day in days_of_week_map.items() if eng_day == day][0]
            with st.expander(f"ตั้งค่าเวลาเปิดปิดของวัน{day_thai}"):
                if day not in st.session_state.opening_hours_dict:
                    st.session_state.opening_hours_dict[day] = {
                        "start_time": datetime.time(7, 0),
                        "end_time": datetime.time(16, 0)
                    }

                st.session_state.opening_hours_dict[day]["start_time"] = st.time_input(
                    f"เวลาเปิด ({day_thai})",
                    value=st.session_state.opening_hours_dict[day]["start_time"],
                    key=f"start_time_{day}_{st.session_state.editing_store_index}"
                )
                st.session_state.opening_hours_dict[day]["end_time"] = st.time_input(
                    f"เวลาปิด ({day_thai})",
                    value=st.session_state.opening_hours_dict[day]["end_time"],
                    key=f"end_time_{day}_{st.session_state.editing_store_index}"
                )

                if st.session_state.opening_hours_dict[day]["end_time"] < st.session_state.opening_hours_dict[day]["start_time"]:
                    st.error(f"เวลาปิดของวัน{day_thai} ต้องมากกว่าเวลาเปิด")

    elif st.session_state.opening_option == "everyday" or st.session_state.opening_option == "every_other_day":
        if "everyday" not in st.session_state.opening_hours_dict:
            st.session_state.opening_hours_dict["everyday"] = {
                "start_time": datetime.time(7, 0),
                "end_time": datetime.time(16, 0)
            }
        st.session_state.opening_hours_dict["everyday"]["start_time"] = st.time_input(
            f"เวลาเปิด",
            value=st.session_state.opening_hours_dict["everyday"]["start_time"],
            key=f"start_time_ทุกวัน_{st.session_state.editing_store_index}"
        )
        st.session_state.opening_hours_dict["everyday"]["end_time"] = st.time_input(
            f"เวลาปิด",
            value=st.session_state.opening_hours_dict["everyday"]["end_time"],
            key=f"end_time_ทุกวัน_{st.session_state.editing_store_index}"
        )
        if st.session_state.opening_hours_dict["everyday"]["end_time"] < st.session_state.opening_hours_dict["everyday"]["start_time"]:
            st.error(f"เวลาปิดต้องมากกว่าเวลาเปิด")

    # --- Add or Edit Store Button ---
    if st.session_state.editing_store_index is None:
        button_label = "เพิ่มร้านค้า"
        if st.button(button_label):
            if not st.session_state.store_name:
                st.error("กรุณากรอกชื่อร้านค้า")
            else:
                new_store = {
                    "name": st.session_state.store_name,
                    "opening_hours": {
                        "frequency": st.session_state.opening_option,
                        "days": {}
                    },
                    "food_items": []  # Create empty food_items list
                }
                
                if st.session_state.opening_option == "specific_days":
                    new_store["opening_hours"]["days"] = {
                        day: {
                            "start_time": st.session_state.opening_hours_dict[day]["start_time"].strftime("%H:%M"),
                            "end_time": st.session_state.opening_hours_dict[day]["end_time"].strftime("%H:%M")
                        } for day in st.session_state.opening_days
                    }
                elif st.session_state.opening_option == "date_range":
                    new_store["opening_hours"]["start_date"] = st.session_state.opening_start_date.strftime("%Y-%m-%d")
                    new_store["opening_hours"]["end_date"] = st.session_state.opening_end_date.strftime("%Y-%m-%d")
                    new_store["opening_hours"]["days"] = {
                        day: {
                            "start_time": st.session_state.opening_hours_dict[day]["start_time"].strftime("%H:%M"),
                            "end_time": st.session_state.opening_hours_dict[day]["end_time"].strftime("%H:%M")
                        } for day in days_of_week_map.values()
                    }
                elif st.session_state.opening_option == "everyday" or st.session_state.opening_option == "every_other_day":
                    new_store["opening_hours"]["days"]["everyday"] = {
                        "start_time": st.session_state.opening_hours_dict["everyday"]["start_time"].strftime("%H:%M"),
                        "end_time": st.session_state.opening_hours_dict["everyday"]["end_time"].strftime("%H:%M")
                    }

                canteens[canteen_index]["stores"].append(new_store)
                save_canteens(canteens)
                st.success(f"เพิ่มร้านค้า {st.session_state.store_name} ใน {st.session_state.selected_canteen} เรียบร้อยแล้ว!")

                # Reset input values in session state
                st.session_state.editing_store_index = None
                init_session_state()
                st.rerun()
    else:
        button_label = "บันทึกการแก้ไข"
        if st.button(button_label):
            if not st.session_state.store_name:
                st.error("กรุณากรอกชื่อร้านค้า")
            else:
                updated_store = {
                    "name": st.session_state.store_name,
                    "opening_hours": {
                        "frequency": st.session_state.opening_option,
                        "days": {}
                    },
                    "food_items": canteens[canteen_index]["stores"][st.session_state.editing_store_index][
                        "food_items"
                    ],  # Keep existing food_items
                }

                if st.session_state.opening_option == "specific_days":
                    updated_store["opening_hours"]["days"] = {
                        day: {
                            "start_time": st.session_state.opening_hours_dict[day]["start_time"].strftime("%H:%M"),
                            "end_time": st.session_state.opening_hours_dict[day]["end_time"].strftime("%H:%M")
                        } for day in st.session_state.opening_days
                    }
                elif st.session_state.opening_option == "date_range":
                    updated_store["opening_hours"]["start_date"] = st.session_state.opening_start_date.strftime("%Y-%m-%d")
                    updated_store["opening_hours"]["end_date"] = st.session_state.opening_end_date.strftime("%Y-%m-%d")
                    updated_store["opening_hours"]["days"] = {
                        day: {
                            "start_time": st.session_state.opening_hours_dict[day]["start_time"].strftime("%H:%M"),
                            "end_time": st.session_state.opening_hours_dict[day]["end_time"].strftime("%H:%M")
                        } for day in days_of_week_map.values()
                    }
                elif st.session_state.opening_option == "everyday" or st.session_state.opening_option == "every_other_day":
                    updated_store["opening_hours"]["days"]["everyday"] = {
                        "start_time": st.session_state.opening_hours_dict["everyday"]["start_time"].strftime("%H:%M"),
                        "end_time": st.session_state.opening_hours_dict["everyday"]["end_time"].strftime("%H:%M")
                    }
                
                canteens[canteen_index]["stores"][st.session_state.editing_store_index] = updated_store
                save_canteens(canteens)
                st.success(f"แก้ไขร้านค้า {st.session_state.store_name} ใน {st.session_state.selected_canteen} เรียบร้อยแล้ว!")

                # Reset input values and editing state
                st.session_state.editing_store_index = None
                init_session_state()
                st.rerun()

    # --- Display, Edit, and Delete Stores ---
    st.header(f"ข้อมูลร้านค้าใน {st.session_state.selected_canteen}")

    for i, store in enumerate(canteens[canteen_index]["stores"]):
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.write(f"**ชื่อร้าน:** {store['name']}")
            
            # --- Display Opening Hours (Modified) ---
            freq_display = frequencies_map.get(store["opening_hours"]["frequency"], store["opening_hours"]["frequency"]) # Get Thai display or use English if not found
            if store["opening_hours"]["frequency"] in ["everyday", "every_other_day"]:
                st.write(f"**เวลาเปิด-ปิด:** {freq_display} {store['opening_hours']['days']["everyday"]['start_time']}-{store['opening_hours']['days']["everyday"]['end_time']}")
            elif store["opening_hours"]["frequency"] == "specific_days":
                for day, hours in store['opening_hours']['days'].items():
                    day_thai = [thai_day for thai_day, eng_day in days_of_week_map.items() if eng_day == day][0]
                    st.write(f"**{day_thai}:** {hours['start_time']}-{hours['end_time']}")
            elif store["opening_hours"]["frequency"] == "date_range":
                st.write(f"**วันที่:** {store['opening_hours']['start_date']} ถึง {store['opening_hours']['end_date']}")
                for day, hours in store['opening_hours']['days'].items():
                    day_thai = [thai_day for thai_day, eng_day in days_of_week_map.items() if eng_day == day][0]
                    st.write(f"**{day_thai}:** {hours['start_time']}-{hours['end_time']}")
            st.write(f"**จำนวนรายการอาหาร:** {len(store['food_items'])}")

        with col2:
            if st.button(f"แก้ไข", key=f"edit_store_{i}"):
                # Set session state for editing
                st.session_state.editing_store_index = i
                st.session_state.selected_canteen = canteens[canteen_index]["canteen_name"]
                st.rerun()

        with col3:
            if st.button(f"ลบ", key=f"delete_store_{i}"):
                canteens[canteen_index]["stores"].pop(i)
                save_canteens(canteens)
                st.session_state.editing_store_index = None
                init_session_state()
                st.rerun()