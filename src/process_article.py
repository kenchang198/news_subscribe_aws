# src/process_article.py を更新
import os
import logging
from openai import OpenAI
from src.config import IS_LAMBDA, OPENAI_API_KEY

# ロギング設定
logger = logging.getLogger(__name__)

# OpenAI クライアント初期化
client = OpenAI(api_key=OPENAI_API_KEY)


def summarize_english_article(article_url, article_title, article_content):
    """
    英語記事を要約する
    """
    logger.info(f"英語要約開始: {article_title}")

    prompt = f"""
    Summarize the following Medium article in clear, concise English in about
    250 words. Focus on the main ideas and key points. If there is code,
    just mention that "the article includes code examples" without including the actual code.
    
    Title: {article_title}
    URL: {article_url}
    Content: {article_content}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert technical writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"英語要約完了: {len(summary)}文字")
        return summary
    except Exception as e:
        logger.error(f"英語要約中にエラー: {str(e)}")
        return f"Error generating English summary: {str(e)}"


def translate_to_japanese(english_text):
    """
    英語テキストを日本語に翻訳する
    """
    logger.info("日本語翻訳開始")

    prompt = f"""
    Translate the following English text to natural Japanese.
    Ensure that technical terms are translated accurately.
    
    English:
    {english_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert translator specializing in technical content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800
        )

        translation = response.choices[0].message.content.strip()
        logger.info(f"日本語翻訳完了: {len(translation)}文字")
        return translation
    except Exception as e:
        logger.error(f"日本語翻訳中にエラー: {str(e)}")
        return f"翻訳エラー: {str(e)}"


def process_article(article):
    """
    記事を要約・翻訳する
    """
    logger.info(f"記事処理開始: {article['title']}")

    try:
        # 英語要約を生成
        english_summary = summarize_english_article(
            article["link"],
            article["title"],
            article["summary"]
        )

        # 日本語に翻訳
        japanese_summary = translate_to_japanese(english_summary)

        # 記事情報を更新
        article["english_summary"] = english_summary
        article["japanese_summary"] = japanese_summary

        logger.info(f"記事処理完了: {article['title']}")
        return article
    except Exception as e:
        logger.error(f"記事処理中にエラー: {str(e)}")
        raise


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
