import os
import boto3
import logging
from botocore.exceptions import ClientError

from src.config import (
    IS_LAMBDA,
    AWS_REGION,
    AUDIO_DIR,
    POLLY_VOICE_ID,
    S3_BUCKET_NAME,
    S3_PREFIX
)

# ロギング設定
logger = logging.getLogger(__name__)

def synthesize_unified_speech(text, s3_key=None, local_file_path=None, voice_id=POLLY_VOICE_ID):
    """
    テキストを一つの音声ファイルに合成し、S3またはローカルに保存する
    
    Parameters:
    text (str): 音声合成するテキスト
    s3_key (str, optional): S3に保存する際のキー（IS_LAMBDA=Trueの場合必須）
    local_file_path (str, optional): ローカルに保存する際のファイルパス（IS_LAMBDA=Falseの場合必須）
    voice_id (str, optional): Pollyの音声ID
    
    Returns:
    str: 音声ファイルのURL (S3の場合) またはローカルパス
    """
    try:
        # 引数の検証
        if IS_LAMBDA and not s3_key:
            logger.error("Lambda環境ではs3_keyの指定が必須です")
            return None
        if not IS_LAMBDA and not local_file_path:
            logger.error("ローカル環境ではlocal_file_pathの指定が必須です")
            return None
        
        # Pollyクライアントの初期化
        polly_client = boto3.client('polly', region_name=AWS_REGION)
        
        # 音声合成リクエスト
        logger.info(f"Pollyで音声合成開始 (Voice: {voice_id})")
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine='neural'
        )
        
        # レスポンスから音声データを取得
        if "AudioStream" in response:
            audio_stream = response['AudioStream'].read()
            
            # Lambda環境の場合はS3に保存
            if IS_LAMBDA:
                s3 = boto3.resource('s3')
                s3.Object(S3_BUCKET_NAME, s3_key).put(
                    Body=audio_stream,
                    ContentType='audio/mp3'
                )
                audio_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
                logger.info(f"音声ファイルをS3に保存: {s3_key}")
                return audio_url
            
            # ローカル環境の場合はファイルに保存
            else:
                # 親ディレクトリが存在しない場合は作成
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                with open(local_file_path, 'wb') as file:
                    file.write(audio_stream)
                
                logger.info(f"音声ファイルをローカルに保存: {local_file_path}")
                return local_file_path
        else:
            logger.error("AudioStreamがレスポンスに含まれていません")
            return None
            
    except ClientError as e:
        logger.error(f"Polly API呼び出し中にエラー: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"音声合成中にエラー: {str(e)}")
        return None


def estimate_duration(text):
    """テキストから概算の音声時間を計算 (秒単位)"""
    # 日本語の場合、1文字あたり約0.2秒として概算
    # ポーズや記号なども考慮して若干余裕を持たせる
    char_count = len(text)
    estimated_seconds = int(char_count * 0.2) + 10  # 10秒の余裕
    return estimated_seconds


# テスト実行用
if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # テストテキスト（短いテストテキストにする）
    test_text = "これはPollyによる統合音声合成のテストです。ニュース記事を一つの音声ファイルとして合成します。"
    
    # ローカルテスト
    local_path = os.path.join(AUDIO_DIR, "unified_test.mp3")
    result = synthesize_unified_speech(test_text, local_file_path=local_path)
    
    if result:
        print(f"音声ファイル生成成功: {result}")
        
        # 再生時間の予測
        duration = estimate_duration(test_text)
        print(f"予測再生時間: {duration}秒")
    else:
        print("音声ファイル生成失敗")
