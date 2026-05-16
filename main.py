import os
import json
import feedparser
import requests
from requests.auth import HTTPBasicAuth

RSS_URL = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
BLOG_ID = "gensentrend"

LIVEDOOR_ID = os.environ["LIVEDOOR_ID"]
LIVEDOOR_PASS = os.environ["LIVEDOOR_PASS"]

SEEN_FILE = "seen.json"

# =========================
# 重複防止
# =========================

if os.path.exists(SEEN_FILE):
    seen = set(json.load(open(SEEN_FILE, "r", encoding="utf-8")))
else:
    seen = set()

def is_new(link):
    return link not in seen

def mark_seen(link):
    seen.add(link)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False)

# =========================
# RSS取得
# =========================

feed = feedparser.parse(RSS_URL)

if not feed.entries:
    print("記事なし")
    exit()

# =========================
# livedoor投稿
# =========================

def post_blog(title, link):
    url = f"https://blogcms.jp/atompub/{BLOG_ID}/article"

    body = f"""📰 {title}

元記事:
{link}
"""

    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom">
<title>{title}</title>
<content type="html">
<![CDATA[
{body}
]]>
</content>
</entry>
"""

    res = requests.post(
        url,
        data=xml.encode("utf-8"),
        headers={"Content-Type": "application/atom+xml; charset=utf-8"},
        auth=HTTPBasicAuth(LIVEDOOR_ID, LIVEDOOR_PASS)
    )

    print("Status:", res.status_code)

# =========================
# 実行
# =========================

for entry in feed.entries[:5]:

    title = entry.title
    link = entry.link

    if not is_new(link):
        continue

    print("投稿:", title)

    post_blog(title, link)
    mark_seen(link)