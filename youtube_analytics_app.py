import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re
import json
import os
from datetime import datetime, timedelta
import time

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Chamberlin Media Monitor",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# GLOBAL STYLES — YouTube Studio dark aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.stApp {
    background-color: #0f0f0f;
    color: #e0e0e0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid #222;
}
[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem;
}

/* ── Headers ── */
h1 { color: #ffffff; font-weight: 700; font-size: 26px; letter-spacing: -0.5px; margin-bottom: 0 !important; }
h2 { color: #f1f1f1; font-weight: 600; font-size: 18px; }
h3 { color: #e0e0e0; font-weight: 500; font-size: 15px; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 16px 20px !important;
}
[data-testid="metric-container"] label {
    color: #909090 !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 26px !important;
    font-weight: 700 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* ── Buttons ── */
.stButton > button {
    background-color: #ff0000;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 13px;
    padding: 8px 18px;
    transition: background 0.15s;
}
.stButton > button:hover {
    background-color: #cc0000;
    color: #fff;
    border: none;
}
.stButton > button[kind="secondary"] {
    background-color: #2a2a2a;
    color: #e0e0e0;
}
.stButton > button[kind="secondary"]:hover {
    background-color: #383838;
}

/* ── Inputs ── */
.stTextInput > div > input,
.stTextArea > div > textarea,
.stSelectbox > div > div {
    background-color: #1a1a1a !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    color: #e0e0e0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stSelectbox > div > div:hover {
    border-color: #ff0000 !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #2a2a2a;
    gap: 0;
}
[data-testid="stTabs"] button[role="tab"] {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: #909090;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 13px;
    padding: 10px 18px;
    border-radius: 0;
    transition: all 0.15s;
}
[data-testid="stTabs"] button[role="tab"]:hover {
    color: #e0e0e0;
    background: #1a1a1a;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #ff0000;
    border-bottom: 2px solid #ff0000;
    background: transparent;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    overflow: hidden;
}
[data-testid="stDataFrame"] thead tr th {
    background: #1a1a1a !important;
    color: #909090 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #2a2a2a !important;
}
[data-testid="stDataFrame"] tbody tr:hover td {
    background: #1e1e1e !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background-color: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #e0e0e0 !important;
    font-weight: 500 !important;
}

/* ── Alerts ── */
.stAlert {
    background-color: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
}

/* ── Dividers ── */
hr { border-color: #2a2a2a !important; }

/* ── Sidebar channel pills ── */
.channel-pill {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 6px;
    font-size: 13px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* ── Info box ── */
.info-box {
    background: #161b22;
    border: 1px solid #30363d;
    border-left: 3px solid #ff0000;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 12px;
    font-size: 13px;
    color: #c9d1d9;
}

/* ── Alert box ── */
.alert-box {
    background: #1f1108;
    border: 1px solid #d4a017;
    border-left: 3px solid #f5a623;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #e0c87a;
}

/* ── Success box ── */
.success-box {
    background: #0d1f12;
    border: 1px solid #2ea043;
    border-left: 3px solid #56d364;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #7ee787;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f0f0f; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #555; }

/* ── Logo area ── */
.logo-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}
.logo-icon {
    width: 32px;
    height: 32px;
    background: #ff0000;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS & PERSISTENCE
# ─────────────────────────────────────────────
DATA_FILE = "channels.json"
SNAPSHOT_FILE = "snapshots.json"

PLOTLY_DARK = {
    "paper_bgcolor": "#0f0f0f",
    "plot_bgcolor": "#151515",
    "font": {"color": "#e0e0e0", "family": "DM Sans"},
    "xaxis": {"gridcolor": "#222", "zerolinecolor": "#333"},
    "yaxis": {"gridcolor": "#222", "zerolinecolor": "#333"},
    "margin": {"l": 20, "r": 20, "t": 40, "b": 20},
}

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "channels" not in st.session_state:
    st.session_state.channels = {}
if "notes" not in st.session_state:
    st.session_state.notes = {}
if "generated_ideas" not in st.session_state:
    st.session_state.generated_ideas = {}
if "snapshots" not in st.session_state:
    st.session_state.snapshots = {}


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def load_data():
    """Load channels from JSON file into session state."""
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r") as f:
            loaded = json.load(f)
        for k, v in loaded.items():
            df = None
            if v.get("data"):
                df = pd.read_json(v["data"])
                if not df.empty and "Published" in df.columns:
                    df["Published"] = pd.to_datetime(df["Published"], errors="coerce", utc=True)
                    df["Published"] = df["Published"].dt.tz_localize(None)
            st.session_state.channels[k] = {
                "id": v["id"],
                "data": df,
                "channel_stats": v.get("channel_stats", {}),
                "last_refreshed": v.get("last_refreshed", "Never"),
            }
            st.session_state.notes[k] = v.get("notes", "")
            st.session_state.generated_ideas[k] = v.get("ideas", {})
    except Exception as e:
        st.sidebar.error(f"Error loading data: {e}")


def save_data():
    """Persist session state to JSON file."""
    save_payload = {}
    for k, v in st.session_state.channels.items():
        df_json = v["data"].to_json() if v.get("data") is not None else None
        save_payload[k] = {
            "id": v["id"],
            "data": df_json,
            "channel_stats": v.get("channel_stats", {}),
            "last_refreshed": v.get("last_refreshed", "Never"),
            "notes": st.session_state.notes.get(k, ""),
            "ideas": st.session_state.generated_ideas.get(k, {}),
        }
    with open(DATA_FILE, "w") as f:
        json.dump(save_payload, f)


def load_snapshots():
    if not os.path.exists(SNAPSHOT_FILE):
        return
    try:
        with open(SNAPSHOT_FILE, "r") as f:
            st.session_state.snapshots = json.load(f)
    except Exception:
        pass


def save_snapshot(channel_name, stats):
    """Save a timestamped snapshot of channel stats for growth tracking."""
    today = datetime.now().strftime("%Y-%m-%d")
    if channel_name not in st.session_state.snapshots:
        st.session_state.snapshots[channel_name] = {}
    st.session_state.snapshots[channel_name][today] = stats
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(st.session_state.snapshots, f)


def fetch_channel_data(api_key: str, channel_id: str):
    """Fetch channel info + recent videos from YouTube Data API."""
    youtube = build("youtube", "v3", developerKey=api_key)

    # Channel stats
    ch_resp = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id,
    ).execute()
    if not ch_resp.get("items"):
        raise ValueError(f"Channel ID '{channel_id}' not found.")
    ch = ch_resp["items"][0]
    subs = int(ch["statistics"].get("subscriberCount", 0))
    total_views = int(ch["statistics"].get("viewCount", 0))
    video_count = int(ch["statistics"].get("videoCount", 0))
    uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    channel_name = ch["snippet"]["title"]
    channel_thumb = ch["snippet"]["thumbnails"].get("default", {}).get("url", "")

    # Video list (up to 100)
    videos = []
    next_page = None
    for _ in range(2):
        pl = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_id,
            maxResults=50,
            pageToken=next_page,
        ).execute()
        video_ids = [item["contentDetails"]["videoId"] for item in pl["items"]]
        vid_resp = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids),
        ).execute()
        for item in vid_resp["items"]:
            s = item["statistics"]
            sn = item["snippet"]
            videos.append({
                "Title": sn["title"],
                "Published": sn["publishedAt"][:10],
                "Views": int(s.get("viewCount", 0)),
                "Likes": int(s.get("likeCount", 0)),
                "Comments": int(s.get("commentCount", 0)),
                "URL": f"https://youtu.be/{item['id']}",
            })
        next_page = pl.get("nextPageToken")
        if not next_page:
            break

    df = pd.DataFrame(videos)
    if not df.empty:
        df["Published"] = pd.to_datetime(df["Published"])
        df = df.sort_values("Published", ascending=False)
        df["Days Since Publish"] = (datetime.now() - df["Published"]).dt.days
        df["Views per Day"] = (df["Views"] / df["Days Since Publish"].replace(0, 1)).round(1)
        df["Like Rate %"] = (df["Likes"] / df["Views"].replace(0, 1) * 100).round(2)
        df["Comment Rate %"] = (df["Comments"] / df["Views"].replace(0, 1) * 100).round(2)

    channel_stats = {
        "subscribers": subs,
        "total_views": total_views,
        "video_count": video_count,
        "channel_name": channel_name,
        "channel_thumb": channel_thumb,
    }
    return df, channel_stats


def generate_ideas(channel_name: str, df: pd.DataFrame) -> dict:
    """Analyze titles and generate content ideas (local heuristic, no API needed)."""
    all_titles = " | ".join(df["Title"].tolist())
    niche = (channel_name + " " + all_titles).lower()
    words = re.findall(r"\b[a-z]{4,}\b", niche)
    stop = {"this", "that", "with", "from", "have", "what", "your", "they", "their",
             "will", "more", "just", "been", "like", "also", "when", "then", "than",
             "about", "which", "there", "after", "video", "youtube", "channel"}
    filtered = [w for w in words if w not in stop]
    common = Counter(filtered).most_common(10)
    top = [w[0] for w in common][:6]

    if len(top) < 6:
        top += ["content", "growth", "strategy", "viral", "trending", "tips"][len(top):]

    # Best performing titles for inspiration
    top_vids = df.nlargest(5, "Views")["Title"].tolist()

    ideas = [
        f"The Ultimate Guide to {top[0].title()} (Based on What's Already Working)",
        f"Why Your {top[1].title()} Strategy Is Failing — And How to Fix It",
        f"{top[2].title()} vs {top[3].title()}: What Performs Better?",
        f"How I Grew Our {top[0].title()} Audience by 10x",
        f"The {top[4].title()} Playbook Nobody Is Talking About",
        f"Stop Making These {top[5].title()} Mistakes (Deep Dive)",
    ]

    return {
        "topics": top,
        "ideas": ideas,
        "inspiration": top_vids,
    }


def get_best_upload_day(df: pd.DataFrame):
    """Return best day to upload based on avg views."""
    temp = df.copy()
    temp["Day"] = temp["Published"].dt.day_name()
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    avg = temp.groupby("Day")["Views"].mean().reindex(day_order).dropna()
    return avg


def detect_alerts(channels: dict) -> list:
    """Detect performance anomalies across channels."""
    alerts = []
    for name, info in channels.items():
        df = info.get("data")
        if df is None or df.empty:
            continue
        # Last 30 days vs prior 30 days
        cutoff = datetime.now() - timedelta(days=30)
        prior = datetime.now() - timedelta(days=60)
        recent = df[df["Published"] >= cutoff]["Views"]
        older = df[(df["Published"] >= prior) & (df["Published"] < cutoff)]["Views"]
        if len(recent) >= 2 and len(older) >= 2:
            r_avg = recent.mean()
            o_avg = older.mean()
            if o_avg > 0:
                pct = (r_avg - o_avg) / o_avg * 100
                if pct <= -30:
                    alerts.append({"channel": name, "type": "drop", "pct": pct})
                elif pct >= 50:
                    alerts.append({"channel": name, "type": "spike", "pct": pct})
    return alerts


def fmt_number(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


# ─────────────────────────────────────────────
# LOAD ON FIRST RUN
# ─────────────────────────────────────────────
if not st.session_state.channels:
    load_data()
    load_snapshots()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="logo-row">
        <div class="logo-icon">▶</div>
        <div style="font-size:16px;font-weight:700;color:#fff;letter-spacing:-0.3px;">Chamberlin<br><span style="color:#ff0000;font-size:12px;font-weight:500;letter-spacing:1px;">MEDIA MONITOR</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    API_KEY = st.text_input("YouTube Data API Key", type="password", placeholder="AIza...")
    st.divider()

    # Add channel
    with st.expander("➕  Add Channel"):
        nickname = st.text_input("Nickname", placeholder="My Channel")
        ch_id_input = st.text_input("Channel ID", placeholder="UCxxxxxxxxxxxxxxxxxxxx")
        if st.button("Add Channel"):
            if not API_KEY:
                st.error("Enter API key first.")
            elif not nickname or not ch_id_input:
                st.error("Fill in both fields.")
            elif nickname in st.session_state.channels:
                st.error("Channel already exists.")
            else:
                st.session_state.channels[nickname] = {
                    "id": ch_id_input.strip(),
                    "data": None,
                    "channel_stats": {},
                    "last_refreshed": "Never",
                }
                st.session_state.notes[nickname] = ""
                st.session_state.generated_ideas[nickname] = {}
                save_data()
                st.success(f"Added: {nickname}")
                st.rerun()

    # Channel list
    if st.session_state.channels:
        st.markdown("**Channels**")
        for ch_name in list(st.session_state.channels.keys()):
            col_a, col_b = st.columns([5, 1])
            stats = st.session_state.channels[ch_name].get("channel_stats", {})
            subs_str = fmt_number(stats.get("subscribers", 0)) if stats.get("subscribers") else "—"
            col_a.markdown(f"**{ch_name}**  \n<small style='color:#888'>{subs_str} subs</small>", unsafe_allow_html=True)
            if col_b.button("✕", key=f"rm_{ch_name}", help=f"Remove {ch_name}"):
                del st.session_state.channels[ch_name]
                st.session_state.notes.pop(ch_name, None)
                st.session_state.generated_ideas.pop(ch_name, None)
                save_data()
                st.rerun()
        st.divider()

    # Bulk refresh
    if st.session_state.channels and API_KEY:
        if st.button("🔄  Refresh All Channels", use_container_width=True):
            errors = []
            prog = st.progress(0)
            total = len(st.session_state.channels)
            for i, (ch_name, info) in enumerate(st.session_state.channels.items()):
                try:
                    df, stats = fetch_channel_data(API_KEY, info["id"])
                    st.session_state.channels[ch_name]["data"] = df
                    st.session_state.channels[ch_name]["channel_stats"] = stats
                    st.session_state.channels[ch_name]["last_refreshed"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    save_snapshot(ch_name, {"subscribers": stats["subscribers"], "total_views": stats["total_views"]})
                except Exception as e:
                    errors.append(f"{ch_name}: {e}")
                prog.progress((i + 1) / total)
            save_data()
            if errors:
                for err in errors:
                    st.error(err)
            else:
                st.success("All channels refreshed!")
            time.sleep(0.5)
            st.rerun()

# ─────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────
if not API_KEY:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="info-box">🔑  Enter your <strong>YouTube Data API Key</strong> in the sidebar to get started.</div>', unsafe_allow_html=True)
    st.stop()

if not st.session_state.channels:
    st.markdown('<div class="info-box">📡  Add your first YouTube channel using the sidebar.</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────
# NAVIGATION TABS
# ─────────────────────────────────────────────
TAB_HOME, TAB_OVERVIEW, TAB_DETAIL, TAB_GROWTH = st.tabs([
    "🏠  Dashboard",
    "📊  All Channels",
    "🔍  Channel Detail",
    "📈  Growth Trends",
])

# ══════════════════════════════════════════════
# TAB 1 — DASHBOARD HOME
# ══════════════════════════════════════════════
with TAB_HOME:
    st.markdown("## Team Dashboard")
    st.caption("Quick wins, alerts, and performance at a glance.")
    st.markdown("<br>", unsafe_allow_html=True)

    # Alerts
    alerts = detect_alerts(st.session_state.channels)
    if alerts:
        st.markdown("### 🚨 Performance Alerts")
        for a in alerts:
            if a["type"] == "drop":
                st.markdown(f'<div class="alert-box">📉 <strong>{a["channel"]}</strong> — avg views dropped <strong>{abs(a["pct"]):.0f}%</strong> vs last 30 days</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="success-box">📈 <strong>{a["channel"]}</strong> — avg views up <strong>{a["pct"]:.0f}%</strong> vs last 30 days</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Top-level KPIs across all channels
    total_subs = sum(v.get("channel_stats", {}).get("subscribers", 0) for v in st.session_state.channels.values())
    total_views_all = sum(v.get("channel_stats", {}).get("total_views", 0) for v in st.session_state.channels.values())
    total_channels = len(st.session_state.channels)
    loaded_channels = sum(1 for v in st.session_state.channels.values() if v.get("data") is not None)

    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("Total Subscribers", fmt_number(total_subs))
    kc2.metric("Total Channel Views", fmt_number(total_views_all))
    kc3.metric("Channels Tracked", total_channels)
    kc4.metric("Channels with Data", loaded_channels)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # Top performers across all channels
    all_video_rows = []
    for ch_name, info in st.session_state.channels.items():
        df = info.get("data")
        if df is not None and not df.empty:
            top5 = df.nlargest(5, "Views per Day").copy()
            top5["Channel"] = ch_name
            all_video_rows.append(top5)

    if all_video_rows:
        combined = pd.concat(all_video_rows, ignore_index=True)
        combined = combined.nlargest(10, "Views per Day")

        st.markdown("### 🏆 Top Performing Videos Right Now")
        st.caption("Ranked by Views per Day — best indicators of momentum.")
        disp = combined[["Channel", "Title", "Views per Day", "Views", "Like Rate %", "Published"]].copy()
        disp["Published"] = disp["Published"].dt.strftime("%Y-%m-%d")
        st.dataframe(disp, use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Quick wins: high comment rate, low view count (underexposed)
        st.markdown("### 💡 Quick Wins — High Engagement, Low Reach")
        st.caption("Videos with high comment rates but lower views — worth promoting.")
        qw = combined.nlargest(5, "Comment Rate %").nsmallest(3, "Views")
        if not qw.empty:
            for _, row in qw.iterrows():
                st.markdown(f'<div class="info-box">📌 <strong>{row["Channel"]}</strong> — {row["Title"][:80]} &nbsp;|&nbsp; {row["Comment Rate %"]:.2f}% comment rate, {fmt_number(int(row["Views"]))} views</div>', unsafe_allow_html=True)

    else:
        st.info("Refresh channel data to see the dashboard.")

# ══════════════════════════════════════════════
# TAB 2 — ALL CHANNELS OVERVIEW
# ══════════════════════════════════════════════
with TAB_OVERVIEW:
    st.markdown("## All Channels Overview")
    st.markdown("<br>", unsafe_allow_html=True)

    summary_rows = []
    for ch_name, info in st.session_state.channels.items():
        df = info.get("data")
        stats = info.get("channel_stats", {})
        avg_vpd = round(df["Views per Day"].mean(), 1) if df is not None and not df.empty else 0
        avg_views = int(df["Views"].mean()) if df is not None and not df.empty else 0
        summary_rows.append({
            "Channel": ch_name,
            "Subscribers": stats.get("subscribers", 0),
            "Total Views": stats.get("total_views", 0),
            "Videos Analyzed": len(df) if df is not None else 0,
            "Avg Views / Video": avg_views,
            "Avg Views / Day": avg_vpd,
            "Last Refreshed": info.get("last_refreshed", "Never"),
        })

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows).sort_values("Total Views", ascending=False)

        # Display with formatted numbers
        display_summary = summary_df.copy()
        display_summary["Subscribers"] = display_summary["Subscribers"].apply(fmt_number)
        display_summary["Total Views"] = display_summary["Total Views"].apply(fmt_number)
        display_summary["Avg Views / Video"] = display_summary["Avg Views / Video"].apply(fmt_number)
        st.dataframe(display_summary, use_container_width=True, hide_index=True)

        csv_bytes = summary_df.to_csv(index=False).encode()
        st.download_button("⬇ Export All Channels CSV", csv_bytes, "chamberlin_all_channels.csv", "text/csv")

        # Comparison bar chart
        if len(summary_rows) > 1:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Channel Comparison")
            fig = px.bar(
                summary_df,
                x="Channel",
                y="Subscribers",
                title="Subscribers by Channel",
                color="Subscribers",
                color_continuous_scale=["#330000", "#ff0000"],
            )
            fig.update_layout(**PLOTLY_DARK, showlegend=False)
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 3 — CHANNEL DETAIL
# ══════════════════════════════════════════════
with TAB_DETAIL:
    if not st.session_state.channels:
        st.info("Add channels to get started.")
        st.stop()

    # Channel selector
    selected = st.selectbox("Select Channel", list(st.session_state.channels.keys()), label_visibility="collapsed")
    info = st.session_state.channels[selected]
    ch_id = info["id"]

    col_h1, col_h2 = st.columns([6, 2])
    with col_h1:
        stats_preview = info.get("channel_stats", {})
        if stats_preview.get("channel_name"):
            st.markdown(f"## {stats_preview['channel_name']}")
        else:
            st.markdown(f"## {selected}")
        st.caption(f"Channel ID: `{ch_id}`  •  Last refreshed: {info.get('last_refreshed', 'Never')}")
    with col_h2:
        if st.button("🔄  Refresh This Channel", type="primary", use_container_width=True):
            with st.spinner("Fetching from YouTube..."):
                try:
                    df_new, stats_new = fetch_channel_data(API_KEY, ch_id)
                    st.session_state.channels[selected]["data"] = df_new
                    st.session_state.channels[selected]["channel_stats"] = stats_new
                    st.session_state.channels[selected]["last_refreshed"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    save_snapshot(selected, {"subscribers": stats_new["subscribers"], "total_views": stats_new["total_views"]})
                    save_data()
                    st.success("Refreshed!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    df = info.get("data")
    stats = info.get("channel_stats", {})

    if df is None or df.empty:
        st.info("Click **Refresh This Channel** to load data.")
        st.stop()

    # Key metrics
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Subscribers", fmt_number(stats.get("subscribers", 0)))
    m2.metric("Total Views", fmt_number(stats.get("total_views", 0)))
    m3.metric("Videos Analyzed", len(df))
    m4.metric("Avg Views / Video", fmt_number(int(df["Views"].mean())))
    m5.metric("Avg Views / Day", f"{df['Views per Day'].mean():.1f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Sub-tabs
    DT_VT, DT_CHARTS, DT_TIMING, DT_SERIES, DT_IDEAS, DT_NOTES = st.tabs([
        "📋  Video Table",
        "📊  Charts",
        "🕐  Upload Timing",
        "🎯  Content Series",
        "💡  Ideas",
        "📝  Notes",
    ])

    # ── Video Table ──
    with DT_VT:
        disp = df[["Title", "Published", "Views", "Views per Day", "Like Rate %", "Comment Rate %", "Likes", "Comments", "URL"]].copy()
        disp["Published"] = disp["Published"].dt.strftime("%Y-%m-%d")
        sort_col = st.selectbox("Sort by", ["Views", "Views per Day", "Like Rate %", "Comment Rate %", "Published"], index=0)
        disp = disp.sort_values(sort_col, ascending=False)
        st.dataframe(disp, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇  Export Channel CSV",
            df.to_csv(index=False).encode(),
            f"{selected.replace(' ','_')}_data.csv",
            "text/csv",
        )

    # ── Charts ──
    with DT_CHARTS:
        c1, c2 = st.columns(2)

        with c1:
            top10 = df.nlargest(10, "Views").sort_values("Views")
            fig_top = px.bar(
                top10,
                x="Views",
                y="Title",
                orientation="h",
                title="Top 10 Videos by Views",
                color="Views",
                color_continuous_scale=["#220000", "#ff0000"],
            )
            fig_top.update_layout(**PLOTLY_DARK, showlegend=False)
            fig_top.update_traces(marker_line_width=0)
            fig_top.update_yaxes(tickfont_size=11)
            st.plotly_chart(fig_top, use_container_width=True)

        with c2:
            top10_vpd = df.nlargest(10, "Views per Day").sort_values("Views per Day")
            fig_vpd = px.bar(
                top10_vpd,
                x="Views per Day",
                y="Title",
                orientation="h",
                title="Top 10 by Views / Day (Momentum)",
                color="Views per Day",
                color_continuous_scale=["#001122", "#0099ff"],
            )
            fig_vpd.update_layout(**PLOTLY_DARK, showlegend=False)
            fig_vpd.update_traces(marker_line_width=0)
            fig_vpd.update_yaxes(tickfont_size=11)
            st.plotly_chart(fig_vpd, use_container_width=True)

        # Views over time
        trend = df.sort_values("Published")
        fig_trend = px.line(
            trend,
            x="Published",
            y="Views",
            title="Views Over Time",
            markers=True,
        )
        fig_trend.update_traces(line_color="#ff0000", marker_color="#ff6666", marker_size=5)
        fig_trend.update_layout(**PLOTLY_DARK)
        st.plotly_chart(fig_trend, use_container_width=True)

        # Like + Comment rate scatter
        fig_scatter = px.scatter(
            df,
            x="Views",
            y="Like Rate %",
            size="Comments",
            color="Comment Rate %",
            hover_name="Title",
            title="Engagement Map (size = Comment count)",
            color_continuous_scale="Reds",
        )
        fig_scatter.update_layout(**PLOTLY_DARK)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ── Upload Timing ──
    with DT_TIMING:
        st.markdown("### Upload Schedule Optimizer")
        st.caption("Best days to post based on your historical performance.")

        day_avg = get_best_upload_day(df)
        if not day_avg.empty:
            best_day = day_avg.idxmax()
            best_views = day_avg.max()

            st.markdown(f'<div class="success-box">✅ Best day to upload: <strong>{best_day}</strong> — avg {fmt_number(int(best_views))} views per video</div>', unsafe_allow_html=True)

            fig_days = px.bar(
                x=day_avg.index,
                y=day_avg.values,
                title="Average Views by Upload Day",
                labels={"x": "Day of Week", "y": "Avg Views"},
                color=day_avg.values,
                color_continuous_scale=["#1a0000", "#ff0000"],
            )
            fig_days.update_layout(**PLOTLY_DARK, showlegend=False)
            fig_days.update_traces(marker_line_width=0)
            st.plotly_chart(fig_days, use_container_width=True)

        # Upload frequency
        st.markdown("### Upload Frequency")
        monthly = df.copy()
        monthly["Month"] = monthly["Published"].dt.to_period("M").astype(str)
        freq = monthly.groupby("Month").size().reset_index(name="Videos Posted")
        fig_freq = px.bar(freq, x="Month", y="Videos Posted", title="Videos Posted Per Month")
        fig_freq.update_traces(marker_color="#444", marker_line_width=0)
        fig_freq.update_layout(**PLOTLY_DARK)
        st.plotly_chart(fig_freq, use_container_width=True)

    # ── Content Series ──
    with DT_SERIES:
        st.markdown("### Content Series Tracker")
        st.caption("Identify which topics or series are performing best.")

        # Extract common phrases from titles (2-word patterns)
        title_words = []
        for title in df["Title"].tolist():
            words = re.findall(r"\b[A-Za-z]{3,}\b", title)
            title_words.extend([words[i] + " " + words[i+1] for i in range(len(words)-1)])

        stop2 = {"This Is", "That Is", "And The", "In The", "On The", "Of The", "To The", "Is A", "It Is", "You Are", "With The", "For The", "How To"}
        filtered_phrases = [p for p in title_words if p.title() not in stop2 and len(p) > 6]
        phrase_counts = Counter(filtered_phrases).most_common(15)

        if phrase_counts:
            phrase_df = pd.DataFrame(phrase_counts, columns=["Phrase / Topic", "Count"])
            # Map phrase to avg views
            def avg_views_for_phrase(phrase):
                mask = df["Title"].str.contains(re.escape(phrase), case=False, na=False)
                return df.loc[mask, "Views"].mean() if mask.any() else 0

            phrase_df["Avg Views"] = phrase_df["Phrase / Topic"].apply(avg_views_for_phrase).round(0).astype(int)
            phrase_df = phrase_df.sort_values("Avg Views", ascending=False)

            fig_series = px.scatter(
                phrase_df,
                x="Count",
                y="Avg Views",
                text="Phrase / Topic",
                title="Topic Frequency vs. Avg Views",
                color="Avg Views",
                color_continuous_scale="Reds",
                size="Count",
            )
            fig_series.update_traces(textposition="top center", textfont_size=10)
            fig_series.update_layout(**PLOTLY_DARK)
            st.plotly_chart(fig_series, use_container_width=True)

            st.dataframe(phrase_df, use_container_width=True, hide_index=True)
        else:
            st.info("Not enough title data for series analysis.")

    # ── Ideas ──
    with DT_IDEAS:
        st.markdown("### Video Ideas Generator")
        st.caption("Analyzes your top-performing titles to suggest new content directions.")

        if st.button("✨  Generate Ideas", type="primary"):
            with st.spinner("Analyzing channel niche..."):
                ideas_data = generate_ideas(selected, df)
                st.session_state.generated_ideas[selected] = ideas_data
                save_data()

        ideas = st.session_state.generated_ideas.get(selected, {})
        if ideas:
            st.markdown("**Detected Topics:**")
            tags_html = " ".join([f'<span style="background:#1a0000;border:1px solid #ff3333;color:#ff9999;padding:3px 10px;border-radius:20px;font-size:12px;margin:2px;display:inline-block">{t}</span>' for t in ideas.get("topics", [])])
            st.markdown(tags_html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("**Suggested Video Ideas:**")
            for idea in ideas.get("ideas", []):
                st.markdown(f'<div class="info-box">🎬  {idea}</div>', unsafe_allow_html=True)

            if ideas.get("inspiration"):
                st.markdown("<br>**Top videos that inspired these ideas:**")
                for t in ideas.get("inspiration", [])[:3]:
                    st.caption(f"• {t}")

    # ── Notes ──
    with DT_NOTES:
        st.markdown("### Team Notes")
        st.caption("Shared notes for this channel — saved automatically.")
        current_notes = st.session_state.notes.get(selected, "")
        new_notes = st.text_area("", value=current_notes, height=200, placeholder="Add notes, observations, or action items here...")
        if st.button("💾  Save Notes", type="primary"):
            st.session_state.notes[selected] = new_notes
            save_data()
            st.success("Notes saved.")

# ══════════════════════════════════════════════
# TAB 4 — GROWTH TRENDS
# ══════════════════════════════════════════════
with TAB_GROWTH:
    st.markdown("## Growth Trends")
    st.caption("Historical snapshots of subscriber and view growth over time. Data is saved each time you refresh a channel.")

    if not st.session_state.snapshots:
        st.info("No growth data yet. Refresh channels over time to build historical snapshots.")
    else:
        growth_channel = st.selectbox("Select Channel", list(st.session_state.snapshots.keys()), key="growth_ch")
        snap_data = st.session_state.snapshots.get(growth_channel, {})

        if snap_data:
            dates = sorted(snap_data.keys())
            subs_series = [snap_data[d].get("subscribers", 0) for d in dates]
            views_series = [snap_data[d].get("total_views", 0) for d in dates]

            snap_df = pd.DataFrame({"Date": dates, "Subscribers": subs_series, "Total Views": views_series})

            g1, g2 = st.columns(2)
            with g1:
                fig_sub_growth = px.line(snap_df, x="Date", y="Subscribers", title="Subscriber Growth", markers=True)
                fig_sub_growth.update_traces(line_color="#ff0000", marker_color="#ff6666")
                fig_sub_growth.update_layout(**PLOTLY_DARK)
                st.plotly_chart(fig_sub_growth, use_container_width=True)

            with g2:
                fig_view_growth = px.line(snap_df, x="Date", y="Total Views", title="Total Views Growth", markers=True)
                fig_view_growth.update_traces(line_color="#0099ff", marker_color="#66ccff")
                fig_view_growth.update_layout(**PLOTLY_DARK)
                st.plotly_chart(fig_view_growth, use_container_width=True)

            st.dataframe(snap_df.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.divider()
st.caption("Chamberlin Media Monitor  •  Built for your team  •  Data from YouTube Data API v3")
