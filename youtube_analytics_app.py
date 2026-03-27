import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import plotly.express as px
from collections import Counter
import re
from datetime import datetime

st.set_page_config(page_title="YouTube Multi-Channel Analytics", layout="wide")

st.title("YouTube Multi-Channel Analytics")

# API Key
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
    input_value = st.text_input("Channel URL, @handle, or Channel ID (UC...)", 
                                placeholder="https://www.youtube.com/@example or @example or UCxxxx")
    
    if st.button("Add Channel"):
        if not nickname or not input_value:
            st.sidebar.error("Please provide both nickname and channel info.")
        elif not api_key:
            st.sidebar.error("Please enter your YouTube API key in the sidebar.")
        else:
            try:
                youtube = build("youtube", "v3", developerKey=api_key)
                channel_id = resolve_to_channel_id(youtube, input_value.strip())
                st.session_state.channels[nickname] = {
                    "id": channel_id,
                    "data": None,
                    "last_refresh": None
                }
                st.sidebar.success(f"Added: {nickname}")
            except Exception as e:
                st.sidebar.error(f"Could not add channel: {str(e)}")

# Remove channels
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
    st.info("Add your channels in the sidebar.")
    st.stop()

# Main area
selected = st.selectbox("Select a channel", list(st.session_state.channels.keys()))
channel_info = st.session_state.channels[selected]
channel_id = channel_info["id"]

st.subheader(f"Channel: {selected}")
st.caption(f"Channel ID: {channel_id} | Last refreshed: {channel_info.get('last_refresh', 'Never')}")

def resolve_to_channel_id(youtube, value):
    """Convert URL, @handle, or direct ID to Channel ID"""
    if value.startswith("UC") and len(value) > 20:
        return value  # Already a Channel ID
    
    # Handle URL or @handle
    if "youtube.com" in value or value.startswith("@"):
        # Extract handle
        if "/@ " in value:
            handle = value.split("@")[-1].split("/")[0]
        elif value.startswith("@"):
            handle = value[1:]
        elif "/channel/" in value:
            return value.split("/channel/")[-1].split("/")[0]
        else:
            handle = value.split("/")[-1].lstrip("@")
        
        # Try forHandle (modern way)
        try:
            resp = youtube.channels().list(part="id", forHandle=handle).execute()
            if resp.get("items"):
                return resp["items"][0]["id"]
        except:
            pass
    
    # Fallback: search
    resp = youtube.search().list(part="snippet", q=value, type="channel", maxResults=1).execute()
    if resp.get("items"):
        return resp["items"][0]["snippet"]["channelId"]
    
    raise ValueError("Could not find channel. Try using the exact Channel ID (UC...) instead.")

if st.button("Refresh Data Now"):
    with st.spinner("Fetching latest public data from YouTube..."):
        try:
            youtube = build("youtube", "v3", developerKey=api_key)
            ch_resp = youtube.channels().list(part="contentDetails", id=channel_id).execute()
            uploads_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            
            videos = []
            next_page = None
            for _ in range(2):  # up to ~100 recent videos
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
    col1.metric("Total Videos Shown", len(df))
    col2.metric("Total Views", f"{df['Views'].sum():,}")
    col3.metric("Average Views per Video", f"{int(df['Views'].mean()):,}")

    tab1, tab2, tab3 = st.tabs(["Top Videos", "Views Trend", "Content Suggestions"])

    with tab1:
        top = df.nlargest(10, "Views")
        fig = px.bar(top, x="Views", y="Title", orientation="h", title="Top 10 Videos by Views")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top[["Title", "Published", "Views", "Likes", "Comments", "URL"]], use_container_width=True)

    with tab2:
        fig2 = px.line(df.sort_values("Published"), x="Published", y="Views", title="Views Over Time", markers=True)
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        if st.button("Generate Content Suggestions"):
            high = df[df["Views"] > df["Views"].quantile(0.7)] if len(df) > 10 else df
            high_keywords = []
            for title in high["Title"]:
                cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
                high_keywords.extend([w for w in cleaned.split() if len(w) > 3])
            common = Counter(high_keywords).most_common(8)
            
            st.write("Strong topics from your top videos:")
            for word, count in common[:6]:
                st.write(f"- {word}")
            
            st.write("\nSuggested new video ideas:")
            if common:
                top_word = common[0][0].title()
                st.write(f"1. {top_word} Tutorial - Step by Step")
                st.write(f"2. How We Improved {top_word}")
                st.write(f"3. Common Mistakes with {top_word}")
                st.write(f"4. {top_word} Tips for 2026")

else:
    st.info("Click 'Refresh Data Now' to load statistics for this channel.")

st.caption("Each channel analyzed separately • Public data via YouTube API")
