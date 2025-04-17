import datetime
import boto3
import os
from botocore.exceptions import ClientError
import logging
from typing import Union
from src.config import POLLY_VOICE_ID, IS_LAMBDA, AUDIO_DIR

# ロガー設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

POLLY_OUTPUT_FORMAT = "mp3"


def synthesize_and_upload_narrations(
    narrations: dict[str, str],
    episode_date: datetime.date,
    s3_bucket: Union[str, None] = None,
    s3_prefix: Union[str, None] = None,
) -> dict[str, str]:
    """
    ナレーションテキストをPollyで音声合成し、S3またはローカルに保存する。

    Args:
        narrations: ナレーションの種類(key)とテキスト(value)の辞書。
        episode_date: エピソードの日付。
        s3_bucket: アップロード先のS3バケット名 (Lambda実行時のみ必須)。
        s3_prefix: アップロード先のS3プレフィックス (Lambda実行時のみ必須)。

    Returns:
        ナレーションの種類(key)と保存先パス(S3キーまたはローカルパス)(value)の辞書。
        エラーが発生した場合は空の辞書を返す可能性あり。
    """
    if IS_LAMBDA and (not s3_bucket or not s3_prefix):
        logger.error(
            "S3 bucket and prefix are required when running in Lambda environment.")
        return {}

    polly_client = boto3.client('polly')
    s3_client = boto3.client('s3') if IS_LAMBDA else None
    output_paths = {}
    date_str = episode_date.strftime("%Y-%m-%d")

    # ローカル保存用ディレクトリパス
    local_narration_dir = os.path.join(AUDIO_DIR, "narration")
    if not IS_LAMBDA:
        os.makedirs(local_narration_dir, exist_ok=True)

    for key, text in narrations.items():
        output_filename = f"{date_str}_{key}.{POLLY_OUTPUT_FORMAT}"

        if IS_LAMBDA:
            s3_key = f"{s3_prefix}/narration/{output_filename}"
            target_path_log = f"s3://{s3_bucket}/{s3_key}"
        else:
            local_path = os.path.join(local_narration_dir, output_filename)
            target_path_log = local_path

        logger.info(f"Synthesizing narration '{key}' to {target_path_log}")

        try:
            # Pollyで音声合成
            response = polly_client.synthesize_speech(
                Text=text,
                OutputFormat=POLLY_OUTPUT_FORMAT,
                VoiceId=POLLY_VOICE_ID,
                Engine='neural'
            )

            # レスポンスからオーディオストリームを取得
            audio_stream = response.get('AudioStream')
            if audio_stream:
                if IS_LAMBDA:
                    # S3に直接アップロード
                    s3_client.put_object(
                        Bucket=s3_bucket,
                        Key=s3_key,
                        Body=audio_stream.read(),
                        ContentType=f'audio/{POLLY_OUTPUT_FORMAT}'
                    )
                    logger.info(
                        f"Successfully uploaded '{key}' to {target_path_log}")
                    output_paths[key] = s3_key
                else:
                    # ローカルファイルに保存
                    with open(local_path, 'wb') as file:
                        file.write(audio_stream.read())
                    logger.info(
                        f"Successfully saved '{key}' to {target_path_log}")
                    output_paths[key] = local_path
            else:
                logger.error(
                    f"Could not get audio stream for narration '{key}'")

        except ClientError as e:
            # Polly APIエラーまたはS3アップロード/ファイル書き込みエラー
            logger.error(
                f"Error synthesizing or saving narration '{key}': {e}")
            continue  # 次のナレーションへ
        except Exception as e:
            # 予期せぬエラー
            logger.error(f"Unexpected error processing narration '{key}': {e}")
            continue  # 次のナレーションへ

    return output_paths


# --- 動作確認用 ---
if __name__ == '__main__':
    # loggingの基本設定 (コンソール出力用)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # boto3がAWS認証情報を見つけられるように設定が必要
    # 例: ~/.aws/credentials または 環境変数 AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
    logger.info("Checking AWS credentials configuration for Polly access.")
    # (実際にはここで認証チェックは行わず、boto3に任せる)

    TEST_DATE = datetime.date.today()
    # テスト用のナレーションデータ生成
    try:
        from src.narration_generator import generate_narration_texts
        sample_articles = [{'title': 'ローカルテスト記事1'}, {'title': 'ローカルテスト記事2'}]
        test_narrations = generate_narration_texts(TEST_DATE, sample_articles)
        logger.info(
            f"Generated {len(test_narrations)} narration texts for testing.")
    except ImportError:
        logger.error(
            "Failed to import generate_narration_texts. Make sure src/narration_generator.py exists.")
        test_narrations = {}

    if test_narrations:
        # --- ローカル実行 ---
        logger.info(
            "--- Running synthesize_and_upload_narrations in Local Mode ---")
        # IS_LAMBDA=Falseのはずなので、S3引数はNoneを渡す
        local_paths = synthesize_and_upload_narrations(
            test_narrations,
            TEST_DATE,
            s3_bucket=None,
            s3_prefix=None
        )

        if local_paths:
            print("\nSuccessfully generated local narration files:")
            for key, path in local_paths.items():
                print(f"  {key}: {path}")
                # ファイルが存在するか確認 (オプション)
                if os.path.exists(path):
                    print(f"    -> File exists: {path}")
                else:
                    print(f"    -> File NOT found: {path}")
        else:
            print("\nLocal generation failed or no narrations were processed.")
    else:
        print("\nSkipping synthesis due to missing narration texts.")
