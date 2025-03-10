import boto3
import os
from src.config import AWS_REGION, S3_BUCKET_NAME, S3_PREFIX


def upload_to_s3(local_file_path, object_name=None):
    """
    ローカルファイルをS3バケットにアップロードする

    :param local_file_path: アップロードするローカルファイルのパス
    :param object_name: S3オブジェクト名。指定しない場合はローカルファイル名を使用
    :return: アップロードが成功した場合はS3のURL、失敗した場合はNone
    """
    # オブジェクト名が指定されていない場合は、ファイル名を使用
    if object_name is None:
        object_name = os.path.basename(local_file_path)

    # 必要に応じてS3のプレフィックスを追加
    if S3_PREFIX:
        object_name = f"{S3_PREFIX}{object_name}"

    # S3クライアントを作成
    s3_client = boto3.client('s3', region_name=AWS_REGION)

    try:
        # ファイルをアップロード
        s3_client.upload_file(local_file_path, S3_BUCKET_NAME, object_name)

        # S3のURLを生成
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{object_name}"
        print(f"File uploaded to: {s3_url}")

        return s3_url
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None
