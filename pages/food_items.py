import streamlit as st
import pymongo
from pymongo.server_api import ServerApi
import hmac
from bson.objectid import ObjectId

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

@st.cache_resource()
def database_init():
    return pymongo.MongoClient(st.secrets["mongo_uri"], server_api=ServerApi("1"))

mongo = database_init()

if not mongo:
    st.error("Cannot Access Data Storage")
    st.stop()

st.title("🍲 ข้อมูลรายการอาหาร")

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

def update_store(store_id, updated_store):
    store_collection.update_one({"_id": ObjectId(store_id)}, {"$set": updated_store})

# --- Load and Extract Data ---
canteens = load_canteens()
stores = load_stores()

# --- Session State Initialization ---
if "selected_canteen_id" not in st.session_state:
    st.session_state.selected_canteen_id = None
if "selected_store_id" not in st.session_state:
    st.session_state.selected_store_id = None
if "food_item_name" not in st.session_state:
    st.session_state.food_item_name = ""
if "food_item_price" not in st.session_state:
    st.session_state.food_item_price = 0.0
if "food_item_category" not in st.session_state:
    st.session_state.food_item_category = "food"
if "food_item_sub_category" not in st.session_state:
    st.session_state.food_item_sub_category = ""
if "editing_item_index" not in st.session_state:
    st.session_state.editing_item_index = None

# --- Dropdowns to Select Canteen and Store ---
canteen_options = {str(c["_id"]): c["name"] for c in canteens}
st.session_state.selected_canteen_id = st.selectbox(
    "เลือกโรงอาหาร",
    options=canteen_options.keys(),
    index=list(canteen_options.keys()).index(st.session_state.selected_canteen_id) if st.session_state.selected_canteen_id in canteen_options else 0,
    format_func=lambda x: canteen_options[x],
    key="canteen_select"
)

if st.session_state.selected_canteen_id:
    store_options = {str(s["_id"]): s["name"] for s in stores if str(s["canteenId"]) == st.session_state.selected_canteen_id}
    st.session_state.selected_store_id = st.selectbox(
        "เลือกร้านค้า",
        options=store_options.keys(),
        index=list(store_options.keys()).index(st.session_state.selected_store_id) if st.session_state.selected_store_id in store_options else 0,
        format_func=lambda x: store_options[x],
        key="store_select"
    )

# --- Input Form for Food Item ---
if st.session_state.selected_store_id:
    st.header("เพิ่ม/แก้ไขรายการอาหาร")

    # --- Sub Category Mapping ---
    sub_category_mapping = {
        "food": {
            "ก๋วยเตี๋ยว เกาเหลา": "noodles",
            "ต้ม แกง": "soup_curry",
            "ข้าวมันไก่": "chicken_rice",
            "ข้าวราดแกง/ข้าวต่าง ๆ": "rice_curry",
            "ส้มตำ อาหารอีสาน": "somtum_northeastern",
            "สเต็ก": "steak",
            "อาหารญี่ปุ่น": "japanese",
            "อื่น ๆ": "others",
        },
        "DRINK": {
            "น้ำหวาน": "sweetened",
            "น้ำผลไม้/น้ำปั่น": "juice_smoothie",
            "ชา กาแฟ": "tea_coffee",
            "อื่น ๆ": "others",
        },
    }

    # --- Load Existing Data if Editing ---
    if st.session_state.editing_item_index is not None:
        selected_store = next((s for s in stores if str(s["_id"]) == st.session_state.selected_store_id), None)
        if selected_store and "menu" in selected_store:
            editing_item = selected_store["menu"][st.session_state.editing_item_index]
            st.session_state.food_item_name = editing_item["name"]
            st.session_state.food_item_price = editing_item["price"]
            st.session_state.food_item_category = editing_item["category"]

            # Reverse lookup for display
            if st.session_state.food_item_category in sub_category_mapping:
                reverse_mapping = {v: k for k, v in sub_category_mapping[st.session_state.food_item_category].items()}
                st.session_state.food_item_sub_category = reverse_mapping.get(editing_item.get("sub_category", ""), "")
            else:
                st.session_state.food_item_sub_category = ""

    else:
        st.session_state.food_item_name = ""
        st.session_state.food_item_price = 0.0
        st.session_state.food_item_category = "food"
        st.session_state.food_item_sub_category = ""

    # --- Input Fields ---
    st.session_state.food_item_name = st.text_input("ชื่ออาหาร", value=st.session_state.food_item_name)
    st.session_state.food_item_price = st.number_input("ราคา", min_value=0.0, format="%.2f", value=st.session_state.food_item_price)
    st.session_state.food_item_category = st.selectbox(
        "หมวดหมู่",
        options=["food", "DRINK"],
        index=["food", "DRINK"].index(st.session_state.food_item_category),
        format_func=lambda x: {
            "food": "อาหาร",
            "DRINK": "เครื่องดื่ม",
        }.get(x, x)
    )

    # --- Sub Category Selection ---
    if st.session_state.food_item_category in sub_category_mapping:
        st.session_state.food_item_sub_category = st.selectbox(
            "หมวดหมู่ย่อย",
            options=sub_category_mapping[st.session_state.food_item_category].keys(),
            index=list(sub_category_mapping[st.session_state.food_item_category].keys()).index(st.session_state.food_item_sub_category) if st.session_state.food_item_sub_category in sub_category_mapping[st.session_state.food_item_category] else 0,
        )
    else:
        st.session_state.food_item_sub_category = ""

    # --- Edit/Add Button ---
    if st.session_state.editing_item_index is not None:
        button_label = "แก้ไขรายการอาหาร"
    else:
        button_label = "เพิ่มรายการอาหาร"

    if st.button(button_label):
        if not st.session_state.food_item_name or st.session_state.food_item_price == 0.0:
            st.error("กรุณากรอกชื่ออาหารและราคา")
        else:
            # Translate sub_category to English for database storage
            translated_sub_category = sub_category_mapping[st.session_state.food_item_category].get(st.session_state.food_item_sub_category, "")

            new_food_item = {
                "name": st.session_state.food_item_name,
                "price": st.session_state.food_item_price,
                "category": st.session_state.food_item_category,
                "sub_category": translated_sub_category,
            }

            # Find the selected store and update its menu
            selected_store = store_collection.find_one({"_id": ObjectId(st.session_state.selected_store_id)})
            if selected_store:
                if "menu" not in selected_store:
                    selected_store["menu"] = []

                if st.session_state.editing_item_index is not None:
                    # Update the existing item
                    selected_store["menu"][st.session_state.editing_item_index] = new_food_item
                    st.session_state.editing_item_index = None  # Reset editing mode
                else:
                    # Append the new food item to the menu
                    selected_store["menu"].append(new_food_item)

                # Update the store in the database
                update_store(st.session_state.selected_store_id, selected_store)

                if st.session_state.editing_item_index is None:
                    st.success(f"เพิ่มรายการอาหาร '{st.session_state.food_item_name}' เรียบร้อยแล้ว")
                else:
                    st.success(f"แก้ไขรายการอาหาร '{st.session_state.food_item_name}' เรียบร้อยแล้ว")

                # Reset input values
                st.session_state.food_item_name = ""
                st.session_state.food_item_price = 0.0
                st.session_state.food_item_category = "food"
                st.session_state.food_item_sub_category = ""
                st.rerun()

    # --- Display Existing Menu Items ---
    st.header("รายการอาหารที่มีอยู่")
    selected_store = next((s for s in stores if str(s["_id"]) == st.session_state.selected_store_id), None)
    if selected_store and "menu" in selected_store:
        for i, item in enumerate(selected_store["menu"]):
            st.write(f"**ชื่อ:** {item['name']}")
            st.write(f"**ราคา:** {item['price']:.2f} บาท")
            st.write(f"**หมวดหมู่:** {item['category']}")

            # Display sub_category in Thai using reverse lookup
            if item["category"] in sub_category_mapping:
                reverse_mapping = {v: k for k, v in sub_category_mapping[item["category"]].items()}
                display_sub_category = reverse_mapping.get(item.get("sub_category", ""), "-")
            else:
                display_sub_category = "-"

            st.write(f"**หมวดหมู่ย่อย:** {display_sub_category}")

            col1, col2, col3 = st.columns([1, 1, 5])

            if col1.button("ลบ", key=f"delete_item_{i}"):
                # Remove the item from the menu
                selected_store["menu"].pop(i)

                # Update the store in the database
                update_store(st.session_state.selected_store_id, selected_store)
                st.rerun()

            if col2.button("แก้ไข", key=f"edit_item_{i}"):
                # Set the item index to be edited and populate form fields
                st.session_state.editing_item_index = i
                st.rerun()

            st.markdown("---")  # Add a separator between items
    else:
        st.write("ยังไม่มีรายการอาหารสำหรับร้านค้านี้")
