import json
import os
import time
import logging
from src.fetch_rss import fetch_rss
from src.summarize import summarize_article
from src.text_to_speech import synthesize_speech
from src.s3_uploader import upload_to_s3
from src.config import (
    MAX_ARTICLES_PER_FEED,
    RSS_FEEDS,
    API_DELAY_SECONDS,
    AUDIO_DIR
)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    """
    AWS Lambda のハンドラー関数

    RSSフィードからニュース記事を取得し、要約して音声に変換、S3にアップロードします。

    Args:
        event: Lambdaイベントデータ
        context: Lambda実行コンテキスト

    Returns:
        dict: 処理結果のサマリー
    """
    logger.info("Starting news processing...")

    processed_articles = []

    # 環境に応じた一時ディレクトリの設定
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # 各フィードを処理
    for feed_config in RSS_FEEDS:
        feed_url = feed_config["url"]
        source_name = feed_config["name"]

        logger.info(f"Processing feed: {source_name}")

        try:
            articles = fetch_rss(feed_url)

            # 各記事を処理
            for article in articles[:MAX_ARTICLES_PER_FEED]:
                article_id = article["id"]

                # 記事情報の抽出
                title = article["title"]
                link = article["link"]
                summary = article["summary"]

                logger.info(
                    f"Processing article: {title[:50]}... (ID: {article_id})")

                try:
                    # 記事の要約
                    summarized_text = summarize_article(link, title, summary)
                    logger.info(
                        f"Summary completed: {summarized_text[:50]}...")

                    # 音声合成（一時保存）
                    output_filename = f"{AUDIO_DIR}/{article_id}.mp3"
                    audio_file = synthesize_speech(
                        summarized_text, output_filename)

                    # アップロード（Lambda環境ではS3、ローカル環境ではファイルコピー）
                    if audio_file:
                        file_url = upload_to_s3(audio_file)

                        if file_url:
                            # 処理結果を記録
                            processed_articles.append({
                                "id": article_id,
                                "title": title,
                                "link": link,
                                "source": source_name,
                                "summary": summarized_text,
                                "audio_url": file_url,
                                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                            })
                            logger.info(
                                f"Audio file created and stored: {file_url}")

                except Exception as e:
                    logger.error(
                        f"Error processing article '{title[:30]}...': {str(e)}", exc_info=True)

                # API制限回避のため少し待機
                time.sleep(API_DELAY_SECONDS)

        except Exception as e:
            logger.error(
                f"Error processing feed {source_name}: {str(e)}", exc_info=True)

    # 処理結果をJSONとして保存
    if processed_articles:
        try:
            json_data = json.dumps(
                processed_articles, ensure_ascii=False, indent=2)
            json_filename = f"{AUDIO_DIR}/processed_articles.json"

            with open(json_filename, "w", encoding="utf-8") as f:
                f.write(json_data)

            # メタデータをアップロード
            metadata_path = "data/processed_articles.json"
            metadata_url = upload_to_s3(json_filename, metadata_path)
            logger.info(f"Metadata saved to: {metadata_url}")
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}", exc_info=True)

    result = {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Processed {len(processed_articles)} articles",
            "articles": processed_articles,
        }, ensure_ascii=False),
    }

    logger.info(
        f"Processing completed: {len(processed_articles)} articles processed")
    return result


# ローカルテスト用
if __name__ == "__main__":
    # ローカル実行環境のディレクトリを準備
    os.makedirs("audio", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # Lambda関数を実行
    logger.info("Running in local development environment")
    result = lambda_handler(None, None)
    logger.info(
        f"Execution completed with status code: {result['statusCode']}")
