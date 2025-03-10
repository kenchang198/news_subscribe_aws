import json
import os
import time
from src.fetch_rss import fetch_rss
from src.summarize import summarize_article
from src.text_to_speech import synthesize_speech
from src.s3_uploader import upload_to_s3
from src.config import MAX_ARTICLES_PER_FEED, RSS_FEEDS


def lambda_handler(event, context):
    """
    AWS Lambda のハンドラー関数
    """
    print("Starting news processing...")

    processed_articles = []

    # Lambda実行用の一時ディレクトリ
    tmp_dir = "/tmp"

    # 各フィードを処理
    for feed_config in RSS_FEEDS:
        feed_url = feed_config["url"]
        source_name = feed_config["name"]

        print(f"Processing feed: {source_name}")
        articles = fetch_rss(feed_url)

        # 各記事を処理
        for article in articles[:MAX_ARTICLES_PER_FEED]:
            article_id = article["id"]

            # 記事情報の抽出
            title = article["title"]
            link = article["link"]
            summary = article["summary"]

            print(f"Processing: article_id {article_id} title {title}")

            try:
                # 記事の要約
                summarized_text = summarize_article(link, title, summary)
                print(f"Summary completed: {summarized_text[:50]}...")

                # 音声合成（Lambda の /tmp に一時保存）
                output_filename = f"{tmp_dir}/{article_id}.mp3"
                audio_file = synthesize_speech(
                    summarized_text, output_filename)

                # S3にアップロード
                if audio_file:
                    s3_url = upload_to_s3(audio_file)

                    if s3_url:
                        # 処理結果を記録
                        processed_articles.append(
                            {
                                "id": article_id,
                                "title": title,
                                "link": link,
                                "source": source_name,
                                "summary": summarized_text,
                                "audio_url": s3_url,
                                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                            }
                        )
                        print(f"Audio file created and uploaded: {s3_url}")

            except Exception as e:
                print(f"Error processing article: {e}")

            # API制限回避のため少し待機
            time.sleep(1)

    # 処理結果をJSONとしてS3に保存
    if processed_articles:
        try:
            json_data = json.dumps(processed_articles, ensure_ascii=False)
            json_filename = f"{tmp_dir}/processed_articles.json"

            with open(json_filename, "w", encoding="utf-8") as f:
                f.write(json_data)

            # メタデータをS3にアップロード
            metadata_url = upload_to_s3(
                json_filename, "data/processed_articles.json")
            print(f"Metadata uploaded to: {metadata_url}")
        except Exception as e:
            print(f"Error saving metadata: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": f"Processed {len(processed_articles)} articles",
                "articles": processed_articles,
            },
            ensure_ascii=False,
        ),
    }


# ローカルテスト用
if __name__ == "__main__":
    lambda_handler(None, None)
