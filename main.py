import os
import json
import feedparser
import requests
from requests.auth import HTTPBasicAuth
from google import genai

# =========================
# 設定
# =========================

RSS_URL = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"
BLOG_ID = "gensentrend"

LIVEDOOR_ID = os.environ["LIVEDOOR_ID"]
LIVEDOOR_PASS = os.environ["LIVEDOOR_PASS"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

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
# Gemini
# =========================

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_article(title, summary, link):
    prompt = f"""
あなたはニュースまとめブログの編集者です。

以下のニュースを読みやすくまとめてください。

条件:
- 日本語
- 見出し付き
- 400〜700文字
- 誇張しない
- 読みやすさ重視
- 軽い感想を最後に入れる

タイトル:
{title}

内容:
{summary}

元URL:
{link}
"""

    res = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return res.text

# =========================
# livedoor投稿
# =========================

def post_blog(title, article, link):

    url = f"https://blogcms.jp/atompub/{BLOG_ID}/article"

    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom">
<title>{title}</title>
<content type="html">
<![CDATA[
{article}

<br><br>
引用元:
<a href="{link}">{link}</a>
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
    print(res.text)

# =========================
# メイン処理（複数記事対応）
# =========================

for entry in feed.entries[:5]:

    title = entry.title
    link = entry.link
    summary = getattr(entry, "summary", "")

    if not is_new(link):
        continue

    print("処理中:", title)

    try:
        article = generate_article(title, summary, link)
        post_blog(title, article, link)
        mark_seen(link)

        print("投稿完了")

    except Exception as e:
        print("エラー:", e)