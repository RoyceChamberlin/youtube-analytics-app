"""
Chamberlin Media Monitor — Render.com
YouTube Data API v3
"""
import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re, json, os, html as _h
from datetime import datetime, timedelta
import sqlite3, contextlib
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Chamberlin Media Monitor",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# PASSWORD GATE
# ─────────────────────────────────────────────────────────────
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""<style>
    body{background:#000!important}
    .lw{max-width:340px;margin:120px auto;text-align:center}
    .li{width:52px;height:52px;background:#ff0033;border-radius:12px;display:flex;
        align-items:center;justify-content:center;font-size:22px;font-weight:900;
        color:#fff;margin:0 auto 18px;box-shadow:0 0 32px rgba(255,0,51,.4)}
    .lt{font-size:20px;font-weight:700;color:#fff;margin-bottom:4px}
    .ls{font-size:13px;color:#555;margin-bottom:28px}
    </style>
    <div class="lw">
      <div class="li">▶</div>
      <div class="lt">Chamberlin Media Monitor</div>
      <div class="ls">Enter password to continue</div>
    </div>""", unsafe_allow_html=True)
    col = st.columns([1,2,1])[1]
    with col:
        pwd = st.text_input("pw", type="password", placeholder="Password", label_visibility="collapsed")
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
# DESIGN SYSTEM — pure black + neon glow aesthetic
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
*,*::before,*::after{box-sizing:border-box}
h1 a,h2 a,h3 a{display:none!important}

:root{
  --bg:#000000;
  --bg-2:#080808;
  --bg-3:#0d0d0d;
  --bg-4:#141414;
  --bg-5:#1a1a1a;
  --border:#1e1e1e;
  --border-2:#2a2a2a;
  --text:#f0f0f0;
  --text-muted:#555;
  --text-dim:#333;
  --red:#ff2244;
  --red-glow:rgba(255,34,68,.25);
  --blue:#00aaff;
  --blue-glow:rgba(0,170,255,.2);
  --green:#00ff88;
  --green-glow:rgba(0,255,136,.2);
  --gold:#ffaa00;
  --gold-glow:rgba(255,170,0,.2);
  --purple:#aa44ff;
  --purple-glow:rgba(170,68,255,.2);
  --font:'Inter',sans-serif;
  --font-mono:'JetBrains Mono',monospace;
  --radius:10px;--radius-sm:7px;
}

html,body,[class*="css"]{
  font-family:var(--font);
  background:#000!important;
  color:var(--text);
}
.stApp{background:#000!important}

/* ── Kill ALL Streamlit chrome ── */
#MainMenu,footer,header,
[data-testid="stToolbar"],[data-testid="stStatusWidget"],
[data-testid="stDecoration"],[data-testid="stHeader"],
.stDeployButton,[class*="viewerBadge"],
.viewerBadge_container__1QSob,.stActionButton,
[data-testid="manage-app-button"]{
  display:none!important;visibility:hidden!important;height:0!important
}

/* ── Kill native Streamlit sidebar entirely — we use our own ── */
[data-testid="stSidebar"]{display:none!important}
[data-testid="collapsedControl"]{display:none!important}

/* ── Main content full width, padded for our custom hamburger ── */
.main .block-container{
  padding:1.2rem 1.5rem 5rem!important;
  max-width:1440px;
  margin-left:0!important;
}

/* ── Typography ── */
h1{font-family:var(--font);font-weight:700;font-size:20px;letter-spacing:-.3px;color:#fff!important;margin:0!important;padding:0!important}
h2{font-family:var(--font);font-weight:600;font-size:16px;color:#fff!important;margin-bottom:4px!important}
p,li{font-size:14px;line-height:1.6}

/* ── Buttons — glow on primary ── */
.stButton>button{
  font-family:var(--font)!important;font-weight:600!important;font-size:12px!important;
  border-radius:var(--radius-sm)!important;border:none!important;
  padding:8px 16px!important;transition:all .2s ease!important;cursor:pointer;
  letter-spacing:.2px;
}
.stButton>button[kind="primary"]{
  background:var(--red)!important;color:#fff!important;
  box-shadow:0 0 16px var(--red-glow)!important;
}
.stButton>button[kind="primary"]:hover{
  background:#ff0033!important;
  box-shadow:0 0 28px rgba(255,34,68,.5)!important;
}
.stButton>button[kind="secondary"]{
  background:var(--bg-4)!important;color:var(--text-muted)!important;
  border:1px solid var(--border-2)!important;
}
.stButton>button[kind="secondary"]:hover{
  color:var(--text)!important;border-color:#444!important;
  background:var(--bg-5)!important;
}

/* ── Inputs ── */
.stTextInput>div>input,.stTextArea>div>textarea{
  background:var(--bg-3)!important;border:1px solid var(--border-2)!important;
  border-radius:var(--radius-sm)!important;color:var(--text)!important;
  font-family:var(--font)!important;font-size:13px!important;
}
.stTextInput>div>input:focus,.stTextArea>div>textarea:focus{
  border-color:var(--red)!important;
  box-shadow:0 0 0 3px var(--red-glow)!important;
}
.stSelectbox>div>div{
  background:var(--bg-3)!important;border:1px solid var(--border-2)!important;
  border-radius:var(--radius-sm)!important;color:var(--text)!important;
  font-family:var(--font)!important;font-size:13px!important;
}
label{color:var(--text-muted)!important;font-size:11px!important;font-weight:500!important}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"]{
  border-bottom:1px solid var(--border)!important;background:transparent!important;
  gap:0!important;padding:0!important;overflow-x:auto!important;flex-wrap:nowrap!important;
}
[data-testid="stTabs"] button[role="tab"]{
  font-family:var(--font)!important;font-size:12px!important;font-weight:500!important;
  color:var(--text-muted)!important;background:transparent!important;border:none!important;
  border-bottom:2px solid transparent!important;border-radius:0!important;
  padding:10px 16px!important;white-space:nowrap;transition:all .15s!important;
}
[data-testid="stTabs"] button[role="tab"]:hover{color:#888!important}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{
  color:#fff!important;border-bottom:2px solid var(--red)!important;
  text-shadow:0 0 12px var(--red-glow);
}
[data-testid="stTabs"] [data-testid="stTabsContent"]{padding-top:20px!important}

/* ── DataFrames ── */
[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:var(--radius)!important;overflow:hidden!important}
[data-testid="stDataFrame"] thead th{background:var(--bg-3)!important;color:var(--text-muted)!important;font-size:9px!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:.8px!important;border-bottom:1px solid var(--border)!important;padding:8px 12px!important}
[data-testid="stDataFrame"] tbody td{font-size:12px!important;border-bottom:1px solid var(--border)!important;padding:7px 12px!important;color:var(--text)!important}
[data-testid="stDataFrame"] tbody tr:hover td{background:var(--bg-3)!important}

/* ── Expander ── */
.streamlit-expanderHeader{background:var(--bg-3)!important;border:1px solid var(--border-2)!important;border-radius:var(--radius-sm)!important;color:var(--text)!important;font-family:var(--font)!important;font-size:12px!important;font-weight:500!important;padding:9px 12px!important}
.streamlit-expanderContent{background:var(--bg-2)!important;border:1px solid var(--border)!important;border-top:none!important;border-radius:0 0 var(--radius-sm) var(--radius-sm)!important}

/* ── Progress ── */
[data-testid="stProgressBar"]>div>div{background:var(--red)!important;border-radius:2px!important;box-shadow:0 0 8px var(--red-glow)!important}
[data-testid="stProgressBar"]>div{background:var(--bg-4)!important;border-radius:2px!important;height:2px!important}

hr{border-color:var(--border)!important;margin:12px 0!important}
::-webkit-scrollbar{width:3px;height:3px}
::-webkit-scrollbar-track{background:#000}
::-webkit-scrollbar-thumb{background:#222;border-radius:3px}

/* ── GLOW STAT BUBBLES ── */
.yt-bubble-row{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}
.yt-bubble{
  background:var(--bg-3);border:1px solid var(--border-2);
  border-radius:12px;padding:16px 18px;flex:1 1 130px;min-width:120px;
  transition:all .2s ease;position:relative;overflow:hidden;
}
.yt-bubble::before{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:inherit;opacity:.5;
}
.yt-bubble-label{font-family:var(--font-mono);font-size:8px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.4px;margin-bottom:8px}
.yt-bubble-value{font-size:24px;font-weight:700;color:#fff;letter-spacing:-.5px;line-height:1;margin-bottom:3px}
.yt-bubble-sub{font-size:10px;color:var(--text-muted)}
/* Colored variants with glow */
.yt-bubble-red{border-left:2px solid var(--red);box-shadow:inset 0 0 30px rgba(255,34,68,.04),0 0 0 0 transparent}
.yt-bubble-red:hover{box-shadow:0 0 20px rgba(255,34,68,.12);border-color:rgba(255,34,68,.4)}
.yt-bubble-red .yt-bubble-value{color:var(--red);text-shadow:0 0 20px var(--red-glow)}
.yt-bubble-blue{border-left:2px solid var(--blue)}
.yt-bubble-blue:hover{box-shadow:0 0 20px var(--blue-glow);border-color:rgba(0,170,255,.3)}
.yt-bubble-blue .yt-bubble-value{color:var(--blue);text-shadow:0 0 20px var(--blue-glow)}
.yt-bubble-green{border-left:2px solid var(--green)}
.yt-bubble-green:hover{box-shadow:0 0 20px var(--green-glow);border-color:rgba(0,255,136,.3)}
.yt-bubble-green .yt-bubble-value{color:var(--green);text-shadow:0 0 20px var(--green-glow)}
.yt-bubble-gold{border-left:2px solid var(--gold)}
.yt-bubble-gold:hover{box-shadow:0 0 20px var(--gold-glow);border-color:rgba(255,170,0,.3)}
.yt-bubble-gold .yt-bubble-value{color:var(--gold);text-shadow:0 0 20px var(--gold-glow)}
.yt-bubble-grey{border-left:2px solid #333}
.yt-bubble-active{border-color:var(--red)!important;box-shadow:0 0 20px var(--red-glow)!important}

/* ── GLOW CARDS (outlier tracker) ── */
.outlier-card{
  background:var(--bg-3);
  border:1px solid var(--border-2);
  border-left:2px solid var(--green);
  border-radius:12px;
  padding:14px 16px;margin-bottom:8px;
  display:flex;align-items:flex-start;gap:12px;
  transition:all .2s;
  box-shadow:inset 0 0 40px rgba(0,255,136,.02);
}
.outlier-card:hover{
  border-color:rgba(0,255,136,.3);
  box-shadow:0 0 24px rgba(0,255,136,.08);
}
.outlier-thumb{width:88px;height:50px;object-fit:cover;border-radius:6px;flex-shrink:0}
.outlier-thumb-ph{width:88px;height:50px;background:var(--bg-5);border-radius:6px;display:flex;align-items:center;justify-content:center;color:#333;font-size:18px;flex-shrink:0}
.outlier-body{flex:1;min-width:0}
.outlier-badge{
  display:inline-flex;align-items:center;gap:5px;
  background:rgba(0,255,136,.1);border:1px solid rgba(0,255,136,.2);
  color:var(--green);padding:2px 8px;border-radius:4px;
  font-size:9px;font-weight:700;font-family:var(--font-mono);
  letter-spacing:.5px;margin-bottom:5px;
  text-shadow:0 0 10px var(--green-glow);
}
.outlier-title{font-size:13px;font-weight:600;color:#fff;line-height:1.4;margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.outlier-ch{font-size:9px;color:var(--red);font-weight:700;margin-bottom:5px;font-family:var(--font-mono);letter-spacing:.3px}
.outlier-stats{display:flex;gap:14px;flex-wrap:wrap}
.o-stat{font-family:var(--font-mono);font-size:9px;color:var(--text-muted)}
.o-stat span{color:#ccc;font-weight:600}

/* ── Section label ── */
.section-label{
  font-family:var(--font-mono);font-size:8px;font-weight:600;
  color:var(--text-dim);text-transform:uppercase;letter-spacing:2px;
  margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border);
}

/* ── Alert rows ── */
.alert{border-radius:var(--radius-sm);padding:10px 12px;font-size:13px;margin-bottom:8px;display:flex;align-items:flex-start;gap:10px}
.alert-icon{font-size:14px;flex-shrink:0;margin-top:1px}
.alert-body{flex:1}
.alert-title{font-weight:600;margin-bottom:2px}
.alert-desc{font-size:11px;opacity:.7}
.alert-warn{background:rgba(255,170,0,.06);border:1px solid rgba(255,170,0,.2);color:#cc9900}
.alert-info{background:rgba(0,170,255,.06);border:1px solid rgba(0,170,255,.15);color:#0088cc}

/* Best day */
.best-day{background:var(--bg-3);border:1px solid rgba(0,255,136,.15);border-radius:var(--radius);padding:14px 18px;display:flex;align-items:center;gap:14px;margin-bottom:16px;box-shadow:0 0 20px rgba(0,255,136,.05)}
.best-day-label{font-size:9px;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;font-family:var(--font-mono);margin-bottom:2px}
.best-day-value{font-size:22px;font-weight:700;color:var(--green);text-shadow:0 0 16px var(--green-glow)}
.best-day-sub{font-size:11px;color:var(--text-muted)}

/* Tags */
.tags{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:14px}
.tag{background:var(--bg-4);border:1px solid var(--border-2);color:var(--text-muted);padding:3px 9px;border-radius:20px;font-size:11px;font-weight:500;font-family:var(--font-mono)}
.tag-hot{border-color:rgba(255,34,68,.3);color:#ff6680;background:rgba(255,34,68,.06);text-shadow:0 0 8px rgba(255,34,68,.3)}

.refresh-btn-wrap .stButton>button{font-size:11px!important;padding:5px 12px!important}
.stTextArea textarea{font-family:var(--font-mono)!important;font-size:12px!important;line-height:1.7!important}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# PLOTLY THEME — pure black
# ─────────────────────────────────────────────────────────────
PLOTLY = dict(
    paper_bgcolor="#000000", plot_bgcolor="#080808",
    font=dict(family="Inter", color="#555", size=11),
    xaxis=dict(gridcolor="#111", zerolinecolor="#1a1a1a", linecolor="#1a1a1a",
               tickfont=dict(size=10), automargin=True),
    yaxis=dict(gridcolor="#111", zerolinecolor="#1a1a1a", linecolor="#1a1a1a",
               tickfont=dict(size=10), automargin=True),
    margin=dict(l=10, r=10, t=44, b=40),
    title_font=dict(size=13, color="#e8e8e8", family="Inter"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e1e1e", font=dict(size=11)),
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
            likes INTEGER DEFAULT 0, comments INTEGER DEFAULT 0, url TEXT, thumbnail TEXT,
            days_since_publish INTEGER DEFAULT 0, views_per_day REAL DEFAULT 0,
            like_rate REAL DEFAULT 0, comment_rate REAL DEFAULT 0,
            FOREIGN KEY (channel_name) REFERENCES channels(name) ON DELETE CASCADE)""")
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
                df = df.rename(columns={"title":"Title","views":"Views","likes":"Likes","comments":"Comments","url":"URL","thumbnail":"Thumbnail","days_since_publish":"Days Since Publish","views_per_day":"Views per Day","like_rate":"Like Rate %","comment_rate":"Comment Rate %"})
            channels[ch["name"]] = {"id":ch["channel_id"],"data":df,"channel_stats":stats,"last_refreshed":ch["last_refreshed"],"notes":ch["notes"] or "","ideas":ideas}
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
                db.execute("INSERT INTO videos (channel_name,title,published,views,likes,comments,url,thumbnail,days_since_publish,views_per_day,like_rate,comment_rate) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (name,row.get("Title",""),pub,int(row.get("Views",0)),int(row.get("Likes",0)),int(row.get("Comments",0)),row.get("URL",""),row.get("Thumbnail",""),int(row.get("Days Since Publish",0)),float(row.get("Views per Day",0)),float(row.get("Like Rate %",0)),float(row.get("Comment Rate %",0))))

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
            folders[fname] = [r["channel_name"] for r in db.execute("SELECT channel_name FROM folder_channels WHERE folder_name=?",(fname,)).fetchall()]
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
    if not ch_resp.get("items"): raise ValueError(f"Channel not found: {channel_id}")
    ch = ch_resp["items"][0]
    stats = {
        "subscribers": int(ch["statistics"].get("subscriberCount",0)),
        "total_views":  int(ch["statistics"].get("viewCount",0)),
        "channel_name": ch["snippet"]["title"],
        "channel_thumb":ch["snippet"]["thumbnails"].get("medium",{}).get("url",""),
        "description":  ch["snippet"].get("description","")[:300],
    }
    uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    videos, next_page = [], None
    for _ in range(2):
        pl = youtube.playlistItems().list(part="contentDetails",playlistId=uploads_id,maxResults=50,pageToken=next_page).execute()
        video_ids = [i["contentDetails"]["videoId"] for i in pl["items"]]
        vr = youtube.videos().list(part="snippet,statistics",id=",".join(video_ids)).execute()
        for item in vr["items"]:
            s=item["statistics"]; sn=item["snippet"]
            thumbs=sn.get("thumbnails",{})
            thumb_url=(thumbs.get("maxres") or thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url","")
            videos.append({"Title":sn["title"],"Published":sn["publishedAt"][:10],"Views":int(s.get("viewCount",0)),"Likes":int(s.get("likeCount",0)),"Comments":int(s.get("commentCount",0)),"URL":f"https://youtu.be/{item['id']}","Thumbnail":thumb_url})
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
    if not resp.get("items"): raise ValueError(f"No channel found: {channel_id}")
    return resp["items"][0]["snippet"]["title"]

# ─────────────────────────────────────────────────────────────
# TIME FILTER
# ─────────────────────────────────────────────────────────────
TIME_PRESETS = {"7d":7,"30d":30,"90d":90,"6mo":180,"1yr":365,"All":0}

def apply_time_filter(df, preset, custom_start=None, custom_end=None):
    if df is None or df.empty or "Published" not in df.columns: return df
    if preset=="Custom" and custom_start and custom_end:
        s=pd.Timestamp(custom_start); e=pd.Timestamp(custom_end)+pd.Timedelta(days=1)
        return df[(df["Published"]>=s)&(df["Published"]<e)]
    if preset=="Month" and custom_start:
        y,m=custom_start; s=pd.Timestamp(year=y,month=m,day=1)
        e=(s+pd.offsets.MonthEnd(1))+pd.Timedelta(days=1)
        return df[(df["Published"]>=s)&(df["Published"]<e)]
    days=TIME_PRESETS.get(preset,0)
    if days==0: return df
    return df[df["Published"]>=pd.Timestamp(datetime.now()-timedelta(days=days))]

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
    outliers=[]
    for ch_name,info in channels.items():
        df=info.get("data"); stats=info.get("channel_stats",{})
        if df is None or df.empty: continue
        old=df[df["Days Since Publish"]>=30]
        if old.empty: continue
        median_vpd=old["Views per Day"].median()
        if median_vpd<=0: continue
        ch_display=stats.get("channel_name",ch_name)
        for _,row in old.iterrows():
            ratio=row.get("Views per Day",0)/median_vpd
            if ratio>=2.0:
                outliers.append({"channel":ch_name,"ch_display":ch_display,"title":row.get("Title",""),"url":row.get("URL",""),"thumbnail":row.get("Thumbnail",""),"views":int(row.get("Views",0)),"vpd":float(row.get("Views per Day",0)),"days":int(row.get("Days Since Publish",0)),"ratio":ratio,"lr":float(row.get("Like Rate %",0))})
    outliers.sort(key=lambda x:x["ratio"],reverse=True)
    return outliers[:12]

def render_thumb_table(df, show_channel=False, height=580):
    rows=""
    for _,row in df.iterrows():
        b=""
        if row.get("Days Since Publish",999)<=14: b="NEW"
        elif row.get("Views per Day",0)>=500: b="HOT"
        elif row.get("Days Since Publish",0)>=90 and row.get("Views per Day",0)>=100: b="EVERGREEN"
        bmap={"NEW":("#00aaff","rgba(0,170,255,.15)"),"HOT":("#ff2244","rgba(255,34,68,.15)"),"EVERGREEN":("#00ff88","rgba(0,255,136,.15)")}
        badge=(f'<span style="background:{bmap[b][1]};color:{bmap[b][0]};border:1px solid {bmap[b][0]}33;padding:2px 7px;border-radius:3px;font-size:8px;font-weight:700;letter-spacing:.5px;font-family:monospace;margin-right:4px">{b}</span>' if b else "")
        thu=_h.escape(str(row.get("Thumbnail",""))); url=_h.escape(str(row.get("URL","#"))); tit=_h.escape(str(row.get("Title","")))
        pub=row["Published"].strftime("%Y-%m-%d") if pd.notna(row.get("Published")) else "—"
        ch_html=(f'<div style="font-size:9px;color:#ff2244;font-weight:700;margin-bottom:2px;letter-spacing:.3px">{_h.escape(str(row.get("Channel","")))}</div>' if show_channel and row.get("Channel") else "")
        thumb=(f'<img src="{thu}" style="width:106px;height:60px;object-fit:cover;border-radius:5px;display:block" loading="lazy">' if thu else '<div style="width:106px;height:60px;background:#111;border-radius:5px;display:flex;align-items:center;justify-content:center;color:#333;font-size:16px">▶</div>')
        rows+=f"""<tr class="vrow">
          <td style="padding:7px 8px;width:122px"><a href="{url}" target="_blank">{thumb}</a></td>
          <td style="padding:7px 10px;min-width:160px;max-width:300px">
            {ch_html}
            <div style="font-size:12px;font-weight:600;color:#e8e8e8;line-height:1.4;margin-bottom:2px">{tit}</div>
            <div style="font-size:9px;color:#444;margin-bottom:3px">{pub} · {int(row.get('Days Since Publish',0))}d</div>
            {badge}<a href="{url}" target="_blank" style="color:#ff2244;font-size:9px;font-weight:700;text-decoration:none;letter-spacing:.3px">WATCH ↗</a>
          </td>
          <td class="n">{fmt(int(row.get('Views',0)))}</td>
          <td class="n nh">{fmt(int(row.get('Likes',0)))}</td>
          <td class="n nh">{fmt(int(row.get('Comments',0)))}</td>
          <td class="n">{row.get('Views per Day',0):.1f}</td>
          <td class="n nh">{row.get('Like Rate %',0):.2f}%</td>
          <td class="n nh">{row.get('Comment Rate %',0):.2f}%</td>
        </tr>"""
    doc=f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
      *{{box-sizing:border-box;margin:0;padding:0}}
      body{{background:#000;font-family:'Inter',system-ui,sans-serif;color:#e8e8e8;overflow-x:auto}}
      table{{width:100%;border-collapse:collapse;min-width:380px}}
      thead tr{{background:#080808;position:sticky;top:0;z-index:10}}
      th{{padding:8px 10px;text-align:right;font-size:8px;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid #111;white-space:nowrap}}
      th:nth-child(1),th:nth-child(2){{text-align:left}}
      .vrow:hover td{{background:#0a0a0a}}
      td{{border-bottom:1px solid #0d0d0d;vertical-align:middle}}
      .n{{text-align:right;font-family:'JetBrains Mono',monospace;font-size:11px;color:#ccc;white-space:nowrap;padding:7px 10px}}
      ::-webkit-scrollbar{{width:3px;height:3px}}
      ::-webkit-scrollbar-track{{background:#000}}
      ::-webkit-scrollbar-thumb{{background:#1a1a1a;border-radius:2px}}
      @media(max-width:520px){{.nh,.th-h{{display:none}}table{{min-width:280px}}}}
    </style></head><body>
    <table><thead><tr>
      <th>Thumb</th><th>Title</th><th>Views</th>
      <th class="th-h">Likes</th><th class="th-h">Comments</th>
      <th>V/Day</th><th class="th-h">Like%</th><th class="th-h">Cmt%</th>
    </tr></thead><tbody>{rows}</tbody></table></body></html>"""
    components.html(doc, height=height, scrolling=True)

def chart_top_views(df, n=10):
    top=df.nlargest(n,"Views")[["Title","Views"]].sort_values("Views").copy()
    top["Label"]=top["Title"].str[:45]; colors=top["Views"].tolist()
    fig=go.Figure(go.Bar(x=top["Views"],y=top["Label"],orientation="h",
        marker=dict(color=colors,colorscale=[[0,"#1a0008"],[1,"#ff2244"]],showscale=False),
        text=[fmt(v) for v in top["Views"]],textposition="outside",textfont=dict(size=10,color="#444")))
    fig.update_layout(**_pb(),title=f"Top {n} by Total Views",height=max(260,n*34),showlegend=False,
        margin=dict(l=10,r=70,t=40,b=10),
        xaxis=dict(visible=False,gridcolor="#0d0d0d"),
        yaxis=dict(tickfont=dict(size=10,color="#555"),automargin=True,gridcolor="#0d0d0d",linecolor="#111"))
    return fig

def chart_top_momentum(df, n=10):
    top=df.nlargest(n,"Views per Day")[["Title","Views per Day"]].sort_values("Views per Day").copy()
    top["Label"]=top["Title"].str[:45]; colors=top["Views per Day"].tolist()
    fig=go.Figure(go.Bar(x=top["Views per Day"],y=top["Label"],orientation="h",
        marker=dict(color=colors,colorscale=[[0,"#000d1a"],[1,"#00aaff"]],showscale=False),
        text=[f'{v:.0f}' for v in top["Views per Day"]],textposition="outside",textfont=dict(size=10,color="#444")))
    fig.update_layout(**_pb(),title=f"Top {n} by Momentum (V/Day)",height=max(260,n*34),showlegend=False,
        margin=dict(l=10,r=70,t=40,b=10),
        xaxis=dict(visible=False,gridcolor="#0d0d0d"),
        yaxis=dict(tickfont=dict(size=10,color="#555"),automargin=True,gridcolor="#0d0d0d",linecolor="#111"))
    return fig

# ─────────────────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────────────────
init_db()

SEED_DATA = {
    "Angel Studios":[("UCb02Js81Etta5BgML6jK-fQ","Angel Studios"),("UCYxkRL8mgBlunTKYX4In7LA","Angel Kids"),("UCZFLi-CFABqg49AVj3ZY38Q","Angel Studios 2"),("UCPMnn5ZkYHf2epbcekcImPQ","Angel Studios 3"),("UCw6rIEbumyIW-Gu34Q3jFeg","Angel Studios 4")],
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
if "time_preset"   not in st.session_state: st.session_state.time_preset   = "All"
if "time_cs"       not in st.session_state: st.session_state.time_cs       = None
if "time_ce"       not in st.session_state: st.session_state.time_ce       = None
if "time_my"       not in st.session_state: st.session_state.time_my       = None
if "sb_open"       not in st.session_state: st.session_state.sb_open       = False

# ─────────────────────────────────────────────────────────────
# CUSTOM SIDEBAR — fully custom HTML/CSS/JS overlay
# No dependency on Streamlit's native sidebar at all.
# Communicates back via a hidden Streamlit text input + JS.
# ─────────────────────────────────────────────────────────────

# Build sidebar content as JSON to pass into the iframe
def build_sidebar_data():
    channels_list = []
    for ch_key, info in st.session_state.channels.items():
        s = info.get("channel_stats", {})
        channels_list.append({
            "key": ch_key,
            "name": s.get("channel_name") or ch_key,
            "subs": fmt(s.get("subscribers", 0)) if s.get("subscribers") else "—",
            "loaded": info.get("data") is not None,
        })
    folders_list = sorted(st.session_state.folders.keys())
    active_folder = st.session_state.active_folder or ""
    time_preset = st.session_state.time_preset
    return json.dumps({
        "channels": channels_list,
        "folders": folders_list,
        "active_folder": active_folder,
        "time_preset": time_preset,
        "time_presets": list(TIME_PRESETS.keys()) + ["Month","Custom"],
    })

sb_data = build_sidebar_data()

# Hidden input to receive commands from the sidebar iframe
cmd_input = st.empty()
with cmd_input:
    raw_cmd = st.text_input("__sidebar_cmd__", value="", key="sb_cmd", label_visibility="collapsed")

# Process command if any
if raw_cmd:
    try:
        cmd = json.loads(raw_cmd)
        action = cmd.get("action","")
        if action == "set_folder":
            st.session_state.active_folder = cmd.get("folder") or None
            st.session_state["sb_cmd"] = ""
            st.rerun()
        elif action == "set_time":
            st.session_state.time_preset = cmd.get("preset","All")
            st.session_state["sb_cmd"] = ""
            st.rerun()
        elif action == "delete_channel":
            key = cmd.get("key","")
            if key and key in st.session_state.channels:
                delete_channel_from_db(key)
                del st.session_state.channels[key]
                st.session_state["sb_cmd"] = ""
                st.rerun()
        elif action == "refresh_all":
            st.session_state["sb_cmd"] = ""
            st.session_state["_do_refresh"] = True
            st.rerun()
        elif action == "add_channel":
            cid = cmd.get("channel_id","").strip()
            if cid and st.session_state.api_key:
                if cid not in [v["id"] for v in st.session_state.channels.values()]:
                    try:
                        ch_name = lookup_channel_name(st.session_state.api_key, cid)
                        if ch_name in st.session_state.channels:
                            ch_name = f"{ch_name} ({cid[-6:]})"
                        st.session_state.channels[ch_name] = {"id":cid,"data":None,"channel_stats":{},"last_refreshed":"Never","notes":"","ideas":{}}
                        save_channel_to_db(ch_name,cid,{},None,"Never")
                        if st.session_state.active_folder:
                            add_channel_to_folder_db(st.session_state.active_folder,ch_name)
                            st.session_state.folders[st.session_state.active_folder].append(ch_name)
                    except Exception:
                        pass
            st.session_state["sb_cmd"] = ""
            st.rerun()
    except Exception:
        pass

# Do refresh if triggered
if st.session_state.get("_do_refresh"):
    st.session_state["_do_refresh"] = False
    af_r = st.session_state.active_folder
    targets = {k:v for k,v in st.session_state.channels.items() if (not af_r or (af_r in st.session_state.folders and k in st.session_state.folders[af_r]))}
    fetch_channel_data.clear()
    prog = st.progress(0, text="Refreshing channels...")
    total = len(targets)
    for i,(ch_key,info) in enumerate(targets.items()):
        try:
            df_new,st_new = fetch_channel_data(st.session_state.api_key, info["id"])
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.channels[ch_key].update({"data":df_new,"channel_stats":st_new,"last_refreshed":ts})
            save_channel_to_db(ch_key,info["id"],st_new,df_new,ts,info.get("notes",""),info.get("ideas",{}))
            prog.progress((i+1)/total, text=f"Done: {st_new.get('channel_name',ch_key)}")
        except Exception as e:
            st.error(f"{ch_key}: {e}")
    prog.empty()
    st.rerun()

# Inject the custom sidebar HTML
components.html(f"""<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#000;--bg2:#080808;--bg3:#0d0d0d;--bg4:#141414;--bg5:#1a1a1a;
  --border:#1e1e1e;--border2:#2a2a2a;
  --text:#e8e8e8;--muted:#555;--dim:#333;
  --red:#ff2244;--blue:#00aaff;--green:#00ff88;--gold:#ffaa00;
  --font:'Inter',sans-serif;--mono:'JetBrains Mono',monospace;
}}
body{{background:transparent;font-family:var(--font);color:var(--text);overflow:hidden}}

/* ── Hamburger button — always fixed in parent page ── */
#ham{{
  position:fixed;top:14px;left:14px;
  width:42px;height:42px;
  background:var(--bg3);border:1px solid var(--border2);border-radius:10px;
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;z-index:2147483647;
  transition:all .2s;
  box-shadow:0 0 0 0 transparent;
}}
#ham:hover{{
  background:var(--red);border-color:var(--red);
  box-shadow:0 0 20px rgba(255,34,68,.4);
}}
#ham svg{{transition:transform .2s}}
#ham.open svg{{transform:rotate(90deg)}}

/* ── Overlay backdrop ── */
#backdrop{{
  display:none;position:fixed;inset:0;
  background:rgba(0,0,0,.7);backdrop-filter:blur(4px);
  z-index:99997;
}}
#backdrop.open{{display:block}}

/* ── Sidebar drawer ── */
#drawer{{
  position:fixed;top:0;left:-320px;width:300px;height:100vh;
  background:var(--bg2);border-right:1px solid var(--border);
  z-index:99998;overflow-y:auto;overflow-x:hidden;
  transition:left .3s cubic-bezier(.4,0,.2,1);
  padding-bottom:40px;
}}
#drawer.open{{left:0;box-shadow:0 0 60px rgba(0,0,0,.8)}}
::-webkit-scrollbar{{width:3px}}
::-webkit-scrollbar-track{{background:var(--bg)}}
::-webkit-scrollbar-thumb{{background:#222;border-radius:3px}}

/* ── Drawer inner ── */
.sb-top{{
  display:flex;align-items:center;gap:10px;
  padding:18px 16px 16px;
  border-bottom:1px solid var(--border);
  position:sticky;top:0;background:var(--bg2);z-index:10;
}}
.sb-logo{{
  width:30px;height:30px;background:var(--red);border-radius:7px;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;font-weight:900;color:#fff;flex-shrink:0;
  box-shadow:0 0 16px rgba(255,34,68,.35);
}}
.sb-title{{font-size:13px;font-weight:700;color:#fff;line-height:1.2}}
.sb-sub{{font-size:9px;color:var(--red);font-weight:600;letter-spacing:1.5px;text-transform:uppercase}}

.sb-section{{padding:14px 16px 0}}
.sb-label{{
  font-family:var(--mono);font-size:8px;font-weight:600;
  color:var(--dim);text-transform:uppercase;letter-spacing:2px;
  margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid var(--border);
}}

/* Time filter chips */
.time-chips{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:2px}}
.t-chip{{
  font-family:var(--mono);font-size:10px;font-weight:600;
  padding:4px 10px;border-radius:5px;cursor:pointer;
  background:var(--bg4);border:1px solid var(--border2);
  color:var(--muted);transition:all .15s;
}}
.t-chip:hover{{color:var(--text);border-color:#333}}
.t-chip.active{{
  background:rgba(255,34,68,.12);border-color:rgba(255,34,68,.35);
  color:var(--red);box-shadow:0 0 10px rgba(255,34,68,.15);
}}

/* Folder buttons */
.folder-btn{{
  display:flex;align-items:center;gap:8px;width:100%;
  padding:8px 10px;border-radius:7px;cursor:pointer;
  border:1px solid transparent;transition:all .15s;
  background:transparent;color:var(--muted);
  font-family:var(--font);font-size:12px;font-weight:500;
  margin-bottom:3px;text-align:left;
}}
.folder-btn:hover{{background:var(--bg4);color:var(--text);border-color:var(--border2)}}
.folder-btn.active{{
  background:rgba(255,34,68,.08);border-color:rgba(255,34,68,.25);
  color:#fff;box-shadow:0 0 12px rgba(255,34,68,.08);
}}
.folder-dot{{width:6px;height:6px;border-radius:50%;background:var(--dim);flex-shrink:0;transition:background .15s}}
.folder-btn.active .folder-dot{{background:var(--red);box-shadow:0 0 6px var(--red)}}

/* Channel pills */
.ch-pill{{
  display:flex;align-items:center;gap:8px;
  padding:8px 10px;border-radius:7px;
  background:var(--bg3);border:1px solid var(--border);
  margin-bottom:4px;transition:border-color .15s;
}}
.ch-pill:hover{{border-color:var(--border2)}}
.ch-status{{width:6px;height:6px;border-radius:50%;flex-shrink:0}}
.ch-status.loaded{{background:var(--green);box-shadow:0 0 6px var(--green)}}
.ch-status.empty{{background:var(--dim)}}
.ch-info{{flex:1;min-width:0}}
.ch-name{{font-size:12px;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.ch-subs{{font-size:9px;color:var(--muted);font-family:var(--mono)}}
.ch-del{{
  font-size:11px;color:var(--dim);background:none;border:none;
  cursor:pointer;padding:2px 5px;border-radius:3px;transition:all .15s;flex-shrink:0;
}}
.ch-del:hover{{color:var(--red);background:rgba(255,34,68,.12)}}

/* Add channel form */
.add-form{{margin-top:8px;display:none}}
.add-form.open{{display:block}}
.add-input{{
  width:100%;background:var(--bg4);border:1px solid var(--border2);
  border-radius:6px;color:var(--text);font-family:var(--mono);
  font-size:11px;padding:7px 10px;margin-bottom:6px;outline:none;
}}
.add-input:focus{{border-color:var(--red);box-shadow:0 0 0 2px rgba(255,34,68,.2)}}
.add-btn{{
  width:100%;padding:7px;border-radius:6px;border:none;cursor:pointer;
  background:var(--red);color:#fff;font-family:var(--font);
  font-size:12px;font-weight:600;transition:all .2s;
  box-shadow:0 0 12px rgba(255,34,68,.25);
}}
.add-btn:hover{{box-shadow:0 0 20px rgba(255,34,68,.45)}}

/* Refresh button */
.refresh-btn{{
  display:flex;align-items:center;justify-content:center;gap:7px;
  width:calc(100% - 32px);margin:12px 16px 0;
  padding:10px;border-radius:8px;border:1px solid rgba(255,34,68,.25);
  background:rgba(255,34,68,.06);color:var(--red);
  font-family:var(--font);font-size:12px;font-weight:600;
  cursor:pointer;transition:all .2s;letter-spacing:.2px;
}}
.refresh-btn:hover{{
  background:rgba(255,34,68,.12);border-color:rgba(255,34,68,.4);
  box-shadow:0 0 20px rgba(255,34,68,.15);
}}

.toggle-add{{
  display:flex;align-items:center;gap:6px;
  font-size:11px;color:var(--muted);cursor:pointer;
  padding:4px 0;transition:color .15s;margin-bottom:4px;
  background:none;border:none;font-family:var(--font);
}}
.toggle-add:hover{{color:var(--text)}}
</style>
</head><body>

<!-- Always-visible hamburger -->
<div id="ham" onclick="toggleDrawer()">
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect y="3" width="18" height="1.5" rx=".75" fill="#e8e8e8"/>
    <rect y="8.25" width="18" height="1.5" rx=".75" fill="#e8e8e8"/>
    <rect y="13.5" width="18" height="1.5" rx=".75" fill="#e8e8e8"/>
  </svg>
</div>

<!-- Backdrop -->
<div id="backdrop" onclick="closeDrawer()"></div>

<!-- Sidebar drawer -->
<div id="drawer">
  <div class="sb-top">
    <div class="sb-logo">▶</div>
    <div>
      <div class="sb-title">Chamberlin</div>
      <div class="sb-sub">Media Monitor</div>
    </div>
  </div>

  <!-- Time filter -->
  <div class="sb-section">
    <div class="sb-label">Time Filter</div>
    <div class="time-chips" id="time-chips"></div>
  </div>

  <!-- Folders -->
  <div class="sb-section" id="folders-section" style="margin-top:14px"></div>

  <!-- Channels -->
  <div class="sb-section" style="margin-top:14px">
    <div class="sb-label">Channels</div>
    <div id="channel-list"></div>
    <button class="toggle-add" onclick="toggleAdd()">＋ Add channel</button>
    <div class="add-form" id="add-form">
      <input class="add-input" id="add-input" placeholder="Channel ID  (UCxxxxxxxx)" />
      <button class="add-btn" onclick="submitAdd()">Add Channel</button>
    </div>
  </div>

  <!-- Refresh -->
  <button class="refresh-btn" onclick="sendCmd({{action:'refresh_all'}})">
    ↺  Refresh All Channels
  </button>
</div>

<script>
const DATA = {sb_data};

function toggleDrawer(){{
  const d=document.getElementById('drawer');
  const b=document.getElementById('backdrop');
  const h=document.getElementById('ham');
  const open=d.classList.toggle('open');
  b.classList.toggle('open',open);
  h.classList.toggle('open',open);
}}
function closeDrawer(){{
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('backdrop').classList.remove('open');
  document.getElementById('ham').classList.remove('open');
}}

// Send command to Streamlit via the hidden input
function sendCmd(obj){{
  const val = JSON.stringify(obj);
  // Find the hidden input in the parent Streamlit page
  const inputs = window.parent.document.querySelectorAll('input[type="text"]');
  for(const inp of inputs){{
    if(inp.closest('[data-testid="stTextInput"]') || inp.placeholder === '' || inp.value === ''){{
      // Use React's synthetic event system
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
      nativeInputValueSetter.call(inp, val);
      inp.dispatchEvent(new Event('input', {{bubbles:true}}));
      break;
    }}
  }}
  closeDrawer();
}}

function toggleAdd(){{
  const f=document.getElementById('add-form');
  f.classList.toggle('open');
  if(f.classList.contains('open')) document.getElementById('add-input').focus();
}}

function submitAdd(){{
  const cid=document.getElementById('add-input').value.trim();
  if(cid) sendCmd({{action:'add_channel',channel_id:cid}});
}}
document.getElementById('add-input').addEventListener('keydown',e=>{{
  if(e.key==='Enter') submitAdd();
}});

// Render time chips
const timeChips=document.getElementById('time-chips');
DATA.time_presets.forEach(p=>{{
  const c=document.createElement('div');
  c.className='t-chip'+(p===DATA.time_preset?' active':'');
  c.textContent=p;
  c.onclick=()=>sendCmd({{action:'set_time',preset:p}});
  timeChips.appendChild(c);
}});

// Render folders
const fSec=document.getElementById('folders-section');
if(DATA.folders.length>0){{
  const lbl=document.createElement('div');
  lbl.className='sb-label';lbl.textContent='Client Folders';
  fSec.appendChild(lbl);
  ['All Channels',...DATA.folders].forEach(f=>{{
    const btn=document.createElement('button');
    btn.className='folder-btn'+(( (f==='All Channels'&&!DATA.active_folder)||(f===DATA.active_folder))?' active':'');
    const dot=document.createElement('span');
    dot.className='folder-dot';
    btn.appendChild(dot);
    btn.appendChild(document.createTextNode(f));
    btn.onclick=()=>sendCmd({{action:'set_folder',folder:f==='All Channels'?'':f}});
    fSec.appendChild(btn);
  }});
}}

// Render channels
const chList=document.getElementById('channel-list');
DATA.channels.forEach(ch=>{{
  const pill=document.createElement('div');
  pill.className='ch-pill';
  const status=document.createElement('span');
  status.className='ch-status '+(ch.loaded?'loaded':'empty');
  const info=document.createElement('div');
  info.className='ch-info';
  const name=document.createElement('div');
  name.className='ch-name';name.textContent=ch.name;name.title=ch.key;
  const subs=document.createElement('div');
  subs.className='ch-subs';subs.textContent=ch.subs+' subs';
  info.appendChild(name);info.appendChild(subs);
  const del=document.createElement('button');
  del.className='ch-del';del.textContent='✕';
  del.onclick=(e)=>{{e.stopPropagation();sendCmd({{action:'delete_channel',key:ch.key}})}};
  pill.appendChild(status);pill.appendChild(info);pill.appendChild(del);
  chList.appendChild(pill);
}});
</script>
</body></html>""", height=0)

# ─────────────────────────────────────────────────────────────
# GUARD
# ─────────────────────────────────────────────────────────────
if not st.session_state.api_key:
    st.markdown("""<div style="max-width:440px;margin:100px auto;text-align:center">
        <div style="font-size:40px;margin-bottom:14px">▶</div>
        <h2 style="font-size:20px;font-weight:700;color:#fff;margin-bottom:8px">Chamberlin Media Monitor</h2>
        <p style="color:#444;font-size:13px">API key not configured. Set YOUTUBE_API_KEY in your environment variables.</p>
    </div>""", unsafe_allow_html=True)
    st.stop()

if not st.session_state.channels:
    st.markdown("""<div style="max-width:440px;margin:100px auto;text-align:center">
        <div style="font-size:40px;margin-bottom:14px">📡</div>
        <h2 style="font-size:20px;font-weight:600;color:#fff;margin-bottom:8px">No channels yet</h2>
        <p style="color:#444;font-size:13px">Open the ☰ menu and add a YouTube channel ID.</p>
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

active_filter_label = st.session_state.time_preset

# Filter banner
if st.session_state.time_preset != "All":
    st.markdown(f"""<div style="background:rgba(255,34,68,.05);border:1px solid rgba(255,34,68,.15);
        border-radius:8px;padding:6px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px">
        <span style="font-size:10px;color:#ff2244;font-family:monospace;font-weight:700">● FILTERED</span>
        <span style="font-size:12px;color:#888">{active_filter_label}</span>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# MAIN TABS  — leave space for hamburger at top-left
# ─────────────────────────────────────────────────────────────
st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
T_DASH, T_ALL, T_DETAIL = st.tabs(["  Dashboard  ","  All Channels  ","  Channel Detail  "])

# ═══════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════
with T_DASH:
    _title = f"Dashboard — {_af}" if _af else "Dashboard"
    _sub   = f"{len(view_channels)} channels" + (f" · {_af}" if _af else "")
    st.markdown(f'<h1 style="margin-bottom:2px;padding-left:54px">{_title}</h1><p style="color:#444;font-size:11px;margin-bottom:20px;padding-left:54px">{_sub}</p>', unsafe_allow_html=True)

    total_subs  = sum(v.get("channel_stats",{}).get("subscribers",0) for v in view_channels.values())
    total_views = sum(v.get("channel_stats",{}).get("total_views",0)  for v in view_channels.values())
    loaded      = sum(1 for v in view_channels.values() if v.get("data") is not None)
    total_rev   = sum(int(info.get("data")["Views"].sum())*3.5/1000 for info in view_channels.values() if info.get("data") is not None and not info.get("data").empty)

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
            <div class="yt-bubble-value">{fmt_usd(total_rev)}</div>
            <div class="yt-bubble-sub">~$3.50 RPM</div>
        </div>
        <div class="yt-bubble yt-bubble-green">
            <div class="yt-bubble-label">Channels</div>
            <div class="yt-bubble-value">{len(view_channels)}</div>
            <div class="yt-bubble-sub">{loaded} loaded</div>
        </div>
    </div>''', unsafe_allow_html=True)

    # ── OUTLIER TRACKER ───────────────────────────────────────
    st.markdown('<div class="section-label">⚡  Outlier Tracker — Old Videos Spiking</div>', unsafe_allow_html=True)
    outliers = detect_outliers(st.session_state.channels)
    if outliers:
        for o in outliers:
            thu=_h.escape(o["thumbnail"]); url=_h.escape(o["url"]); tit=_h.escape(o["title"])
            thumb_el=(f'<img src="{thu}" class="outlier-thumb" loading="lazy">' if thu else '<div class="outlier-thumb-ph">▶</div>')
            st.markdown(f"""<div class="outlier-card">
              <a href="{url}" target="_blank" style="text-decoration:none">{thumb_el}</a>
              <div class="outlier-body">
                <div class="outlier-badge">⚡ {o['ratio']:.1f}x above median</div>
                <div class="outlier-title" title="{tit}">{tit}</div>
                <div class="outlier-ch">{_h.escape(o['ch_display'])}</div>
                <div class="outlier-stats">
                  <div class="o-stat">Views <span>{fmt(o['views'])}</span></div>
                  <div class="o-stat">V/Day <span>{o['vpd']:.0f}</span></div>
                  <div class="o-stat">Age <span>{o['days']}d</span></div>
                  <div class="o-stat">Like% <span>{o['lr']:.2f}%</span></div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert alert-info"><div class="alert-icon">📊</div><div class="alert-body"><div class="alert-title">No outliers yet</div><div class="alert-desc">Refresh channels — outliers appear when a 30+ day old video pulls 2× the channel median views/day.</div></div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Revenue table
    rev_rows=[]
    for ch_name,info in view_channels.items():
        df_r=info.get("data"); s=info.get("channel_stats",{})
        if df_r is not None and not df_r.empty:
            tv=int(df_r["Views"].sum())
            rev_rows.append({"Channel":s.get("channel_name",ch_name),"Total Views":tv,"Low ($1.5)":fmt_usd(tv*1.5/1000),"Mid ($3.5)":fmt_usd(tv*3.5/1000),"High ($5)":fmt_usd(tv*5.0/1000)})
    if rev_rows:
        st.markdown('<div class="section-label">Estimated Revenue by Channel</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(rev_rows), use_container_width=True, hide_index=True)
        st.caption("⚠️ Estimates only — actual revenue varies by niche and monetization.")
        st.markdown("<br>", unsafe_allow_html=True)

    # Top videos by momentum
    all_rows=[]
    for ch_name,info in view_channels.items():
        df=get_filtered_df(info)
        if df is not None and not df.empty:
            top=df.nlargest(8,"Views per Day").copy(); top["Channel"]=ch_name; all_rows.append(top)
    if all_rows:
        combined=pd.concat(all_rows).nlargest(12,"Views per Day").reset_index(drop=True)
        st.markdown('<div class="section-label">Top Videos by Momentum</div>', unsafe_allow_html=True)
        render_thumb_table(combined, show_channel=True)
        st.markdown("<br>", unsafe_allow_html=True)
        all_full=pd.concat(all_rows)
        qw=all_full[all_full["Comment Rate %"]>all_full["Comment Rate %"].quantile(0.7)].nsmallest(4,"Views")
        if not qw.empty:
            st.markdown('<div class="section-label">Quick Wins — High Engagement, Low Reach</div>', unsafe_allow_html=True)
            for _,row in qw.iterrows():
                st.markdown(f"""<div class="alert alert-warn"><div class="alert-icon">💡</div>
                    <div class="alert-body"><div class="alert-title">{row.get('Channel','')} — {str(row['Title'])[:70]}</div>
                    <div class="alert-desc">{row['Comment Rate %']:.2f}% comment rate · {fmt(row['Views'])} views</div>
                    </div></div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert alert-info"><div class="alert-icon">ℹ️</div><div class="alert-body"><div class="alert-title">No data for this period</div><div class="alert-desc">Try a wider time range or refresh channels.</div></div></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════
# ALL CHANNELS
# ═══════════════════════════════════════════
with T_ALL:
    st.markdown('<h1 style="margin-bottom:2px;padding-left:54px">All Channels</h1><p style="color:#444;font-size:11px;margin-bottom:20px;padding-left:54px">Portfolio overview</p>', unsafe_allow_html=True)
    rows=[]
    for ch_key,info in view_channels.items():
        df=get_filtered_df(info); s=info.get("channel_stats",{})
        tv=int(df["Views"].sum()) if df is not None and not df.empty else 0
        rows.append({"Channel":s.get("channel_name",ch_key),"Subscribers":s.get("subscribers",0),"Total Views":s.get("total_views",0),"Videos (Period)":len(df) if df is not None and not df.empty else 0,"Avg Views":int(df["Views"].mean()) if df is not None and not df.empty else 0,"Avg V/Day":round(df["Views per Day"].mean(),1) if df is not None and not df.empty else 0,"Est Revenue":fmt_usd(tv*3.5/1000),"Last Refreshed":info.get("last_refreshed","Never")})
    if rows:
        sdf=pd.DataFrame(rows).sort_values("Total Views",ascending=False)
        disp=sdf.copy()
        disp["Subscribers"]=disp["Subscribers"].apply(fmt)
        disp["Total Views"]=disp["Total Views"].apply(fmt)
        disp["Avg Views"]=disp["Avg Views"].apply(fmt)
        st.dataframe(disp,use_container_width=True,hide_index=True)
        st.download_button("⬇  Export CSV",sdf.to_csv(index=False).encode(),"chamberlin_channels.csv","text/csv")
        if len(rows)>1:
            st.markdown("<br>",unsafe_allow_html=True)
            fig_s=px.bar(sdf,x="Channel",y="Subscribers",title="Subscribers by Channel",color="Subscribers",color_continuous_scale=["#1a0008","#ff2244"])
            fig_s.update_layout(**PLOTLY,showlegend=False,height=280); fig_s.update_traces(marker_line_width=0); fig_s.update_xaxes(tickangle=-30)
            st.plotly_chart(fig_s,use_container_width=True,config=plotly_cfg())
            fig_v=px.bar(sdf,x="Channel",y="Avg V/Day",title="Avg Views/Day by Channel",color="Avg V/Day",color_continuous_scale=["#000d1a","#00aaff"])
            fig_v.update_layout(**PLOTLY,showlegend=False,height=280); fig_v.update_traces(marker_line_width=0); fig_v.update_xaxes(tickangle=-30)
            st.plotly_chart(fig_v,use_container_width=True,config=plotly_cfg())

# ═══════════════════════════════════════════
# CHANNEL DETAIL
# ═══════════════════════════════════════════
with T_DETAIL:
    selected=st.selectbox("Channel",list(view_channels.keys()) if view_channels else list(st.session_state.channels.keys()),label_visibility="collapsed")
    info=st.session_state.channels[selected]
    stats=info.get("channel_stats",{})
    ch_df_raw=info.get("data"); ch_df=get_filtered_df(info)

    head_l,head_r=st.columns([5,2])
    with head_l:
        st.markdown(f'<h1 style="padding-left:54px">{stats.get("channel_name",selected)}</h1><p style="color:#444;font-size:10px;font-family:monospace;padding-left:54px">{info["id"]} · {info.get("last_refreshed","Never")}</p>', unsafe_allow_html=True)
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
                except Exception as e: st.error(str(e))
        st.markdown('</div>',unsafe_allow_html=True)

    st.divider()

    if ch_df_raw is None or ch_df_raw.empty:
        st.markdown('<div class="alert alert-info"><div class="alert-icon">ℹ️</div><div class="alert-body"><div class="alert-title">No data loaded</div><div class="alert-desc">Click Refresh to load video data.</div></div></div>',unsafe_allow_html=True)
        st.stop()

    working_df = ch_df if (ch_df is not None and not ch_df.empty) else ch_df_raw
    if ch_df is not None and ch_df.empty and st.session_state.time_preset!="All":
        st.markdown('<div class="alert alert-warn"><div class="alert-icon">⚠️</div><div class="alert-body"><div class="alert-title">No videos in this period</div><div class="alert-desc">Showing all-time data.</div></div></div>',unsafe_allow_html=True)

    avg_views=int(working_df["Views"].mean()); total_views_ch=int(working_df["Views"].sum())
    avg_lr=working_df["Like Rate %"].mean(); avg_cr=working_df["Comment Rate %"].mean()
    rev_str=f"{fmt_usd(total_views_ch*1.5/1000)}–{fmt_usd(total_views_ch*5.0/1000)}"

    bubble_defs=[
        ("subscribers","Subscribers",fmt(stats.get("subscribers",0)),"total subs","yt-bubble-red"),
        ("views","Views",fmt(total_views_ch),"in period","yt-bubble-blue"),
        ("avg_views","Avg Views",fmt(avg_views),"per video","yt-bubble-green"),
        ("revenue","Est Revenue",rev_str,"$1.5–$5 RPM","yt-bubble-gold"),
        ("engagement","Like Rate",f"{avg_lr:.2f}%",f"cmt {avg_cr:.2f}%","yt-bubble-grey"),
        ("videos","Videos",str(len(working_df)),"in period","yt-bubble-grey"),
    ]
    bhtml='<div class="yt-bubble-row">'
    for key,label,value,sub,cls in bubble_defs:
        ac="yt-bubble-active" if st.session_state.bubble_chart==key else ""
        bhtml+=f'<div class="yt-bubble {cls} {ac}"><div class="yt-bubble-label">{label}</div><div class="yt-bubble-value" style="font-size:18px">{value}</div><div class="yt-bubble-sub">{sub}</div></div>'
    bhtml+='</div>'
    st.markdown(bhtml,unsafe_allow_html=True)

    bc=st.columns(6)
    for i,(key,label,_,_,_) in enumerate(bubble_defs):
        if bc[i].button("↗",key=f"bub_{selected}_{key}",use_container_width=True,help=label):
            st.session_state.bubble_chart=None if st.session_state.bubble_chart==key else key; st.rerun()

    bc_sel=st.session_state.bubble_chart
    if bc_sel=="views":
        vt=working_df.sort_values("Published")
        fv=go.Figure()
        fv.add_trace(go.Scatter(x=vt["Published"],y=vt["Views"].cumsum(),mode="lines",line=dict(color="#00aaff",width=2),fill="tozeroy",fillcolor="rgba(0,170,255,.04)",name="Cumulative"))
        fv.add_trace(go.Bar(x=vt["Published"],y=vt["Views"],marker_color="rgba(0,170,255,.25)",marker_line_width=0,name="Per Video"))
        fv.update_layout(**PLOTLY,title="Views Over Time",height=300); st.plotly_chart(fv,use_container_width=True,config=plotly_cfg())
    elif bc_sel=="avg_views":
        fh=go.Figure(); fh.add_trace(go.Histogram(x=working_df["Views"],nbinsx=20,marker_color="#ff2244",marker_line_width=0,opacity=.7))
        fh.add_vline(x=avg_views,line_dash="dash",line_color="#666",annotation_text=f"Avg: {fmt(avg_views)}")
        fh.update_layout(**PLOTLY,title="Views Distribution",height=280); st.plotly_chart(fh,use_container_width=True,config=plotly_cfg())
    elif bc_sel=="revenue":
        rc=working_df.nlargest(15,"Views").copy(); rc["Mid"]=(rc["Views"]*3.5/1000).round(0); rc=rc.sort_values("Mid"); rc["L"]=rc["Title"].str[:45]
        fr=go.Figure(go.Bar(x=rc["Mid"],y=rc["L"],orientation="h",marker=dict(color=rc["Mid"].tolist(),colorscale=[[0,"#0d0800"],[1,"#ffaa00"]],showscale=False),text=[f"${v:,.0f}" for v in rc["Mid"]],textposition="outside",textfont=dict(size=9,color="#555")))
        fr.update_layout(**_pb(),title="Est Revenue — Top 15 ($3.50 RPM)",height=max(280,len(rc)*32),showlegend=False,margin=dict(l=10,r=70,t=40,b=10),xaxis=dict(visible=False,gridcolor="#0d0d0d"),yaxis=dict(tickfont=dict(size=9,color="#555"),automargin=True))
        st.plotly_chart(fr,use_container_width=True,config=plotly_cfg()); st.caption("⚠️ Estimates only.")
    elif bc_sel=="engagement":
        fe=px.scatter(working_df,x="Views",y="Like Rate %",hover_name="Title",color="Like Rate %",color_continuous_scale=[[0,"#1a0008"],[1,"#ff2244"]],title="Like Rate vs Views")
        fe.update_layout(**PLOTLY,height=260); st.plotly_chart(fe,use_container_width=True,config=plotly_cfg())
    elif bc_sel=="videos":
        m2=working_df.copy(); m2["Month"]=m2["Published"].dt.to_period("M").astype(str)
        cad=m2.groupby("Month").agg(Count=("Title","count"),TV=("Views","sum")).reset_index()
        fc=go.Figure()
        fc.add_trace(go.Bar(x=cad["Month"],y=cad["Count"],name="Videos",marker_color="#1a1a1a",marker_line_width=0))
        fc.add_trace(go.Scatter(x=cad["Month"],y=cad["TV"],name="Views",yaxis="y2",line=dict(color="#ff2244",width=2),marker=dict(size=5,color="#ff2244")))
        P2={k:v for k,v in PLOTLY.items() if k not in ("xaxis","yaxis")}
        fc.update_layout(**P2,title="Upload Cadence",xaxis=dict(tickangle=-30,tickfont=dict(size=9,color="#555"),automargin=True,gridcolor="#0d0d0d"),yaxis2=dict(overlaying="y",side="right",color="#555"),legend=dict(orientation="h",y=1.1),height=300)
        st.plotly_chart(fc,use_container_width=True,config=plotly_cfg())

    st.markdown("<br>",unsafe_allow_html=True)
    DT1,DT2,DT3,DT4,DT5=st.tabs(["  Videos  ","  Charts  ","  Upload Timing  ","  Content Series  ","  Notes  "])

    with DT1:
        sb=st.selectbox("Sort",["Views","Views per Day","Like Rate %","Comment Rate %","Published"],label_visibility="collapsed")
        sd=working_df.sort_values(sb,ascending=(sb=="Published")).reset_index(drop=True)
        pk=f"vp_{selected}"; sk=f"vs_{selected}"
        if pk not in st.session_state: st.session_state[pk]=0
        if st.session_state.get(sk)!=sb: st.session_state[pk]=0; st.session_state[sk]=sb
        pp=20; tp=max(1,(len(sd)+pp-1)//pp); pg=st.session_state[pk]
        render_thumb_table(sd.iloc[pg*pp:(pg+1)*pp].reset_index(drop=True))
        pc=st.columns([1,1,4,1,1])
        if pc[0].button("⟨⟨",key=f"f_{selected}",disabled=pg==0): st.session_state[pk]=0; st.rerun()
        if pc[1].button("⟨",key=f"p_{selected}",disabled=pg==0): st.session_state[pk]-=1; st.rerun()
        pc[2].markdown(f'<p style="text-align:center;color:#444;font-size:11px;padding-top:8px">Page {pg+1}/{tp} — {len(sd)} videos</p>',unsafe_allow_html=True)
        if pc[3].button("⟩",key=f"n_{selected}",disabled=pg>=tp-1): st.session_state[pk]+=1; st.rerun()
        if pc[4].button("⟩⟩",key=f"l_{selected}",disabled=pg>=tp-1): st.session_state[pk]=tp-1; st.rerun()
        st.markdown("<br>",unsafe_allow_html=True)
        st.download_button("⬇  Export CSV",working_df.to_csv(index=False).encode(),f"{selected.replace(' ','_')}.csv","text/csv")

    with DT2:
        st.plotly_chart(chart_top_views(working_df),use_container_width=True,config=plotly_cfg())
        st.plotly_chart(chart_top_momentum(working_df),use_container_width=True,config=plotly_cfg())
        tr=working_df.sort_values("Published")
        f3=go.Figure(); f3.add_trace(go.Scatter(x=tr["Published"],y=tr["Views"],mode="lines+markers",line=dict(color="#ff2244",width=2),marker=dict(color="#ff2244",size=4),fill="tozeroy",fillcolor="rgba(255,34,68,.04)"))
        f3.update_layout(**PLOTLY,title="Views Per Video Over Time",height=240); st.plotly_chart(f3,use_container_width=True,config=plotly_cfg())
        fl=go.Figure(); fl.add_trace(go.Bar(x=tr["Published"],y=tr["Likes"],marker_color="#ff2244",marker_line_width=0))
        fl.update_layout(**PLOTLY,title="Likes Per Video",height=200); st.plotly_chart(fl,use_container_width=True,config=plotly_cfg())
        fcm=go.Figure(); fcm.add_trace(go.Bar(x=tr["Published"],y=tr["Comments"],marker_color="#00aaff",marker_line_width=0))
        fcm.update_layout(**PLOTLY,title="Comments Per Video",height=200); st.plotly_chart(fcm,use_container_width=True,config=plotly_cfg())
        fe2=px.scatter(working_df,x="Views",y="Like Rate %",size="Comments",color="Comment Rate %",hover_name="Title",title="Engagement Map",color_continuous_scale=[[0,"#1a0008"],[1,"#ff2244"]])
        fe2.update_layout(**PLOTLY,height=280); st.plotly_chart(fe2,use_container_width=True,config=plotly_cfg())
        fd=px.scatter(working_df,x="Days Since Publish",y="Views per Day",hover_name="Title",color="Views",color_continuous_scale=[[0,"#080808"],[1,"#00ff88"]],title="Evergreen Detector")
        fd.update_layout(**PLOTLY,height=280,xaxis_title="Days Since Published",yaxis_title="V/Day"); st.plotly_chart(fd,use_container_width=True,config=plotly_cfg())
        st.caption("Videos above trend at high age = evergreen worth promoting.")
        rc2=working_df.nlargest(15,"Views").copy(); rc2["Rev"]=(rc2["Views"]*3.5/1000).round(0); rc2=rc2.sort_values("Rev"); rc2["L"]=rc2["Title"].str[:45]
        frv=go.Figure(go.Bar(x=rc2["Rev"],y=rc2["L"],orientation="h",marker=dict(color=rc2["Rev"].tolist(),colorscale=[[0,"#0d0800"],[1,"#ffaa00"]],showscale=False),text=[f"${v:,.0f}" for v in rc2["Rev"]],textposition="outside",textfont=dict(size=9,color="#555")))
        frv.update_layout(**_pb(),title="Est Revenue — Top 15 ($3.50 RPM)",height=max(280,len(rc2)*32),showlegend=False,margin=dict(l=10,r=70,t=40,b=10),xaxis=dict(visible=False,gridcolor="#0d0d0d"),yaxis=dict(tickfont=dict(size=9,color="#555"),automargin=True))
        st.plotly_chart(frv,use_container_width=True,config=plotly_cfg()); st.caption("⚠️ Revenue estimates use $3.50 RPM.")

    with DT3:
        day_order=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        tmp=working_df.copy(); tmp["Day"]=tmp["Published"].dt.day_name()
        da=tmp.groupby("Day")["Views"].mean().reindex(day_order).dropna()
        if not da.empty:
            bd=da.idxmax(); ba=da.max()
            st.markdown(f"""<div class="best-day"><div style="font-size:22px">📅</div><div>
              <div class="best-day-label">Best Day to Upload</div>
              <div class="best-day-value">{bd}</div>
              <div class="best-day-sub">Avg {fmt(int(ba))} views</div>
            </div></div>""",unsafe_allow_html=True)
            fbd=px.bar(x=da.index,y=da.values,title="Avg Views by Upload Day",labels={"x":"","y":"Avg Views"},color=da.values,color_continuous_scale=[[0,"#1a0008"],[1,"#ff2244"]])
            fbd.update_layout(**PLOTLY,showlegend=False,height=240); fbd.update_traces(marker_line_width=0); st.plotly_chart(fbd,use_container_width=True,config=plotly_cfg())
        mn=working_df.copy(); mn["Month"]=mn["Published"].dt.to_period("M").astype(str)
        fr2=mn.groupby("Month").agg(Videos=("Title","count"),Avg=("Views","mean")).reset_index(); fr2["Avg"]=fr2["Avg"].round(0).astype(int)
        fff=px.bar(fr2,x="Month",y="Videos",title="Videos per Month",labels={"Videos":"Videos","Month":""}); fff.update_traces(marker_color="#1a1a1a",marker_line_width=0); fff.update_layout(**PLOTLY,height=220); fff.update_xaxes(tickangle=-40,tickfont=dict(size=9)); st.plotly_chart(fff,use_container_width=True,config=plotly_cfg())
        fav=px.line(fr2,x="Month",y="Avg",title="Avg Views per Month",labels={"Avg":"Avg Views","Month":""},markers=True); fav.update_traces(line_color="#ff2244",marker_color="#ff2244",marker_size=5); fav.update_layout(**PLOTLY,height=220); fav.update_xaxes(tickangle=-40,tickfont=dict(size=9)); st.plotly_chart(fav,use_container_width=True,config=plotly_cfg())

    with DT4:
        st.markdown('<div class="section-label">Topic Analysis</div>',unsafe_allow_html=True)
        titles=working_df["Title"].tolist(); wa=[]
        for t in titles: wa.extend(re.findall(r"\b[A-Za-z]{3,}\b",t))
        stop={"this","that","with","from","have","what","your","they","their","will","more","just","been","like","also","when","then","than","about","which","there","after","video","youtube","channel","episode","part","feat","official","full","new","the","and","for","are","but","not","you","all","can","her","was","one","our","out","day","get","has","him","his","how","its","let","may","now","old","own","see","two","way","who","boy","did","use"}
        filt=[w.lower() for w in wa if w.lower() not in stop and len(w)>3]
        tw=Counter(filt).most_common(20)
        if tw:
            th='<div class="tags">'
            for word,count in tw[:14]:
                mask=working_df["Title"].str.contains(word,case=False,na=False)
                av=int(working_df.loc[mask,"Views"].mean()) if mask.any() else 0
                cls="tag tag-hot" if av>working_df["Views"].mean() else "tag"
                th+=f'<span class="{cls}">{word} ({count})</span>'
            th+='</div>'
            st.markdown(th,unsafe_allow_html=True)
            st.caption("🔴 Red = above-average views for keyword")
        phr=[]
        for t in titles:
            ws=re.findall(r"\b[A-Za-z]{3,}\b",t)
            phr.extend([f"{ws[i]} {ws[i+1]}" for i in range(len(ws)-1)])
        sp={"and the","in the","on the","of the","to the","is a","it is","with the","for the","how to","that is","this is","you are"}
        ph=[p.lower() for p in phr if p.lower() not in sp]
        pc2=Counter(ph).most_common(12)
        if pc2:
            pdf=pd.DataFrame(pc2,columns=["Phrase","Count"])
            pdf["Avg Views"]=pdf["Phrase"].apply(lambda p: int(working_df.loc[working_df["Title"].str.contains(p,case=False,na=False),"Views"].mean()) if working_df["Title"].str.contains(p,case=False,na=False).any() else 0)
            pdf=pdf.sort_values("Avg Views",ascending=False)
            fps=px.scatter(pdf,x="Count",y="Avg Views",text="Phrase",title="Topic Frequency vs Avg Views",color="Avg Views",color_continuous_scale=[[0,"#1a0008"],[1,"#ff2244"]],size="Count")
            fps.update_traces(textposition="top center",textfont=dict(size=9,color="#888"))
            fps.update_layout(**PLOTLY,height=340); st.plotly_chart(fps,use_container_width=True,config=plotly_cfg())
            st.dataframe(pdf,use_container_width=True,hide_index=True)

    with DT5:
        st.markdown('<div class="section-label">Team Notes</div>',unsafe_allow_html=True)
        nn=st.text_area("Notes",value=info.get("notes",""),height=200,placeholder="Observations, strategy, action items...",label_visibility="collapsed")
        if st.button("💾  Save Notes",type="primary"):
            st.session_state.channels[selected]["notes"]=nn
            save_channel_to_db(selected,info["id"],stats,ch_df_raw,info.get("last_refreshed",""),nn,info.get("ideas",{}))
            st.success("Saved.")

st.markdown("<br><br>",unsafe_allow_html=True)
st.divider()
st.markdown('<p style="color:#222;font-size:10px;font-family:monospace">Chamberlin Media Monitor  ·  YouTube Data API v3</p>',unsafe_allow_html=True)
