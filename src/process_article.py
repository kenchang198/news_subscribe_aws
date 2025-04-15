# src/process_article.py を更新
import os
import logging
import openai
import google.generativeai as genai
from src.config import (
    IS_LAMBDA,
    OPENAI_API_KEY,
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    OPENAI_MODEL,  # OpenAIモデル設定をインポート
    AI_PROVIDER
)

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
JAPANESE_SUMMARY_PROMPT_TEMPLATE = """
以下の記事を要約してください。

【要約のガイドライン】
• 記事の主要なポイントを全て含める
• 最低でも8文以上、300-400字以上※の長さで要約すること（これは必須条件です）
• 音声で聞きやすいよう、自然な日本語で書く
• 技術用語はそのまま使用し、簡潔に説明を加える
• 記事の主張や結論を明確に伝える
• 内容をどうしても短くできない場合は、より詳細に説明することを優先する
• 箇条書きではなく、文章として構成する
• 記事の冒頭に「この記事は〜についてです」などの導入文を入れる
• 最後に結論や今後の展望について述べる
タイトル: {article_title}
URL: {article_url}
内容: {article_content}
※元の記事の文字数がこれより少ない場合や内容が短い場合、無理にこちらの文字数に合わせる必要はありません。
"""


def summarize_japanese_article(article_url, article_title, article_content):
    """
    日本語記事を直接要約する（AIプロバイダーを自動選択）
    """
    logger.info(f"日本語要約開始: {article_title[:30]}...")

    if AI_PROVIDER == 'gemini' and GOOGLE_API_KEY:
        logger.info("AI Provider: Gemini (Google API Key found)")
        return summarize_japanese_with_gemini(article_url, article_title, article_content)
    elif AI_PROVIDER == 'openai' and OPENAI_API_KEY:
        logger.info("AI Provider: OpenAI (OpenAI API Key found)")
        return summarize_japanese_with_openai(article_url, article_title, article_content)
    else:
        if not GOOGLE_API_KEY and not OPENAI_API_KEY:
            error_msg = "有効なAI APIキーが設定されていません (Google or OpenAI)。"
        elif AI_PROVIDER == 'gemini' and not GOOGLE_API_KEY:
            error_msg = f"AI_PROVIDER が 'gemini' ですが、GOOGLE_API_KEY が設定されていません。"
        elif AI_PROVIDER == 'openai' and not OPENAI_API_KEY:
            error_msg = f"AI_PROVIDER が 'openai' ですが、OPENAI_API_KEY が設定されていません。"
        else:
            error_msg = f"不明な AI_PROVIDER '{AI_PROVIDER}' または関連するAPIキーがありません。"
        logger.error(error_msg)
        return f"要約エラー: {error_msg}"


def summarize_japanese_with_openai(article_url, article_title, article_content):
    """
    OpenAI APIを使用して日本語記事を直接要約する
    """
    logger.info("OpenAI APIで日本語要約処理")

    # 共通プロンプトを使用
    prompt = JAPANESE_SUMMARY_PROMPT_TEMPLATE.format(
        article_title=article_title,
        article_url=article_url,
        article_content=article_content
    )

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,  # config.pyで指定されたモデルを使用
            messages=[
                {"role": "system", "content": "あなたはITニュースを音声で聞きやすく要約する専門家です。技術的な内容を正確に、わかりやすく伝えることを心がけてください。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000  # より長い要約のために増加
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"OpenAI 日本語要約完了: {len(summary)}文字")
        return summary
    except Exception as e:
        logger.error(f"OpenAI 日本語要約中にエラー: {str(e)}")
        return f"要約エラー: Error code: {type(e).__name__} - {str(e)}"


def summarize_japanese_with_gemini(article_url, article_title, article_content):
    """
    Google Gemini APIを使用して日本語記事を直接要約する
    """
    logger.info("Gemini APIで日本語要約処理")

    # 共通プロンプトを使用
    prompt = JAPANESE_SUMMARY_PROMPT_TEMPLATE.format(
        article_title=article_title,
        article_url=article_url,
        article_content=article_content
    )

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)

        summary = response.text.strip()
        logger.info(f"Gemini 日本語要約完了: {len(summary)}文字")
        return summary
    except Exception as e:
        logger.error(f"Gemini 日本語要約中にエラー: {str(e)}")
        return f"要約エラー: Error code: {type(e).__name__} - {str(e)}"


def translate_to_japanese(english_text):
    """
    英語テキストを日本語に翻訳する（AIプロバイダーを自動選択）
    """
    logger.info("日本語翻訳開始")

    if AI_PROVIDER == 'gemini' and GOOGLE_API_KEY:
        logger.info("AI Provider for Translation: Gemini")
        return translate_with_gemini(english_text)
    elif AI_PROVIDER == 'openai' and OPENAI_API_KEY:
        logger.info("AI Provider for Translation: OpenAI")
        return translate_with_openai(english_text)
    else:
        if not GOOGLE_API_KEY and not OPENAI_API_KEY:
            error_msg = "有効なAI APIキーが設定されていません (Google or OpenAI)。"
        elif AI_PROVIDER == 'gemini' and not GOOGLE_API_KEY:
            error_msg = f"AI_PROVIDER が 'gemini' ですが、GOOGLE_API_KEY が設定されていません。"
        elif AI_PROVIDER == 'openai' and not OPENAI_API_KEY:
            error_msg = f"AI_PROVIDER が 'openai' ですが、OPENAI_API_KEY が設定されていません。"
        else:
            error_msg = f"不明な AI_PROVIDER '{AI_PROVIDER}' または関連するAPIキーがありません。"
        logger.error(error_msg)
        return f"翻訳エラー: {error_msg}"


def translate_with_openai(english_text):
    """
    OpenAI APIを使用して英語テキストを日本語に翻訳する
    """
    logger.info("OpenAI APIで日本語翻訳処理")

    prompt = f"""
    Translate the following English text to natural Japanese.
    Ensure that technical terms are translated accurately.
    
    English:
    {english_text}
    """

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,  # config.pyで指定されたモデルを使用
            messages=[
                {"role": "system", "content": "You are an expert translator specializing in technical content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000  # より長い要約のために増加
        )

        translation = response.choices[0].message.content.strip()
        logger.info(f"OpenAI 日本語翻訳完了: {len(translation)}文字")
        return translation
    except Exception as e:
        logger.error(f"OpenAI 日本語翻訳中にエラー: {str(e)}")
        return f"翻訳エラー: Error code: {type(e).__name__} - {str(e)}"


def translate_with_gemini(english_text):
    """
    Google Gemini APIを使用して英語テキストを日本語に翻訳する
    """
    logger.info("Gemini APIで日本語翻訳処理")

    prompt = f"""
    Translate the following English text to natural Japanese.
    Ensure that technical terms are translated accurately.
    
    English:
    {english_text}
    """

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)

        translation = response.text.strip()
        logger.info(f"Gemini 日本語翻訳完了: {len(translation)}文字")
        return translation
    except Exception as e:
        logger.error(f"Gemini 日本語翻訳中にエラー: {str(e)}")
        return f"翻訳エラー: Error code: {type(e).__name__} - {str(e)}"


def process_article(article):
    """
    記事を要約する
    """
    logger.info(f"記事処理開始: {article['title'][:30]}...")

    try:
        # 日本語で直接要約
        japanese_summary = summarize_japanese_article(
            article["link"],
            article["title"],
            article["summary"]
        )

        # エラーメッセージが返ってきた場合は処理を続ける（フォールバック）
        if japanese_summary.startswith("要約エラー:"):
            logger.warning("日本語要約でエラーが発生しましたが、処理を続行します")

        # 記事情報を更新
        article["japanese_summary"] = japanese_summary

        # APIリソース消費を削減するため英語関連の処理を完全に省略

        # AI プロバイダー情報を追加
        article["ai_provider"] = AI_PROVIDER

        logger.info(f"記事処理完了: {article['title'][:30]}...")
        return article
    except Exception as e:
        logger.error(f"記事処理中にエラー: {str(e)}")
        # 基本情報だけでも記事を返す
        article["japanese_summary"] = f"記事処理エラー: {str(e)}"
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
        print("\n日本語要約:")
        print(processed["japanese_summary"])

        # 処理結果をファイルに保存
        with open("data/processed_article.json", "w", encoding="utf-8") as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
