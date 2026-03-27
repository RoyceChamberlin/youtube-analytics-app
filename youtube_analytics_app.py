"""
Chamberlin Media Monitor
Streamlit Cloud-ready • YouTube Data API v3 • Claude AI
"""

import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re
import json
import os
import time
import anthropic
from datetime import datetime, timedelta
import sqlite3
import contextlib

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chamberlin Media Monitor",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# DESIGN SYSTEM
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

:root {
    --bg:           #0a0a0a;
    --bg-2:         #111111;
    --bg-3:         #181818;
    --bg-4:         #1f1f1f;
    --border:       #252525;
    --border-2:     #2e2e2e;
    --text:         #e8e8e8;
    --text-muted:   #737373;
    --text-dim:     #4a4a4a;
    --red:          #ff0033;
    --red-dim:      #8b0000;
    --red-glow:     rgba(255,0,51,0.15);
    --blue:         #1e8fff;
    --green:        #1db954;
    --yellow:       #f5a623;
    --font:         'Instrument Sans', sans-serif;
    --font-mono:    'JetBrains Mono', monospace;
    --radius:       10px;
    --radius-sm:    6px;
}

html, body, [class*="css"] {
    font-family: var(--font);
    background-color: var(--bg) !important;
    color: var(--text);
}

.stApp { background: var(--bg) !important; }
.main .block-container { padding: 2rem 2.5rem 4rem !important; max-width: 1400px; }

[data-testid="stSidebar"] {
    background: var(--bg-2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }
[data-testid="stSidebar"] .block-container { padding: 1.5rem 1.2rem 2rem !important; }

h1 { font-family: var(--font); font-weight: 700; font-size: 22px; letter-spacing: -0.3px; color: #fff !important; margin: 0 !important; padding: 0 !important; }
h2 { font-family: var(--font); font-weight: 600; font-size: 17px; color: #fff !important; margin-bottom: 4px !important; }
h3 { font-family: var(--font); font-weight: 500; font-size: 14px; color: var(--text-muted) !important; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 12px !important; }
p, li { font-size: 14px; line-height: 1.6; }

[data-testid="metric-container"] {
    background: var(--bg-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 20px 22px !important;
    transition: border-color 0.2s;
}
[data-testid="metric-container"]:hover { border-color: var(--border-2) !important; }
[data-testid="metric-container"] label {
    font-family: var(--font-mono) !important;
    color: var(--text-muted) !important;
    font-size: 10px !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 500;
}
[data-testid="stMetricValue"] { font-family: var(--font) !important; color: #fff !important; font-size: 28px !important; font-weight: 700 !important; letter-spacing: -0.5px; }
[data-testid="stMetricDelta"] { font-size: 12px !important; }

.stButton > button {
    font-family: var(--font) !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border-radius: var(--radius-sm) !important;
    border: none !important;
    padding: 9px 18px !important;
    transition: all 0.15s ease !important;
    cursor: pointer;
}
.stButton > button[kind="primary"] { background: var(--red) !important; color: #fff !important; }
.stButton > button[kind="primary"]:hover { background: #cc0029 !important; box-shadow: 0 0 20px var(--red-glow) !important; }
.stButton > button[kind="secondary"] { background: var(--bg-4) !important; color: var(--text) !important; border: 1px solid var(--border-2) !important; }
.stButton > button[kind="secondary"]:hover { background: var(--bg-3) !important; border-color: #444 !important; }

.stTextInput > div > input,
.stTextArea > div > textarea {
    background: var(--bg-3) !important;
    border: 1px solid var(--border-2) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: var(--font) !important;
    font-size: 13px !important;
    transition: border-color 0.15s;
}
.stTextInput > div > input:focus,
.stTextArea > div > textarea:focus { border-color: var(--red) !important; box-shadow: 0 0 0 3px var(--red-glow) !important; }
.stSelectbox > div > div { background: var(--bg-3) !important; border: 1px solid var(--border-2) !important; border-radius: var(--radius-sm) !important; color: var(--text) !important; font-family: var(--font) !important; font-size: 13px !important; }
label { color: var(--text-muted) !important; font-size: 12px !important; font-weight: 500 !important; letter-spacing: 0.3px; }

[data-testid="stTabs"] [role="tablist"] { border-bottom: 1px solid var(--border) !important; background: transparent !important; gap: 0 !important; padding: 0 !important; }
[data-testid="stTabs"] button[role="tab"] { font-family: var(--font) !important; font-size: 13px !important; font-weight: 500 !important; color: var(--text-muted) !important; background: transparent !important; border: none !important; border-bottom: 2px solid transparent !important; border-radius: 0 !important; padding: 12px 20px !important; transition: all 0.15s !important; }
[data-testid="stTabs"] button[role="tab"]:hover { color: var(--text) !important; background: rgba(255,255,255,0.03) !important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color: #fff !important; border-bottom: 2px solid var(--red) !important; }
[data-testid="stTabs"] [data-testid="stTabsContent"] { padding-top: 24px !important; }

[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: var(--radius) !important; overflow: hidden !important; }
[data-testid="stDataFrame"] table { font-family: var(--font) !important; }
[data-testid="stDataFrame"] thead th { background: var(--bg-3) !important; color: var(--text-muted) !important; font-size: 10px !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.8px !important; border-bottom: 1px solid var(--border) !important; padding: 10px 14px !important; }
[data-testid="stDataFrame"] tbody td { font-size: 13px !important; border-bottom: 1px solid var(--border) !important; padding: 10px 14px !important; color: var(--text) !important; }
[data-testid="stDataFrame"] tbody tr:hover td { background: var(--bg-3) !important; }

.streamlit-expanderHeader { background: var(--bg-3) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-sm) !important; color: var(--text) !important; font-family: var(--font) !important; font-size: 13px !important; font-weight: 500 !important; padding: 10px 14px !important; }
.streamlit-expanderContent { background: var(--bg-2) !important; border: 1px solid var(--border) !important; border-top: none !important; border-radius: 0 0 var(--radius-sm) var(--radius-sm) !important; }

[data-testid="stProgressBar"] > div > div { background: var(--red) !important; border-radius: 2px !important; }
[data-testid="stProgressBar"] > div { background: var(--bg-4) !important; border-radius: 2px !important; height: 3px !important; }

hr { border-color: var(--border) !important; margin: 16px 0 !important; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border-2); border-radius: 3px; }

/* Custom components */
.brand { display: flex; align-items: center; gap: 10px; padding: 4px 0 20px; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
.brand-icon { width: 30px; height: 30px; background: var(--red); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 900; color: white; flex-shrink: 0; }
.brand-text { line-height: 1.2; }
.brand-name { font-size: 14px; font-weight: 700; color: #fff; }
.brand-sub { font-size: 10px; color: var(--red); font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
.page-header-left h1 { font-size: 24px; margin-bottom: 4px !important; }
.page-header-left p { color: var(--text-muted); font-size: 13px; margin: 0; }

.alert { border-radius: var(--radius-sm); padding: 12px 14px; font-size: 13px; margin-bottom: 8px; display: flex; align-items: flex-start; gap: 10px; }
.alert-icon { font-size: 15px; flex-shrink: 0; margin-top: 1px; }
.alert-body { flex: 1; }
.alert-title { font-weight: 600; margin-bottom: 2px; }
.alert-desc  { font-size: 12px; opacity: 0.8; }
.alert-warn   { background: rgba(245,166,35,0.1); border: 1px solid rgba(245,166,35,0.3); color: #e8c46b; }
.alert-danger { background: rgba(255,0,51,0.08); border: 1px solid rgba(255,0,51,0.25); color: #ff8099; }
.alert-success{ background: rgba(29,185,84,0.08); border: 1px solid rgba(29,185,84,0.25); color: #5ce68f; }
.alert-info   { background: rgba(30,143,255,0.08); border: 1px solid rgba(30,143,255,0.25); color: #7ac2ff; }

.video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; margin-top: 4px; }
.video-card { background: var(--bg-3); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; transition: border-color 0.2s, transform 0.15s; }
.video-card:hover { border-color: var(--border-2); transform: translateY(-2px); }
.video-thumb { width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; background: var(--bg-4); }
.video-thumb-ph { width: 100%; aspect-ratio: 16/9; background: var(--bg-4); display: flex; align-items: center; justify-content: center; color: var(--text-dim); font-size: 28px; }
.video-card-body { padding: 12px 14px; }
.video-card-title { font-size: 13px; font-weight: 600; color: var(--text); line-height: 1.4; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.video-card-meta { display: flex; gap: 10px; flex-wrap: wrap; }
.vstat { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); }
.vstat span { color: var(--text); font-weight: 600; }
.video-card-link { display: inline-block; margin-top: 8px; font-size: 11px; color: var(--red); text-decoration: none; font-weight: 600; letter-spacing: 0.3px; }
.vbadge { display: inline-block; padding: 2px 7px; border-radius: 3px; font-size: 10px; font-weight: 600; margin-bottom: 6px; font-family: var(--font-mono); letter-spacing: 0.5px; }
.badge-hot  { background: rgba(255,0,51,0.15); color: #ff6680; border: 1px solid rgba(255,0,51,0.3); }
.badge-new  { background: rgba(30,143,255,0.15); color: #7ac2ff; border: 1px solid rgba(30,143,255,0.3); }
.badge-ever { background: rgba(29,185,84,0.15); color: #5ce68f; border: 1px solid rgba(29,185,84,0.3); }

.ai-response { background: linear-gradient(135deg, rgba(255,0,51,0.04) 0%, rgba(0,0,0,0) 60%); border: 1px solid rgba(255,0,51,0.2); border-radius: var(--radius); padding: 20px 22px; margin-bottom: 16px; }
.ai-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.ai-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--red); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
.ai-label { font-family: var(--font-mono); font-size: 10px; font-weight: 600; color: var(--red); letter-spacing: 1px; text-transform: uppercase; }

.best-day { background: rgba(29,185,84,0.06); border: 1px solid rgba(29,185,84,0.2); border-radius: var(--radius); padding: 16px 20px; display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.best-day-icon { font-size: 28px; }
.best-day-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.8px; font-family: var(--font-mono); margin-bottom: 2px; }
.best-day-value { font-size: 22px; font-weight: 700; color: var(--green); }
.best-day-sub { font-size: 12px; color: var(--text-muted); }

.tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
.tag { background: var(--bg-4); border: 1px solid var(--border-2); color: var(--text-muted); padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; font-family: var(--font-mono); }
.tag-hot { border-color: rgba(255,0,51,0.4); color: #ff8099; background: rgba(255,0,51,0.08); }

.section-label { font-family: var(--font-mono); font-size: 9px; font-weight: 600; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }

.ch-pill { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: var(--bg-3); border: 1px solid var(--border); border-radius: var(--radius-sm); margin-bottom: 6px; transition: border-color 0.15s; }
.ch-pill:hover { border-color: var(--border-2); }
.ch-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); flex-shrink: 0; }
.ch-dot-empty { background: var(--text-dim); }
.ch-info { flex: 1; min-width: 0; }
.ch-name { font-size: 12px; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ch-subs { font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); }

.stTextArea textarea { font-family: var(--font-mono) !important; font-size: 12px !important; line-height: 1.7 !important; }

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
[data-testid="stToolbar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────────────────────
PLOTLY = dict(
    paper_bgcolor="#0a0a0a",
    plot_bgcolor="#111111",
    font=dict(family="Instrument Sans", color="#737373", size=12),
    xaxis=dict(gridcolor="#1e1e1e", zerolinecolor="#252525", linecolor="#252525"),
    yaxis=dict(gridcolor="#1e1e1e", zerolinecolor="#252525", linecolor="#252525"),
    margin=dict(l=16, r=16, t=44, b=16),
    title_font=dict(size=14, color="#e8e8e8", family="Instrument Sans"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#252525"),
)

# ─────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────
DB_PATH = "/tmp/chamberlin.db" if os.path.exists("/tmp") else "chamberlin.db"

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
        # Migrate: strip any time component from existing snapshot dates
        db.execute("""
            UPDATE snapshots
            SET snapshot_date = substr(snapshot_date, 1, 10)
            WHERE length(snapshot_date) > 10
        """)

def load_channels_from_db() -> dict:
    channels = {}
    with get_db() as db:
        rows = db.execute("SELECT * FROM channels").fetchall()
        for row in rows:
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
                "id": ch["channel_id"], "data": df, "channel_stats": stats,
                "last_refreshed": ch["last_refreshed"], "notes": ch["notes"] or "", "ideas": ideas}
    return channels

def save_channel_to_db(name, channel_id, stats, df, last_refreshed, notes="", ideas=None):
    with get_db() as db:
        db.execute("""INSERT INTO channels (name,channel_id,channel_stats,last_refreshed,notes,ideas)
            VALUES (?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET
            channel_id=excluded.channel_id, channel_stats=excluded.channel_stats,
            last_refreshed=excluded.last_refreshed, notes=excluded.notes, ideas=excluded.ideas""",
            (name, channel_id, json.dumps(stats), last_refreshed, notes, json.dumps(ideas or {})))
        if df is not None and not df.empty:
            db.execute("DELETE FROM videos WHERE channel_name=?", (name,))
            for _, row in df.iterrows():
                pub = row["Published"].strftime("%Y-%m-%d") if pd.notna(row["Published"]) else ""
                db.execute("""INSERT INTO videos
                    (channel_name,title,published,views,likes,comments,url,thumbnail,
                     days_since_publish,views_per_day,like_rate,comment_rate)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (name, row.get("Title",""), pub,
                     int(row.get("Views",0)), int(row.get("Likes",0)), int(row.get("Comments",0)),
                     row.get("URL",""), row.get("Thumbnail",""),
                     int(row.get("Days Since Publish",0)), float(row.get("Views per Day",0)),
                     float(row.get("Like Rate %",0)), float(row.get("Comment Rate %",0))))

def delete_channel_from_db(name):
    with get_db() as db:
        db.execute("DELETE FROM channels WHERE name=?", (name,))
        db.execute("DELETE FROM videos WHERE channel_name=?", (name,))

def save_snapshot_to_db(channel_name, subscribers, total_views):
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as db:
        db.execute("""INSERT INTO snapshots (channel_name,snapshot_date,subscribers,total_views)
            VALUES (?,?,?,?) ON CONFLICT(channel_name,snapshot_date) DO UPDATE SET
            subscribers=excluded.subscribers, total_views=excluded.total_views""",
            (channel_name, today, subscribers, total_views))

def load_snapshots_from_db(channel_name) -> pd.DataFrame:
    with get_db() as db:
        rows = db.execute(
            "SELECT snapshot_date,subscribers,total_views FROM snapshots WHERE channel_name=? ORDER BY snapshot_date",
            (channel_name,)).fetchall()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame([dict(r) for r in rows])
    # Strip any time component, force clean date strings
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"]).dt.normalize().dt.date
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
    return df

# ─────────────────────────────────────────────────────────────
# SECRETS
# ─────────────────────────────────────────────────────────────
def get_secret(key, fallback=""):
    try:
        return st.secrets.get(key, fallback)
    except Exception:
        return os.environ.get(key, fallback)

# ─────────────────────────────────────────────────────────────
# YOUTUBE API
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_channel_data(api_key: str, channel_id: str):
    youtube = build("youtube", "v3", developerKey=api_key)
    ch_resp = youtube.channels().list(part="snippet,statistics,contentDetails", id=channel_id).execute()
    if not ch_resp.get("items"):
        raise ValueError(f"Channel ID not found: {channel_id}")
    ch = ch_resp["items"][0]
    stats = {
        "subscribers":   int(ch["statistics"].get("subscriberCount", 0)),
        "total_views":   int(ch["statistics"].get("viewCount", 0)),
        "video_count":   int(ch["statistics"].get("videoCount", 0)),
        "channel_name":  ch["snippet"]["title"],
        "channel_thumb": ch["snippet"]["thumbnails"].get("medium", {}).get("url", ""),
        "description":   ch["snippet"].get("description", "")[:300],
    }
    uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]

    videos, next_page = [], None
    for _ in range(2):
        pl = youtube.playlistItems().list(
            part="contentDetails", playlistId=uploads_id,
            maxResults=50, pageToken=next_page).execute()
        video_ids = [i["contentDetails"]["videoId"] for i in pl["items"]]
        vr = youtube.videos().list(part="snippet,statistics", id=",".join(video_ids)).execute()
        for item in vr["items"]:
            s = item["statistics"]; sn = item["snippet"]
            thumbs = sn.get("thumbnails", {})
            thumb_url = (thumbs.get("maxres") or thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")
            videos.append({
                "Title":     sn["title"],
                "Published": sn["publishedAt"][:10],
                "Views":     int(s.get("viewCount", 0)),
                "Likes":     int(s.get("likeCount", 0)),
                "Comments":  int(s.get("commentCount", 0)),
                "URL":       f"https://youtu.be/{item['id']}",
                "Thumbnail": thumb_url,
            })
        next_page = pl.get("nextPageToken")
        if not next_page: break

    df = pd.DataFrame(videos)
    if not df.empty:
        df["Published"] = pd.to_datetime(df["Published"])
        df = df.sort_values("Published", ascending=False).reset_index(drop=True)
        df["Days Since Publish"] = (datetime.now() - df["Published"]).dt.days.clip(lower=1)
        df["Views per Day"]  = (df["Views"] / df["Days Since Publish"]).round(1)
        df["Like Rate %"]    = (df["Likes"]    / df["Views"].replace(0,1) * 100).round(2)
        df["Comment Rate %"] = (df["Comments"] / df["Views"].replace(0,1) * 100).round(2)
    return df, stats

def lookup_channel_name(api_key: str, channel_id: str) -> str:
    """Fetch just the channel title — cheap single API call."""
    youtube = build("youtube", "v3", developerKey=api_key)
    resp = youtube.channels().list(part="snippet", id=channel_id).execute()
    if not resp.get("items"):
        raise ValueError(f"No channel found for ID: {channel_id}")
    return resp["items"][0]["snippet"]["title"]


# ─────────────────────────────────────────────────────────────
# CLAUDE AI
# ─────────────────────────────────────────────────────────────
def generate_ai_ideas(anthropic_key: str, channel_name: str, df: pd.DataFrame, channel_desc: str = "") -> str:
    client = anthropic.Anthropic(api_key=anthropic_key)
    top_titles    = df.nlargest(15, "Views")["Title"].tolist()
    recent_titles = df.nlargest(10, "Views per Day")["Title"].tolist()
    avg_views = int(df["Views"].mean())
    day_col = df.copy(); day_col["Day"] = day_col["Published"].dt.day_name()
    best_day = day_col.groupby("Day")["Views"].mean().idxmax() if len(day_col) > 6 else "unknown"

    prompt = f"""You are a YouTube growth strategist analyzing a channel called "{channel_name}".

Channel overview:
- Average views per video: {avg_views:,}
- Best performing upload day: {best_day}
- Channel description: {channel_desc or "Not provided"}

Top 15 videos by views:
{chr(10).join(f"• {t}" for t in top_titles)}

Top 10 videos by momentum (views/day):
{chr(10).join(f"• {t}" for t in recent_titles)}

Based on this data, provide:

1. **Niche & Audience Analysis** (2-3 sentences on what's working and why)

2. **6 High-Potential Video Ideas** — each with:
   - A compelling, specific title
   - Why it will perform based on the patterns you see
   - Best format (long-form, short, series episode, etc.)

3. **One Series Concept** — a multi-part series that could drive sustained subscriber growth

4. **One Contrarian Opportunity** — something this channel is NOT doing that could outperform current content

Be specific, strategic, and data-driven. Reference actual patterns from the titles."""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=1400,
        messages=[{"role": "user", "content": prompt}])
    return msg.content[0].text

# ─────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────
def fmt(n) -> str:
    n = int(n)
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return f"{n:,}"

def detect_alerts(channels: dict) -> list:
    alerts = []
    cutoff = datetime.now() - timedelta(days=30)
    prior  = datetime.now() - timedelta(days=60)
    for name, info in channels.items():
        df = info.get("data")
        if df is None or df.empty or "Published" not in df.columns: continue
        recent = df[df["Published"] >= cutoff]["Views"]
        older  = df[(df["Published"] >= prior) & (df["Published"] < cutoff)]["Views"]
        if len(recent) >= 2 and len(older) >= 2 and older.mean() > 0:
            pct = (recent.mean() - older.mean()) / older.mean() * 100
            if pct <= -30: alerts.append({"channel": name, "type": "drop", "pct": pct})
            elif pct >= 40: alerts.append({"channel": name, "type": "spike", "pct": pct})
        if len(df) >= 5:
            old_vids = df[df["Days Since Publish"] >= 90]
            if not old_vids.empty:
                ev = old_vids[old_vids["Views per Day"] > df["Views per Day"].median() * 1.5]
                if not ev.empty:
                    alerts.append({"channel": name, "type": "evergreen",
                                   "title": ev.iloc[0]["Title"], "vpd": ev.iloc[0]["Views per Day"]})
    return alerts

def get_badge(row) -> str:
    if row["Days Since Publish"] <= 14: return '<span class="vbadge badge-new">NEW</span>'
    if row["Views per Day"] >= 500:     return '<span class="vbadge badge-hot">HOT</span>'
    if row["Days Since Publish"] >= 90 and row["Views per Day"] >= 100:
        return '<span class="vbadge badge-ever">EVERGREEN</span>'
    return ""

def render_video_grid(df: pd.DataFrame, max_cards: int = 12):
    subset = df.head(max_cards)
    cards = '<div class="video-grid">'
    for _, row in subset.iterrows():
        badge = get_badge(row)
        thumb = (f'<img class="video-thumb" src="{row["Thumbnail"]}" alt="" loading="lazy">'
                 if row.get("Thumbnail") else '<div class="video-thumb-ph">▶</div>')
        title = str(row["Title"]).replace('"','&quot;')[:80]
        ch    = f'<div class="vstat" style="color:var(--red);font-weight:600">{row.get("Channel","")}</div>' if row.get("Channel") else ""
        cards += f"""<div class="video-card">
            <a href="{row['URL']}" target="_blank" style="text-decoration:none">{thumb}</a>
            <div class="video-card-body">
                {ch}{badge}
                <div class="video-card-title">{title}</div>
                <div class="video-card-meta">
                    <div class="vstat"><span>{fmt(row['Views'])}</span> views</div>
                    <div class="vstat"><span>{row['Views per Day']:.0f}</span>/day</div>
                    <div class="vstat"><span>{row['Like Rate %']:.1f}%</span> liked</div>
                </div>
                <a href="{row['URL']}" target="_blank" class="video-card-link">Watch ↗</a>
            </div></div>"""
    cards += '</div>'
    st.markdown(cards, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────────────────
init_db()

if "channels" not in st.session_state:
    st.session_state.channels = load_channels_from_db()
if "api_key" not in st.session_state:
    st.session_state.api_key = get_secret("YOUTUBE_API_KEY")
if "anthropic_key" not in st.session_state:
    st.session_state.anthropic_key = get_secret("ANTHROPIC_API_KEY")
if "ideas_cache" not in st.session_state:
    st.session_state.ideas_cache = {}

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div class="brand">
        <div class="brand-icon">▶</div>
        <div class="brand-text">
            <div class="brand-name">Chamberlin</div>
            <div class="brand-sub">Media Monitor</div>
        </div></div>""", unsafe_allow_html=True)

    with st.expander("🔑  API Keys", expanded=not st.session_state.api_key):
        yt_key  = st.text_input("YouTube Data API Key",  value=st.session_state.api_key,  type="password", placeholder="AIza...")
        ant_key = st.text_input("Anthropic API Key",     value=st.session_state.anthropic_key, type="password", placeholder="sk-ant-...")
        if st.button("Save Keys", use_container_width=True):
            st.session_state.api_key      = yt_key
            st.session_state.anthropic_key = ant_key
            st.success("Saved.")

    st.markdown('<div class="section-label" style="margin-top:16px">Channels</div>', unsafe_allow_html=True)

    with st.expander("➕  Add Channel"):
        new_id = st.text_input("Channel ID", placeholder="UCxxxxxxxxxxxxxxxxxxxx")
        st.caption("The channel name will be fetched automatically.")
        if st.button("Add Channel", type="primary", use_container_width=True):
            if not st.session_state.api_key:
                st.error("Enter YouTube API key first.")
            elif not new_id:
                st.error("Enter a Channel ID.")
            else:
                cid = new_id.strip()
                # Check for duplicate IDs
                existing_ids = [v["id"] for v in st.session_state.channels.values()]
                if cid in existing_ids:
                    st.error("That channel is already added.")
                else:
                    with st.spinner("Looking up channel..."):
                        try:
                            ch_name = lookup_channel_name(st.session_state.api_key, cid)
                            if ch_name in st.session_state.channels:
                                # Append ID suffix if name collision
                                ch_name = f"{ch_name} ({cid[-6:]})"
                            st.session_state.channels[ch_name] = {
                                "id": cid, "data": None, "channel_stats": {},
                                "last_refreshed": "Never", "notes": "", "ideas": {}}
                            save_channel_to_db(ch_name, cid, {}, None, "Never")
                            st.success(f"Added: {ch_name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not find channel: {e}")

    if st.session_state.channels:
        for ch_name in list(st.session_state.channels.keys()):
            info  = st.session_state.channels[ch_name]
            stats = info.get("channel_stats", {})
            subs_str = fmt(stats.get("subscribers",0)) if stats.get("subscribers") else "—"
            has_data = info.get("data") is not None
            dot_cls  = "ch-dot" if has_data else "ch-dot ch-dot-empty"
            c1, c2 = st.columns([5,1])
            c1.markdown(f"""<div class="ch-pill">
                <div class="{dot_cls}"></div>
                <div class="ch-info">
                    <div class="ch-name">{ch_name}</div>
                    <div class="ch-subs">{subs_str} subs</div>
                </div></div>""", unsafe_allow_html=True)
            if c2.button("✕", key=f"del_{ch_name}"):
                delete_channel_from_db(ch_name)
                del st.session_state.channels[ch_name]
                st.rerun()

        st.divider()
        if st.session_state.api_key:
            if st.button("↺  Refresh All Channels", type="primary", use_container_width=True):
                errors = []
                prog = st.progress(0, text="Refreshing...")
                total = len(st.session_state.channels)
                fetch_channel_data.clear()
                for i, (ch_name, info) in enumerate(st.session_state.channels.items()):
                    try:
                        df, stats = fetch_channel_data(st.session_state.api_key, info["id"])
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                        st.session_state.channels[ch_name].update({"data":df,"channel_stats":stats,"last_refreshed":ts})
                        save_channel_to_db(ch_name, info["id"], stats, df, ts, info.get("notes",""), info.get("ideas",{}))
                        save_snapshot_to_db(ch_name, stats["subscribers"], stats["total_views"])
                        prog.progress((i+1)/total, text=f"Done: {ch_name}")
                    except Exception as e:
                        errors.append(f"{ch_name}: {e}")
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
        <p style="color:#737373">Enter your YouTube Data API key in the sidebar to get started.</p>
    </div>""", unsafe_allow_html=True)
    st.stop()

if not st.session_state.channels:
    st.markdown("""<div style="max-width:480px;margin:80px auto;text-align:center">
        <div style="font-size:48px;margin-bottom:16px">📡</div>
        <h2 style="font-size:20px;font-weight:600;color:#fff;margin-bottom:8px">No channels yet</h2>
        <p style="color:#737373">Add your first YouTube channel using the sidebar.</p>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────
# MAIN TABS
# ─────────────────────────────────────────────────────────────
T_DASH, T_ALL, T_DETAIL, T_GROWTH = st.tabs(["  Dashboard  ","  All Channels  ","  Channel Detail  ","  Growth Trends  "])

# ═══════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════
with T_DASH:
    st.markdown("""<div class="page-header">
        <div class="page-header-left">
            <h1>Dashboard</h1>
            <p>Performance overview across all channels</p>
        </div></div>""", unsafe_allow_html=True)

    total_subs  = sum(v.get("channel_stats",{}).get("subscribers",0) for v in st.session_state.channels.values())
    total_views = sum(v.get("channel_stats",{}).get("total_views",0)  for v in st.session_state.channels.values())
    loaded      = sum(1 for v in st.session_state.channels.values() if v.get("data") is not None)

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Total Subscribers",   fmt(total_subs))
    k2.metric("Combined Views",       fmt(total_views))
    k3.metric("Channels Tracked",     len(st.session_state.channels))
    k4.metric("Channels with Data",   loaded)

    st.markdown("<br>", unsafe_allow_html=True)

    alerts = detect_alerts(st.session_state.channels)
    if alerts:
        st.markdown('<div class="section-label">Alerts</div>', unsafe_allow_html=True)
        for a in alerts:
            if a["type"] == "drop":
                st.markdown(f"""<div class="alert alert-danger"><div class="alert-icon">📉</div>
                    <div class="alert-body"><div class="alert-title">{a['channel']} — View drop detected</div>
                    <div class="alert-desc">Avg views down {abs(a['pct']):.0f}% vs prior 30 days. Review upload cadence or title strategy.</div></div></div>""", unsafe_allow_html=True)
            elif a["type"] == "spike":
                st.markdown(f"""<div class="alert alert-success"><div class="alert-icon">📈</div>
                    <div class="alert-body"><div class="alert-title">{a['channel']} — Momentum spike</div>
                    <div class="alert-desc">Avg views up {a['pct']:.0f}% vs prior 30 days. Double down on what's working.</div></div></div>""", unsafe_allow_html=True)
            elif a["type"] == "evergreen":
                st.markdown(f"""<div class="alert alert-info"><div class="alert-icon">🌿</div>
                    <div class="alert-body"><div class="alert-title">{a['channel']} — Evergreen asset identified</div>
                    <div class="alert-desc">"{a['title'][:65]}..." still pulling {a['vpd']:.0f} views/day. Consider promoting it or building a series around it.</div></div></div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    all_rows = []
    for ch_name, info in st.session_state.channels.items():
        df = info.get("data")
        if df is not None and not df.empty:
            top = df.nlargest(8,"Views per Day").copy()
            top["Channel"] = ch_name
            all_rows.append(top)

    if all_rows:
        combined = pd.concat(all_rows).nlargest(12,"Views per Day")
        st.markdown('<div class="section-label">Top Videos Right Now — By Momentum</div>', unsafe_allow_html=True)
        render_video_grid(combined, max_cards=12)

        st.markdown("<br><br>", unsafe_allow_html=True)
        all_full = pd.concat(all_rows)
        st.markdown('<div class="section-label">Quick Wins — High Engagement, Low Reach</div>', unsafe_allow_html=True)
        qw = all_full[all_full["Comment Rate %"] > all_full["Comment Rate %"].quantile(0.7)].nsmallest(4,"Views")
        for _, row in qw.iterrows():
            ch = row.get("Channel","")
            st.markdown(f"""<div class="alert alert-warn"><div class="alert-icon">💡</div>
                <div class="alert-body"><div class="alert-title">{ch} — {str(row['Title'])[:70]}</div>
                <div class="alert-desc">{row['Comment Rate %']:.2f}% comment rate with only {fmt(row['Views'])} views — high resonance, low distribution.</div></div></div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert alert-info"><div class="alert-icon">ℹ️</div><div class="alert-body"><div class="alert-title">No data loaded</div><div class="alert-desc">Refresh your channels to populate the dashboard.</div></div></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════
# ALL CHANNELS
# ═══════════════════════════════════════════
with T_ALL:
    st.markdown("""<div class="page-header">
        <div class="page-header-left"><h1>All Channels</h1><p>Portfolio overview and comparison</p></div></div>""", unsafe_allow_html=True)

    rows = []
    for ch_name, info in st.session_state.channels.items():
        df = info.get("data"); s = info.get("channel_stats",{})
        rows.append({
            "Channel":         ch_name,
            "Subscribers":     s.get("subscribers",0),
            "Total Views":     s.get("total_views",0),
            "Videos Analyzed": len(df) if df is not None else 0,
            "Avg Views":       int(df["Views"].mean()) if df is not None and not df.empty else 0,
            "Avg Views/Day":   round(df["Views per Day"].mean(),1) if df is not None and not df.empty else 0,
            "Last Refreshed":  info.get("last_refreshed","Never"),
        })

    if rows:
        summary_df = pd.DataFrame(rows).sort_values("Total Views", ascending=False)
        disp = summary_df.copy()
        disp["Subscribers"] = disp["Subscribers"].apply(fmt)
        disp["Total Views"] = disp["Total Views"].apply(fmt)
        disp["Avg Views"]   = disp["Avg Views"].apply(fmt)
        st.dataframe(disp, use_container_width=True, hide_index=True)
        st.download_button("⬇  Export CSV", summary_df.to_csv(index=False).encode(), "chamberlin_channels.csv", "text/csv")

        if len(rows) > 1:
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                fig = px.bar(summary_df, x="Channel", y="Subscribers", title="Subscribers by Channel",
                             color="Subscribers", color_continuous_scale=["#1a0000","#ff0033"])
                fig.update_layout(**PLOTLY, showlegend=False)
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig2 = px.bar(summary_df, x="Channel", y="Avg Views/Day", title="Avg Views/Day by Channel",
                              color="Avg Views/Day", color_continuous_scale=["#001a33","#1e8fff"])
                fig2.update_layout(**PLOTLY, showlegend=False)
                fig2.update_traces(marker_line_width=0)
                st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════
# CHANNEL DETAIL
# ═══════════════════════════════════════════
with T_DETAIL:
    selected = st.selectbox("Channel", list(st.session_state.channels.keys()), label_visibility="collapsed")
    info     = st.session_state.channels[selected]
    stats    = info.get("channel_stats",{})
    ch_df    = info.get("data")

    head_l, head_r = st.columns([5,2])
    with head_l:
        st.markdown(f"""<div style="margin-bottom:4px">
            <h1>{stats.get('channel_name', selected)}</h1>
            <p style="color:var(--text-muted);font-size:12px;font-family:var(--font-mono)">
                ID: {info['id']}  •  Last refreshed: {info.get('last_refreshed','Never')}
            </p></div>""", unsafe_allow_html=True)
    with head_r:
        if st.button("↺  Refresh Channel", type="primary", use_container_width=True):
            with st.spinner("Fetching from YouTube..."):
                try:
                    fetch_channel_data.clear()
                    df_new, stats_new = fetch_channel_data(st.session_state.api_key, info["id"])
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.channels[selected].update({"data":df_new,"channel_stats":stats_new,"last_refreshed":ts})
                    save_channel_to_db(selected, info["id"], stats_new, df_new, ts, info.get("notes",""), info.get("ideas",{}))
                    save_snapshot_to_db(selected, stats_new["subscribers"], stats_new["total_views"])
                    st.success("Done!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    st.divider()

    if ch_df is None or ch_df.empty:
        st.markdown('<div class="alert alert-info"><div class="alert-icon">ℹ️</div><div class="alert-body"><div class="alert-title">No data loaded</div><div class="alert-desc">Click Refresh Channel to load video data.</div></div></div>', unsafe_allow_html=True)
        st.stop()

    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("Subscribers",     fmt(stats.get("subscribers",0)))
    m2.metric("Total Views",     fmt(stats.get("total_views",0)))
    m3.metric("Videos Analyzed", len(ch_df))
    m4.metric("Avg Views",       fmt(int(ch_df["Views"].mean())))
    m5.metric("Avg Views / Day", f"{ch_df['Views per Day'].mean():.1f}")

    st.markdown("<br>", unsafe_allow_html=True)

    DT1,DT2,DT3,DT4,DT5,DT6 = st.tabs(["  Videos  ","  Charts  ","  Upload Timing  ","  Content Series  ","  AI Ideas  ","  Notes  "])

    # ── VIDEOS ──
    with DT1:
        c_a, c_b = st.columns([2,4])
        view_mode = c_a.radio("View", ["Grid","Table"], horizontal=True, label_visibility="collapsed")
        sort_by   = c_b.selectbox("Sort by", ["Views","Views per Day","Like Rate %","Comment Rate %","Published"], label_visibility="collapsed")
        sorted_df = ch_df.sort_values(sort_by, ascending=(sort_by=="Published")).reset_index(drop=True)
        if view_mode == "Grid":
            render_video_grid(sorted_df, max_cards=24)
        else:
            disp = sorted_df[["Title","Published","Views","Views per Day","Like Rate %","Comment Rate %","Likes","Comments","URL"]].copy()
            disp["Published"] = disp["Published"].dt.strftime("%Y-%m-%d")
            st.dataframe(disp, use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("⬇  Export CSV", ch_df.to_csv(index=False).encode(), f"{selected.replace(' ','_')}.csv","text/csv")

    # ── CHARTS ──
    with DT2:
        c1,c2 = st.columns(2)
        with c1:
            top10 = ch_df.nlargest(10,"Views").sort_values("Views")
            fig = px.bar(top10, x="Views", y="Title", orientation="h", title="Top 10 by Total Views",
                         color="Views", color_continuous_scale=["#1a0000","#ff0033"])
            fig.update_layout(**PLOTLY, showlegend=False, height=380)
            fig.update_traces(marker_line_width=0)
            fig.update_yaxes(tickfont=dict(size=10,color="#737373"))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            top10m = ch_df.nlargest(10,"Views per Day").sort_values("Views per Day")
            fig2 = px.bar(top10m, x="Views per Day", y="Title", orientation="h", title="Top 10 by Momentum",
                          color="Views per Day", color_continuous_scale=["#001a33","#1e8fff"])
            fig2.update_layout(**PLOTLY, showlegend=False, height=380)
            fig2.update_traces(marker_line_width=0)
            fig2.update_yaxes(tickfont=dict(size=10,color="#737373"))
            st.plotly_chart(fig2, use_container_width=True)

        trend = ch_df.sort_values("Published")
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=trend["Published"], y=trend["Views"], mode="lines+markers",
            line=dict(color="#ff0033",width=2), marker=dict(color="#ff0033",size=5),
            fill="tozeroy", fillcolor="rgba(255,0,51,0.06)", name="Views"))
        fig3.update_layout(**PLOTLY, title="Views Over Time", height=300)
        st.plotly_chart(fig3, use_container_width=True)

        fig4 = px.scatter(ch_df, x="Views", y="Like Rate %", size="Comments", color="Comment Rate %",
                          hover_name="Title", title="Engagement Map — bubble size = Comments",
                          color_continuous_scale="Reds")
        fig4.update_layout(**PLOTLY, height=350)
        st.plotly_chart(fig4, use_container_width=True)

    # ── UPLOAD TIMING ──
    with DT3:
        day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        temp = ch_df.copy(); temp["Day"] = temp["Published"].dt.day_name()
        day_avg = temp.groupby("Day")["Views"].mean().reindex(day_order).dropna()

        if not day_avg.empty:
            best_day = day_avg.idxmax(); best_avg = day_avg.max()
            st.markdown(f"""<div class="best-day">
                <div class="best-day-icon">📅</div>
                <div>
                    <div class="best-day-label">Best Day to Upload</div>
                    <div class="best-day-value">{best_day}</div>
                    <div class="best-day-sub">Avg {fmt(int(best_avg))} views on videos posted this day</div>
                </div></div>""", unsafe_allow_html=True)

            fig = px.bar(x=day_avg.index, y=day_avg.values, title="Avg Views by Upload Day",
                         labels={"x":"","y":"Avg Views"}, color=day_avg.values,
                         color_continuous_scale=["#1a0000","#ff0033"])
            fig.update_layout(**PLOTLY, showlegend=False)
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)

        monthly = ch_df.copy()
        monthly["Month"] = monthly["Published"].dt.to_period("M").astype(str)
        freq = monthly.groupby("Month").agg(Videos=("Title","count"), Avg_Views=("Views","mean")).reset_index()
        freq["Avg_Views"] = freq["Avg_Views"].round(0).astype(int)

        fa, fb = st.columns(2)
        with fa:
            fig_freq = px.bar(freq, x="Month", y="Videos", title="Videos Posted per Month",
                              labels={"Videos":"Videos Posted","Month":""})
            fig_freq.update_traces(marker_color="#2a2a2a", marker_line_width=0)
            fig_freq.update_layout(**PLOTLY)
            st.plotly_chart(fig_freq, use_container_width=True)
        with fb:
            fig_avgv = px.line(freq, x="Month", y="Avg_Views", title="Avg Views per Month",
                               labels={"Avg_Views":"Avg Views","Month":""}, markers=True)
            fig_avgv.update_traces(line_color="#ff0033", marker_color="#ff0033", marker_size=6)
            fig_avgv.update_layout(**PLOTLY)
            st.plotly_chart(fig_avgv, use_container_width=True)

    # ── CONTENT SERIES ──
    with DT4:
        st.markdown('<div class="section-label">Topic Analysis</div>', unsafe_allow_html=True)
        titles = ch_df["Title"].tolist()
        words_all = []
        for t in titles: words_all.extend(re.findall(r"\b[A-Za-z]{3,}\b", t))
        stop = {"this","that","with","from","have","what","your","they","their","will","more","just","been",
                "like","also","when","then","than","about","which","there","after","video","youtube",
                "channel","episode","part","feat","official","full","new","the","and","for","are","but",
                "not","you","all","can","her","was","one","our","out","day","get","has","him","his",
                "how","its","let","may","now","old","own","see","two","way","who","boy","did","use"}
        filtered = [w.lower() for w in words_all if w.lower() not in stop and len(w) > 3]
        top_words = Counter(filtered).most_common(20)

        if top_words:
            tags_html = '<div class="tags">'
            for word, count in top_words[:14]:
                mask  = ch_df["Title"].str.contains(word, case=False, na=False)
                avg_v = int(ch_df.loc[mask,"Views"].mean()) if mask.any() else 0
                cls   = "tag tag-hot" if avg_v > ch_df["Views"].mean() else "tag"
                tags_html += f'<span class="{cls}">{word} ({count})</span>'
            tags_html += '</div>'
            st.markdown(tags_html, unsafe_allow_html=True)
            st.caption("🔴 Red = above-average views for this keyword")

        phrases = []
        for t in titles:
            ws = re.findall(r"\b[A-Za-z]{3,}\b", t)
            phrases.extend([f"{ws[i]} {ws[i+1]}" for i in range(len(ws)-1)])
        stop_phrases = {"and the","in the","on the","of the","to the","is a","it is","with the","for the","how to","that is","this is","you are"}
        phrases_f = [p.lower() for p in phrases if p.lower() not in stop_phrases]
        phrase_counts = Counter(phrases_f).most_common(12)

        if phrase_counts:
            phr_df = pd.DataFrame(phrase_counts, columns=["Phrase","Count"])
            phr_df["Avg Views"] = phr_df["Phrase"].apply(
                lambda p: int(ch_df.loc[ch_df["Title"].str.contains(p,case=False,na=False),"Views"].mean())
                if ch_df["Title"].str.contains(p,case=False,na=False).any() else 0)
            phr_df = phr_df.sort_values("Avg Views", ascending=False)
            fig = px.scatter(phr_df, x="Count", y="Avg Views", text="Phrase",
                             title="Topic Frequency vs. Avg Views",
                             color="Avg Views", color_continuous_scale="Reds", size="Count")
            fig.update_traces(textposition="top center", textfont=dict(size=10,color="#e8e8e8"))
            fig.update_layout(**PLOTLY, height=400)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(phr_df, use_container_width=True, hide_index=True)

    # ── AI IDEAS ──
    with DT5:
        st.markdown('<div class="section-label">Claude AI — Strategic Ideas</div>', unsafe_allow_html=True)
        if not st.session_state.anthropic_key:
            st.markdown('<div class="alert alert-warn"><div class="alert-icon">⚠️</div><div class="alert-body"><div class="alert-title">Anthropic API key required</div><div class="alert-desc">Add your key in the sidebar to enable AI-powered ideas.</div></div></div>', unsafe_allow_html=True)
        else:
            if st.button("✦  Generate Strategic Ideas with Claude", type="primary"):
                with st.spinner("Claude is analyzing your channel..."):
                    try:
                        result = generate_ai_ideas(
                            st.session_state.anthropic_key, selected, ch_df,
                            stats.get("description",""))
                        st.session_state.ideas_cache[selected] = result
                        st.session_state.channels[selected]["ideas"] = {"ai_text": result}
                        save_channel_to_db(selected, info["id"], stats, ch_df,
                                           info.get("last_refreshed",""), info.get("notes",""), {"ai_text": result})
                    except Exception as e:
                        st.error(f"Claude API error: {e}")

            cached = (st.session_state.ideas_cache.get(selected) or
                      info.get("ideas",{}).get("ai_text",""))
            if cached:
                st.markdown(f"""<div class="ai-response">
                    <div class="ai-header">
                        <div class="ai-dot"></div>
                        <div class="ai-label">Claude Analysis</div>
                    </div>
                    <div style="font-size:13px;line-height:1.9;color:#c8c8c8;white-space:pre-wrap">{cached}</div>
                </div>""", unsafe_allow_html=True)

    # ── NOTES ──
    with DT6:
        st.markdown('<div class="section-label">Team Notes</div>', unsafe_allow_html=True)
        new_notes = st.text_area("Notes", value=info.get("notes",""), height=220,
                                 placeholder="Observations, strategy, action items...",
                                 label_visibility="collapsed")
        if st.button("💾  Save Notes", type="primary"):
            st.session_state.channels[selected]["notes"] = new_notes
            save_channel_to_db(selected, info["id"], stats, ch_df,
                               info.get("last_refreshed",""), new_notes, info.get("ideas",{}))
            st.success("Saved.")

# ═══════════════════════════════════════════
# GROWTH TRENDS
# ═══════════════════════════════════════════
with T_GROWTH:
    st.markdown("""<div class="page-header">
        <div class="page-header-left"><h1>Growth Trends</h1>
        <p>Historical snapshots — updated every time you refresh a channel</p>
        </div></div>""", unsafe_allow_html=True)

    growth_ch = st.selectbox("Channel", list(st.session_state.channels.keys()), key="g_ch")
    snap_df   = load_snapshots_from_db(growth_ch)

    if snap_df.empty:
        st.markdown('<div class="alert alert-info"><div class="alert-icon">📸</div><div class="alert-body"><div class="alert-title">No snapshots yet</div><div class="alert-desc">Refresh this channel over multiple days to build a growth history.</div></div></div>', unsafe_allow_html=True)
    else:
        snap_df["snapshot_date"] = pd.to_datetime(snap_df["snapshot_date"]).dt.normalize()
        g1,g2 = st.columns(2)
        with g1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=snap_df["snapshot_date"], y=snap_df["subscribers"],
                mode="lines+markers", line=dict(color="#ff0033",width=2), marker=dict(size=6,color="#ff0033"),
                fill="tozeroy", fillcolor="rgba(255,0,51,0.06)", name="Subscribers"))
            fig.update_layout(**PLOTLY, title="Subscriber Growth", height=300)
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=snap_df["snapshot_date"], y=snap_df["total_views"],
                mode="lines+markers", line=dict(color="#1e8fff",width=2), marker=dict(size=6,color="#1e8fff"),
                fill="tozeroy", fillcolor="rgba(30,143,255,0.06)", name="Total Views"))
            fig2.update_layout(**PLOTLY, title="Total Views Growth", height=300)
            st.plotly_chart(fig2, use_container_width=True)

        if len(snap_df) > 1:
            snap_df = snap_df.sort_values("snapshot_date")
            snap_df["Δ Subscribers"] = snap_df["subscribers"].diff().fillna(0).astype(int)
            snap_df["Δ Total Views"] = snap_df["total_views"].diff().fillna(0).astype(int)
            snap_df["Date"]          = snap_df["snapshot_date"].dt.strftime("%Y-%m-%d")
            st.dataframe(
                snap_df[["Date","subscribers","total_views","Δ Subscribers","Δ Total Views"]]
                .rename(columns={"subscribers":"Subscribers","total_views":"Total Views"})
                .sort_values("Date", ascending=False),
                use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown('<p style="color:var(--text-dim);font-size:11px;font-family:var(--font-mono)">Chamberlin Media Monitor  •  YouTube Data API v3  •  Claude AI  •  Built for Chamberlin Media</p>', unsafe_allow_html=True)
