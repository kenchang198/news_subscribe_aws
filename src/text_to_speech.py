import boto3
from src.config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, POLLY_VOICE_ID, POLLY_ENGINE


def synthesize_speech(text, output_filename, voice_id=POLLY_VOICE_ID):
    """
    テキストを音声に変換してS3またはローカルに保存

    :param text: 音声に変換するテキスト
    :param output_filename: 出力ファイル名
    :param voice_id: 使用する音声ID（日本語ならTakumi、Mizukiなど）
    :return: 保存されたファイルのパス
    """
    # AWSのPollyクライアント初期化
    # polly_client = boto3.client(
    #     "polly",
    #     region_name='ap-northeast-1',
    #     aws_access_key_id=AWS_ACCESS_KEY_ID,
    #     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    # )
    polly_client = boto3.client("polly", region_name='ap-northeast-1')

    # 音声合成リクエスト
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat="mp3",
        VoiceId=voice_id,
        Engine=POLLY_ENGINE,
    )

    # ローカルにファイル保存
    if "AudioStream" in response:
        with open(output_filename, "wb") as file:
            file.write(response["AudioStream"].read())
        return output_filename
    else:
        return None


# 使用例
# audio_file = synthesize_speech(summarized_text, f"audio/{article_id}.mp3")
