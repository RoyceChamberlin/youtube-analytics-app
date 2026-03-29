"""
Chamberlin Media Monitor — Flask
Render.com deployment
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from googleapiclient.discovery import build
import sqlite3, json, os, contextlib
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chamberlin-secret-2026")

PASSWORD      = os.environ.get("APP_PASSWORD", "ChamMedia2026")
YT_API_KEY    = os.environ.get("YOUTUBE_API_KEY", "")
_DATA_DIR     = os.environ.get("DATA_DIR", "/data")
os.makedirs(_DATA_DIR, exist_ok=True)
DB_PATH       = os.path.join(_DATA_DIR, "chamberlin.db")

# ─────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────
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
            channel_stats TEXT DEFAULT '{}',
            last_refreshed TEXT DEFAULT 'Never',
            notes TEXT DEFAULT '')""")
        db.execute("""CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_name TEXT NOT NULL, title TEXT,
            published TEXT, views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0, comments INTEGER DEFAULT 0,
            url TEXT, thumbnail TEXT,
            days_since_publish INTEGER DEFAULT 0,
            views_per_day REAL DEFAULT 0,
            like_rate REAL DEFAULT 0, comment_rate REAL DEFAULT 0,
            FOREIGN KEY (channel_name) REFERENCES channels(name) ON DELETE CASCADE)""")
        db.execute("CREATE TABLE IF NOT EXISTS folders (name TEXT PRIMARY KEY)")
        db.execute("""CREATE TABLE IF NOT EXISTS folder_channels (
            folder_name TEXT NOT NULL, channel_name TEXT NOT NULL,
            PRIMARY KEY (folder_name, channel_name))""")

init_db()

# ─────────────────────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────────────────────
SEED_DATA = {
    "Angel Studios": [
        ("UCb02Js81Etta5BgML6jK-fQ", "Angel Studios"),
        ("UCYxkRL8mgBlunTKYX4In7LA", "Angel Kids"),
        ("UCZFLi-CFABqg49AVj3ZY38Q", "Angel Studios 2"),
        ("UCPMnn5ZkYHf2epbcekcImPQ", "Angel Studios 3"),
        ("UCw6rIEbumyIW-Gu34Q3jFeg", "Angel Studios 4"),
    ],
    "Blaze Media":       [("UCoxZVv224nHvTmkMk0N3fYA", "Blaze Media")],
    "Backyard Butchers": [("UC53maXyeHXst2ZGHwsfHGCA", "Backyard Butchers")],
}

def seed():
    with get_db() as db:
        existing = {r["channel_id"] for r in db.execute("SELECT channel_id FROM channels").fetchall()}
    for folder, channels in SEED_DATA.items():
        with get_db() as db:
            db.execute("INSERT OR IGNORE INTO folders (name) VALUES (?)", (folder,))
        for ch_id, name in channels:
            if ch_id not in existing:
                with get_db() as db:
                    taken = {r["name"] for r in db.execute("SELECT name FROM channels").fetchall()}
                actual = name
                i = 1
                while actual in taken:
                    actual = f"{name} ({i})"; i += 1
                with get_db() as db:
                    db.execute("INSERT OR IGNORE INTO channels (name,channel_id) VALUES (?,?)", (actual, ch_id))
                    db.execute("INSERT OR IGNORE INTO folder_channels (folder_name,channel_name) VALUES (?,?)", (folder, actual))

seed()

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def fmt(n):
    n = int(n)
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return f"{n:,}"

def fmt_usd(n):
    n = int(n)
    if n >= 1_000_000: return f"${n/1_000_000:.1f}M"
    if n >= 1_000:     return f"${n/1_000:.0f}K"
    return f"${n:,}"

def load_channels():
    channels = {}
    with get_db() as db:
        for row in db.execute("SELECT * FROM channels").fetchall():
            ch = dict(row)
            stats = json.loads(ch["channel_stats"] or "{}")
            vrows = db.execute(
                "SELECT * FROM videos WHERE channel_name=? ORDER BY views DESC",
                (ch["name"],)).fetchall()
            videos = [dict(r) for r in vrows]
            channels[ch["name"]] = {
                "id": ch["channel_id"],
                "stats": stats,
                "videos": videos,
                "last_refreshed": ch["last_refreshed"],
                "notes": ch["notes"] or "",
            }
    return channels

def load_folders():
    folders = {}
    with get_db() as db:
        for fr in db.execute("SELECT name FROM folders ORDER BY name").fetchall():
            fname = fr["name"]
            crows = db.execute(
                "SELECT channel_name FROM folder_channels WHERE folder_name=?",
                (fname,)).fetchall()
            folders[fname] = [r["channel_name"] for r in crows]
    return folders

def detect_outliers(channels):
    outliers = []
    for ch_name, info in channels.items():
        videos = info.get("videos", [])
        if not videos: continue
        ch_display = info["stats"].get("channel_name", ch_name)
        old = [v for v in videos if v.get("days_since_publish", 0) >= 30]
        if not old: continue
        vpds = [v.get("views_per_day", 0) for v in old if v.get("views_per_day", 0) > 0]
        if not vpds: continue
        median_vpd = sorted(vpds)[len(vpds)//2]
        if median_vpd <= 0: continue
        for v in old:
            ratio = v.get("views_per_day", 0) / median_vpd
            if ratio >= 2.0:
                outliers.append({
                    "channel": ch_name,
                    "ch_display": ch_display,
                    "title": v.get("title",""),
                    "url": v.get("url",""),
                    "thumbnail": v.get("thumbnail",""),
                    "views": fmt(v.get("views",0)),
                    "vpd": f"{v.get('views_per_day',0):.0f}",
                    "days": v.get("days_since_publish",0),
                    "ratio": round(ratio,1),
                    "lr": f"{v.get('like_rate',0):.2f}",
                })
    outliers.sort(key=lambda x: x["ratio"], reverse=True)
    return outliers[:12]

# ─────────────────────────────────────────────────────────────
# YOUTUBE
# ─────────────────────────────────────────────────────────────
def yt_fetch(channel_id):
    api_key = YT_API_KEY
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY not set")
    youtube = build("youtube", "v3", developerKey=api_key)
    ch_resp = youtube.channels().list(
        part="snippet,statistics,contentDetails", id=channel_id).execute()
    if not ch_resp.get("items"):
        raise ValueError(f"Channel not found: {channel_id}")
    ch = ch_resp["items"][0]
    stats = {
        "subscribers":  int(ch["statistics"].get("subscriberCount", 0)),
        "total_views":  int(ch["statistics"].get("viewCount", 0)),
        "channel_name": ch["snippet"]["title"],
        "channel_thumb":ch["snippet"]["thumbnails"].get("medium",{}).get("url",""),
    }
    uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    videos, next_page = [], None
    for _ in range(2):
        pl = youtube.playlistItems().list(
            part="contentDetails", playlistId=uploads_id,
            maxResults=50, pageToken=next_page).execute()
        video_ids = [i["contentDetails"]["videoId"] for i in pl["items"]]
        vr = youtube.videos().list(
            part="snippet,statistics", id=",".join(video_ids)).execute()
        for item in vr["items"]:
            s = item["statistics"]; sn = item["snippet"]
            thumbs = sn.get("thumbnails",{})
            thumb_url = (thumbs.get("maxres") or thumbs.get("high") or
                         thumbs.get("medium") or thumbs.get("default") or {}).get("url","")
            pub = sn["publishedAt"][:10]
            pub_dt = datetime.strptime(pub, "%Y-%m-%d")
            days = max(1, (datetime.now() - pub_dt).days)
            views = int(s.get("viewCount",0))
            likes = int(s.get("likeCount",0))
            comments = int(s.get("commentCount",0))
            videos.append({
                "title":    sn["title"],
                "published":pub,
                "views":    views,
                "likes":    likes,
                "comments": comments,
                "url":      f"https://youtu.be/{item['id']}",
                "thumbnail":thumb_url,
                "days_since_publish": days,
                "views_per_day":      round(views/days, 1),
                "like_rate":          round(likes/max(views,1)*100, 2),
                "comment_rate":       round(comments/max(views,1)*100, 2),
            })
        next_page = pl.get("nextPageToken")
        if not next_page: break
    return stats, videos

def yt_lookup_name(channel_id):
    youtube = build("youtube", "v3", developerKey=YT_API_KEY)
    resp = youtube.channels().list(part="snippet", id=channel_id).execute()
    if not resp.get("items"):
        raise ValueError(f"No channel found: {channel_id}")
    return resp["items"][0]["snippet"]["title"]

def save_channel(name, channel_id, stats, videos, last_refreshed, notes=""):
    with get_db() as db:
        db.execute("""INSERT INTO channels (name,channel_id,channel_stats,last_refreshed,notes)
            VALUES (?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET
            channel_id=excluded.channel_id, channel_stats=excluded.channel_stats,
            last_refreshed=excluded.last_refreshed, notes=excluded.notes""",
            (name, channel_id, json.dumps(stats), last_refreshed, notes))
        if videos:
            db.execute("DELETE FROM videos WHERE channel_name=?", (name,))
            for v in videos:
                db.execute("""INSERT INTO videos
                    (channel_name,title,published,views,likes,comments,url,thumbnail,
                     days_since_publish,views_per_day,like_rate,comment_rate)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (name, v["title"], v["published"], v["views"], v["likes"],
                     v["comments"], v["url"], v["thumbnail"],
                     v["days_since_publish"], v["views_per_day"],
                     v["like_rate"], v["comment_rate"]))

# ─────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────
def logged_in():
    return session.get("auth") == True

# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def index():
    if not logged_in():
        return redirect(url_for("login"))
    channels = load_channels()
    folders  = load_folders()
    outliers = detect_outliers(channels)

    # totals
    total_subs  = sum(c["stats"].get("subscribers",0) for c in channels.values())
    total_views = sum(c["stats"].get("total_views",0)  for c in channels.values())
    total_rev   = sum(
        sum(v["views"] for v in c["videos"]) * 3.5 / 1000
        for c in channels.values()
    )

    # revenue per channel
    rev_rows = []
    for ch_name, info in channels.items():
        tv = sum(v["views"] for v in info["videos"])
        if tv > 0:
            rev_rows.append({
                "name": info["stats"].get("channel_name", ch_name),
                "views": fmt(tv),
                "low":   fmt_usd(tv*1.5/1000),
                "mid":   fmt_usd(tv*3.5/1000),
                "high":  fmt_usd(tv*5.0/1000),
            })

    # top momentum videos (across all channels)
    all_vids = []
    for ch_name, info in channels.items():
        for v in info["videos"][:50]:
            all_vids.append({**v, "channel": info["stats"].get("channel_name", ch_name)})
    top_momentum = sorted(all_vids, key=lambda x: x["views_per_day"], reverse=True)[:12]

    return render_template("index.html",
        channels=channels,
        folders=folders,
        outliers=outliers,
        total_subs=fmt(total_subs),
        total_views=fmt(total_views),
        total_rev=fmt_usd(total_rev),
        n_channels=len(channels),
        rev_rows=rev_rows,
        top_momentum=top_momentum,
    )

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["auth"] = True
            return redirect(url_for("index"))
        error = "Incorrect password"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/channel/<ch_name>")
def api_channel(ch_name):
    if not logged_in(): return jsonify({"error":"unauthorized"}), 401
    channels = load_channels()
    if ch_name not in channels:
        return jsonify({"error":"not found"}), 404
    info = channels[ch_name]
    videos = info["videos"]

    # sort
    sort = request.args.get("sort","views")
    sort_map = {"views":"views","vpd":"views_per_day","likes":"likes","lr":"like_rate","pub":"published"}
    sort_key = sort_map.get(sort,"views")
    videos_sorted = sorted(videos, key=lambda x: x.get(sort_key,0), reverse=(sort_key!="published"))

    # charts data
    trend = sorted(videos, key=lambda x: x["published"])
    labels_trend = [v["published"] for v in trend]
    views_trend  = [v["views"] for v in trend]
    vpd_trend    = [v["views_per_day"] for v in trend]

    top10_views = sorted(videos, key=lambda x:x["views"], reverse=True)[:10]
    top10_vpd   = sorted(videos, key=lambda x:x["views_per_day"], reverse=True)[:10]

    # upload timing
    day_totals = {}
    for v in videos:
        try:
            day = datetime.strptime(v["published"],"%Y-%m-%d").strftime("%A")
            day_totals.setdefault(day,[]).append(v["views"])
        except: pass
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_avgs  = {d: int(sum(day_totals[d])/len(day_totals[d])) for d in day_order if d in day_totals}
    best_day  = max(day_avgs, key=day_avgs.get) if day_avgs else "—"

    # monthly
    monthly = {}
    for v in videos:
        mo = v["published"][:7]
        monthly.setdefault(mo, {"count":0,"views":0})
        monthly[mo]["count"] += 1
        monthly[mo]["views"] += v["views"]
    monthly_labels = sorted(monthly.keys())
    monthly_counts = [monthly[m]["count"] for m in monthly_labels]
    monthly_views  = [int(monthly[m]["views"]/monthly[m]["count"]) for m in monthly_labels]

    # revenue
    rev_vids = sorted(videos, key=lambda x:x["views"], reverse=True)[:15]
    for v in rev_vids:
        v["rev_mid"] = round(v["views"]*3.5/1000,0)

    return jsonify({
        "name":      ch_name,
        "display":   info["stats"].get("channel_name", ch_name),
        "id":        info["id"],
        "refreshed": info["last_refreshed"],
        "notes":     info["notes"],
        "stats": {
            "subscribers": fmt(info["stats"].get("subscribers",0)),
            "total_views":  fmt(info["stats"].get("total_views",0)),
            "avg_views":    fmt(int(sum(v["views"] for v in videos)/max(len(videos),1))),
            "avg_vpd":      f"{sum(v['views_per_day'] for v in videos)/max(len(videos),1):.1f}",
            "avg_lr":       f"{sum(v['like_rate'] for v in videos)/max(len(videos),1):.2f}%",
            "rev_range":    f"{fmt_usd(int(sum(v['views'] for v in videos)*1.5/1000))}–{fmt_usd(int(sum(v['views'] for v in videos)*5/1000))}",
            "n_videos":     len(videos),
        },
        "videos": [{
            "title":    v["title"],
            "published":v["published"],
            "views":    fmt(v["views"]),
            "likes":    fmt(v["likes"]),
            "comments": fmt(v["comments"]),
            "vpd":      f"{v['views_per_day']:.1f}",
            "lr":       f"{v['like_rate']:.2f}%",
            "cr":       f"{v['comment_rate']:.2f}%",
            "url":      v["url"],
            "thumbnail":v["thumbnail"],
            "days":     v["days_since_publish"],
            "badge":    "NEW" if v["days_since_publish"]<=14 else ("HOT" if v["views_per_day"]>=500 else ("EVERGREEN" if v["days_since_publish"]>=90 and v["views_per_day"]>=100 else "")),
        } for v in videos_sorted[:50]],
        "charts": {
            "trend_labels": labels_trend,
            "views_trend":  views_trend,
            "vpd_trend":    vpd_trend,
            "top10_views_labels": [v["title"][:40] for v in reversed(top10_views)],
            "top10_views_data":   [v["views"] for v in reversed(top10_views)],
            "top10_vpd_labels":   [v["title"][:40] for v in reversed(top10_vpd)],
            "top10_vpd_data":     [v["views_per_day"] for v in reversed(top10_vpd)],
            "day_labels": list(day_avgs.keys()),
            "day_data":   list(day_avgs.values()),
            "best_day":   best_day,
            "monthly_labels": monthly_labels,
            "monthly_counts": monthly_counts,
            "monthly_views":  monthly_views,
            "rev_labels": [v["title"][:40] for v in reversed(rev_vids)],
            "rev_data":   [v["rev_mid"] for v in reversed(rev_vids)],
        },
    })

@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    if not logged_in(): return jsonify({"error":"unauthorized"}), 401
    data = request.json or {}
    ch_name = data.get("channel_name")
    channels = load_channels()
    targets = {ch_name: channels[ch_name]} if (ch_name and ch_name in channels) else channels
    results = []
    for name, info in targets.items():
        try:
            stats, videos = yt_fetch(info["id"])
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_channel(name, info["id"], stats, videos, ts, info["notes"])
            results.append({"name": name, "status": "ok",
                            "display": stats.get("channel_name", name)})
        except Exception as e:
            results.append({"name": name, "status": "error", "msg": str(e)})
    return jsonify({"results": results})

@app.route("/api/channel/add", methods=["POST"])
def api_add_channel():
    if not logged_in(): return jsonify({"error":"unauthorized"}), 401
    data = request.json or {}
    ch_id  = data.get("channel_id","").strip()
    folder = data.get("folder","")
    if not ch_id:
        return jsonify({"error":"No channel ID provided"}), 400
    with get_db() as db:
        existing = {r["channel_id"] for r in db.execute("SELECT channel_id FROM channels").fetchall()}
    if ch_id in existing:
        return jsonify({"error":"Channel already added"}), 400
    try:
        ch_name = yt_lookup_name(ch_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    with get_db() as db:
        taken = {r["name"] for r in db.execute("SELECT name FROM channels").fetchall()}
    actual = ch_name; i = 1
    while actual in taken:
        actual = f"{ch_name} ({i})"; i += 1
    save_channel(actual, ch_id, {}, [], "Never")
    if folder:
        with get_db() as db:
            db.execute("INSERT OR IGNORE INTO folder_channels (folder_name,channel_name) VALUES (?,?)",(folder,actual))
    return jsonify({"name": actual, "channel_id": ch_id})

@app.route("/api/channel/delete", methods=["POST"])
def api_delete_channel():
    if not logged_in(): return jsonify({"error":"unauthorized"}), 401
    data = request.json or {}
    name = data.get("name","")
    with get_db() as db:
        db.execute("DELETE FROM channels WHERE name=?", (name,))
        db.execute("DELETE FROM videos WHERE channel_name=?", (name,))
        db.execute("DELETE FROM folder_channels WHERE channel_name=?", (name,))
    return jsonify({"ok": True})

@app.route("/api/notes", methods=["POST"])
def api_notes():
    if not logged_in(): return jsonify({"error":"unauthorized"}), 401
    data = request.json or {}
    with get_db() as db:
        db.execute("UPDATE channels SET notes=? WHERE name=?",
                   (data.get("notes",""), data.get("channel_name","")))
    return jsonify({"ok": True})

@app.route("/api/folder/add", methods=["POST"])
def api_folder_add():
    if not logged_in(): return jsonify({"error":"unauthorized"}), 401
    data = request.json or {}
    name = data.get("name","").strip()
    if not name: return jsonify({"error":"No name"}), 400
    with get_db() as db:
        db.execute("INSERT OR IGNORE INTO folders (name) VALUES (?)", (name,))
    return jsonify({"ok": True})

@app.route("/api/folder/delete", methods=["POST"])
def api_folder_delete():
    if not logged_in(): return jsonify({"error":"unauthorized"}), 401
    data = request.json or {}
    name = data.get("name","")
    with get_db() as db:
        db.execute("DELETE FROM folders WHERE name=?", (name,))
        db.execute("DELETE FROM folder_channels WHERE folder_name=?", (name,))
    return jsonify({"ok": True})

@app.route("/api/folder/assign", methods=["POST"])
def api_folder_assign():
    if not logged_in(): return jsonify({"error":"unauthorized"}), 401
    data = request.json or {}
    with get_db() as db:
        db.execute("INSERT OR IGNORE INTO folder_channels (folder_name,channel_name) VALUES (?,?)",
                   (data.get("folder",""), data.get("channel","")))
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
