import os
import openai
from src.config import OPENAI_API_KEY, OPENAI_MODEL

# OpenAI APIキーの設定
client = openai.OpenAI(api_key=OPENAI_API_KEY)


def summarize_article(article_url, article_title, article_summary):
    # 記事の本文を取得する処理（必要に応じて）
    # ここでは簡略化のため、タイトルとRSS内の要約を利用

    prompt = f"""以下の記事を日本語で3行程度に要約してください。
    タイトル: {article_title}
    概要: {article_summary}
    URL: {article_url}
    """

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "あなたはITニュースを簡潔に要約するアシスタントです。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.5
    )

    return response.choices[0].message.content.strip()
