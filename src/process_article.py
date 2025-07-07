# src/process_article.py を更新
import logging
import openai
import google.generativeai as genai
from src.utils import create_article_id
from src.config import (
    OPENAI_API_KEY,
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    OPENAI_MODEL,  # OpenAIモデル設定をインポート
    AI_PROVIDER,
    SUMMARY_MAX_LENGTH
)
import re

# ロギング設定
logger = logging.getLogger(__name__)

# OpenAI クライアント初期化（レガシーサポート用）
openai_client = None
if OPENAI_API_KEY:
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Google Gemini API 設定
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# 共通プロンプトテンプレート
SUMMARY_PROMPT_TEMPLATE = """
以下の記事を要約してください。

【要約のガイドライン】
• 記事の主要なポイントを全て含める
• 約400文字を目安とし、最大でも500文字以内に収まるように簡潔に記述してください。
• 音声で聞きやすいよう、自然な日本語で書く
• 技術用語はそのまま使用し、簡潔に説明を加える
• 記事の主張や結論を明確に伝える
• 箇条書きではなく、文章として構成する
• 記事の冒頭に「この記事は〜についてです」などの導入文を入れる
• 最後に結論や今後の展望について述べる
タイトル: {article_title}
URL: {article_url}
内容: {article_content}
※元の記事の文字数がこれより少ない場合や内容が短い場合、無理にこちらの文字数に合わせる必要はありません。
"""

MAX_RETRIES = 3


def summarize_article(article_url, article_title, article_content):
    """
    記事を直接要約する（AIプロバイダーを自動選択）
    """
    logger.info(f"要約開始: {article_title[:30]}...")

    if AI_PROVIDER == 'gemini' and GOOGLE_API_KEY:
        logger.info("AI Provider: Gemini (Google API Key found)")
        return summarize_with_gemini(
            article_url,
            article_title,
            article_content
        )
    elif AI_PROVIDER == 'openai' and OPENAI_API_KEY:
        logger.info("AI Provider: OpenAI (OpenAI API Key found)")
        return summarize_with_openai(
            article_url,
            article_title,
            article_content
        )
    else:
        if not GOOGLE_API_KEY and not OPENAI_API_KEY:
            error_msg = "有効なAI APIキーが設定されていません (Google or OpenAI)。"
        elif AI_PROVIDER == 'gemini' and not GOOGLE_API_KEY:
            error_msg = (
                "AI_PROVIDER が 'gemini' ですが、GOOGLE_API_KEY が設定されていません。"
            )
        elif AI_PROVIDER == 'openai' and not OPENAI_API_KEY:
            error_msg = (
                "AI_PROVIDER が 'openai' ですが、OPENAI_API_KEY が設定されていません。"
            )
        else:
            error_msg = (
                f"不明な AI_PROVIDER '{AI_PROVIDER}' または関連するAPIキーがありません。"
            )
        logger.error(error_msg)
        return f"要約エラー: {error_msg}"


def summarize_with_openai(article_url, article_title, article_content):
    """
    OpenAI APIを使用して記事を直接要約する
    """
    logger.info("OpenAI APIで要約処理")

    # 共通プロンプトを使用
    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        article_title=article_title,
        article_url=article_url,
        article_content=article_content
    )

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "あなたはITニュースを音声で聞きやすく要約する専門家です。"
                        "技術的な内容を正確に、わかりやすく伝えることを心がけてください。"
                    ),
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"OpenAI 要約完了: {len(summary)}文字")
        return summary
    except Exception as e:
        logger.error(f"OpenAI 要約中にエラー: {str(e)}")
        return f"要約エラー: Error code: {type(e).__name__} - {str(e)}"


def summarize_with_gemini(article_url, article_title, article_content):
    """
    Google Gemini APIを使用して記事を直接要約する
    """
    logger.info("Gemini APIで要約処理")

    # 共通プロンプトを使用
    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        article_title=article_title,
        article_url=article_url,
        article_content=article_content
    )

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)

        summary = response.text.strip()
        marker = "この記事は"
        if marker in summary:
            summary = summary[summary.index(marker):].strip()
        logger.info(f"Gemini 要約完了: {len(summary)}文字")
        return summary
    except Exception as e:
        logger.error(f"Gemini 要約中にエラー: {str(e)}")
        return f"要約エラー: Error code: {type(e).__name__} - {str(e)}"


# 英語翻訳関数は削除されました（使用されていないため）


def process_article(article):
    """
    記事を要約する
    """
    logger.info(f"記事処理開始: {article['title'][:30]}...")

    try:
        # 要約
        summary = summarize_article(
            article["link"],
            article["title"],
            article["summary"]
        )

        # エラーメッセージが返ってきた場合は処理を続ける（フォールバック）
        if summary.startswith("要約エラー:"):
            logger.warning("要約でエラーが発生しましたが、処理を続行します")

        # 文字数制限のチェックと切り詰め
        if len(summary) > SUMMARY_MAX_LENGTH:
            logger.warning(
                "要約が最大長(%s文字)を超えるため切り詰めます: %s文字",
                SUMMARY_MAX_LENGTH,
                len(summary),
            )
            # 文の途中で切れないように、最後の「。」で切り詰める
            summary_temp = summary[:SUMMARY_MAX_LENGTH]
            # 最後の「。」の位置を探す
            last_period_pos = summary_temp.rfind('。')
            if last_period_pos > 0:  # 「。」が見つかった場合
                summary = summary_temp[:last_period_pos+1]  # 「。」も含める
            else:
                # 「。」が見つからない場合は、単純に切り詰めて「。」を追加
                summary = summary_temp + '。'
            logger.info(f"切り詰め後の長さ: {len(summary)}文字")

        # 記事IDを生成（URLベースのハッシュ）
        article_url = article.get("link", "")
        article_id = create_article_id(article_url)

        # 元のURLを保持しつつ、IDを短い一意の値に変更
        article["url"] = article_url
        article["id"] = article_id

        # 記事情報を更新
        article["summary"] = summary

        # APIリソース消費を削減するため英語関連の処理を完全に省略
        article["english_summary"] = "Not generated"
        article["english_audio_url"] = None

        # AI プロバイダー情報を追加
        article["ai_provider"] = AI_PROVIDER

        logger.info(f"記事処理完了: {article['title'][:30]}...（ID: {article_id}）")
        return article
    except Exception as e:
        logger.error(f"記事処理中にエラー: {str(e)}")
        # 基本情報だけでも記事を返す
        article["summary"] = f"記事処理エラー: {str(e)}"
        article["ai_provider"] = "error"
        return article


# テスト実行用
if __name__ == "__main__":
    import json

    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # テスト記事データをロード
    with open("data/medium_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)

    # 最初の記事だけ処理
    if articles:
        processed = process_article(articles[0])

        print("英語要約:")
        print(processed["english_summary"])
        print("\n要約:")
        print(processed["summary"])

        # 処理結果をファイルに保存
        with open("data/processed_article.json", "w", encoding="utf-8") as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
