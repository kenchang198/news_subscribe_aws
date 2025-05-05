import json
import os
import time
import logging
import datetime  # datetimeをインポート
from src.fetch_rss import fetch_rss
from src.process_article import process_article
from src.s3_uploader import upload_to_s3
# ナレーション関連をインポート
from src.narration_generator import generate_narration_texts
from src.polly_synthesizer import synthesize_and_upload_narrations
# 統合音声生成関連をインポート
from src.unified import (
    generate_unified_content,
    synthesize_unified_speech
)
from src.config import (
    MAX_ARTICLES_PER_FEED,
    AUDIO_DIR,
    IS_LAMBDA,
    RSS_FEEDS,
    S3_BUCKET_NAME,
    S3_PREFIX
)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROCESSED_IDS_FILENAME = "processed_article_ids.json"
PROCESSED_IDS_S3_KEY = f"data/{PROCESSED_IDS_FILENAME}"
PROCESSED_IDS_LOCAL_PATH = f"data/{PROCESSED_IDS_FILENAME}"
MAX_PROCESSED_IDS = 1000  # 保存するIDの最大件数


def load_processed_ids():
    """処理済み記事IDをロードする"""
    processed_ids = set()
    if IS_LAMBDA:
        import boto3
        from botocore.exceptions import ClientError
        s3_client = boto3.client('s3')
        try:
            response = s3_client.get_object(
                Bucket=S3_BUCKET_NAME,
                Key=PROCESSED_IDS_S3_KEY
            )
            ids_list = json.loads(response['Body'].read().decode('utf-8'))
            processed_ids = set(ids_list)
            logger.info(f"S3から{len(processed_ids)}件の処理済みIDを読み込みました")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.info("S3に処理済みIDファイルが存在しませんでした。新規作成します。")
            else:
                logger.error(f"S3からの処理済みID読み込み中にエラー: {e}")
        except Exception as e:
            logger.error(f"処理済みIDファイルの解析中にエラー: {e}")
    else:
        if os.path.exists(PROCESSED_IDS_LOCAL_PATH):
            try:
                with open(PROCESSED_IDS_LOCAL_PATH, "r", encoding="utf-8") as f:
                    ids_list = json.load(f)
                    processed_ids = set(ids_list)
                # logger メッセージを f-string 以外で結合
                log_msg = "ローカルから" + str(len(processed_ids)) + "件のIDをロード"
                logger.info(log_msg)
            except Exception as e:
                logger.error(f"ローカルの処理済みIDファイル読み込み中にエラー: {e}")
        else:
            logger.info("ローカルに処理済みIDファイルが存在しません。新規作成します。")
    return processed_ids


def save_processed_ids(processed_ids):
    """処理済み記事IDを保存する"""
    # set を list に変換してソート (任意だがデバッグしやすい)
    ids_list = sorted(list(processed_ids), reverse=True)

    # 最新 MAX_PROCESSED_IDS 件のみ保持
    if len(ids_list) > MAX_PROCESSED_IDS:
        ids_list = ids_list[:MAX_PROCESSED_IDS]
        logger.info(f"処理済みIDを最新{MAX_PROCESSED_IDS}件に制限しました。")

    if IS_LAMBDA:
        import boto3
        s3_client = boto3.client('s3')
        try:
            # Lambda環境では一時ファイルを/tmpに作成
            tmp_path = f"/tmp/{PROCESSED_IDS_FILENAME}"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(ids_list, f)
            # S3 にアップロード
            s3_client.upload_file(
                tmp_path, S3_BUCKET_NAME, PROCESSED_IDS_S3_KEY)
            logger.info(f"処理済みID {len(ids_list)}件をS3に保存しました")
        except Exception as e:
            logger.error(f"S3への処理済みID保存中にエラー: {e}")
    else:
        try:
            os.makedirs("data", exist_ok=True)
            with open(PROCESSED_IDS_LOCAL_PATH, "w", encoding="utf-8") as f:
                json.dump(ids_list, f, indent=2)  # ローカルは見やすいようにインデント
            logger.info(f"処理済みID {len(ids_list)}件をローカルに保存しました")
        except Exception as e:
            logger.error(f"ローカルへの処理済みID保存中にエラー: {e}")


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
        "source": "Tech News"
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
            tmp_file = f"/tmp/episodes_list.json"
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
    os.environ['TZ'] = 'Asia/Tokyo'
    time.tzset()
    """
    複数の日本語RSSフィードから記事を取得、要約して日本語音声を生成するLambda関数
    """
    logger.info("日本のITニュース記事処理を開始します...")

    all_articles = []
    processed_articles = []
    newly_processed_ids = set()

    os.makedirs(AUDIO_DIR, exist_ok=True)
    processed_ids = load_processed_ids()

    # ★ エピソードID（今日の日付）を先に決定
    today = time.strftime("%Y-%m-%d")

    try:
        # 複数のRSSフィードから記事を取得
        for source_id, feed_url in RSS_FEEDS.items():
            logger.info(f"{source_id}からフィードを取得します...")
            try:
                fetched_articles = fetch_rss(feed_url)

                # 処理済み記事を除外し、ソース情報を追加
                added_count = 0
                for article in fetched_articles:
                    if article['id'] not in processed_ids:
                        article["source_id"] = source_id
                        all_articles.append(article)
                        added_count += 1
                    # else:
                        # logger.debug(f"処理済み記事スキップ: {article['id']}")

                # ログメッセージを修正
                logger.info(f"{source_id}: {added_count}件の未処理記事を追加")
            except Exception as e:
                # logger エラーメッセージを短縮
                logger.error(
                    f"{source_id} 取得/フィルタエラー: {str(e)}", exc_info=True)

        # 最新の記事を優先（公開日でソート）
        all_articles.sort(key=lambda x: x.get("published", ""), reverse=True)

        # 各サイトから最大記事数を制限 & 処理済みIDを記録
        articles_per_source = {}
        selected_articles = []
        sources_at_limit = set()
        num_target_sources = len(RSS_FEEDS)

        for article in all_articles:
            if len(sources_at_limit) == num_target_sources:
                logger.info("すべてのソースが記事数上限に達したため、記事選択を終了します。")
                break

            source_id = article.get("source_id", "unknown")
            if source_id not in articles_per_source:
                articles_per_source[source_id] = 0

            if source_id not in sources_at_limit:
                if articles_per_source[source_id] < MAX_ARTICLES_PER_FEED:
                    selected_articles.append(article)
                    articles_per_source[source_id] += 1
                    newly_processed_ids.add(article['id'])
                    if articles_per_source[source_id] == MAX_ARTICLES_PER_FEED:
                        sources_at_limit.add(source_id)
                        log_msg = (f"ソース '{source_id}' が上限 "
                                   f"({MAX_ARTICLES_PER_FEED}) に達しました。")
                        logger.info(log_msg)

        logger.info(f"合計{len(selected_articles)}件の記事を処理対象としました")

        # 選択された記事を処理 (enumerate でインデックスを取得)
        for idx, article in enumerate(selected_articles):
            try:
                # 記事処理（要約など）のみ実行
                processed = process_article(article)

                processed_articles.append(processed)
                logger.info(
                    f"記事 {idx+1}/{len(selected_articles)} を処理: {processed['title']}")  # 進捗ログ改善

            except Exception as e:
                logger.error(
                    f"記事「{article['title']}」の処理中にエラー: {str(e)}", exc_info=True)

    except Exception as e:
        logger.error(f"記事取得・処理中にエラー: {str(e)}", exc_info=True)
    finally:
        # 実行中にエラーが発生しても、処理できたIDは保存する
        if newly_processed_ids:
            logger.info(f"今回処理した記事ID数: {len(newly_processed_ids)}")
            updated_processed_ids = processed_ids.union(newly_processed_ids)
            save_processed_ids(updated_processed_ids)
        else:
            logger.info("今回新しく処理した記事はありませんでした。")

    # この時点では episode_data をまだ保存しない（audio_url 確定後に保存）
    episode_data = None

    # --- 統合音声生成処理 ---
    if processed_articles:  # 処理された記事がある場合のみ統合音声生成
        try:
            logger.info("統合音声生成処理を開始します...")
            # 日付を取得 (Lambda実行時の日付)
            episode_date = datetime.date.today()

            # 統合コンテンツ（全ての記事と繋ぎナレーション）の生成
            unified_content = generate_unified_content(
                processed_articles, episode_date)

            # 音声ファイル名の決定
            date_str = unified_content["date"]
            audio_filename = f"{date_str}.mp3"

            # 音声ファイルのパス/URL設定
            if IS_LAMBDA:
                audio_s3_key = f"{S3_PREFIX}{audio_filename}"
                audio_local_path = None
            else:
                audio_s3_key = None
                audio_local_path = os.path.join(AUDIO_DIR, audio_filename)

            # 統合音声の合成と保存
            audio_url = synthesize_unified_speech(
                unified_content["full_text"],
                audio_s3_key,
                audio_local_path
            )

            # 統合音声生成が成功した場合、audio_url を episode_data に統合
            if processed_articles:
                episode_data = {
                    "episode_id": today,
                    "title": f"Tech News ({today})",
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "audio_url": audio_url,  # 追加
                    "articles": processed_articles,
                    "source": "Tech News"
                }

                # ディレクトリ作成
                if not IS_LAMBDA:
                    os.makedirs("data/episodes", exist_ok=True)

                try:
                    if IS_LAMBDA:
                        # S3にアップロード
                        tmp_episode_file = f"/tmp/episode_{today}.json"
                        with open(tmp_episode_file, "w", encoding="utf-8") as f:
                            json.dump(episode_data, f,
                                      ensure_ascii=False, indent=2)
                        episode_s3_path = f"data/episodes/episode_{today}.json"
                        upload_to_s3(tmp_episode_file, episode_s3_path)
                    else:
                        episode_filename = f"data/episodes/episode_{today}.json"
                        with open(episode_filename, "w", encoding="utf-8") as f:
                            json.dump(episode_data, f,
                                      ensure_ascii=False, indent=2)
                    # エピソードリストを更新
                    update_episodes_list(episode_data)
                    logger.info(f"エピソード（統合音声付き）を保存しました: {today}")
                except Exception as e:
                    logger.error(f"エピソード保存中にエラー: {e}", exc_info=True)
            else:
                logger.error("audio_url が取得できなかったため episode_data への統合をスキップします")

        except Exception as e:
            logger.error(f"統合音声生成処理中にエラーが発生しました: {e}", exc_info=True)
            # 統合音声生成エラーは致命的ではないため、処理を続行
    else:
        logger.info("処理対象の記事がなかったため、統合音声生成をスキップします。")
    # --- 統合音声生成処理 ここまで ---

    # --- 従来のナレーション生成・合成処理 (テスト検証用に一時的に残す) ---
    narration_s3_keys = {}
    if processed_articles and False:  # False条件で無効化
        try:
            logger.info("ナレーション音声の生成を開始します...")
            # 日付を取得 (Lambda実行時の日付)
            episode_date = datetime.date.today()
            # ナレーションテキスト生成
            narration_texts = generate_narration_texts(
                episode_date, processed_articles)
            # 音声合成とS3アップロード
            narration_s3_keys = synthesize_and_upload_narrations(
                narrations=narration_texts,
                episode_date=episode_date,
                s3_bucket=S3_BUCKET_NAME,
                s3_prefix=S3_PREFIX
            )
            logger.info("ナレーション音声の生成・アップロードが完了しました。")
        except Exception as e:
            logger.error(f"ナレーション生成中にエラーが発生しました: {e}", exc_info=True)
            # ナレーション生成エラーは致命的ではないため、処理を続行
    else:
        logger.info("従来のナレーション生成は無効化されています。")
    # --- 従来のナレーション生成・合成処理 ここまで ---

    # 従来のプレイリストメタデータ生成処理は無効化
    # 統合音声化に伴い、従来のメタデータ生成処理は不要となりました
    # 統合メタデータは src/unified/metadata_processor.py で生成されます

    logger.info("Lambda処理完了")

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
    os.makedirs("audio/narration", exist_ok=True)  # ナレーション音声用
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/episodes", exist_ok=True)
    os.makedirs("data/unified", exist_ok=True)  # 統合メタデータ用

    # デバッグモード（気になる処理を個別に実行する場合はここに追加）
    DEBUG_MODE = False
    if DEBUG_MODE:
        # 統合音声生成テスト用（既存インポートの再定義を避ける）
        from src.unified.metadata_processor import (
            create_unified_metadata,
            save_unified_metadata
        )

        try:
            logger.info("統合音声生成テスト開始...")

            # テスト用に2記事のみ取得
            articles = fetch_rss(RSS_FEEDS['hatena_it'])[:2]
            processed_articles = []

            # 記事処理
            for article in articles:
                processed = process_article(article)
                processed_articles.append(processed)

            # 統合コンテンツ生成
            unified_content = generate_unified_content(processed_articles)

            # 日付とファイル名設定
            date_str = unified_content["date"]
            audio_filename = f"{date_str}_test.mp3"
            audio_path = os.path.join(AUDIO_DIR, audio_filename)

            # 統合音声生成
            audio_url = synthesize_unified_speech(
                unified_content["full_text"],
                None,  # S3キーは使用しない
                audio_path  # ローカルパス
            )

            # メタデータ生成と保存
            if audio_url:
                metadata = create_unified_metadata(
                    processed_articles,
                    f"{date_str}_test",
                    audio_url,
                    unified_content["full_text"]
                )
                save_unified_metadata(metadata, f"{date_str}_test")
                logger.info(f"統合音声生成テスト完了: {audio_url}")
            else:
                logger.error("統合音声生成失敗")

        except Exception as e:
            logger.error(f"統合音声生成テスト中にエラー: {str(e)}", exc_info=True)

        logger.info("デバッグモード終了")
        exit(0)  # デバッグモードの場合はここで終了

    # Lambda関数を実行
    logger.info("ローカル開発環境で実行中...")
    result = lambda_handler(None, None)
    logger.info(f"実行結果: {result}")
