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

# OpenAI用のシステムメッセージ（挨拶・前置き禁止を強調）
OPENAI_SYSTEM_MESSAGE = (
    "あなたはITニュースを簡潔に要約するアシスタントです。\n"
    "以下のルールを厳守してください: \n"
    "1. 『はい、承知いたしました』などの挨拶や前置き表現を絶対に含めない。\n"
    f"2. 出力は要約本文のみとし、日本語で句点を用いた3文以内、{SUMMARY_MAX_LENGTH}文字以内でまとめる。\n"
)

# 各モデルで共通利用するプロンプトテンプレート
PROMPT_TEMPLATE = (
    "重要: 返答は要約本文のみであり、挨拶や前置きは絶対に含めないこと。\n"
    "以下の記事を{max_len}文字以内の日本語で要約してください。\n"
    "全体で3行程度にまとめてください。\n"
    "タイトル: {title}\n"
    "概要: {summary}\n"
    "URL: {url}\n"
)


def summarize_article(article_url, article_title, article_summary):
    """
    記事を要約する関数（AIプロバイダーを自動選択）
    """
    # 先頭30文字のみログに出力して行長を抑制
    logger.info("記事要約開始: %s...", article_title[:30])

    if AI_PROVIDER == 'gemini' and GOOGLE_API_KEY:
        return summarize_with_gemini(
            article_url,
            article_title,
            article_summary,
        )
    elif OPENAI_API_KEY:
        return summarize_with_openai(
            article_url,
            article_title,
            article_summary,
        )
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
    prompt = PROMPT_TEMPLATE.format(
        max_len=SUMMARY_MAX_LENGTH,
        title=article_title,
        summary=article_summary,
        url=article_url,
    )

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": OPENAI_SYSTEM_MESSAGE},
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
    prompt = PROMPT_TEMPLATE.format(
        max_len=SUMMARY_MAX_LENGTH,
        title=article_title,
        summary=article_summary,
        url=article_url,
    )

    try:
        # 新しいバージョンのGemini APIに対応
        # APIバージョンの問題を修正するため、完全修飾モデル名を使用
        model_name = GEMINI_MODEL
        if '/' not in model_name and not model_name.startswith('models/'):
            model_name = f'models/{model_name}'
        logger.info(f"Using Gemini model: {model_name}")
        
        # モデルインスタンスの作成
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        summary = response.text.strip()
        logger.info(f"Gemini 要約完了: {len(summary)}文字")
        return summary
    except Exception as e:
        error_msg = f"Gemini APIエラー: {str(e)}"
        logger.error(error_msg)
        return error_msg
