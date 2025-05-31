import os
import boto3
import logging
from src.config import AWS_REGION, AUDIO_DIR, POLLY_VOICE_ID

# ロギング設定
logger = logging.getLogger(__name__)


# 英語音声合成は不要なため、関数を削除


def synthesize_speech(text, output_filename, voice_id=POLLY_VOICE_ID):
    """AWS Pollyを使用してテキストから音声を合成する"""
    logger.info(f"音声合成開始 (Voice: {voice_id})")

    try:
        polly_client = boto3.client('polly', region_name=AWS_REGION)
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine='neural'
        )

        if "AudioStream" in response:
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)
            with open(output_filename, 'wb') as file:
                file.write(response['AudioStream'].read())
            logger.info(f"音声合成完了: {output_filename}")
            return output_filename
        else:
            logger.error("AudioStreamがレスポンスに含まれていません")
            return None
    except Exception as e:
        logger.error(f"音声合成中にエラー: {str(e)}")
        return None


# generate_audio_for_article は統合音声方式へ移行したため削除しました。


# テスト実行用
if __name__ == "__main__":
    logger.info("synthesize_speech の簡易テストを実行します。")
    sample_text = "これはテスト音声です。"
    output_path = os.path.join(AUDIO_DIR, "sample_test.mp3")
    result = synthesize_speech(sample_text, output_path)
    if result:
        logger.info(f"テスト音声生成成功: {result}")
    else:
        logger.error("テスト音声生成失敗")
