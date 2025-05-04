import os
import logging
import openai
import google.generativeai as genai
from src.config import SUMMARY_MAX_LENGTH
from src.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    AI_PROVIDER
)

# ロギング設定
logger = logging.getLogger(__name__)

# OpenAI APIキーの設定（レガシーサポート用）
openai_client = None
if OPENAI_API_KEY:
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Google Gemini APIキーの設定
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def summarize_article(article_url, article_title, article_summary):
    """
    記事を要約する関数（AIプロバイダーを自動選択）
    """
    logger.info(f"記事要約開始: {article_title[:30]}...")

    if AI_PROVIDER == 'gemini' and GOOGLE_API_KEY:
        return summarize_with_gemini(article_url, article_title, article_summary)
    elif OPENAI_API_KEY:
        return summarize_with_openai(article_url, article_title, article_summary)
    else:
        error_msg = "有効なAI APIキーが設定されていません。"
        logger.error(error_msg)
        return error_msg


def summarize_with_openai(article_url, article_title, article_summary):
    """
    OpenAI APIを使用して記事を要約する
    """
    logger.info("OpenAI APIで要約処理")

    # 記事の本文を取得する処理（必要に応じて）
    # ここでは簡略化のため、タイトルとRSS内の要約を利用
    # 最大文字数を明示的に指定
    prompt = f"""以下の記事を{SUMMARY_MAX_LENGTH}文字以内の日本語で要約してください。
    全体で3行程度にまとめてください。
    タイトル: {article_title}
    概要: {article_summary}
    URL: {article_url}
    """

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "あなたはITニュースを簡潔に要約するアシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.5
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"OpenAI 要約完了: {len(summary)}文字")
        return summary
    except Exception as e:
        error_msg = f"OpenAI APIエラー: {str(e)}"
        logger.error(error_msg)
        return error_msg


def summarize_with_gemini(article_url, article_title, article_summary):
    """
    Google Gemini APIを使用して記事を要約する
    """
    logger.info("Gemini APIで要約処理")

    # 最大文字数を明示的に指定
    prompt = f"""以下の記事を{SUMMARY_MAX_LENGTH}文字以内の日本語で要約してください。
    全体で3行程度にまとめてください。
    タイトル: {article_title}
    概要: {article_summary}
    URL: {article_url}
    """

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)

        summary = response.text.strip()
        logger.info(f"Gemini 要約完了: {len(summary)}文字")
        return summary
    except Exception as e:
        error_msg = f"Gemini APIエラー: {str(e)}"
        logger.error(error_msg)
        return error_msg
