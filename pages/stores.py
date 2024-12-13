import streamlit as st
import json
import datetime

st.set_page_config(page_title="ข้อมูลร้านค้า", page_icon="🏪")

st.sidebar.header("MUGE100 C10-297 Data Entry")
st.sidebar.markdown("Implementation by Chanakan Moongthin")
st.sidebar.page_link("canteen.py", label="ข้อมูลโรงอาหาร", icon="🍽️")
st.sidebar.page_link("pages/stores.py", label="ข้อมูลร้านค้า", icon="🏪")
st.sidebar.page_link("pages/food_items.py", label="ข้อมูลรายการอาหาร", icon="🍲")
st.sidebar.page_link("pages/download_json.py", label="ดาวน์โหลดข้อมูล JSON", icon="⬇️")

st.title("🏪 ข้อมูลร้านค้า")

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

# Load existing canteen data
canteen_data = load_canteen_data()

# --- Extract Existing Canteen Names ---
existing_canteen_names = [entry["canteen_name"] for entry in canteen_data]

# --- Input Form ---
st.header("เพิ่ม/แก้ไข ข้อมูลร้านค้า")

# Use session state to store input values and manage widget keys
if "editing_store_index" not in st.session_state:
    st.session_state.editing_store_index = None

def init_session_state(store=None):
    st.session_state.store_name = store["name"] if store else ""
    st.session_state.opening_option = store["opening_hours"]["frequency"] if store else "ทุกวัน"
    st.session_state.opening_days = list(store["opening_hours"]["days"].keys()) if store and st.session_state.opening_option == "เฉพาะบางวัน" else []
    st.session_state.opening_start_date = datetime.datetime.strptime(store["opening_hours"]["start_date"], "%Y-%m-%d").date() if store and "start_date" in store["opening_hours"] else datetime.date.today()
    st.session_state.opening_end_date = datetime.datetime.strptime(store["opening_hours"]["end_date"], "%Y-%m-%d").date() if store and "end_date" in store["opening_hours"] else datetime.date.today()
    if store:
        st.session_state.opening_hours_dict = {
            day: {
                "start_time": datetime.datetime.strptime(hours["start_time"], "%H:%M").time(),
                "end_time": datetime.datetime.strptime(hours["end_time"], "%H:%M").time()
            } for day, hours in store["opening_hours"]["days"].items()
        } if store and st.session_state.opening_option in ["เฉพาะบางวัน", "ช่วงวันที่"] else {
            "ทุกวัน": {
                "start_time": datetime.datetime.strptime(store["opening_hours"]["days"]["ทุกวัน"]["start_time"], "%H:%M").time(),
                "end_time": datetime.datetime.strptime(store["opening_hours"]["days"]["ทุกวัน"]["end_time"], "%H:%M").time()
            } if store and "ทุกวัน" in store["opening_hours"]["days"] else {
                "start_time": datetime.time(7, 0),
                "end_time": datetime.time(16, 0)
            }
        }
    else:
        st.session_state.opening_hours_dict = {
            "ทุกวัน": {
                "start_time": datetime.time(7, 0),
                "end_time": datetime.time(16, 0)
            }
        }

# Initialize session state based on whether we are editing or adding
if st.session_state.editing_store_index is not None:
    canteen_index = next((i for i, c in enumerate(canteen_data) if c["canteen_name"] == st.session_state.selected_canteen), None)
    store_to_edit = canteen_data[canteen_index]["stores"][st.session_state.editing_store_index]
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
    canteen_index = next((i for i, c in enumerate(canteen_data) if c["canteen_name"] == st.session_state.selected_canteen), None)

    # --- Input Fields for Store ---
    st.session_state.store_name = st.text_input("ชื่อร้านค้า", value=st.session_state.store_name, key=store_name_key)
    
    st.session_state.opening_option = st.selectbox(
        "ความถี่", ["ทุกวัน", "วันเว้นวัน", "เฉพาะบางวัน", "ช่วงวันที่"], key=opening_option_key, index=["ทุกวัน", "วันเว้นวัน", "เฉพาะบางวัน", "ช่วงวันที่"].index(st.session_state.opening_option)
    )

    days_of_week = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

    if st.session_state.opening_option == "เฉพาะบางวัน":
        st.session_state.opening_days = st.multiselect(
            "เลือกวัน",
            days_of_week,
            default=st.session_state.opening_days
        )
        
        if st.session_state.opening_days:
            for day in st.session_state.opening_days:
                with st.expander(f"ตั้งค่าเวลาเปิดปิดของวัน{day}"):
                    if day not in st.session_state.opening_hours_dict:
                        st.session_state.opening_hours_dict[day] = {
                            "start_time": datetime.time(7, 0),
                            "end_time": datetime.time(16, 0)
                        }

                    st.session_state.opening_hours_dict[day]["start_time"] = st.time_input(
                        f"เวลาเปิด ({day})",
                        value=st.session_state.opening_hours_dict[day]["start_time"],
                        key=f"start_time_{day}_{st.session_state.editing_store_index}"
                    )
                    st.session_state.opening_hours_dict[day]["end_time"] = st.time_input(
                        f"เวลาปิด ({day})",
                        value=st.session_state.opening_hours_dict[day]["end_time"],
                        key=f"end_time_{day}_{st.session_state.editing_store_index}"
                    )

                    if st.session_state.opening_hours_dict[day]["end_time"] < st.session_state.opening_hours_dict[day]["start_time"]:
                        st.error(f"เวลาปิดของวัน{day} ต้องมากกว่าเวลาเปิด")
    elif st.session_state.opening_option == "ช่วงวันที่":
        st.session_state.opening_start_date = st.date_input(
            "วันที่เริ่มต้น", value=st.session_state.opening_start_date
        )
        st.session_state.opening_end_date = st.date_input(
            "วันที่สิ้นสุด", value=st.session_state.opening_end_date
        )
        if st.session_state.opening_end_date < st.session_state.opening_start_date:
            st.error("วันที่สิ้นสุดต้องมากกว่าวันที่เริ่มต้น")

        for day in days_of_week:
            with st.expander(f"ตั้งค่าเวลาเปิดปิดของวัน{day}"):
                if day not in st.session_state.opening_hours_dict:
                    st.session_state.opening_hours_dict[day] = {
                        "start_time": datetime.time(7, 0),
                        "end_time": datetime.time(16, 0)
                    }

                st.session_state.opening_hours_dict[day]["start_time"] = st.time_input(
                    f"เวลาเปิด ({day})",
                    value=st.session_state.opening_hours_dict[day]["start_time"],
                    key=f"start_time_{day}_{st.session_state.editing_store_index}"
                )
                st.session_state.opening_hours_dict[day]["end_time"] = st.time_input(
                    f"เวลาปิด ({day})",
                    value=st.session_state.opening_hours_dict[day]["end_time"],
                    key=f"end_time_{day}_{st.session_state.editing_store_index}"
                )

                if st.session_state.opening_hours_dict[day]["end_time"] < st.session_state.opening_hours_dict[day]["start_time"]:
                    st.error(f"เวลาปิดของวัน{day} ต้องมากกว่าเวลาเปิด")

    elif st.session_state.opening_option == "ทุกวัน" or st.session_state.opening_option == "วันเว้นวัน":
        if "ทุกวัน" not in st.session_state.opening_hours_dict:
            st.session_state.opening_hours_dict["ทุกวัน"] = {
                "start_time": datetime.time(7, 0),
                "end_time": datetime.time(16, 0)
            }
        st.session_state.opening_hours_dict["ทุกวัน"]["start_time"] = st.time_input(
            f"เวลาเปิด",
            value=st.session_state.opening_hours_dict["ทุกวัน"]["start_time"],
            key=f"start_time_ทุกวัน_{st.session_state.editing_store_index}"
        )
        st.session_state.opening_hours_dict["ทุกวัน"]["end_time"] = st.time_input(
            f"เวลาปิด",
            value=st.session_state.opening_hours_dict["ทุกวัน"]["end_time"],
            key=f"end_time_ทุกวัน_{st.session_state.editing_store_index}"
        )
        if st.session_state.opening_hours_dict["ทุกวัน"]["end_time"] < st.session_state.opening_hours_dict["ทุกวัน"]["start_time"]:
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
                
                if st.session_state.opening_option == "เฉพาะบางวัน":
                    new_store["opening_hours"]["days"] = {
                        day: {
                            "start_time": st.session_state.opening_hours_dict[day]["start_time"].strftime("%H:%M"),
                            "end_time": st.session_state.opening_hours_dict[day]["end_time"].strftime("%H:%M")
                        } for day in st.session_state.opening_days
                    }
                elif st.session_state.opening_option == "ช่วงวันที่":
                    new_store["opening_hours"]["start_date"] = st.session_state.opening_start_date.strftime("%Y-%m-%d")
                    new_store["opening_hours"]["end_date"] = st.session_state.opening_end_date.strftime("%Y-%m-%d")
                    new_store["opening_hours"]["days"] = {
                        day: {
                            "start_time": st.session_state.opening_hours_dict[day]["start_time"].strftime("%H:%M"),
                            "end_time": st.session_state.opening_hours_dict[day]["end_time"].strftime("%H:%M")
                        } for day in days_of_week
                    }
                elif st.session_state.opening_option == "ทุกวัน" or st.session_state.opening_option == "วันเว้นวัน":
                    new_store["opening_hours"]["days"]["ทุกวัน"] = {
                        "start_time": st.session_state.opening_hours_dict["ทุกวัน"]["start_time"].strftime("%H:%M"),
                        "end_time": st.session_state.opening_hours_dict["ทุกวัน"]["end_time"].strftime("%H:%M")
                    }

                canteen_data[canteen_index]["stores"].append(new_store)
                save_canteen_data(canteen_data)
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
                    "food_items": canteen_data[canteen_index]["stores"][st.session_state.editing_store_index][
                        "food_items"
                    ],  # Keep existing food_items
                }

                if st.session_state.opening_option == "เฉพาะบางวัน":
                    updated_store["opening_hours"]["days"] = {
                        day: {
                            "start_time": st.session_state.opening_hours_dict[day]["start_time"].strftime("%H:%M"),
                            "end_time": st.session_state.opening_hours_dict[day]["end_time"].strftime("%H:%M")
                        } for day in st.session_state.opening_days
                    }
                elif st.session_state.opening_option == "ช่วงวันที่":
                    updated_store["opening_hours"]["start_date"] = st.session_state.opening_start_date.strftime("%Y-%m-%d")
                    updated_store["opening_hours"]["end_date"] = st.session_state.opening_end_date.strftime("%Y-%m-%d")
                    updated_store["opening_hours"]["days"] = {
                        day: {
                            "start_time": st.session_state.opening_hours_dict[day]["start_time"].strftime("%H:%M"),
                            "end_time": st.session_state.opening_hours_dict[day]["end_time"].strftime("%H:%M")
                        } for day in days_of_week
                    }
                elif st.session_state.opening_option == "ทุกวัน" or st.session_state.opening_option == "วันเว้นวัน":
                    updated_store["opening_hours"]["days"]["ทุกวัน"] = {
                        "start_time": st.session_state.opening_hours_dict["ทุกวัน"]["start_time"].strftime("%H:%M"),
                        "end_time": st.session_state.opening_hours_dict["ทุกวัน"]["end_time"].strftime("%H:%M")
                    }
                
                canteen_data[canteen_index]["stores"][st.session_state.editing_store_index] = updated_store
                save_canteen_data(canteen_data)
                st.success(f"แก้ไขร้านค้า {st.session_state.store_name} ใน {st.session_state.selected_canteen} เรียบร้อยแล้ว!")

                # Reset input values and editing state
                st.session_state.editing_store_index = None
                init_session_state()
                st.rerun()

    # --- Display, Edit, and Delete Stores ---
    st.header(f"ข้อมูลร้านค้าใน {st.session_state.selected_canteen}")

    for i, store in enumerate(canteen_data[canteen_index]["stores"]):
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.write(f"**ชื่อร้าน:** {store['name']}")
            
            if store["opening_hours"]["frequency"] == "ทุกวัน":
                freq_display = "ทุกวัน"
                st.write(f"**เวลาเปิด-ปิด:** {freq_display} {store['opening_hours']['days']['ทุกวัน']['start_time']}-{store['opening_hours']['days']['ทุกวัน']['end_time']}")
            elif store["opening_hours"]["frequency"] == "วันเว้นวัน":
                freq_display = "วันเว้นวัน"
                st.write(f"**เวลาเปิด-ปิด:** {freq_display} {store['opening_hours']['days']['ทุกวัน']['start_time']}-{store['opening_hours']['days']['ทุกวัน']['end_time']}")
            elif store["opening_hours"]["frequency"] == "เฉพาะบางวัน":
                for day, hours in store['opening_hours']['days'].items():
                    st.write(f"**{day}:** {hours['start_time']}-{hours['end_time']}")
            elif store["opening_hours"]["frequency"] == "ช่วงวันที่":
                st.write(f"**วันที่:** {store['opening_hours']['start_date']} ถึง {store['opening_hours']['end_date']}")
                for day, hours in store['opening_hours']['days'].items():
                    st.write(f"**{day}:** {hours['start_time']}-{hours['end_time']}")
            st.write(f"**จำนวนรายการอาหาร:** {len(store['food_items'])}")

        with col2:
            if st.button(f"แก้ไข", key=f"edit_store_{i}"):
                # Set session state for editing
                st.session_state.editing_store_index = i
                st.session_state.selected_canteen = canteen_data[canteen_index]["canteen_name"]
                st.rerun()

        with col3:
            if st.button(f"ลบ", key=f"delete_store_{i}"):
                canteen_data[canteen_index]["stores"].pop(i)
                save_canteen_data(canteen_data)
                st.session_state.editing_store_index = None
                init_session_state()
                st.rerun()