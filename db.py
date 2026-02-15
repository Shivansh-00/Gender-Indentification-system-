"""
Database layer for EquiVision — In-Memory Local Backend
All CRUD operations for users, events, attendees, folders.
No external database required. Data persists for the lifetime of the server process.
"""
import hashlib
import json
import uuid
from datetime import datetime

# ══════════════════════════════════════════════
#  IN-MEMORY STORES  (persist across reruns)
# ══════════════════════════════════════════════
_users = {}          # id -> {id, username, password_hash}
_events = {}         # id -> {id, user_id, name, password, hall_rows, hall_cols, cluster_size, date, team_members, roles, folder_id}
_attendees = {}      # auto-inc id -> {id, event_id, ...}
_folders = {}        # id -> {id, user_id, name, date}
_folder_events = []  # [{folder_id, event_id}]
_attendee_counter = 0


def _hash_password(password: str) -> str:
    """Simple SHA-256 hash for passwords."""
    return hashlib.sha256(password.encode()).hexdigest()


def _next_attendee_id():
    global _attendee_counter
    _attendee_counter += 1
    return _attendee_counter

# --------------- USERS ---------------

def create_user(username: str, password: str) -> dict | None:
    """Register a new user. Returns user dict or None on failure."""
    # Check duplicate username
    for u in _users.values():
        if u['username'] == username:
            return None  # Username taken
    uid = str(uuid.uuid4())
    user = {"id": uid, "username": username, "password_hash": _hash_password(password)}
    _users[uid] = user
    return user


def authenticate(username: str, password: str) -> dict | None:
    """Check credentials. Returns user dict or None."""
    ph = _hash_password(password)
    for u in _users.values():
        if u['username'] == username and u['password_hash'] == ph:
            return u
    return None


def get_user_by_id(user_id: str) -> dict | None:
    """Fetch user by ID."""
    return _users.get(user_id)

# --------------- EVENTS ---------------

def create_event(user_id: str, event_id: str, name: str, password: str,
                 hall_rows: int, hall_cols: int, cluster_size: int = 1,
                 folder_id: str = None) -> dict | None:
    """Insert a new event."""
    data = {
        "id": event_id,
        "user_id": user_id,
        "name": name,
        "password": password,
        "hall_rows": hall_rows,
        "hall_cols": hall_cols,
        "cluster_size": cluster_size,
        "date": str(datetime.now()),
        "team_members": "[]",
        "roles": "{}",
        "folder_id": folder_id,
    }
    _events[event_id] = data
    return data


def get_events(user_id: str) -> list:
    """Fetch all events for a user."""
    return [e for e in _events.values() if e['user_id'] == user_id]


def get_event_by_id(event_id: str) -> dict | None:
    """Fetch single event."""
    return _events.get(event_id)


def update_event(event_id: str, updates: dict):
    """Update event fields."""
    if event_id in _events:
        _events[event_id].update(updates)


def delete_event(event_id: str):
    """Delete event and its attendees."""
    # Remove attendees
    to_del = [aid for aid, a in _attendees.items() if a['event_id'] == event_id]
    for aid in to_del:
        del _attendees[aid]
    # Remove event
    _events.pop(event_id, None)

# --------------- ATTENDEES ---------------

def add_attendee(event_id: str, record: dict) -> dict | None:
    """Insert an attendee record."""
    encoding = record.get('encoding', [])
    if hasattr(encoding, 'tolist'):
        encoding = encoding.tolist()

    aid = _next_attendee_id()
    data = {
        "id": aid,
        "event_id": event_id,
        "name": record.get('name', ''),
        "gender": record.get('gender', ''),
        "seat": record.get('seat', ''),
        "student_id": record.get('id', ''),
        "branch": record.get('branch', ''),
        "age": int(record.get('age', 0)),
        "encoding": json.dumps(encoding),
        "timestamp": record.get('timestamp', str(datetime.now())),
    }
    _attendees[aid] = data
    return data


def get_attendees(event_id: str) -> list:
    """Fetch all attendees for an event. Parses encoding back from JSON."""
    formatted = []
    for a in _attendees.values():
        if a['event_id'] != event_id:
            continue
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
            'timestamp': a.get('timestamp', ''),
        })
    return formatted


def delete_attendee(attendee_db_id: int):
    """Delete a single attendee by DB id."""
    _attendees.pop(attendee_db_id, None)


def clear_attendees(event_id: str):
    """Delete all attendees for an event."""
    to_del = [aid for aid, a in _attendees.items() if a['event_id'] == event_id]
    for aid in to_del:
        del _attendees[aid]

# --------------- FOLDERS ---------------

def create_folder(user_id: str, name: str) -> dict | None:
    """Create a folder."""
    fid = str(uuid.uuid4())
    data = {"id": fid, "user_id": user_id, "name": name, "date": str(datetime.now())}
    _folders[fid] = data
    return data


def get_folders(user_id: str) -> list:
    """Fetch all folders for a user."""
    return [f for f in _folders.values() if f['user_id'] == user_id]


def add_event_to_folder(folder_id: str, event_id: str):
    """Link an event to a folder."""
    _folder_events.append({"folder_id": folder_id, "event_id": event_id})


def get_folder_events(folder_id: str) -> list:
    """Get all event IDs in a folder."""
    return [r['event_id'] for r in _folder_events if r['folder_id'] == folder_id]

# --------------- TEAM MEMBERS ---------------

def save_team_members(event_id: str, members: list):
    """Save team members as JSON in event record."""
    if event_id in _events:
        _events[event_id]["team_members"] = json.dumps(members)


def get_team_members(event_id: str) -> list:
    """Get team members from event record."""
    if event_id in _events:
        tm = _events[event_id].get("team_members", "[]")
        if isinstance(tm, str):
            try:
                return json.loads(tm)
            except:
                return []
        return tm if isinstance(tm, list) else []
    return []


def save_roles(event_id: str, roles: list):
    """Save roles as JSON in event record."""
    if event_id in _events:
        _events[event_id]["roles"] = json.dumps(roles)


def get_roles(event_id: str) -> list:
    """Get roles from event record."""
    if event_id in _events:
        r = _events[event_id].get("roles", "[]")
        if isinstance(r, str):
            try:
                return json.loads(r)
            except:
                return []
        return r if isinstance(r, list) else []
    return []
