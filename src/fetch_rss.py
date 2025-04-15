import feedparser
import time
import logging
from datetime import datetime, timezone

# ロギング設定
logger = logging.getLogger(__name__)

# processed_article_file
processed_articles_filepath = 'processed_article_ids.json'


def fetch_rss(feed_url):
    logger.info(f"RSSフィードを取得中: {feed_url}")
    articles = []

    try:
        feed = feedparser.parse(feed_url)
        logger.info(f"フィードから{len(feed.entries)}件のエントリーを取得しました。")

        for entry in feed.entries:
            article_id = entry.get('link', entry.get('id'))
            if not article_id:
                title = entry.get('title', 'No Title')
                logger.warning(f"ID無し記事スキップ: {title[:50]}...")
                continue

            published_time = None
            published_parsed = entry.get('published_parsed')
            updated_parsed = entry.get('updated_parsed')

            if published_parsed:
                # time.mktime を変数に格納して行長を調整
                ts = time.mktime(published_parsed)
                dt_naive = datetime.fromtimestamp(
                    ts
                )
                published_time = dt_naive.replace(tzinfo=timezone.utc)
            elif updated_parsed:
                # time.mktime を変数に格納して行長を調整
                ts = time.mktime(updated_parsed)
                dt_naive = datetime.fromtimestamp(
                    ts
                )
                published_time = dt_naive.replace(tzinfo=timezone.utc)

            published_str = published_time.isoformat() if published_time else ""

            # content の取得を簡略化（デフォルト値を改善）
            content_list = entry.get('content', [])
            content_value = content_list[0].get(
                'value', '') if content_list else ''

            article_data = {
                'id': article_id,
                'title': entry.get('title', 'No Title'),
                'link': entry.get('link', ''),
                'published': published_str,
                'summary': entry.get('summary', ''),
                'content': content_value
            }
            articles.append(article_data)

    except Exception as e:
        logger.error(f"RSSフィードの取得または解析中にエラー: {e}", exc_info=True)

    logger.info(f"フィード処理完了: {feed_url}, 取得記事数: {len(articles)}")
    return articles


if __name__ == "__main__":
    # テスト用
    articles = fetch_rss("https://b.hatena.ne.jp/entrylist/it.rss")
    for article in articles[:3]:  # 3件だけ表示
        print(f"📌 {article['title']} ({article['source']})")
        print(f"🔗 {article['link']}")
        print(f"📝 {article['summary']}\n")
