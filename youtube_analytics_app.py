"""
Chamberlin Media Monitor — Render.com deployment
YouTube Data API v3
"""

import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re, json, os, html as _hesc
from datetime import datetime, timedelta
import sqlite3, contextlib
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Chamberlin Media Monitor",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="collapsed",   # collapsed by default — cleaner on mobile
)

# ─────────────────────────────────────────────────────────────
# PASSWORD GATE
# ─────────────────────────────────────────────────────────────
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""<style>
    .login-wrap{max-width:360px;margin:100px auto;text-align:center}
    .login-icon{width:52px;height:52px;background:#ff0033;border-radius:12px;
        display:flex;align-items:center;justify-content:center;
        font-size:24px;font-weight:900;color:white;margin:0 auto 20px}
    .login-title{font-size:20px;font-weight:700;color:#fff;margin-bottom:4px}
    .login-sub{font-size:13px;color:#737373;margin-bottom:32px}
    </style>
    <div class="login-wrap">
        <div class="login-icon">▶</div>
        <div class="login-title">Chamberlin Media Monitor</div>
        <div class="login-sub">Enter your team password to continue</div>
    </div>""", unsafe_allow_html=True)
    col = st.columns([1,2,1])[1]
    with col:
        pwd = st.text_input("Password", type="password", placeholder="••••••••••••", label_visibility="collapsed")
        if st.button("Sign In", type="primary", use_container_width=True):
            if pwd == "ChamMedia2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()

# ─────────────────────────────────────────────────────────────
# DESIGN SYSTEM
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
*,*::before,*::after{box-sizing:border-box}
h1 a,h2 a,h3 a{display:none!important}
:root{
  --bg:#0a0a0a;--bg-2:#111;--bg-3:#181818;--bg-4:#1f1f1f;
  --border:#252525;--border-2:#2e2e2e;
  --text:#e8e8e8;--text-muted:#737373;--text-dim:#4a4a4a;
  --red:#ff0033;--red-glow:rgba(255,0,51,.15);
  --blue:#1e8fff;--green:#1db954;--yellow:#f5a623;
  --font:'Instrument Sans',sans-serif;--font-mono:'JetBrains Mono',monospace;
  --radius:10px;--radius-sm:6px;
  --sidebar-w:280px;
}
html,body,[class*="css"]{font-family:var(--font);background-color:var(--bg)!important;color:var(--text)}
.stApp{background:var(--bg)!important}

/* ── Hide ALL Streamlit chrome ── */
#MainMenu,footer,header{visibility:hidden!important;height:0!important;overflow:hidden!important}
.stDeployButton,[data-testid="stToolbar"],[data-testid="stStatusWidget"],
[data-testid="stDecoration"],[data-testid="stHeader"],
[class*="viewerBadge"],[class*="styles_viewerBadge"],
.viewerBadge_container__1QSob,.stActionButton,
[data-testid="manage-app-button"]{display:none!important}

/* ── SIDEBAR — slide-over drawer on all screen sizes ──
   We use Streamlit's native sidebar but style it as a fixed overlay drawer.
   The native collapsedControl toggle is re-styled as a persistent ☰ button. */
[data-testid="stSidebar"]{
  background:var(--bg-2)!important;
  border-right:1px solid var(--border)!important;
  min-width:var(--sidebar-w)!important;
  max-width:var(--sidebar-w)!important;
}
[data-testid="stSidebar"]>div{padding:0!important}
[data-testid="stSidebar"] .block-container{padding:0 1rem 2rem!important}

/* ── Hamburger toggle — always pinned top-left, always visible ── */
[data-testid="collapsedControl"]{
  display:flex!important;visibility:visible!important;opacity:1!important;
  position:fixed!important;top:14px!important;left:14px!important;
  z-index:2147483647!important;
  background:#1c1c1c!important;border:1px solid #3a3a3a!important;
  border-radius:8px!important;width:40px!important;height:40px!important;
  align-items:center!important;justify-content:center!important;
  cursor:pointer!important;box-shadow:0 2px 20px rgba(0,0,0,.9)!important;
}
[data-testid="collapsedControl"]:hover{background:#ff0033!important;border-color:#ff0033!important}
[data-testid="collapsedControl"] svg{color:#e8e8e8!important;width:18px!important;height:18px!important}

/* Main content — always full width, slight top padding for the hamburger */
.main .block-container{
  padding:1rem 1.5rem 4rem!important;
  max-width:1400px;
  margin-top:12px!important;
}

/* Typography */
h1{font-family:var(--font);font-weight:700;font-size:20px;letter-spacing:-.3px;color:#fff!important;margin:0!important;padding:0!important}
h2{font-family:var(--font);font-weight:600;font-size:17px;color:#fff!important;margin-bottom:4px!important}
h3{font-family:var(--font);font-weight:500;font-size:13px;color:var(--text-muted)!important;text-transform:uppercase;letter-spacing:.8px;margin-bottom:10px!important}
p,li{font-size:14px;line-height:1.6}

/* Metrics */
[data-testid="metric-container"]{background:var(--bg-3)!important;border:1px solid var(--border)!important;border-radius:var(--radius)!important;padding:16px 18px!important}
[data-testid="metric-container"] label{font-family:var(--font-mono)!important;color:var(--text-muted)!important;font-size:9px!important;text-transform:uppercase;letter-spacing:1px;font-weight:500}
[data-testid="stMetricValue"]{font-family:var(--font)!important;color:#fff!important;font-size:24px!important;font-weight:700!important;letter-spacing:-.5px}

/* Buttons */
.stButton>button{font-family:var(--font)!important;font-weight:600!important;font-size:13px!important;border-radius:var(--radius-sm)!important;border:none!important;padding:8px 16px!important;transition:all .15s ease!important;cursor:pointer}
.stButton>button[kind="primary"]{background:var(--red)!important;color:#fff!important}
.stButton>button[kind="primary"]:hover{background:#cc0029!important}
.stButton>button[kind="secondary"]{background:var(--bg-4)!important;color:var(--text)!important;border:1px solid var(--border-2)!important}
.stButton>button[kind="secondary"]:hover{background:var(--bg-3)!important;border-color:#444!important}

/* Inputs */
.stTextInput>div>input,.stTextArea>div>textarea{background:var(--bg-3)!important;border:1px solid var(--border-2)!important;border-radius:var(--radius-sm)!important;color:var(--text)!important;font-family:var(--font)!important;font-size:13px!important}
.stTextInput>div>input:focus,.stTextArea>div>textarea:focus{border-color:var(--red)!important;box-shadow:0 0 0 3px var(--red-glow)!important}
.stSelectbox>div>div{background:var(--bg-3)!important;border:1px solid var(--border-2)!important;border-radius:var(--radius-sm)!important;color:var(--text)!important;font-family:var(--font)!important;font-size:13px!important}
label{color:var(--text-muted)!important;font-size:12px!important;font-weight:500!important}

/* Tabs */
[data-testid="stTabs"] [role="tablist"]{border-bottom:1px solid var(--border)!important;background:transparent!important;gap:0!important;padding:0!important;overflow-x:auto!important;flex-wrap:nowrap!important}
[data-testid="stTabs"] button[role="tab"]{font-family:var(--font)!important;font-size:12px!important;font-weight:500!important;color:var(--text-muted)!important;background:transparent!important;border:none!important;border-bottom:2px solid transparent!important;border-radius:0!important;padding:10px 16px!important;white-space:nowrap;transition:all .15s!important}
[data-testid="stTabs"] button[role="tab"]:hover{color:var(--text)!important}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{color:#fff!important;border-bottom:2px solid var(--red)!important}
[data-testid="stTabs"] [data-testid="stTabsContent"]{padding-top:20px!important}

/* Table */
[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:var(--radius)!important;overflow:hidden!important}
[data-testid="stDataFrame"] thead th{background:var(--bg-3)!important;color:var(--text-muted)!important;font-size:10px!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:.8px!important;border-bottom:1px solid var(--border)!important;padding:8px 12px!important}
[data-testid="stDataFrame"] tbody td{font-size:12px!important;border-bottom:1px solid var(--border)!important;padding:8px 12px!important;color:var(--text)!important}
[data-testid="stDataFrame"] tbody tr:hover td{background:var(--bg-3)!important}

/* Expander */
.streamlit-expanderHeader{background:var(--bg-3)!important;border:1px solid var(--border)!important;border-radius:var(--radius-sm)!important;color:var(--text)!important;font-family:var(--font)!important;font-size:13px!important;font-weight:500!important;padding:10px 14px!important}
.streamlit-expanderContent{background:var(--bg-2)!important;border:1px solid var(--border)!important;border-top:none!important;border-radius:0 0 var(--radius-sm) var(--radius-sm)!important}

/* Progress */
[data-testid="stProgressBar"]>div>div{background:var(--red)!important;border-radius:2px!important}
[data-testid="stProgressBar"]>div{background:var(--bg-4)!important;border-radius:2px!important;height:3px!important}

hr{border-color:var(--border)!important;margin:12px 0!important}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border-2);border-radius:3px}

/* ── Sidebar inner components ── */
.sb-brand{display:flex;align-items:center;gap:10px;padding:16px 0 16px;border-bottom:1px solid var(--border);margin-bottom:16px}
.sb-brand-icon{width:28px;height:28px;background:var(--red);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:900;color:white;flex-shrink:0}
.sb-brand-name{font-size:13px;font-weight:700;color:#fff}
.sb-brand-sub{font-size:9px;color:var(--red);font-weight:600;letter-spacing:1.5px;text-transform:uppercase}
.sb-label{font-family:var(--font-mono);font-size:9px;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:1.5px;margin:14px 0 8px;padding-bottom:6px;border-bottom:1px solid var(--border)}
.ch-pill{display:flex;align-items:center;gap:8px;padding:7px 10px;background:var(--bg-3);border:1px solid var(--border);border-radius:var(--radius-sm);margin-bottom:5px}
.ch-dot{width:6px;height:6px;border-radius:50%;background:var(--green);flex-shrink:0}
.ch-dot-empty{background:var(--text-dim)}
.ch-name{font-size:12px;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ch-subs{font-size:10px;color:var(--text-muted);font-family:var(--font-mono)}

/* ── Stat bubbles ── */
.yt-bubble-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.yt-bubble{background:var(--bg-3);border:1px solid var(--border);border-radius:10px;padding:14px 16px;flex:1 1 120px;min-width:110px}
.yt-bubble-label{font-family:var(--font-mono);font-size:8px;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:1.2px;margin-bottom:6px}
.yt-bubble-value{font-size:22px;font-weight:700;color:#fff;letter-spacing:-.5px;line-height:1;margin-bottom:3px}
.yt-bubble-sub{font-size:10px;color:var(--text-muted)}
.yt-bubble-red{border-left:3px solid var(--red)}
.yt-bubble-blue{border-left:3px solid var(--blue)}
.yt-bubble-green{border-left:3px solid var(--green)}
.yt-bubble-grey{border-left:3px solid #444}
.yt-bubble-gold{border-left:3px solid #f5a623}
.yt-bubble-active{border-color:var(--red)!important;background:rgba(255,0,51,.06)!important}

/* ── Outlier tracker cards ── */
.outlier-card{background:var(--bg-3);border:1px solid var(--border);border-left:3px solid var(--green);border-radius:var(--radius);padding:14px 16px;margin-bottom:10px;display:flex;align-items:flex-start;gap:14px}
.outlier-thumb{width:90px;height:51px;object-fit:cover;border-radius:5px;flex-shrink:0;background:var(--bg-4)}
.outlier-thumb-ph{width:90px;height:51px;background:var(--bg-4);border-radius:5px;display:flex;align-items:center;justify-content:center;color:var(--text-dim);font-size:20px;flex-shrink:0}
.outlier-body{flex:1;min-width:0}
.outlier-title{font-size:13px;font-weight:600;color:var(--text);line-height:1.4;margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.outlier-ch{font-size:10px;color:var(--red);font-weight:700;margin-bottom:4px;font-family:var(--font-mono)}
.outlier-stats{display:flex;gap:12px;flex-wrap:wrap}
.outlier-stat{font-family:var(--font-mono);font-size:10px;color:var(--text-muted)}
.outlier-stat span{color:#fff;font-weight:700}
.outlier-badge{display:inline-block;background:rgba(29,185,84,.15);border:1px solid rgba(29,185,84,.3);color:#5ce68f;padding:2px 8px;border-radius:3px;font-size:9px;font-weight:700;font-family:var(--font-mono);letter-spacing:.5px;margin-bottom:5px}

/* ── Section label ── */
.section-label{font-family:var(--font-mono);font-size:9px;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid var(--border)}

/* ── Alert rows ── */
.alert{border-radius:var(--radius-sm);padding:10px 12px;font-size:13px;margin-bottom:8px;display:flex;align-items:flex-start;gap:10px}
.alert-icon{font-size:14px;flex-shrink:0;margin-top:1px}
.alert-body{flex:1}
.alert-title{font-weight:600;margin-bottom:2px}
.alert-desc{font-size:12px;opacity:.8}
.alert-warn{background:rgba(245,166,35,.1);border:1px solid rgba(245,166,35,.3);color:#e8c46b}
.alert-success{background:rgba(29,185,84,.08);border:1px solid rgba(29,185,84,.25);color:#5ce68f}
.alert-info{background:rgba(30,143,255,.08);border:1px solid rgba(30,143,255,.25);color:#7ac2ff}

/* Best day */
.best-day{background:rgba(29,185,84,.06);border:1px solid rgba(29,185,84,.2);border-radius:var(--radius);padding:14px 18px;display:flex;align-items:center;gap:14px;margin-bottom:16px}
.best-day-icon{font-size:24px}
.best-day-label{font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.8px;font-family:var(--font-mono);margin-bottom:2px}
.best-day-value{font-size:20px;font-weight:700;color:var(--green)}
.best-day-sub{font-size:11px;color:var(--text-muted)}

/* Tags */
.tags{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:14px}
.tag{background:var(--bg-4);border:1px solid var(--border-2);color:var(--text-muted);padding:3px 9px;border-radius:20px;font-size:11px;font-weight:500;font-family:var(--font-mono)}
.tag-hot{border-color:rgba(255,0,51,.4);color:#ff8099;background:rgba(255,0,51,.08)}

.refresh-btn-wrap .stButton>button{font-size:11px!important;padding:6px 12px!important;font-weight:500!important}
.stTextArea textarea{font-family:var(--font-mono)!important;font-size:12px!important;line-height:1.7!important}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────────────────────
PLOTLY = dict(
    paper_bgcolor="#0a0a0a", plot_bgcolor="#111111",
    font=dict(family="Instrument Sans", color="#737373", size=11),
    xaxis=dict(gridcolor="#1e1e1e", zerolinecolor="#252525", linecolor="#252525",
               tickfont=dict(size=10), automargin=True),
    yaxis=dict(gridcolor="#1e1e1e", zerolinecolor="#252525", linecolor="#252525",
               tickfont=dict(size=10), automargin=True),
    margin=dict(l=10, r=10, t=44, b=40),
    title_font=dict(size=13, color="#e8e8e8", family="Instrument Sans"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#252525", font=dict(size=11)),
    autosize=True,
)

def plotly_cfg():
    return {"responsive": True, "displayModeBar": False}

def _pb():
    return {k:v for k,v in PLOTLY.items() if k not in ("xaxis","yaxis","margin")}

# ─────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────
_DATA_DIR = os.environ.get("DATA_DIR", "/data")
os.makedirs(_DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(_DATA_DIR, "chamberlin.db")

@contextlib.contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS channels (
            name TEXT PRIMARY KEY, channel_id TEXT NOT NULL,
            channel_stats TEXT DEFAULT '{}', last_refreshed TEXT DEFAULT 'Never',
            notes TEXT DEFAULT '', ideas TEXT DEFAULT '{}')""")
        db.execute("""CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, channel_name TEXT NOT NULL,
            title TEXT, published TEXT, views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0, comments INTEGER DEFAULT 0,
            url TEXT, thumbnail TEXT,
            days_since_publish INTEGER DEFAULT 0, views_per_day REAL DEFAULT 0,
            like_rate REAL DEFAULT 0, comment_rate REAL DEFAULT 0,
            FOREIGN KEY (channel_name) REFERENCES channels(name) ON DELETE CASCADE)""")
        db.execute("""CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT, channel_name TEXT NOT NULL,
            snapshot_date TEXT NOT NULL, subscribers INTEGER DEFAULT 0, total_views INTEGER DEFAULT 0,
            UNIQUE(channel_name, snapshot_date))""")
        db.execute("CREATE TABLE IF NOT EXISTS folders (name TEXT PRIMARY KEY)")
        db.execute("""CREATE TABLE IF NOT EXISTS folder_channels (
            folder_name TEXT NOT NULL, channel_name TEXT NOT NULL,
            PRIMARY KEY (folder_name, channel_name))""")

def load_channels_from_db():
    channels = {}
    with get_db() as db:
        for row in db.execute("SELECT * FROM channels").fetchall():
            ch = dict(row)
            stats = json.loads(ch["channel_stats"] or "{}")
            ideas = json.loads(ch["ideas"] or "{}")
            vrows = db.execute("SELECT * FROM videos WHERE channel_name=? ORDER BY views DESC",(ch["name"],)).fetchall()
            df = None
            if vrows:
                df = pd.DataFrame([dict(r) for r in vrows])
                df["Published"] = pd.to_datetime(df["published"], errors="coerce")
                df = df.rename(columns={
                    "title":"Title","views":"Views","likes":"Likes","comments":"Comments",
                    "url":"URL","thumbnail":"Thumbnail","days_since_publish":"Days Since Publish",
                    "views_per_day":"Views per Day","like_rate":"Like Rate %","comment_rate":"Comment Rate %"})
            channels[ch["name"]] = {
                "id":ch["channel_id"],"data":df,"channel_stats":stats,
                "last_refreshed":ch["last_refreshed"],"notes":ch["notes"] or "","ideas":ideas}
    return channels

def save_channel_to_db(name, channel_id, stats, df, last_refreshed, notes="", ideas=None):
    with get_db() as db:
        db.execute("""INSERT INTO channels (name,channel_id,channel_stats,last_refreshed,notes,ideas)
            VALUES (?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET
            channel_id=excluded.channel_id,channel_stats=excluded.channel_stats,
            last_refreshed=excluded.last_refreshed,notes=excluded.notes,ideas=excluded.ideas""",
            (name,channel_id,json.dumps(stats),last_refreshed,notes,json.dumps(ideas or {})))
        if df is not None and not df.empty:
            db.execute("DELETE FROM videos WHERE channel_name=?",(name,))
            for _,row in df.iterrows():
                pub = row["Published"].strftime("%Y-%m-%d") if pd.notna(row["Published"]) else ""
                db.execute("""INSERT INTO videos
                    (channel_name,title,published,views,likes,comments,url,thumbnail,
                     days_since_publish,views_per_day,like_rate,comment_rate)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (name,row.get("Title",""),pub,
                     int(row.get("Views",0)),int(row.get("Likes",0)),int(row.get("Comments",0)),
                     row.get("URL",""),row.get("Thumbnail",""),
                     int(row.get("Days Since Publish",0)),float(row.get("Views per Day",0)),
                     float(row.get("Like Rate %",0)),float(row.get("Comment Rate %",0))))

def delete_channel_from_db(name):
    with get_db() as db:
        db.execute("DELETE FROM channels WHERE name=?",(name,))
        db.execute("DELETE FROM videos WHERE channel_name=?",(name,))
        db.execute("DELETE FROM folder_channels WHERE channel_name=?",(name,))

def load_folders_from_db():
    folders = {}
    with get_db() as db:
        for fr in db.execute("SELECT name FROM folders ORDER BY name").fetchall():
            fname = fr["name"]
            crows = db.execute("SELECT channel_name FROM folder_channels WHERE folder_name=?",(fname,)).fetchall()
            folders[fname] = [r["channel_name"] for r in crows]
    return folders

def save_folder_to_db(n):
    with get_db() as db: db.execute("INSERT OR IGNORE INTO folders (name) VALUES (?)",(n,))

def delete_folder_from_db(n):
    with get_db() as db:
        db.execute("DELETE FROM folders WHERE name=?",(n,))
        db.execute("DELETE FROM folder_channels WHERE folder_name=?",(n,))

def add_channel_to_folder_db(f,c):
    with get_db() as db: db.execute("INSERT OR IGNORE INTO folder_channels (folder_name,channel_name) VALUES (?,?)",(f,c))

def remove_channel_from_folder_db(f,c):
    with get_db() as db: db.execute("DELETE FROM folder_channels WHERE folder_name=? AND channel_name=?",(f,c))

# ─────────────────────────────────────────────────────────────
# SECRETS
# ─────────────────────────────────────────────────────────────
def get_secret(key, fallback=""):
    try: return st.secrets.get(key, fallback)
    except: return os.environ.get(key, fallback)

# ─────────────────────────────────────────────────────────────
# YOUTUBE API
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_channel_data(api_key, channel_id):
    youtube = build("youtube","v3",developerKey=api_key)
    ch_resp = youtube.channels().list(part="snippet,statistics,contentDetails",id=channel_id).execute()
    if not ch_resp.get("items"):
        raise ValueError(f"Channel ID not found: {channel_id}")
    ch = ch_resp["items"][0]
    stats = {
        "subscribers":  int(ch["statistics"].get("subscriberCount",0)),
        "total_views":  int(ch["statistics"].get("viewCount",0)),
        "video_count":  int(ch["statistics"].get("videoCount",0)),
        "channel_name": ch["snippet"]["title"],
        "channel_thumb":ch["snippet"]["thumbnails"].get("medium",{}).get("url",""),
        "description":  ch["snippet"].get("description","")[:300],
    }
    uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    videos, next_page = [], None
    for _ in range(2):
        pl = youtube.playlistItems().list(
            part="contentDetails",playlistId=uploads_id,maxResults=50,pageToken=next_page).execute()
        video_ids = [i["contentDetails"]["videoId"] for i in pl["items"]]
        vr = youtube.videos().list(part="snippet,statistics",id=",".join(video_ids)).execute()
        for item in vr["items"]:
            s=item["statistics"]; sn=item["snippet"]
            thumbs=sn.get("thumbnails",{})
            thumb_url=(thumbs.get("maxres") or thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url","")
            videos.append({
                "Title":sn["title"],"Published":sn["publishedAt"][:10],
                "Views":int(s.get("viewCount",0)),"Likes":int(s.get("likeCount",0)),
                "Comments":int(s.get("commentCount",0)),
                "URL":f"https://youtu.be/{item['id']}","Thumbnail":thumb_url,
            })
        next_page = pl.get("nextPageToken")
        if not next_page: break
    df = pd.DataFrame(videos)
    if not df.empty:
        df["Published"] = pd.to_datetime(df["Published"])
        df = df.sort_values("Published",ascending=False).reset_index(drop=True)
        df["Days Since Publish"]=(datetime.now()-df["Published"]).dt.days.clip(lower=1)
        df["Views per Day"]=(df["Views"]/df["Days Since Publish"]).round(1)
        df["Like Rate %"]=(df["Likes"]/df["Views"].replace(0,1)*100).round(2)
        df["Comment Rate %"]=(df["Comments"]/df["Views"].replace(0,1)*100).round(2)
    return df, stats

def lookup_channel_name(api_key, channel_id):
    youtube = build("youtube","v3",developerKey=api_key)
    resp = youtube.channels().list(part="snippet",id=channel_id).execute()
    if not resp.get("items"):
        raise ValueError(f"No channel found for ID: {channel_id}")
    return resp["items"][0]["snippet"]["title"]

# ─────────────────────────────────────────────────────────────
# TIME FILTER
# ─────────────────────────────────────────────────────────────
TIME_PRESETS = {"7 Days":7,"30 Days":30,"90 Days":90,"6 Months":180,"12 Months":365,"All Time":0}

def apply_time_filter(df, preset, custom_start=None, custom_end=None):
    if df is None or df.empty or "Published" not in df.columns: return df
    if preset=="Custom" and custom_start and custom_end:
        s=pd.Timestamp(custom_start); e=pd.Timestamp(custom_end)+pd.Timedelta(days=1)
        return df[(df["Published"]>=s)&(df["Published"]<e)]
    if preset=="Month" and custom_start:
        y,m=custom_start
        s=pd.Timestamp(year=y,month=m,day=1)
        e=(s+pd.offsets.MonthEnd(1))+pd.Timedelta(days=1)
        return df[(df["Published"]>=s)&(df["Published"]<e)]
    days=TIME_PRESETS.get(preset,0)
    if days==0: return df
    cutoff=pd.Timestamp(datetime.now()-timedelta(days=days))
    return df[df["Published"]>=cutoff]

# ─────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────
def fmt(n):
    n=int(n)
    if n>=1_000_000: return f"{n/1_000_000:.1f}M"
    if n>=1_000: return f"{n/1_000:.1f}K"
    return f"{n:,}"

def fmt_usd(n):
    n=int(n)
    if n>=1_000_000: return f"${n/1_000_000:.1f}M"
    if n>=1_000: return f"${n/1_000:.0f}K"
    return f"${n:,}"

def detect_outliers(channels):
    """
    Outlier = video published 30+ days ago whose Views/Day in the
    last 30 days is >= 2x its all-time Views/Day average.
    Returns list of dicts sorted by spike ratio descending.
    """
    outliers = []
    cutoff_age = 30          # video must be at least this many days old
    lookback   = 30          # compare recent vpd vs lifetime vpd

    for ch_name, info in channels.items():
        df = info.get("data")
        stats = info.get("channel_stats", {})
        if df is None or df.empty: continue
        old_vids = df[df["Days Since Publish"] >= cutoff_age]
        if old_vids.empty: continue
        ch_display = stats.get("channel_name", ch_name)

        for _, row in old_vids.iterrows():
            lifetime_vpd = row.get("Views per Day", 0)
            if lifetime_vpd <= 0: continue
            # We don't have day-by-day data so we use Views/Day as the proxy.
            # A video is an outlier if its VPD is significantly above the
            # channel median for videos of similar age.
            channel_median_vpd = old_vids["Views per Day"].median()
            if channel_median_vpd <= 0: continue
            ratio = lifetime_vpd / channel_median_vpd
            if ratio >= 2.0:
                outliers.append({
                    "channel":    ch_name,
                    "ch_display": ch_display,
                    "title":      row.get("Title",""),
                    "url":        row.get("URL",""),
                    "thumbnail":  row.get("Thumbnail",""),
                    "views":      int(row.get("Views",0)),
                    "vpd":        float(lifetime_vpd),
                    "days":       int(row.get("Days Since Publish",0)),
                    "ratio":      ratio,
                    "likes":      int(row.get("Likes",0)),
                    "lr":         float(row.get("Like Rate %",0)),
                })

    outliers.sort(key=lambda x: x["ratio"], reverse=True)
    return outliers[:12]

def render_thumb_table(df, show_channel=False, height=600):
    rows=""
    for _,row in df.iterrows():
        badge_map={"NEW":("#1e8fff","#0d3a6e"),"HOT":("#ff0033","#3a0010"),"EVERGREEN":("#1db954","#0a2e1a")}
        b=""
        if row.get("Days Since Publish",999)<=14: b="NEW"
        elif row.get("Views per Day",0)>=500: b="HOT"
        elif row.get("Days Since Publish",0)>=90 and row.get("Views per Day",0)>=100: b="EVERGREEN"
        badge_html=(f'<span style="background:{badge_map[b][1]};color:{badge_map[b][0]};border:1px solid {badge_map[b][0]};padding:2px 7px;border-radius:3px;font-size:9px;font-weight:700;letter-spacing:.5px;font-family:monospace;margin-right:4px">{b}</span>' if b else "")
        thu=_hesc.escape(str(row.get("Thumbnail","")))
        url=_hesc.escape(str(row.get("URL","#")))
        tit=_hesc.escape(str(row.get("Title","")))
        pub=row["Published"].strftime("%Y-%m-%d") if pd.notna(row.get("Published")) else "—"
        ch_html=(f'<div style="font-size:10px;color:#ff0033;font-weight:700;margin-bottom:2px">{_hesc.escape(str(row.get("Channel","")))}</div>' if show_channel and row.get("Channel") else "")
        thumb=(f'<img src="{thu}" style="width:110px;height:62px;object-fit:cover;border-radius:5px;display:block" loading="lazy">' if thu else '<div style="width:110px;height:62px;background:#1f1f1f;border-radius:5px;display:flex;align-items:center;justify-content:center;color:#444;font-size:16px">▶</div>')
        rows+=f"""<tr class="vrow">
          <td style="padding:7px 8px;width:126px;min-width:110px"><a href="{url}" target="_blank">{thumb}</a></td>
          <td style="padding:7px 10px;min-width:160px;max-width:320px">
            {ch_html}
            <div style="font-size:12px;font-weight:600;color:#e8e8e8;line-height:1.4;margin-bottom:2px">{tit}</div>
            <div style="font-size:10px;color:#737373;margin-bottom:3px">{pub} · {int(row.get('Days Since Publish',0))}d ago</div>
            {badge_html}<a href="{url}" target="_blank" style="color:#ff0033;font-size:10px;font-weight:700;text-decoration:none">WATCH ↗</a>
          </td>
          <td class="num">{fmt(int(row.get('Views',0)))}</td>
          <td class="num nh">{fmt(int(row.get('Likes',0)))}</td>
          <td class="num nh">{fmt(int(row.get('Comments',0)))}</td>
          <td class="num">{row.get('Views per Day',0):.1f}</td>
          <td class="num nh">{row.get('Like Rate %',0):.2f}%</td>
          <td class="num nh">{row.get('Comment Rate %',0):.2f}%</td>
        </tr>"""
    html_doc=f"""<!DOCTYPE html><html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
      *{{box-sizing:border-box;margin:0;padding:0}}
      body{{background:#0a0a0a;font-family:'Instrument Sans',system-ui,sans-serif;color:#e8e8e8;overflow-x:auto}}
      table{{width:100%;border-collapse:collapse;font-size:12px;min-width:420px}}
      thead tr{{background:#181818;position:sticky;top:0;z-index:10}}
      th{{padding:8px 10px;text-align:right;font-size:9px;font-weight:700;color:#4a4a4a;text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid #252525;white-space:nowrap}}
      th:nth-child(1),th:nth-child(2){{text-align:left}}
      .vrow:hover td{{background:#141414}}
      td{{border-bottom:1px solid #1a1a1a;vertical-align:middle;transition:background .1s}}
      .num{{text-align:right;font-family:'JetBrains Mono',monospace;font-size:11px;color:#e8e8e8;white-space:nowrap;padding:7px 10px}}
      ::-webkit-scrollbar{{width:3px;height:3px}}
      ::-webkit-scrollbar-track{{background:#0a0a0a}}
      ::-webkit-scrollbar-thumb{{background:#2a2a2a;border-radius:2px}}
      @media(max-width:540px){{.nh,.th-h{{display:none}}table{{min-width:300px}}}}
    </style></head><body>
    <table>
      <thead><tr>
        <th>Thumb</th><th>Title</th><th>Views</th>
        <th class="th-h">Likes</th><th class="th-h">Comments</th>
        <th>Views/Day</th><th class="th-h">Like%</th><th class="th-h">Cmt%</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table></body></html>"""
    components.html(html_doc, height=height, scrolling=True)

def chart_top_views(df, n=10):
    top = df.nlargest(n,"Views")[["Title","Views"]].sort_values("Views").copy()
    top["Label"] = top["Title"].str[:45]
    colors = top["Views"].tolist()
    fig = go.Figure(go.Bar(
        x=top["Views"], y=top["Label"], orientation="h",
        marker=dict(color=colors,colorscale=[[0,"#3a0010"],[1,"#ff0033"]],showscale=False),
        text=[fmt(v) for v in top["Views"]], textposition="outside",
        textfont=dict(size=10,color="#737373"),
    ))
    fig.update_layout(**_pb(), title=f"Top {n} by Total Views",
                      height=max(280,n*36), showlegend=False,
                      margin=dict(l=10,r=70,t=44,b=10),
                      xaxis=dict(visible=False,gridcolor="#1e1e1e"),
                      yaxis=dict(tickfont=dict(size=10),automargin=True,gridcolor="#1e1e1e",linecolor="#252525"))
    return fig

def chart_top_momentum(df, n=10):
    top = df.nlargest(n,"Views per Day")[["Title","Views per Day"]].sort_values("Views per Day").copy()
    top["Label"] = top["Title"].str[:45]
    colors = top["Views per Day"].tolist()
    fig = go.Figure(go.Bar(
        x=top["Views per Day"], y=top["Label"], orientation="h",
        marker=dict(color=colors,colorscale=[[0,"#001a33"],[1,"#1e8fff"]],showscale=False),
        text=[f'{v:.0f}' for v in top["Views per Day"]], textposition="outside",
        textfont=dict(size=10,color="#737373"),
    ))
    fig.update_layout(**_pb(), title=f"Top {n} by Momentum (Views/Day)",
                      height=max(280,n*36), showlegend=False,
                      margin=dict(l=10,r=70,t=44,b=10),
                      xaxis=dict(visible=False,gridcolor="#1e1e1e"),
                      yaxis=dict(tickfont=dict(size=10),automargin=True,gridcolor="#1e1e1e",linecolor="#252525"))
    return fig

# ─────────────────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────────────────
init_db()

SEED_DATA = {
    "Angel Studios":[
        ("UCb02Js81Etta5BgML6jK-fQ","Angel Studios"),
        ("UCYxkRL8mgBlunTKYX4In7LA","Angel Kids"),
        ("UCZFLi-CFABqg49AVj3ZY38Q","Angel Studios 2"),
        ("UCPMnn5ZkYHf2epbcekcImPQ","Angel Studios 3"),
        ("UCw6rIEbumyIW-Gu34Q3jFeg","Angel Studios 4"),
    ],
    "Blaze Media":[("UCoxZVv224nHvTmkMk0N3fYA","Blaze Media")],
    "Backyard Butchers":[("UC53maXyeHXst2ZGHwsfHGCA","Backyard Butchers")],
}

def seed_channels_and_folders():
    existing_ids=set()
    with get_db() as db:
        existing_ids={r["channel_id"] for r in db.execute("SELECT channel_id FROM channels").fetchall()}
    for folder_name,channels in SEED_DATA.items():
        save_folder_to_db(folder_name)
        for ch_id,placeholder_name in channels:
            if ch_id not in existing_ids:
                actual_name=placeholder_name; suffix=1
                with get_db() as db:
                    taken={r["name"] for r in db.execute("SELECT name FROM channels").fetchall()}
                while actual_name in taken:
                    actual_name=f"{placeholder_name} ({suffix})"; suffix+=1
                save_channel_to_db(actual_name,ch_id,{},None,"Never")
                add_channel_to_folder_db(folder_name,actual_name)

seed_channels_and_folders()

if "channels"      not in st.session_state: st.session_state.channels      = load_channels_from_db()
if "api_key"       not in st.session_state: st.session_state.api_key       = get_secret("YOUTUBE_API_KEY")
if "folders"       not in st.session_state: st.session_state.folders       = load_folders_from_db()
if "active_folder" not in st.session_state: st.session_state.active_folder = None
if "bubble_chart"  not in st.session_state: st.session_state.bubble_chart  = None
if "time_preset"   not in st.session_state: st.session_state.time_preset   = "All Time"
if "time_cs"       not in st.session_state: st.session_state.time_cs       = None
if "time_ce"       not in st.session_state: st.session_state.time_ce       = None
if "time_my"       not in st.session_state: st.session_state.time_my       = None

# ─────────────────────────────────────────────────────────────
# SIDEBAR — clean drawer design
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div class="sb-brand">
        <div class="sb-brand-icon">▶</div>
        <div>
            <div class="sb-brand-name">Chamberlin</div>
            <div class="sb-brand-sub">Media Monitor</div>
        </div></div>""", unsafe_allow_html=True)

    with st.expander("🔑  API Key", expanded=not st.session_state.api_key):
        yt_key = st.text_input("YouTube Data API Key", value=st.session_state.api_key,
                               type="password", placeholder="AIza...", label_visibility="collapsed")
        if st.button("Save Key", use_container_width=True):
            st.session_state.api_key = yt_key
            st.success("Saved.")

    # ── Time Filter ────────────────────────────────────────────
    with st.expander("🕐  Time Filter", expanded=False):
        preset_options = list(TIME_PRESETS.keys()) + ["Month","Custom"]
        cur = st.session_state.time_preset
        cols = st.columns(2)
        for i,p in enumerate(preset_options):
            if cols[i%2].button(p, key=f"tp_{p}",
                                type="primary" if cur==p else "secondary",
                                use_container_width=True):
                st.session_state.time_preset=p
                st.session_state.time_cs=None
                st.session_state.time_ce=None
                st.session_state.time_my=None
                st.rerun()
        if st.session_state.time_preset=="Month":
            now=datetime.now()
            y=st.selectbox("Year",list(range(now.year,now.year-6,-1)),key="tf_yr")
            m=st.selectbox("Month",list(range(1,13)),index=now.month-1,
                           format_func=lambda x:datetime(2000,x,1).strftime("%B"),key="tf_mo")
            st.session_state.time_my=(y,m)
        if st.session_state.time_preset=="Custom":
            ds=st.date_input("From",value=datetime.now()-timedelta(days=90),key="tf_cs")
            de=st.date_input("To",value=datetime.now(),key="tf_ce")
            st.session_state.time_cs=ds; st.session_state.time_ce=de
        lbl=st.session_state.time_preset
        if lbl=="Month" and st.session_state.time_my:
            y2,m2=st.session_state.time_my; lbl=f"{datetime(y2,m2,1).strftime('%b')} {y2}"
        elif lbl=="Custom" and st.session_state.time_cs:
            lbl=f"{st.session_state.time_cs} → {st.session_state.time_ce}"
        st.markdown(f'<div style="text-align:center;margin-top:6px;font-family:monospace;font-size:10px;color:#ff6680">● {lbl}</div>',unsafe_allow_html=True)

    active_filter_label = lbl

    # ── Folders ────────────────────────────────────────────────
    if st.session_state.folders:
        st.markdown('<div class="sb-label">Client Folders</div>', unsafe_allow_html=True)
        folder_options = ["All Channels"] + sorted(st.session_state.folders.keys())
        for fname in folder_options:
            is_active = fname == (st.session_state.active_folder or "All Channels")
            if st.button(fname, key=f"folder_btn_{fname}",
                         type="primary" if is_active else "secondary",
                         use_container_width=True):
                st.session_state.active_folder = None if fname=="All Channels" else fname
                st.rerun()

    af = st.session_state.active_folder
    if af and af in st.session_state.folders:
        visible_channels = {k:v for k,v in st.session_state.channels.items()
                            if k in st.session_state.folders[af]}
    else:
        visible_channels = st.session_state.channels

    # ── Channel list ───────────────────────────────────────────
    st.markdown('<div class="sb-label">Channels</div>', unsafe_allow_html=True)

    if visible_channels:
        for ch_key in list(visible_channels.keys()):
            info  = st.session_state.channels[ch_key]
            stats_ch = info.get("channel_stats",{})
            display_name = stats_ch.get("channel_name") or ch_key
            subs_str = fmt(stats_ch.get("subscribers",0)) if stats_ch.get("subscribers") else "—"
            dot_cls  = "ch-dot" if info.get("data") is not None else "ch-dot ch-dot-empty"
            c1,c2 = st.columns([5,1])
            c1.markdown(f"""<div class="ch-pill">
                <div class="{dot_cls}"></div>
                <div style="flex:1;min-width:0">
                    <div class="ch-name" title="{_hesc.escape(ch_key)}">{_hesc.escape(display_name)}</div>
                    <div class="ch-subs">{subs_str} subs</div>
                </div></div>""", unsafe_allow_html=True)
            if c2.button("✕",key=f"del_{ch_key}"):
                delete_channel_from_db(ch_key)
                del st.session_state.channels[ch_key]
                st.rerun()

    with st.expander("➕  Add Channel"):
        new_id = st.text_input("Channel ID", placeholder="UCxxxxxxxxxxxxxxxxxxxx", label_visibility="collapsed")
        st.caption("Name is fetched automatically.")
        if st.button("Add Channel", type="primary", use_container_width=True):
            if not st.session_state.api_key:
                st.error("Enter API key first.")
            elif not new_id:
                st.error("Enter a Channel ID.")
            else:
                cid=new_id.strip()
                if cid in [v["id"] for v in st.session_state.channels.values()]:
                    st.error("Already added.")
                else:
                    with st.spinner("Looking up..."):
                        try:
                            ch_name=lookup_channel_name(st.session_state.api_key,cid)
                            if ch_name in st.session_state.channels:
                                ch_name=f"{ch_name} ({cid[-6:]})"
                            st.session_state.channels[ch_name]={"id":cid,"data":None,"channel_stats":{},"last_refreshed":"Never","notes":"","ideas":{}}
                            save_channel_to_db(ch_name,cid,{},None,"Never")
                            if st.session_state.active_folder:
                                add_channel_to_folder_db(st.session_state.active_folder,ch_name)
                                st.session_state.folders[st.session_state.active_folder].append(ch_name)
                            st.success(f"Added: {ch_name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

    with st.expander("📁  Folders"):
        nfn=st.text_input("New folder name",placeholder="Client Name",label_visibility="collapsed")
        if st.button("Create Folder",use_container_width=True):
            if nfn.strip():
                fn=nfn.strip()
                if fn not in st.session_state.folders:
                    save_folder_to_db(fn); st.session_state.folders[fn]=[]
                    st.success(f"Created: {fn}"); st.rerun()
                else: st.error("Already exists.")
        if st.session_state.folders and st.session_state.channels:
            st.markdown("---")
            ach=st.selectbox("Channel",list(st.session_state.channels.keys()),key="assign_ch",label_visibility="collapsed")
            afo=st.selectbox("Folder",list(st.session_state.folders.keys()),key="assign_f",label_visibility="collapsed")
            ca,cb=st.columns(2)
            if ca.button("Add",key="do_assign",use_container_width=True):
                if ach not in st.session_state.folders[afo]:
                    add_channel_to_folder_db(afo,ach); st.session_state.folders[afo].append(ach)
                    st.success("Added!"); st.rerun()
                else: st.info("Already in folder.")
            if cb.button("Remove",key="do_remove",use_container_width=True):
                if ach in st.session_state.folders[afo]:
                    remove_channel_from_folder_db(afo,ach); st.session_state.folders[afo].remove(ach)
                    st.success("Removed."); st.rerun()
        if st.session_state.folders:
            st.markdown("---")
            df2=st.selectbox("Delete folder",list(st.session_state.folders.keys()),key="del_f",label_visibility="collapsed")
            if st.button("🗑 Delete",key="do_del_folder",use_container_width=True):
                delete_folder_from_db(df2); del st.session_state.folders[df2]
                if st.session_state.active_folder==df2: st.session_state.active_folder=None
                st.rerun()

    st.divider()
    if st.session_state.api_key and visible_channels:
        rl=f"↺  Refresh {af}" if af else "↺  Refresh All"
        if st.button(rl, type="primary", use_container_width=True):
            errors=[]; prog=st.progress(0,text="Refreshing...")
            total=len(visible_channels)
            fetch_channel_data.clear()
            for i,(ch_key,info) in enumerate(visible_channels.items()):
                try:
                    df_new,st_new=fetch_channel_data(st.session_state.api_key,info["id"])
                    ts=datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.channels[ch_key].update({"data":df_new,"channel_stats":st_new,"last_refreshed":ts})
                    save_channel_to_db(ch_key,info["id"],st_new,df_new,ts,info.get("notes",""),info.get("ideas",{}))
                    prog.progress((i+1)/total,text=f"Done: {st_new.get('channel_name',ch_key)}")
                except Exception as e:
                    errors.append(f"{ch_key}: {e}")
            prog.empty()
            for err in errors: st.error(err)
            if not errors: st.success("All refreshed!")
            st.rerun()

# ─────────────────────────────────────────────────────────────
# GUARD
# ─────────────────────────────────────────────────────────────
if not st.session_state.api_key:
    st.markdown("""<div style="max-width:480px;margin:80px auto;text-align:center">
        <div style="font-size:48px;margin-bottom:16px">▶</div>
        <h2 style="font-size:22px;font-weight:700;color:#fff;margin-bottom:8px">Chamberlin Media Monitor</h2>
        <p style="color:#737373">Tap ☰ in the top-left to open the menu and enter your YouTube API key.</p>
    </div>""", unsafe_allow_html=True)
    st.stop()

if not st.session_state.channels:
    st.markdown("""<div style="max-width:480px;margin:80px auto;text-align:center">
        <div style="font-size:48px;margin-bottom:16px">📡</div>
        <h2 style="font-size:20px;font-weight:600;color:#fff;margin-bottom:8px">No channels yet</h2>
        <p style="color:#737373">Open the ☰ menu and add a YouTube channel.</p>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────
# ACTIVE FILTER
# ─────────────────────────────────────────────────────────────
_af=st.session_state.active_folder
if _af and _af in st.session_state.folders:
    view_channels={k:v for k,v in st.session_state.channels.items() if k in st.session_state.folders[_af]}
else:
    view_channels=st.session_state.channels

def get_filtered_df(info):
    df=info.get("data")
    if df is None or df.empty: return df
    p=st.session_state.time_preset
    if p=="Month": return apply_time_filter(df,"Month",custom_start=st.session_state.time_my)
    elif p=="Custom": return apply_time_filter(df,"Custom",custom_start=st.session_state.time_cs,custom_end=st.session_state.time_ce)
    else: return apply_time_filter(df,p)

# Time filter banner
if st.session_state.time_preset!="All Time":
    st.markdown(f"""<div style="background:rgba(255,0,51,.06);border:1px solid rgba(255,0,51,.2);
        border-radius:8px;padding:7px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px">
        <span style="font-size:11px;color:#ff6680;font-family:monospace;font-weight:700">● FILTERED:</span>
        <span style="font-size:12px;color:#e8e8e8">{active_filter_label}</span>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────────────────────
T_DASH, T_ALL, T_DETAIL = st.tabs(["  Dashboard  ","  All Channels  ","  Channel Detail  "])

# ═══════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════
with T_DASH:
    _title    = f"Dashboard — {_af}" if _af else "Dashboard"
    _subtitle = f"{len(view_channels)} channels" + (f" in {_af}" if _af else "")
    st.markdown(f'<h1 style="margin-bottom:2px">{_title}</h1><p style="color:var(--text-muted);font-size:12px;margin-bottom:18px">{_subtitle}</p>', unsafe_allow_html=True)

    total_subs  = sum(v.get("channel_stats",{}).get("subscribers",0) for v in view_channels.values())
    total_views = sum(v.get("channel_stats",{}).get("total_views",0)  for v in view_channels.values())
    loaded      = sum(1 for v in view_channels.values() if v.get("data") is not None)
    total_est_rev_mid = sum(
        int(info.get("data")["Views"].sum())*3.5/1000
        for info in view_channels.values()
        if info.get("data") is not None and not info.get("data").empty
    )

    st.markdown(f'''<div class="yt-bubble-row">
        <div class="yt-bubble yt-bubble-red">
            <div class="yt-bubble-label">Subscribers</div>
            <div class="yt-bubble-value">{fmt(total_subs)}</div>
            <div class="yt-bubble-sub">across all channels</div>
        </div>
        <div class="yt-bubble yt-bubble-blue">
            <div class="yt-bubble-label">Total Views</div>
            <div class="yt-bubble-value">{fmt(total_views)}</div>
            <div class="yt-bubble-sub">lifetime</div>
        </div>
        <div class="yt-bubble yt-bubble-gold">
            <div class="yt-bubble-label">Est. Revenue</div>
            <div class="yt-bubble-value">{fmt_usd(total_est_rev_mid)}</div>
            <div class="yt-bubble-sub">~$3.50 RPM</div>
        </div>
        <div class="yt-bubble yt-bubble-green">
            <div class="yt-bubble-label">Channels</div>
            <div class="yt-bubble-value">{len(view_channels)}</div>
            <div class="yt-bubble-sub">{loaded} loaded</div>
        </div>
    </div>''', unsafe_allow_html=True)

    # ── OUTLIER TRACKER ──────────────────────────────────────
    st.markdown('<div class="section-label" style="margin-top:4px">⚡ Outlier Tracker — Old Videos Spiking</div>', unsafe_allow_html=True)
    outliers = detect_outliers(st.session_state.channels)
    if outliers:
        for o in outliers:
            thu = _hesc.escape(o["thumbnail"])
            url = _hesc.escape(o["url"])
            tit = _hesc.escape(o["title"])
            thumb_el = (f'<img src="{thu}" class="outlier-thumb" loading="lazy">'
                        if thu else '<div class="outlier-thumb-ph">▶</div>')
            spike_x = f'{o["ratio"]:.1f}x'
            st.markdown(f"""<div class="outlier-card">
                <a href="{url}" target="_blank">{thumb_el}</a>
                <div class="outlier-body">
                    <div class="outlier-badge">⚡ {spike_x} above channel median</div>
                    <div class="outlier-title" title="{tit}">{tit}</div>
                    <div class="outlier-ch">{_hesc.escape(o['ch_display'])}</div>
                    <div class="outlier-stats">
                        <div class="outlier-stat">Views <span>{fmt(o['views'])}</span></div>
                        <div class="outlier-stat">Views/Day <span>{o['vpd']:.0f}</span></div>
                        <div class="outlier-stat">Age <span>{o['days']}d</span></div>
                        <div class="outlier-stat">Like Rate <span>{o['lr']:.2f}%</span></div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert alert-info"><div class="alert-icon">📊</div><div class="alert-body"><div class="alert-title">No outliers detected yet</div><div class="alert-desc">Refresh your channels — outliers appear when a 30+ day old video is getting 2× the channel\'s median views/day.</div></div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Revenue table ──────────────────────────────────────────
    rev_rows=[]
    for ch_name,info in view_channels.items():
        df_r=info.get("data"); s=info.get("channel_stats",{})
        if df_r is not None and not df_r.empty:
            tv=int(df_r["Views"].sum())
            rev_rows.append({
                "Channel":s.get("channel_name",ch_name),
                "Total Views":tv,
                "Est Low ($1.5)":fmt_usd(tv*1.5/1000),
                "Est Mid ($3.5)":fmt_usd(tv*3.5/1000),
                "Est High ($5)": fmt_usd(tv*5.0/1000),
            })
    if rev_rows:
        st.markdown('<div class="section-label">Estimated Revenue by Channel</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(rev_rows), use_container_width=True, hide_index=True)
        st.caption("⚠️ Estimates only — actual revenue varies by niche, RPM, and monetization status.")
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Top videos ────────────────────────────────────────────
    all_rows=[]
    for ch_name,info in view_channels.items():
        df=get_filtered_df(info)
        if df is not None and not df.empty:
            top=df.nlargest(8,"Views per Day").copy()
            top["Channel"]=ch_name
            all_rows.append(top)

    if all_rows:
        combined=pd.concat(all_rows).nlargest(12,"Views per Day").reset_index(drop=True)
        st.markdown('<div class="section-label">Top Videos — By Momentum</div>', unsafe_allow_html=True)
        render_thumb_table(combined, show_channel=True)

        st.markdown("<br>", unsafe_allow_html=True)
        all_full=pd.concat(all_rows)
        qw=all_full[all_full["Comment Rate %"]>all_full["Comment Rate %"].quantile(0.7)].nsmallest(4,"Views")
        if not qw.empty:
            st.markdown('<div class="section-label">Quick Wins — High Engagement, Low Reach</div>', unsafe_allow_html=True)
            for _,row in qw.iterrows():
                st.markdown(f"""<div class="alert alert-warn"><div class="alert-icon">💡</div>
                    <div class="alert-body"><div class="alert-title">{row.get('Channel','')} — {str(row['Title'])[:70]}</div>
                    <div class="alert-desc">{row['Comment Rate %']:.2f}% comment rate · only {fmt(row['Views'])} views</div>
                    </div></div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert alert-info"><div class="alert-icon">ℹ️</div><div class="alert-body"><div class="alert-title">No data for this period</div><div class="alert-desc">Try a wider time range or refresh your channels.</div></div></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════
# ALL CHANNELS
# ═══════════════════════════════════════════
with T_ALL:
    st.markdown('<h1 style="margin-bottom:2px">All Channels</h1><p style="color:var(--text-muted);font-size:12px;margin-bottom:18px">Portfolio overview</p>', unsafe_allow_html=True)
    rows=[]
    for ch_key,info in view_channels.items():
        df=get_filtered_df(info); s=info.get("channel_stats",{})
        tv=int(df["Views"].sum()) if df is not None and not df.empty else 0
        rows.append({
            "Channel":         s.get("channel_name",ch_key),
            "Subscribers":     s.get("subscribers",0),
            "Total Views":     s.get("total_views",0),
            "Videos in Period":len(df) if df is not None and not df.empty else 0,
            "Avg Views":       int(df["Views"].mean()) if df is not None and not df.empty else 0,
            "Avg Views/Day":   round(df["Views per Day"].mean(),1) if df is not None and not df.empty else 0,
            "Est Revenue":     fmt_usd(tv*3.5/1000),
            "Last Refreshed":  info.get("last_refreshed","Never"),
        })
    if rows:
        sdf=pd.DataFrame(rows).sort_values("Total Views",ascending=False)
        disp=sdf.copy()
        disp["Subscribers"]=disp["Subscribers"].apply(fmt)
        disp["Total Views"]=disp["Total Views"].apply(fmt)
        disp["Avg Views"]=disp["Avg Views"].apply(fmt)
        st.dataframe(disp, use_container_width=True, hide_index=True)
        st.download_button("⬇  Export CSV", sdf.to_csv(index=False).encode(), "chamberlin_channels.csv","text/csv")
        if len(rows)>1:
            st.markdown("<br>", unsafe_allow_html=True)
            fig_s=px.bar(sdf,x="Channel",y="Subscribers",title="Subscribers by Channel",
                         color="Subscribers",color_continuous_scale=["#1a0000","#ff0033"])
            fig_s.update_layout(**PLOTLY,showlegend=False,height=300)
            fig_s.update_traces(marker_line_width=0)
            fig_s.update_xaxes(tickangle=-30)
            st.plotly_chart(fig_s,use_container_width=True,config=plotly_cfg())
            fig_v=px.bar(sdf,x="Channel",y="Avg Views/Day",title="Avg Views/Day by Channel",
                         color="Avg Views/Day",color_continuous_scale=["#001a33","#1e8fff"])
            fig_v.update_layout(**PLOTLY,showlegend=False,height=300)
            fig_v.update_traces(marker_line_width=0)
            fig_v.update_xaxes(tickangle=-30)
            st.plotly_chart(fig_v,use_container_width=True,config=plotly_cfg())

# ═══════════════════════════════════════════
# CHANNEL DETAIL
# ═══════════════════════════════════════════
with T_DETAIL:
    selected=st.selectbox("Channel",
        list(view_channels.keys()) if view_channels else list(st.session_state.channels.keys()),
        label_visibility="collapsed")
    info=st.session_state.channels[selected]
    stats=info.get("channel_stats",{})
    ch_df_raw=info.get("data")
    ch_df=get_filtered_df(info)

    head_l,head_r=st.columns([5,2])
    with head_l:
        st.markdown(f'<h1>{stats.get("channel_name",selected)}</h1><p style="color:var(--text-muted);font-size:11px;font-family:monospace">ID: {info["id"]} · Refreshed: {info.get("last_refreshed","Never")}</p>', unsafe_allow_html=True)
    with head_r:
        st.markdown('<div class="refresh-btn-wrap">', unsafe_allow_html=True)
        if st.button("↺  Refresh", type="primary", use_container_width=True):
            with st.spinner("Fetching..."):
                try:
                    fetch_channel_data.clear()
                    df_new,st_new=fetch_channel_data(st.session_state.api_key,info["id"])
                    ts=datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.channels[selected].update({"data":df_new,"channel_stats":st_new,"last_refreshed":ts})
                    save_channel_to_db(selected,info["id"],st_new,df_new,ts,info.get("notes",""),info.get("ideas",{}))
                    st.success("Done!"); st.rerun()
                except Exception as e:
                    st.error(str(e))
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    if ch_df_raw is None or ch_df_raw.empty:
        st.markdown('<div class="alert alert-info"><div class="alert-icon">ℹ️</div><div class="alert-body"><div class="alert-title">No data loaded</div><div class="alert-desc">Click Refresh to load video data.</div></div></div>', unsafe_allow_html=True)
        st.stop()

    working_df = ch_df if (ch_df is not None and not ch_df.empty) else ch_df_raw
    if ch_df is not None and ch_df.empty and st.session_state.time_preset!="All Time":
        st.markdown(f'<div class="alert alert-warn"><div class="alert-icon">⚠️</div><div class="alert-body"><div class="alert-title">No videos in this period</div><div class="alert-desc">Showing all-time data instead.</div></div></div>', unsafe_allow_html=True)

    avg_views      = int(working_df["Views"].mean())
    total_views_ch = int(working_df["Views"].sum())
    avg_like_rate  = working_df["Like Rate %"].mean()
    avg_com_rate   = working_df["Comment Rate %"].mean()
    est_rev_low    = total_views_ch*1.5/1000
    est_rev_high   = total_views_ch*5.0/1000
    rev_str        = f"{fmt_usd(est_rev_low)}–{fmt_usd(est_rev_high)}"

    bubble_defs=[
        ("subscribers","Subscribers", fmt(stats.get("subscribers",0)),"total",       "yt-bubble-red"),
        ("views",      "Views",        fmt(total_views_ch),           "in period",   "yt-bubble-blue"),
        ("avg_views",  "Avg Views",    fmt(avg_views),                "per video",   "yt-bubble-green"),
        ("revenue",    "Est Revenue",  rev_str,                       "$1.5–$5 RPM", "yt-bubble-gold"),
        ("engagement", "Like Rate",    f"{avg_like_rate:.2f}%",       f"cmt {avg_com_rate:.2f}%","yt-bubble-grey"),
        ("videos",     "Videos",       str(len(working_df)),          "in period",   "yt-bubble-grey"),
    ]
    bhtml='<div class="yt-bubble-row">'
    for key,label,value,sub,cls in bubble_defs:
        ac="yt-bubble-active" if st.session_state.bubble_chart==key else ""
        bhtml+=f'<div class="yt-bubble {cls} {ac}"><div class="yt-bubble-label">{label}</div><div class="yt-bubble-value" style="font-size:18px">{value}</div><div class="yt-bubble-sub">{sub}</div></div>'
    bhtml+='</div>'
    st.markdown(bhtml,unsafe_allow_html=True)

    bc=st.columns(6)
    for i,(key,label,_,_,_) in enumerate(bubble_defs):
        if bc[i].button(f"↗",key=f"bub_{selected}_{key}",use_container_width=True,help=label):
            st.session_state.bubble_chart=None if st.session_state.bubble_chart==key else key
            st.rerun()

    bc_sel=st.session_state.bubble_chart
    if bc_sel=="views":
        vt=working_df.sort_values("Published")
        fig_v=go.Figure()
        fig_v.add_trace(go.Scatter(x=vt["Published"],y=vt["Views"].cumsum(),mode="lines",line=dict(color="#1e8fff",width=2),fill="tozeroy",fillcolor="rgba(30,143,255,.06)",name="Cumulative"))
        fig_v.add_trace(go.Bar(x=vt["Published"],y=vt["Views"],marker_color="rgba(30,143,255,.3)",marker_line_width=0,name="Per Video"))
        fig_v.update_layout(**PLOTLY,title="Views Over Time",height=320)
        st.plotly_chart(fig_v,use_container_width=True,config=plotly_cfg())
    elif bc_sel=="avg_views":
        fig_h=go.Figure()
        fig_h.add_trace(go.Histogram(x=working_df["Views"],nbinsx=20,marker_color="#ff0033",marker_line_width=0,opacity=.8))
        fig_h.add_vline(x=avg_views,line_dash="dash",line_color="#fff",annotation_text=f"Avg: {fmt(avg_views)}")
        fig_h.update_layout(**PLOTLY,title="Views Distribution",xaxis_title="Views",yaxis_title="# Videos",height=300)
        st.plotly_chart(fig_h,use_container_width=True,config=plotly_cfg())
    elif bc_sel=="revenue":
        rc=working_df.nlargest(15,"Views").copy()
        rc["Est Mid"]=(rc["Views"]*3.5/1000).round(0); rc=rc.sort_values("Est Mid"); rc["Label"]=rc["Title"].str[:45]
        fig_r=go.Figure(go.Bar(x=rc["Est Mid"],y=rc["Label"],orientation="h",
            marker=dict(color=rc["Est Mid"].tolist(),colorscale=[[0,"#1a0a00"],[1,"#f5a623"]],showscale=False),
            text=[f"${v:,.0f}" for v in rc["Est Mid"]],textposition="outside",textfont=dict(size=9,color="#737373")))
        fig_r.update_layout(**_pb(),title="Est. Revenue — Top 15 ($3.50 RPM)",height=max(300,len(rc)*34),showlegend=False,margin=dict(l=10,r=70,t=44,b=10),xaxis=dict(visible=False,gridcolor="#1e1e1e"),yaxis=dict(tickfont=dict(size=9),automargin=True,gridcolor="#1e1e1e",linecolor="#252525"))
        st.plotly_chart(fig_r,use_container_width=True,config=plotly_cfg())
        st.caption("⚠️ Estimates only.")
    elif bc_sel=="engagement":
        fig_lr=px.scatter(working_df,x="Views",y="Like Rate %",hover_name="Title",color="Like Rate %",color_continuous_scale="Reds",title="Like Rate vs Views")
        fig_lr.update_layout(**PLOTLY,height=280)
        st.plotly_chart(fig_lr,use_container_width=True,config=plotly_cfg())
        fig_cr=px.scatter(working_df,x="Views",y="Comment Rate %",hover_name="Title",color="Comment Rate %",color_continuous_scale=["#001a33","#1e8fff"],title="Comment Rate vs Views")
        fig_cr.update_layout(**PLOTLY,height=280)
        st.plotly_chart(fig_cr,use_container_width=True,config=plotly_cfg())
    elif bc_sel=="videos":
        m2=working_df.copy(); m2["Month"]=m2["Published"].dt.to_period("M").astype(str)
        cad=m2.groupby("Month").agg(Count=("Title","count"),Total_Views=("Views","sum")).reset_index()
        fig_cad=go.Figure()
        fig_cad.add_trace(go.Bar(x=cad["Month"],y=cad["Count"],name="Videos",marker_color="#252525",marker_line_width=0))
        fig_cad.add_trace(go.Scatter(x=cad["Month"],y=cad["Total_Views"],name="Total Views",yaxis="y2",line=dict(color="#ff0033",width=2),marker=dict(size=5,color="#ff0033")))
        P2={k:v for k,v in PLOTLY.items() if k not in ("xaxis","yaxis")}
        fig_cad.update_layout(**P2,title="Upload Cadence",xaxis=dict(tickangle=-30,tickfont=dict(size=9),automargin=True,gridcolor="#1e1e1e"),yaxis2=dict(overlaying="y",side="right",gridcolor="#1e1e1e",color="#737373"),legend=dict(orientation="h",y=1.1),height=320)
        st.plotly_chart(fig_cad,use_container_width=True,config=plotly_cfg())

    st.markdown("<br>",unsafe_allow_html=True)
    DT1,DT2,DT3,DT4,DT5=st.tabs(["  Videos  ","  Charts  ","  Upload Timing  ","  Content Series  ","  Notes  "])

    with DT1:
        sort_by=st.selectbox("Sort by",["Views","Views per Day","Like Rate %","Comment Rate %","Published"],label_visibility="collapsed")
        sd=working_df.sort_values(sort_by,ascending=(sort_by=="Published")).reset_index(drop=True)
        pk=f"vid_page_{selected}"; sk=f"vid_sort_{selected}"
        if pk not in st.session_state: st.session_state[pk]=0
        if st.session_state.get(sk)!=sort_by: st.session_state[pk]=0; st.session_state[sk]=sort_by
        per_page=20; total_pages=max(1,(len(sd)+per_page-1)//per_page); page=st.session_state[pk]
        render_thumb_table(sd.iloc[page*per_page:(page+1)*per_page].reset_index(drop=True))
        pc=st.columns([1,1,4,1,1])
        if pc[0].button("⟨⟨",key=f"first_{selected}",disabled=page==0): st.session_state[pk]=0; st.rerun()
        if pc[1].button("⟨",key=f"prev_{selected}",disabled=page==0): st.session_state[pk]-=1; st.rerun()
        pc[2].markdown(f'<p style="text-align:center;color:var(--text-muted);font-size:12px;padding-top:8px">Page {page+1}/{total_pages} — {len(sd)} videos</p>',unsafe_allow_html=True)
        if pc[3].button("⟩",key=f"next_{selected}",disabled=page>=total_pages-1): st.session_state[pk]+=1; st.rerun()
        if pc[4].button("⟩⟩",key=f"last_{selected}",disabled=page>=total_pages-1): st.session_state[pk]=total_pages-1; st.rerun()
        st.markdown("<br>",unsafe_allow_html=True)
        st.download_button("⬇  Export CSV",working_df.to_csv(index=False).encode(),f"{selected.replace(' ','_')}.csv","text/csv")

    with DT2:
        st.plotly_chart(chart_top_views(working_df),use_container_width=True,config=plotly_cfg())
        st.plotly_chart(chart_top_momentum(working_df),use_container_width=True,config=plotly_cfg())
        trend=working_df.sort_values("Published")
        fig3=go.Figure()
        fig3.add_trace(go.Scatter(x=trend["Published"],y=trend["Views"],mode="lines+markers",line=dict(color="#ff0033",width=2),marker=dict(color="#ff0033",size=4),fill="tozeroy",fillcolor="rgba(255,0,51,.06)",name="Views"))
        fig3.update_layout(**PLOTLY,title="Views Per Video Over Time",height=260)
        st.plotly_chart(fig3,use_container_width=True,config=plotly_cfg())
        fig_lk=go.Figure()
        fig_lk.add_trace(go.Bar(x=trend["Published"],y=trend["Likes"],marker_color="#ff0033",marker_line_width=0))
        fig_lk.update_layout(**PLOTLY,title="Likes Per Video",height=220)
        st.plotly_chart(fig_lk,use_container_width=True,config=plotly_cfg())
        fig_cm=go.Figure()
        fig_cm.add_trace(go.Bar(x=trend["Published"],y=trend["Comments"],marker_color="#1e8fff",marker_line_width=0))
        fig_cm.update_layout(**PLOTLY,title="Comments Per Video",height=220)
        st.plotly_chart(fig_cm,use_container_width=True,config=plotly_cfg())
        fig4=px.scatter(working_df,x="Views",y="Like Rate %",size="Comments",color="Comment Rate %",hover_name="Title",title="Engagement Map",color_continuous_scale="Reds")
        fig4.update_layout(**PLOTLY,height=300)
        st.plotly_chart(fig4,use_container_width=True,config=plotly_cfg())
        fig_decay=px.scatter(working_df,x="Days Since Publish",y="Views per Day",hover_name="Title",color="Views",color_continuous_scale=["#111","#ff0033"],title="Evergreen Detector")
        fig_decay.update_layout(**PLOTLY,height=300,xaxis_title="Days Since Published",yaxis_title="Views/Day")
        st.plotly_chart(fig_decay,use_container_width=True,config=plotly_cfg())
        st.caption("Videos above the trend at high age = evergreen content worth promoting.")
        rc2=working_df.nlargest(15,"Views").copy(); rc2["Est Revenue"]=(rc2["Views"]*3.5/1000).round(0); rc2=rc2.sort_values("Est Revenue"); rc2["Label"]=rc2["Title"].str[:45]
        fig_rv=go.Figure(go.Bar(x=rc2["Est Revenue"],y=rc2["Label"],orientation="h",marker=dict(color=rc2["Est Revenue"].tolist(),colorscale=[[0,"#1a0a00"],[1,"#f5a623"]],showscale=False),text=[f"${v:,.0f}" for v in rc2["Est Revenue"]],textposition="outside",textfont=dict(size=9,color="#737373")))
        fig_rv.update_layout(**_pb(),title="Est. Revenue — Top 15 ($3.50 RPM)",height=max(300,len(rc2)*34),showlegend=False,margin=dict(l=10,r=70,t=44,b=10),xaxis=dict(visible=False,gridcolor="#1e1e1e"),yaxis=dict(tickfont=dict(size=9),automargin=True,gridcolor="#1e1e1e",linecolor="#252525"))
        st.plotly_chart(fig_rv,use_container_width=True,config=plotly_cfg())
        st.caption("⚠️ Revenue estimates use $3.50 RPM midpoint.")

    with DT3:
        day_order=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        tmp=working_df.copy(); tmp["Day"]=tmp["Published"].dt.day_name()
        day_avg=tmp.groupby("Day")["Views"].mean().reindex(day_order).dropna()
        if not day_avg.empty:
            bd=day_avg.idxmax(); ba=day_avg.max()
            st.markdown(f"""<div class="best-day"><div class="best-day-icon">📅</div><div>
                <div class="best-day-label">Best Day to Upload</div>
                <div class="best-day-value">{bd}</div>
                <div class="best-day-sub">Avg {fmt(int(ba))} views</div>
            </div></div>""",unsafe_allow_html=True)
            fig_bd=px.bar(x=day_avg.index,y=day_avg.values,title="Avg Views by Upload Day",labels={"x":"","y":"Avg Views"},color=day_avg.values,color_continuous_scale=["#1a0000","#ff0033"])
            fig_bd.update_layout(**PLOTLY,showlegend=False,height=260)
            fig_bd.update_traces(marker_line_width=0)
            st.plotly_chart(fig_bd,use_container_width=True,config=plotly_cfg())
        mon=working_df.copy(); mon["Month"]=mon["Published"].dt.to_period("M").astype(str)
        freq=mon.groupby("Month").agg(Videos=("Title","count"),Avg_Views=("Views","mean")).reset_index()
        freq["Avg_Views"]=freq["Avg_Views"].round(0).astype(int)
        fig_fr=px.bar(freq,x="Month",y="Videos",title="Videos Posted per Month",labels={"Videos":"Videos","Month":""})
        fig_fr.update_traces(marker_color="#2a2a2a",marker_line_width=0)
        fig_fr.update_layout(**PLOTLY,height=240)
        fig_fr.update_xaxes(tickangle=-40,tickfont=dict(size=9))
        st.plotly_chart(fig_fr,use_container_width=True,config=plotly_cfg())
        fig_av=px.line(freq,x="Month",y="Avg_Views",title="Avg Views per Month",labels={"Avg_Views":"Avg Views","Month":""},markers=True)
        fig_av.update_traces(line_color="#ff0033",marker_color="#ff0033",marker_size=6)
        fig_av.update_layout(**PLOTLY,height=240)
        fig_av.update_xaxes(tickangle=-40,tickfont=dict(size=9))
        st.plotly_chart(fig_av,use_container_width=True,config=plotly_cfg())

    with DT4:
        st.markdown('<div class="section-label">Topic Analysis</div>',unsafe_allow_html=True)
        titles=working_df["Title"].tolist()
        words_all=[]
        for t in titles: words_all.extend(re.findall(r"\b[A-Za-z]{3,}\b",t))
        stop={"this","that","with","from","have","what","your","they","their","will","more","just","been","like","also","when","then","than","about","which","there","after","video","youtube","channel","episode","part","feat","official","full","new","the","and","for","are","but","not","you","all","can","her","was","one","our","out","day","get","has","him","his","how","its","let","may","now","old","own","see","two","way","who","boy","did","use"}
        filtered=[w.lower() for w in words_all if w.lower() not in stop and len(w)>3]
        top_words=Counter(filtered).most_common(20)
        if top_words:
            tags_html='<div class="tags">'
            for word,count in top_words[:14]:
                mask=working_df["Title"].str.contains(word,case=False,na=False)
                avg_v=int(working_df.loc[mask,"Views"].mean()) if mask.any() else 0
                cls="tag tag-hot" if avg_v>working_df["Views"].mean() else "tag"
                tags_html+=f'<span class="{cls}">{word} ({count})</span>'
            tags_html+='</div>'
            st.markdown(tags_html,unsafe_allow_html=True)
            st.caption("🔴 Red = above-average views for this keyword")
        phrases=[]
        for t in titles:
            ws=re.findall(r"\b[A-Za-z]{3,}\b",t)
            phrases.extend([f"{ws[i]} {ws[i+1]}" for i in range(len(ws)-1)])
        stop_ph={"and the","in the","on the","of the","to the","is a","it is","with the","for the","how to","that is","this is","you are"}
        ph_f=[p.lower() for p in phrases if p.lower() not in stop_ph]
        ph_ct=Counter(ph_f).most_common(12)
        if ph_ct:
            phr_df=pd.DataFrame(ph_ct,columns=["Phrase","Count"])
            phr_df["Avg Views"]=phr_df["Phrase"].apply(lambda p: int(working_df.loc[working_df["Title"].str.contains(p,case=False,na=False),"Views"].mean()) if working_df["Title"].str.contains(p,case=False,na=False).any() else 0)
            phr_df=phr_df.sort_values("Avg Views",ascending=False)
            fig_ph=px.scatter(phr_df,x="Count",y="Avg Views",text="Phrase",title="Topic Frequency vs. Avg Views",color="Avg Views",color_continuous_scale="Reds",size="Count")
            fig_ph.update_traces(textposition="top center",textfont=dict(size=9,color="#e8e8e8"))
            fig_ph.update_layout(**PLOTLY,height=360)
            st.plotly_chart(fig_ph,use_container_width=True,config=plotly_cfg())
            st.dataframe(phr_df,use_container_width=True,hide_index=True)

    with DT5:
        st.markdown('<div class="section-label">Team Notes</div>',unsafe_allow_html=True)
        new_notes=st.text_area("Notes",value=info.get("notes",""),height=200,placeholder="Observations, strategy, action items...",label_visibility="collapsed")
        if st.button("💾  Save Notes",type="primary"):
            st.session_state.channels[selected]["notes"]=new_notes
            save_channel_to_db(selected,info["id"],stats,ch_df_raw,info.get("last_refreshed",""),new_notes,info.get("ideas",{}))
            st.success("Saved.")

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("<br><br>",unsafe_allow_html=True)
st.divider()
st.markdown('<p style="color:#4a4a4a;font-size:11px;font-family:monospace">Chamberlin Media Monitor  •  YouTube Data API v3  •  Built for Chamberlin Media</p>',unsafe_allow_html=True)
