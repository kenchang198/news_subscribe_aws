import os
import boto3
import logging
from src.config import IS_LAMBDA, AWS_REGION, AUDIO_DIR

# ロギング設定
logger = logging.getLogger(__name__)


# 英語音声合成は不要なため、関数を削除


def synthesize_japanese_speech(text, output_filename, voice_id="Takumi"):
    """
    日本語テキストを音声に変換（男性声）
    """
    logger.info("日本語音声合成開始")

    try:
        polly_client = boto3.client('polly', region_name=AWS_REGION)

        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine='neural'
        )

        if "AudioStream" in response:
            with open(output_filename, 'wb') as file:
                file.write(response['AudioStream'].read())
            logger.info(f"日本語音声合成完了: {output_filename}")
            return output_filename
        else:
            logger.error("AudioStreamがレスポンスに含まれていません")
            return None
    except Exception as e:
        logger.error(f"日本語音声合成中にエラー: {str(e)}")
        return None


def generate_audio_for_article(article):
    """
    日本語の要約音声を生成（英語は省略）
    """
    logger.info(f"音声生成開始: {article['title']}")

    try:
        # ディレクトリが存在することを確認
        os.makedirs(AUDIO_DIR, exist_ok=True)

        # 英語音声は省略（リソース節約のため）
        
        # 日本語音声生成
        japanese_output_filename = f"{AUDIO_DIR}/{article['id']}_ja.mp3"
        japanese_audio = synthesize_japanese_speech(
            article["japanese_summary"],
            japanese_output_filename
        )

        # 音声ファイルのURLを記事情報に追加
        # ローカル環境ではファイルパス、Lambda環境ではS3 URLになる
        if japanese_audio:
            if IS_LAMBDA:
                # Lambda環境では後でS3にアップロードするための印をつける
                article["japanese_audio_file"] = japanese_audio
            else:
                # ローカル環境ではファイルパスをそのまま使用
                article["japanese_audio_url"] = japanese_audio

            logger.info(f"音声生成完了: {article['title']}")
        else:
            logger.error(f"音声生成に失敗しました: {article['title']}")

        return article
    except Exception as e:
        logger.error(f"音声生成中にエラー: {str(e)}")
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
    with open("data/processed_article.json", "r", encoding="utf-8") as f:
        article = json.load(f)

    # 音声生成
    article_with_audio = generate_audio_for_article(article)

    # 結果を出力
    print(f"英語音声ファイル: {article_with_audio.get('english_audio_url', 'なし')}")
    print(f"日本語音声ファイル: {article_with_audio.get('japanese_audio_url', 'なし')}")
