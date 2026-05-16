import os
import feedparser
import requests
from requests.auth import HTTPBasicAuth
from google import genai

# =========================================
# 設定
# =========================================

# RSS
RSS_URL = "https://news.yahoo.co.jp/rss/topics/top-picks.xml"

# livedoorブログID
BLOG_ID = "gensentrend"

# 環境変数
LIVEDOOR_ID = os.environ["LIVEDOOR_ID"]
LIVEDOOR_PASS = os.environ["LIVEDOOR_PASS"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# =========================================
# RSS取得
# =========================================

feed = feedparser.parse(RSS_URL)

if len(feed.entries) == 0:
    print("記事なし")
    exit()

entry = feed.entries[0]

title = entry.title
link = entry.link

summary = ""

if hasattr(entry, "summary"):
    summary = entry.summary

print("取得記事:", title)

# =========================================
# Gemini
# =========================================

client = genai.Client(api_key=GEMINI_API_KEY)

prompt = f"""
以下のニュースをまとめブログ風の記事にしてください。

タイトル:
{title}

内容:
{summary}

元記事:
{link}

条件:
・日本語
・読みやすく
・SEOを意識
・見出しをつける
・2chまとめ風
・最後に簡単な感想も入れる
"""

response = client.models.generate_content(
    model="gemini-1.5-flash"
    contents=prompt
)

article = response.text

print("記事生成完了")

# =========================================
# livedoor投稿
# =========================================

url = f"https://livedoor.blogcms.jp/atompub/{BLOG_ID}/article"

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
    headers={
        "Content-Type": "application/atom+xml; charset=utf-8"
    },
    auth=HTTPBasicAuth(
        LIVEDOOR_ID,
        LIVEDOOR_PASS
    )
)

print("Status:", res.status_code)
print(res.text)