import os
import boto3
import logging
from src.config import IS_LAMBDA, AWS_REGION, AUDIO_DIR, POLLY_VOICE_ID

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


def generate_audio_for_article(article, episode_id, index):
    """記事の要約から音声を生成する
    
    注意: 統合音声生成方式への移行により、この関数は廃止予定です。
    互換性のために残していますが、実際には音声ファイルは生成しません。
    """
    logger.info(f"[廃止予定] 個別音声生成スキップ ({episode_id}, Index {index+1}): {article['title']}")

    try:
        # 個別音声ファイル生成は行わず、メタデータのみ設定
        
        # 互換性のためのダミーパス設定
        audio_base_filename = f"{episode_id}_{index + 1}.mp3"
        output_filename = os.path.join(AUDIO_DIR, audio_base_filename)
        
        # ダミーURLの設定
        if IS_LAMBDA:
            # 実際のS3パスではなく、統合ファイルへのマーカーを設定
            article["audio_file"] = f"unified/{episode_id}.mp3#{index}"
        else:
            # ローカルでも同様のマーカーを設定
            article["audio_url"] = f"unified/{episode_id}.mp3#{index}"
            
        logger.info(f"[廃止予定] 音声メタデータ設定のみ完了 ({episode_id}, Index {index+1})")
        
        return article
    except Exception as e:
        logger.error(f"音声メタデータ設定中にエラー ({episode_id}, Index {index+1}): {str(e)}")
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
