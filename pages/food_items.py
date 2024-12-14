import hmac
import streamlit as st
import pymongo
from pymongo.server_api import ServerApi

st.set_page_config(page_title="ข้อมูลรายการอาหาร", page_icon="🍲")

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

st.title("🍲 ข้อมูลรายการอาหาร")

def load_canteen_data():
    db = mongo.muge_canteen
    data = db.canteen_data.find()
    data = list(data)
    return data

def save_canteen_data(canteen_data):
    db = mongo.muge_canteen
    canteen_collection = db.canteen_data

    for entry in canteen_data:
        canteen_collection.replace_one(
            {"id": entry['id']},
            entry,
            upsert=True
        )

canteen_data = load_canteen_data()

# --- Extract Existing Canteen Names, Store Names---
existing_canteen_names = [entry["canteen_name"] for entry in canteen_data]
existing_store_names = {}
for canteen in canteen_data:
    if canteen["canteen_name"] not in existing_store_names:
        existing_store_names[canteen["canteen_name"]] = [
            store["name"] for store in canteen["stores"]
        ]

# --- Initialize Session State ---
if "selected_canteen" not in st.session_state:
    st.session_state.selected_canteen = (
        existing_canteen_names[0] if existing_canteen_names else None
    )
if "selected_store" not in st.session_state:
    st.session_state.selected_store = ""
if "editing_food_index" not in st.session_state:
    st.session_state.editing_food_index = None
if "food_name" not in st.session_state:
    st.session_state.food_name = ""
if "normal_price" not in st.session_state:
    st.session_state.normal_price = 0.0
if "special_price" not in st.session_state:
    st.session_state.special_price = None
food_name_key = f"food_name_{st.session_state.editing_food_index}"
normal_price_key = f"normal_price_{st.session_state.editing_food_index}"
special_price_key = f"special_price_{st.session_state.editing_food_index}"

if st.session_state.editing_food_index is not None:
    canteen_index_edit = next(
        (
            i
            for i, c in enumerate(canteen_data)
            if c["canteen_name"] == st.session_state.selected_canteen
        ),
        None,
    )
    if canteen_index_edit is not None:
        store_index_edit = next(
            (
                i
                for i, s in enumerate(canteen_data[canteen_index_edit]["stores"])
                if s["name"] == st.session_state.selected_store
            ),
            None,
        )
        if store_index_edit is not None:
            if st.session_state.editing_food_index < len(
                canteen_data[canteen_index_edit]["stores"][store_index_edit][
                    "food_items"
                ]
            ):
                food_item = canteen_data[canteen_index_edit]["stores"][
                    store_index_edit
                ]["food_items"][st.session_state.editing_food_index]
                st.session_state.food_name = food_item["name"]
                st.session_state.normal_price = food_item["prices"]["normal"]
                st.session_state.special_price = food_item["prices"].get("special")

# --- Select Canteen ---
canteen_selection = st.selectbox(
    "เลือกโรงอาหาร",
    options=existing_canteen_names,
    index=existing_canteen_names.index(st.session_state.selected_canteen)
    if st.session_state.selected_canteen in existing_canteen_names
    else 0,
    key="canteen_selection",
)

# --- Update Session State ---
if canteen_selection != st.session_state.selected_canteen:
    st.session_state.selected_canteen = canteen_selection
    st.session_state.selected_store = ""  # Reset store selection

# --- Select Store ---
if st.session_state.selected_canteen:
    store_selection = st.selectbox(
        "เลือกร้านค้า",
        options=existing_store_names.get(st.session_state.selected_canteen, []),
        index=existing_store_names.get(st.session_state.selected_canteen, []).index(
            st.session_state.selected_store
        )
        if st.session_state.selected_store
        in existing_store_names.get(st.session_state.selected_canteen, [])
        else 0,
        key="store_selection",
    )

    # --- Update Session State ---
    if store_selection != st.session_state.selected_store:
        st.session_state.selected_store = store_selection

    if not st.session_state.selected_store:
        st.info("กรุณาเลือกร้านค้าก่อน")
    else:
        canteen_index = next(
            (
                i
                for i, c in enumerate(canteen_data)
                if c["canteen_name"] == st.session_state.selected_canteen
            ),
            None,
        )
        store_index = next(
            (
                i
                for i, s in enumerate(canteen_data[canteen_index]["stores"])
                if s["name"] == st.session_state.selected_store
            ),
            None,
        )

        # --- Input Fields for Food Items ---
        st.subheader("รายการอาหาร")
        food_name = st.text_input(
            "ชื่ออาหาร", value=st.session_state.food_name, key=food_name_key
        )
        normal_price = st.number_input(
            "ราคา (ธรรมดา)",
            min_value=0.0,
            format="%.2f",
            value=st.session_state.normal_price,
            key=normal_price_key,
        )
        special_price = st.number_input(
            "ราคา (พิเศษ)",
            min_value=0.0,
            format="%.2f",
            value=st.session_state.special_price,
            key=special_price_key,
        )

        if food_name != st.session_state.food_name:
            st.session_state.food_name = food_name
        if normal_price != st.session_state.normal_price:
            st.session_state.normal_price = normal_price
        if special_price != st.session_state.special_price:
            st.session_state.special_price = special_price

        button_label = (
            "บันทึกการแก้ไข"
            if st.session_state.editing_food_index is not None
            else "เพิ่มรายการอาหาร"
        )
        if st.button(button_label):
            if st.session_state.food_name and st.session_state.normal_price is not None:
                food_item = {
                    "name": st.session_state.food_name,
                    "prices": {"normal": st.session_state.normal_price},
                }
                if st.session_state.special_price is not None:
                    food_item["prices"]["special"] = st.session_state.special_price

                if st.session_state.editing_food_index is not None:
                    canteen_data[canteen_index]["stores"][store_index]["food_items"][
                        st.session_state.editing_food_index
                    ] = food_item
                    st.success(
                        f"แก้ไขรายการอาหาร {st.session_state.food_name} ในร้าน {st.session_state.selected_store} เรียบร้อยแล้ว!"
                    )
                    st.session_state.editing_food_index = None
                    st.session_state.food_name = ""
                    st.session_state.normal_price = 0.0
                    st.session_state.special_price = None
                else:
                    if (
                        "food_items"
                        not in canteen_data[canteen_index]["stores"][store_index]
                    ):
                        canteen_data[canteen_index]["stores"][store_index][
                            "food_items"
                        ] = []
                    canteen_data[canteen_index]["stores"][store_index][
                        "food_items"
                    ].append(food_item)
                    st.success(
                        f"เพิ่มรายการอาหาร {st.session_state.food_name} ในร้าน {st.session_state.selected_store} เรียบร้อยแล้ว!"
                    )
                    st.session_state.food_name = ""
                    st.session_state.normal_price = 0.0
                    st.session_state.special_price = None

                save_canteen_data(canteen_data)

            else:
                st.error("กรุณากรอกชื่ออาหารและราคา(ธรรมดา)")

        st.header(
            f"รายการอาหารของร้าน {st.session_state.selected_store} ({st.session_state.selected_canteen})"
        )
        if "food_items" in canteen_data[canteen_index]["stores"][store_index]:
            for i, item in enumerate(
                canteen_data[canteen_index]["stores"][store_index]["food_items"]
            ):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    prices_text = f"{item['prices']['normal']:.2f} บาท"
                    if "special" in item["prices"]:
                        prices_text += f" (พิเศษ: {item['prices']['special']:.2f} บาท)"
                    st.write(f"{i+1}. {item['name']} - {prices_text}")
                with col2:
                    if st.button(f"แก้ไข", key=f"edit_food_{i}"):
                        st.session_state.editing_food_index = i
                        st.session_state.food_name = item["name"]
                        st.session_state.normal_price = item["prices"]["normal"]
                        st.session_state.special_price = item["prices"].get("special")
                        st.rerun()
                with col3:
                    if st.button(f"ลบ", key=f"delete_food_{i}"):
                        canteen_data[canteen_index]["stores"][store_index][
                            "food_items"
                        ].pop(i)
                        save_canteen_data(canteen_data)
                        st.session_state.editing_food_index = None
                        st.rerun()
else:
    st.info("กรุณาเลือกโรงอาหารก่อน")