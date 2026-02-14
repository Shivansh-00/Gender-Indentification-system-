"""
Database layer for EquiVision — Supabase (Cloud PostgreSQL)
All CRUD operations for users, events, attendees, folders.
"""
import streamlit as st
import hashlib
import json
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

# --------------- INIT ---------------

@st.cache_resource
def get_supabase_client():
    """Create and cache the Supabase client."""
    if create_client is None:
        st.error("supabase package not installed. Run: pip install supabase")
        return None
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

def _hash_password(password: str) -> str:
    """Simple SHA-256 hash for passwords."""
    return hashlib.sha256(password.encode()).hexdigest()

# --------------- USERS ---------------

def create_user(username: str, password: str) -> dict | None:
    """Register a new user. Returns user dict or None on failure."""
    sb = get_supabase_client()
    if not sb: return None
    try:
        result = sb.table("users").insert({
            "username": username,
            "password_hash": _hash_password(password)
        }).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return None  # Username taken
        raise
    return None

def authenticate(username: str, password: str) -> dict | None:
    """Check credentials. Returns user dict or None."""
    sb = get_supabase_client()
    if not sb: return None
    try:
        result = sb.table("users").select("*").eq(
            "username", username
        ).eq(
            "password_hash", _hash_password(password)
        ).execute()
        if result.data:
            return result.data[0]
    except:
        pass
    return None

def get_user_by_id(user_id: str) -> dict | None:
    """Fetch user by ID."""
    sb = get_supabase_client()
    if not sb: return None
    try:
        result = sb.table("users").select("*").eq("id", user_id).execute()
        if result.data:
            return result.data[0]
    except:
        pass
    return None

# --------------- EVENTS ---------------

def create_event(user_id: str, event_id: str, name: str, password: str, 
                 hall_rows: int, hall_cols: int, cluster_size: int = 1,
                 folder_id: str = None) -> dict | None:
    """Insert a new event."""
    sb = get_supabase_client()
    if not sb: return None
    try:
        data = {
            "id": event_id,
            "user_id": user_id,
            "name": name,
            "password": password,
            "hall_rows": hall_rows,
            "hall_cols": hall_cols,
            "cluster_size": cluster_size,
            "date": str(datetime.now()),
        }
        if folder_id:
            data["folder_id"] = folder_id
        result = sb.table("events").insert(data).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        st.error(f"DB Error (create_event): {e}")
    return None

def get_events(user_id: str) -> list:
    """Fetch all events for a user."""
    sb = get_supabase_client()
    if not sb: return []
    try:
        result = sb.table("events").select("*").eq("user_id", user_id).execute()
        return result.data or []
    except:
        return []

def get_event_by_id(event_id: str) -> dict | None:
    """Fetch single event."""
    sb = get_supabase_client()
    if not sb: return None
    try:
        result = sb.table("events").select("*").eq("id", event_id).execute()
        if result.data:
            return result.data[0]
    except:
        pass
    return None

def update_event(event_id: str, updates: dict):
    """Update event fields."""
    sb = get_supabase_client()
    if not sb: return
    try:
        sb.table("events").update(updates).eq("id", event_id).execute()
    except Exception as e:
        st.error(f"DB Error (update_event): {e}")

def delete_event(event_id: str):
    """Delete event and its attendees."""
    sb = get_supabase_client()
    if not sb: return
    try:
        sb.table("attendees").delete().eq("event_id", event_id).execute()
        sb.table("events").delete().eq("id", event_id).execute()
    except Exception as e:
        st.error(f"DB Error (delete_event): {e}")

# --------------- ATTENDEES ---------------

def add_attendee(event_id: str, record: dict) -> dict | None:
    """Insert an attendee record. Converts encoding to JSON string."""
    sb = get_supabase_client()
    if not sb: return None
    try:
        # Encoding is a list of floats — store as JSON
        encoding = record.get('encoding', [])
        if hasattr(encoding, 'tolist'):
            encoding = encoding.tolist()
        
        data = {
            "event_id": event_id,
            "name": record.get('name', ''),
            "gender": record.get('gender', ''),
            "seat": record.get('seat', ''),
            "student_id": record.get('id', ''),
            "branch": record.get('branch', ''),
            "age": int(record.get('age', 0)),
            "encoding": json.dumps(encoding),
            "timestamp": record.get('timestamp', str(datetime.now()))
        }
        result = sb.table("attendees").insert(data).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        st.error(f"DB Error (add_attendee): {e}")
    return None

def get_attendees(event_id: str) -> list:
    """Fetch all attendees for an event. Parses encoding back from JSON."""
    sb = get_supabase_client()
    if not sb: return []
    try:
        result = sb.table("attendees").select("*").eq("event_id", event_id).execute()
        attendees = result.data or []
        
        # Convert back to app format
        formatted = []
        for a in attendees:
            enc = a.get('encoding', '[]')
            if isinstance(enc, str):
                try:
                    enc = json.loads(enc)
                except:
                    enc = []
            
            formatted.append({
                'sl_no': a.get('id', 0),
                'name': a.get('name', ''),
                'gender': a.get('gender', ''),
                'seat': a.get('seat', ''),
                'id': a.get('student_id', ''),
                'branch': a.get('branch', ''),
                'age': a.get('age', 0),
                'encoding': enc,
                'timestamp': a.get('timestamp', '')
            })
        return formatted
    except Exception as e:
        st.error(f"DB Error (get_attendees): {e}")
        return []

def delete_attendee(attendee_db_id: int):
    """Delete a single attendee by DB id."""
    sb = get_supabase_client()
    if not sb: return
    try:
        sb.table("attendees").delete().eq("id", attendee_db_id).execute()
    except:
        pass

def clear_attendees(event_id: str):
    """Delete all attendees for an event."""
    sb = get_supabase_client()
    if not sb: return
    try:
        sb.table("attendees").delete().eq("event_id", event_id).execute()
    except:
        pass

# --------------- FOLDERS ---------------

def create_folder(user_id: str, name: str) -> dict | None:
    """Create a folder."""
    sb = get_supabase_client()
    if not sb: return None
    try:
        result = sb.table("folders").insert({
            "user_id": user_id,
            "name": name,
            "date": str(datetime.now())
        }).execute()
        if result.data:
            return result.data[0]
    except Exception as e:
        st.error(f"DB Error (create_folder): {e}")
    return None

def get_folders(user_id: str) -> list:
    """Fetch all folders for a user."""
    sb = get_supabase_client()
    if not sb: return []
    try:
        result = sb.table("folders").select("*").eq("user_id", user_id).execute()
        return result.data or []
    except:
        return []

def add_event_to_folder(folder_id: str, event_id: str):
    """Link an event to a folder."""
    sb = get_supabase_client()
    if not sb: return
    try:
        sb.table("folder_events").insert({
            "folder_id": folder_id,
            "event_id": event_id
        }).execute()
    except:
        pass

def get_folder_events(folder_id: str) -> list:
    """Get all event IDs in a folder."""
    sb = get_supabase_client()
    if not sb: return []
    try:
        result = sb.table("folder_events").select("event_id").eq("folder_id", folder_id).execute()
        return [r['event_id'] for r in (result.data or [])]
    except:
        return []

# --------------- TEAM MEMBERS ---------------

def save_team_members(event_id: str, members: list):
    """Save team members as JSON in event record."""
    sb = get_supabase_client()
    if not sb: return
    try:
        sb.table("events").update({
            "team_members": json.dumps(members)
        }).eq("id", event_id).execute()
    except Exception as e:
        st.error(f"DB Error (save_team_members): {e}")

def get_team_members(event_id: str) -> list:
    """Get team members from event record."""
    sb = get_supabase_client()
    if not sb: return []
    try:
        result = sb.table("events").select("team_members").eq("id", event_id).execute()
        if result.data and result.data[0].get('team_members'):
            tm = result.data[0]['team_members']
            if isinstance(tm, str):
                return json.loads(tm)
            return tm
    except:
        pass
    return []

def save_roles(event_id: str, roles: list):
    """Save roles as JSON in event record."""
    sb = get_supabase_client()
    if not sb: return
    try:
        sb.table("events").update({
            "roles": json.dumps(roles)
        }).eq("id", event_id).execute()
    except Exception as e:
        st.error(f"DB Error (save_roles): {e}")

def get_roles(event_id: str) -> list:
    """Get roles from event record."""
    sb = get_supabase_client()
    if not sb: return []
    try:
        result = sb.table("events").select("roles").eq("id", event_id).execute()
        if result.data and result.data[0].get('roles'):
            r = result.data[0]['roles']
            if isinstance(r, str):
                return json.loads(r)
            return r
    except:
        pass
    return []
