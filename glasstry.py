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
import tempfile
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

import db  # Supabase database layer

# --- STATE INITIALIZATION ---
if 'face_engine' not in st.session_state: st.session_state.face_engine = FaceEngine()
if 'main_folders' not in st.session_state: st.session_state.main_folders = {}
if 'events' not in st.session_state: st.session_state.events = {} 
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'page' not in st.session_state: st.session_state.page = "login"
if 'current_event' not in st.session_state: st.session_state.current_event = None
if 'subpage' not in st.session_state: st.session_state.subpage = None
if 'auth_stage' not in st.session_state: st.session_state.auth_stage = 0
if 'verification_code' not in st.session_state: st.session_state.verification_code = None
if 'upload_key' not in st.session_state: st.session_state.upload_key = 0
if 'db_loaded' not in st.session_state: st.session_state.db_loaded = False

def load_from_db():
    """Sync events and folders from Supabase into session state."""
    uid = st.session_state.user_id
    if not uid: return
    
    # Load events
    events_raw = db.get_events(uid)
    for e in events_raw:
        eid = e['id']
        if eid not in st.session_state.events:
            tm = e.get('team_members', '[]')
            if isinstance(tm, str):
                try: tm = __import__('json').loads(tm)
                except: tm = []
            elif tm is None: tm = []
            
            rl = e.get('roles', '[]')
            if isinstance(rl, str):
                try: rl = __import__('json').loads(rl)
                except: rl = {}
            elif rl is None: rl = {}
            
            st.session_state.events[eid] = {
                'name': e.get('name', ''),
                'date': e.get('date', ''),
                'password': e.get('password', ''),
                'hall_rows': e.get('hall_rows', 5),
                'hall_cols': e.get('hall_cols', 10),
                'cluster_size': e.get('cluster_size', 1),
                'data': db.get_attendees(eid),
                'roles': rl if isinstance(rl, dict) else {},
                'team_members': tm if isinstance(tm, list) else []
            }
    
    # Load folders
    folders_raw = db.get_folders(uid)
    for f in folders_raw:
        fname = f.get('name', '')
        if fname not in st.session_state.main_folders:
            folder_event_ids = db.get_folder_events(f['id'])
            st.session_state.main_folders[fname] = {
                'date': f.get('date', ''),
                'events': folder_event_ids,
                'db_id': f['id']
            }
    
    st.session_state.db_loaded = True

st.set_page_config(page_title="Gender Attendance AI", layout="wide")

# --- CSS STYLES ---
def local_css():
    st.markdown("""
    <style>
        /* ═══════════════════════════════════════════════════════════════════
           EQUIVISION — ULTRA-PREMIUM DESIGN SYSTEM v5.0
           World-class glassmorphic interface with cinematic depth
           ═══════════════════════════════════════════════════════════════════ */

        /* FONT STACK — Optimized loading with display swap */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');

        /* ══════════════ DESIGN TOKENS ══════════════ */
        :root {
            /* Primary spectrum */
            --primary: #7C5CFC;
            --primary-50: rgba(124, 92, 252, 0.05);
            --primary-100: rgba(124, 92, 252, 0.10);
            --primary-200: #C4B5FD;
            --primary-300: #A78BFA;
            --primary-400: #8B6FF8;
            --primary-500: #7C5CFC;
            --primary-600: #6D4AE6;
            --primary-700: #5B34E8;
            --primary-800: #4C1D95;
            --primary-glow: rgba(124, 92, 252, 0.35);
            --primary-glow-soft: rgba(124, 92, 252, 0.12);

            /* Secondary spectrum */
            --secondary: #34D399;
            --secondary-100: rgba(52, 211, 153, 0.10);
            --secondary-300: #6EE7B7;
            --secondary-500: #34D399;
            --secondary-700: #059669;
            --secondary-glow: rgba(52, 211, 153, 0.25);

            /* Accent spectrum */
            --accent: #F59E0B;
            --accent-300: #FCD34D;
            --accent-glow: rgba(245, 158, 11, 0.15);

            /* Rose spectrum (for female indicators) */
            --rose-400: #FB7185;
            --rose-500: #F43F5E;
            --rose-600: #E11D48;
            --rose-glow: rgba(244, 63, 94, 0.25);

            /* Sky spectrum (for other indicators) */
            --sky-400: #38BDF8;
            --sky-500: #0EA5E9;
            --sky-glow: rgba(56, 189, 248, 0.25);

            /* Surfaces — Deep space palette */
            --bg-void: #060810;
            --bg-deep: #0A0D16;
            --bg-base: #0F1219;
            --bg-elevated: #151922;
            --bg-surface: #1A1F2B;
            --bg-card: rgba(255, 255, 255, 0.022);
            --bg-card-hover: rgba(255, 255, 255, 0.048);
            --bg-card-active: rgba(124, 92, 252, 0.06);
            --bg-input: rgba(0, 0, 0, 0.28);
            --bg-input-hover: rgba(0, 0, 0, 0.35);
            --bg-input-focus: rgba(0, 0, 0, 0.42);

            /* Text hierarchy */
            --text-primary: #F1F5F9;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --text-faint: #475569;
            --text-inverse: #0F172A;

            /* Borders */
            --border-invisible: rgba(255, 255, 255, 0.03);
            --border-subtle: rgba(255, 255, 255, 0.055);
            --border-default: rgba(255, 255, 255, 0.085);
            --border-hover: rgba(124, 92, 252, 0.3);
            --border-focus: rgba(124, 92, 252, 0.5);
            --border-active: rgba(124, 92, 252, 0.6);

            /* Radii */
            --radius-xs: 6px;
            --radius-sm: 10px;
            --radius-md: 16px;
            --radius-lg: 22px;
            --radius-xl: 30px;
            --radius-2xl: 40px;
            --radius-full: 9999px;

            /* Shadows — Layered depth system */
            --shadow-xs: 0 1px 3px rgba(0,0,0,0.12);
            --shadow-sm: 0 2px 8px rgba(0,0,0,0.18), 0 1px 2px rgba(0,0,0,0.08);
            --shadow-md: 0 6px 24px rgba(0,0,0,0.22), 0 2px 6px rgba(0,0,0,0.12);
            --shadow-lg: 0 12px 40px rgba(0,0,0,0.28), 0 4px 12px rgba(0,0,0,0.15);
            --shadow-xl: 0 20px 60px rgba(0,0,0,0.35), 0 8px 20px rgba(0,0,0,0.18);
            --shadow-glow-purple: 0 0 30px var(--primary-glow-soft), 0 0 60px rgba(124, 92, 252, 0.05);
            --shadow-glow-green: 0 0 30px var(--secondary-100), 0 0 60px rgba(52, 211, 153, 0.05);
            --shadow-card: 0 4px 20px rgba(0,0,0,0.18), 0 1px 3px rgba(0,0,0,0.1), inset 0 1px 0 rgba(255,255,255,0.03);
            --shadow-card-hover: 0 16px 48px rgba(124, 92, 252, 0.12), 0 6px 16px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.06);

            /* Transitions */
            --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
            --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
            --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
            --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
            --duration-instant: 0.08s;
            --duration-fast: 0.15s;
            --duration-normal: 0.28s;
            --duration-slow: 0.45s;
            --duration-glacial: 0.7s;

            /* Glass */
            --glass-blur: 24px;
            --glass-saturate: 1.8;
            --glass-bg: rgba(255, 255, 255, 0.025);
            --glass-border: rgba(255, 255, 255, 0.06);
        }

        /* ══════════════ GLOBAL FOUNDATION ══════════════ */
        html {
            scroll-behavior: smooth;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
            font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
        }

        body, .stApp {
            background-color: var(--bg-void) !important;
            color: var(--text-primary);
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-weight: 400;
            line-height: 1.65;
            font-size: 15px;
        }

        /* Deep space ambient mesh — multi-layer */
        .stApp {
            background-image:
                radial-gradient(ellipse 90% 70% at 3% 3%, rgba(124, 92, 252, 0.07) 0%, transparent 55%),
                radial-gradient(ellipse 70% 55% at 97% 8%, rgba(52, 211, 153, 0.05) 0%, transparent 50%),
                radial-gradient(ellipse 55% 45% at 50% 97%, rgba(245, 158, 11, 0.035) 0%, transparent 45%),
                radial-gradient(ellipse 45% 35% at 75% 55%, rgba(124, 92, 252, 0.025) 0%, transparent 45%),
                radial-gradient(ellipse 35% 25% at 20% 70%, rgba(244, 63, 94, 0.02) 0%, transparent 40%),
                radial-gradient(ellipse 60% 40% at 40% 30%, rgba(56, 189, 248, 0.015) 0%, transparent 45%);
            background-attachment: fixed;
        }

        /* Animated nebula overlay */
        .stApp::before {
            content: '';
            position: fixed;
            inset: 0;
            background:
                radial-gradient(circle 700px at 15% 25%, rgba(124, 92, 252, 0.035) 0%, transparent 100%),
                radial-gradient(circle 500px at 85% 65%, rgba(52, 211, 153, 0.025) 0%, transparent 100%),
                radial-gradient(circle 350px at 50% 90%, rgba(244, 63, 94, 0.015) 0%, transparent 100%);
            pointer-events: none;
            z-index: 0;
            animation: nebulaBreath 25s ease-in-out infinite alternate;
            will-change: transform;
        }

        @keyframes nebulaBreath {
            0% { transform: translate3d(0, 0, 0) scale(1) rotate(0deg); opacity: 1; }
            33% { transform: translate3d(-1.5%, 0.8%, 0) scale(1.015) rotate(0.3deg); opacity: 0.9; }
            66% { transform: translate3d(0.8%, -0.5%, 0) scale(1.01) rotate(-0.2deg); opacity: 0.95; }
            100% { transform: translate3d(0.5%, -0.8%, 0) scale(1.005) rotate(0.1deg); opacity: 1; }
        }

        /* Grain texture overlay for cinematic depth */
        .stApp::after {
            content: '';
            position: fixed;
            inset: 0;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.015'/%3E%3C/svg%3E");
            pointer-events: none;
            z-index: 0;
            opacity: 0.4;
            mix-blend-mode: overlay;
        }

        /* ══════════════ SCROLLBAR ══════════════ */
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, var(--primary-500) 0%, var(--secondary-500) 100%);
            border-radius: var(--radius-full);
        }
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, var(--primary-400) 0%, var(--secondary-300) 100%);
        }
        * { scrollbar-width: thin; scrollbar-color: var(--primary-500) transparent; }

        /* ══════════════ TYPOGRAPHY ══════════════ */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.03em;
            background: linear-gradient(140deg, #FFFFFF 0%, #E2E8F0 35%, var(--primary-300) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.6rem !important;
            line-height: 1.2 !important;
            position: relative;
        }

        h1 {
            font-weight: 900 !important;
            font-size: 2.4rem !important;
            letter-spacing: -0.04em;
            background: linear-gradient(140deg, #FFFFFF 0%, var(--primary-300) 45%, var(--secondary-300) 100%);
            -webkit-background-clip: text;
            background-clip: text;
            animation: h1Breathe 7s ease-in-out infinite;
            will-change: transform;
            filter: drop-shadow(0 0 20px rgba(124, 92, 252, 0.08));
        }

        h2 { font-size: 1.7rem !important; font-weight: 800 !important; }
        h3 { font-size: 1.35rem !important; font-weight: 700 !important; }
        h4 { font-size: 1.15rem !important; }

        @keyframes h1Breathe {
            0%, 100% { transform: translate3d(0, 0, 0); filter: drop-shadow(0 0 20px rgba(124, 92, 252, 0.08)); }
            50% { transform: translate3d(0, -3px, 0); filter: drop-shadow(0 0 30px rgba(124, 92, 252, 0.15)); }
        }

        p, span, label, .stMarkdown { color: var(--text-secondary); }

        /* ══════════════ GLASSMORPHIC CARD SYSTEM ══════════════ */
        .card,
        [data-testid="stMetric"],
        [data-testid="stExpander"],
        div.stDataFrame,
        div[data-testid="stForm"],
        div[data-testid="stSidebar"] {
            background: var(--glass-bg) !important;
            backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
            -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate)) !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: var(--radius-lg) !important;
            box-shadow: var(--shadow-card) !important;
            transition:
                transform var(--duration-normal) var(--ease-out),
                box-shadow var(--duration-slow) var(--ease-out),
                border-color var(--duration-normal) var(--ease-smooth),
                background var(--duration-normal) var(--ease-smooth);
            position: relative;
            overflow: hidden;
        }

        /* Top edge specular highlight */
        .card::before,
        [data-testid="stMetric"]::before,
        [data-testid="stExpander"]::before,
        div[data-testid="stForm"]::before {
            content: '';
            position: absolute;
            top: 0; left: 8%; right: 8%;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), rgba(255,255,255,0.15), rgba(255,255,255,0.1), transparent);
            pointer-events: none;
            z-index: 1;
        }

        /* Bottom edge subtle shadow line */
        .card::after,
        [data-testid="stMetric"]::after {
            content: '';
            position: absolute;
            bottom: 0; left: 15%; right: 15%;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(0,0,0,0.15), transparent);
            pointer-events: none;
        }

        .card:hover,
        [data-testid="stMetric"]:hover,
        [data-testid="stExpander"]:hover {
            transform: translate3d(0, -3px, 0);
            background: var(--bg-card-hover) !important;
            box-shadow: var(--shadow-card-hover) !important;
            border-color: var(--border-hover) !important;
        }

        .card:hover::before,
        [data-testid="stMetric"]:hover::before {
            background: linear-gradient(90deg, transparent, rgba(124, 92, 252, 0.15), rgba(124, 92, 252, 0.25), rgba(124, 92, 252, 0.15), transparent);
        }

        /* ── METRIC CARDS ── */
        [data-testid="stMetric"] {
            padding: 1.6rem 1.4rem;
            text-align: center;
            background: linear-gradient(160deg, var(--glass-bg), rgba(124, 92, 252, 0.015)) !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.7rem;
            color: var(--text-muted) !important;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            font-weight: 600;
            font-family: 'Space Grotesk', sans-serif;
            margin-bottom: 0.3rem;
        }

        [data-testid="stMetricValue"] {
            font-size: 2.1rem !important;
            font-weight: 800 !important;
            font-family: 'Inter', sans-serif !important;
            background: linear-gradient(140deg, #FFFFFF, var(--primary-300));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            filter: drop-shadow(0 0 8px rgba(124, 92, 252, 0.1));
        }

        [data-testid="stMetricDelta"] {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.75rem !important;
        }

        /* ══════════════ BUTTONS — Premium Interactive System ══════════════ */
        div.stButton > button {
            background: linear-gradient(140deg, var(--primary-500) 0%, var(--primary-700) 100%) !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: var(--radius-md) !important;
            padding: 0.72rem 1.6rem !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.015em !important;
            box-shadow:
                0 4px 14px rgba(124, 92, 252, 0.2),
                0 1px 3px rgba(0,0,0,0.12),
                inset 0 1px 0 rgba(255,255,255,0.12) !important;
            transition:
                transform var(--duration-normal) var(--ease-spring),
                box-shadow var(--duration-normal) var(--ease-out),
                border-color var(--duration-fast) ease,
                filter var(--duration-normal) ease !important;
            position: relative;
            overflow: hidden;
            width: 100%;
            cursor: pointer;
            will-change: transform;
            -webkit-tap-highlight-color: transparent;
        }

        /* Shimmer sweep on hover */
        div.stButton > button::before {
            content: '';
            position: absolute;
            top: 0; left: -200%;
            width: 80%; height: 100%;
            background: linear-gradient(
                105deg,
                transparent 25%,
                rgba(255,255,255,0.06) 38%,
                rgba(255,255,255,0.15) 46%,
                rgba(255,255,255,0.2) 50%,
                rgba(255,255,255,0.15) 54%,
                rgba(255,255,255,0.06) 62%,
                transparent 75%
            );
            transition: left 0.7s var(--ease-out);
            pointer-events: none;
        }

        /* Inner glow ring on hover */
        div.stButton > button::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            opacity: 0;
            background: radial-gradient(circle at 50% 0%, rgba(255,255,255,0.12) 0%, transparent 60%);
            transition: opacity var(--duration-normal) ease;
            pointer-events: none;
        }

        div.stButton > button:hover {
            transform: translate3d(0, -2px, 0) scale(1.012);
            box-shadow:
                0 8px 28px rgba(124, 92, 252, 0.3),
                0 3px 10px rgba(0,0,0,0.15),
                inset 0 1px 0 rgba(255,255,255,0.18) !important;
            border-color: rgba(255,255,255,0.22) !important;
            filter: brightness(1.05);
        }

        div.stButton > button:hover::before { left: 200%; }
        div.stButton > button:hover::after { opacity: 1; }

        div.stButton > button:active {
            transform: translate3d(0, 0, 0) scale(0.975);
            transition-duration: var(--duration-instant);
            box-shadow: 0 2px 8px rgba(124, 92, 252, 0.2), inset 0 2px 4px rgba(0,0,0,0.15) !important;
            filter: brightness(0.95);
        }

        /* ── FORM CONTAINERS ── */
        div[data-testid="stForm"] {
            padding: 1.75rem !important;
            border: 1px solid var(--border-subtle) !important;
            background: linear-gradient(165deg, var(--glass-bg), rgba(124, 92, 252, 0.01)) !important;
        }

        /* ══════════════ INPUT FIELDS — Refined Interaction ══════════════ */
        .stTextInput > div > div > input,
        .stDateInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > div,
        .stMultiSelect > div > div > div,
        .stTextArea textarea {
            background-color: var(--bg-input) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-default) !important;
            border-radius: var(--radius-sm) !important;
            padding: 0.65rem 1rem !important;
            font-family: 'Outfit', sans-serif !important;
            font-size: 0.9rem !important;
            transition:
                border-color var(--duration-fast) ease,
                box-shadow var(--duration-fast) ease,
                background-color var(--duration-fast) ease !important;
        }

        .stTextInput > div > div > input:hover,
        .stDateInput > div > div > input:hover,
        .stNumberInput > div > div > input:hover,
        .stTextArea textarea:hover {
            background-color: var(--bg-input-hover) !important;
            border-color: var(--border-hover) !important;
        }

        .stTextInput > div > div > input:focus,
        .stDateInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea textarea:focus {
            border-color: var(--primary-500) !important;
            box-shadow: 0 0 0 3px var(--primary-glow-soft), 0 0 24px rgba(124, 92, 252, 0.06) !important;
            background-color: var(--bg-input-focus) !important;
            outline: none !important;
        }

        /* Input labels */
        .stTextInput label, .stSelectbox label, .stNumberInput label,
        .stDateInput label, .stMultiSelect label, .stTextArea label {
            font-weight: 500 !important;
            color: var(--text-secondary) !important;
            font-size: 0.82rem !important;
            letter-spacing: 0.015em;
            font-family: 'Space Grotesk', sans-serif !important;
        }

        /* ══════════════ RADIO / TOGGLE ══════════════ */
        .stRadio > div { gap: 0.35rem; }

        .stRadio > div > label {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: var(--radius-sm) !important;
            padding: 0.55rem 1.1rem !important;
            transition: all var(--duration-fast) var(--ease-smooth) !important;
            cursor: pointer;
        }

        .stRadio > div > label:hover {
            border-color: var(--border-hover) !important;
            background: var(--bg-card-hover) !important;
            transform: translate3d(0, -1px, 0);
            box-shadow: 0 4px 12px rgba(124, 92, 252, 0.08);
        }

        /* ══════════════ TABS — Segmented Control ══════════════ */
        .stTabs [data-baseweb="tab-list"] {
            gap: 3px;
            background: rgba(0, 0, 0, 0.2) !important;
            border-radius: var(--radius-md) !important;
            padding: 4px !important;
            border: 1px solid var(--border-subtle) !important;
            backdrop-filter: blur(12px);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: var(--radius-sm) !important;
            font-weight: 500 !important;
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 0.82rem !important;
            padding: 0.55rem 1.3rem !important;
            color: var(--text-muted) !important;
            transition: all var(--duration-fast) var(--ease-smooth) !important;
            border: 1px solid transparent !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: var(--text-primary) !important;
            background: rgba(124, 92, 252, 0.06) !important;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(140deg, var(--primary-500), var(--primary-700)) !important;
            color: white !important;
            box-shadow: 0 3px 14px rgba(124, 92, 252, 0.25), inset 0 1px 0 rgba(255,255,255,0.1) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
        }

        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] { display: none !important; }

        /* ══════════════ EXPANDER ══════════════ */
        [data-testid="stExpander"] { overflow: hidden; }

        [data-testid="stExpander"] details summary {
            font-weight: 600 !important;
            font-family: 'Space Grotesk', sans-serif !important;
            color: var(--text-secondary) !important;
            padding: 1.1rem 1.3rem !important;
            transition: all var(--duration-fast) ease !important;
            border-radius: var(--radius-lg) !important;
        }

        [data-testid="stExpander"] details summary:hover {
            color: var(--text-primary) !important;
            background: rgba(124, 92, 252, 0.03);
        }

        /* ══════════════ DATA TABLE ══════════════ */
        div.stDataFrame { overflow: hidden; }

        .stDataFrame [data-testid="stDataFrameResizable"] {
            border-radius: var(--radius-md) !important;
            overflow: hidden;
        }

        .stDataFrame table { border-collapse: separate !important; border-spacing: 0 !important; }

        .stDataFrame th {
            background: linear-gradient(180deg, rgba(124, 92, 252, 0.1), rgba(124, 92, 252, 0.06)) !important;
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 0.75rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
            border-bottom: 1px solid var(--border-default) !important;
            padding: 0.8rem 1rem !important;
        }

        .stDataFrame td {
            color: var(--text-secondary) !important;
            border-bottom: 1px solid var(--border-invisible) !important;
            font-size: 0.85rem !important;
            padding: 0.6rem 1rem !important;
            transition: background var(--duration-fast) ease;
        }

        .stDataFrame tr:hover td {
            background: rgba(124, 92, 252, 0.035) !important;
        }

        /* ══════════════ CAMERA / FILE UPLOAD ══════════════ */
        div[data-testid="stCameraInput"] {
            border: 2px solid var(--border-default);
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-lg);
            transition: all var(--duration-normal) var(--ease-out);
        }
        div[data-testid="stCameraInput"]:hover {
            border-color: var(--border-hover);
            box-shadow: var(--shadow-xl), var(--shadow-glow-purple);
        }

        [data-testid="stFileUploader"] {
            border: 2px dashed var(--border-default) !important;
            border-radius: var(--radius-lg) !important;
            padding: 2rem !important;
            transition: all var(--duration-normal) var(--ease-out) !important;
            background: rgba(124, 92, 252, 0.01) !important;
            position: relative;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: var(--primary-500) !important;
            background: rgba(124, 92, 252, 0.035) !important;
            box-shadow: inset 0 0 30px rgba(124, 92, 252, 0.03);
        }

        /* ══════════════ SLIDER ══════════════ */
        .stSlider > div > div > div > div { background: var(--primary-500) !important; }
        .stSlider [data-baseweb="slider"] [role="slider"] {
            background: var(--primary-500) !important;
            border: 3px solid rgba(255,255,255,0.9) !important;
            box-shadow: 0 2px 10px rgba(124, 92, 252, 0.4), 0 0 20px rgba(124, 92, 252, 0.15) !important;
            transition: transform var(--duration-fast) var(--ease-spring) !important;
        }
        .stSlider [data-baseweb="slider"] [role="slider"]:hover {
            transform: scale(1.15);
        }

        /* ══════════════ PROGRESS BAR ══════════════ */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, var(--primary-500), var(--primary-400), var(--secondary-500)) !important;
            background-size: 200% 100%;
            border-radius: var(--radius-full) !important;
            box-shadow: 0 0 16px var(--primary-glow-soft);
            animation: progressShimmer 2s ease-in-out infinite;
        }

        @keyframes progressShimmer {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }

        /* ══════════════ ALERTS ══════════════ */
        .stAlert, [data-testid="stAlert"] {
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--border-subtle) !important;
            backdrop-filter: blur(16px) !important;
        }

        div[data-testid="stAlert"] > div[role="alert"] {
            border-radius: var(--radius-md) !important;
        }

        /* ══════════════ DIVIDER ══════════════ */
        hr {
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg,
                transparent 0%,
                var(--border-subtle) 15%,
                var(--primary-glow-soft) 40%,
                rgba(124, 92, 252, 0.15) 50%,
                var(--primary-glow-soft) 60%,
                var(--border-subtle) 85%,
                transparent 100%
            ) !important;
            margin: 2.2rem 0 !important;
        }

        /* ══════════════ CAPTIONS ══════════════ */
        .stCaption, small {
            color: var(--text-faint) !important;
            font-size: 0.78rem !important;
            font-family: 'Space Grotesk', sans-serif;
        }

        /* ══════════════ DOWNLOAD BUTTON ══════════════ */
        .stDownloadButton > button {
            background: linear-gradient(140deg, var(--secondary-700), var(--secondary-500)) !important;
            border: 1px solid rgba(52, 211, 153, 0.25) !important;
            box-shadow: 0 4px 14px rgba(52, 211, 153, 0.15), inset 0 1px 0 rgba(255,255,255,0.1) !important;
        }
        .stDownloadButton > button:hover {
            box-shadow: 0 8px 28px rgba(52, 211, 153, 0.25), inset 0 1px 0 rgba(255,255,255,0.15) !important;
            filter: brightness(1.06);
        }

        /* ══════════════ PLOTLY ══════════════ */
        .js-plotly-plot .plotly .modebar {
            background: rgba(15, 18, 25, 0.8) !important;
            backdrop-filter: blur(8px);
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--border-subtle);
        }

        /* ══════════════ SIDEBAR ══════════════ */
        div[data-testid="stSidebar"] {
            border-radius: 0 var(--radius-xl) var(--radius-xl) 0 !important;
            border-left: none !important;
            background: linear-gradient(180deg, rgba(15, 18, 25, 0.95), rgba(10, 13, 22, 0.98)) !important;
        }

        /* ══════════════ TOOLTIP / JSON / SPINNER ══════════════ */
        [data-testid="stTooltipIcon"] { color: var(--text-faint) !important; }

        .stJson {
            background: var(--bg-input) !important;
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--border-subtle) !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.8rem !important;
        }

        .stSpinner > div { border-top-color: var(--primary-500) !important; }

        /* ══════════════ TOGGLE ══════════════ */
        .stToggle label span {
            font-family: 'Space Grotesk', sans-serif !important;
            font-weight: 500;
        }

        /* ══════════════ IMAGES ══════════════ */
        .stImage {
            border-radius: var(--radius-md);
            overflow: hidden;
        }

        .stImage img {
            border-radius: var(--radius-md) !important;
            transition: transform var(--duration-slow) var(--ease-out);
        }

        /* ═══════════════════════════════════════════════════════
           LOGIN PAGE — CINEMATIC IMMERSIVE EXPERIENCE
           ═══════════════════════════════════════════════════════ */

        .login-title {
            font-family: 'Inter', sans-serif;
            font-weight: 900;
            font-size: clamp(2.8rem, 7vw, 5rem);
            text-align: center;
            margin-bottom: 0.15rem;
            letter-spacing: -0.055em;
            line-height: 1.05;
            background: linear-gradient(
                135deg,
                #FFFFFF 0%,
                var(--primary-300) 25%,
                #FFFFFF 45%,
                var(--secondary-300) 65%,
                #FFFFFF 85%,
                var(--primary-200) 100%
            );
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: titleShimmer 8s ease-in-out infinite;
            filter: drop-shadow(0 0 40px var(--primary-glow)) drop-shadow(0 0 80px rgba(52, 211, 153, 0.1));
            position: relative;
        }

        @keyframes titleShimmer {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        .login-subtitle {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 400;
            font-size: clamp(0.8rem, 1.8vw, 1.05rem);
            color: var(--text-muted);
            text-align: center;
            font-style: normal;
            margin-bottom: 2.5rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            opacity: 0;
            animation: subtitleReveal 1.5s ease-out 0.6s forwards;
        }

        @keyframes subtitleReveal {
            from { opacity: 0; transform: translateY(10px) scale(0.97); letter-spacing: 0.3em; }
            to { opacity: 0.6; transform: translateY(0) scale(1); letter-spacing: 0.15em; }
        }

        /* ── STARFIELD ── */
        #stars-container {
            position: fixed;
            inset: 0;
            z-index: 1;
            overflow: hidden;
            pointer-events: none;
            background: transparent;
        }

        .stApp > header, .stApp > div:nth-child(1) {
            z-index: 2;
            position: relative;
        }

        .star {
            position: absolute;
            border-radius: 50%;
            opacity: 0;
            will-change: transform, opacity;
        }

        .star--sm {
            width: 1px; height: 1px;
            background: rgba(255, 255, 255, 0.5);
            box-shadow: 0 0 2px rgba(255, 255, 255, 0.25);
            animation: starPulse 4s ease-in-out infinite;
        }

        .star--md {
            width: 1.5px; height: 1.5px;
            background: rgba(200, 210, 255, 0.7);
            box-shadow: 0 0 5px rgba(200, 210, 255, 0.35), 0 0 10px rgba(124, 92, 252, 0.15);
            animation: starPulse 5s ease-in-out infinite;
        }

        .star--lg {
            width: 2.5px; height: 2.5px;
            background: rgba(255, 255, 255, 0.85);
            box-shadow: 0 0 7px rgba(255, 255, 255, 0.4), 0 0 16px rgba(124, 92, 252, 0.12);
            animation: starPulse 6.5s ease-in-out infinite;
        }

        @keyframes starPulse {
            0%, 100% { opacity: 0.08; transform: scale(0.7); }
            25% { opacity: 0.5; }
            50% { opacity: 1; transform: scale(1.4); }
            75% { opacity: 0.5; }
        }

        /* Shooting stars */
        .shooting-star {
            position: absolute;
            width: 2px; height: 2px;
            background: white;
            border-radius: 50%;
            box-shadow:
                0 0 4px 1px rgba(255,255,255,0.5),
                -20px 0 8px rgba(124, 92, 252, 0.3),
                -40px 0 5px rgba(124, 92, 252, 0.15),
                -60px 0 3px rgba(124, 92, 252, 0.05);
            animation: shoot 4s ease-in infinite;
            opacity: 0;
        }

        @keyframes shoot {
            0% { transform: translate3d(0, 0, 0) rotate(-35deg); opacity: 0; }
            3% { opacity: 1; }
            12% { transform: translate3d(350px, 220px, 0) rotate(-35deg); opacity: 0; }
            100% { opacity: 0; }
        }

        /* Aurora borealis */
        .aurora {
            position: fixed;
            bottom: -25%;
            left: -15%;
            width: 130%;
            height: 55%;
            background: linear-gradient(
                180deg,
                transparent 0%,
                rgba(124, 92, 252, 0.015) 30%,
                rgba(52, 211, 153, 0.025) 50%,
                rgba(56, 189, 248, 0.015) 70%,
                transparent 100%
            );
            filter: blur(70px);
            animation: auroraWave 18s ease-in-out infinite alternate;
            pointer-events: none;
            z-index: 0;
        }

        @keyframes auroraWave {
            0% { transform: translate3d(-6%, 0, 0) skewY(-1.5deg) scaleX(1); }
            50% { transform: translate3d(3%, -2%, 0) skewY(0.5deg) scaleX(1.03); }
            100% { transform: translate3d(6%, -4%, 0) skewY(1.5deg) scaleX(0.98); }
        }

        /* Orbital ring behind title */
        .login-orbital {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 400px;
            height: 400px;
            border-radius: 50%;
            border: 1px solid rgba(124, 92, 252, 0.06);
            animation: orbitalSpin 30s linear infinite;
            pointer-events: none;
        }

        .login-orbital::before {
            content: '';
            position: absolute;
            top: -2px; left: 50%;
            width: 4px; height: 4px;
            border-radius: 50%;
            background: var(--primary-300);
            box-shadow: 0 0 8px var(--primary-glow);
        }

        @keyframes orbitalSpin {
            from { transform: translate(-50%, -50%) rotate(0deg); }
            to { transform: translate(-50%, -50%) rotate(360deg); }
        }

        /* ═══════════════════════════════════════════════════════
           PERSON CARD — Premium Attendance Card V2
           ═══════════════════════════════════════════════════════ */
        .person-card {
            background: linear-gradient(155deg, 
                rgba(124, 92, 252, 0.08) 0%, 
                rgba(52, 211, 153, 0.04) 50%, 
                rgba(124, 92, 252, 0.05) 100%
            ) !important;
            backdrop-filter: blur(32px) saturate(2.2) !important;
            -webkit-backdrop-filter: blur(32px) saturate(2.2) !important;
            border: 1px solid rgba(124, 92, 252, 0.18) !important;
            border-radius: var(--radius-xl) !important;
            padding: 1.8rem 1.5rem !important;
            text-align: center;
            position: relative;
            overflow: hidden;
            box-shadow:
                0 12px 40px rgba(0,0,0,0.22),
                0 4px 12px rgba(124, 92, 252, 0.1),
                0 1px 3px rgba(0,0,0,0.1),
                inset 0 1px 0 rgba(255,255,255,0.08);
            animation: personCardIn 0.5s var(--ease-out) both;
            transform-style: preserve-3d;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .person-card:hover {
            transform: translateY(-4px) scale(1.01);
            border-color: rgba(124, 92, 252, 0.3) !important;
            box-shadow:
                0 20px 50px rgba(0,0,0,0.25),
                0 8px 20px rgba(124, 92, 252, 0.15),
                0 0 30px rgba(124, 92, 252, 0.08),
                inset 0 1px 0 rgba(255,255,255,0.1);
        }

        .person-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 12%;
            right: 12%;
            height: 1px;
            background: linear-gradient(90deg, 
                transparent 0%,
                rgba(124, 92, 252, 0.4) 30%,
                rgba(52, 211, 153, 0.35) 50%,
                rgba(124, 92, 252, 0.4) 70%,
                transparent 100%
            );
            opacity: 0.9;
        }

        .person-card::after {
            content: '';
            position: absolute;
            top: -60%;
            left: -40%;
            width: 180%;
            height: 180%;
            background: radial-gradient(
                ellipse at 30% 30%,
                rgba(124, 92, 252, 0.06) 0%,
                transparent 50%
            );
            animation: personCardGlow 8s ease-in-out infinite alternate;
            pointer-events: none;
            z-index: 0;
        }

        .person-card h3 {
            margin: 0 0 0.3rem 0 !important;
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            background: linear-gradient(140deg, #FFFFFF 0%, var(--primary-200) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            position: relative;
            z-index: 1;
            letter-spacing: -0.01em;
        }

        .person-card-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.3rem 0.75rem;
            background: rgba(124, 92, 252, 0.15);
            border: 1px solid rgba(124, 92, 252, 0.25);
            border-radius: var(--radius-full);
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--primary-200);
            margin-top: 0.5rem;
            position: relative;
            z-index: 1;
        }

        @keyframes personCardIn {
            from { 
                opacity: 0; 
                transform: translate3d(0, 20px, 0) scale(0.95) rotateX(-5deg);
                filter: blur(4px);
            }
            to { 
                opacity: 1; 
                transform: translate3d(0, 0, 0) scale(1) rotateX(0deg);
                filter: blur(0);
            }
        }

        @keyframes personCardGlow {
            0% { transform: translate(0%, 0%) rotate(0deg); opacity: 0.8; }
            50% { transform: translate(3%, 2%) rotate(1deg); opacity: 1; }
            100% { transform: translate(5%, 5%) rotate(2deg); opacity: 0.9; }
        }

        /* Person card face image container */
        .person-card-image {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            margin: 0 auto 1rem;
            overflow: hidden;
            border: 3px solid rgba(124, 92, 252, 0.3);
            box-shadow: 
                0 4px 15px rgba(0, 0, 0, 0.2),
                0 0 20px rgba(124, 92, 252, 0.15);
            position: relative;
            z-index: 1;
        }

        .person-card-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        /* Stats inside person card */
        .person-card-stats {
            display: flex;
            justify-content: center;
            gap: 1.5rem;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            position: relative;
            z-index: 1;
        }

        .person-card-stat {
            text-align: center;
        }

        .person-card-stat-value {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--text-primary);
            display: block;
        }

        .person-card-stat-label {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.65rem;
            color: var(--text-faint);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* ═══════════════════════════════════════════════════════
           PAGE TRANSITIONS
           ═══════════════════════════════════════════════════════ */
        .main .block-container {
            animation: pageReveal 0.4s var(--ease-out) both;
        }

        @keyframes pageReveal {
            from { opacity: 0; transform: translate3d(0, 10px, 0); }
            to { opacity: 1; transform: translate3d(0, 0, 0); }
        }

        /* Staggered column animation */
        .main .block-container [data-testid="column"] {
            animation: colPop 0.4s var(--ease-out) both;
        }
        .main .block-container [data-testid="column"]:nth-child(1) { animation-delay: 0.05s; }
        .main .block-container [data-testid="column"]:nth-child(2) { animation-delay: 0.1s; }
        .main .block-container [data-testid="column"]:nth-child(3) { animation-delay: 0.15s; }
        .main .block-container [data-testid="column"]:nth-child(4) { animation-delay: 0.2s; }

        @keyframes colPop {
            from { opacity: 0; transform: translate3d(0, 6px, 0) scale(0.98); }
            to { opacity: 1; transform: translate3d(0, 0, 0) scale(1); }
        }

        /* ═══════════════════════════════════════════════════════
           SEATING GRID — Premium Interactive Map
           ═══════════════════════════════════════════════════════ */
        .seat-grid-container {
            display: flex;
            flex-direction: column;
            gap: 5px;
            overflow-x: auto;
            padding: 1.75rem;
            background:
                linear-gradient(150deg, rgba(124, 92, 252, 0.025), rgba(0,0,0,0.12), rgba(52, 211, 153, 0.015));
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-subtle);
            backdrop-filter: blur(12px);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.03), var(--shadow-md);
        }

        .seat-row { display: flex; gap: 5px; }

        .seat-row-label {
            width: 34px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.7rem;
            color: var(--text-faint);
            letter-spacing: 0.05em;
        }

        .seat-cell {
            width: 56px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--radius-xs);
            font-family: 'Inter', sans-serif;
            color: white;
            transition:
                transform var(--duration-fast) var(--ease-spring),
                box-shadow var(--duration-fast) ease,
                filter var(--duration-fast) ease;
            cursor: default;
            position: relative;
        }

        .seat-cell:hover {
            transform: scale(1.12) translate3d(0, -2px, 0);
            z-index: 3;
            filter: brightness(1.1);
        }

        .seat-empty {
            background: rgba(255,255,255,0.018);
            border: 1px solid rgba(255,255,255,0.03);
        }

        .seat-empty:hover {
            background: rgba(255,255,255,0.04);
            border-color: rgba(255,255,255,0.08);
        }

        .seat-male {
            background: linear-gradient(140deg, rgba(108, 93, 211, 0.8) 0%, rgba(91, 52, 232, 0.85) 100%);
            border: 1px solid rgba(124, 92, 252, 0.45);
            box-shadow: 0 2px 8px rgba(108, 93, 211, 0.25), inset 0 1px 0 rgba(255,255,255,0.08);
        }
        .seat-male:hover { box-shadow: 0 6px 20px rgba(108, 93, 211, 0.45), inset 0 1px 0 rgba(255,255,255,0.12); }

        .seat-female {
            background: linear-gradient(140deg, rgba(244, 63, 94, 0.8) 0%, rgba(225, 29, 72, 0.85) 100%);
            border: 1px solid rgba(244, 63, 94, 0.45);
            box-shadow: 0 2px 8px rgba(244, 63, 94, 0.25), inset 0 1px 0 rgba(255,255,255,0.08);
        }
        .seat-female:hover { box-shadow: 0 6px 20px rgba(244, 63, 94, 0.45), inset 0 1px 0 rgba(255,255,255,0.12); }

        .seat-other {
            background: linear-gradient(140deg, rgba(56, 189, 248, 0.8) 0%, rgba(14, 165, 233, 0.85) 100%);
            border: 1px solid rgba(56, 189, 248, 0.45);
            box-shadow: 0 2px 8px rgba(56, 189, 248, 0.25), inset 0 1px 0 rgba(255,255,255,0.08);
        }
        .seat-other:hover { box-shadow: 0 6px 20px rgba(56, 189, 248, 0.45), inset 0 1px 0 rgba(255,255,255,0.12); }

        .seat-name {
            font-weight: 600;
            font-size: 0.72rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 50px;
            display: block;
            text-shadow: 0 1px 3px rgba(0,0,0,0.35);
        }

        .seat-num { font-size: 0.6rem; opacity: 0.15; font-family: 'JetBrains Mono', monospace; }

        .seat-legend {
            display: flex;
            gap: 1.8rem;
            margin-top: 1rem;
            padding: 0.75rem 1rem;
            background: rgba(0,0,0,0.15);
            border-radius: var(--radius-sm);
            border: 1px solid var(--border-invisible);
        }

        .seat-legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.75rem;
            color: var(--text-muted);
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 500;
        }

        .seat-legend-dot {
            width: 12px;
            height: 12px;
            border-radius: 4px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }

        /* ═══════════════════════════════════════════════════════
           PDF DOWNLOAD
           ═══════════════════════════════════════════════════════ */
        .pdf-download-btn {
            display: block;
            text-align: center;
            padding: 0.9rem 2rem;
            margin-top: 1.2rem;
            background: linear-gradient(140deg, var(--primary-500), var(--primary-700));
            color: white !important;
            text-decoration: none !important;
            border-radius: var(--radius-md);
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            font-size: 0.88rem;
            letter-spacing: 0.02em;
            box-shadow: 0 4px 18px rgba(124, 92, 252, 0.25), inset 0 1px 0 rgba(255,255,255,0.1);
            transition:
                transform var(--duration-normal) var(--ease-spring),
                box-shadow var(--duration-normal) ease,
                filter var(--duration-normal) ease;
            position: relative;
            overflow: hidden;
        }

        .pdf-download-btn:hover {
            transform: translate3d(0, -2px, 0);
            box-shadow: 0 10px 32px rgba(124, 92, 252, 0.35), inset 0 1px 0 rgba(255,255,255,0.15);
            filter: brightness(1.05);
        }

        .pdf-download-btn::after {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(
                120deg,
                transparent 30%,
                rgba(255,255,255,0.06) 45%,
                rgba(255,255,255,0.1) 50%,
                rgba(255,255,255,0.06) 55%,
                transparent 70%
            );
            background-size: 250% 250%;
            animation: pdfSheen 4s ease-in-out infinite;
        }

        @keyframes pdfSheen {
            0%, 100% { background-position: 250% 50%; }
            50% { background-position: -50% 50%; }
        }

        /* ═══════════════════════════════════════════════════════
           DASHBOARD MENU CARDS (Event Menu) — ULTRA PREMIUM V2
           ═══════════════════════════════════════════════════════ */
        
        /* Menu Grid Container */
        .menu-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.25rem;
            padding: 1rem 0;
        }

        @media (max-width: 900px) {
            .menu-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 1rem;
            }
        }

        @media (max-width: 600px) {
            .menu-grid {
                grid-template-columns: 1fr;
                gap: 0.85rem;
            }
        }

        .menu-card {
            background: linear-gradient(165deg, 
                rgba(255, 255, 255, 0.04) 0%,
                rgba(124, 92, 252, 0.025) 50%,
                rgba(52, 211, 153, 0.015) 100%
            );
            backdrop-filter: blur(24px) saturate(1.8);
            -webkit-backdrop-filter: blur(24px) saturate(1.8);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: var(--radius-xl);
            padding: 1.75rem 1.5rem 1.25rem;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            overflow: hidden;
            cursor: pointer;
            min-height: 160px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            transform-style: preserve-3d;
            perspective: 1000px;
        }

        /* Top specular highlight */
        .menu-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 15%;
            right: 15%;
            height: 1px;
            background: linear-gradient(90deg, 
                transparent 0%,
                rgba(255, 255, 255, 0.12) 30%,
                rgba(255, 255, 255, 0.2) 50%,
                rgba(255, 255, 255, 0.12) 70%,
                transparent 100%
            );
            opacity: 0.8;
            transition: opacity 0.3s ease;
        }

        /* Animated gradient background on hover */
        .menu-card::after {
            content: '';
            position: absolute;
            inset: 0;
            background: radial-gradient(
                ellipse 80% 80% at var(--mouse-x, 50%) var(--mouse-y, 50%),
                rgba(124, 92, 252, 0.15) 0%,
                transparent 60%
            );
            opacity: 0;
            transition: opacity 0.4s ease;
            pointer-events: none;
            z-index: 0;
        }

        .menu-card:hover {
            transform: translateY(-8px) scale(1.02) rotateX(2deg);
            border-color: rgba(124, 92, 252, 0.35);
            box-shadow: 
                0 20px 50px rgba(0, 0, 0, 0.25),
                0 10px 25px rgba(124, 92, 252, 0.2),
                0 0 0 1px rgba(124, 92, 252, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            background: linear-gradient(165deg, 
                rgba(255, 255, 255, 0.06) 0%,
                rgba(124, 92, 252, 0.06) 50%,
                rgba(52, 211, 153, 0.03) 100%
            );
        }

        .menu-card:hover::before {
            background: linear-gradient(90deg, 
                transparent 0%,
                rgba(124, 92, 252, 0.3) 30%,
                rgba(124, 92, 252, 0.5) 50%,
                rgba(124, 92, 252, 0.3) 70%,
                transparent 100%
            );
            opacity: 1;
        }

        .menu-card:hover::after {
            opacity: 1;
        }

        .menu-card:active {
            transform: translateY(-2px) scale(0.98);
            transition-duration: 0.1s;
        }

        /* Icon Container */
        .menu-card-icon-wrap {
            width: 64px;
            height: 64px;
            border-radius: 18px;
            background: linear-gradient(145deg, 
                rgba(124, 92, 252, 0.15),
                rgba(124, 92, 252, 0.05)
            );
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1rem;
            position: relative;
            z-index: 1;
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            box-shadow: 
                0 4px 15px rgba(124, 92, 252, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }

        .menu-card:hover .menu-card-icon-wrap {
            transform: scale(1.1) translateY(-4px);
            background: linear-gradient(145deg, 
                rgba(124, 92, 252, 0.25),
                rgba(52, 211, 153, 0.1)
            );
            box-shadow: 
                0 8px 25px rgba(124, 92, 252, 0.3),
                0 0 30px rgba(124, 92, 252, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
        }

        .menu-card-icon {
            font-size: 2rem;
            display: block;
            filter: drop-shadow(0 2px 8px rgba(124, 92, 252, 0.3));
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
            animation: iconFloat 4s ease-in-out infinite;
        }

        .menu-card:hover .menu-card-icon {
            transform: scale(1.15);
            filter: drop-shadow(0 4px 15px rgba(124, 92, 252, 0.5));
            animation-play-state: paused;
        }

        @keyframes iconFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-3px); }
        }

        .menu-card-title {
            font-family: 'Inter', -apple-system, sans-serif;
            font-weight: 700;
            font-size: 1rem;
            color: var(--text-primary);
            margin-bottom: 0.4rem;
            letter-spacing: -0.01em;
            position: relative;
            z-index: 1;
            transition: all 0.3s ease;
            background: linear-gradient(140deg, #FFFFFF 0%, #E2E8F0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .menu-card:hover .menu-card-title {
            background: linear-gradient(140deg, #FFFFFF 0%, var(--primary-200) 100%);
            -webkit-background-clip: text;
            background-clip: text;
        }

        .menu-card-desc {
            font-family: 'Outfit', sans-serif;
            font-size: 0.82rem;
            color: var(--text-muted);
            line-height: 1.45;
            margin-bottom: 0;
            max-width: 200px;
            position: relative;
            z-index: 1;
            transition: color 0.3s ease;
        }

        .menu-card:hover .menu-card-desc {
            color: var(--text-secondary);
        }

        /* Shimmer effect on hover */
        .menu-card-shimmer {
            position: absolute;
            top: 0;
            left: -150%;
            width: 50%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent 0%,
                rgba(255, 255, 255, 0.03) 25%,
                rgba(255, 255, 255, 0.08) 50%,
                rgba(255, 255, 255, 0.03) 75%,
                transparent 100%
            );
            transform: skewX(-20deg);
            transition: left 0.8s ease;
            pointer-events: none;
        }

        .menu-card:hover .menu-card-shimmer {
            left: 150%;
        }

        /* Color variants for different card types */
        .menu-card[data-variant="capture"] .menu-card-icon-wrap {
            background: linear-gradient(145deg, rgba(52, 211, 153, 0.2), rgba(52, 211, 153, 0.05));
        }
        .menu-card[data-variant="capture"]:hover {
            border-color: rgba(52, 211, 153, 0.35);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25), 0 10px 25px rgba(52, 211, 153, 0.2);
        }

        .menu-card[data-variant="analytics"] .menu-card-icon-wrap {
            background: linear-gradient(145deg, rgba(56, 189, 248, 0.2), rgba(56, 189, 248, 0.05));
        }
        .menu-card[data-variant="analytics"]:hover {
            border-color: rgba(56, 189, 248, 0.35);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25), 0 10px 25px rgba(56, 189, 248, 0.2);
        }

        .menu-card[data-variant="settings"] .menu-card-icon-wrap {
            background: linear-gradient(145deg, rgba(245, 158, 11, 0.2), rgba(245, 158, 11, 0.05));
        }
        .menu-card[data-variant="settings"]:hover {
            border-color: rgba(245, 158, 11, 0.35);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25), 0 10px 25px rgba(245, 158, 11, 0.2);
        }

        .menu-card[data-variant="team"] .menu-card-icon-wrap {
            background: linear-gradient(145deg, rgba(244, 63, 94, 0.2), rgba(244, 63, 94, 0.05));
        }
        .menu-card[data-variant="team"]:hover {
            border-color: rgba(244, 63, 94, 0.35);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25), 0 10px 25px rgba(244, 63, 94, 0.2);
        }

        /* Entrance animation for cards */
        .menu-card {
            animation: menuCardEntrance 0.6s cubic-bezier(0.16, 1, 0.3, 1) backwards;
        }

        .menu-card:nth-child(1) { animation-delay: 0.05s; }
        .menu-card:nth-child(2) { animation-delay: 0.1s; }
        .menu-card:nth-child(3) { animation-delay: 0.15s; }
        .menu-card:nth-child(4) { animation-delay: 0.2s; }
        .menu-card:nth-child(5) { animation-delay: 0.25s; }
        .menu-card:nth-child(6) { animation-delay: 0.3s; }
        .menu-card:nth-child(7) { animation-delay: 0.35s; }

        @keyframes menuCardEntrance {
            from {
                opacity: 0;
                transform: translateY(30px) scale(0.9);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            .menu-card {
                padding: 1.4rem 1.2rem 1rem;
                min-height: 140px;
                border-radius: var(--radius-lg);
            }
            
            .menu-card-icon-wrap {
                width: 54px;
                height: 54px;
                border-radius: 14px;
                margin-bottom: 0.8rem;
            }
            
            .menu-card-icon {
                font-size: 1.7rem;
            }
            
            .menu-card-title {
                font-size: 0.92rem;
            }
            
            .menu-card-desc {
                font-size: 0.75rem;
            }
        }

        @media (max-width: 480px) {
            .menu-card {
                padding: 1.2rem 1rem 0.9rem;
                min-height: 120px;
                flex-direction: row;
                text-align: left;
                gap: 1rem;
            }
            
            .menu-card-icon-wrap {
                width: 48px;
                height: 48px;
                border-radius: 12px;
                margin-bottom: 0;
                flex-shrink: 0;
            }
            
            .menu-card-icon {
                font-size: 1.5rem;
            }
            
            .menu-card-content {
                flex: 1;
            }
            
            .menu-card-title {
                font-size: 0.88rem;
                margin-bottom: 0.2rem;
            }
            
            .menu-card-desc {
                font-size: 0.72rem;
                max-width: none;
            }
        }

        /* Button inside card styling override */
        .menu-card-container div.stButton > button {
            margin-top: 0.5rem;
            background: linear-gradient(140deg, rgba(124, 92, 252, 0.2), rgba(124, 92, 252, 0.1)) !important;
            border: 1px solid rgba(124, 92, 252, 0.25) !important;
            color: var(--text-primary) !important;
            font-size: 0.8rem !important;
            padding: 0.5rem 1rem !important;
            backdrop-filter: blur(8px);
        }

        .menu-card-container div.stButton > button:hover {
            background: linear-gradient(140deg, rgba(124, 92, 252, 0.35), rgba(124, 92, 252, 0.2)) !important;
            border-color: rgba(124, 92, 252, 0.5) !important;
            transform: translateY(-2px) scale(1.02);
        }

        /* Hidden button approach - make card clickable */
        .menu-card-clickable {
            cursor: pointer;
        }

        .menu-card-clickable div.stButton {
            position: absolute;
            inset: 0;
            opacity: 0;
        }

        .menu-card-clickable div.stButton > button {
            width: 100% !important;
            height: 100% !important;
            background: transparent !important;
            border: none !important;
        }

        /* ═══════════════════════════════════════════════════════
           EVENT LIST CARDS
           ═══════════════════════════════════════════════════════ */
        .event-list-card {
            background: var(--glass-bg);
            backdrop-filter: blur(16px) saturate(1.5);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            padding: 1.2rem 1.5rem;
            margin-bottom: 0.5rem;
            transition: all var(--duration-normal) var(--ease-out);
            position: relative;
            overflow: hidden;
        }

        .event-list-card::before {
            content: '';
            position: absolute;
            left: 0; top: 20%; bottom: 20%;
            width: 3px;
            border-radius: 0 var(--radius-full) var(--radius-full) 0;
            background: linear-gradient(180deg, var(--primary-500), var(--secondary-500));
            opacity: 0;
            transition: opacity var(--duration-normal) ease;
        }

        .event-list-card:hover {
            border-color: var(--border-hover);
            box-shadow: var(--shadow-card-hover);
            transform: translate3d(0, -2px, 0);
        }

        .event-list-card:hover::before { opacity: 1; }

        .event-list-card h3 {
            font-size: 1.15rem !important;
            margin-bottom: 0.3rem !important;
        }

        .event-list-meta {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.78rem;
            color: var(--text-faint);
            letter-spacing: 0.02em;
        }

        /* ═══════════════════════════════════════════════════════
           WELCOME BANNER (Home Page) — ENHANCED V2
           ═══════════════════════════════════════════════════════ */
        .welcome-banner {
            background: linear-gradient(155deg, 
                rgba(124, 92, 252, 0.06) 0%,
                rgba(52, 211, 153, 0.04) 50%, 
                rgba(124, 92, 252, 0.03) 100%
            );
            backdrop-filter: blur(24px) saturate(1.8);
            -webkit-backdrop-filter: blur(24px) saturate(1.8);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: var(--radius-xl);
            padding: 2rem 2.5rem;
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
            box-shadow:
                0 8px 32px rgba(0, 0, 0, 0.15),
                0 0 0 1px rgba(124, 92, 252, 0.05),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }

        .welcome-banner::before {
            content: '';
            position: absolute;
            top: 0;
            left: 8%;
            right: 8%;
            height: 1px;
            background: linear-gradient(90deg, 
                transparent 0%,
                rgba(255, 255, 255, 0.12) 25%,
                rgba(124, 92, 252, 0.2) 50%,
                rgba(255, 255, 255, 0.12) 75%,
                transparent 100%
            );
        }

        .welcome-banner::after {
            content: '';
            position: absolute;
            top: -60%;
            right: -25%;
            width: 400px;
            height: 400px;
            border-radius: 50%;
            background: radial-gradient(circle, 
                rgba(124, 92, 252, 0.06) 0%,
                rgba(52, 211, 153, 0.03) 40%,
                transparent 70%
            );
            pointer-events: none;
            animation: welcomeOrbFloat 20s ease-in-out infinite alternate;
        }

        @keyframes welcomeOrbFloat {
            0% { transform: translate(0, 0) rotate(0deg); }
            100% { transform: translate(-30px, 20px) rotate(10deg); }
        }

        .welcome-greeting {
            font-family: 'Inter', -apple-system, sans-serif;
            font-weight: 800;
            font-size: 2rem;
            letter-spacing: -0.03em;
            background: linear-gradient(140deg, #FFFFFF 0%, var(--primary-200) 60%, var(--secondary-300) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.4rem;
            line-height: 1.2;
        }

        .welcome-time {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.82rem;
            color: var(--text-muted);
            letter-spacing: 0.03em;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        /* Responsive welcome banner */
        @media (max-width: 768px) {
            .welcome-banner {
                padding: 1.5rem 1.3rem;
                border-radius: var(--radius-lg);
            }
            
            .welcome-greeting {
                font-size: 1.5rem;
            }
            
            .welcome-time {
                font-size: 0.72rem;
            }
        }

        @media (max-width: 480px) {
            .welcome-banner {
                padding: 1.2rem 1rem;
            }
            
            .welcome-greeting {
                font-size: 1.25rem;
            }
            
            .welcome-time {
                font-size: 0.68rem;
            }
        }

        /* ═══════════════════════════════════════════════════════
           ACCESSIBILITY & PERFORMANCE
           ═══════════════════════════════════════════════════════ */

        *:focus-visible {
            outline: 2px solid var(--primary-500) !important;
            outline-offset: 2px;
            border-radius: 4px;
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        }

        @media (prefers-color-scheme: light) {
            /* Future: Light mode overrides could go here */
        }

        /* ═══════════════════════════════════════════════════════
           RESPONSIVE BREAKPOINTS — COMPREHENSIVE MOBILE-FIRST
           ═══════════════════════════════════════════════════════ */
        
        /* Extra Large Screens (1400px+) */
        @media (min-width: 1400px) {
            .main .block-container {
                max-width: 1320px;
                padding: 2rem 3rem;
            }
        }

        /* Large Tablets & Small Laptops (1024px - 1199px) */
        @media (max-width: 1199px) {
            h1 { font-size: 2rem !important; }
            .welcome-banner { padding: 1.8rem 2rem; }
            [data-testid="stMetric"] { padding: 1.3rem 1.1rem; }
        }

        /* Tablets (768px - 1023px) */
        @media (max-width: 1024px) {
            h1 { font-size: 1.8rem !important; }
            h2 { font-size: 1.4rem !important; }
            h3 { font-size: 1.2rem !important; }
            
            .main .block-container {
                padding: 1rem 1.5rem;
            }
            
            /* Stack columns on tablet */
            [data-testid="column"] {
                min-width: 45% !important;
            }
            
            .welcome-banner {
                padding: 1.6rem 1.8rem;
            }
            
            .welcome-greeting {
                font-size: 1.6rem;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.8rem !important;
            }
            
            .seat-grid-container {
                padding: 1.25rem;
            }
            
            .seat-cell {
                width: 50px;
                height: 40px;
            }
        }

        /* Small Tablets & Large Phones (768px) */
        @media (max-width: 768px) {
            h1 { font-size: 1.6rem !important; }
            h2 { font-size: 1.3rem !important; }
            h3 { font-size: 1.1rem !important; }
            
            .main .block-container {
                padding: 0.75rem 1rem;
            }
            
            /* Full width columns on mobile */
            [data-testid="column"] {
                min-width: 100% !important;
                margin-bottom: 0.5rem;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.5rem !important;
            }
            
            [data-testid="stMetric"] {
                padding: 1rem 0.8rem;
            }
            
            [data-testid="stMetricLabel"] {
                font-size: 0.65rem;
            }
            
            div.stButton > button {
                padding: 0.6rem 1rem !important;
                font-size: 0.82rem !important;
            }
            
            .login-title {
                font-size: 2.2rem !important;
            }
            
            .login-subtitle {
                font-size: 0.75rem !important;
                letter-spacing: 0.1em;
            }
            
            .welcome-banner {
                padding: 1.4rem 1.3rem;
                margin-bottom: 1rem;
                border-radius: var(--radius-lg);
            }
            
            .welcome-greeting {
                font-size: 1.4rem;
            }
            
            .welcome-time {
                font-size: 0.72rem;
            }
            
            .seat-grid-container {
                padding: 1rem;
                border-radius: var(--radius-md);
            }
            
            .seat-cell {
                width: 44px;
                height: 36px;
            }
            
            .seat-name {
                max-width: 38px;
                font-size: 0.62rem;
            }
            
            .seat-row-label {
                width: 28px;
                font-size: 0.6rem;
            }
            
            .seat-legend {
                flex-wrap: wrap;
                gap: 1rem;
                padding: 0.6rem 0.8rem;
            }
            
            .seat-legend-item {
                font-size: 0.68rem;
            }
            
            /* Person Card Mobile */
            .person-card {
                padding: 1.2rem !important;
                border-radius: var(--radius-md) !important;
            }
            
            .person-card h3 {
                font-size: 1rem !important;
            }
            
            /* Form containers */
            div[data-testid="stForm"] {
                padding: 1.2rem !important;
                border-radius: var(--radius-md) !important;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
                padding: 3px !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                padding: 0.45rem 0.9rem !important;
                font-size: 0.75rem !important;
            }
            
            /* Expander */
            [data-testid="stExpander"] details summary {
                padding: 0.9rem 1rem !important;
                font-size: 0.85rem !important;
            }
            
            /* Data table */
            .stDataFrame th {
                padding: 0.6rem 0.5rem !important;
                font-size: 0.68rem !important;
            }
            
            .stDataFrame td {
                padding: 0.5rem 0.5rem !important;
                font-size: 0.78rem !important;
            }
            
            /* File uploader */
            [data-testid="stFileUploader"] {
                padding: 1.5rem !important;
            }
            
            /* Sidebar */
            div[data-testid="stSidebar"] {
                border-radius: 0 var(--radius-lg) var(--radius-lg) 0 !important;
            }
        }

        /* Mobile Phones (480px) */
        @media (max-width: 480px) {
            h1 { font-size: 1.35rem !important; }
            h2 { font-size: 1.15rem !important; }
            h3 { font-size: 1rem !important; }
            
            .main .block-container {
                padding: 0.5rem 0.75rem;
            }
            
            .login-title {
                font-size: 1.8rem !important;
            }
            
            .login-subtitle {
                font-size: 0.68rem !important;
                margin-bottom: 1.8rem;
            }
            
            .welcome-banner {
                padding: 1.1rem 1rem;
            }
            
            .welcome-greeting {
                font-size: 1.2rem;
            }
            
            .welcome-time {
                font-size: 0.68rem;
            }
            
            div.stButton > button {
                padding: 0.55rem 0.8rem !important;
                font-size: 0.78rem !important;
                border-radius: var(--radius-sm) !important;
            }
            
            [data-testid="stMetric"] {
                padding: 0.9rem 0.7rem;
                border-radius: var(--radius-md) !important;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.3rem !important;
            }
            
            [data-testid="stMetricLabel"] {
                font-size: 0.6rem;
            }
            
            .seat-grid-container {
                padding: 0.75rem;
            }
            
            .seat-cell {
                width: 38px;
                height: 30px;
            }
            
            .seat-name {
                max-width: 32px;
                font-size: 0.55rem;
            }
            
            .seat-row-label {
                width: 24px;
                font-size: 0.55rem;
            }
            
            /* Inputs mobile */
            .stTextInput > div > div > input,
            .stDateInput > div > div > input,
            .stNumberInput > div > div > input,
            .stTextArea textarea {
                padding: 0.55rem 0.8rem !important;
                font-size: 0.85rem !important;
            }
            
            /* Radio buttons mobile */
            .stRadio > div > label {
                padding: 0.45rem 0.8rem !important;
                font-size: 0.8rem !important;
            }
            
            /* Tabs mobile */
            .stTabs [data-baseweb="tab"] {
                padding: 0.4rem 0.7rem !important;
                font-size: 0.7rem !important;
            }
            
            /* Alerts mobile */
            .stAlert {
                padding: 0.7rem 0.9rem !important;
                font-size: 0.8rem !important;
            }
            
            /* PDF download button */
            .pdf-download-btn {
                padding: 0.7rem 1.2rem;
                font-size: 0.8rem;
            }
        }

        /* Extra Small Phones (360px) */
        @media (max-width: 360px) {
            h1 { font-size: 1.2rem !important; }
            h2 { font-size: 1.05rem !important; }
            
            .login-title {
                font-size: 1.5rem !important;
            }
            
            .welcome-greeting {
                font-size: 1.1rem;
            }
            
            div.stButton > button {
                padding: 0.5rem 0.7rem !important;
                font-size: 0.72rem !important;
            }
            
            .seat-cell {
                width: 32px;
                height: 26px;
            }
            
            .seat-name {
                max-width: 28px;
                font-size: 0.5rem;
            }
        }

        /* Landscape orientation on mobile */
        @media (max-height: 500px) and (orientation: landscape) {
            .login-title {
                font-size: 1.8rem !important;
                margin-bottom: 0.5rem;
            }
            
            .login-subtitle {
                margin-bottom: 1rem;
            }
            
            .welcome-banner {
                padding: 1rem;
                margin-bottom: 0.75rem;
            }
        }

        /* Touch device optimizations */
        @media (hover: none) and (pointer: coarse) {
            /* Larger touch targets */
            div.stButton > button {
                min-height: 44px;
            }
            
            .stRadio > div > label {
                min-height: 44px;
            }
            
            .stCheckbox > label {
                min-height: 44px;
            }
            
            /* Remove hover effects that don't work on touch */
            .menu-card:hover {
                transform: none;
            }
            
            .menu-card:active {
                transform: scale(0.98);
                background: linear-gradient(165deg, 
                    rgba(255, 255, 255, 0.06) 0%,
                    rgba(124, 92, 252, 0.06) 50%,
                    rgba(52, 211, 153, 0.03) 100%
                );
            }
            
            /* Seat cells touch feedback */
            .seat-cell:active {
                transform: scale(0.95);
            }
        }

        /* High contrast mode support */
        @media (prefers-contrast: high) {
            :root {
                --border-default: rgba(255, 255, 255, 0.2);
                --border-hover: rgba(124, 92, 252, 0.5);
                --text-muted: #B8C0CC;
            }
            
            div.stButton > button {
                border-width: 2px !important;
            }
            
            .stTextInput > div > div > input,
            .stTextArea textarea {
                border-width: 2px !important;
            }
        }

        /* ═══════════════════════════════════════════════════════
           HIGH DPI / RETINA ADJUSTMENTS
           ═══════════════════════════════════════════════════════ */
        @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
            .star--sm { box-shadow: 0 0 1.5px rgba(255, 255, 255, 0.2); }
            .star--md { box-shadow: 0 0 3px rgba(200, 210, 255, 0.3); }
        }

        /* ═══════════════════════════════════════════════════════════════════
           EQUIVISION — ULTRA-PREMIUM ENHANCEMENTS v5.5
           World-class micro-interactions & advanced effects
           ═══════════════════════════════════════════════════════════════════ */

        /* ══════════════ BUTTON RIPPLE EFFECT ══════════════ */
        div.stButton > button {
            position: relative;
            overflow: hidden;
            transform-style: preserve-3d;
            perspective: 1000px;
        }

        div.stButton > button .ripple {
            position: absolute;
            border-radius: 50%;
            transform: scale(0);
            animation: rippleEffect 0.6s linear;
            background: rgba(255, 255, 255, 0.25);
            pointer-events: none;
        }

        @keyframes rippleEffect {
            to { transform: scale(4); opacity: 0; }
        }

        /* Button 3D lift on hover */
        div.stButton > button:hover {
            transform: translate3d(0, -3px, 0) rotateX(2deg) scale(1.015);
            box-shadow:
                0 12px 35px rgba(124, 92, 252, 0.35),
                0 4px 12px rgba(0,0,0,0.2),
                0 1px 3px rgba(0,0,0,0.15),
                inset 0 1px 0 rgba(255,255,255,0.2) !important;
        }

        /* Magnetic button effect - subtle movement toward cursor */
        div.stButton > button:hover::after {
            content: '';
            position: absolute;
            inset: 0;
            background: radial-gradient(
                circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
                rgba(255,255,255,0.15) 0%,
                transparent 50%
            );
            opacity: 1;
            pointer-events: none;
        }

        /* ══════════════ SKELETON LOADING ANIMATION ══════════════ */
        @keyframes skeletonPulse {
            0%, 100% { 
                background-position: 200% 50%;
                opacity: 0.6;
            }
            50% { 
                background-position: -200% 50%;
                opacity: 1;
            }
        }

        .skeleton-loader {
            background: linear-gradient(
                90deg,
                rgba(255,255,255,0.03) 0%,
                rgba(124, 92, 252, 0.08) 25%,
                rgba(255,255,255,0.12) 50%,
                rgba(124, 92, 252, 0.08) 75%,
                rgba(255,255,255,0.03) 100%
            );
            background-size: 400% 100%;
            animation: skeletonPulse 2s ease-in-out infinite;
            border-radius: var(--radius-md);
        }

        /* ══════════════ FLOATING LABEL EFFECT FOR INPUTS ══════════════ */
        .stTextInput > div,
        .stNumberInput > div,
        .stDateInput > div {
            position: relative;
        }

        .stTextInput > div > div > input:not(:placeholder-shown) + label,
        .stTextInput > div > div > input:focus + label {
            transform: translateY(-1.6rem) scale(0.85);
            color: var(--primary-400);
            font-weight: 600;
        }

        /* Enhanced input focus ring with glow animation */
        .stTextInput > div > div > input:focus,
        .stDateInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea textarea:focus {
            border-color: var(--primary-400) !important;
            box-shadow: 
                0 0 0 4px var(--primary-glow-soft),
                0 0 30px rgba(124, 92, 252, 0.1),
                0 4px 20px rgba(0,0,0,0.15) !important;
            background-color: rgba(0, 0, 0, 0.45) !important;
            outline: none !important;
            animation: inputFocusPulse 2s ease-in-out infinite;
        }

        @keyframes inputFocusPulse {
            0%, 100% { box-shadow: 0 0 0 4px var(--primary-glow-soft), 0 0 30px rgba(124, 92, 252, 0.1); }
            50% { box-shadow: 0 0 0 5px rgba(124, 92, 252, 0.18), 0 0 40px rgba(124, 92, 252, 0.15); }
        }

        /* Input typing animation cursor */
        .stTextInput > div > div > input:focus::placeholder {
            animation: typingCursor 1s steps(1) infinite;
        }

        @keyframes typingCursor {
            50% { opacity: 0; }
        }

        /* ══════════════ PREMIUM CHECKBOX / TOGGLE STYLING ══════════════ */
        .stCheckbox > label > div[data-testid="stCheckbox"] {
            position: relative;
        }

        .stCheckbox > label > div > div {
            width: 22px !important;
            height: 22px !important;
            border: 2px solid var(--border-default) !important;
            border-radius: 7px !important;
            background: var(--bg-input) !important;
            transition: all var(--duration-fast) var(--ease-spring) !important;
            position: relative;
        }

        .stCheckbox > label > div > div:hover {
            border-color: var(--primary-400) !important;
            box-shadow: 0 0 12px var(--primary-glow-soft);
            transform: scale(1.05);
        }

        .stCheckbox > label > div > div[aria-checked="true"] {
            background: linear-gradient(140deg, var(--primary-500), var(--primary-700)) !important;
            border-color: var(--primary-400) !important;
            box-shadow: 0 2px 10px rgba(124, 92, 252, 0.35);
            animation: checkBounce 0.35s var(--ease-spring);
        }

        @keyframes checkBounce {
            0% { transform: scale(0.8); }
            50% { transform: scale(1.15); }
            100% { transform: scale(1); }
        }

        /* Checkmark animation */
        .stCheckbox > label > div > div[aria-checked="true"]::after {
            content: '';
            position: absolute;
            left: 6px;
            top: 2px;
            width: 6px;
            height: 12px;
            border: solid white;
            border-width: 0 2.5px 2.5px 0;
            transform: rotate(45deg);
            animation: checkmarkDraw 0.2s ease-out 0.1s both;
        }

        @keyframes checkmarkDraw {
            from { clip-path: inset(100% 0 0 0); }
            to { clip-path: inset(0 0 0 0); }
        }

        /* Toggle Switch Enhancement */
        .stToggle [data-baseweb="checkbox"] {
            transform-origin: center;
            transition: all var(--duration-fast) var(--ease-spring) !important;
        }

        .stToggle [data-baseweb="checkbox"]:hover {
            transform: scale(1.03);
        }

        .stToggle [data-baseweb="checkbox"] > div {
            background: var(--bg-input) !important;
            border: 1px solid var(--border-default) !important;
            transition: all var(--duration-normal) var(--ease-out) !important;
        }

        .stToggle [data-baseweb="checkbox"][aria-checked="true"] > div {
            background: linear-gradient(90deg, var(--primary-500), var(--secondary-500)) !important;
            border-color: var(--primary-400) !important;
            box-shadow: 0 0 16px var(--primary-glow-soft), inset 0 1px 0 rgba(255,255,255,0.15);
        }

        /* ══════════════ ENHANCED TOOLTIP STYLING ══════════════ */
        [data-testid="stTooltipIcon"] {
            color: var(--text-faint) !important;
            transition: all var(--duration-fast) ease !important;
        }

        [data-testid="stTooltipIcon"]:hover {
            color: var(--primary-400) !important;
            transform: scale(1.15);
            filter: drop-shadow(0 0 6px var(--primary-glow-soft));
        }

        /* Tooltip bubble enhancement */
        [role="tooltip"],
        .stTooltipContent {
            background: rgba(15, 18, 25, 0.95) !important;
            backdrop-filter: blur(20px) saturate(1.8) !important;
            border: 1px solid var(--border-default) !important;
            border-radius: var(--radius-sm) !important;
            box-shadow: 
                0 8px 32px rgba(0,0,0,0.35),
                0 0 0 1px rgba(124, 92, 252, 0.1),
                inset 0 1px 0 rgba(255,255,255,0.05) !important;
            padding: 0.75rem 1rem !important;
            animation: tooltipFadeIn 0.2s var(--ease-out) !important;
        }

        @keyframes tooltipFadeIn {
            from { opacity: 0; transform: translateY(4px) scale(0.96); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        /* ══════════════ ENHANCED ALERT/NOTIFICATION STYLING ══════════════ */
        .stAlert, [data-testid="stAlert"] {
            animation: alertSlideIn 0.4s var(--ease-out) !important;
            position: relative;
            overflow: hidden;
        }

        @keyframes alertSlideIn {
            from { 
                opacity: 0; 
                transform: translateX(-12px);
                filter: blur(4px);
            }
            to { 
                opacity: 1; 
                transform: translateX(0);
                filter: blur(0);
            }
        }

        /* Alert left accent bar animation */
        .stAlert::before,
        [data-testid="stAlert"]::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            border-radius: 4px 0 0 4px;
            animation: alertBarGrow 0.5s var(--ease-out) 0.1s both;
        }

        @keyframes alertBarGrow {
            from { transform: scaleY(0); }
            to { transform: scaleY(1); }
        }

        /* Success alert */
        div[data-testid="stAlert"][data-baseweb*="positive"]::before,
        .element-container:has(.stSuccess)::before {
            background: linear-gradient(180deg, var(--secondary-300), var(--secondary-500));
            box-shadow: 0 0 12px var(--secondary-glow);
        }

        /* Error alert */
        div[data-testid="stAlert"][data-baseweb*="negative"]::before {
            background: linear-gradient(180deg, var(--rose-400), var(--rose-600));
            box-shadow: 0 0 12px var(--rose-glow);
        }

        /* Warning alert */
        div[data-testid="stAlert"][data-baseweb*="warning"]::before {
            background: linear-gradient(180deg, var(--accent-300), var(--accent));
            box-shadow: 0 0 12px var(--accent-glow);
        }

        /* Info alert shimmer */
        div[data-testid="stAlert"]::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 60%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255,255,255,0.03),
                rgba(255,255,255,0.06),
                rgba(255,255,255,0.03),
                transparent
            );
            animation: alertShimmer 3s ease-in-out infinite;
            pointer-events: none;
        }

        @keyframes alertShimmer {
            0%, 100% { left: -100%; }
            50% { left: 150%; }
        }

        /* ══════════════ ENHANCED IMAGE STYLING ══════════════ */
        .stImage {
            position: relative;
            overflow: hidden;
            border-radius: var(--radius-lg) !important;
        }

        .stImage::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            border: 1px solid var(--border-subtle);
            pointer-events: none;
            z-index: 1;
            transition: border-color var(--duration-normal) ease;
        }

        .stImage:hover::before {
            border-color: var(--border-hover);
        }

        .stImage img {
            border-radius: var(--radius-lg) !important;
            transition: 
                transform var(--duration-slow) var(--ease-out),
                filter var(--duration-normal) ease !important;
            will-change: transform;
        }

        .stImage:hover img {
            transform: scale(1.02);
            filter: brightness(1.03) contrast(1.02);
        }

        /* Image reflection/glow effect on hover */
        .stImage::after {
            content: '';
            position: absolute;
            bottom: -50%;
            left: 10%;
            right: 10%;
            height: 50%;
            background: inherit;
            filter: blur(25px);
            opacity: 0;
            transition: opacity var(--duration-normal) ease;
            pointer-events: none;
            z-index: -1;
        }

        .stImage:hover::after {
            opacity: 0.15;
        }

        /* ══════════════ ENHANCED SPINNER / LOADER ══════════════ */
        .stSpinner > div {
            position: relative;
        }

        .stSpinner > div::before {
            content: '';
            position: absolute;
            inset: -4px;
            border-radius: 50%;
            background: conic-gradient(
                from 0deg,
                transparent,
                var(--primary-glow-soft),
                var(--primary-400),
                var(--secondary-400),
                transparent
            );
            animation: spinnerGlow 1.5s linear infinite;
            opacity: 0.5;
            filter: blur(8px);
        }

        @keyframes spinnerGlow {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        /* Custom loading dots animation */
        .loading-dots {
            display: inline-flex;
            gap: 4px;
        }

        .loading-dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--primary-400);
            animation: dotBounce 1.4s ease-in-out infinite both;
        }

        .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
        .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
        .loading-dots span:nth-child(3) { animation-delay: 0s; }

        @keyframes dotBounce {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }

        /* ══════════════ ENHANCED SELECTBOX/DROPDOWN ══════════════ */
        .stSelectbox > div > div,
        .stMultiSelect > div > div {
            transition: all var(--duration-fast) var(--ease-out) !important;
        }

        .stSelectbox > div > div:hover,
        .stMultiSelect > div > div:hover {
            border-color: var(--border-hover) !important;
            box-shadow: 0 4px 16px rgba(124, 92, 252, 0.08);
        }

        /* Dropdown menu enhancement */
        [data-baseweb="popover"],
        [data-baseweb="menu"],
        [data-baseweb="select"] [role="listbox"] {
            background: rgba(15, 18, 25, 0.95) !important;
            backdrop-filter: blur(24px) saturate(1.8) !important;
            border: 1px solid var(--border-default) !important;
            border-radius: var(--radius-md) !important;
            box-shadow: 
                0 16px 48px rgba(0,0,0,0.4),
                0 0 0 1px rgba(124, 92, 252, 0.08),
                inset 0 1px 0 rgba(255,255,255,0.04) !important;
            animation: dropdownSlide 0.2s var(--ease-out) !important;
            overflow: hidden;
        }

        @keyframes dropdownSlide {
            from { opacity: 0; transform: translateY(-8px) scale(0.97); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        /* Dropdown option hover */
        [data-baseweb="menu"] li:hover,
        [role="option"]:hover {
            background: rgba(124, 92, 252, 0.1) !important;
            transition: background var(--duration-instant) ease !important;
        }

        [data-baseweb="menu"] li[aria-selected="true"],
        [role="option"][aria-selected="true"] {
            background: linear-gradient(90deg, rgba(124, 92, 252, 0.15), rgba(124, 92, 252, 0.08)) !important;
            border-left: 3px solid var(--primary-500);
        }

        /* ══════════════ ENHANCED EXPANDER ANIMATION ══════════════ */
        [data-testid="stExpander"] {
            transition: all var(--duration-normal) var(--ease-out) !important;
        }

        [data-testid="stExpander"] details {
            transition: all var(--duration-normal) var(--ease-out) !important;
        }

        [data-testid="stExpander"] details[open] {
            background: rgba(124, 92, 252, 0.02) !important;
        }

        [data-testid="stExpander"] details summary svg {
            transition: transform var(--duration-normal) var(--ease-spring) !important;
        }

        [data-testid="stExpander"] details[open] summary svg {
            transform: rotate(90deg);
        }

        /* Expander content slide animation */
        [data-testid="stExpander"] details > div {
            animation: expanderOpen 0.35s var(--ease-out);
        }

        @keyframes expanderOpen {
            from { 
                opacity: 0;
                transform: translateY(-8px);
                max-height: 0;
            }
            to { 
                opacity: 1;
                transform: translateY(0);
                max-height: 2000px;
            }
        }

        /* ══════════════ NUMBER INPUT ARROWS STYLING ══════════════ */
        .stNumberInput button {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: var(--radius-xs) !important;
            color: var(--text-secondary) !important;
            transition: all var(--duration-fast) var(--ease-out) !important;
        }

        .stNumberInput button:hover {
            background: rgba(124, 92, 252, 0.1) !important;
            border-color: var(--primary-400) !important;
            color: var(--primary-300) !important;
            transform: scale(1.08);
        }

        .stNumberInput button:active {
            transform: scale(0.95);
            background: rgba(124, 92, 252, 0.2) !important;
        }

        /* ══════════════ ENHANCED FILE UPLOADER ══════════════ */
        [data-testid="stFileUploader"] {
            position: relative;
            overflow: hidden;
        }

        [data-testid="stFileUploader"]::before {
            content: '';
            position: absolute;
            inset: 4px;
            border: 2px dashed var(--border-default);
            border-radius: calc(var(--radius-lg) - 4px);
            pointer-events: none;
            transition: all var(--duration-normal) ease;
        }

        [data-testid="stFileUploader"]:hover::before {
            border-color: var(--primary-400);
            animation: dashedBorderMove 0.8s linear infinite;
        }

        @keyframes dashedBorderMove {
            from { stroke-dashoffset: 0; }
            to { stroke-dashoffset: 20; }
        }

        /* File uploader drag active state */
        [data-testid="stFileUploader"]:focus-within {
            border-color: var(--primary-500) !important;
            background: rgba(124, 92, 252, 0.06) !important;
            box-shadow: 
                inset 0 0 40px rgba(124, 92, 252, 0.05),
                0 0 30px rgba(124, 92, 252, 0.08) !important;
        }

        /* Upload icon pulse animation */
        [data-testid="stFileUploader"] svg {
            animation: uploadIconFloat 3s ease-in-out infinite;
        }

        @keyframes uploadIconFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-4px); }
        }

        /* ══════════════ ENHANCED DATA EDITOR ══════════════ */
        [data-testid="stDataFrame"] [role="grid"] {
            border-radius: var(--radius-md) !important;
            overflow: hidden;
        }

        [data-testid="stDataFrame"] [role="gridcell"] {
            transition: background var(--duration-instant) ease !important;
        }

        [data-testid="stDataFrame"] [role="gridcell"]:focus {
            outline: 2px solid var(--primary-400) !important;
            outline-offset: -2px;
            background: rgba(124, 92, 252, 0.08) !important;
        }

        /* Row selection animation */
        [data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {
            background: rgba(124, 92, 252, 0.04) !important;
        }

        /* ══════════════ COPY BUTTON ENHANCEMENT ══════════════ */
        .stCodeBlock button,
        button[aria-label*="Copy"] {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-subtle) !important;
            border-radius: var(--radius-xs) !important;
            transition: all var(--duration-fast) var(--ease-out) !important;
        }

        .stCodeBlock button:hover,
        button[aria-label*="Copy"]:hover {
            background: rgba(124, 92, 252, 0.15) !important;
            border-color: var(--primary-400) !important;
            transform: scale(1.05);
        }

        .stCodeBlock button:active,
        button[aria-label*="Copy"]:active {
            transform: scale(0.95);
        }

        /* Copy success state */
        .stCodeBlock button[data-copied="true"]::after {
            content: '✓';
            position: absolute;
            animation: copySuccess 0.3s var(--ease-spring);
        }

        @keyframes copySuccess {
            from { transform: scale(0); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        /* ══════════════ ENHANCED RADIO BUTTONS ══════════════ */
        .stRadio > div > label {
            position: relative;
            overflow: hidden;
        }

        .stRadio > div > label::before {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(124, 92, 252, 0.04),
                transparent
            );
            transform: translateX(-100%);
            transition: transform 0.5s ease;
        }

        .stRadio > div > label:hover::before {
            transform: translateX(100%);
        }

        /* Selected radio glow */
        .stRadio > div > label[data-baseweb="radio"]:has(input:checked) {
            background: linear-gradient(140deg, rgba(124, 92, 252, 0.12), rgba(124, 92, 252, 0.05)) !important;
            border-color: var(--primary-400) !important;
            box-shadow: 
                0 4px 16px rgba(124, 92, 252, 0.15),
                inset 0 1px 0 rgba(255,255,255,0.05) !important;
        }

        /* ══════════════ CAMERA INPUT ENHANCEMENT ══════════════ */
        div[data-testid="stCameraInput"] {
            position: relative;
        }

        div[data-testid="stCameraInput"]::before {
            content: '';
            position: absolute;
            inset: -2px;
            border-radius: calc(var(--radius-lg) + 2px);
            background: linear-gradient(
                135deg,
                var(--primary-500),
                var(--secondary-500),
                var(--primary-500)
            );
            background-size: 300% 300%;
            animation: cameraGradient 4s ease infinite;
            z-index: -1;
            opacity: 0;
            transition: opacity var(--duration-normal) ease;
        }

        div[data-testid="stCameraInput"]:hover::before {
            opacity: 1;
        }

        @keyframes cameraGradient {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        /* Camera button pulse when active */
        div[data-testid="stCameraInput"] button {
            animation: cameraPulse 2s ease-in-out infinite;
        }

        @keyframes cameraPulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(124, 92, 252, 0.4); }
            50% { box-shadow: 0 0 0 8px rgba(124, 92, 252, 0); }
        }

        /* ══════════════ TEXT SELECTION STYLING ══════════════ */
        ::selection {
            background: rgba(124, 92, 252, 0.35);
            color: white;
        }

        ::-moz-selection {
            background: rgba(124, 92, 252, 0.35);
            color: white;
        }

        /* ══════════════ LINK STYLING ══════════════ */
        a {
            color: var(--primary-300);
            text-decoration: none;
            position: relative;
            transition: color var(--duration-fast) ease;
        }

        a::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--primary-400), var(--secondary-400));
            transition: width var(--duration-normal) var(--ease-out);
        }

        a:hover {
            color: var(--primary-200);
        }

        a:hover::after {
            width: 100%;
        }

        /* ══════════════ ENHANCED FORM CONTAINER ══════════════ */
        div[data-testid="stForm"] {
            position: relative;
        }

        div[data-testid="stForm"]::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 60%;
            height: 1px;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(124, 92, 252, 0.2),
                rgba(52, 211, 153, 0.15),
                rgba(124, 92, 252, 0.2),
                transparent
            );
        }

        /* Form submit animation */
        div[data-testid="stForm"] div.stButton > button[type="submit"] {
            position: relative;
        }

        div[data-testid="stForm"] div.stButton > button[type="submit"]::before {
            content: '';
            position: absolute;
            inset: -3px;
            border-radius: calc(var(--radius-md) + 3px);
            background: linear-gradient(
                90deg,
                var(--primary-500),
                var(--secondary-500),
                var(--primary-500)
            );
            background-size: 200% 100%;
            animation: submitGlow 2s ease-in-out infinite;
            opacity: 0;
            z-index: -1;
            transition: opacity var(--duration-normal) ease;
        }

        div[data-testid="stForm"] div.stButton > button[type="submit"]:hover::before {
            opacity: 0.6;
        }

        @keyframes submitGlow {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        /* ══════════════ COLUMN HOVER EFFECTS ══════════════ */
        [data-testid="column"] > div > div {
            transition: transform var(--duration-normal) var(--ease-out);
        }

        [data-testid="column"]:hover > div > div {
            transform: translateY(-1px);
        }

        /* ══════════════ MARKDOWN CONTENT STYLING ══════════════ */
        .stMarkdown code {
            background: rgba(124, 92, 252, 0.12) !important;
            padding: 0.15em 0.4em !important;
            border-radius: var(--radius-xs) !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.88em !important;
            color: var(--primary-200) !important;
            border: 1px solid rgba(124, 92, 252, 0.15);
        }

        .stMarkdown blockquote {
            border-left: 3px solid var(--primary-500);
            padding-left: 1rem;
            margin-left: 0;
            background: rgba(124, 92, 252, 0.03);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            padding: 0.75rem 1rem;
        }

        /* ══════════════ BADGE STYLING ══════════════ */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.7rem;
            border-radius: var(--radius-full);
            font-size: 0.72rem;
            font-weight: 600;
            font-family: 'Space Grotesk', sans-serif;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            animation: badgePop 0.3s var(--ease-spring);
        }

        .badge-purple {
            background: linear-gradient(140deg, rgba(124, 92, 252, 0.2), rgba(124, 92, 252, 0.1));
            color: var(--primary-200);
            border: 1px solid rgba(124, 92, 252, 0.25);
        }

        .badge-green {
            background: linear-gradient(140deg, rgba(52, 211, 153, 0.2), rgba(52, 211, 153, 0.1));
            color: var(--secondary-300);
            border: 1px solid rgba(52, 211, 153, 0.25);
        }

        .badge-rose {
            background: linear-gradient(140deg, rgba(244, 63, 94, 0.2), rgba(244, 63, 94, 0.1));
            color: var(--rose-400);
            border: 1px solid rgba(244, 63, 94, 0.25);
        }

        @keyframes badgePop {
            from { transform: scale(0.8); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        /* ══════════════ GLASS CARD VARIATIONS ══════════════ */
        .card-glow-purple {
            box-shadow: 
                var(--shadow-card),
                0 0 40px rgba(124, 92, 252, 0.08),
                inset 0 0 30px rgba(124, 92, 252, 0.02) !important;
        }

        .card-glow-green {
            box-shadow: 
                var(--shadow-card),
                0 0 40px rgba(52, 211, 153, 0.08),
                inset 0 0 30px rgba(52, 211, 153, 0.02) !important;
        }

        /* ══════════════ FOCUS RING IMPROVEMENTS ══════════════ */
        *:focus-visible {
            outline: 2px solid var(--primary-400) !important;
            outline-offset: 3px;
            border-radius: var(--radius-xs);
            animation: focusRingPulse 1.5s ease-in-out infinite;
        }

        @keyframes focusRingPulse {
            0%, 100% { outline-offset: 3px; }
            50% { outline-offset: 4px; }
        }

        /* ══════════════ CURSOR ENHANCEMENTS ══════════════ */
        div.stButton > button,
        .stRadio label,
        .stCheckbox label,
        .stSelectbox,
        .stMultiSelect,
        .menu-card,
        .event-list-card,
        a {
            cursor: pointer;
        }

        /* ══════════════ PRINT STYLES ══════════════ */
        @media print {
            .stApp::before,
            .stApp::after,
            .aurora,
            #stars-container,
            .shooting-star {
                display: none !important;
            }

            body, .stApp {
                background: white !important;
                color: black !important;
            }

            * {
                animation: none !important;
                transition: none !important;
            }
        }

        /* ══════════════ UTILITY ANIMATIONS ══════════════ */
        .animate-fade-in {
            animation: fadeIn 0.5s var(--ease-out) both;
        }

        .animate-slide-up {
            animation: slideUp 0.5s var(--ease-out) both;
        }

        .animate-scale-in {
            animation: scaleIn 0.4s var(--ease-spring) both;
        }

        .animate-bounce-in {
            animation: bounceIn 0.6s var(--ease-bounce) both;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes scaleIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }

        @keyframes bounceIn {
            0% { opacity: 0; transform: scale(0.3); }
            50% { transform: scale(1.05); }
            70% { transform: scale(0.9); }
            100% { opacity: 1; transform: scale(1); }
        }

        /* ══════════════ STAGGER DELAY UTILITIES ══════════════ */
        .stagger-1 { animation-delay: 0.05s; }
        .stagger-2 { animation-delay: 0.1s; }
        .stagger-3 { animation-delay: 0.15s; }
        .stagger-4 { animation-delay: 0.2s; }
        .stagger-5 { animation-delay: 0.25s; }
        .stagger-6 { animation-delay: 0.3s; }

        /* ══════════════ SHIMMER TEXT EFFECT ══════════════ */
        .shimmer-text {
            background: linear-gradient(
                90deg,
                var(--text-primary) 0%,
                var(--primary-300) 25%,
                var(--text-primary) 50%,
                var(--secondary-300) 75%,
                var(--text-primary) 100%
            );
            background-size: 400% 100%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: shimmerText 4s ease-in-out infinite;
        }

        @keyframes shimmerText {
            0% { background-position: 100% 50%; }
            100% { background-position: -100% 50%; }
        }

        /* ══════════════ GLASS DIVIDER ══════════════ */
        .glass-divider {
            height: 1px;
            background: linear-gradient(
                90deg,
                transparent,
                var(--border-subtle) 10%,
                rgba(124, 92, 252, 0.2) 30%,
                rgba(52, 211, 153, 0.15) 50%,
                rgba(124, 92, 252, 0.2) 70%,
                var(--border-subtle) 90%,
                transparent
            );
            margin: 2rem 0;
            position: relative;
        }

        .glass-divider::after {
            content: '';
            position: absolute;
            top: -2px;
            left: 50%;
            transform: translateX(-50%);
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--primary-400);
            box-shadow: 0 0 12px var(--primary-glow);
        }

        /* ══════════════ FLOATING ICON ANIMATION ══════════════ */
        .float-icon {
            animation: floatIcon 3s ease-in-out infinite;
        }

        @keyframes floatIcon {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            25% { transform: translateY(-4px) rotate(2deg); }
            75% { transform: translateY(2px) rotate(-1deg); }
        }

        /* ══════════════ SUCCESS CHECKMARK ANIMATION ══════════════ */
        .success-check {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(140deg, var(--secondary-500), var(--secondary-700));
            display: flex;
            align-items: center;
            justify-content: center;
            animation: successPop 0.5s var(--ease-spring);
            box-shadow: 0 4px 20px var(--secondary-glow);
        }

        .success-check::after {
            content: '✓';
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
            animation: checkDraw 0.3s ease-out 0.2s both;
        }

        @keyframes successPop {
            0% { transform: scale(0); opacity: 0; }
            50% { transform: scale(1.2); }
            100% { transform: scale(1); opacity: 1; }
        }

        @keyframes checkDraw {
            from { opacity: 0; transform: scale(0.5); }
            to { opacity: 1; transform: scale(1); }
        }

        /* ══════════════ COUNTER ANIMATION ══════════════ */
        .counter-animate {
            display: inline-block;
            animation: counterPop 0.4s var(--ease-spring);
        }

        @keyframes counterPop {
            0% { transform: scale(1.5); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }

        /* ══════════════ CARD STACK EFFECT ══════════════ */
        .card-stack {
            position: relative;
        }

        .card-stack::before,
        .card-stack::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            z-index: -1;
        }

        .card-stack::before {
            transform: translateY(6px) translateX(3px) rotate(1deg);
            opacity: 0.5;
        }

        .card-stack::after {
            transform: translateY(12px) translateX(6px) rotate(2deg);
            opacity: 0.3;
        }

        /* ══════════════ NOTIFICATION DOT ══════════════ */
        .notification-dot {
            position: relative;
        }

        .notification-dot::after {
            content: '';
            position: absolute;
            top: -2px;
            right: -2px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--rose-500);
            border: 2px solid var(--bg-base);
            animation: notificationPulse 2s ease-in-out infinite;
        }

        @keyframes notificationPulse {
            0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(244, 63, 94, 0.5); }
            50% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(244, 63, 94, 0); }
        }

        /* ═══════════════════════════════════════════════════════════════════════════
           🌌 PREMIUM FUTURISTIC ENHANCEMENTS v6.0 - Ultra Modern UI System
           ═══════════════════════════════════════════════════════════════════════════ */

        /* ══════════════ ANIMATED STARFIELD BACKGROUND ══════════════ */
        @keyframes twinkle {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.2); }
        }

        @keyframes starFloat {
            0% { transform: translateY(0) translateX(0); }
            25% { transform: translateY(-10px) translateX(5px); }
            50% { transform: translateY(-5px) translateX(-5px); }
            75% { transform: translateY(5px) translateX(3px); }
            100% { transform: translateY(0) translateX(0); }
        }

        .stApp {
            position: relative;
        }

        /* Star Layer 1 - Small fast stars */
        .stars-layer-1 {
            position: fixed;
            inset: 0;
            background-image: 
                radial-gradient(1px 1px at 10% 20%, rgba(255,255,255,0.6) 1px, transparent 0),
                radial-gradient(1px 1px at 30% 40%, rgba(255,255,255,0.5) 1px, transparent 0),
                radial-gradient(1px 1px at 50% 10%, rgba(255,255,255,0.7) 1px, transparent 0),
                radial-gradient(1px 1px at 70% 60%, rgba(255,255,255,0.4) 1px, transparent 0),
                radial-gradient(1px 1px at 90% 30%, rgba(255,255,255,0.6) 1px, transparent 0),
                radial-gradient(1px 1px at 15% 80%, rgba(255,255,255,0.5) 1px, transparent 0),
                radial-gradient(1px 1px at 85% 85%, rgba(255,255,255,0.4) 1px, transparent 0),
                radial-gradient(1px 1px at 45% 70%, rgba(255,255,255,0.6) 1px, transparent 0);
            animation: starFloat 60s ease-in-out infinite;
            pointer-events: none;
            z-index: 0;
        }

        /* Star Layer 2 - Medium twinkling stars */
        .stars-layer-2 {
            position: fixed;
            inset: 0;
            background-image:
                radial-gradient(2px 2px at 25% 35%, rgba(124, 92, 252, 0.8) 1px, transparent 0),
                radial-gradient(2px 2px at 65% 15%, rgba(52, 211, 153, 0.7) 1px, transparent 0),
                radial-gradient(2px 2px at 85% 45%, rgba(255, 255, 255, 0.9) 1px, transparent 0),
                radial-gradient(2px 2px at 35% 75%, rgba(245, 158, 11, 0.6) 1px, transparent 0),
                radial-gradient(2px 2px at 55% 55%, rgba(124, 92, 252, 0.7) 1px, transparent 0);
            animation: twinkle 4s ease-in-out infinite, starFloat 80s ease-in-out infinite reverse;
            pointer-events: none;
            z-index: 0;
        }

        /* Star Layer 3 - Large glowing stars */
        .stars-layer-3 {
            position: fixed;
            inset: 0;
            background-image:
                radial-gradient(3px 3px at 20% 50%, rgba(255,255,255,0.9) 1px, transparent 0),
                radial-gradient(4px 4px at 75% 25%, rgba(124, 92, 252, 0.8) 1px, transparent 0),
                radial-gradient(3px 3px at 40% 90%, rgba(52, 211, 153, 0.7) 1px, transparent 0);
            animation: twinkle 6s ease-in-out infinite 2s;
            pointer-events: none;
            z-index: 0;
        }

        /* ══════════════ GRADIENT MESH ANIMATED BACKGROUND ══════════════ */
        @keyframes gradientShift {
            0% { 
                background-position: 0% 50%;
                filter: hue-rotate(0deg);
            }
            25% { background-position: 50% 100%; }
            50% { 
                background-position: 100% 50%;
                filter: hue-rotate(15deg);
            }
            75% { background-position: 50% 0%; }
            100% { 
                background-position: 0% 50%;
                filter: hue-rotate(0deg);
            }
        }

        .gradient-mesh-bg {
            position: fixed;
            inset: 0;
            background: 
                linear-gradient(45deg, rgba(124, 92, 252, 0.03), transparent 40%),
                linear-gradient(135deg, rgba(52, 211, 153, 0.02), transparent 40%),
                linear-gradient(225deg, rgba(245, 158, 11, 0.015), transparent 40%),
                linear-gradient(315deg, rgba(244, 63, 94, 0.01), transparent 40%);
            background-size: 400% 400%;
            animation: gradientShift 30s ease infinite;
            pointer-events: none;
            z-index: -1;
        }

        /* ══════════════ MAGNETIC HOVER BUTTONS ══════════════ */
        .magnetic-btn {
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }

        .magnetic-btn:hover {
            transform: translate3d(var(--mx, 0), var(--my, 0), 0);
        }

        /* ══════════════ NEON GLOW BUTTONS ══════════════ */
        [data-testid="stButton"] > button {
            position: relative;
            overflow: hidden;
            isolation: isolate;
        }

        [data-testid="stButton"] > button::before {
            content: '';
            position: absolute;
            inset: -2px;
            background: linear-gradient(135deg, var(--primary-500), var(--secondary-500), var(--primary-500));
            background-size: 200% 200%;
            border-radius: inherit;
            z-index: -2;
            opacity: 0;
            transition: opacity 0.4s ease;
            animation: borderGlow 3s ease infinite paused;
        }

        [data-testid="stButton"] > button:hover::before {
            opacity: 1;
            animation-play-state: running;
        }

        [data-testid="stButton"] > button::after {
            content: '';
            position: absolute;
            inset: 1px;
            background: var(--bg-elevated);
            border-radius: calc(var(--radius-md) - 1px);
            z-index: -1;
            transition: background 0.3s ease;
        }

        [data-testid="stButton"] > button:hover::after {
            background: linear-gradient(135deg, rgba(124, 92, 252, 0.15), rgba(52, 211, 153, 0.1));
        }

        @keyframes borderGlow {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        /* Neon edge lighting on hover */
        [data-testid="stButton"] > button:hover {
            box-shadow: 
                0 0 20px rgba(124, 92, 252, 0.4),
                0 0 40px rgba(124, 92, 252, 0.2),
                0 0 60px rgba(124, 92, 252, 0.1),
                inset 0 0 30px rgba(124, 92, 252, 0.05);
        }

        /* ══════════════ RIPPLE CLICK ANIMATION ══════════════ */
        @keyframes rippleSpread {
            0% {
                transform: translate(-50%, -50%) scale(0);
                opacity: 0.6;
            }
            100% {
                transform: translate(-50%, -50%) scale(4);
                opacity: 0;
            }
        }

        .ripple-effect {
            position: absolute;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.4) 0%, transparent 70%);
            width: 100px;
            height: 100px;
            pointer-events: none;
            animation: rippleSpread 0.6s ease-out forwards;
        }

        /* ══════════════ FLOATING CARDS WITH SOFT SHADOWS ══════════════ */
        @keyframes floatCard {
            0%, 100% { 
                transform: translateY(0) rotateX(0) rotateY(0);
                box-shadow: var(--shadow-card);
            }
            25% { 
                transform: translateY(-4px) rotateX(1deg) rotateY(-0.5deg);
            }
            50% { 
                transform: translateY(-8px) rotateX(0) rotateY(0);
                box-shadow: var(--shadow-xl), 0 30px 60px rgba(124, 92, 252, 0.08);
            }
            75% { 
                transform: translateY(-4px) rotateX(-1deg) rotateY(0.5deg);
            }
        }

        .float-card {
            animation: floatCard 6s ease-in-out infinite;
            transform-style: preserve-3d;
            perspective: 1000px;
        }

        /* ══════════════ 3D TILT EFFECT ON MOUSE ══════════════ */
        .tilt-card {
            transform-style: preserve-3d;
            transition: transform 0.15s ease-out;
            will-change: transform;
        }

        .tilt-card:hover {
            transform: perspective(1000px) rotateX(var(--tilt-x, 0deg)) rotateY(var(--tilt-y, 0deg)) scale(1.02);
        }

        .tilt-card::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: linear-gradient(
                135deg,
                rgba(255, 255, 255, 0.15) 0%,
                transparent 50%,
                rgba(0, 0, 0, 0.1) 100%
            );
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }

        .tilt-card:hover::before {
            opacity: 1;
        }

        /* ══════════════ HERO GRADIENT TEXT ══════════════ */
        .hero-text {
            font-size: 3.5rem !important;
            font-weight: 900 !important;
            background: linear-gradient(
                135deg,
                #FFFFFF 0%,
                var(--primary-300) 25%,
                var(--secondary-300) 50%,
                var(--accent-300) 75%,
                #FFFFFF 100%
            );
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: heroGradient 8s ease infinite;
            filter: drop-shadow(0 4px 20px rgba(124, 92, 252, 0.3));
        }

        @keyframes heroGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* ══════════════ TEXT SHIMMER EFFECT ══════════════ */
        .shimmer-text {
            position: relative;
            display: inline-block;
            background: linear-gradient(
                120deg,
                var(--text-secondary) 0%,
                var(--text-secondary) 40%,
                #FFFFFF 50%,
                var(--text-secondary) 60%,
                var(--text-secondary) 100%
            );
            background-size: 200% 100%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: shimmerPass 3s ease-in-out infinite;
        }

        @keyframes shimmerPass {
            0% { background-position: 100% 0; }
            100% { background-position: -100% 0; }
        }

        /* ══════════════ TYPEWRITER ANIMATION ══════════════ */
        .typewriter {
            overflow: hidden;
            border-right: 2px solid var(--primary-500);
            white-space: nowrap;
            animation: 
                typewriter 3s steps(40, end),
                blinkCursor 0.75s step-end infinite;
        }

        @keyframes typewriter {
            from { width: 0; }
            to { width: 100%; }
        }

        @keyframes blinkCursor {
            from, to { border-color: transparent; }
            50% { border-color: var(--primary-500); }
        }

        /* ══════════════ ANIMATED COUNTERS ══════════════ */
        .counter-number {
            display: inline-block;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--primary-300), var(--secondary-300));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: counterBounce 0.5s var(--ease-spring);
        }

        @keyframes counterBounce {
            0% { transform: scale(0.5) translateY(20px); opacity: 0; }
            60% { transform: scale(1.1) translateY(-5px); }
            100% { transform: scale(1) translateY(0); opacity: 1; }
        }

        /* ══════════════ GLASS NAVBAR STICKY ══════════════ */
        .glass-navbar {
            position: sticky;
            top: 0;
            z-index: 1000;
            background: rgba(15, 18, 25, 0.7);
            backdrop-filter: blur(20px) saturate(1.8);
            -webkit-backdrop-filter: blur(20px) saturate(1.8);
            border-bottom: 1px solid var(--border-subtle);
            transition: all 0.3s ease;
        }

        .glass-navbar.scrolled {
            background: rgba(15, 18, 25, 0.95);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        }

        /* ══════════════ SCROLL PROGRESS INDICATOR ══════════════ */
        .scroll-progress {
            position: fixed;
            top: 0;
            left: 0;
            width: var(--scroll-progress, 0%);
            height: 3px;
            background: linear-gradient(90deg, var(--primary-500), var(--secondary-500), var(--accent));
            z-index: 9999;
            transition: width 0.1s ease;
            box-shadow: 0 0 10px var(--primary-glow);
        }

        /* ══════════════ CUSTOM GRADIENT SCROLLBAR ══════════════ */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, var(--primary-500) 0%, var(--secondary-500) 50%, var(--accent) 100%);
            border-radius: 10px;
            border: 2px solid transparent;
            background-clip: padding-box;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, var(--primary-400) 0%, var(--secondary-400) 50%, var(--accent-300) 100%);
        }

        /* ══════════════ SMOOTH SCROLL SNAP SECTIONS ══════════════ */
        .scroll-snap-container {
            scroll-snap-type: y mandatory;
            overflow-y: scroll;
            height: 100vh;
        }

        .scroll-snap-section {
            scroll-snap-align: start;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* ══════════════ ICON HOVER ANIMATIONS ══════════════ */
        .icon-hover {
            display: inline-flex;
            transition: all 0.3s var(--ease-spring);
        }

        .icon-hover:hover {
            transform: scale(1.15) rotate(-5deg);
            filter: drop-shadow(0 0 8px var(--primary-glow));
        }

        /* Bounce on hover */
        .icon-bounce:hover {
            animation: iconBounce 0.5s var(--ease-spring);
        }

        @keyframes iconBounce {
            0%, 100% { transform: translateY(0); }
            25% { transform: translateY(-6px); }
            50% { transform: translateY(0); }
            75% { transform: translateY(-3px); }
        }

        /* Shake on hover */
        .icon-shake:hover {
            animation: iconShake 0.4s ease;
        }

        @keyframes iconShake {
            0%, 100% { transform: translateX(0); }
            20% { transform: translateX(-3px) rotate(-5deg); }
            40% { transform: translateX(3px) rotate(5deg); }
            60% { transform: translateX(-2px) rotate(-3deg); }
            80% { transform: translateX(2px) rotate(3deg); }
        }

        /* Pulse glow on hover */
        .icon-glow:hover {
            animation: iconPulseGlow 1s ease infinite;
        }

        @keyframes iconPulseGlow {
            0%, 100% { filter: drop-shadow(0 0 5px var(--primary-glow)); }
            50% { filter: drop-shadow(0 0 15px var(--primary-glow)) drop-shadow(0 0 25px var(--primary-glow-soft)); }
        }

        /* ══════════════ SKELETON LOADING PREMIUM ══════════════ */
        @keyframes skeletonShimmer {
            0% {
                background-position: -200% 0;
            }
            100% {
                background-position: 200% 0;
            }
        }

        .skeleton-premium {
            background: linear-gradient(
                90deg,
                rgba(255, 255, 255, 0.02) 0%,
                rgba(255, 255, 255, 0.05) 20%,
                rgba(124, 92, 252, 0.08) 40%,
                rgba(52, 211, 153, 0.06) 60%,
                rgba(255, 255, 255, 0.05) 80%,
                rgba(255, 255, 255, 0.02) 100%
            );
            background-size: 200% 100%;
            animation: skeletonShimmer 2s ease infinite;
            border-radius: var(--radius-md);
        }

        /* ══════════════ PAGE TRANSITION ANIMATIONS ══════════════ */
        @keyframes fadeSlideIn {
            0% {
                opacity: 0;
                transform: translateY(30px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes fadeSlideOut {
            0% {
                opacity: 1;
                transform: translateY(0);
            }
            100% {
                opacity: 0;
                transform: translateY(-30px);
            }
        }

        .page-transition-in {
            animation: fadeSlideIn 0.5s var(--ease-out) forwards;
        }

        .page-transition-out {
            animation: fadeSlideOut 0.3s var(--ease-smooth) forwards;
        }

        /* ══════════════ CONFETTI/SPARKLE SUCCESS EFFECT ══════════════ */
        @keyframes confettiFloat {
            0% {
                transform: translateY(0) rotate(0deg);
                opacity: 1;
            }
            100% {
                transform: translateY(-100vh) rotate(720deg);
                opacity: 0;
            }
        }

        .confetti-particle {
            position: fixed;
            width: 10px;
            height: 10px;
            pointer-events: none;
            z-index: 10000;
            animation: confettiFloat 3s ease-out forwards;
        }

        .confetti-particle:nth-child(odd) {
            background: var(--primary-500);
            border-radius: 50%;
        }

        .confetti-particle:nth-child(even) {
            background: var(--secondary-500);
            clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
        }

        /* Sparkle effect */
        @keyframes sparkle {
            0%, 100% { opacity: 0; transform: scale(0) rotate(0deg); }
            50% { opacity: 1; transform: scale(1) rotate(180deg); }
        }

        .sparkle {
            position: absolute;
            width: 20px;
            height: 20px;
            background: radial-gradient(circle, #FFF 0%, transparent 70%);
            animation: sparkle 0.8s ease-in-out forwards;
            pointer-events: none;
        }

        /* ══════════════ DARK/LIGHT THEME TRANSITION ══════════════ */
        .theme-transition {
            transition: 
                background-color 0.5s ease,
                color 0.5s ease,
                border-color 0.5s ease,
                box-shadow 0.5s ease !important;
        }

        /* ══════════════ CURSOR GLOW EFFECT ══════════════ */
        .cursor-glow {
            position: fixed;
            width: 300px;
            height: 300px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(124, 92, 252, 0.08) 0%, transparent 70%);
            pointer-events: none;
            z-index: 9998;
            transform: translate(-50%, -50%);
            transition: opacity 0.3s ease;
            mix-blend-mode: screen;
        }

        /* ══════════════ WELCOME ANIMATION AFTER LOGIN ══════════════ */
        @keyframes welcomeReveal {
            0% {
                opacity: 0;
                transform: scale(0.9) translateY(50px);
                filter: blur(10px);
            }
            50% {
                filter: blur(5px);
            }
            100% {
                opacity: 1;
                transform: scale(1) translateY(0);
                filter: blur(0);
            }
        }

        .welcome-animation {
            animation: welcomeReveal 0.8s var(--ease-out) forwards;
        }

        /* Staggered children animation */
        .welcome-animation > *:nth-child(1) { animation-delay: 0.1s; }
        .welcome-animation > *:nth-child(2) { animation-delay: 0.2s; }
        .welcome-animation > *:nth-child(3) { animation-delay: 0.3s; }
        .welcome-animation > *:nth-child(4) { animation-delay: 0.4s; }
        .welcome-animation > *:nth-child(5) { animation-delay: 0.5s; }

        /* ══════════════ EXPANDABLE ACCORDION PREMIUM ══════════════ */
        [data-testid="stExpander"] {
            overflow: hidden;
            transition: all 0.4s var(--ease-out);
        }

        [data-testid="stExpander"] summary {
            padding: 1rem 1.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        [data-testid="stExpander"] summary:hover {
            background: rgba(124, 92, 252, 0.05);
        }

        [data-testid="stExpander"][open] {
            background: rgba(124, 92, 252, 0.02);
            border-color: var(--border-hover);
        }

        [data-testid="stExpander"] details[open] > div {
            animation: accordionSlideDown 0.4s var(--ease-out);
        }

        @keyframes accordionSlideDown {
            0% {
                opacity: 0;
                transform: translateY(-10px);
                max-height: 0;
            }
            100% {
                opacity: 1;
                transform: translateY(0);
                max-height: 1000px;
            }
        }

        /* ══════════════ RESPONSIVE GRID AUTO-REARRANGE ══════════════ */
        .auto-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            transition: all 0.4s var(--ease-out);
        }

        .auto-grid > * {
            animation: gridItemAppear 0.5s var(--ease-out) forwards;
            opacity: 0;
        }

        @keyframes gridItemAppear {
            0% {
                opacity: 0;
                transform: scale(0.9) translateY(20px);
            }
            100% {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }

        /* Stagger grid items */
        .auto-grid > *:nth-child(1) { animation-delay: 0.05s; }
        .auto-grid > *:nth-child(2) { animation-delay: 0.1s; }
        .auto-grid > *:nth-child(3) { animation-delay: 0.15s; }
        .auto-grid > *:nth-child(4) { animation-delay: 0.2s; }
        .auto-grid > *:nth-child(5) { animation-delay: 0.25s; }
        .auto-grid > *:nth-child(6) { animation-delay: 0.3s; }

        /* ══════════════ GLASSMORPHISM PANELS PREMIUM ══════════════ */
        .glass-panel {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(24px) saturate(1.8);
            -webkit-backdrop-filter: blur(24px) saturate(1.8);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: var(--radius-xl);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.08),
                inset 0 -1px 0 rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }

        /* Glass reflection */
        .glass-panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 50%;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, transparent 100%);
            pointer-events: none;
        }

        /* ══════════════ ANIMATED GRADIENT BORDERS ══════════════ */
        .gradient-border-animated {
            position: relative;
            padding: 2px;
            border-radius: var(--radius-lg);
            background: linear-gradient(135deg, var(--primary-500), var(--secondary-500), var(--accent), var(--rose-500), var(--primary-500));
            background-size: 300% 300%;
            animation: gradientBorderMove 4s ease infinite;
        }

        .gradient-border-animated > * {
            background: var(--bg-base);
            border-radius: calc(var(--radius-lg) - 2px);
        }

        @keyframes gradientBorderMove {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* ══════════════ HOVER LIFT EFFECT ENHANCED ══════════════ */
        .hover-lift {
            transition: all 0.4s var(--ease-out);
        }

        .hover-lift:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 
                0 20px 40px rgba(0, 0, 0, 0.2),
                0 0 60px rgba(124, 92, 252, 0.1);
        }

        /* ══════════════ AMBIENT GLOW CONTAINERS ══════════════ */
        .ambient-glow {
            position: relative;
        }

        .ambient-glow::after {
            content: '';
            position: absolute;
            inset: -20px;
            background: radial-gradient(circle at center, var(--primary-glow-soft) 0%, transparent 70%);
            opacity: 0;
            transition: opacity 0.5s ease;
            pointer-events: none;
            z-index: -1;
        }

        .ambient-glow:hover::after {
            opacity: 1;
        }

        /* ══════════════ PREMIUM METRIC CARDS ══════════════ */
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.01)) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            padding: 1.5rem !important;
            position: relative;
            overflow: hidden;
        }

        [data-testid="stMetric"]::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary-500), var(--secondary-500));
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.5s var(--ease-out);
        }

        [data-testid="stMetric"]:hover::before {
            transform: scaleX(1);
        }

        /* ══════════════ SUCCESS/ERROR STATE ANIMATIONS ══════════════ */
        @keyframes successPulse {
            0% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.4); }
            70% { box-shadow: 0 0 0 15px rgba(52, 211, 153, 0); }
            100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
        }

        @keyframes errorShake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }

        .success-state {
            animation: successPulse 0.6s ease-out;
            border-color: var(--secondary-500) !important;
        }

        .error-state {
            animation: errorShake 0.5s ease;
            border-color: var(--rose-500) !important;
        }

        /* ══════════════ LOADING DOTS ANIMATION ══════════════ */
        .loading-dots {
            display: inline-flex;
            gap: 4px;
        }

        .loading-dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--primary-500);
            animation: dotPulse 1.4s ease-in-out infinite;
        }

        .loading-dots span:nth-child(1) { animation-delay: 0s; }
        .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
        .loading-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes dotPulse {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }

        /* ══════════════ GLOW TEXT ON IMPORTANT ELEMENTS ══════════════ */
        .glow-text {
            text-shadow: 
                0 0 10px var(--primary-glow),
                0 0 20px var(--primary-glow-soft),
                0 0 30px rgba(124, 92, 252, 0.1);
            animation: textGlow 2s ease-in-out infinite alternate;
        }

        @keyframes textGlow {
            0% {
                text-shadow: 
                    0 0 10px var(--primary-glow),
                    0 0 20px var(--primary-glow-soft);
            }
            100% {
                text-shadow: 
                    0 0 15px var(--primary-glow),
                    0 0 30px var(--primary-glow),
                    0 0 45px var(--primary-glow-soft);
            }
        }

        /* ══════════════ FUTURISTIC INPUT FIELDS ══════════════ */
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea {
            background: rgba(0, 0, 0, 0.3) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: var(--radius-md) !important;
            color: var(--text-primary) !important;
            transition: all 0.3s var(--ease-out) !important;
            position: relative;
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: var(--primary-500) !important;
            box-shadow: 
                0 0 0 3px rgba(124, 92, 252, 0.1),
                0 0 20px rgba(124, 92, 252, 0.1) !important;
            background: rgba(0, 0, 0, 0.4) !important;
        }

        /* Input glow line animation */
        [data-testid="stTextInput"]::after,
        [data-testid="stNumberInput"]::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            width: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--primary-500), var(--secondary-500));
            transition: all 0.3s var(--ease-out);
            transform: translateX(-50%);
        }

        [data-testid="stTextInput"]:focus-within::after,
        [data-testid="stNumberInput"]:focus-within::after {
            width: 100%;
        }

        /* ══════════════ PARALLAX SCROLL ELEMENTS ══════════════ */
        .parallax-slow {
            transform: translateY(calc(var(--scroll-y, 0) * 0.3));
            transition: transform 0.1s linear;
        }

        .parallax-fast {
            transform: translateY(calc(var(--scroll-y, 0) * -0.5));
            transition: transform 0.1s linear;
        }

        /* ══════════════ MORPHING SHAPES BACKGROUND ══════════════ */
        @keyframes morphBlob {
            0%, 100% {
                border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
            }
            25% {
                border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%;
            }
            50% {
                border-radius: 50% 60% 30% 60% / 30% 40% 70% 50%;
            }
            75% {
                border-radius: 60% 40% 60% 30% / 70% 50% 40% 60%;
            }
        }

        .morph-blob {
            position: fixed;
            width: 400px;
            height: 400px;
            background: linear-gradient(135deg, rgba(124, 92, 252, 0.05), rgba(52, 211, 153, 0.03));
            animation: morphBlob 20s ease-in-out infinite;
            filter: blur(60px);
            pointer-events: none;
            z-index: -1;
        }

        .morph-blob-1 {
            top: 10%;
            left: 10%;
            animation-delay: 0s;
        }

        .morph-blob-2 {
            bottom: 20%;
            right: 15%;
            animation-delay: -7s;
            background: linear-gradient(135deg, rgba(52, 211, 153, 0.04), rgba(245, 158, 11, 0.02));
        }

    </style>
    """, unsafe_allow_html=True)

def inject_premium_elements():
    """Inject premium futuristic UI elements - starfield, scroll progress, cursor glow, morphing blobs"""
    st.markdown("""
    <!-- Animated Starfield Layers -->
    <div class="stars-layer-1"></div>
    <div class="stars-layer-2"></div>
    <div class="stars-layer-3"></div>
    
    <!-- Gradient Mesh Background -->
    <div class="gradient-mesh-bg"></div>
    
    <!-- Morphing Blob Shapes -->
    <div class="morph-blob morph-blob-1"></div>
    <div class="morph-blob morph-blob-2"></div>
    
    <!-- Scroll Progress Indicator -->
    <div class="scroll-progress" id="scrollProgress"></div>
    
    <!-- Cursor Glow Effect -->
    <div class="cursor-glow" id="cursorGlow"></div>
    
    <script>
        // === SCROLL PROGRESS INDICATOR ===
        (function() {
            const scrollProgress = document.getElementById('scrollProgress');
            if (!scrollProgress) return;
            
            function updateScrollProgress() {
                const scrollTop = window.scrollY || document.documentElement.scrollTop;
                const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
                const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
                scrollProgress.style.width = progress + '%';
            }
            
            window.addEventListener('scroll', updateScrollProgress, { passive: true });
            updateScrollProgress();
        })();
        
        // === CURSOR GLOW EFFECT ===
        (function() {
            const cursorGlow = document.getElementById('cursorGlow');
            if (!cursorGlow) return;
            
            let mouseX = 0, mouseY = 0;
            let currentX = 0, currentY = 0;
            
            document.addEventListener('mousemove', (e) => {
                mouseX = e.clientX;
                mouseY = e.clientY;
            });
            
            function animateCursor() {
                currentX += (mouseX - currentX) * 0.1;
                currentY += (mouseY - currentY) * 0.1;
                cursorGlow.style.left = currentX + 'px';
                cursorGlow.style.top = currentY + 'px';
                requestAnimationFrame(animateCursor);
            }
            animateCursor();
        })();
        
        // === RIPPLE EFFECT ON BUTTONS ===
        (function() {
            document.addEventListener('click', (e) => {
                const btn = e.target.closest('[data-testid="stButton"] button');
                if (!btn) return;
                
                const ripple = document.createElement('span');
                ripple.className = 'ripple-effect';
                
                const rect = btn.getBoundingClientRect();
                ripple.style.left = (e.clientX - rect.left) + 'px';
                ripple.style.top = (e.clientY - rect.top) + 'px';
                
                btn.appendChild(ripple);
                setTimeout(() => ripple.remove(), 600);
            });
        })();
        
        // === 3D TILT EFFECT ON CARDS ===
        (function() {
            const cards = document.querySelectorAll('[data-testid="stMetric"], .menu-card, .person-card');
            
            cards.forEach(card => {
                card.addEventListener('mousemove', (e) => {
                    const rect = card.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    
                    const centerX = rect.width / 2;
                    const centerY = rect.height / 2;
                    
                    const rotateX = (y - centerY) / 10;
                    const rotateY = (centerX - x) / 10;
                    
                    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
                });
                
                card.addEventListener('mouseleave', () => {
                    card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
                });
            });
        })();
        
        // === MAGNETIC BUTTON EFFECT ===
        (function() {
            const buttons = document.querySelectorAll('[data-testid="stButton"] button');
            
            buttons.forEach(btn => {
                btn.addEventListener('mousemove', (e) => {
                    const rect = btn.getBoundingClientRect();
                    const x = e.clientX - rect.left - rect.width / 2;
                    const y = e.clientY - rect.top - rect.height / 2;
                    
                    btn.style.transform = `translate(${x * 0.1}px, ${y * 0.1}px)`;
                });
                
                btn.addEventListener('mouseleave', () => {
                    btn.style.transform = 'translate(0, 0)';
                });
            });
        })();
        
        // === PARALLAX SCROLL EFFECT ===
        (function() {
            window.addEventListener('scroll', () => {
                const scrollY = window.scrollY;
                document.documentElement.style.setProperty('--scroll-y', scrollY + 'px');
            }, { passive: true });
        })();
        
        // === ANIMATED COUNTER NUMBERS ===
        (function() {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const metric = entry.target.querySelector('[data-testid="stMetricValue"]');
                        if (metric) {
                            metric.classList.add('counter-animate');
                        }
                    }
                });
            }, { threshold: 0.5 });
            
            document.querySelectorAll('[data-testid="stMetric"]').forEach(el => observer.observe(el));
        })();
        
        // === SUCCESS CONFETTI EFFECT ===
        window.triggerConfetti = function() {
            const colors = ['#7C5CFC', '#34D399', '#F59E0B', '#F43F5E', '#38BDF8'];
            for (let i = 0; i < 50; i++) {
                const confetti = document.createElement('div');
                confetti.className = 'confetti-particle';
                confetti.style.left = Math.random() * 100 + 'vw';
                confetti.style.bottom = '-20px';
                confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.animationDuration = (2 + Math.random() * 2) + 's';
                confetti.style.animationDelay = Math.random() * 0.5 + 's';
                document.body.appendChild(confetti);
                setTimeout(() => confetti.remove(), 4000);
            }
        };
    </script>
    """, unsafe_allow_html=True)

local_css()
inject_premium_elements()

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
    # Starry Background Injection — Cinematic immersive starfield
    star_sizes = ['star--sm', 'star--md', 'star--lg']
    star_weights = [0.6, 0.3, 0.1]  # More small stars for realism
    import random as _r
    stars_html = "".join([
        f'<div class="star {_r.choices(star_sizes, weights=star_weights, k=1)[0]}" style="top:{_r.randint(0,100)}%;left:{_r.randint(0,100)}%;animation-duration:{_r.uniform(3,10):.1f}s;animation-delay:{_r.uniform(0,8):.1f}s;"></div>'
        for _ in range(180)
    ])
    # Add shooting stars — more frequent, varied speeds
    shooting_html = "".join([
        f'<div class="shooting-star" style="top:{_r.randint(3,45)}%;left:{_r.randint(5,75)}%;animation-delay:{_r.uniform(1,15):.1f}s;animation-duration:{_r.uniform(3,5):.1f}s;"></div>'
        for _ in range(6)
    ])
    st.markdown(f"""
    <div id="stars-container">{stars_html}{shooting_html}</div>
    <div class="aurora"></div>
    <div class="login-orbital" style="width:350px;height:350px;border-color:rgba(124,92,252,0.05);"></div>
    <div class="login-orbital" style="width:550px;height:550px;animation-duration:45s;border-color:rgba(52,211,153,0.03);"></div>
    """, unsafe_allow_html=True)
    
    render_header()
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-title">EquiVision</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Vision Beyond Bias &bull; Seeking Equality &bull; Shaping Fairness</div>', unsafe_allow_html=True)
        
        if st.session_state.auth_stage == 0:
            auth_mode = st.radio("Choose", ["Sign In", "Register"], horizontal=True, label_visibility="collapsed")
            
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if auth_mode == "Sign In":
                if st.button("Sign In", type="primary", use_container_width=True):
                    user = db.authenticate(username, password)
                    if user:
                        st.session_state.current_user = user['username']
                        st.session_state.user_id = user['id']
                        st.session_state.db_loaded = False
                        st.success("✅ Signed In!")
                        st.session_state.page = "home"
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials. Check username/password or Register.")
            else:
                if st.button("Create Account", type="primary", use_container_width=True):
                    if username and password:
                        user = db.create_user(username, password)
                        if user:
                            st.session_state.current_user = user['username']
                            st.session_state.user_id = user['id']
                            st.session_state.db_loaded = False
                            st.success("✅ Account Created & Signed In!")
                            st.session_state.page = "home"
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Username already taken. Try a different one.")
                    else:
                        st.error("Username and Password are required.")

def home_page():
    render_header()
    
    # Load data from DB if not already loaded
    if not st.session_state.db_loaded:
        load_from_db()
    
    # Time & Greeting
    now = datetime.now()
    hour = now.hour
    greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"
    greeting_emoji = "🌅" if hour < 12 else "☀️" if hour < 18 else "🌙"
    
    # Calculate quick stats
    total_events = len(st.session_state.events)
    total_attendees = sum(len(evt.get('data', [])) for evt in st.session_state.events.values())
    total_folders = len(st.session_state.main_folders)
    
    st.markdown(f"""
    <div class="welcome-banner">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
            <div>
                <div class="welcome-greeting">{greeting_emoji} {greeting}, {st.session_state.current_user}!</div>
                <div class="welcome-time">🕒 {now.strftime('%I:%M %p')}  •  📅 {now.strftime('%d %B %Y')}</div>
            </div>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 800; color: var(--primary-300);">{total_events}</div>
                    <div style="font-size: 0.7rem; color: var(--text-faint); text-transform: uppercase; letter-spacing: 0.05em;">Events</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 800; color: var(--secondary-300);">{total_attendees}</div>
                    <div style="font-size: 0.7rem; color: var(--text-faint); text-transform: uppercase; letter-spacing: 0.05em;">Attendees</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 800; color: var(--sky-400);">{total_folders}</div>
                    <div style="font-size: 0.7rem; color: var(--text-faint); text-transform: uppercase; letter-spacing: 0.05em;">Folders</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <h3 style="
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.2rem;
        margin: 1.5rem 0 1rem;
        color: var(--text-primary);
    ">Quick Actions</h3>
    """, unsafe_allow_html=True)
    
    # Action cards with better styling
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.markdown("""
        <div class="menu-card" data-variant="capture" style="margin-bottom: 0.5rem;">
            <div class="menu-card-shimmer"></div>
            <div class="menu-card-icon-wrap">
                <span class="menu-card-icon">➕</span>
            </div>
            <div class="menu-card-content">
                <div class="menu-card-title">Create New Event</div>
                <div class="menu-card-desc">Start a new attendance tracking session</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("➕ Create Event", use_container_width=True, type="primary", key="btn_create_event"):
            st.session_state.page = "create_event"
            st.rerun()
            
        st.markdown("""
        <div class="menu-card" data-variant="default" style="margin-bottom: 0.5rem; margin-top: 1rem;">
            <div class="menu-card-shimmer"></div>
            <div class="menu-card-icon-wrap">
                <span class="menu-card-icon">📂</span>
            </div>
            <div class="menu-card-content">
                <div class="menu-card-title">Existing Events</div>
                <div class="menu-card-desc">Access and manage your events</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📂 Browse Events", use_container_width=True, key="btn_events"):
            st.session_state.page = "events_list"
            st.rerun()
            
    with col2:
        st.markdown("""
        <div class="menu-card" data-variant="settings" style="margin-bottom: 0.5rem;">
            <div class="menu-card-shimmer"></div>
            <div class="menu-card-icon-wrap">
                <span class="menu-card-icon">📁</span>
            </div>
            <div class="menu-card-content">
                <div class="menu-card-title">Create Folder</div>
                <div class="menu-card-desc">Organize events into collections</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📁 New Folder", use_container_width=True, key="btn_create_folder"):
            st.session_state.page = "create_folder"
            st.rerun()
            
        st.markdown("""
        <div class="menu-card" data-variant="analytics" style="margin-bottom: 0.5rem; margin-top: 1rem;">
            <div class="menu-card-shimmer"></div>
            <div class="menu-card-icon-wrap">
                <span class="menu-card-icon">📋</span>
            </div>
            <div class="menu-card-content">
                <div class="menu-card-title">View Folders</div>
                <div class="menu-card-desc">Browse your event collections</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📋 View Folders", use_container_width=True, key="btn_view_folders"):
            st.session_state.page = "view_folders"
            st.rerun()
    
    # Decorative divider
    st.markdown('''
    <div style="
        height: 1px;
        margin: 2rem 0 1.5rem;
        background: linear-gradient(90deg, 
            transparent 0%,
            rgba(124, 92, 252, 0.15) 20%,
            rgba(124, 92, 252, 0.3) 50%,
            rgba(52, 211, 153, 0.2) 80%,
            transparent 100%
        );
    "></div>
    ''', unsafe_allow_html=True)
    
    # Logout button - styled
    col_spacer, col_logout, col_spacer2 = st.columns([2, 1, 2])
    with col_logout:
        if st.button("🚪 Logout", use_container_width=True, key="btn_logout"):
            st.session_state.current_user = None
            st.session_state.user_id = None
            st.session_state.events = {}
            st.session_state.main_folders = {}
            st.session_state.db_loaded = False
            st.session_state.page = "login"
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
                eid = f"{name}_{str(date)}".replace(" ", "_")
                
                # Save to Supabase
                db.create_event(
                    user_id=st.session_state.user_id,
                    event_id=eid, name=name, password=password,
                    hall_rows=5, hall_cols=10, cluster_size=1
                )
                
                # Also keep in session state
                st.session_state.events[eid] = {
                    "name": name,
                    "date": str(date),
                    "password": password,
                    "hall_rows": 5,
                    "hall_cols": 10,
                    "cluster_size": 1, 
                    "data": [],
                    "roles": {},
                    "team_members": []
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
        st.markdown(f"""
        <div class="event-list-card">
            <h3>{evt['name']}</h3>
            <div class="event-list-meta">📅 {evt['date']}  •  👥 {len(evt['data'])} Participants</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Select →", key=f"sel_{eid}", use_container_width=True):
            st.session_state.current_event = eid
            st.session_state.page = "event_menu"
            st.rerun()

def event_menu():
    render_header()
    eid = st.session_state.current_event
    evt = st.session_state.events[eid]
    
    # Enhanced Header with gradient
    st.markdown(f'''
    <div style="margin-bottom: 2rem;">
        <h1 style="
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 2.2rem;
            margin-bottom: 0.3rem;
            background: linear-gradient(135deg, #FFFFFF 0%, var(--primary-300) 50%, var(--secondary-300) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        ">🖥️ {evt['name']}</h1>
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 1rem;
            background: rgba(124, 92, 252, 0.1);
            border: 1px solid rgba(124, 92, 252, 0.2);
            border-radius: 20px;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.82rem;
            color: var(--text-secondary);
        ">
            <span style="color: var(--primary-300);">●</span> Event Dashboard
            <span style="opacity: 0.5;">•</span>
            <span style="font-family: 'JetBrains Mono', monospace;">{evt['date']}</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Menu items with variants for color coding
    menu_items = [
        ("📸", "Start Session", "Begin live attendance capture", "capture", "attendance_setup"),
        ("📋", "Records", "View attendance database", "default", "database"),
        ("📊", "Analytics", "Charts, metrics & insights", "analytics", "dashboard"),
        ("⚙️", "Hall Setup", "Configure seating dimensions", "settings", "hall_dims"),
        ("👥", "Teams", "Analyze gender-balanced teams", "team", "team_analysis"),
        ("🎯", "Team Roles", "Manage roles & allocations", "default", "team_management"),
        ("📂", "Batch Import", "Upload multiple pictures", "capture", "batch_upload"),
    ]
    
    def _menu_card_html(icon, title, desc, variant="default"):
        return f'''
        <div class="menu-card" data-variant="{variant}">
            <div class="menu-card-shimmer"></div>
            <div class="menu-card-icon-wrap">
                <span class="menu-card-icon">{icon}</span>
            </div>
            <div class="menu-card-content">
                <div class="menu-card-title">{title}</div>
                <div class="menu-card-desc">{desc}</div>
            </div>
        </div>
        '''

    # First row - 3 cards
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        st.markdown(_menu_card_html(*menu_items[0][:4]), unsafe_allow_html=True)
        if st.button("📸 Start Session", key="btn_attendance", use_container_width=True, type="primary"):
            st.session_state.subpage = menu_items[0][4]
            st.rerun()
            
    with col2:
        st.markdown(_menu_card_html(*menu_items[1][:4]), unsafe_allow_html=True)
        if st.button("📋 View Records", key="btn_records", use_container_width=True):
            st.session_state.subpage = menu_items[1][4]
            st.rerun()
            
    with col3:
        st.markdown(_menu_card_html(*menu_items[2][:4]), unsafe_allow_html=True)
        if st.button("📊 Analytics", key="btn_analytics", use_container_width=True):
            st.session_state.subpage = menu_items[2][4]
            st.rerun()
    
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Second row - 3 cards
    col4, col5, col6 = st.columns(3, gap="medium")
    
    with col4:
        st.markdown(_menu_card_html(*menu_items[3][:4]), unsafe_allow_html=True)
        if st.button("⚙️ Hall Setup", key="btn_hall", use_container_width=True):
            st.session_state.subpage = menu_items[3][4]
            st.rerun()
            
    with col5:
        st.markdown(_menu_card_html(*menu_items[4][:4]), unsafe_allow_html=True)
        if st.button("👥 Teams", key="btn_teams", use_container_width=True):
            st.session_state.subpage = menu_items[4][4]
            st.rerun()
            
    with col6:
        st.markdown(_menu_card_html(*menu_items[5][:4]), unsafe_allow_html=True)
        if st.button("🎯 Roles", key="btn_roles", use_container_width=True):
            st.session_state.subpage = menu_items[5][4]
            st.rerun()
    
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Third row - 1 card centered
    col7, col8, col9 = st.columns([1, 1, 1], gap="medium")
    
    with col7:
        st.markdown(_menu_card_html(*menu_items[6][:4]), unsafe_allow_html=True)
        if st.button("📂 Batch Import", key="btn_batch", use_container_width=True):
            st.session_state.subpage = menu_items[6][4]
            st.rerun()

    # Decorative divider
    st.markdown('''
    <div style="
        height: 1px;
        margin: 2rem 0;
        background: linear-gradient(90deg, 
            transparent 0%,
            rgba(124, 92, 252, 0.15) 20%,
            rgba(124, 92, 252, 0.3) 50%,
            rgba(52, 211, 153, 0.2) 80%,
            transparent 100%
        );
        position: relative;
    ">
        <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 8px;
            height: 8px;
            background: var(--primary-400);
            border-radius: 50%;
            box-shadow: 0 0 15px rgba(124, 92, 252, 0.5);
        "></div>
    </div>
    ''', unsafe_allow_html=True)
    
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
                    # Use opencv backend for fastest detection
                    detection_backend = "opencv"
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
            <div class="person-card">
                <h3 style="margin:0;">📝 Person {idx + 1}/{len(faces)}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            c_img, c_info = st.columns([1, 2])
            with c_img: st.image(face_crop, width=100)
            with c_info:
                st.metric("Gender", face['gender'])
                # Show confidence as percentage (0-100%)
                conf_val = face.get('confidence', None)
                if isinstance(conf_val, (int, float)):
                    if 0 <= conf_val <= 1:
                        conf_pct = conf_val * 100
                    else:
                        conf_pct = conf_val
                    st.metric("Confidence", f"{conf_pct:.1f}%")
                else:
                    st.metric("Confidence", "N/A")

            # Seat Allocation
            cluster = evt.get('cluster_size', 1)
            seat_mgr = SeatingManager(evt['hall_rows'], evt['hall_cols'], cluster_size=cluster)
            # Use a temporary list including current session additions if needed, but for now just evt['data']
            allocated_seat = seat_mgr.allocate_seat(evt['data'], face['gender'])
            
            # DUPLICATE CHECK using Cosine Similarity (optimized for Facenet512)
            is_duplicate = False
            matched_name = ""
            match_confidence = 0.0
            
            new_encoding = np.array(face['encoding'])
            new_norm = np.linalg.norm(new_encoding)
            known_encs = st.session_state.face_engine.known_encodings
            known_ids = st.session_state.face_engine.known_ids
            current_evt_id = st.session_state.current_event
            
            if len(known_encs) > 0 and new_norm > 0:
                event_indices = [idx for idx, meta in enumerate(known_ids) if meta['event_id'] == current_evt_id]
                if event_indices:
                    best_similarity = 0
                    best_match_idx = -1
                    
                    for i in event_indices:
                        known_vec = np.array(known_encs[i])
                        known_norm = np.linalg.norm(known_vec)
                        if known_norm == 0: continue
                        
                        # Cosine similarity: more accurate for face recognition
                        similarity = np.dot(known_vec, new_encoding) / (known_norm * new_norm)
                        
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match_idx = i
                    
                    # Threshold 0.65 optimized for Facenet512
                    if best_similarity > 0.65 and best_match_idx >= 0:
                        is_duplicate = True
                        matched_name = known_ids[best_match_idx]['name']
                        match_confidence = best_similarity * 100

            if is_duplicate:
                st.warning(f"⚠️ **Already Registered:** {matched_name} ({match_confidence:.1f}% match)")
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
                            db.add_attendee(st.session_state.current_event, record)
                            
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
                    # Sync to DB: clear and re-add
                    db.clear_attendees(st.session_state.current_event)
                    for rec in evt['data']:
                        db.add_attendee(st.session_state.current_event, rec)
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
            html_grid = '<div class="seat-grid-container">'
            
            for r in range(rows):
                row_html = '<div class="seat-row">'
                # Row Label
                row_html += f'<div class="seat-row-label">{chr(65+r)}</div>'
                
                for c in range(cols):
                    p_data = seat_map.get((r, c))
                    
                    # Default Styles
                    cell_class = "seat-cell seat-empty"
                    text_content = f"<span class='seat-num'>{c+1}</span>"
                    tooltip = f"Row {chr(65+r)}, Seat {c+1}: Empty"
                    
                    if p_data:
                        name_display = p_data.get('name', '???')
                        tooltip = f"Row {chr(65+r)}, Seat {c+1}: {name_display} ({p_data['gender']})"
                        
                        if p_data['gender'] == 'Male':
                            cell_class = "seat-cell seat-male"
                        elif p_data['gender'] == 'Female':
                            cell_class = "seat-cell seat-female"
                        else:
                            cell_class = "seat-cell seat-other"
                            
                        # Intelligent Font Sizing
                        f_size = "0.8rem"
                        if len(name_display) > 6: f_size = "0.7rem"
                        if len(name_display) > 10: f_size = "0.6rem"
                        
                        text_content = f"<span class='seat-name' style='font-size:{f_size};'>{name_display}</span>"
                    
                    cell_html = f'<div class="{cell_class}" title="{tooltip}">{text_content}</div>'
                    row_html += cell_html
                
                row_html += "</div>"
                html_grid += row_html
                
            html_grid += "</div>"
            
            # Legend
            html_grid += '''
            <div class="seat-legend">
                <div class="seat-legend-item"><div class="seat-legend-dot" style="background:linear-gradient(135deg,#6C5DD3,#5B34E8)"></div>Male</div>
                <div class="seat-legend-item"><div class="seat-legend-dot" style="background:linear-gradient(135deg,#F43F5E,#E11D48)"></div>Female</div>
                <div class="seat-legend-item"><div class="seat-legend-dot" style="background:linear-gradient(135deg,#38BDF8,#0EA5E9)"></div>Other</div>
            </div>
            '''
            
            st.markdown(html_grid, unsafe_allow_html=True)
            
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
                    pdf.set_font("Arial", size=16)
                    pdf.cell(200, 10, txt=f"Event Report: {evt['name']}", ln=1, align='C')
                    
                    pdf.set_font("Arial", size=10)
                    pdf.cell(200, 10, txt=f"Date: {evt['date']} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1, align='C')
                    
                    # Metrics
                    m_count = len(df[df['gender']=='Male'])
                    f_count = len(df[df['gender']=='Female'])
                    nb_count = len(df) - m_count - f_count
                    avg_age = df['age'].mean() if not df['age'].empty else 0
                    
                    pdf.ln(5)
                    pdf.set_font("Arial", style='B', size=12)
                    pdf.cell(0, 10, f"Summary Statistics", ln=1)
                    pdf.set_font("Arial", size=10)
                    pdf.cell(0, 7, f"Total Attendees: {len(df)}", ln=1)
                    pdf.cell(0, 7, f"Male: {m_count} | Female: {f_count} | Non-Binary: {nb_count}", ln=1)
                    pdf.cell(0, 7, f"Average Age: {avg_age:.1f}", ln=1)
                    pdf.ln(5)

                    # --- CHARTS ---
                    try:
                        # Pie Chart
                        df_gender = pd.DataFrame([{"Gender": k, "Count": v} for k, v in {"Male": m_count, "Female": f_count, "Non-Binary": nb_count}.items() if v > 0])
                        if not df_gender.empty:
                            fig_pie = px.pie(df_gender, values='Count', names='Gender', color='Gender',
                                             color_discrete_map={'Male':'#6C5DD3', 'Female':'#FF5A5F', 'Non-Binary':'#A0D2EB'})
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_pie:
                                fig_pie.write_image(tmp_pie.name)
                                pdf.image(tmp_pie.name, x=10, y=pdf.get_y(), w=80)
                        
                        # Age Bar Chart
                        age_counts = df['age'].value_counts().reset_index()
                        if not age_counts.empty:
                            age_counts.columns = ['Age', 'Count']
                            fig_bar = px.bar(age_counts, x='Age', y='Count', color='Count', color_continuous_scale=['#A0D2EB', '#6C5DD3'])
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_bar:
                                fig_bar.write_image(tmp_bar.name)
                                pdf.image(tmp_bar.name, x=100, y=pdf.get_y() - 0, w=80) # Side by side? 
                                
                        pdf.ln(60) # Move down past images
                    except Exception as e:
                        pdf.cell(0, 10, f"(Charts unavailable: Install 'kaleido')", ln=1)
                        # st.error(f"Chart Error: {e}")

                    # --- SEATING GRID ---
                    pdf.add_page()
                    pdf.set_font("Arial", style='B', size=14)
                    pdf.cell(0, 10, "Seating Arrangement", ln=1, align='C')
                    pdf.ln(5)
                    
                    # Re-build seat map
                    rows_h = evt.get('hall_rows', 5)
                    cols_h = evt.get('hall_cols', 10)
                    seat_map_pdf = {}
                    for p in evt['data']:
                        try:
                            s_str = p.get('seat', '')
                            if s_str and "Row" in s_str:
                                parts = s_str.split(',')
                                r_idx = ord(parts[0].replace("Row ", "").strip()) - 65
                                c_idx = int(parts[1].replace("Seat ", "").strip()) - 1
                                seat_map_pdf[(r_idx, c_idx)] = p
                        except: pass
                        
                    # Draw Grid
                    cell_w = 15
                    cell_h = 10
                    start_x = 10
                    start_y = pdf.get_y()
                    
                    pdf.set_font("Arial", size=6)
                    
                    for r in range(rows_h):
                        # check page break
                        if start_y + (r+1)*cell_h > 270:
                             pdf.add_page()
                             start_y = 20
                        
                        current_y = start_y + r*cell_h
                        # Row Label
                        pdf.set_xy(start_x, current_y)
                        pdf.set_text_color(0, 0, 0)
                        pdf.cell(5, cell_h, chr(65+r), 0, 0, 'C')
                        
                        for c in range(cols_h):
                            x = start_x + 8 + c*cell_w
                            # check overflow width
                            if x + cell_w > 200: continue # Clip if too wide
                            
                            p_data = seat_map_pdf.get((r, c))
                            
                            # Default fill (Grey/Empty)
                            # FPDF needs RGB 0-255
                            pdf.set_fill_color(245, 245, 245) 
                            pdf.set_draw_color(200, 200, 200)
                            
                            txt = ""
                            if p_data:
                                gender = p_data.get('gender', '')
                                if gender == 'Male': pdf.set_fill_color(200, 200, 255) # Light Purple
                                elif gender == 'Female': pdf.set_fill_color(255, 200, 200) # Light Pink
                                else: pdf.set_fill_color(200, 255, 255) # Cyan
                                
                                txt = p_data.get('name', '')[:6] # Truncate heavily
                            
                            pdf.rect(x, current_y, cell_w, cell_h, 'DF')
                            
                            if txt:
                                pdf.set_xy(x, current_y)
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(cell_w, cell_h, txt, 0, 0, 'C')
                                
                    pdf.ln(10)
                    
                    pdf.add_page()
                    pdf.set_font("Arial", style='B', size=14)
                    pdf.cell(0, 10, "Participant List", ln=1, align='C')
                    pdf.ln(5)
                    
                    # Table Header
                    pdf.set_font("Arial", style='B', size=10)
                    col_widths = [15, 60, 30, 60, 20] # SL, Name, Gender, Seat, Age
                    headers = ['SL', 'Name', 'Gender', 'Seat', 'Age']
                    
                    for i, h in enumerate(headers):
                        pdf.cell(col_widths[i], 8, h, 1)
                    pdf.ln()
                    
                    # Table Rows
                    pdf.set_font("Arial", size=9)
                    for _, row in df.iterrows():
                        pdf.cell(col_widths[0], 8, str(row.get('sl_no', '')), 1)
                        # Truncate Name to fit
                        name_txt = str(row.get('name', 'N/A'))
                        if len(name_txt) > 25: name_txt = name_txt[:22] + "..."
                        pdf.cell(col_widths[1], 8, name_txt, 1)
                        
                        pdf.cell(col_widths[2], 8, str(row.get('gender', '')), 1)
                        pdf.cell(col_widths[3], 8, str(row.get('seat', 'Unassigned')), 1)
                        pdf.cell(col_widths[4], 8, str(row.get('age', '')), 1)
                        pdf.ln()
                        
                    # Output
                    pdf_content = pdf.output(dest='S').encode('latin-1')
                    b64 = base64.b64encode(pdf_content).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="EventReport_{evt["name"]}.pdf" class="pdf-download-btn">📄 Download PDF Report</a>'
                    st.success("✅ PDF Generated!")
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
    
    if st.button("💾 Save Dimensions"):
        db.update_event(st.session_state.current_event, {
            'hall_rows': evt['hall_rows'],
            'hall_cols': evt['hall_cols'],
            'cluster_size': evt['cluster_size']
        })
        st.success(f"✅ Dimensions Saved! Cluster: {evt.get('cluster_size', 1)}")

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
                            db.add_attendee(st.session_state.current_event, record)
                            
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
        folder = db.create_folder(st.session_state.user_id, f_name)
        folder_db_id = folder['id'] if folder else None
        st.session_state.main_folders[f_name] = {"date": str(datetime.now().date()), "events": [], "db_id": folder_db_id}
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
                if fdata.get('db_id'):
                    db.add_event_to_folder(fdata['db_id'], sel_evt)
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
                    db.save_roles(st.session_state.current_event, evt['roles'])
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
                    db.save_team_members(st.session_state.current_event, evt['team_members'])
                    st.success(f"{name} added!")
                    st.rerun()
                else:
                    st.error("Name is required.")
        
        st.write(f"### Team Members ({len(evt['team_members'])})")
        
        # Prepare Display Data
        display_data = []
        for m in evt['team_members']:
            d = {'ID': m['id'], 'Name': m['name'], 'Gender': m['gender']}
            
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
        
        if not display_data:
            st.info("No members added yet.")
        else:
            # Editing Toggle
            if st.toggle("Enable Editing"):
                pwd = st.text_input("Enter Event Password to Edit", type="password")
                real_pwd = evt.get('password', 'admin') # Default to admin if not set
                
                if pwd == real_pwd:
                    st.success("🔓 Editing Enabled")
                    df_edit = pd.DataFrame(display_data)
                    
                    edited_df = st.data_editor(df_edit, num_rows="dynamic", key="team_editor")
                    
                    if st.button("💾 Save Changes", type="primary"):
                        # Reconstruct team_members list
                        new_members = []
                        for _, row in edited_df.iterrows():
                            # Parse Skills back to list
                            s_str = row.get('Skills', '')
                            # Simple comma split
                            s_list = [s.strip() for s in s_str.split(',') if s.strip()]
                            
                            new_members.append({
                                'id': row.get('ID', generate_code()), # Keep ID or gen new if added
                                'name': row.get('Name', 'Unknown'),
                                'gender': row.get('Gender', 'Non-Binary'),
                                'skills': s_list
                            })
                        
                        evt['team_members'] = new_members
                        db.save_team_members(st.session_state.current_event, evt['team_members'])
                        st.success("✅ Changes Saved!")
                        st.rerun()
                elif pwd:
                    st.error("❌ Incorrect Password")
            else:
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
                        color = "blue" if item['c']['gender'] == 'Male' else "violet"
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
