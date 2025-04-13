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


def summarize_english_article(article_url, article_title, article_content):
    """
    英語記事を要約する（AIプロバイダーを自動選択）
    """
    logger.info(f"英語要約開始: {article_title[:30]}...")
    
    if AI_PROVIDER == 'gemini' and GOOGLE_API_KEY:
        return summarize_english_with_gemini(article_url, article_title, article_content)
    elif OPENAI_API_KEY:
        return summarize_english_with_openai(article_url, article_title, article_content)
    else:
        error_msg = "有効なAI APIキーが設定されていません。"
        logger.error(error_msg)
        return f"Error generating English summary: {error_msg}"


def summarize_english_with_openai(article_url, article_title, article_content):
    """
    OpenAI APIを使用して英語記事を要約する
    """
    logger.info("OpenAI APIで英語要約処理")

    prompt = f"""
    Summarize the following Medium article in clear, concise English in about
    250 words. Focus on the main ideas and key points. If there is code,
    just mention that "the article includes code examples" without including the actual code.
    
    Title: {article_title}
    URL: {article_url}
    Content: {article_content}
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert technical writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"OpenAI 英語要約完了: {len(summary)}文字")
        return summary
    except Exception as e:
        logger.error(f"OpenAI 英語要約中にエラー: {str(e)}")
        return f"Error generating English summary: Error code: {type(e).__name__} - {str(e)}"


def summarize_english_with_gemini(article_url, article_title, article_content):
    """
    Google Gemini APIを使用して英語記事を要約する
    """
    logger.info("Gemini APIで英語要約処理")

    prompt = f"""
    Summarize the following article in clear, concise English in about
    250 words. Focus on the main ideas and key points. If there is code,
    just mention that "the article includes code examples" without including the actual code.
    
    Title: {article_title}
    URL: {article_url}
    Content: {article_content}
    """

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        summary = response.text.strip()
        logger.info(f"Gemini 英語要約完了: {len(summary)}文字")
        return summary
    except Exception as e:
        logger.error(f"Gemini 英語要約中にエラー: {str(e)}")
        return f"Error generating English summary: Error code: {type(e).__name__} - {str(e)}"


def translate_to_japanese(english_text):
    """
    英語テキストを日本語に翻訳する（AIプロバイダーを自動選択）
    """
    logger.info("日本語翻訳開始")
    
    if AI_PROVIDER == 'gemini' and GOOGLE_API_KEY:
        return translate_with_gemini(english_text)
    elif OPENAI_API_KEY:
        return translate_with_openai(english_text)
    else:
        error_msg = "有効なAI APIキーが設定されていません。"
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
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert translator specializing in technical content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800
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
    記事を要約・翻訳する
    """
    logger.info(f"記事処理開始: {article['title'][:30]}...")

    try:
        # 英語要約を生成
        english_summary = summarize_english_article(
            article["link"],
            article["title"],
            article["summary"]
        )

        # エラーメッセージが返ってきた場合は処理を続ける（フォールバック）
        if english_summary.startswith("Error generating English summary:"):
            logger.warning("英語要約でエラーが発生しましたが、処理を続行します")
        
        # 日本語に翻訳
        japanese_summary = translate_to_japanese(english_summary)
        
        # エラーメッセージが返ってきた場合は処理を続ける（フォールバック）
        if japanese_summary.startswith("翻訳エラー:"):
            logger.warning("日本語翻訳でエラーが発生しましたが、処理を続行します")

        # 記事情報を更新
        article["english_summary"] = english_summary
        article["japanese_summary"] = japanese_summary
        
        # AI プロバイダー情報を追加
        article["ai_provider"] = AI_PROVIDER

        logger.info(f"記事処理完了: {article['title'][:30]}...")
        return article
    except Exception as e:
        logger.error(f"記事処理中にエラー: {str(e)}")
        # 基本情報だけでも記事を返す
        article["english_summary"] = f"Error processing article: {str(e)}"
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
