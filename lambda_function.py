import json
import os
import time
import logging
import shutil
import datetime  # datetimeをインポート
from src.fetch_rss import fetch_rss
from src.process_article import process_article
from src.text_to_speech import generate_audio_for_article
from src.s3_uploader import upload_to_s3
# ナレーション関連をインポート
from src.narration_generator import generate_narration_texts
from src.polly_synthesizer import synthesize_and_upload_narrations
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
                    if article['link'].startswith('https://github.com/'):
                        logger.info(f"GitHub URLをスキップしました: {article['title']} - {article['link']}")
                        continue
                        
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
                # ★ episode_id と index を渡すように変更
                processed = process_article(article)
                processed = generate_audio_for_article(processed, today, idx)

                # 音声合成とS3アップロード (Lambda環境でのみ実行)
                if IS_LAMBDA and "audio_file" in processed:
                    # ★ S3パス生成も新しいファイル名基準に
                    # os.path.basename はフルパスからファイル名部分を取得する
                    audio_filename = os.path.basename(
                        processed['audio_file'])
                    s3_path = f"audio/{audio_filename}"
                    processed["audio_url"] = upload_to_s3(
                        processed["audio_file"], s3_path)
                    del processed["audio_file"]

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

    # エピソードの生成
    if processed_articles:
        try:
            # ★ episode_id は既に決定済み
            # today = time.strftime("%Y-%m-%d") # 削除
            episode_data = {
                "episode_id": today,
                "title": f"Tech News ({today})",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "articles": processed_articles,
                "source": "Tech News"
            }

            # ディレクトリ作成
            if IS_LAMBDA:
                pass  # Lambda環境では必要ない
            else:
                os.makedirs("data/episodes", exist_ok=True)

            # エピソードデータを保存
            if IS_LAMBDA:
                # Lambda環境では一時ファイルを/tmpに作成
                tmp_episode_file = f"/tmp/episode_{today}.json"
                with open(tmp_episode_file, "w", encoding="utf-8") as f:
                    json.dump(episode_data, f, ensure_ascii=False, indent=2)
                # S3にアップロード
                episode_s3_path = f"data/episodes/episode_{today}.json"
                upload_to_s3(tmp_episode_file, episode_s3_path)
            else:
                # ローカル環境では直接ファイルに書き込み
                episode_filename = f"data/episodes/episode_{today}.json"
                with open(episode_filename, "w", encoding="utf-8") as f:
                    json.dump(episode_data, f, ensure_ascii=False, indent=2)
                logger.info(f"エピソードをS3に保存しました: {episode_s3_path}")

            # エピソードリストも更新
            update_episodes_list(episode_data)

            logger.info(f"エピソードを生成しました: {today}")
        except Exception as e:
            logger.error(f"エピソード生成中にエラー: {str(e)}", exc_info=True)

    # --- ナレーション生成・合成処理 ---
    narration_s3_keys = {}
    if processed_articles:  # 処理された記事がある場合のみナレーション生成
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
        logger.info("処理対象の記事がなかったため、ナレーション生成をスキップします。")
    # --- ナレーション生成・合成処理 ここまで ---

    # メタデータ生成
    def build_s3_url(s3_key):
        if s3_key:
            return f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
        return None

    intro_s3_key = narration_s3_keys.get('intro')
    outro_s3_key = narration_s3_keys.get('outro')

    # シームレス再生用のメタデータ　（プレイリスト形式）
    metadata_data = {
        "episode_id": today,
        "title": f"Tech News ({today})",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "intro_audio_url": build_s3_url(intro_s3_key),
        "outro_audio_url": build_s3_url(outro_s3_key),
        "playlist": [],  # プレイリスト形式での再生順序を定義
        "sources": ["Tech News"]
    }

    # エピソードデータ（APIで使用する記事情報）
    episode_data = {
        "episode_id": today,
        "title": f"Tech News ({today})",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "articles": [],
        "source": "Tech News"
    }

    # プレイリストの构築
    # 1. イントロナレーション
    if intro_s3_key:
        metadata_data["playlist"].append({
            "type": "intro",
            "audio_url": build_s3_url(intro_s3_key)
        })
    
    # 各記事のデータを処理
    for idx, article in enumerate(processed_articles):
        # URLが正しく設定されているか確認
        article_url = article.get("url") or article.get("link", "")
        article_id = article["id"]
        
        # エピソードデータ用（API用）
        article_data = {
            "id": article_id,  # 新しい短いID形式
            "url": article_url,  # 元のURLを保持
            "title": article["title"],
            "summary": article["summary"],
            "audio_url": article.get("audio_url"),
            "duration": article.get("duration"),
            "published": article.get("published"),
            "source_id": article.get("source_id", "unknown")
        }
        episode_data["articles"].append(article_data)
        
        # メタデータ用プレイリストの構築
        # 2a. 記事イントロナレーション
        transition_key = narration_s3_keys.get(f'transition_{idx+1}')
        if transition_key:
            metadata_data["playlist"].append({
                "type": "article_intro",
                "article_id": article_id,
                "audio_url": build_s3_url(transition_key)
            })
        
        # 2b. 記事本体
        if article.get("audio_url"):
            metadata_data["playlist"].append({
                "type": "article",
                "article_id": article_id,
                "audio_url": article["audio_url"]
            })
    
    # 3. エンディング
    if outro_s3_key:
        metadata_data["playlist"].append({
            "type": "outro",
            "audio_url": build_s3_url(outro_s3_key)
        })

    # エピソードリストを更新
    update_episodes_list(episode_data)

    # 生成されたメタデータを保存
    # ディレクトリ作成
    if IS_LAMBDA:
        pass  # Lambda環境では必要ない
    else:
        os.makedirs("data/metadata", exist_ok=True)
        
    metadata_filename = f"metadata_{today}.json"
    if IS_LAMBDA:
        # Lambda環境では一時ファイルを/tmpに作成
        tmp_metadata_file = f"/tmp/{metadata_filename}"
        with open(tmp_metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, ensure_ascii=False, indent=2)
        # S3 にアップロード
        metadata_s3_key = f"data/metadata/{metadata_filename}"
        metadata_s3_url = upload_to_s3(tmp_metadata_file, metadata_s3_key)
        logger.info(f"再生用メタデータをS3に保存しました: {metadata_s3_url}")
    else:
        # ローカル環境では直接ファイルに書き込み
        local_metadata_path = f"data/metadata/{metadata_filename}"
        with open(local_metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, ensure_ascii=False, indent=2)
        logger.info(f"再生用メタデータをローカルに保存しました: {local_metadata_path}")

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
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/episodes", exist_ok=True)

    # Lambda関数を実行
    logger.info("ローカル開発環境で実行中...")
    result = lambda_handler(None, None)
    logger.info(f"実行結果: {result}")
