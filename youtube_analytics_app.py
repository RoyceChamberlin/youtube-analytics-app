import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import plotly.express as px
from collections import Counter
import re
import json
import os
from datetime import datetime
import time

st.set_page_config(page_title="YouTube Multi-Channel Live Analytics", layout="wide")
st.title("🎥 Multi-Channel YouTube Live Analytics + Smart Suggestions")

# ==================== API KEY ====================
if "YOUTUBE" in st.secrets:
    API_KEY = st.secrets["YOUTUBE"]["API_KEY"]
    st.sidebar.success("✅ API key loaded securely")
else:
    API_KEY = st.sidebar.text_input("YouTube Data API Key", type="password")

st.sidebar.header("📺 Add Channels (URL or @handle)")

if "channels" not in st.session_state:
    st.session_state.channels = {}

# Add new channel by URL
with st.sidebar.expander("➕ Add Channel"):
    name = st.text_input("Channel Nickname (e.g. Main Channel)")
    url = st.text_input("YouTube Channel URL or @handle", placeholder="https://www.youtube.com/@yourchannel or @yourchannel")
    if st.button("Add Channel") and name and url and API_KEY:
        # Resolve URL to Channel ID
        try:
            youtube = build("youtube", "v3", developerKey=API_KEY)
            channel_id = get_channel_id(youtube, url)
            st.session_state.channels[name] = {"id": channel_id, "data": None, "last_refresh": None}
            st.success(f"✅ Added {name} (ID: {channel_id})")
        except Exception as e:
            st.error(f"Could not resolve URL: {e}")

# Helper function to convert URL/@handle to Channel ID
def get_channel_id(youtube, url_or_handle):
    handle = url_or_handle.strip()
    if handle.startswith("https://"):
        # Extract handle or ID from full URL
        if "/@ " in handle:
            handle = handle.split("@")[-1].split("/")[0]
        elif "/channel/" in handle:
            return handle.split("/channel/")[-1].split("/")[0]
        elif "/c/" in handle or "/user/" in handle:
            # Fallback - search by name (less accurate)
            search_resp = youtube.search().list(part="snippet", q=handle.split("/")[-1], type="channel", maxResults=1).execute()
            return search_resp["items"][0]["snippet"]["channelId"]
    if handle.startswith("@"):
        handle = handle[1:]
    # Use forHandle (best for @handles)
    resp = youtube.channels().list(part="id", forHandle=handle).execute()
    if resp["items"]:
        return resp["items"][0]["id"]
    raise ValueError("Channel not found")

# List & remove channels
for name in list(st.session_state.channels.keys()):
    col1, col2 = st.sidebar.columns([4, 1])
    col1.write(f"• {name}")
    if col2.button("🗑", key=f"rm_{name}"):
        del st.session_state.channels[name]
        st.rerun()

if not API_KEY:
    st.warning("👆 Enter your YouTube API key in the sidebar")
    st.stop()

if not st.session_state.channels:
    st.info("Add your first channel using a URL or @handle above 👆")
    st.stop()

# ==================== MAIN APP ====================
selected_channel = st.selectbox("Select Channel", options=list(st.session_state.channels.keys()))
channel_info = st.session_state.channels[selected_channel]
channel_id = channel_info["id"]

st.subheader(f"📊 Live Analysis for: **{selected_channel}**")
st.caption(f"Channel ID: {channel_id} | Last refreshed: {channel_info.get('last_refresh', 'Never')}")

# Live auto-refresh toggle
live_mode = st.checkbox("🔴 Enable Live Updates (auto-refresh every 10 minutes)", value=False)

# Manual refresh button
if st.button(f"🔄 Refresh Data Now for {selected_channel}", type="primary") or channel_info["data"] is None:
    refresh_data(selected_channel, channel_id)

# Auto-refresh loop
if live_mode:
    st.info("🔴 Live mode active — refreshing every 10 minutes")
    if st.button("Stop Live Mode"):
        live_mode = False
    else:
        time.sleep(600)  # 10 minutes
        st.rerun()

# ==================== REFRESH FUNCTION ====================
def refresh_data(name, channel_id):
    with st.spinner("Fetching latest public data from YouTube..."):
        youtube = build("youtube", "v3", developerKey=API_KEY)
        
        # Get channel + uploads playlist
        channel_resp = youtube.channels().list(part="contentDetails", id=channel_id).execute()
        uploads_id = channel_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # Fetch up to 100 recent videos
        videos = []
        next_page = None
        for _ in range(2):  # 100 videos max
            pl_resp = youtube.playlistItems().list(
                part="contentDetails", playlistId=uploads_id, maxResults=50, pageToken=next_page
            ).execute()
            
            video_ids = [item["contentDetails"]["videoId"] for item in pl_resp["items"]]
            
            vid_resp = youtube.videos().list(part="snippet,statistics", id=",".join(video_ids)).execute()
            
            for item in vid_resp["items"]:
                stats = item["statistics"]
                snippet = item["snippet"]
                videos.append({
                    "Title": snippet["title"],
                    "Published": snippet["publishedAt"][:10],
                    "Views": int(stats.get("viewCount", 0)),
                    "Likes": int(stats.get("likeCount", 0)),
                    "Comments": int(stats.get("commentCount", 0)),
                    "Video ID": item["id"],
                    "URL": f"https://youtu.be/{item['id']}"
                })
            
            next_page = pl_resp.get("nextPageToken")
            if not next_page: break
        
        df = pd.DataFrame(videos)
        df["Published"] = pd.to_datetime(df["Published"])
        df = df.sort_values("Published", ascending=False)
        
        st.session_state.channels[name]["data"] = df
        st.session_state.channels[name]["last_refresh"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        st.success("✅ Data refreshed!")
        st.rerun()

# Show results if data exists
df = channel_info.get("data")
if df is not None and not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Videos", len(df))
    col2.metric("Total Views", f"{df['Views'].sum():,}")
    col3.metric("Avg Views/Video", f"{int(df['Views'].mean()):,}")
    col4.metric("Avg Likes", f"{int(df['Likes'].mean()):,}")

    tab1, tab2, tab3, tab4 = st.tabs(["Top Videos", "Trend", "High vs Low", "💡 Smart Suggestions"])

    with tab1:
        top = df.nlargest(10, "Views")
        fig = px.bar(top, x="Views", y="Title", orientation="h", title="Top 10 Videos")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top[["Title", "Published", "Views", "Likes", "Comments", "URL"]], use_container_width=True)

    with tab2:
        fig2 = px.line(df.sort_values("Published"), x="Published", y="Views", title="Views Over Time", markers=True)
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        high = df[df["Views"] > df["Views"].quantile(0.75)]
        low = df[df["Views"] < df["Views"].quantile(0.25)]
        st.write("**High-Performing** (top 25%)")
        st.dataframe(high[["Title", "Views", "Likes", "Comments"]].head(8))
        st.write("**Low-Performing** (bottom 25%)")
        st.dataframe(low[["Title", "Views", "Likes", "Comments"]].head(8))

    with tab4:
        if st.button("Generate Fresh Content Suggestions"):
            with st.spinner("Analyzing your best & worst videos..."):
                high_titles = high["Title"].tolist()
                low_titles = low["Title"].tolist()
                
                def top_keywords(titles):
                    words = [w for title in titles for w in re.sub(r'[^a-zA-Z0-9\s]', '', title.lower()).split() if len(w) > 3]
                    return Counter(words).most_common(15)
                
                high_k = top_keywords(high_titles)
                low_k = top_keywords(low_titles)
                
                st.subheader("✅ What’s Working (Double Down)")
                for word, count in high_k[:6]:
                    st.write(f"• **{word}** appears in your top videos — keep using it!")
                
                st.subheader("🚫 What to Avoid")
                for word, count in low_k[:4]:
                    st.write(f"• **{word}** is in your weaker videos")
                
                st.subheader("🚀 Ready-to-Use New Video Ideas")
                st.write("1. " + high_k[0][0].title() + " Tutorial – Step-by-Step (2026 Update)")
                st.write("2. Behind the Scenes of my " + high_titles[0][:40] + "...")
                st.write("3. Top 10 Mistakes with " + high_k[1][0].title())
                st.write("4. " + high_k[0][0].title() + " vs " + low_k[0][0].title() + " – Which Wins?")
                st.info("These ideas are based 100% on **your own data** — they have the highest chance of performing well!")

else:
    st.info("Click 'Refresh Data Now' to load stats")

st.caption("App updated just for you • Live public data from YouTube • Suggestions powered by your real performance")
