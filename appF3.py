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

st.set_page_config(page_title="Gender Attendance", layout="wide")

# BACK BUTTON HELPER
def back_button(target_page):
    if st.button("⬅️ Back", key=f"back_{target_page}"):
        st.session_state.page = target_page
        st.rerun()

def login():
    st.title("🔐 Event Host Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Sign In", type="primary"):
        if username == "host" and password == "123":
            st.session_state.current_user = username
            st.session_state.page = "home"
            st.rerun()
        else:
            st.error("❌ Wrong credentials")
    st.caption("💡 Demo: `host` / `123`")

def home():
    st.markdown("# 🎉 Gender Equality Attendance System")
    st.subheader(f"Good {'Morning' if int(datetime.now().strftime('%H')) < 12 else 'Afternoon'}, {st.session_state.current_user}! 👋")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Create New Event", use_container_width=True):
            st.session_state.page = "create_event"
            st.rerun()
        if st.button("📂 Existing Events", use_container_width=True):
            st.session_state.page = "events_list"
            st.rerun()
    with col2:
        if st.button("📁 Create Main Event Folder", use_container_width=True):
            st.session_state.page = "create_folder"
            st.rerun()
        if st.button("📋 Check Main Event Folders", use_container_width=True):
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
    
    back_button("home")

def simple_gender_detection(image):
    rand = np.random.random()
    if rand > 0.85: return "Female", 88
    elif rand > 0.15: return "Male", 85
    else: return "Non-Binary", 90

def event_dashboard():
    event = st.session_state.events[st.session_state.current_event]
    folder_name = "None"
    if st.session_state.current_folder:
        folder = st.session_state.main_folders[st.session_state.current_folder]
        folder_name = folder['name']
    
    st.header(f"📋 {event['name']} - {event['date']} ({folder_name})")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: 
        if st.button("📸 Start Attendance"): 
            st.session_state.subpage = "attendance"; st.rerun()
    with col2: 
        if st.button("📊 View Dashboard"): 
            st.session_state.subpage = "dashboard"; st.rerun()
    with col3: 
        if st.button("📋 View Database"): 
            st.session_state.subpage = "database"; st.rerun()
    with col4: 
        if st.button("🎯 Hall Dimensions"): 
            st.session_state.subpage = "hall"; st.rerun()
    
    # Back to events list
    if st.button("🏠 Back to Events"):
        st.session_state.page = "events_list"
        st.rerun()
    
    if 'subpage' in st.session_state:
        if st.session_state.subpage == "attendance": attendance_page(event)
        elif st.session_state.subpage == "dashboard": dashboard_page(event)
        elif st.session_state.subpage == "database": database_page(event)
        elif st.session_state.subpage == "hall": hall_page(event)

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

def attendance_page(event):
    st.header("📸 Live Attendance")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**📷 Webcam**")
        img_buffer = st.camera_input("Take photo")
        
        if img_buffer:
            # Check if this is a new photo
            bytes_data = img_buffer.getvalue()
            if st.session_state.last_photo_hash != bytes_data:
                st.session_state.last_photo_hash = bytes_data
                
                # New photo - Process it
                with st.spinner("🔍 Detecting faces..."):
                    image = Image.open(img_buffer)
                    # Load known faces for dedup check (optional, if implemented in engine)
                    # st.session_state.face_engine.load_known_faces({st.session_state.current_event: event})
                    
                    faces = st.session_state.face_engine.process_image(image)
                    st.session_state.detected_faces = faces
                    st.session_state.current_face_idx = 0
            
            # Use detected faces
            faces = st.session_state.detected_faces
            current_idx = st.session_state.current_face_idx
            original_image = Image.open(img_buffer)
            
            if not faces:
                st.warning("⚠️ No faces detected! Try again.")
                st.image(original_image, use_column_width=True)
            elif current_idx >= len(faces):
                st.success("✅ All faces processed for this photo!")
                st.image(draw_faces(original_image, faces, -1), use_column_width=True)
                if st.button("📸 Next Photo"):
                    # Clear state for next photo
                    st.session_state.last_photo_hash = None
                    st.session_state.detected_faces = []
                    st.rerun()
            else:
                # Registration in progress
                st.info(f"📝 Registering Person {current_idx + 1} of {len(faces)}")
                
                # Draw boxes
                display_img = draw_faces(original_image, faces, current_idx)
                st.image(display_img, caption=f"Processing P{current_idx+1}", use_column_width=True)
                
                # Current person details
                face = faces[current_idx]
                seat = f"Row A, Seat {len(event['data']) % event['hall_cols'] + 1}" # Simple seat logic
                
                with st.form(key=f"reg_form_{current_idx}"):
                    # Show cropped face for clarity
                    top, right, bottom, left = face['bbox']
                    # Ensure bbox is within bounds
                    top, left = max(0, top), max(0, left)
                    bottom, right = min(original_image.height, bottom), min(original_image.width, right)
                    
                    face_crop = original_image.crop((left, top, right, bottom))
                    st.image(face_crop, caption="Current Person", width=150)
                    
                    st.write(f"**Details for P{current_idx+1}:**")
                    col_a, col_b = st.columns(2)
                    col_a.metric("Gender", face['gender'])
                    col_b.metric("Confidence", f"{face['confidence']:.1f}%" if isinstance(face['confidence'], (int, float)) else "N/A")
                    
                    name = st.text_input("Name", key=f"name_input_{current_idx}")
                    
                    if st.form_submit_button("✅ Register & Next"):
                        if name:
                            # Save data
                            event["data"].append({
                                "sl_no": len(event["data"])+1,
                                "name": name,
                                "gender": face['gender'],
                                "seat": seat,
                                "encoding": face['encoding'] # Store encoding for future duplicate checks
                            })
                            st.success(f"✅ Saved {name}!")
                            st.session_state.current_face_idx += 1
                            st.rerun()
                        else:
                            st.error("⚠️ Please enter a name.")
    
    with col2:
        st.markdown("### 📋 Session Log")
        if event["data"]:
            df = pd.DataFrame(event["data"])
            st.dataframe(df.iloc[::-1].head(5)[['name', 'gender', 'seat']], hide_index=True)
        else:
            st.info("No registrations yet.")
            
    # Back button
    if st.button("⬅️ Back to Dashboard"): 
        st.session_state.subpage = None; st.rerun()

def dashboard_page(event):
    st.header("📊 Equality Dashboard")
    if event["data"]:
        df = pd.DataFrame(event["data"])
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(df))
        col2.metric("Male", len(df[df["gender"]=="Male"]))
        col3.metric("Female", len(df[df["gender"]=="Female"]))
        st.dataframe(df[['sl_no','gender','seat']].head(10))
        st.download_button("📥 CSV", df.to_csv(index=False), "report.csv")
    if st.button("⬅️ Back to Dashboard"): st.session_state.subpage = None; st.rerun()

def database_page(event):
    st.header("📋 Database")
    if event["data"]: st.dataframe(pd.DataFrame(event["data"]))
    if st.button("⬅️ Back to Dashboard"): st.session_state.subpage = None; st.rerun()

def hall_page(event):
    st.header("🎯 Hall Setup")
    event["hall_rows"] = st.number_input("Rows", value=event["hall_rows"])
    event["hall_cols"] = st.number_input("Columns", value=event["hall_cols"])
    if st.button("⬅️ Back to Dashboard"): st.session_state.subpage = None; st.rerun()

def events_list():
    st.header("📂 Events")
    for event_id, event in st.session_state.events.items():
        if st.button(f"📋 {event['name']} ({len(event['data'])} participants)"):
            st.session_state.current_event = event_id
            st.session_state.page = "event_dashboard"
            st.rerun()
    back_button("home")

# ROUTING
if st.session_state.page == "login": login()
elif st.session_state.page == "home": home()
elif st.session_state.page == "create_event": create_event()
elif st.session_state.page == "create_folder": create_folder()
elif st.session_state.page == "events_list": events_list()
elif st.session_state.page == "main_folders_list": main_folders_list()
elif st.session_state.page == "event_dashboard": event_dashboard()
