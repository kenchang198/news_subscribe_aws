import feedparser
import hashlib
import re
import json
import os
import logging
from src.config import IS_LAMBDA, AUDIO_DIR, RSS_FEEDS

# ロギング設定
logger = logging.getLogger(__name__)


def generate_safe_id(title, url):
    """
    タイトルとURLから安全なファイル名として使用できるIDを生成
    """
    # URLのハッシュを生成
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

    # タイトルの一部を安全な形式に変換
    safe_title = re.sub(r'[^\w\s]', '', title)[:30].strip().replace(' ', '_')

    return f"{safe_title}_{url_hash}"


def fetch_news_articles():
    """
    各RSSフィードから記事を取得
    """
    all_articles = []
    
    for source_id, feed_url in RSS_FEEDS.items():
        logger.info(f"{source_id}のフィード取得開始: {feed_url}")

        try:
            feed = feedparser.parse(feed_url)
            logger.info(f"{len(feed.entries)}件の記事を取得しました")

            for entry in feed.entries:
                # 記事の一意IDを生成
                article_id = generate_safe_id(entry.title, entry.link)

                # 記事情報を抽出
                article = {
                    "id": article_id,
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary if hasattr(entry, 'summary') else "",
                    "author": entry.author if hasattr(entry, 'author') else "不明",
                    "published": entry.published if hasattr(entry, 'published') else "",
                    "source": feed.feed.title if hasattr(feed.feed, 'title') else source_id,
                    "source_id": source_id
                }

                all_articles.append(article)
                logger.debug(f"記事取得: {article['title']}")
        except Exception as e:
            logger.error(f"{source_id}のフィード取得中にエラー: {str(e)}")
    
    # 公開日でソート（新しい順）
    all_articles.sort(key=lambda x: x.get("published", ""), reverse=True)
    
    return all_articles


def save_articles_for_testing(articles, filename="news_articles.json"):
    """
    テスト用に記事データをJSONファイルに保存（ローカル環境用）
    """
    if not IS_LAMBDA:
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)
        print(filepath)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

        logger.info(f"{len(articles)}件の記事を保存しました: {filepath}")
        return filepath
    return None


# テスト実行用
if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # ニュースサイトからフィードを取得
    articles = fetch_news_articles()

    # 最初の5件だけ表示
    for article in articles[:5]:
        print(f"タイトル: {article['title']}")
        print(f"出典: {article['source']} ({article['source_id']})")
        print(f"リンク: {article['link']}")
        print(f"概要: {article['summary'][:150]}...")
        print("")

    # テスト用にファイルに保存
    save_articles_for_testing(articles)
