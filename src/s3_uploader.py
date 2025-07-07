import boto3
import os
import logging
from src.config import AWS_REGION, S3_BUCKET_NAME, API_BASE_URL, IS_LAMBDA

logger = logging.getLogger(__name__)


def build_api_audio_url(file_path):
    """
    APIエンドポイント経由の音声ファイルURLを生成する
    
    :param file_path: S3キーまたはファイルパス
    :return: API経由のアクセスURL
    """
    # パスからファイル名を抽出
    file_name = os.path.basename(file_path)
    
    # 開発環境か本番環境かで分岐
    base_url = API_BASE_URL if IS_LAMBDA else "http://localhost:5001"
    
    # audio/で始まる場合は、そのまま使用
    if file_path.startswith('audio/'):
        return f"{base_url}/audio/{file_path}"
    else:
        return f"{base_url}/audio/{file_name}"

def upload_to_s3(local_file_path, object_name=None):
    """
    ローカルファイルをS3バケットにアップロードする

    :param local_file_path: アップロードするローカルファイルのパス
    :param object_name: S3オブジェクト名。指定しない場合はローカルファイル名を使用
    :return: アップロードが成功した場合はAPIゲートウェイ経由のURL、失敗した場合はNone
    """
    # オブジェクト名が指定されていない場合は、ファイル名を使用
    if object_name is None:
        object_name = os.path.basename(local_file_path)

    if IS_LAMBDA:
        # Lambda環境：S3にアップロード
        try:
            # S3クライアントを作成
            s3_client = boto3.client('s3', region_name=AWS_REGION)
            
            # ファイルをアップロード
            s3_client.upload_file(local_file_path, S3_BUCKET_NAME, object_name)
            
            # デバッグ用に元のS3 URLもログに記録
            s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{object_name}"
            logger.info(f"File uploaded to S3: {s3_url}")
            
            # APIゲートウェイ経由のURLを返す
            api_url = build_api_audio_url(object_name)
            logger.info(f"API access URL: {api_url}")
            
            return api_url
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            return None
    else:
        # ローカル環境：シミュレーションのURLを返す
        api_url = build_api_audio_url(object_name)
        logger.info(f"Local API access URL (simulated): {api_url}")
        return api_url
