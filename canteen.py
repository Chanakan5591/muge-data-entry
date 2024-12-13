import streamlit as st
import json
import datetime

st.set_page_config(page_title="ข้อมูลโรงอาหาร", page_icon="🍽️")

st.sidebar.header("MUGE100 C10-297 Data Entry")
st.sidebar.markdown("Implementation by Chanakan Moongthin")
st.sidebar.page_link("canteen.py", label="ข้อมูลโรงอาหาร", icon="🍽️")
st.sidebar.page_link("pages/stores.py", label="ข้อมูลร้านค้า", icon="🏪")
st.sidebar.page_link("pages/food_items.py", label="ข้อมูลรายการอาหาร", icon="🍲")
st.sidebar.page_link("pages/download_json.py", label="ดาวน์โหลดข้อมูล JSON", icon="⬇️")

st.title("🍽️ ข้อมูลโรงอาหาร")

# Function to load canteen data from JSON file
def load_canteen_data(filepath="canteen_data.json"):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Function to save canteen data to JSON file
def save_canteen_data(canteen_data, filepath="canteen_data.json"):
    with open(filepath, "w") as f:
        json.dump(canteen_data, f, indent=4)

# Load existing canteen data or initialize an empty list
canteen_data = load_canteen_data()

# --- Input Form ---
st.header("เพิ่ม/แก้ไข ข้อมูลโรงอาหาร")

# Use session state to store input values
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

# --- Input Fields ---
# Check if we are editing an existing canteen
if st.session_state.editing_id is not None:
    # If editing, display the current canteen name as a non-editable text
    st.session_state.canteen_name = st.text_input(
        "ชื่อโรงอาหาร",
        value=st.session_state.canteen_name
    )
else:
    # If not editing, allow text input for the canteen name
    st.session_state.canteen_name = st.text_input("กรอกชื่อโรงอาหาร")

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

# --- Add or Edit Entry Button ---
if st.session_state.editing_id is None:
    button_label = "เพิ่มข้อมูล"
    if st.button(button_label):
        # Check for duplicate canteen names (case-insensitive)
        canteen_names = [entry["canteen_name"].lower() for entry in canteen_data]
        if st.session_state.canteen_name.lower() in canteen_names:
            st.error("มีชื่อโรงอาหารนี้อยู่แล้ว กรุณาใช้ชื่ออื่น")
        elif not st.session_state.canteen_name:
            st.error("กรุณากรอกชื่อโรงอาหาร")
        else:
            # Create a dictionary for the new entry
            entry = {
                "id": len(canteen_data) + 1 if not canteen_data else max(c["id"] for c in canteen_data) + 1,
                "canteen_name": st.session_state.canteen_name,
                "busy_hours": {
                    "start_time": st.session_state.busy_start_time.strftime("%H:%M"),
                    "end_time": st.session_state.busy_end_time.strftime("%H:%M"),
                },
                "with_airconditioning": st.session_state.with_airconditioning,
                "stores": [],
            }

            # Add the new entry to the canteen data
            canteen_data.append(entry)
            save_canteen_data(canteen_data)
            st.success("เพิ่มข้อมูลโรงอาหารเรียบร้อยแล้ว!")

            # Reset input values in session state
            st.session_state.canteen_name = ""
            st.session_state.busy_start_time = datetime.time(11, 0)
            st.session_state.busy_end_time = datetime.time(13, 0)
            st.session_state.with_airconditioning = False
else:
    button_label = "บันทึกการแก้ไข"
    if st.button(button_label):
        if not st.session_state.canteen_name:
            st.error("กรุณากรอกชื่อโรงอาหาร")
        else:
            # Find the entry to edit
            entry_index = next((i for i, entry in enumerate(canteen_data) if entry["id"] == st.session_state.editing_id), None)

            if entry_index is not None:
                # Update the entry
                canteen_data[entry_index]["canteen_name"] = st.session_state.canteen_name
                canteen_data[entry_index]["busy_hours"]["start_time"] = st.session_state.busy_start_time.strftime("%H:%M")
                canteen_data[entry_index]["busy_hours"]["end_time"] = st.session_state.busy_end_time.strftime("%H:%M")
                canteen_data[entry_index]["with_airconditioning"] = st.session_state.with_airconditioning

                save_canteen_data(canteen_data)
                st.success("แก้ไขข้อมูลโรงอาหารเรียบร้อยแล้ว!")

                # Reset input values and editing state
                st.session_state.canteen_name = ""
                st.session_state.busy_start_time = datetime.time(11, 0)
                st.session_state.busy_end_time = datetime.time(13, 0)
                st.session_state.with_airconditioning = False
                st.session_state.editing_id = None

# --- Display, Edit, and Delete ---
st.header("ข้อมูลโรงอาหารปัจจุบัน")

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
        if st.button(f"แก้ไข", key=f"edit_{entry['id']}"):
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
            st.rerun()

    with col3:
        if st.button(f"ลบ", key=f"delete_{entry['id']}"):
            canteen_data.pop(i)
            save_canteen_data(canteen_data)
            st.rerun()

if st.button("บันทึกข้อมูล"):
    save_canteen_data(canteen_data)
    st.success("บันทึกข้อมูลเรียบร้อยแล้ว!")