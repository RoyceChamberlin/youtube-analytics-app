import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import plotly.express as px
from collections import Counter
import re
import json
import os
from datetime import datetime

st.set_page_config(page_title="YouTube Team Analytics", layout="wide", initial_sidebar_state="expanded")

# Sleek professional dark theme
st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; color: #e0e0e0; }
    .sidebar .sidebar-content { background-color: #111111; border-right: 1px solid #333; }
    h1 { color: #ffffff; font-weight: 600; }
    h2, h3 { color: #ffffff; }
    .stButton>button { background-color: #ff0000; color: white; border: none; border-radius: 6px; padding: 8px 16px; }
    .stButton>button:hover { background-color: #cc0000; }
    .metric-container { background-color: #1f1f1f; padding: 20px; border-radius: 10px; border: 1px solid #333; }
    .stDataFrame { background-color: #1a1a1a; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("YouTube Team Analytics")

# Sidebar
st.sidebar.header("Settings")
API_KEY = st.sidebar.text_input("YouTube Data API Key", type="password")

st.sidebar.header("Manage Channels")

if "channels" not in st.session_state:
    st.session_state.channels = {}
if "notes" not in st.session_state:
    st.session_state.notes = {}
if "generated_ideas" not in st.session_state:
    st.session_state.generated_ideas = {}

# Load data
if os.path.exists("channels.json"):
    try:
        with open("channels.json", "r") as f:
            loaded = json.load(f)
            for k, v in loaded.items():
                df = pd.read_json(v["data"]) if v.get("data") else None
                if df is not None and not df.empty:
                    df["Published"] = pd.to_datetime(df["Published"], errors='coerce')
                st.session_state.channels[k] = {"id": v["id"], "data": df, "channel_stats": v.get("channel_stats", {})}
                st.session_state.notes[k] = v.get("notes", "")
                st.session_state.generated_ideas[k] = v.get("ideas", "")
    except:
        pass

# Add channel
with st.sidebar.expander("Add Channel"):
    name = st.text_input("Channel Nickname")
    channel_id = st.text_input("Channel ID (UCxxxx...)")
    if st.button("Add Channel") and name and channel_id and API_KEY:
        st.session_state.channels[name] = {"id": channel_id.strip(), "data": None, "channel_stats": {}}
        st.session_state.notes[name] = ""
        st.session_state.generated_ideas[name] = ""
        st.sidebar.success(f"Added: {name}")

# List channels with clean remove
if st.session_state.channels:
    st.sidebar.write("**Your Channels**")
    for name in list(st.session_state.channels.keys()):
        col1, col2 = st.sidebar.columns([5, 1])
        col1.write(name)
        if col2.button("Remove", key=f"rm_{name}"):
            if name in st.session_state.channels:
                del st.session_state.channels[name]
            if name in st.session_state.notes:
                del st.session_state.notes[name]
            if name in st.session_state.generated_ideas:
                del st.session_state.generated_ideas[name]
            st.rerun()

if not API_KEY:
    st.warning("Please enter your YouTube Data API key in the sidebar.")
    st.stop()

if not st.session_state.channels:
    st.info("Add your channels using the sidebar.")
    st.stop()

# Tabs
tab_all, tab_detail = st.tabs(["📊 All Channels Overview", "🔍 Channel Detail"])

with tab_all:
    st.subheader("All Channels Summary")
    summary_data = []
    for name, info in st.session_state.channels.items():
        df = info.get("data")
        stats = info.get("channel_stats", {})
        summary_data.append({
            "Channel": name,
            "Subscribers": f"{stats.get('subscribers', 0):,}",
            "Total Views": f"{stats.get('total_views', 0):,}",
            "Videos Analyzed": len(df) if df is not None else 0,
            "Avg Views/Video": f"{int(df['Views'].mean()):,}" if df is not None and not df.empty else "0",
        })
    summary_df = pd.DataFrame(summary_data)
    if not summary_df.empty:
        st.dataframe(summary_df.sort_values(by="Total Views", ascending=False), use_container_width=True, hide_index=True)
        csv = summary_df.to_csv(index=False).encode()
        st.download_button("Export All Channels (CSV)", csv, "all_channels.csv", "text/csv")

with tab_detail:
    selected = st.selectbox("Select Channel", list(st.session_state.channels.keys()))
    info = st.session_state.channels[selected]
    channel_id = info["id"]

    st.subheader(f"Channel: **{selected}**")
    st.caption(f"ID: {channel_id}")

    if st.button("Refresh Data for This Channel", type="primary") or info.get("data") is None:
        with st.spinner("Fetching data from YouTube..."):
            youtube = build("youtube", "v3", developerKey=API_KEY)
            ch_resp = youtube.channels().list(part="snippet,statistics,contentDetails", id=channel_id).execute()
            ch = ch_resp["items"][0]
            subs = int(ch["statistics"].get("subscriberCount", 0))
            total_views = int(ch["statistics"].get("viewCount", 0))
            uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]

            videos = []
            next_page = None
            for _ in range(2):
                pl = youtube.playlistItems().list(part="contentDetails", playlistId=uploads_id, maxResults=50, pageToken=next_page).execute()
                video_ids = [item["contentDetails"]["videoId"] for item in pl["items"]]
                vid_resp = youtube.videos().list(part="snippet,statistics", id=",".join(video_ids)).execute()
                for item in vid_resp["items"]:
                    s = item["statistics"]
                    sn = item["snippet"]
                    videos.append({
                        "Title": sn["title"],
                        "Published": sn["publishedAt"][:10],
                        "Views": int(s.get("viewCount", 0)),
                        "Likes": int(s.get("likeCount", 0)),
                        "Comments": int(s.get("commentCount", 0)),
                        "URL": f"https://youtu.be/{item['id']}"
                    })
                next_page = pl.get("nextPageToken")
                if not next_page: break

            df = pd.DataFrame(videos)
            if not df.empty:
                df["Published"] = pd.to_datetime(df["Published"])
                df = df.sort_values("Published", ascending=False)
                df["Days Since Publish"] = (datetime.now() - df["Published"]).dt.days
                df["Views per Day"] = (df["Views"] / df["Days Since Publish"].replace(0, 1)).round(1)
                df["Like Rate %"] = (df["Likes"] / df["Views"].replace(0, 1) * 100).round(2)
                df["Comment Rate %"] = (df["Comments"] / df["Views"].replace(0, 1) * 100).round(2)

            st.session_state.channels[selected]["data"] = df
            st.session_state.channels[selected]["channel_stats"] = {"subscribers": subs, "total_views": total_views}

            # Save
            save_data = {k: {"id": v["id"], "data": v["data"].to_json() if v["data"] is not None else None, "channel_stats": v.get("channel_stats", {}), "notes": st.session_state.notes.get(k, ""), "ideas": st.session_state.generated_ideas.get(k, "")} for k, v in st.session_state.channels.items()}
            with open("channels.json", "w") as f:
                json.dump(save_data, f)
            st.success("Data refreshed successfully")

    df = info.get("data")
    stats = info.get("channel_stats", {})

    if df is not None and not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Subscribers", f"{stats.get('subscribers', 0):,}")
        col2.metric("Total Views", f"{stats.get('total_views', 0):,}")
        col3.metric("Videos", len(df))
        col4.metric("Avg Views/Video", f"{int(df['Views'].mean()):,}")

        tabs = st.tabs(["Video Table", "Charts", "Upload Timing", "Grok Ideas", "Team Notes"])

        with tabs[0]:
            disp = df[["Title", "Published", "Views", "Views per Day", "Like Rate %", "Comment Rate %", "URL"]].copy()
            disp["Published"] = disp["Published"].dt.strftime("%Y-%m-%d")
            st.dataframe(disp.sort_values("Views", ascending=False), use_container_width=True, hide_index=True)
            st.download_button("Export CSV", df.to_csv(index=False).encode(), f"{selected}.csv", "text/csv")

        with tabs[1]:
            top = df.nlargest(10, "Views")
            st.plotly_chart(px.bar(top, x="Views", y="Title", orientation="h", title="Top 10 Videos"), use_container_width=True)
            st.plotly_chart(px.line(df.sort_values("Published"), x="Published", y="Views", title="Views Trend", markers=True), use_container_width=True)

        with tabs[2]:
            temp = df.copy()
            temp["Day of Week"] = temp["Published"].dt.day_name()
            st.bar_chart(temp.groupby("Day of Week")["Views"].mean())

        with tabs[3]:
            st.write("**Grok Video Ideas** – based on this channel's actual content")
            if st.button("Generate Ideas", type="primary"):
                with st.spinner("Analyzing channel niche and performance..."):
                    all_titles = " | ".join(df["Title"].tolist())
                    niche = (selected + " " + all_titles).lower()
                    words = re.findall(r'\b[a-z]{4,}\b', niche)
                    common = Counter(words).most_common(8)
                    top = [w[0] for w in common if len(w[0]) > 3][:6]

                    ideas_list = [
                        f"1. Fun {top[0].title()} Storytime for Kids",
                        f"2. Learning {top[1].title()} with Songs and Games",
                        f"3. {top[2].title()} vs {top[3].title()} - Which One Wins?",
                        f"4. Easy {top[4].title()} Activities for Little Ones",
                        f"5. Daily {top[0].title()} Routine Kids Will Love"
                    ]

                    st.session_state.generated_ideas[selected] = {"topics": top, "ideas": ideas_list}

            if selected in st.session_state.generated_ideas and st.session_state.generated_ideas[selected]:
                data = st.session_state.generated_ideas[selected]
                st.write("**Detected Topics:**", ", ".join(data.get("topics", [])))
                st.write("**Suggested Videos:**")
                for idea in data.get("ideas", []):
                    st.write(idea)

        with tabs[4]:
            notes = st.text_area("Team Notes", value=st.session_state.notes.get(selected, ""), height=180)
            if st.button("Save Notes"):
                st.session_state.notes[selected] = notes
                # Save
                save_data = {k: {"id": v["id"], "data": v["data"].to_json() if v["data"] is not None else None, "channel_stats": v.get("channel_stats", {}), "notes": st.session_state.notes.get(k, ""), "ideas": st.session_state.generated_ideas.get(k, "")} for k, v in st.session_state.channels.items()}
                with open("channels.json", "w") as f:
                    json.dump(save_data, f)
                st.success("Notes saved")

    else:
        st.info("Click the Refresh button above to load data for this channel.")

st.caption("YouTube Team Analytics • Clean & useful for improving video performance")
