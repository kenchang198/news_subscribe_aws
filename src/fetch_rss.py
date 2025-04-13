import feedparser
import hashlib
import re
import json
import os
import logging
from langdetect import detect, LangDetectException
from src.config import (
    AUDIO_DIR, LOCAL_DATA_DIR, S3_OBJECT_DATA_DIR
)

# ロギング設定
logger = logging.getLogger(__name__)

# processed_article_file
processed_articles_filepath = 'processed_article_ids.json'


def is_english_content(text):
    """
    テキストが英語かどうかを判定する
    
    Args:
        text: 判定するテキスト
        
    Returns:
        bool: 英語ならTrue、それ以外ならFalse
    """
    if not text:
        return False
        
    try:
        # HTML タグを削除
        clean_text = re.sub(r'<.*?>', '', text)
        # 長すぎるテキストは最初の500文字だけ判定
        if len(clean_text) > 500:
            clean_text = clean_text[:500]
            
        lang = detect(clean_text)
        return lang == 'en'
    except LangDetectException:
        logger.warning(f"言語判定に失敗しました: {text[:50]}...")
        return False


def load_processed_ids(is_lambda=False, s3_bucket=None):
    """
    過去に処理した記事IDのリストを読み込みます

    Args:
        is_lambda: Lambda環境かどうか
        s3_bucket: S3バケット名（Lambda環境の場合）

    Returns:
        list: 過去に処理した記事IDのリスト
    """
    processed_ids = []

    if is_lambda and s3_bucket:
        # Lambda環境ではS3から読み込み
        import boto3
        s3_client = boto3.client('s3')
        try:
            response = s3_client.get_object(
                Bucket=s3_bucket,
                Key=f"{S3_OBJECT_DATA_DIR}/{processed_articles_filepath}"
            )
            processed_ids = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"S3から{len(processed_ids)}件の処理済み記事IDを読み込みました")
        except Exception as e:
            logger.info(f"処理済み記事IDファイルが存在しないか読み込めませんでした: {str(e)}")
    else:
        # ローカル環境ではファイルから読み込み
        file_path = f"{LOCAL_DATA_DIR}/{processed_articles_filepath}"
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    processed_ids = json.loads(f.read())
                logger.info(f"ローカルから{len(processed_ids)}件の処理済み記事IDを読み込みました")
            except Exception as e:
                logger.error(f"処理済み記事IDファイルの読み込み中にエラーが発生しました: {str(e)}")
        else:
            logger.info("処理済み記事IDファイルが存在しないため、新規作成します")

    return processed_ids


def save_processed_ids(processed_ids, is_lambda=False, s3_bucket=None):
    """
    処理した記事IDのリストを保存します

    Args:
        processed_ids: 処理した記事IDのリスト
        is_lambda: Lambda環境かどうか
        s3_bucket: S3バケット名（Lambda環境の場合）
    """
    if is_lambda:
        file_path = f'{AUDIO_DIR}/{processed_articles_filepath}'
    else:
        os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
        file_path = f"{LOCAL_DATA_DIR}/{processed_articles_filepath}"

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(processed_ids, f, ensure_ascii=False, indent=2)

    if is_lambda and s3_bucket:
        # Lambda環境ではS3にもアップロード
        import boto3
        s3_client = boto3.client('s3')
        try:
            s3_client.upload_file(
                file_path,
                s3_bucket,
                f"{S3_OBJECT_DATA_DIR}/{processed_articles_filepath}"
            )
            logger.info(f"処理済み記事ID({len(processed_ids)}件)をS3に保存しました")
        except Exception as e:
            logger.error(f"処理済み記事IDのS3保存中にエラーが発生しました: {str(e)}")
    else:
        logger.info(f"処理済み記事ID({len(processed_ids)}件)をローカルに保存しました")


def fetch_rss(feed_url, is_lambda=False, s3_bucket=None):
    """
    RSSフィードから記事を取得し、過去に処理した記事を除外します

    Args:
        feed_url: RSSフィードのURL
        is_lambda: Lambda環境かどうか
        s3_bucket: S3バケット名（Lambda環境の場合）

    Returns:
        list: 重複を除外した記事のリスト
    """
    # 過去に処理した記事IDを読み込み
    processed_ids = load_processed_ids(is_lambda, s3_bucket)

    articles = []
    new_processed_ids = []

    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        original_id = entry.id

        # 過去に処理した記事かどうかをチェック
        if original_id in processed_ids:
            logger.info(f"重複記事をスキップしました: {entry.title}")
            continue  # 重複記事はスキップ
            
        # タイトルと概要から言語判定
        title_text = entry.title
        summary_text = entry.summary if hasattr(entry, 'summary') else ""
        
        # 英語コンテンツのみフィルタリング
        # 日本語サイトの場合はこのチェックをスキップするためコメントアウト
        # if not is_english_content(title_text) and not is_english_content(summary_text):
        #    logger.info(f"英語以外の記事をスキップしました: {entry.title[:30]}...")
        #    processed_ids.append(original_id)  # 非英語の記事もスキップした記録に追加
        #    continue

        # 記事の一意IDを生成
        url_hash = hashlib.md5(original_id.encode()).hexdigest()[:8]
        safe_title = re.sub(r'[^\w\s]', '', entry.title)[:30]
        safe_title = safe_title.replace(' ', '_')
        safe_id = f"{safe_title}_{url_hash}"

        articles.append({
            "id": safe_id,
            "original_id": original_id,
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary if hasattr(entry, 'summary') else "",
            "source": feed.feed.title,
            "author": entry.author if hasattr(entry, 'author') else "",
            "published": entry.published if hasattr(entry, 'published') else "",
            "source_id": feed_url.split("/")[-2] if "/" in feed_url else "unknown",
        })

        # 処理した記事IDを記録
        new_processed_ids.append(original_id)

    # 新しく処理した記事IDを既存のリストに追加して保存
    if new_processed_ids:
        processed_ids.extend(new_processed_ids)

        # 最新1000件に制限
        if len(processed_ids) > 1000:
            processed_ids = processed_ids[-1000:]

        save_processed_ids(processed_ids, is_lambda, s3_bucket)
        logger.info(
            f"{len(new_processed_ids)}件の新規記事を処理しました（保存済み記事ID: {len(processed_ids)}件）")
    else:
        logger.info("新規記事はありませんでした")

    return articles


if __name__ == "__main__":
    # テスト用
    articles = fetch_rss("https://b.hatena.ne.jp/entrylist/it.rss")
    for article in articles[:3]:  # 3件だけ表示
        print(f"📌 {article['title']} ({article['source']})")
        print(f"🔗 {article['link']}")
        print(f"📝 {article['summary']}\n")
