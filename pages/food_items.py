import streamlit as st
import pymongo
from pymongo.server_api import ServerApi
import datetime
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
if "food_item_description" not in st.session_state:
    st.session_state.food_item_description = ""
if "food_item_price" not in st.session_state:
    st.session_state.food_item_price = 0.0
if "food_item_category" not in st.session_state:
    st.session_state.food_item_category = "MAIN"

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
    st.header("เพิ่มรายการอาหาร")

    st.session_state.food_item_name = st.text_input("ชื่ออาหาร", value=st.session_state.food_item_name)
    st.session_state.food_item_description = st.text_area("คำอธิบาย (Optional)", value=st.session_state.food_item_description)
    st.session_state.food_item_price = st.number_input("ราคา", min_value=0.0, format="%.2f", value=st.session_state.food_item_price)
    st.session_state.food_item_category = st.selectbox(
        "หมวดหมู่",
        options=["MAIN", "SIDE", "DRINK", "VEGETARIAN"],
        index=["MAIN", "SIDE", "DRINK", "VEGETARIAN"].index(st.session_state.food_item_category),
        format_func=lambda x: {
            "MAIN": "อาหารจานหลัก",
            "SIDE": "กับข้าว",
            "DRINK": "เครื่องดื่ม",
            "VEGETARIAN": "มังสวิรัติ"
        }.get(x, x)
    )

    if st.button("เพิ่มรายการอาหาร"):
        if not st.session_state.food_item_name or st.session_state.food_item_price == 0.0:
            st.error("กรุณากรอกชื่ออาหารและราคา")
        else:
            new_food_item = {
                "name": st.session_state.food_item_name,
                "description": st.session_state.food_item_description,
                "price": st.session_state.food_item_price,
                "category": st.session_state.food_item_category,
            }

            # Find the selected store and update its menu
            selected_store = store_collection.find_one({"_id": ObjectId(st.session_state.selected_store_id)})
            if selected_store:
                if "menu" not in selected_store:
                    selected_store["menu"] = []

                # Append the new food item to the menu
                selected_store["menu"].append(new_food_item)
                
                # Update the store in the database
                update_store(st.session_state.selected_store_id, selected_store)

                st.success(f"เพิ่มรายการอาหาร '{st.session_state.food_item_name}' เรียบร้อยแล้ว")

                # Reset input values
                st.session_state.food_item_name = ""
                st.session_state.food_item_description = ""
                st.session_state.food_item_price = 0.0
                st.session_state.food_item_category = "MAIN"
                st.rerun()

    # --- Display Existing Menu Items ---
    st.header("รายการอาหารที่มีอยู่")
    selected_store = next((s for s in stores if str(s["_id"]) == st.session_state.selected_store_id), None)
    if selected_store and "menu" in selected_store:
        for i, item in enumerate(selected_store["menu"]):
            st.write(f"**ชื่อ:** {item['name']}")
            if item["description"]:
                st.write(f"**คำอธิบาย:** {item['description']}")
            st.write(f"**ราคา:** {item['price']:.2f} บาท")
            st.write(f"**หมวดหมู่:** {item['category']}")

            col1, col2 = st.columns([1, 5])
            
            if col1.button("ลบ", key=f"delete_item_{i}"):
                # Remove the item from the menu
                selected_store["menu"].pop(i)
                
                # Update the store in the database
                update_store(st.session_state.selected_store_id, selected_store)
                st.rerun()
            
            st.markdown("---")  # Add a separator between items
    else:
        st.write("ยังไม่มีรายการอาหารสำหรับร้านค้านี้")