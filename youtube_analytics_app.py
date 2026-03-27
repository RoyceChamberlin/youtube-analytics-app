import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import plotly.express as px
from collections import Counter
import re
from datetime import datetime

st.set_page_config(page_title="YouTube Channel Analytics", layout="wide")

st.title("YouTube Multi-Channel Analytics")

# API Key handling
if "YOUTUBE" in st.secrets:
    api_key = st.secrets["YOUTUBE"]["API_KEY"]
else:
    api_key = st.sidebar.text_input("YouTube Data API Key", type="password")

st.sidebar.header("Channels")

if "channels" not in st.session_state:
    st.session_state.channels = {}

# Add channel section
with st.sidebar.expander("Add New Channel"):
    nickname = st.text_input("Channel Nickname")
    channel_input = st.text_input("YouTube Channel URL or @handle", 
                                  placeholder="https://www.youtube.com/@example or @example")
    
    if st.button("Add Channel"):
        if not nickname or not channel_input:
            st.sidebar.error("Please fill in both nickname and URL/handle")
        elif not api_key:
            st.sidebar.error("Please provide your YouTube API key")
        else:
            try:
                youtube = build("youtube", "v3", developerKey=api_key)
                channel_id = resolve_channel_id(youtube, channel_input)
                st.session_state.channels[nickname] = {
                    "id": channel_id,
                    "data": None,
                    "last_refresh": None
                }
                st.sidebar.success(f"Channel added: {nickname}")
            except Exception as e:
                st.sidebar.error(f"Error adding channel: {str(e)}")

# List existing channels with remove option
for name in list(st.session_state.channels.keys()):
    col1, col2 = st.sidebar.columns([4, 1])
    col1.write(name)
    if col2.button("Remove", key=f"remove_{name}"):
        del st.session_state.channels[name]
        st.rerun()

if not api_key:
    st.warning("Enter your YouTube Data API key in the sidebar to continue.")
    st.stop()

if not st.session_state.channels:
    st.info("Add at least one channel using the sidebar.")
    st.stop()

# Main area
selected = st.selectbox("Select channel to analyze", list(st.session_state.channels.keys()))
channel_info = st.session_state.channels[selected]
channel_id = channel_info["id"]

st.subheader(f"Channel: {selected}")
st.caption(f"Channel ID: {channel_id} | Last refreshed: {channel_info.get('last_refresh', 'Never')}")

def resolve_channel_id(youtube, input_str):
    input_str = input_str.strip()
    if input_str.startswith("http"):
        # Extract handle or ID from URL
        if "/@ " in input_str:
            handle = input_str.split("@")[-1].split("/")[0]
        elif "/channel/" in input_str:
            return input_str.split("/channel/")[-1].split("/")[0]
        else:
            handle = input_str.split("/")[-1]
    else:
        handle = input_str.lstrip("@")
    
    # Try forHandle first (best for @handles)
    try:
        resp = youtube.channels().list(part="id", forHandle=handle).execute()
        if resp.get("items"):
            return resp["items"][0]["id"]
    except:
        pass
    
    # Fallback: search by name
    resp = youtube.search().list(part="snippet", q=handle, type="channel", maxResults=1).execute()
    if resp.get("items"):
        return resp["items"][0]["snippet"]["channelId"]
    raise ValueError("Could not find channel. Check the URL or handle.")

if st.button("Refresh Data Now"):
    with st.spinner("Fetching latest public data..."):
        try:
            youtube = build("youtube", "v3", developerKey=api_key)
            # Get uploads playlist
            ch_resp = youtube.channels().list(part="contentDetails", id=channel_id).execute()
            uploads_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            
            # Fetch videos
            videos = []
            next_page = None
            for _ in range(2):  # up to ~100 videos
                pl_resp = youtube.playlistItems().list(
                    part="contentDetails", 
                    playlistId=uploads_id, 
                    maxResults=50, 
                    pageToken=next_page
                ).execute()
                
                if not pl_resp.get("items"):
                    break
                    
                video_ids = [item["contentDetails"]["videoId"] for item in pl_resp["items"]]
                vid_resp = youtube.videos().list(
                    part="snippet,statistics", 
                    id=",".join(video_ids)
                ).execute()
                
                for item in vid_resp["items"]:
                    stats = item["statistics"]
                    snippet = item["snippet"]
                    videos.append({
                        "Title": snippet["title"],
                        "Published": snippet["publishedAt"][:10],
                        "Views": int(stats.get("viewCount", 0)),
                        "Likes": int(stats.get("likeCount", 0)),
                        "Comments": int(stats.get("commentCount", 0)),
                        "URL": f"https://youtu.be/{item['id']}"
                    })
                
                next_page = pl_resp.get("nextPageToken")
                if not next_page:
                    break
            
            df = pd.DataFrame(videos)
            if not df.empty:
                df["Published"] = pd.to_datetime(df["Published"])
                df = df.sort_values("Published", ascending=False)
            
            st.session_state.channels[selected]["data"] = df
            st.session_state.channels[selected]["last_refresh"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.success("Data refreshed successfully.")
            st.rerun()
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")

# Display results
df = channel_info.get("data")
if df is not None and not df.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Videos", len(df))
    col2.metric("Total Views", f"{df['Views'].sum():,}")
    col3.metric("Average Views per Video", f"{int(df['Views'].mean()):,}")

    tab1, tab2, tab3 = st.tabs(["Top Videos", "Performance Trend", "Content Suggestions"])

    with tab1:
        top_videos = df.nlargest(10, "Views")
        fig = px.bar(top_videos, x="Views", y="Title", orientation="h", title="Top 10 Videos by Views")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top_videos[["Title", "Published", "Views", "Likes", "Comments", "URL"]], use_container_width=True)

    with tab2:
        sorted_df = df.sort_values("Published")
        fig2 = px.line(sorted_df, x="Published", y="Views", title="Views Over Time", markers=True)
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        if st.button("Generate Content Suggestions"):
            with st.spinner("Analyzing your video performance..."):
                high = df[df["Views"] > df["Views"].quantile(0.7)]
                low = df[df["Views"] < df["Views"].quantile(0.3)]
                
                def extract_keywords(titles):
                    words = []
                    for t in titles:
                        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', t.lower())
                        words.extend([w for w in cleaned.split() if len(w) > 3])
                    return Counter(words).most_common(10)
                
                high_keywords = extract_keywords(high["Title"].tolist())
                
                st.write("**Strong performing topics (double down on these):**")
                for word, count in high_keywords[:6]:
                    st.write(f"- {word}")
                
                st.write("\n**Suggested new video ideas based on your best content:**")
                if high_keywords:
                    top_word = high_keywords[0][0].title()
                    st.write(f"1. {top_word} Tutorial - Complete Guide (2026)")
                    st.write(f"2. How I Improved My {top_word} Results")
                    st.write(f"3. Common Mistakes with {top_word} (And How to Fix Them)")
                    st.write(f"4. {top_word} vs Traditional Methods - Which Wins?")
                
                st.info("These suggestions are generated from your own video performance data.")

else:
    st.info("Click 'Refresh Data Now' to load statistics for this channel.")

st.caption("Public data from YouTube Data API • Suggestions based on your channel performance")
