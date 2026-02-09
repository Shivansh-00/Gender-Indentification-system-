import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from datetime import datetime

# --- CONFIG & STYLES ---
st.set_page_config(page_title="Gender Attendance", layout="wide", initial_sidebar_state="collapsed")

def local_css():
    st.markdown("""
    <style>
        /* Main Background */
        .stApp {
            background: linear-gradient(135deg, #1e1e2f 0%, #2d3436 100%);
        }

        /* Glassmorphism Card Effect */
        div[data-testid="stVerticalBlock"] > div:has(div.glass-card) {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        /* Big Animated Buttons */
        .stButton > button {
            width: 100%;
            height: 60px;
            border-radius: 12px;
            border: none;
            background: linear-gradient(45deg, #6c5ce7, #a29bfe);
            color: white;
            font-weight: bold;
            font-size: 18px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }

        .stButton > button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(108, 92, 231, 0.4);
            background: linear-gradient(45deg, #a29bfe, #6c5ce7);
            border: none;
            color: white;
        }

        /* Top Right Navigation Bar */
        .nav-container {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 999;
            display: flex;
            gap: 10px;
        }

        /* Metric Styling */
        [data-testid="stMetricValue"] {
            font-size: 40px;
            color: #00cec9;
        }
        
        /* Input Field Styling */
        .stTextInput>div>div>input {
            background: rgba(255,255,255,0.05);
            color: white;
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- INITIALIZATION ---
for key in ['main_folders', 'events', 'current_user', 'page', 'current_event', 'current_folder', 'subpage']:
    if key not in st.session_state:
        if key in ['main_folders', 'events']: st.session_state[key] = {}
        else: st.session_state[key] = None
if st.session_state.page is None: st.session_state.page = "login"

# --- UI COMPONENTS ---
def top_nav():
    """Fixed top-right navigation"""
    cols = st.columns([8, 1, 1])
    with cols[1]:
        if st.button("🏠", help="Go Home"):
            st.session_state.page = "home"
            st.rerun()
    with cols[2]:
        if st.button("⬅️", help="Back"):
            # Simple logic to determine 'back'
            if st.session_state.page in ["create_event", "events_list", "create_folder", "main_folders_list"]:
                st.session_state.page = "home"
            elif st.session_state.page == "event_dashboard":
                st.session_state.page = "events_list"
            st.rerun()

def glass_container_start():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

# --- PAGES ---
def login():
    st.markdown("<h1 style='text-align: center; color: white;'>🔐 System Access</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        glass_container_start()
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Sign In"):
            if username == "host" and password == "123":
                st.session_state.current_user = username
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("❌ Invalid Credentials")

def home():
    top_nav()
    st.markdown(f"<h1 style='color: white;'>Welcome, {st.session_state.current_user}! ✨</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        glass_container_start()
        st.markdown("### 🎫 Events")
        if st.button("➕ Create New Event"):
            st.session_state.page = "create_event"; st.rerun()
        if st.button("📂 View All Events"):
            st.session_state.page = "events_list"; st.rerun()
            
    with col2:
        glass_container_start()
        st.markdown("### 📁 Management")
        if st.button("📁 New Main Folder"):
            st.session_state.page = "create_folder"; st.rerun()
        if st.button("📋 Main Folders List"):
            st.session_state.page = "main_folders_list"; st.rerun()

def event_dashboard():
    top_nav()
    event = st.session_state.events[st.session_state.current_event]
    st.markdown(f"<h2 style='color: white;'>📊 {event['name']}</h2>", unsafe_allow_html=True)
    
    # Sub-navigation inside dashboard
    tabs = st.tabs(["📸 Attendance", "📈 Analytics", "🗄️ Database", "⚙️ Setup"])
    
    with tabs[0]:
        attendance_page(event)
    with tabs[1]:
        dashboard_page(event)
    with tabs[2]:
        database_page(event)
    with tabs[3]:
        hall_page(event)

# --- LOGIC HELPERS ---
def simple_gender_detection(image):
    # Simulating API logic
    res = np.random.choice(["Male", "Female", "Non-Binary"], p=[0.45, 0.45, 0.1])
    return res, np.random.randint(85, 99)

def attendance_page(event):
    col1, col2 = st.columns([2, 1])
    with col1:
        img_file = st.camera_input("Scanner")
        if img_file:
            gender, conf = simple_gender_detection(img_file)
            st.session_state.last_capture = {"gender": gender, "conf": conf}
            
    with col2:
        if 'last_capture' in st.session_state:
            res = st.session_state.last_capture
            st.metric("Detected Gender", res['gender'], f"{res['conf']}% Match")
            name = st.text_input("Participant Name")
            if st.button("✅ Confirm Registration"):
                event["data"].append({
                    "sl_no": len(event["data"])+1, 
                    "gender": res['gender'], 
                    "name": name,
                    "time": datetime.now().strftime("%H:%M")
                })
                st.success(f"Registered {name}!")

def dashboard_page(event):
    if not event["data"]:
        st.info("No data yet.")
        return
    df = pd.DataFrame(event["data"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df))
    c2.metric("Female", len(df[df['gender']=='Female']))
    c3.metric("Male", len(df[df['gender']=='Male']))
    st.bar_chart(df['gender'].value_counts())

def create_event():
    top_nav()
    st.header("New Event")
    with st.container():
        name = st.text_input("Event Name")
        date = st.date_input("Date")
        if st.button("Create"):
            eid = f"{name}_{date}"
            st.session_state.events[eid] = {"name": name, "date": str(date), "data": [], "hall_rows": 5, "hall_cols": 10}
            st.session_state.page = "home"; st.rerun()

def events_list():
    top_nav()
    st.header("Your Events")
    for eid, ev in st.session_state.events.items():
        if st.button(f"Open {ev['name']} - {len(ev['data'])} attendees", key=eid):
            st.session_state.current_event = eid
            st.session_state.page = "event_dashboard"
            st.rerun()

# --- ROUTER ---
pages = {
    "login": login,
    "home": home,
    "create_event": create_event,
    "events_list": events_list,
    "event_dashboard": event_dashboard
}

if st.session_state.page in pages:
    pages[st.session_state.page]()
else:
    # Fallback for missing pages (create_folder, etc)
    st.write(f"Page {st.session_state.page} under construction")
    if st.button("Back Home"):
        st.session_state.page = "home"
        st.rerun()