# youtube_analytics_app.py

import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# -------------------- CONFIG -------------------- #
st.set_page_config(page_title="YouTube Team Analytics", layout="wide", page_icon="📊")
st.markdown(
    """
    <style>
        body {background-color: #121212; color: #FFFFFF;}
        .stSidebar {background-color: #1F1F1F;}
        .stButton>button {background-color:#FF0000; color:white; border-radius:5px;}
        .stDataFrame th {background-color:#2C2C2C; color:white;}
        .stDataFrame td {background-color:#1E1E1E; color:white;}
        .stTextInput>div>input {background-color:#1E1E1E; color:white;}
        .stMarkdown {color:white;}
        .stSelectbox>div>div>div {background-color:#1E1E1E; color:white;}
        .stTextArea>div>textarea {background-color:#1E1E1E; color:white;}
    </style>
    """,
    unsafe_allow_html=True
)

DATA_FILE = "channels.json"

# -------------------- HELPER FUNCTIONS -------------------- #
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"channels": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def fetch_channel_data(youtube, channel_id):
    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )
    response = request.execute()
    if "items" not in response or not response["items"]:
        st.error("Invalid Channel ID or insufficient permissions.")
        return None
    item = response["items"][0]
    snippet = item["snippet"]
    stats = item["statistics"]
    return {
        "channel_id": channel_id,
        "title": snippet["title"],
        "subscribers": int(stats.get("subscriberCount", 0)),
        "views": int(stats.get("viewCount", 0)),
        "videos_count": int(stats.get("videoCount", 0))
    }

def fetch_videos(youtube, channel_id):
    videos = []
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=50,
        order="date"
    )
    response = request.execute()
    for item in response.get("items", []):
        if item["id"]["kind"] == "youtube#video":
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            videos.append({
                "video_id": video_id,
                "title": snippet["title"],
                "published": snippet["publishedAt"]
            })
    return videos

def fetch_video_stats(youtube, video_ids):
    stats_list = []
    for i in range(0, len(video_ids), 50):  # API limit 50 per call
        batch_ids = video_ids[i:i+50]
        request = youtube.videos().list(
            part="statistics",
            id=",".join(batch_ids)
        )
        response = request.execute()
        for item in response.get("items", []):
            stats = item["statistics"]
            stats_list.append({
                "video_id": item["id"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0))
            })
    return stats_list

def generate_video_ideas(channel_name, titles):
    # Very simple niche detection for demo
    niche = "General"
    name_lower = channel_name.lower()
    if "kids" in name_lower or any("kids" in t.lower() for t in titles):
        niche = "Kids Content"
    elif "gaming" in name_lower or any("game" in t.lower() for t in titles):
        niche = "Gaming"
    elif "edu" in name_lower or any("learn" in t.lower() for t in titles):
        niche = "Education"
    # Generate 5 ideas
    return [f"{niche} Video Idea #{i+1}" for i in range(5)]

def format_number(n):
    return f"{n:,}"

# -------------------- LOAD & SAVE DATA -------------------- #
data = load_data()
if "channels_data" not in st.session_state:
    st.session_state.channels_data = {}

# -------------------- SIDEBAR -------------------- #
st.sidebar.header("YouTube Team Analytics")
api_key = st.sidebar.text_input("YouTube Data API Key", type="password")
st.sidebar.markdown("---")
st.sidebar.subheader("Manage Channels")

# Add channel
new_channel_id = st.sidebar.text_input("Add Channel by ID")
if st.sidebar.button("Add Channel") and new_channel_id:
    if not api_key:
        st.sidebar.error("Enter API Key first!")
    else:
        youtube = build("youtube", "v3", developerKey=api_key)
        with st.spinner("Fetching channel data..."):
            channel_data = fetch_channel_data(youtube, new_channel_id)
        if channel_data:
            data["channels"].append(channel_data)
            save_data(data)
            st.sidebar.success(f"Added {channel_data['title']}")

# List channels with remove
for ch in data["channels"]:
    col1, col2 = st.sidebar.columns([3,1])
    col1.markdown(f"{ch['title']}")
    if col2.button("Remove", key=ch["channel_id"]):
        data["channels"] = [c for c in data["channels"] if c["channel_id"] != ch["channel_id"]]
        save_data(data)
        st.experimental_rerun()

# -------------------- MAIN APP -------------------- #
tabs = ["All Channels Overview", "Channel Detail"]
selected_tab = st.sidebar.radio("Navigation", tabs)

if selected_tab == "All Channels Overview":
    st.title("All Channels Overview")
    table_data = []
    for ch in data["channels"]:
        table_data.append({
            "Channel Name": ch["title"],
            "Subscribers": format_number(ch["subscribers"]),
            "Total Views": format_number(ch["views"]),
            "Videos Analyzed": ch.get("videos_count", 0),
            "Avg Views/Video": format_number(int(ch["views"]/max(1,ch.get("videos_count",1))))
        })
    df = pd.DataFrame(table_data)
    st.dataframe(df)
    st.download_button("Export CSV", df.to_csv(index=False), "channels_overview.csv")

elif selected_tab == "Channel Detail":
    st.title("Channel Detail")
    channel_options = {ch["title"]: ch["channel_id"] for ch in data["channels"]}
    if not channel_options:
        st.info("Add a channel first in the sidebar.")
    else:
        selected_channel_name = st.selectbox("Select Channel", list(channel_options.keys()))
        channel_id = channel_options[selected_channel_name]
        youtube = build("youtube", "v3", developerKey=api_key)
        ch_data = next(ch for ch in data["channels"] if ch["channel_id"] == channel_id)

        # Metrics Cards
        st.subheader(f"{ch_data['title']} (ID: {ch_data['channel_id']})")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Subscribers", format_number(ch_data["subscribers"]))
        col2.metric("Total Views", format_number(ch_data["views"]))
        col3.metric("Videos Analyzed", ch_data.get("videos_count",0))
        avg_views = int(ch_data["views"]/max(1,ch_data.get("videos_count",1)))
        col4.metric("Avg Views/Video", format_number(avg_views))

        # Fetch video details
        with st.spinner("Fetching videos..."):
            videos = fetch_videos(youtube, channel_id)
            video_ids = [v["video_id"] for v in videos]
            stats = fetch_video_stats(youtube, video_ids)
            # Merge stats into videos
            for v in videos:
                s = next((x for x in stats if x["video_id"]==v["video_id"]), {})
                v.update(s)
                pub_date = datetime.fromisoformat(v["published"].replace("Z","+00:00"))
                v["Views/Day"] = int(v.get("views",0)/max(1,(datetime.utcnow() - pub_date).days))
                v["Like Rate %"] = round(v.get("likes",0)/max(1,v.get("views",1))*100,2)
                v["Comment Rate %"] = round(v.get("comments",0)/max(1,v.get("views",1))*100,2)
                v["Published Date"] = pub_date.strftime("%Y-%m-%d")

        video_df = pd.DataFrame(videos)[["title","Published Date","views","Views/Day","Like Rate %","Comment Rate %"]]
        video_df.rename(columns={
            "title":"Title",
            "views":"Views",
            "Views/Day":"Views per Day"
        }, inplace=True)

        st.subheader("Videos Table")
        st.dataframe(video_df)
        st.download_button("Export Videos CSV", video_df.to_csv(index=False), "videos.csv")

        # Performance Charts
        st.subheader("Performance Charts")
        top_videos = sorted(videos, key=lambda x: x.get("views",0), reverse=True)[:10]
        fig, ax = plt.subplots()
        ax.barh([v["title"] for v in top_videos][::-1], [v["views"] for v in top_videos][::-1], color="#FF0000")
        ax.set_xlabel("Views")
        ax.set_ylabel("Top 10 Videos")
        st.pyplot(fig)

        # Upload Timing
        st.subheader("Upload Timing")
        day_views = {}
        for v in videos:
            day = datetime.fromisoformat(v["published"].replace("Z","+00:00")).strftime("%A")
            day_views[day] = day_views.get(day, []) + [v.get("views",0)]
        avg_day_views = {k: sum(vs)/len(vs) for k,vs in day_views.items()}
        fig2, ax2 = plt.subplots()
        ax2.bar(avg_day_views.keys(), avg_day_views.values(), color="#FF0000")
        ax2.set_ylabel("Average Views")
        st.pyplot(fig2)
        st.markdown("*Note: Optimal upload days may vary. Typically mid-week performs better.*")

        # Grok Video Ideas
        st.subheader("Grok Video Ideas")
        if "ideas" not in ch_data:
            ch_data["ideas"] = []
        if st.button("Generate Ideas"):
            titles_list = [v["title"] for v in videos]
            ch_data["ideas"] = generate_video_ideas(ch_data["title"], titles_list)
            save_data(data)
        if ch_data["ideas"]:
            st.write(ch_data["ideas"])

        # Team Notes
        st.subheader("Team Notes")
        if "notes" not in ch_data:
            ch_data["notes"] = ""
        notes = st.text_area("Write notes for this channel", value=ch_data["notes"])
        if st.button("Save Notes"):
            ch_data["notes"] = notes
            save_data(data)
            st.success("Notes saved!")
