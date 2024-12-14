import streamlit as st
import pymongo
import datetime
import hmac

from pymongo.server_api import ServerApi

st.set_page_config(page_title="ข้อมูลโรงอาหาร", page_icon="🍽️")

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

st.title("🍽️ ข้อมูลโรงอาหาร")

# Function to load canteen data from MongoDB
def load_canteen_data() -> list:
    db = mongo.muge_canteen
    data = db.canteen_data.find()
    return list(data)

# Function to save canteen data to MongoDB
def save_canteen_data(canteen_data):
    db = mongo.muge_canteen
    canteen_collection = db.canteen_data

    for entry in canteen_data:
        canteen_collection.replace_one(
            {"id": entry['id']},
            entry,
            upsert=True
        )

# Initialize input fields in session state if not present
if "canteen_name" not in st.session_state:
    st.session_state.canteen_name = ""
if "busy_start_time" not in st.session_state:
    st.session_state.busy_start_time = datetime.time(11, 0)
if "busy_end_time" not in st.session_state:
    st.session_state.busy_end_time = datetime.time(13, 0)
if "with_airconditioning" not in st.session_state:
    st.session_state.with_airconditioning = False
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

# --- Input Form ---
st.header("เพิ่ม/แก้ไข ข้อมูลโรงอาหาร")

# --- Input Fields ---
# Canteen name is now always editable
st.session_state.canteen_name = st.text_input("กรอกชื่อโรงอาหาร", value=st.session_state.canteen_name)

st.write("**ช่วงเวลาที่มีลูกค้าเยอะ** (ระบุแค่ช่วงเวลา)")
st.session_state.busy_start_time = st.time_input(
    "เวลาเริ่มต้น", value=st.session_state.busy_start_time
)
st.session_state.busy_end_time = st.time_input(
    "เวลาสิ้นสุด", value=st.session_state.busy_end_time
)
if st.session_state.busy_end_time < st.session_state.busy_start_time:
    st.error("เวลาสิ้นสุดต้องมากกว่าเวลาเริ่มต้น")

st.session_state.with_airconditioning = st.checkbox(
    "มีเครื่องปรับอากาศ", value=st.session_state.with_airconditioning
)

canteen_collection = mongo.muge_canteen.canteen_data

# --- Add or Edit Entry Button ---
if st.session_state.editing_id is None:
    button_label = "เพิ่มข้อมูล"
    if st.button(button_label):
        canteen_data = load_canteen_data()  # Load data inside the button logic
        # Check for duplicate canteen names (case-insensitive)
        canteen_names = [entry["canteen_name"].lower() for entry in canteen_data]
        if st.session_state.canteen_name.lower() in canteen_names:
            st.error("มีชื่อโรงอาหารนี้อยู่แล้ว กรุณาใช้ชื่ออื่น")
        elif not st.session_state.canteen_name:
            st.error("กรุณากรอกชื่อโรงอาหาร")
        else:
            # Create a dictionary for the new entry
            entry = {
                "id": (
                    max([c["id"] for c in canteen_data], default=0) + 1
                ),
                "canteen_name": st.session_state.canteen_name,
                "busy_hours": {
                    "start_time": st.session_state.busy_start_time.strftime("%H:%M"),
                    "end_time": st.session_state.busy_end_time.strftime("%H:%M"),
                },
                "with_airconditioning": st.session_state.with_airconditioning,
                "stores": [],
            }

            # Add the new entry to the canteen data
            canteen_collection.insert_one(entry)
            st.success("เพิ่มข้อมูลโรงอาหารเรียบร้อยแล้ว!")

            # Reset input values in session state
            st.session_state.canteen_name = ""
            st.session_state.busy_start_time = datetime.time(11, 0)
            st.session_state.busy_end_time = datetime.time(13, 0)
            st.session_state.with_airconditioning = False
            st.rerun()  # Force refresh after adding
else:
    button_label = "บันทึกการแก้ไข"
    if st.button(button_label):
        canteen_data = load_canteen_data()  # Load data inside the button logic
        if not st.session_state.canteen_name:
            st.error("กรุณากรอกชื่อโรงอาหาร")
        else:
            # Check for duplicate canteen names (case-insensitive),
            # excluding the current canteen being edited
            canteen_names = [entry["canteen_name"].lower() for entry in canteen_data if entry["id"] != st.session_state.editing_id]
            if st.session_state.canteen_name.lower() in canteen_names:
                st.error("มีชื่อโรงอาหารนี้อยู่แล้ว กรุณาใช้ชื่ออื่น")
                st.rerun()  # Force refresh to show error
            else:
                # Find the entry to edit
                entry_index = next((i for i, entry in enumerate(canteen_data) if entry["id"] == st.session_state.editing_id), None)

                if entry_index is not None:
                    canteen_collection.update_one(
                        {"id": st.session_state.editing_id},
                        {
                            "$set": {
                                "canteen_name": st.session_state.canteen_name,
                                "busy_hours": {
                                    "start_time": st.session_state.busy_start_time.strftime("%H:%M"),
                                    "end_time": st.session_state.busy_end_time.strftime("%H:%M"),
                                },
                                "with_airconditioning": st.session_state.with_airconditioning,
                            }
                        },
                    )

                    st.success("แก้ไขข้อมูลโรงอาหารเรียบร้อยแล้ว!")

                    # Reset input values and editing state
                    st.session_state.canteen_name = ""
                    st.session_state.busy_start_time = datetime.time(11, 0)
                    st.session_state.busy_end_time = datetime.time(13, 0)
                    st.session_state.with_airconditioning = False
                    st.session_state.editing_id = None
                    st.rerun()  # Force refresh after editing

# --- Display, Edit, and Delete ---
st.header("ข้อมูลโรงอาหารปัจจุบัน")

canteen_data = load_canteen_data() # Load data for display

# Create columns for actions
for i, entry in enumerate(canteen_data):
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        # Display entry details in Thai
        st.write(f"**ชื่อโรงอาหาร:** {entry['canteen_name']}")
        st.write(
            f"**ช่วงเวลาที่มีลูกค้าเยอะ:** {entry['busy_hours']['start_time']} - {entry['busy_hours']['end_time']}"
        )
        st.write(
            "**มีเครื่องปรับอากาศ:** "
            + ("ใช่" if entry["with_airconditioning"] else "ไม่ใช่")
        )
        st.write(f"**จำนวนร้านค้า:** {len(entry['stores'])}")

    with col2:
        if st.button("แก้ไข", key=f"edit_{entry['id']}"):
            # Set session state for editing
            st.session_state.editing_id = entry["id"]
            st.session_state.canteen_name = entry["canteen_name"]
            st.session_state.busy_start_time = datetime.datetime.strptime(
                entry["busy_hours"]["start_time"], "%H:%M"
            ).time()
            st.session_state.busy_end_time = datetime.datetime.strptime(
                entry["busy_hours"]["end_time"], "%H:%M"
            ).time()
            st.session_state.with_airconditioning = entry["with_airconditioning"]
            st.rerun()  # Force refresh to update input fields

    with col3:
        if st.button("ลบ", key=f"delete_{entry['id']}"):
            canteen_collection.delete_one({"id": entry['id']})
            st.session_state.editing_id = None  # Reset editing state if deleting the edited item
            st.rerun()  # Force refresh after deleting