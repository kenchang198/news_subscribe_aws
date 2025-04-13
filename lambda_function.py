import json
import os
import time
import logging
import shutil
from src.fetch_rss import fetch_rss
from src.process_article import process_article
from src.text_to_speech import generate_audio_for_article
from src.s3_uploader import upload_to_s3
from src.config import (
    MAX_ARTICLES_PER_FEED,
    AUDIO_DIR,
    IS_LAMBDA,
    RSS_FEEDS,
    S3_BUCKET_NAME
)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def update_episodes_list(episode_data):
    """
    エピソードリストを更新する
    """
    logger.info("エピソードリスト更新開始")

    episodes_list = []
    episodes_list_path = "data/episodes_list.json"

    # 既存のエピソードリストを読み込み
    try:
        if IS_LAMBDA:
            import boto3
            from src.config import S3_BUCKET_NAME

            s3_client = boto3.client('s3')
            try:
                response = s3_client.get_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=episodes_list_path
                )
                episodes_list = json.loads(
                    response['Body'].read().decode('utf-8'))
                logger.info(f"S3から{len(episodes_list)}件のエピソードを読み込みました")
            except Exception as e:
                logger.info(f"エピソードリストが存在しないため、新規作成します: {str(e)}")
        else:
            if os.path.exists(episodes_list_path):
                with open(episodes_list_path, "r", encoding="utf-8") as f:
                    episodes_list = json.load(f)
                logger.info(f"ローカルから{len(episodes_list)}件のエピソードを読み込みました")
    except Exception as e:
        logger.error(f"エピソードリスト読み込み中にエラー: {str(e)}")

    # エピソードの要約情報
    episode_summary = {
        "episode_id": episode_data["episode_id"],
        "title": episode_data["title"],
        "created_at": episode_data["created_at"],
        "article_count": len(episode_data["articles"]),
        "source": "Japanese Tech News"
    }

    # 重複チェック
    existing_ids = [ep["episode_id"] for ep in episodes_list]
    if episode_summary["episode_id"] not in existing_ids:
        episodes_list.append(episode_summary)

    # 日付順に並べ替え（新しい順）
    episodes_list.sort(key=lambda x: x["episode_id"], reverse=True)

    # エピソードリストを保存
    try:
        if IS_LAMBDA:
            # S3に保存
            tmp_file = f"{AUDIO_DIR}/episodes_list.json"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(episodes_list, f, ensure_ascii=False, indent=2)

            upload_to_s3(tmp_file, episodes_list_path)
            logger.info("エピソードリストをS3に保存しました")
        else:
            # ローカルに保存
            os.makedirs("data", exist_ok=True)
            with open(episodes_list_path, "w", encoding="utf-8") as f:
                json.dump(episodes_list, f, ensure_ascii=False, indent=2)
            logger.info("エピソードリストをローカルに保存しました")
    except Exception as e:
        logger.error(f"エピソードリスト保存中にエラー: {str(e)}")

    return episodes_list


def lambda_handler(event, context):
    """
    複数の日本語RSSフィードから記事を取得、要約して日本語音声を生成するLambda関数
    """
    logger.info("日本のITニュース記事処理を開始します...")

    all_articles = []
    processed_articles = []

    # 環境に応じた一時ディレクトリの設定
    os.makedirs(AUDIO_DIR, exist_ok=True)

    try:
        # 複数のRSSフィードから記事を取得
        for source_id, feed_url in RSS_FEEDS.items():
            logger.info(f"{source_id}からフィードを取得します...")
            try:
                # RSSフィードから記事を取得
                articles = fetch_rss(feed_url, IS_LAMBDA, S3_BUCKET_NAME)
                
                # ソース情報を追加
                for article in articles:
                    article["source_id"] = source_id
                
                all_articles.extend(articles)
                logger.info(f"{source_id}から{len(articles)}件の記事を取得しました")
            except Exception as e:
                logger.error(f"{source_id}のフィード取得中にエラー: {str(e)}", exc_info=True)
        
        # 最新の記事を優先（公開日でソート）
        all_articles.sort(key=lambda x: x.get("published", ""), reverse=True)
        
        # 各サイトから最大記事数を制限
        articles_per_source = {}
        selected_articles = []
        
        for article in all_articles:
            source_id = article.get("source_id", "unknown")
            if source_id not in articles_per_source:
                articles_per_source[source_id] = 0
            
            if articles_per_source[source_id] < MAX_ARTICLES_PER_FEED:
                selected_articles.append(article)
                articles_per_source[source_id] += 1
        
        logger.info(f"合計{len(selected_articles)}件の記事を処理対象としました")

        # 選択された記事を処理
        for article in selected_articles:
            try:
                # 日本語要約のみ
                processed = process_article(article)

                # 日本語音声のみ生成
                processed = generate_audio_for_article(processed)

                # Lambda環境の場合はS3にアップロード
                if IS_LAMBDA and "japanese_audio_file" in processed:
                    japanese_s3_path = f"audio/japanese/{os.path.basename(processed['japanese_audio_file'])}"

                    processed["japanese_audio_url"] = upload_to_s3(
                        processed["japanese_audio_file"], japanese_s3_path)

                    # 一時ファイルのパスは削除（不要になったため）
                    del processed["japanese_audio_file"]

                # 処理済み記事を追加
                processed_articles.append(processed)

                logger.info(f"記事を処理しました: {processed['title']}")
            except Exception as e:
                logger.error(
                    f"記事「{article['title']}」の処理中にエラー: {str(e)}", exc_info=True)

    except Exception as e:
        logger.error(f"記事取得・処理中にエラー: {str(e)}", exc_info=True)

    # エピソードの生成（今日の日付で）
    if processed_articles:
        try:
            today = time.strftime("%Y-%m-%d")

            # エピソードデータ
            episode_data = {
                "episode_id": today,
                "title": f"Tech News ({today})",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "articles": processed_articles,
                "source": "Japanese Tech News"
            }

            # JSONファイルとして保存
            episode_filename = f"{AUDIO_DIR}/episode_{today}.json"
            with open(episode_filename, "w", encoding="utf-8") as f:
                json.dump(episode_data, f, ensure_ascii=False, indent=2)

            # Lambda環境ではS3にアップロード、ローカル環境では適切なディレクトリにコピー
            if IS_LAMBDA:
                episode_s3_path = f"data/episodes/episode_{today}.json"
                upload_to_s3(episode_filename, episode_s3_path)
                logger.info(f"エピソードをS3に保存しました: {episode_s3_path}")
            else:
                os.makedirs("data/episodes", exist_ok=True)
                local_path = f"data/episodes/episode_{today}.json"
                shutil.copy2(episode_filename, local_path)
                logger.info(f"エピソードをローカルに保存しました: {local_path}")

            # エピソードリストも更新
            update_episodes_list(episode_data)

            logger.info(f"エピソードを生成しました: {today}")
        except Exception as e:
            logger.error(f"エピソード生成中にエラー: {str(e)}", exc_info=True)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"{len(processed_articles)}件の記事を処理しました",
            "articles": [a["title"] for a in processed_articles]
        }, ensure_ascii=False)
    }


# ローカル実行用
if __name__ == "__main__":
    # ローカル実行環境のディレクトリを準備
    os.makedirs("audio", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/episodes", exist_ok=True)

    # Lambda関数を実行
    logger.info("ローカル開発環境で実行中...")
    result = lambda_handler(None, None)
    logger.info(f"実行結果: {result}")
