import os
import json
import logging
from datetime import datetime

from src.config import IS_LAMBDA, S3_BUCKET_NAME

# ロギング設定
logger = logging.getLogger(__name__)

def create_unified_metadata(processed_articles, episode_id, audio_url, full_text=None):
    """
    統合音声用のメタデータを作成する
    
    Parameters:
    processed_articles (list): 処理済み記事のリスト
    episode_id (str): エピソードID（通常は日付形式 YYYY-MM-DD）
    audio_url (str): 統合音声ファイルのURL/パス
    full_text (str, optional): 統合テキスト（省略可能）
    
    Returns:
    dict: メタデータ辞書
    """
    try:
        # 現在時刻をISO形式で取得
        current_time = datetime.now().isoformat()
        
        # 音声の長さを推定（あれば）
        duration = None
        if full_text:
            # 文字数から大まかな長さを推定（日本語1文字≒0.2秒）
            char_count = len(full_text)
            duration = int(char_count * 0.2) + 10  # 10秒のマージン
        
        # 記事情報の整形
        articles_data = []
        for article in processed_articles:
            article_data = {
                "id": article["id"],
                "title": article["title"],
                "summary": article["summary"],
                "link": article.get("url") or article.get("link", ""),
                "source": article.get("source", "はてなブックマーク"),
                "published": article.get("published", current_time)
            }
            articles_data.append(article_data)
        
        # メタデータ構造の作成
        metadata = {
            "episode_id": episode_id,
            "title": f"Tech News ({episode_id})",
            "created_at": current_time,
            "audio_url": audio_url,
            "duration": duration,
            "articles": articles_data,
            "source": "Tech News"
        }
        
        logger.info(f"統合メタデータを作成しました: {len(articles_data)}件の記事")
        return metadata
        
    except Exception as e:
        logger.error(f"メタデータ作成中にエラー: {str(e)}")
        raise

def save_unified_metadata(metadata, episode_id):
    """
    統合メタデータを保存する（S3またはローカル）
    
    Parameters:
    metadata (dict): 保存するメタデータ
    episode_id (str): エピソードID（通常は日付形式 YYYY-MM-DD）
    
    Returns:
    str: メタデータが保存されたパス/URL
    """
    try:
        # メタデータのJSON文字列化
        metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
        
        # Lambda環境ではS3に保存、それ以外はローカルに保存
        if IS_LAMBDA:
            import boto3
            from src.s3_uploader import upload_to_s3
            
            # 一時ファイルに書き出し
            tmp_file = f"/tmp/unified_metadata_{episode_id}.json"
            with open(tmp_file, "w", encoding="utf-8") as f:
                f.write(metadata_json)
                
            # S3にアップロード
            metadata_s3_key = f"data/unified/metadata_{episode_id}.json"
            s3_url = upload_to_s3(tmp_file, metadata_s3_key)
            
            # 最新のメタデータとしても保存
            latest_tmp_file = f"/tmp/latest_unified_metadata.json"
            with open(latest_tmp_file, "w", encoding="utf-8") as f:
                f.write(metadata_json)
                
            latest_s3_key = f"data/unified/latest_metadata.json"
            upload_to_s3(latest_tmp_file, latest_s3_key)
            
            logger.info(f"統合メタデータをS3に保存しました: {metadata_s3_key}")
            return s3_url
        else:
            # ローカルディレクトリを作成
            os.makedirs("data/unified", exist_ok=True)
            
            # 日付別ファイル
            local_path = f"data/unified/metadata_{episode_id}.json"
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(metadata_json)
                
            # 最新ファイル
            latest_path = "data/unified/latest_metadata.json"
            with open(latest_path, "w", encoding="utf-8") as f:
                f.write(metadata_json)
                
            logger.info(f"統合メタデータをローカルに保存しました: {local_path}")
            return local_path
            
    except Exception as e:
        logger.error(f"メタデータ保存中にエラー: {str(e)}")
        raise

def update_episodes_list(metadata):
    """
    エピソードリストを更新する
    
    Parameters:
    metadata (dict): 追加するエピソードのメタデータ
    
    Returns:
    list: 更新されたエピソードリスト
    """
    logger.info("エピソードリスト更新開始")
    
    episodes_list = []
    episodes_list_path = "data/episodes_list.json"
    
    # 既存のエピソードリストを読み込み
    try:
        if IS_LAMBDA:
            import boto3
            
            s3_client = boto3.client('s3')
            try:
                response = s3_client.get_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=episodes_list_path
                )
                episodes_list = json.loads(response['Body'].read().decode('utf-8'))
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
        "episode_id": metadata["episode_id"],
        "title": metadata["title"],
        "created_at": metadata["created_at"],
        "audio_url": metadata["audio_url"],
        "article_count": len(metadata["articles"]),
        "source": metadata["source"],
        "unified": True  # 統合音声フラグを追加
    }
    
    # 重複チェック（既存のエピソードを更新）
    existing_ids = [ep["episode_id"] for ep in episodes_list]
    if episode_summary["episode_id"] in existing_ids:
        # 既存エピソードのインデックスを探す
        idx = existing_ids.index(episode_summary["episode_id"])
        # 更新
        episodes_list[idx] = episode_summary
        logger.info(f"既存のエピソード {episode_summary['episode_id']} を更新しました")
    else:
        # 新規追加
        episodes_list.append(episode_summary)
        logger.info(f"新しいエピソード {episode_summary['episode_id']} を追加しました")
    
    # 日付順に並べ替え（新しい順）
    episodes_list.sort(key=lambda x: x["episode_id"], reverse=True)
    
    # エピソードリストを保存
    try:
        if IS_LAMBDA:
            from src.s3_uploader import upload_to_s3
            
            # S3に保存
            tmp_file = f"/tmp/episodes_list.json"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(episodes_list, f, ensure_ascii=False, indent=2)
            
            upload_to_s3(tmp_file, episodes_list_path)
            logger.info("統合エピソードリストをS3に保存しました")
        else:
            # ローカルに保存
            os.makedirs("data", exist_ok=True)
            with open(episodes_list_path, "w", encoding="utf-8") as f:
                json.dump(episodes_list, f, ensure_ascii=False, indent=2)
            logger.info("統合エピソードリストをローカルに保存しました")
    except Exception as e:
        logger.error(f"エピソードリスト保存中にエラー: {str(e)}")
    
    return episodes_list


# テスト実行用
if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # サンプル記事
    sample_articles = [
        {
            "id": "article1",
            "title": "サンプル記事1",
            "summary": "これはサンプル記事1の要約です。",
            "link": "https://example.com/article1",
            "source": "はてなブックマーク"
        },
        {
            "id": "article2",
            "title": "サンプル記事2",
            "summary": "これはサンプル記事2の要約です。",
            "link": "https://example.com/article2",
            "source": "はてなブックマーク"
        }
    ]
    
    # 統合メタデータの作成
    today = datetime.now().strftime("%Y-%m-%d")
    test_audio_url = f"https://example.com/audio/{today}.mp3"
    
    metadata = create_unified_metadata(
        sample_articles,
        today,
        test_audio_url,
        "統合テキストサンプル"
    )
    
    # メタデータ出力
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    
    # ローカル保存テスト
    if not IS_LAMBDA:
        saved_path = save_unified_metadata(metadata, today)
        print(f"メタデータ保存先: {saved_path}")
        
        # エピソードリスト更新
        episodes = update_episodes_list(metadata)
        print(f"更新後のエピソード数: {len(episodes)}")
