import json
import os
import time
import logging
from datetime import datetime
from src.fetch_rss import fetch_rss
from src.process_article import process_article
from src.text_to_speech import synthesize_speech
from src.s3_uploader import upload_to_s3
from src.config import MAX_ARTICLES_PER_FEED, RSS_FEEDS, IS_LAMBDA, S3_BUCKET_NAME

# ロギング設定
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


def create_episode():
    """
    複数のRSSフィードから記事を取得し、処理して音声ファイルを生成するメインロジック
    """
    logger.info("Starting news processing for all feeds...")

    all_articles = []
    processed_articles = []
    
    # すべてのフィードから記事を取得
    for source_id, feed_url in RSS_FEEDS.items():
        logger.info(f"Fetching articles from {source_id}...")
        try:
            articles = fetch_rss(feed_url, IS_LAMBDA, S3_BUCKET_NAME)
            
            # 記事のソース情報を追加
            for article in articles:
                article["source_id"] = source_id
            
            all_articles.extend(articles)
            logger.info(f"Fetched {len(articles)} articles from {source_id}")
        except Exception as e:
            logger.error(f"Error fetching articles from {source_id}: {str(e)}")
    
    # 記事の公開日で並べ替え（最新順）
    try:
        all_articles.sort(key=lambda x: x.get("published", ""), reverse=True)
        logger.info(f"Total articles fetched: {len(all_articles)}")
    except Exception as e:
        logger.error(f"Error sorting articles: {str(e)}")
    
    # 各サイトから最大記事数の制限を適用
    articles_per_source = {}
    selected_articles = []
    
    for article in all_articles:
        source_id = article["source_id"]
        if source_id not in articles_per_source:
            articles_per_source[source_id] = 0
        
        if articles_per_source[source_id] < MAX_ARTICLES_PER_FEED:
            selected_articles.append(article)
            articles_per_source[source_id] += 1
    
    logger.info(f"Selected {len(selected_articles)} articles for processing")
    
    # 選択された記事を処理（要約・翻訳・音声化）
    for article in selected_articles:
        try:
            # 記事情報の抽出
            article_id = article["id"]
            title = article["title"]
            link = article["link"]
            source = article["source"]
            source_id = article["source_id"]
            
            logger.info(f"Processing article: {title[:30]}...")
            
            # 記事の処理（要約・翻訳）
            processed = process_article(article)
            
            # 日本語の要約を取得
            summarized_text = processed["japanese_summary"]
            english_summary = processed["english_summary"]
            
            # 音声合成
            if IS_LAMBDA:
                tmp_dir = "/tmp"
            else:
                tmp_dir = "audio"
                os.makedirs(tmp_dir, exist_ok=True)
            
            # 日本語音声の生成
            ja_output_filename = f"{tmp_dir}/{article_id}_ja.mp3"
            ja_audio_file = synthesize_speech(
                summarized_text, ja_output_filename, "ja"
            )
            
            # 英語音声の生成
            en_output_filename = f"{tmp_dir}/{article_id}_en.mp3"
            en_audio_file = synthesize_speech(
                english_summary, en_output_filename, "en"
            )
            
            # S3にアップロード
            ja_s3_url = None
            en_s3_url = None
            
            if ja_audio_file:
                ja_s3_url = upload_to_s3(ja_audio_file, f"audio/{article_id}_ja.mp3")
                logger.info(f"Japanese audio file uploaded: {ja_s3_url}")
            
            if en_audio_file:
                en_s3_url = upload_to_s3(en_audio_file, f"audio/{article_id}_en.mp3")
                logger.info(f"English audio file uploaded: {en_s3_url}")
            
            # 処理結果を記録
            if ja_s3_url or en_s3_url:
                processed_articles.append({
                    "id": article_id,
                    "title": title,
                    "link": link,
                    "summary": processed["summary"] if "summary" in processed else "",
                    "english_summary": english_summary,
                    "japanese_summary": summarized_text,
                    "source": source,
                    "source_id": source_id,
                    "author": processed.get("author", ""),
                    "published": processed.get("published", ""),
                    "ai_provider": processed.get("ai_provider", ""),
                    "japanese_audio_url": ja_s3_url,
                    "english_audio_url": en_s3_url
                })
        
        except Exception as e:
            logger.error(f"Error processing article {article['id']}: {str(e)}")
        
        # API制限回避のため少し待機
        time.sleep(1)
    
    # エピソード情報の生成
    if processed_articles:
        try:
            # 現在の日付を YYYY-MM-DD 形式で取得
            today = datetime.now().strftime("%Y-%m-%d")
            
            # エピソード情報の作成
            episode = {
                "episode_id": today,
                "title": f"Tech News ({today})",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "articles": processed_articles,
                "source": "Japanese Tech News"
            }
            
            # JSONファイルに保存
            if IS_LAMBDA:
                json_filename = f"/tmp/episode_{today}.json"
            else:
                os.makedirs("data", exist_ok=True)
                os.makedirs("data/episodes", exist_ok=True)
                json_filename = f"data/episodes/episode_{today}.json"
            
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(episode, f, ensure_ascii=False, indent=2)
            
            # S3にアップロード
            s3_key = f"data/episodes/episode_{today}.json"
            metadata_url = upload_to_s3(json_filename, s3_key)
            
            if metadata_url:
                logger.info(f"Episode data uploaded to: {metadata_url}")
                return episode
            
        except Exception as e:
            logger.error(f"Error creating episode: {str(e)}")
    
    logger.info(f"Processed {len(processed_articles)} articles")
    return {"articles": processed_articles}


def lambda_handler(event, context):
    """
    AWS Lambda のハンドラー関数
    """
    try:
        episode = create_episode()
        
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Episode created with {len(episode['articles'])} articles",
                    "episode_id": episode.get("episode_id", ""),
                },
                ensure_ascii=False,
            ),
        }
    except Exception as e:
        logger.error(f"Error in lambda handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": f"Error creating episode: {str(e)}",
                },
                ensure_ascii=False,
            ),
        }


# ローカルテスト用
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    create_episode()