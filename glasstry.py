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
import base64

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
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    div[data-testid="stExpander"], div[data-testid="stForm"], div[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    input, .stSelectbox > div > div > div {
        background: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }
    h1, h2, h3, h4, .stMarkdown, label, .stDataFrame, .stMetricLabel {
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricValue"] { color: white !important; }
    .stButton > button {
        background: rgba(255, 255, 255, 0.25);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.4);
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

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
            elif st.session_state.page in ["events_list", "create_event", "create_folder", "view_folders"]:
                st.session_state.page = "home"
            st.rerun()

# --- PAGES ---

def login_page():
    render_header()
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 Event Host Login")
        
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
        st.info("�📂 Import")
        if st.button("Upload CSV File", use_container_width=True):
            st.session_state.subpage = "upload_csv"
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
    elif st.session_state.subpage == "upload_csv": upload_csv(evt)

def attendance_setup(evt):
    st.subheader("🏁 Start Attendance Session")
    mode = st.selectbox("Select Mode", ["Normal (Full Data)", "Privacy (No Personal Data)"])
    if st.button("Start Session", type="primary"):
        st.session_state.temp_mode = mode
        st.session_state.subpage = "attendance_active"
        st.rerun()

def attendance_active(evt):
    mode = st.session_state.temp_mode
    st.subheader(f"📸 Live Session ({mode})")
    
    # 3.2.1 / 3.2.2 Live Logic
    col_cam, col_info = st.columns([1, 1])
    
    with col_cam:
        # Input Method Toggle
        input_method = st.radio("Input Method", ["Camera", "Upload Image"], horizontal=True)
        
        img_file = None
        if input_method == "Camera":
            img_file = st.camera_input("Scan Face")
        else:
            img_file = st.file_uploader("Upload Image (JPG/PNG)", type=['jpg', 'jpeg', 'png'], key=f"uploader_{st.session_state.upload_key}")
            
        # Advanced Settings Expandable
        with st.expander("⚙️ Detection Settings"):
            backend = st.selectbox(
                "Face Detector", 
                ["opencv", "ssd", "mtcnn", "retinaface"], 
                index=1, # Default to SSD (Better than OpenCV/Haar)
                help="If 'opencv' fails, try 'ssd' or others. (May require install)"
            )
            debug_mode = st.checkbox("Show Debug Info", value=True)

    
    with col_info:
        # Live Counters
        df = pd.DataFrame(evt['data'])
        total = len(df)
        if not df.empty:
            m = len(df[df['gender'] == 'Male'])
            f = len(df[df['gender'] == 'Female'])
            ratio = f"{m}:{f}"
        else:
            ratio = "0:0"
            
        st.metric("Total Registered", total)
        st.metric("Current Ratio (M:F)", ratio)
        
        if img_file:
            # PROCESS IMAGE with Caching to ensure Form Persistence
            # Logic: If image bytes haven't changed, don't re-run DeepFace.
            # This prevents specific bugs where re-running detection on submission might fail or drift.
            
            bytes_data = img_file.getvalue()
            
            # Check if we have a cached result for this exact image
            # Also check if backend changed, if so force re-process
            last_backend = st.session_state.get('last_backend', None)
            
            if st.session_state.get('last_img_bytes') != bytes_data or last_backend != backend:
                # New image or new backend -> Process
                img = Image.open(img_file)
                st.session_state.last_results = st.session_state.face_engine.process_image(img, detector_backend=backend)
                st.session_state.last_img_bytes = bytes_data
                st.session_state.last_img_object = img # Store for display
                st.session_state.last_backend = backend
            
            results = st.session_state.last_results
            img = st.session_state.get('last_img_object', Image.open(img_file))
            
            if not results:
                st.warning("No face detected.")
            else:
                face = results[0] # Take first face
                st.image(img, caption=f"Detected: {face['gender']}", width=200)
                
                # Check Duplicate
                if face['is_duplicate']:
                    dup = face['duplicate_info']
                    st.error(f"⚠️ Already Registered in {dup['event_id']} as {dup['name']}")
                    st.write("Do you want to register them anyway?")
                    
                # Seat Allocation
                cluster = evt.get('cluster_size', 1)
                seat_mgr = SeatingManager(evt['hall_rows'], evt['hall_cols'], cluster_size=cluster)
                allocated_seat = seat_mgr.allocate_seat(evt['data'], face['gender'])
                st.success(f"🪑 Allocated Seat: {allocated_seat}")
                
                # Registration Form
                with st.form("reg_form_process", clear_on_submit=True):
                    st.write("### Participant Details")
                    
                    if "Privacy" in mode:
                        # Privacy Mode
                        st.info("🔒 Privacy Mode: Only recording Gender & Seat")
                        submitted = st.form_submit_button("Register & Save")
                        if submitted:
                            evt['data'].append({
                                "sl_no": len(evt['data'])+1,
                                "gender": face['gender'],
                                "seat": allocated_seat,
                                "timestamp": str(datetime.now())
                            })
                            st.success("Saved!")
                            st.session_state.last_img_bytes = None # Clear cache to force next
                            st.session_state.upload_key += 1
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        # Normal Mode
                        name = st.text_input("Name")
                        pid = st.text_input("ID")
                        branch = st.text_input("Branch")
                        age = st.number_input("Age", 0, 100, 18)
                        
                        submitted = st.form_submit_button("Register & Save")
                        if submitted:
                            if name:
                                evt['data'].append({
                                    "sl_no": len(evt['data'])+1,
                                    "gender": face['gender'],
                                    "seat": allocated_seat,
                                    "name": name,
                                    "id": pid,
                                    "branch": branch,
                                    "age": age,
                                    "encoding": face['encoding'],
                                    "timestamp": str(datetime.now())
                                })
                                # Add to known faces
                                st.session_state.face_engine.known_encodings.append(np.array(face['encoding']))
                                st.session_state.face_engine.known_ids.append({'name': name, 'event_id': st.session_state.current_event})
                                
                                st.success(f"Saved {name}!")
                                st.session_state.last_img_bytes = None # Clear cache
                                st.session_state.upload_key += 1
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ Name is required!")
    
    st.markdown("---")
    if st.button("End Session and Save"):
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
    # Filters
    st.write("Filter Participants:")
    age_range = st.slider("Select Age Range", 0, 100, (0, 100))
    
    if evt['data']:
        df = pd.DataFrame(evt['data'])
        # Filter Logic
        if 'age' in df.columns:
            # Handle NaN/None in age for privacy mode entries
            df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(0)
            df = df[(df['age'] >= age_range[0]) & (df['age'] <= age_range[1])]
            
        # Stats
        c1, c2, c3 = st.columns(3)
        c1.metric("Males", len(df[df['gender']=='Male']))
        c2.metric("Females", len(df[df['gender']=='Female']))
        c3.metric("Non-Binary", len(df[df['gender']=='Non-Binary']))
        
        # Visual Hall Map
        st.write("### 🏟️ Hall Seating Map")
        st.caption("🟦 Male | 🟪 Female | 🟨 Non-Binary")
        
        # Create Grid
        rows = evt['hall_rows']
        cols = evt['hall_cols']
        
        # Prepare grid data
        seat_grid = {} # (r,c) -> gender/info
        for p in evt['data']:
            try:
                # Parse "Row A, Seat 1"
                parts = p['seat'].split(',')
                # Row A -> 0, Row B -> 1
                r_idx = ord(parts[0].replace("Row ", "").strip()) - 65
                c_idx = int(parts[1].replace("Seat ", "").strip()) - 1
                seat_grid[(r_idx, c_idx)] = p
            except: pass
            
        # Render Grid using Columns
        for r in range(rows):
            # Create a container for the row to keep it tight
            row_cols = st.columns(cols)
            for c in range(cols):
                participant = seat_grid.get((r, c))
                
                with row_cols[c]:
                    if participant:
                        g = participant['gender']
                        color_hex = "#3b82f6" if g == 'Male' else "#d946ef" if g == 'Female' else "#eab308" # Blue, Pink, Yellow
                        
                        # Tooltip info
                        info = f"{participant.get('name', 'Unknown')}"
                        if 'id' in participant: info += f"\nID: {participant['id']}"
                        
                        st.markdown(f'''
                        <div title="{info}" style="
                            width: 100%; 
                            height: 30px; 
                            background-color: {color_hex}; 
                            border-radius: 4px;
                            border: 1px solid rgba(255,255,255,0.5);
                            cursor: pointer;">
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        st.markdown(f'''
                        <div style="
                            width: 100%; 
                            height: 30px; 
                            background-color: rgba(255,255,255,0.1); 
                            border-radius: 4px;
                            border: 1px dashed rgba(255,255,255,0.3);">
                        </div>
                        ''', unsafe_allow_html=True)
        
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

def upload_csv(evt):
    st.subheader("📂 Upload CSV")
    st.info("Ensure CSV has columns: name, gender (Male/Female), age, etc.")
    uploaded = st.file_uploader("Choose CSV", type='csv')
    if uploaded:
        try:
            new_df = pd.read_csv(uploaded)
            st.write("Preview:", new_df.head())
            
            # Map columns logic (simplified)
            required = ['name', 'gender']
            if all(col in new_df.columns.str.lower() for col in required):
                 # Case insensitive alignment
                 new_df.columns = new_df.columns.str.lower()
                 
                 if st.button("Import Data"):
                     records = new_df.to_dict('records')
                     seating_mgr = SeatingManager(evt['hall_rows'], evt['hall_cols'])
                     
                     count = 0
                     for rec in records:
                         # Allocate seat for imported data too!
                         seat = seating_mgr.allocate_seat(evt['data'], rec.get('gender', 'Male'))
                         rec['seat'] = seat
                         rec['sl_no'] = len(evt['data']) + 1
                         rec['timestamp'] = str(datetime.now())
                         evt['data'].append(rec)
                         count += 1
                         
                     st.success(f"✅ Imported {count} records!")
                     time.sleep(1)
                     st.rerun()
            else:
                st.warning(f"CSV must contain {required} columns.")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

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
                m = 0
                f = 0
                for eid in fdata['events']:
                    d = st.session_state.events[eid]['data']
                    total += len(d)
                    m += len([x for x in d if x['gender'] == 'Male'])
                    f += len([x for x in d if x['gender'] == 'Female'])
                
                st.write("### 📊 Aggregated Stats")
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Participants", total)
                c2.metric("Total Males", m)
                c3.metric("Total Females", f)
                
                st.write("### 📂 Events in this Folder")
                for eid in fdata['events']:
                    if st.button(f"Go to {st.session_state.events[eid]['name']}", key=f"goto_{fname}_{eid}"):
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
