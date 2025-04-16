import os
import boto3
import logging
from src.config import IS_LAMBDA, AWS_REGION, AUDIO_DIR

# ロギング設定
logger = logging.getLogger(__name__)


# 英語音声合成は不要なため、関数を削除


def synthesize_speech(text, output_filename, voice_id="Takumi"):
    """AWS Pollyを使用してテキストから音声を合成する"""
    logger.info("音声合成開始")

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


def generate_audio_for_article(article, episode_id, index):
    """記事の要約から音声を生成する"""
    logger.info(f"音声生成開始 ({episode_id}, Index {index+1}): {article['title']}")

    try:
        os.makedirs(AUDIO_DIR, exist_ok=True)

        audio_base_filename = f"{episode_id}_{index + 1}.mp3"
        output_filename = os.path.join(AUDIO_DIR, audio_base_filename)

        audio_file = synthesize_speech(
            article["summary"],
            output_filename
        )

        if audio_file:
            if IS_LAMBDA:
                article["audio_file"] = audio_file
            else:
                article["audio_url"] = audio_file
            logger.info(f"音声生成完了 ({episode_id}, Index {index+1})")
        else:
            logger.error(f"音声生成失敗 ({episode_id}, Index {index+1})")
            article["audio_file"] = None
            article["audio_url"] = None

        return article
    except Exception as e:
        logger.error(f"音声生成中にエラー ({episode_id}, Index {index+1}): {str(e)}")
        raise


# テスト実行用
if __name__ == "__main__":
    import json

    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 処理済み記事データをロード
    try:
        with open("data/processed_article.json", "r", encoding="utf-8") as f:
            article = json.load(f)
    except FileNotFoundError:
        logger.error(
            "Test file data/processed_article.json not found. Skipping test.")
        article = None

    if article:
        # 音声生成
        article_with_audio = generate_audio_for_article(article, "episode1", 0)

        # 結果を出力
        print(f"英語音声ファイル: {article_with_audio.get('english_audio_url', 'なし')}")
        print(
            f"音声ファイル: {article_with_audio.get('audio_file') or article_with_audio.get('audio_url', 'なし')}")
