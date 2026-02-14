import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from datetime import datetime
from datetime import datetime
import time
import random
import string
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None
    print("Warning: FPDF not found. Install 'fpdf' for PDF reports.")
import plotly.express as px
import plotly.graph_objects as go
import cv2

# Custom Modules
try:
    from face_engine import FaceEngine, draw_results
    from utils import SeatingManager, TeamManager
except ImportError as e:
    st.error(f"Missing modules: {e}")
    st.stop()

# --- STATE INITIALIZATION ---
if 'face_engine' not in st.session_state: st.session_state.face_engine = FaceEngine()
if 'main_folders' not in st.session_state: st.session_state.main_folders = {} # {folder_name: {date, events: []}}
if 'events' not in st.session_state: st.session_state.events = {} 
# Event structure: {id: {name, date, password, hall_rows, hall_cols, data: []}}
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'page' not in st.session_state: st.session_state.page = "login"
if 'current_event' not in st.session_state: st.session_state.current_event = None
if 'subpage' not in st.session_state: st.session_state.subpage = None
if 'auth_stage' not in st.session_state: st.session_state.auth_stage = 0 # 0: Login, 1: 2FA, 2: Access
if 'verification_code' not in st.session_state: st.session_state.verification_code = None
if 'upload_key' not in st.session_state: st.session_state.upload_key = 0

st.set_page_config(page_title="Gender Attendance AI", layout="wide")

# --- CSS STYLES ---
def local_css():
    st.markdown("""
    <style>
        /* IMPORT FONTS */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Outfit:wght@400;700&display=swap');
        
        /* GLOBAL THEME & ANIMATED BACKGROUND */
        :root {
            --primary: #7F5AF0;
            --secondary: #2CB67D;
            --accent: #FF8906;
            --bg-dark: #16161A;
            --bg-card: rgba(255, 255, 255, 0.05);
            --text-light: #FFFFFE;
            --glass-border: rgba(255, 255, 255, 0.1);
        }
        
        body {
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(at 0% 0%, rgba(127, 90, 240, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(44, 182, 125, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(255, 137, 6, 0.1) 0px, transparent 50%);
            background-attachment: fixed;
            color: var(--text-light);
            font-family: 'Outfit', sans-serif;
        }
        
        /* CUSTOM SCROLLBAR */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: transparent; 
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(127, 90, 240, 0.3); 
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(127, 90, 240, 0.6); 
        }

        /* HEADERS */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif;
            font-weight: 800 !important;
            letter-spacing: -0.02em;
            background: -webkit-linear-gradient(0deg, #FFFFFE, #94A1B2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem !important;
        }

        /* GLOSSY CARDS */
        .card, [data-testid="stMetric"], [data-testid="stExpander"], div.stDataFrame, div[data-testid="stForm"], div[data-testid="stSidebar"] {
            background: var(--bg-card) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: 20px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover, [data-testid="stMetric"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px 0 rgba(127, 90, 240, 0.2) !important;
            border-color: rgba(127, 90, 240, 0.3) !important;
        }

        /* METRIC CARDS SPECIFICS */
        [data-testid="stMetric"] {
            padding: 1.5rem;
            text-align: center;
        }
        [data-testid="stMetricLabel"] { font-size: 0.9rem; color: #94A1B2 !important; letter-spacing: 0.05em; text-transform: uppercase; }
        [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700; color: var(--text-light) !important; text-shadow: 0 0 20px rgba(127,90,240,0.5); }

        /* BUTTONS - GLOSSY & ANIMATED */
        div.stButton > button {
            background: linear-gradient(135deg, rgba(127, 90, 240, 0.8), rgba(44, 182, 125, 0.8)) !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            border-radius: 12px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            letter-spacing: 0.03em !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.3) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative;
            overflow: hidden;
            width: 100%;
        }
        
        div.stButton > button::before {
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: 0.5s;
        }
        
        div.stButton > button:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 25px rgba(127, 90, 240, 0.4), inset 0 1px 0 rgba(255,255,255,0.4) !important;
            border-color: rgba(255,255,255,0.5) !important;
        }
        
        div.stButton > button:hover::before {
            left: 100%;
        }
        
        div.stButton > button:active {
            transform: scale(0.98);
        }

        /* INPUT FIELDS */
        .stTextInput > div > div > input, .stDateInput > div > div > input, .stSelectbox > div > div > div {
            background-color: rgba(0,0,0,0.2) !important;
            color: white !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: 10px !important;
            padding: 0.5rem 1rem !important;
        }
        .stTextInput > div > div > input:focus, .stDateInput > div > div > input:focus {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 2px rgba(127, 90, 240, 0.2) !important;
        }

        /* CUSTOM ANIMATIONS */
        @keyframes subtleFloat {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0px); }
        }
        
        /* APPLY ANIMATION TO MAIN LOGO/HEADER IF DESIRED */
        h1 { animation: subtleFloat 4s ease-in-out infinite; }
        
        /* CAMERA INPUT */
        div[data-testid="stCameraInput"] {
            border: 2px solid var(--glass-border);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        /* LOGIN PAGE STYLES */
        .login-title {
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 3.5rem;
            color: #ffffff;
            text-align: center;
            margin-bottom: 0.2rem;
            letter-spacing: -0.05em;
            text-shadow: 0 0 10px rgba(0, 255, 0, 0.6), 0 0 20px rgba(0, 255, 0, 0.4), 0 0 40px rgba(0, 255, 0, 0.2);
            animation: glow 2s ease-in-out infinite alternate;
        }
        
        .login-subtitle {
            font-family: 'Inter', sans-serif;
            font-weight: 300;
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.7);
            text-align: center;
            font-style: italic;
            margin-bottom: 2rem;
            letter-spacing: 0.05em;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 10px rgba(44, 182, 125, 0.6), 0 0 20px rgba(44, 182, 125, 0.4); }
            to { text-shadow: 0 0 20px rgba(44, 182, 125, 1), 0 0 30px rgba(44, 182, 125, 0.6); }
        }
        
        /* STARRY BACKGROUND - FIX */
        #stars-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1; /* Bring forward to be visible */
            overflow: hidden;
            pointer-events: none; /* Let clicks pass through */
            background: transparent; /* Let the gradient mesh show through */
        }
        
        /* Ensure content sits above stars */
        .stApp > header, .stApp > div:nth-child(1) {
            z-index: 2;
            position: relative;
        }
        
        .star {
            position: absolute;
            background: white;
            border-radius: 50%;
            opacity: 0;
            animation: twinkle 5s infinite;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
        }
        
        @keyframes twinkle {
            0% { opacity: 0; transform: translateY(0) scale(0.5); }
            50% { opacity: 1; transform: translateY(-20px) scale(1.2); }
            100% { opacity: 0; transform: translateY(-40px) scale(0.5); }
        }
    </style>
    """, unsafe_allow_html=True)

local_css()

def draw_faces(image_pil, faces, current_idx):
    img_cv = np.array(image_pil)
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
    
    for idx, face in enumerate(faces):
        top, right, bottom, left = face['bbox']
        
        # Highlight current face
        if idx == current_idx:
            color = (0, 255, 0) # Green for current
            thickness = 3
            label = f"P{idx+1} (Current)"
        else:
            color = (255, 0, 0) # Red for others
            thickness = 2
            if idx < current_idx:
                label = f"P{idx+1} (Done)"
                color = (200, 200, 200) # Gray for done
            else:
                label = f"P{idx+1}"
        
        cv2.rectangle(img_cv, (left, top), (right, bottom), color, thickness)
        cv2.putText(img_cv, f"{label} - {face['gender']}", (left, top - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
    return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

# --- HELPER FUNCTIONS ---
def generate_code():
    return ''.join(random.choices(string.digits, k=6))

def render_header():
    if st.session_state.page == "login": return
    
    col1, col2, col3 = st.columns([8, 1, 1])
    with col1: st.write("")
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.current_event = None
            st.session_state.subpage = None
            st.rerun()
    with col3:
        if st.button("⬅️ Back", use_container_width=True):
            # Back Logic based on hierarchy
            if st.session_state.subpage:
                st.session_state.subpage = None
            elif st.session_state.page == "event_menu":
                st.session_state.page = "events_list"
            elif st.session_state.page in ["events_list", "create_event", "create_folder", "view_folders", "batch_upload"]:
                st.session_state.page = "home"
            st.rerun()

# --- PAGES ---

def login_page():
    # Starry Background Injection
    st.markdown("""
    <div id="stars-container">
        """ + "".join([f'<div class="star" style="top: {random.randint(0,100)}%; left: {random.randint(0,100)}%; width: {random.randint(1,3)}px; height: {random.randint(1,3)}px; animation-duration: {random.randint(3,8)}s; animation-delay: {random.uniform(0,5)}s;"></div>' for _ in range(100)]) + """
    </div>
    """, unsafe_allow_html=True)
    
    render_header()
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-title">EquiVision</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Vision Beyond Bias. Seeking Equality. Shaping Fairness</div>', unsafe_allow_html=True)
        
        if st.session_state.auth_stage == 0:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Sign In", type="primary", use_container_width=True):
                if username == "host" and password == "123":
                    st.session_state.current_user = username
                    st.success("✅ Signed In!")
                    st.session_state.page = "home"
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Invalid Credentials (Try: host / 123)")

def home_page():
    render_header()
    # Time & Greeting
    now = datetime.now()
    hour = now.hour
    greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"
    
    st.markdown(f"# {greeting}, {st.session_state.current_user}! 👋")
    st.write(f"🕒 **{now.strftime('%I:%M %p | %d %B %Y')}**")
    st.markdown("### What do you want to do today?")
    
    # 4 Main Options
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Create New Event", use_container_width=True, type="primary"):
            st.session_state.page = "create_event"
            st.rerun()
        if st.button("📂 Work with Existing Events", use_container_width=True):
            st.session_state.page = "events_list"
            st.rerun()
            
    with col2:
        if st.button("📁 Create a New Main Event Folder", use_container_width=True):
            st.session_state.page = "create_folder"
            st.rerun()
        if st.button("📋 Check Existing Main Event Folders", use_container_width=True):
            st.session_state.page = "view_folders"
            st.rerun()

def create_event():
    render_header()
    st.header("➕ Create New Event")
    with st.form("create_evt_form"):
        name = st.text_input("Name of Event")
        date = st.date_input("Event Date")
        password = st.text_input("Create Event Password", type="password")
        
        if st.form_submit_button("Create Event"):
            if name and password:
                eid = f"{name}_{date}".replace(" ", "_")
                st.session_state.events[eid] = {
                    "name": name,
                    "date": str(date),
                    "password": password,
                    "hall_rows": 5, # Default, can edit later
                    "hall_cols": 10,
                    "cluster_size": 1, 
                    "data": [],
                    "roles": {}, # {role_name: {count: 1, reqs: {skill: weight}}}
                    "team_members": [] # [{id, name, gender, skills: {skill: level}}]
                }
                st.success(f"✅ Event '{name}' Created!")
                st.session_state.page = "events_list"
                time.sleep(1)
                st.rerun()
            else:
                st.error("Name and Password are required.")

def events_list():
    render_header()
    st.header("📂 Select an Event")
    
    if not st.session_state.events:
        st.info("No events found. Go back and create one!")
        return
        
    for eid, evt in st.session_state.events.items():
        col1, col2 = st.columns([3, 1])
        col1.write(f"### {evt['name']}")
        col1.caption(f"📅 {evt['date']} | 👥 {len(evt['data'])} Participants")
        
        if col2.button("Select", key=f"sel_{eid}", use_container_width=True):
            st.session_state.current_event = eid
            st.session_state.page = "event_menu"
            st.rerun()
        st.markdown("---")

def event_menu():
    render_header()
    eid = st.session_state.current_event
    evt = st.session_state.events[eid]
    
    st.header(f"🖥️ {evt['name']}")
    st.caption(f"Event Dashboard | Date: {evt['date']}")
    
    # 3.1 Options as Grid
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    
    with c1:
        st.info("📸 Start Session")
        if st.button("Start Taking Attendance", use_container_width=True):
            st.session_state.subpage = "attendance_setup"
            st.rerun()
    with c2:
        st.info("📋 Records")
        if st.button("View Database", use_container_width=True):
            st.session_state.subpage = "database"
            st.rerun()
    with c3:
        st.info("📊 Analytics")
        if st.button("View Dashboard", use_container_width=True):
            st.session_state.subpage = "dashboard"
            st.rerun()
            
    with c4:
        st.info("⚙️ Hall Setup")
        if st.button("Select Hall Dimensions", use_container_width=True):
            st.session_state.subpage = "hall_dims"
            st.rerun()
    with c5:
        st.info("👥 Teams")
        if st.button("Analyze Team Creation", use_container_width=True):
            st.session_state.subpage = "team_analysis"
            st.rerun()
    with c6:
        st.info("� Team Roles")
        if st.button("Manage Team & Roles", use_container_width=True):
            st.session_state.subpage = "team_management"
            st.rerun()

    c7, c8, c9 = st.columns(3)
    with c7:
        st.info("📂 Batch Import")
        if st.button("Upload Multiple Pictures", use_container_width=True):
            st.session_state.subpage = "batch_upload"
            st.rerun()

    st.markdown("---")
    
    # Render Subpages
    if st.session_state.subpage == "attendance_setup": attendance_setup(evt)
    elif st.session_state.subpage == "attendance_active": attendance_active(evt) # The actual scanning page
    elif st.session_state.subpage == "database": database_view(evt)
    elif st.session_state.subpage == "dashboard": dashboard_view(evt)
    elif st.session_state.subpage == "hall_dims": hall_dims(evt)
    elif st.session_state.subpage == "team_analysis": team_analysis(evt)
    elif st.session_state.subpage == "team_management": team_management(evt)
    elif st.session_state.subpage == "team_management": team_management(evt)
    elif st.session_state.subpage == "batch_upload": batch_upload_page(evt)

def attendance_setup(evt):
    st.subheader("🏁 Start Attendance Session")
    mode = st.selectbox("Select Mode", ["Normal (Full Data)", "Privacy (No Personal Data)"])
    if st.button("Start Session", type="primary"):
        st.session_state.temp_mode = mode
        st.session_state.subpage = "attendance_active"
        st.rerun()

def attendance_active(evt):
    mode = st.session_state.get('temp_mode', 'Normal')
    st.subheader(f"📸 Live Session ({mode})")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown("### 📡 Input Feed")
        
        # Input Method Toggle
        input_method = st.radio("Select Input Method", ["Camera", "Upload Image"], horizontal=True, label_visibility="collapsed")
        
        img_buffer = None
        if input_method == "Camera":
            img_buffer = st.camera_input("Take photo", label_visibility="collapsed")
        else:
            img_buffer = st.file_uploader("Upload Image (JPG/PNG)", type=['jpg', 'jpeg', 'png'], key=f"uploader_{st.session_state.upload_key}")
        
        # State Management for Multi-Person
        if 'last_photo_hash' not in st.session_state: st.session_state.last_photo_hash = None
        if 'detected_faces' not in st.session_state: st.session_state.detected_faces = []
        if 'current_face_idx' not in st.session_state: st.session_state.current_face_idx = 0
        
        if img_buffer:
            bytes_data = img_buffer.getvalue()
            if st.session_state.last_photo_hash != bytes_data:
                st.session_state.last_photo_hash = bytes_data
                
                with st.spinner("🔍 Detecting faces..."):
                    image = Image.open(img_buffer)
                    # Use the face engine
                    detection_backend = "ssd" # Default
                    faces = st.session_state.face_engine.process_image(image, detector_backend=detection_backend)
                    st.session_state.detected_faces = faces
                    st.session_state.current_face_idx = 0
            
            faces = st.session_state.detected_faces
            current_idx = st.session_state.current_face_idx
            original_image = Image.open(img_buffer)
            
            if not faces:
                st.warning("⚠️ No faces detected! Try again.")
                st.image(original_image, use_container_width=True)
            elif current_idx >= len(faces):
                st.success("✅ All faces processed for this photo!")
                st.image(draw_faces(original_image, faces, -1), use_container_width=True)
                if st.button("📸 Catch Next Batch", use_container_width=True):
                    st.session_state.last_photo_hash = None
                    st.session_state.detected_faces = []
                    # Increment upload key to clear uploader if in use
                    if input_method == "Upload Image":
                        st.session_state.upload_key += 1
                    st.rerun()
            else:
                display_img = draw_faces(original_image, faces, current_idx)
                st.image(display_img, use_container_width=True)
                
    with col2:
        if img_buffer and st.session_state.detected_faces and st.session_state.current_face_idx < len(st.session_state.detected_faces):
            faces = st.session_state.detected_faces
            idx = st.session_state.current_face_idx
            face = faces[idx]
            
            # Crop Face
            top, right, bottom, left = face['bbox']
            # Expand crop slightly
            h, w = original_image.height, original_image.width
            top = max(0, top - 20); left = max(0, left - 20)
            bottom = min(h, bottom + 20); right = min(w, right + 20)
            face_crop = original_image.crop((left, top, right, bottom))
            
            st.markdown(f"""
            <div class="card" style="text-align: center; margin-bottom: 20px;">
                <h3 style="margin:0;">📝 Person {idx + 1}/{len(faces)}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            c_img, c_info = st.columns([1, 2])
            with c_img: st.image(face_crop, width=100)
            with c_info:
                st.metric("Gender", face['gender'])
                st.metric("Confidence", f"{face['confidence']:.1f}%" if isinstance(face['confidence'], (int, float)) else "N/A")

            # Seat Allocation
            cluster = evt.get('cluster_size', 1)
            seat_mgr = SeatingManager(evt['hall_rows'], evt['hall_cols'], cluster_size=cluster)
            # Use a temporary list including current session additions if needed, but for now just evt['data']
            allocated_seat = seat_mgr.allocate_seat(evt['data'], face['gender'])
            
            # DUPLICATE CHECK
            is_duplicate = False
            matched_name = ""
            
            new_encoding = np.array(face['encoding'])
            known_encs = st.session_state.face_engine.known_encodings
            known_ids = st.session_state.face_engine.known_ids
            current_evt_id = st.session_state.current_event
            
            if len(known_encs) > 0:
                event_indices = [idx for idx, meta in enumerate(known_ids) if meta['event_id'] == current_evt_id]
                if event_indices:
                    event_encs = [known_encs[idx] for idx in event_indices]
                    distances = np.linalg.norm(event_encs - new_encoding, axis=1)
                    min_dist_idx = np.argmin(distances)
                    if distances[min_dist_idx] < 0.5:
                        is_duplicate = True
                        original_idx = event_indices[min_dist_idx]
                        matched_name = known_ids[original_idx]['name']

            if is_duplicate:
                st.warning(f"⚠️ **Already Registered Person:** {matched_name}")
                st.info("Skipping to next person...")
                if st.button("⏭️ Next Person", use_container_width=True, key=f"skip_{idx}"):
                    st.session_state.current_face_idx += 1
                    st.rerun()
            else:
                st.info(f"📍 Seat: **{allocated_seat}**")
                
                # Registration Form
                with st.form(key=f"reg_form_{idx}"):
                    if "Privacy" in mode:
                        st.caption("🔒 Privacy Mode: Name hidden")
                        name = f"Anon_{generate_code()}"
                        pid = "N/A"; branch = "N/A"; age = 0
                    else:
                        name = st.text_input("Name", key=f"name_{idx}")
                        pid = st.text_input("ID", key=f"id_{idx}")
                        c_b, c_a = st.columns(2)
                        branch = c_b.text_input("Branch", key=f"br_{idx}")
                        age = c_a.number_input("Age", 16, 60, 18, key=f"ag_{idx}")
                    
                    if st.form_submit_button("✅ Register & Next", use_container_width=True, type="primary"):
                        if name:
                            # Save Data
                            record = {
                                "sl_no": len(evt['data'])+1,
                                "gender": face['gender'],
                                "seat": allocated_seat,
                                "name": name,
                                "id": pid,
                                "branch": branch,
                                "age": age,
                                "encoding": face['encoding'], # Store encoding
                                "timestamp": str(datetime.now())
                            }
                            evt['data'].append(record)
                            
                            # Add to known faces logic from previous code
                            if "Privacy" not in mode:
                                st.session_state.face_engine.known_encodings.append(np.array(face['encoding']))
                                st.session_state.face_engine.known_ids.append({'name': name, 'event_id': st.session_state.current_event})

                            st.success(f"✅ Saved {name}!")
                            st.session_state.current_face_idx += 1
                            st.rerun()
                        else:
                            st.error("Name required")
        else:
            st.markdown("### 📋 Session Log")
            if evt['data']:
                df = pd.DataFrame(evt['data'])
                st.dataframe(df.iloc[::-1].head(5)[['name', 'gender', 'seat']], hide_index=True, use_container_width=True)
            else:
                st.info("Waiting for registrations...")

    st.markdown("---")
    if st.button("End Session"):
        st.session_state.subpage = None
        st.rerun()

def database_view(evt):
    st.subheader("📋 Database")
    if evt['data']:
        df = pd.DataFrame(evt['data'])
        
        # Public View (Read-only)
        st.dataframe(df, use_container_width=True)
        
        # Edit capability protected by password
        with st.expander("⚠️ Edit Database"):
            pwd = st.text_input("Enter Event Password to Edit", type="password")
            if st.button("Unlock Editing"):
                if pwd == evt['password']:
                    st.session_state.editing_unlocked = True
                    st.success("Unlocked! You can now edit below.")
                else:
                    st.error("Wrong Password")
            
            if st.session_state.get('editing_unlocked', False):
                st.write("### ✏️ Editor Mode")
                edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
                
                if st.button("💾 Save Changes"):
                    # Convert back to list of dicts
                    evt['data'] = edited_df.to_dict('records')
                    st.success("✅ Changes Saved!")
                    st.rerun()
    else:
        st.info("Empty database.")

def dashboard_view(evt):
    st.subheader("📊 Analytics Dashboard")
    st.write("Filter Participants:")
    age_range = st.slider("Select Age Range", 0, 100, (0, 100))
    
    if evt['data']:
        df = pd.DataFrame(evt['data'])
        if 'age' in df.columns:
            df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(0)
            df = df[(df['age'] >= age_range[0]) & (df['age'] <= age_range[1])]
            
        # Stats
        st.markdown("### Key Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", len(df))
        c2.metric("Males", len(df[df['gender']=='Male']))
        c3.metric("Females", len(df[df['gender']=='Female']))
        c4.metric("Non-Binary", len(df[df['gender']=='Non-Binary']))
        
        st.markdown("---")
        
        # Plotly Charts
        c_pie, c_bar = st.columns(2)
        with c_pie:
            st.subheader("Gender Distribution")
            gender_counts = df['gender'].value_counts().reset_index()
            gender_counts.columns = ['Gender', 'Count']
            fig_pie = px.pie(gender_counts, values='Count', names='Gender', 
                             color='Gender',
                             color_discrete_map={'Male':'#6C5DD3', 'Female':'#FF5A5F', 'Non-Binary':'#A0D2EB'},
                             hole=0.4)
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c_bar:
            st.subheader("Age vs Gender")
            if 'age' in df.columns:
                 fig_bar = px.histogram(df, x='gender', y='age', color='gender', 
                                    histfunc='avg', title="Average Age by Gender",
                                    color_discrete_map={'Male':'#6C5DD3', 'Female':'#FF5A5F', 'Non-Binary':'#A0D2EB'})
                 fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
                 st.plotly_chart(fig_bar, use_container_width=True)

        # Seating Heatmap using Plotly

        rows = evt.get('hall_rows', 5)
        cols = evt.get('hall_cols', 10)
        st.markdown("### 🏟️ Seating Arrangement")
        
        try:
            # Prepare Grid Data
            seat_map = {}
            unmapped_participants = []
            
            for p in evt['data']:
                try:
                    s_str = p.get('seat', '')
                    if not s_str or "Full" in s_str or "Error" in s_str:
                        unmapped_participants.append(p)
                        continue
                        
                    parts = s_str.split(',')
                    if len(parts) < 2:
                        unmapped_participants.append(p)
                        continue
                        
                    # Parse "Row A, Seat 1"
                    r_str = parts[0].replace("Row ", "").strip()
                    c_str = parts[1].replace("Seat ", "").strip()
                    r_idx = ord(r_str) - 65
                    c_idx = int(c_str) - 1
                    
                    if 0 <= r_idx < rows and 0 <= c_idx < cols:
                        seat_map[(r_idx, c_idx)] = p
                    else:
                        unmapped_participants.append(p) # Out of bounds
                except Exception as e: 
                    unmapped_participants.append(p)
                    # st.warning(f"Error parsing seat '{p.get('seat')}': {e}")

            # Generate HTML Grid
            html_grid = '<div style="display: flex; flex-direction: column; gap: 10px; overflow-x: auto; padding: 10px; background: rgba(255,255,255,0.02); border-radius: 10px;">'
            
            for r in range(rows):
                row_html = '<div style="display: flex; gap: 10px;">'
                # Row Label
                row_html += f'<div style="width: 40px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: rgba(255,255,255,0.7);">{chr(65+r)}</div>'
                
                for c in range(cols):
                    p_data = seat_map.get((r, c))
                    
                    # Default Styles
                    bg_color = "rgba(255,255,255,0.05)"
                    border_color = "rgba(255,255,255,0.1)"
                    text_content = f"<span style='font-size: 0.7rem; opacity: 0.3;'>{c+1}</span>"
                    tooltip = f"Row {chr(65+r)}, Seat {c+1}: Empty"
                    
                    if p_data:
                        name_display = p_data.get('name', '???')
                        tooltip = f"Row {chr(65+r)}, Seat {c+1}: {name_display} ({p_data['gender']})"
                        
                        if p_data['gender'] == 'Male':
                            bg_color = "rgba(108, 93, 211, 0.9)" # Purple
                            border_color = "#6C5DD3"
                        elif p_data['gender'] == 'Female':
                            bg_color = "rgba(255, 90, 95, 0.9)" # Pink
                            border_color = "#FF5A5F"
                        else:
                            bg_color = "rgba(160, 210, 235, 0.9)" # Blue
                            border_color = "#A0D2EB"
                            
                        # Intelligent Font Sizing
                        f_size = "0.85rem"
                        if len(name_display) > 6: f_size = "0.7rem"
                        if len(name_display) > 10: f_size = "0.6rem"
                        
                        text_content = f"<span style='font-weight: bold; font-size: {f_size}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 55px; display: block;'>{name_display}</span>"
                    
                    cell_html = f"""<div style="background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 8px; width: 60px; height: 50px; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s; cursor: default;" title="{tooltip}">{text_content}</div>"""
                    row_html += cell_html
                
                row_html += "</div>"
                html_grid += row_html
                
            html_grid += "</div>"
            
            st.markdown(html_grid, unsafe_allow_html=True)
            st.caption("Purple: Male | Pink: Female | Blue: Other")
            
            # Show Unmapped
            if unmapped_participants:
                with st.expander(f"⚠️ Unassigned / Parsing Issues ({len(unmapped_participants)})"):
                    st.write("These participants have been registered but could not be placed on the visual grid (likely due to Hall Capacity limits or data errors):")
                    for up in unmapped_participants:
                        st.write(f"- **{up.get('name', 'Unknown')}** ({up.get('seat', 'No Seat')})")
        
        except Exception as e:
            st.error(f"❌ Error rendering seating matrix: {e}")

        
        # 3. Download
        st.markdown("---")
        st.write("### 📥 Reports")
        c1, c2 = st.columns(2)
        
        # CSV
        csv = df.to_csv(index=False).encode('utf-8')
        c1.download_button("Download CSV", csv, "report.csv", "text/csv", use_container_width=True)
        
        # PDF
        if c2.button("Generate PDF Report", use_container_width=True):
            if FPDF is None:
                st.error("❌ 'fpdf' library is missing. Please run: pip install fpdf")
            else:
                try:
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.cell(200, 10, txt=f"Event Report: {evt['name']}", ln=1, align='C')
                    pdf.cell(200, 10, txt=f"Date: {evt['date']}", ln=1, align='C')
                    pdf.cell(200, 10, txt=f"Total: {len(df)} | M: {len(df[df['gender']=='Male'])} | F: {len(df[df['gender']=='Female'])}", ln=1, align='C')
                    pdf.ln(10)
                    
                    # Table Header
                    col_width = 30
                    headers = ['SL', 'Name', 'Gender', 'Seat', 'Age']
                    for h in headers:
                        pdf.cell(col_width, 10, h, 1)
                    pdf.ln()
                    
                    # Table Rows
                    for _, row in df.iterrows():
                        pdf.cell(col_width, 10, str(row.get('sl_no', '')), 1)
                        pdf.cell(col_width, 10, str(row.get('name', 'N/A')[:12]), 1) # Truncate
                        pdf.cell(col_width, 10, str(row.get('gender', '')), 1)
                        pdf.cell(col_width, 10, str(row.get('seat', '')), 1)
                        pdf.cell(col_width, 10, str(row.get('age', '')), 1)
                        pdf.ln()
                        
                    # Bytes logic
                    b64 = base64.b64encode(pdf.output(dest='S').encode('latin-1')).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="report.pdf">Download PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
                
                except Exception as e:
                    st.error(f"PDF Error: {e}")

def hall_dims(evt):
    st.subheader("⚙️ Hall Dimensions")
    c1, c2 = st.columns(2)
    evt['hall_rows'] = c1.number_input("Rows", 1, 26, evt['hall_rows'])
    evt['hall_cols'] = c2.number_input("Columns", 1, 50, evt['hall_cols'])
    
    st.markdown("### 👥 Seating Logic")
    evt['cluster_size'] = st.number_input("Cluster Size (Same Gender Grouping)", 1, 10, evt.get('cluster_size', 1), help="Number of students of same gender to seat together (e.g. 3 Boys, 3 Girls...)")
    st.success(f"Dimensions Updated. Cluster: {evt.get('cluster_size', 1)}")

def team_analysis(evt):
    st.subheader("👥 Analyze Team Creation")
    # 3.6 Advice Logic
    df = pd.DataFrame(evt['data'])
    total = len(df)
    m = len(df[df['gender']=='Male']) if not df.empty else 0
    f = len(df[df['gender']=='Female']) if not df.empty else 0
    
    st.write(f"**Total Students**: {total} (M: {m}, F: {f})")
    
    req_size = st.number_input("Target students per team", 2, 10, 4)
    
    if total > 0:
        num_teams = total // req_size
        st.info(f"💡 Advice: You can form **{num_teams}** fully balanced teams.")
        if st.button("Generate Teams"):
            teams = TeamManager.generate_teams(evt['data'], req_size)
            for i, t in enumerate(teams):
                st.write(f"**Team {i+1}**: {[p['gender'] for p in t]}")

def batch_upload_page(evt):
    st.subheader("📂 Batch Upload Multiple Pictures")
    st.info("Select a folder of images to auto-register participants.")
    st.caption("Naming convention: P1, P2... (If multiple: P1-1M, P1-2F...)")
    
    uploaded_files = st.file_uploader("Choose images...", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])
    
    if uploaded_files:
        # 1. Initial Capacity Check (Image vs Seats) strategy
        # We did a rough check before, but now we'll do it smarter or just keep rough check
        # User requested: "number of seats < number of images -> Error"
        rows = evt['hall_rows']
        cols = evt['hall_cols']
        total_seats = rows * cols
        current_data_count = len(evt['data'])
        available_seats = total_seats - current_data_count
        new_files_count = len(uploaded_files)
        
        if new_files_count > available_seats:
            st.error(f"❌ Too less seats in the hall, please add more seats! (Available: {available_seats}, Uploading: {new_files_count} files)")
            return
            
        st.write(f"Selected {new_files_count} images. Ready to process.")
        
        if st.button("🚀 Process & Register All", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            cluster = evt.get('cluster_size', 1)
            seat_mgr = SeatingManager(rows, cols, cluster_size=cluster)
            
            # Determine starting P number
            max_p = 0
            for d in evt['data']:
                name = d.get('name', '')
                # Extract number from P<Number>...
                if name.startswith('P'):
                    # specific parsing to handle P1, P1-1M etc
                    # Just take the first digit sequence
                    import re
                    match = re.search(r'P(\d+)', name)
                    if match:
                        num = int(match.group(1))
                        if num > max_p: max_p = num
            
            next_p_num = max_p + 1
            processed_count = 0
            warnings_list = []
            
            for i, img_file in enumerate(uploaded_files):
                status_text.text(f"Processing image {i+1}/{new_files_count}...")
                current_p_label_base = next_p_num + processed_count # P number based on actual added count to keep sequence? 
                # Actually, if we skip, the P number shouldn't increment if we want P1, P2... but user said P4 repeated.
                # If P4 is repeated, we just say P4 repeated.
                # Let's keep P_num incrementing for every *file* attempt or just successful ones?
                # Usually successful ones.
                
                try:
                    # Detect
                    image = Image.open(img_file)
                    faces = st.session_state.face_engine.process_image(image, detector_backend="ssd")
                    
                    if faces:
                        # Check strict capacity before adding
                        # Note: We check capacity based on *potential* adds. 
                        # If duplicate, we won't add, so we don't consume seat.
                        # extra_seats_needed = len(faces) # worst case
                        # available = total_seats - len(evt['data'])
                        # if extra_seats_needed > available: ... 
                        # For now, let's just check individually inside loop to be safe and accurate
                        
                        is_multi = len(faces) > 1
                        
                        for f_idx, face in enumerate(faces):
                            # DUPLICATE CHECK
                            new_encoding = np.array(face['encoding'])
                            known_encs = st.session_state.face_engine.known_encodings
                            known_ids = st.session_state.face_engine.known_ids
                            current_evt_id = st.session_state.current_event
                            
                            match_found = False
                            matched_name = ""
                            
                            # Filter for current event only (or global? User said "Person P4 repeated", P4 implies current event context)
                            # We'll check against ALL known faces in THIS event
                            if len(known_encs) > 0:
                                # Create list of encodings for this event
                                event_indices = [idx for idx, meta in enumerate(known_ids) if meta['event_id'] == current_evt_id]
                                if event_indices:
                                    event_encs = [known_encs[idx] for idx in event_indices]
                                    
                                    # Calculate distances
                                    # simple euclidean distance
                                    distances = np.linalg.norm(event_encs - new_encoding, axis=1)
                                    min_dist_idx = np.argmin(distances)
                                    if distances[min_dist_idx] < 0.5: # Strict threshold for duplicate
                                        match_found = True
                                        original_idx = event_indices[min_dist_idx]
                                        matched_name = known_ids[original_idx]['name']

                            if match_found:
                                warnings_list.append(f"Person **{matched_name}** has been repeated in *{img_file.name}*, he/she will be registered only once.")
                                continue # Skip registration
                                
                            # If not duplicate, CHECK SEATS
                            if len(evt['data']) >= total_seats:
                                st.error(f"❌ Hall Full! Stopped at {img_file.name}. (Seat limit reached)")
                                # Stop everything? or just this face?
                                # Break out of file loop
                                raise StopIteration("Hall Full")

                            gender = face['gender']
                            
                            # Label Logic
                            # We use len(evt['data']) + 1 to ensure sequential naming based on ACTUAL stored data
                            # This handles the skipping correctly (e.g. if we skip P4 duplicate, next new person becomes P5 is wrong? 
                            # No, if P4 is repeated, it's P4.
                            # Next NEW person should be P5.
                            # So using len + 1 is safe.
                            next_sl = len(evt['data']) + 1
                            
                            if is_multi:
                                g_code = gender[0].upper()
                                p_label = f"P{next_sl}-{f_idx+1}{g_code}"
                            else:
                                p_label = f"P{next_sl}"
                            
                            # Allocate Seat
                            seat = seat_mgr.allocate_seat(evt['data'], gender)
                            
                            # Register
                            record = {
                                "sl_no": next_sl,
                                "gender": gender,
                                "seat": seat,
                                "name": p_label, 
                                "id": "Batch_Upload",
                                "branch": "N/A",
                                "age": 0, 
                                "encoding": face['encoding'],
                                "timestamp": str(datetime.now())
                            }
                            evt['data'].append(record)
                            
                            # Add to known faces
                            st.session_state.face_engine.known_encodings.append(np.array(face['encoding']))
                            st.session_state.face_engine.known_ids.append({'name': p_label, 'event_id': current_evt_id})
                            
                            processed_count += 1
                    else:
                        st.warning(f"⚠️ No face detected in {img_file.name}. Skipped.")
                        
                except StopIteration:
                    break
                except Exception as e:
                    st.error(f"Error processing {img_file.name}: {e}")
                
                progress_bar.progress((i + 1) / new_files_count)
            
            if warnings_list:
                for w in warnings_list:
                    st.warning(w)
                    
            st.success(f"✅ Batch Processing Complete! Registered {processed_count} new participants.")
            time.sleep(3) # Give time to read warnings
            st.rerun()

def create_folder():
    render_header()
    st.header("📁 Create Main Event Folder")
    f_name = st.text_input("Folder Name")
    if st.button("Create"):
        st.session_state.main_folders[f_name] = {"date": str(datetime.now().date()), "events": []}
        st.success("Created!")
        st.session_state.page = "home"
        st.rerun()

def view_folders():
    render_header()
    st.header("Manage Main Folders")
    
    if not st.session_state.main_folders:
        st.info("No folders. Create one!")
        return

    for fname, fdata in st.session_state.main_folders.items():
        with st.expander(f"📁 {fname} (Date: {fdata['date']})"):
            # Sub-events management
            st.write(f"**Sub-events**: {len(fdata['events'])}")
            
            # Add existing event to folder
            all_events = list(st.session_state.events.keys())
            avail = [e for e in all_events if e not in fdata['events']]
            
            sel_evt = st.selectbox("Add Event to Folder", avail, key=f"sel_add_{fname}")
            if st.button("Add", key=f"btn_add_{fname}"):
                fdata['events'].append(sel_evt)
                st.success("Added!")
                st.rerun()
                
            # Aggregate Stats
            if fdata['events']:
                total = 0
                gender_counts_folder = {'Male': 0, 'Female': 0, 'Non-Binary': 0}
                event_stats = []

                for eid in fdata['events']:
                    if eid not in st.session_state.events: continue
                    d = st.session_state.events[eid]['data']
                    count = len(d)
                    total += count
                    
                    m = len([x for x in d if x['gender'] == 'Male'])
                    f = len([x for x in d if x['gender'] == 'Female'])
                    nb = len([x for x in d if x['gender'] == 'Non-Binary'])
                    
                    gender_counts_folder['Male'] += m
                    gender_counts_folder['Female'] += f
                    gender_counts_folder['Non-Binary'] += nb
                    
                    event_stats.append({
                        "Event": st.session_state.events[eid]['name'],
                        "Attendees": count
                    })
                
                st.write("### 📊 Aggregated Stats")
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Participants", total)
                c2.metric("Total Males", gender_counts_folder['Male'])
                c3.metric("Total Females", gender_counts_folder['Female'])
                
                # Plotly Charts
                cp1, cp2 = st.columns(2)
                with cp1:
                    df_gender = pd.DataFrame([{"Gender": k, "Count": v} for k, v in gender_counts_folder.items() if v > 0])
                    if not df_gender.empty:
                        fig_pie = px.pie(df_gender, values='Count', names='Gender', 
                                         color='Gender',
                                         color_discrete_map={'Male':'#6C5DD3', 'Female':'#FF5A5F', 'Non-Binary':'#A0D2EB'},
                                         hole=0.4)
                        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), margin=dict(t=20, b=20))
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.info("No gender data available.")
                        
                with cp2:
                    if event_stats:
                        df_evts = pd.DataFrame(event_stats)
                        fig_bar = px.bar(df_evts, x='Event', y='Attendees', color='Attendees',
                                         color_continuous_scale=['#A0D2EB', '#6C5DD3'])
                        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), margin=dict(t=20, b=20))
                        st.plotly_chart(fig_bar, use_container_width=True)
                    else:
                        st.info("No event data available.")
                
                st.write("### 📂 Events in this Folder")
                for eid in fdata['events']:
                    if eid in st.session_state.events:
                        evt_name = st.session_state.events[eid]['name']
                        if st.button(f"Go to {evt_name}", key=f"goto_{fname}_{eid}"):
                             st.session_state.current_event = eid
                             st.session_state.page = "event_menu"
                             st.rerun()

try:
    from utils import SeatingManager, TeamManager, TeamBalancer
except: pass

def team_management(evt):
    st.header("🤝 Team Role Allocation")
    
    # Initialize structures if missing
    if 'roles' not in evt: evt['roles'] = {}
    if 'team_members' not in evt: evt['team_members'] = [] # {id, name, gender, skills: {}}
    
    tab1, tab2, tab3 = st.tabs(["1. Define Roles", "2. Add Team Members", "3. Allocate Roles"])
    
    # TAB 1: DEFINE ROLES
    with tab1:
        st.subheader("Define Roles & Skills")
        
        # Initialize dynamic field count
        if 'role_skill_count' not in st.session_state: st.session_state.role_skill_count = 3
        
        c_add, c_rem = st.columns([1,1])
        if c_add.button("➕ Add Skill Field"):
            st.session_state.role_skill_count += 1
            st.rerun()
        if c_rem.button("➖ Remove Skill Field"):
            if st.session_state.role_skill_count > 1:
                st.session_state.role_skill_count -= 1
                st.rerun()

        with st.form("add_role_form", clear_on_submit=True):
            r_name = st.text_input("Role Name (e.g. MC, Creative)")
            r_count = st.number_input("Number of Positions", 1, 10, 2)
            
            st.write(f"Required Skills & Weights (Total: {st.session_state.role_skill_count})")
            
            # Dynamic Inputs
            skills_data = []
            for i in range(st.session_state.role_skill_count):
                c1, c2 = st.columns(2)
                s = c1.text_input(f"Skill {i+1}", key=f"d_skill_{i}")
                w = c2.slider(f"Weight {i+1}", 1, 10, 5, key=f"d_weight_{i}")
                skills_data.append((s, w))
            
            if st.form_submit_button("Add/Update Role"):
                reqs = {}
                for s, w in skills_data:
                    if s.strip(): # Only add if skill name is provided
                        reqs[s.strip()] = w
                
                if r_name and reqs:
                    evt['roles'][r_name] = {'count': r_count, 'reqs': reqs}
                    st.success(f"Role '{r_name}' added with {len(reqs)} skills!")
                    st.rerun()
                else:
                    st.error("Role Name and at least one Skill are required.")
        
        st.write("### Current Roles")
        if evt['roles']:
            for r, data in evt['roles'].items():
                st.write(f"**{r}** (Count: {data['count']})")
                st.json(data['reqs'])
                if st.button(f"Delete {r}", key=f"del_{r}"):
                    del evt['roles'][r]
                    st.rerun()
        else:
            st.info("No roles defined yet.")

    # TAB 2: ADD MEMBERS
    with tab2:
        st.subheader("Add Team Members")
        
        with st.form("add_member_form", clear_on_submit=True):
            name = st.text_input("Name")
            gender = st.selectbox("Gender", ["Male", "Female", "Non-Binary"])
            
            st.write("### Skills")
            st.caption("Select skills this person possesses. (Score is determined by Role Weight)")
            
            all_skills = set()
            for r in evt['roles'].values():
                for s in r['reqs'].keys():
                    all_skills.add(s)
            
            candidate_skills = []
            
            if all_skills:
                # User selects relevant skills
                candidate_skills = st.multiselect("Select Skills", options=sorted(list(all_skills)))
            else:
                st.warning("No roles defined yet. Define roles to see relevant skills.")
            
            # Option to add a custom skill not in the list (for future roles?)
            with st.expander("Add Custom/Extra Skill"):
                cust_skill = st.text_input("Skill Name (e.g. Acrobatics)")
                if cust_skill:
                   candidate_skills.append(cust_skill)
            
            if st.form_submit_button("Add Member"):
                if name:
                    mid = generate_code()
                    evt['team_members'].append({
                        'id': mid,
                        'name': name,
                        'gender': gender,
                        'skills': candidate_skills # List of strings now
                    })
                    st.success(f"{name} added!")
                    st.rerun()
                else:
                    st.error("Name is required.")
        
        st.write(f"### Team Members ({len(evt['team_members'])})")
        if evt['team_members']:
            df_team = pd.DataFrame(evt['team_members'])
            # Flatten skills for display
            display_data = []
            for m in evt['team_members']:
                d = {'Name': m['name'], 'Gender': m['gender']}
                
                # Handle Skills Display (List or Dict)
                skills = m.get('skills', [])
                if isinstance(skills, dict):
                     # Old format: {skill: rating}
                     d['Skills'] = ", ".join([f"{k} ({v})" for k,v in skills.items()])
                elif isinstance(skills, list):
                     # New format: [skill, skill]
                     d['Skills'] = ", ".join([str(s) for s in skills])
                else:
                     d['Skills'] = str(skills)
                
                display_data.append(d)
            st.dataframe(pd.DataFrame(display_data))

    # TAB 3: ALLOCATE
    with tab3:
        st.subheader("Allocate Roles")
        
        mode = st.radio("Allocation Mode", 
            ["Skill Priority (No Gender Adj)", 
             "Balance Mode (Threshold 20%)", 
             "Equality Priority (Threshold 30%)"])
             
        threshold = 0.0
        if "Balance" in mode: threshold = 0.20
        elif "Equality" in mode: threshold = 0.30
        
        if st.button("🚀 Run Allocation", type="primary"):
            assignments, logs = TeamBalancer.allocate_roles(evt['team_members'], evt['roles'], threshold)
            
            st.write("### 🎯 Results")
            
            cols = st.columns(len(assignments))
            for i, (r_name, assigned) in enumerate(assignments.items()):
                with cols[i % len(cols)]:
                    st.success(f"**{r_name}**")
                    if not assigned:
                        st.warning("No candidates.")
                    for item in assigned:
                        color = "blue" if item['c']['gender'] == 'Male' else "magenta"
                        st.markdown(f":{color}[{item['c']['name']}] ({item['c']['gender']})")
                        st.caption(f"Score: {item['s']:.2f}")
            
            if logs:
                with st.expander("Show Logic / Swaps"):
                    for l in logs:
                        st.write(f"- {l}")

# --- MAIN ROUTING ---
if st.session_state.page == "login": login_page()
elif st.session_state.page == "home": home_page()
elif st.session_state.page == "create_event": create_event()
elif st.session_state.page == "events_list": events_list()
elif st.session_state.page == "event_menu": event_menu()
elif st.session_state.page == "create_folder": create_folder()
elif st.session_state.page == "view_folders": view_folders()
