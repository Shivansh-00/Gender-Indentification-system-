import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from datetime import datetime
import cv2
from face_engine import FaceEngine

# Initialize session state
if 'main_folders' not in st.session_state: st.session_state.main_folders = {}
if 'events' not in st.session_state: st.session_state.events = {}
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'page' not in st.session_state: st.session_state.page = "login"
if 'current_event' not in st.session_state: st.session_state.current_event = None
if 'current_folder' not in st.session_state: st.session_state.current_folder = None

# Multi-person attendance state
if 'face_engine' not in st.session_state: st.session_state.face_engine = FaceEngine()
if 'detected_faces' not in st.session_state: st.session_state.detected_faces = []
if 'current_face_idx' not in st.session_state: st.session_state.current_face_idx = 0
if 'last_photo_hash' not in st.session_state: st.session_state.last_photo_hash = None

st.set_page_config(page_title="Gender Attendance", layout="wide", page_icon="👋")

# ==========================================
# 🎨 UI/UX DESIGN SYSTEM
# ==========================================
# ==========================================
# 🎨 UI/UX DESIGN SYSTEM
# ==========================================
def load_css():
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
            font-family: 'Outfit', sans-serif; /* Modern, tech-friendly font */
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
        .card, [data-testid="stMetric"], [data-testid="stExpander"], div.stDataFrame {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover, [data-testid="stMetric"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px 0 rgba(127, 90, 240, 0.2);
            border-color: rgba(127, 90, 240, 0.3);
        }

        /* METRIC CARDS SPECIFICS */
        [data-testid="stMetric"] {
            padding: 1.5rem;
            text-align: center;
        }
        [data-testid="stMetricLabel"] { font-size: 0.9rem; color: #94A1B2; letter-spacing: 0.05em; text-transform: uppercase; }
        [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700; color: var(--text-light) !important; text-shadow: 0 0 20px rgba(127,90,240,0.5); }

        /* BUTTONS - GLOSSY & ANIMATED */
        div.stButton > button {
            background: linear-gradient(135deg, rgba(127, 90, 240, 0.8), rgba(44, 182, 125, 0.8));
            color: white;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 12px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            letter-spacing: 0.03em;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
            box-shadow: 0 8px 25px rgba(127, 90, 240, 0.4), inset 0 1px 0 rgba(255,255,255,0.4);
            border-color: rgba(255,255,255,0.5);
        }
        
        div.stButton > button:hover::before {
            left: 100%;
        }
        
        div.stButton > button:active {
            transform: scale(0.98);
        }
        
        /* SECONDARY BUTTONS (Simple outline or different color) */
        /* Currently streamlining all buttons for consistency, but you can target specific keys if needed */

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

        /* DATAFRAME STYLING */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--glass-border);
        }

        /* EXPANDER HEADER */
        .streamlit-expanderHeader {
            font-weight: 600;
            color: var(--text-light) !important;
            background-color: rgba(255,255,255,0.02) !important;
        }
        
        /* CAMERA INPUT */
        div[data-testid="stCameraInput"] {
            border: 2px solid var(--glass-border);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
    </style>
    """, unsafe_allow_html=True)

load_css()

# BACK BUTTON HELPER
def back_button(target_page):
    if st.button("⬅️ Back", key=f"back_{target_page}"):
        st.session_state.page = target_page
        st.rerun()

def login():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='text-align: center;'><h1>🔐 Event Host Login</h1></div>", unsafe_allow_html=True)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        st.write("")
        if st.button("🚀 Sign In", type="primary", use_container_width=True):
            if username == "host" and password == "123":
                st.session_state.current_user = username
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("❌ Wrong credentials")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray; margin-top: 10px;'>💡 Demo: <code>host</code> / <code>123</code></p>", unsafe_allow_html=True)

def home():
    st.markdown("# 🎉 Gender Equality Attendance System")
    st.subheader(f"Good {'Morning' if int(datetime.now().strftime('%H')) < 12 else 'Afternoon'}, {st.session_state.current_user}! 👋")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            st.info("### ➕ Create New Event\nStart a new attendance session.")
            if st.button("Launch Creator", key="btn_create"):
                st.session_state.page = "create_event"
                st.rerun()
        
        st.write("") # Spacer
        
        with st.container():
             st.success("### 📂 Managed Events\nView and manage your existing events.")
             if st.button("View Events", key="btn_view"):
                st.session_state.page = "events_list"
                st.rerun()

    with col2:
        with st.container():
            st.warning("### 📁 Create Folder\nOrganize events into main folders.")
            if st.button("New Folder", key="btn_folder"):
                st.session_state.page = "create_folder"
                st.rerun()
        
        st.write("") # Spacer

        with st.container():
            st.error("### 📋 Browse Folders\nCheck all your organized folders.")
            if st.button("Check Folders", key="btn_check"):
                st.session_state.page = "main_folders_list"
                st.rerun()

def create_event():
    st.header("➕ Create New Event")
    event_name = st.text_input("Event Name")
    event_date = st.date_input("Event Date")
    
    col1, col2 = st.columns([3,1])
    with col1:
        if st.button("✅ Create Event", type="primary", use_container_width=True):
            event_id = f"{event_name}_{event_date}".replace(" ", "_")
            st.session_state.events[event_id] = {
                "name": event_name, "date": str(event_date), "data": [],
                "hall_rows": 5, "hall_cols": 10
            }
            st.success(f"✅ '{event_name}' created!")
            st.session_state.page = "home"
            st.rerun()
    back_button("home")

def create_folder():
    st.header("📁 Create Main Event Folder")
    folder_name = st.text_input("Folder Name")
    folder_date = st.date_input("Folder Date")
    
    col1, col2 = st.columns([3,1])
    with col1:
        if st.button("✅ Create Folder", type="primary", use_container_width=True):
            folder_id = f"{folder_name}_{folder_date}".replace(" ", "_")
            st.session_state.main_folders[folder_id] = {
                "name": folder_name, "date": str(folder_date), "events": []
            }
            st.success(f"✅ Folder '{folder_name}' created!")
            st.session_state.page = "home"
            st.rerun()
    back_button("home")

def main_folders_list():
    st.header("📁 Main Event Folders")
    
    for folder_id, folder in st.session_state.main_folders.items():
        with st.expander(f"📁 {folder['name']} ({len(folder['events'])} events)"):
            st.write(f"**Date**: {folder['date']}")
            
            available_events = [e for e in st.session_state.events.keys() 
                              if e not in folder['events']]
            selected_event = st.selectbox("Add Event", available_events, key=f"add_{folder_id}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"➕ Add Event", key=f"addbtn_{folder_id}"):
                    folder['events'].append(selected_event)
                    st.success(f"✅ '{selected_event}' added!")
                    st.rerun()
            
            for event_id in folder['events']:
                event_name = st.session_state.events[event_id]['name']
                col1, col2 = st.columns([3,1])
                col1.write(f"• 📋 {event_name}")
                if col2.button("📊 View", key=f"view_{event_id}"):
                    st.session_state.current_folder = folder_id
                    st.session_state.current_event = event_id
                    st.session_state.page = "event_dashboard"
                    st.rerun()
            
            st.markdown("---")
            if st.button("📈 Folder Analytics", key=f"analytics_{folder_id}", use_container_width=True):
                st.session_state.current_folder = folder_id
                st.session_state.page = "folder_dashboard"
                st.rerun()
    
    back_button("home")

def folder_dashboard_page():
    if not st.session_state.current_folder:
        st.error("No folder selected.")
        if st.button("Back"): st.session_state.page = "main_folders_list"; st.rerun()
        return

    folder_id = st.session_state.current_folder
    folder = st.session_state.main_folders[folder_id]
    
    st.markdown(f"## 📈 Analytics: {folder['name']}")
    st.caption(f"📅 Created: {folder['date']}")
    
    # Aggregate Data
    total_attendees = 0
    gender_counts = {"Male": 0, "Female": 0, "Non-Binary": 0}
    event_stats = []
    
    for event_id in folder['events']:
        event = st.session_state.events.get(event_id)
        if not event: continue
        
        count = len(event['data'])
        total_attendees += count
        
        m = len([p for p in event['data'] if p['gender'] == "Male"])
        f = len([p for p in event['data'] if p['gender'] == "Female"])
        nb = count - m - f
        
        gender_counts["Male"] += m
        gender_counts["Female"] += f
        gender_counts["Non-Binary"] += nb
        
        event_stats.append({
            "Event": event['name'],
            "Date": event['date'],
            "Attendees": count,
            "Male": m, 
            "Female": f
        })
    
    # --- METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events", len(folder['events']))
    col2.metric("Total Attendees", total_attendees)
    col3.metric("Avg Attendance", f"{total_attendees / len(folder['events']):.1f}" if folder['events'] else "0")
    
    st.markdown("---")
    
    if total_attendees > 0:
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Overall Gender Distribution")
            df_gender = pd.DataFrame([
                {"Gender": k, "Count": v} for k, v in gender_counts.items() if v > 0
            ])
            
            fig_pie = px.pie(df_gender, values='Count', names='Gender', 
                             color='Gender',
                             color_discrete_map={'Male':'#6C5DD3', 'Female':'#FF5A5F', 'Non-Binary':'#A0D2EB'},
                             hole=0.4)
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("Attendance by Event")
            df_events = pd.DataFrame(event_stats)
            fig_bar = px.bar(df_events, x='Event', y='Attendees', color='Attendees',
                             color_continuous_scale=['#A0D2EB', '#6C5DD3'])
            fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with st.expander("📄 Detailed Event Statistics"):
            st.dataframe(pd.DataFrame(event_stats), use_container_width=True)
    else:
        st.info("No attendance data found in this folder yet.")

    st.write("")
    if st.button("⬅️ Back to Folders", use_container_width=True):
        st.session_state.page = "main_folders_list"
        st.rerun()

# ROUTING
if st.session_state.page == "login": login()
elif st.session_state.page == "home": home()
elif st.session_state.page == "create_event": create_event()
elif st.session_state.page == "create_folder": create_folder()
elif st.session_state.page == "events_list": events_list()
elif st.session_state.page == "main_folders_list": main_folders_list()
elif st.session_state.page == "event_dashboard": event_dashboard()
elif st.session_state.page == "folder_dashboard": folder_dashboard_page()
