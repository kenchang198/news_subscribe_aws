import feedparser
import hashlib
import re


def fetch_rss(feed_url):
    articles = []

    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        url_hash = hashlib.md5(entry.id.encode()).hexdigest()[:8]

        safe_title = re.sub(r'[^\w\s]', '', entry.title)[:30]
        safe_title = safe_title.replace(' ', '_')

        safe_id = f"{safe_title}_{url_hash}"

        articles.append(
            {
                "id": safe_id,
                "original_id": entry.id,
                "title": entry.title,
                "link": entry.link,
                "summary": entry.summary if "summary" in entry else "",
                "source": feed.feed.title,
            }
        )
    return articles


if __name__ == "__main__":
    articles = fetch_rss()
    for article in articles[:3]:  # 3件だけ表示
        print(f"📌 {article['title']} ({article['source']})")
        print(f"🔗 {article['link']}")
        print(f"📝 {article['summary']}\n")
