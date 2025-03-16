import json
import os
import time
import logging
import boto3
import shutil
from src.fetch_rss import fetch_rss
from src.summarize import summarize_article
from src.text_to_speech import synthesize_speech
from src.s3_uploader import upload_to_s3
from src.config import (
    MAX_ARTICLES_PER_FEED,
    RSS_FEEDS,
    API_DELAY_SECONDS,
    AUDIO_DIR,
    IS_LAMBDA,
    LOCAL_DATA_DIR,
    S3_OBJECT_DATA_DIR,
    S3_BUCKET_NAME
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

                    # Lambda環境の場合のみS3にアップロード、ローカルではファイルパスをそのまま使用
                    if audio_file:
                        if IS_LAMBDA:
                            file_url = upload_to_s3(audio_file)
                        else:
                            file_url = audio_file  # ローカル環境ではファイルパスをそのまま使用

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
                                f"Audio file {'uploaded to S3' if IS_LAMBDA else 'saved locally'}: {file_url}")

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
            # 現在日付をエピソードIDとして使用
            today = time.strftime("%Y-%m-%d")
            episode_data = {
                "episode_id": today,
                "title": f"ITニュース要約 ({today})",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "articles": processed_articles
            }

            json_data = json.dumps(episode_data, ensure_ascii=False, indent=2)

            # エピソードごとのJSONファイルを保存
            episode_filename = f"{AUDIO_DIR}/episode_{today}.json"
            with open(episode_filename, "w", encoding="utf-8") as f:
                f.write(json_data)

            # Lambda環境の場合のみS3にアップロード
            if IS_LAMBDA:
                # 個別エピソードのJSONをアップロード
                episode_path = f"{S3_OBJECT_DATA_DIR}/episodes/episode_{today}.json"
                episode_url = upload_to_s3(episode_filename, episode_path)
                logger.info(f"エピソードデータをS3にアップロードしました: {episode_url}")

                # エピソードリストの更新
                episodes_list_path, episodes_list_filename = update_episodes_list(
                    today, processed_articles, AUDIO_DIR, is_lambda=True
                )

                # S3にアップロード
                episodes_list_url = upload_to_s3(
                    episodes_list_filename, episodes_list_path)
                logger.info(f"エピソードリストを更新しS3にアップロードしました: {episodes_list_url}")

            else:
                # ローカル環境
                episodes_dir = f"{LOCAL_DATA_DIR}/episodes"
                os.makedirs(episodes_dir, exist_ok=True)

                # 個別エピソードのJSONをコピー
                episode_local_path = f"{episodes_dir}/episode_{today}.json"
                shutil.copy2(episode_filename, episode_local_path)
                logger.info(f"エピソードデータをローカルに保存しました: {episode_local_path}")

                # エピソードリストの更新
                episodes_list_path, episodes_list_filename = update_episodes_list(
                    today, processed_articles, AUDIO_DIR, is_lambda=False
                )

                # ローカルの保存場所にコピー
                shutil.copy2(episodes_list_filename, episodes_list_path)
                logger.info(f"エピソードリストをローカルに更新しました: {episodes_list_path}")

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


def update_episodes_list(today, processed_articles, tmp_dir, is_lambda=False):
    """
    エピソードリストを更新する関数

    Args:
        today: エピソードID（日付形式の文字列）
        processed_articles: 処理された記事のリスト
        tmp_dir: 一時ディレクトリのパス
        is_lambda: Lambda環境かどうか

    Returns:
        tuple: (エピソードリストのパス, 保存されたファイルのパス)
    """
    logger = logging.getLogger(__name__)
    episodes_list = []

    # エピソードの要約情報
    episode_summary = {
        "episode_id": today,
        "title": f"ITニュース要約 ({today})",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "article_count": len(processed_articles)
    }

    if is_lambda:
        episodes_list_path = "data/episodes_list.json"

        try:
            # 既存のエピソードリストを取得（存在すれば）
            s3_client = boto3.client('s3', region_name='ap-northeast-1')
            try:
                existing_list = s3_client.get_object(
                    Bucket=S3_BUCKET_NAME, Key=episodes_list_path)
                episodes_list = json.loads(existing_list['Body'].read())
            except Exception as e:
                logger.info(f"エピソードリストが存在しないため新規作成します: {str(e)}")
        except Exception as e:
            logger.error(f"S3からエピソードリストの取得中にエラーが発生しました: {str(e)}")
    else:
        # ローカル環境での処理
        data_dir = "data"
        episodes_list_path = f"{data_dir}/episodes_list.json"

        # 既存のリストを読み込み（存在すれば）
        if os.path.exists(episodes_list_path):
            try:
                with open(episodes_list_path, "r", encoding="utf-8") as f:
                    episodes_list = json.loads(f.read())
            except Exception as e:
                logger.error(f"ローカルのエピソードリスト読み込み中にエラー: {str(e)}")

    # 重複チェック
    existing_ids = [ep["episode_id"] for ep in episodes_list]
    if today not in existing_ids:
        episodes_list.append(episode_summary)

    # 日付順に並べ替え（新しい順）
    episodes_list.sort(key=lambda x: x["episode_id"], reverse=True)

    # 更新したリストを保存
    episodes_list_json = json.dumps(
        episodes_list, ensure_ascii=False, indent=2)
    episodes_list_filename = f"{tmp_dir}/episodes_list.json"

    with open(episodes_list_filename, "w", encoding="utf-8") as f:
        f.write(episodes_list_json)

    return episodes_list_path, episodes_list_filename


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
