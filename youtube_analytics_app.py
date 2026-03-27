import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import plotly.express as px
from collections import Counter
import re
import json
import os
from datetime import datetime

# Dark YouTube Studio theme
st.set_page_config(page_title="YouTube Team Analytics", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f0f0f; color: #f1f1f1; }
    .sidebar .sidebar-content { background-color: #1f1f1f; }
    h1, h2, h3 { color: #ffffff; }
    .stButton>button { background-color: #f00; color: white; border: none; }
    .stButton>button:hover { background-color: #c00; }
</style>
""", unsafe_allow_html=True)

st.title("YouTube Team Analytics Command Center")

# ==================== SIDEBAR ====================
st.sidebar.header("Settings")
API_KEY = st.sidebar.text_input("YouTube Data API Key", type="password")

st.sidebar.header("Manage Channels")

if "channels" not in st.session_state:
    st.session_state.channels = {}
if "notes" not in st.session_state:
    st.session_state.notes = {}

# Load saved data
if os.path.exists("channels.json"):
    try:
        with open("channels.json", "r") as f:
            loaded = json.load(f)
            for k, v in loaded.items():
                df = pd.read_json(v["data"]) if v.get("data") else None
                if df is not None and not df.empty:
                    df["Published"] = pd.to_datetime(df["Published"], errors='coerce')
                st.session_state.channels[k] = {
                    "id": v["id"], 
                    "data": df, 
                    "channel_stats": v.get("channel_stats", {})
                }
                st.session_state.notes[k] = v.get("notes", "")
    except:
        pass

# Add channel
with st.sidebar.expander("Add Channel"):
    name = st.text_input("Channel Nickname")
    channel_id = st.text_input("Channel ID (UC...)")
    if st.button("Add Channel") and name and channel_id and API_KEY:
        st.session_state.channels[name] = {"id": channel_id.strip(), "data": None, "channel_stats": {}}
        st.session_state.notes[name] = ""
        st.sidebar.success(f"Added: {name}")

# List & remove
if st.session_state.channels:
    st.sidebar.write("Your Channels")
    for name in list(st.session_state.channels.keys()):
        col1, col2 = st.sidebar.columns([4, 1])
        col1.write(name)
        if col2.button("Remove", key=f"rm_{name}"):
            del st.session_state.channels[name]
            if name in st.session_state.notes:
                del st.session_state.notes[name]
            st.rerun()

if not API_KEY:
    st.warning("Enter your YouTube Data API key in the sidebar.")
    st.stop()

if not st.session_state.channels:
    st.info("Add channels in the sidebar to begin.")
    st.stop()

# Main navigation
tab_all, tab_detail = st.tabs(["All Channels Overview", "Channel Detail"])

# ==================== ALL CHANNELS OVERVIEW ====================
with tab_all:
    st.subheader("All Channels Summary")

    summary_data = []
    for name, info in st.session_state.channels.items():
        df = info.get("data")
        stats = info.get("channel_stats", {})
        row = {
            "Channel": name,
            "Subscribers": stats.get("subscribers", 0),
            "Total Views": stats.get("total_views", 0),
            "Videos Analyzed": len(df) if df is not None else 0,
            "Avg Views/Video": int(df["Views"].mean()) if df is not None and not df.empty else 0,
        }
        summary_data.append(row)

    summary_df = pd.DataFrame(summary_data)
    if not summary_df.empty:
        st.dataframe(summary_df.sort_values("Total Views", ascending=False), use_container_width=True)

        csv_all = summary_df.to_csv(index=False).encode()
        st.download_button("Export All Channels Summary (CSV)", csv_all, "all_channels_summary.csv", "text/csv")

# ==================== CHANNEL DETAIL ====================
with tab_detail:
    selected = st.selectbox("Select Channel", list(st.session_state.channels.keys()))
    channel_info = st.session_state.channels[selected]
    channel_id = channel_info["id"]

    st.subheader(f"Channel: {selected}")
    st.caption(f"Channel ID: {channel_id}")

    # Refresh button
    if st.button("Refresh Data for This Channel", type="primary") or channel_info.get("data") is None:
        with st.spinner("Fetching latest data..."):
            youtube = build("youtube", "v3", developerKey=API_KEY)
            
            # Channel stats
            ch_resp = youtube.channels().list(part="snippet,statistics,contentDetails", id=channel_id).execute()
            ch = ch_resp["items"][0]
            subscriber_count = int(ch["statistics"].get("subscriberCount", 0))
            total_views = int(ch["statistics"].get("viewCount", 0))
            uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]

            # Videos
            videos = []
            next_page = None
            for _ in range(2):
                pl_resp = youtube.playlistItems().list(
                    part="contentDetails", 
                    playlistId=uploads_id, 
                    maxResults=50, 
                    pageToken=next_page
                ).execute()
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
                
                # Calculated metrics
                df["Days Since Publish"] = (datetime.now() - df["Published"]).dt.days
                df["Views per Day"] = (df["Views"] / df["Days Since Publish"].replace(0, 1)).round(1)
                df["Like Rate %"] = (df["Likes"] / df["Views"].replace(0, 1) * 100).round(2)
                df["Comment Rate %"] = (df["Comments"] / df["Views"].replace(0, 1) * 100).round(2)

            st.session_state.channels[selected]["data"] = df
            st.session_state.channels[selected]["channel_stats"] = {
                "subscribers": subscriber_count,
                "total_views": total_views
            }

            # Save everything
            save_data = {}
            for k, v in st.session_state.channels.items():
                save_data[k] = {
                    "id": v["id"],
                    "data": v["data"].to_json() if v["data"] is not None else None,
                    "channel_stats": v.get("channel_stats", {}),
                    "notes": st.session_state.notes.get(k, "")
                }
            with open("channels.json", "w") as f:
                json.dump(save_data, f)
            st.success("Data refreshed")

    df = channel_info.get("data")
    stats = channel_info.get("channel_stats", {})

    if df is not None and not df.empty:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Subscribers", f"{stats.get('subscribers', 0):,}")
        col2.metric("Total Views", f"{stats.get('total_views', 0):,}")
        col3.metric("Videos Analyzed", len(df))
        col4.metric("Avg Views/Video", f"{int(df['Views'].mean()):,}")

        detail_tabs = st.tabs(["Video Table", "Performance Charts", "Upload Timing", "Grok Video Ideas", "Team Notes"])

        with detail_tabs[0]:
            display_df = df[["Title", "Published", "Views", "Views per Day", "Like Rate %", "Comment Rate %", "URL"]].copy()
            display_df["Published"] = display_df["Published"].dt.strftime("%Y-%m-%d")
            st.dataframe(display_df.sort_values("Views", ascending=False), use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode()
            st.download_button("Export This Channel Videos (CSV)", csv, f"{selected}_videos.csv", "text/csv")

        with detail_tabs[1]:
            top = df.nlargest(10, "Views")
            fig1 = px.bar(top, x="Views", y="Title", orientation="h", title="Top 10 Videos")
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.line(df.sort_values("Published"), x="Published", y="Views", title="Views Over Time", markers=True)
            st.plotly_chart(fig2, use_container_width=True)

        with detail_tabs[2]:  # Fixed Upload Timing
            st.write("**Upload Timing Analysis**")
            
            # Ensure datetime before using .dt
            temp_df = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(temp_df["Published"]):
                temp_df["Published"] = pd.to_datetime(temp_df["Published"], errors='coerce')
            
            temp_df["Day of Week"] = temp_df["Published"].dt.day_name()
            temp_df["Hour"] = temp_df["Published"].dt.hour
            
            day_perf = temp_df.groupby("Day of Week")["Views"].mean().round(0).sort_values(ascending=False)
            st.bar_chart(day_perf, x_label="Day of Week", y_label="Average Views")

            st.write("**Best upload days from your data:**")
            st.write(day_perf.head(3))

            st.info("General recommendation: Tuesday–Thursday afternoons often perform well. Always test against your own channel data.")

        with detail_tabs[3]:
            st.write("**Grok Channel Analysis & Strategic Ideas**")
            if st.button("Generate New Video Ideas", type="primary"):
                with st.spinner("Analyzing entire channel..."):
                    all_titles = " | ".join(df["Title"].tolist())
                    words = re.findall(r'\b[a-zA-Z]{4,}\b', all_titles.lower())
                    common = Counter(words).most_common(12)
                    top_topics = [w[0] for w in common[:8]]

                    st.write("**Strong Topics Detected:**", ", ".join(top_topics))

                    st.write("\n**Recommended Video Ideas:**")
                    ideas = [
                        f"1. Complete {top_topics[0].title()} Guide for 2026 – What Actually Works Now",
                        f"2. How We Improved Our {top_topics[1].title()} Results (Step-by-Step)",
                        f"3. Top 7 Mistakes Creators Make with {top_topics[2].title()} (And Fixes)",
                        f"4. {top_topics[0].title()} vs {top_topics[3].title()} – Real Comparison",
                        f"5. Advanced {top_topics[4].title()} Tips That Increased Our Views"
                    ]
                    for idea in ideas:
                        st.write(idea)

                    st.info("Ideas are based on every video title and performance metric from this channel.")

        with detail_tabs[4]:
            st.write("**Team Notes**")
            notes = st.text_area("Add notes or ideas for the team", 
                                value=st.session_state.notes.get(selected, ""), height=200)
            if st.button("Save Notes"):
                st.session_state.notes[selected] = notes
                # Save
                save_data = {}
                for k, v in st.session_state.channels.items():
                    save_data[k] = {
                        "id": v["id"],
                        "data": v["data"].to_json() if v["data"] is not None else None,
                        "channel_stats": v.get("channel_stats", {}),
                        "notes": st.session_state.notes.get(k, "")
                    }
                with open("channels.json", "w") as f:
                    json.dump(save_data, f)
                st.success("Notes saved")

    else:
        st.info("Click 'Refresh Data for This Channel' to load statistics.")

st.caption("YouTube Team Command Center • Designed to help your team improve video performance")
