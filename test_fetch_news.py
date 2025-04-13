#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RSSフィードからニュース記事を取得するテスト用スクリプト
"""

import os
import logging
from src.fetch_news import fetch_news_articles, save_articles_for_testing

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # ディレクトリが存在することを確認
    os.makedirs("data", exist_ok=True)
    
    logger.info("RSSフィードから記事を取得します...")
    
    # ニュース記事を取得
    articles = fetch_news_articles()
    
    # 取得した記事を表示
    logger.info(f"合計{len(articles)}件の記事を取得しました")
    
    # 最初の5件だけ表示
    for i, article in enumerate(articles[:5], 1):
        print(f"\n記事 {i}")
        print(f"タイトル: {article['title']}")
        print(f"出典: {article['source']} ({article['source_id']})")
        print(f"リンク: {article['link']}")
        print(f"概要: {article['summary'][:150]}..." if len(article['summary']) > 150 else f"概要: {article['summary']}")
    
    # テスト用にファイルに保存
    filepath = save_articles_for_testing(articles)
    print(f"\n記事データを保存しました: {filepath}")
    
    print("\nテスト完了!")
