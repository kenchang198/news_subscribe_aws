import logging
import datetime

# ロガー設定
logger = logging.getLogger(__name__)

def generate_unified_content(processed_articles, episode_date=None):
    """
    記事データとナレーションを統合したコンテンツを生成する
    
    Parameters:
    processed_articles (list): 処理済み記事のリスト
    episode_date (datetime.date, optional): エピソード日付（省略時は当日）
    
    Returns:
    dict: 統合コンテンツ情報
    """
    try:
        # 日付情報の取得と整形
        if episode_date is None:
            episode_date = datetime.date.today()
            
        if isinstance(episode_date, str):
            # YYYY-MM-DD形式の文字列からdatetime.dateオブジェクトに変換
            episode_date = datetime.datetime.strptime(episode_date, "%Y-%m-%d").date()
            
        # 日本語の曜日
        weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]
        weekday_jp = weekdays_jp[episode_date.weekday()]
        
        # 日付をフォーマット
        formatted_date = f"{episode_date.month}月{episode_date.day}日{weekday_jp}曜日"
        
        # 挨拶文
        # 複数行のf-stringはトリプルクオートで囲む
        intro_text = f"""みなさんこんにちは本日は{formatted_date}です。
本日もTech News Radioを元気よく初めていきます。"""
        
        # 記事本文とナレーションの統合
        full_text = intro_text + "\n\n"
        
        for i, article in enumerate(processed_articles):
            # 記事導入ナレーション
            if i == 0:
                full_text += f"まず最初に紹介する記事は{article['title']}です。\n\n"
            elif i == len(processed_articles) - 1:
                full_text += f"最後の記事は{article['title']}です。\n\n"
            elif i == 1:
                full_text += f"次の記事は{article['title']}です。\n\n"
            elif i == 2:
                full_text += f"続いてご紹介するのは{article['title']}です。\n\n"
            elif i == 3:
                full_text += f"4つ目の記事は{article['title']}です。\n\n"
            else:
                full_text += f"{i+1}つ目の記事は{article['title']}です。\n\n"
            
            # 記事本文
            full_text += f"{article['summary']}\n\n"
        
        # エンディング
        full_text += """本日のニュースは以上です。
明日もお楽しみに。"""
        
        logger.info(f"統合コンテンツ生成完了: {len(processed_articles)}件の記事")
        
        return {
            "full_text": full_text,
            "article_count": len(processed_articles),
            "date": episode_date.strftime("%Y-%m-%d")
        }
        
    except Exception as e:
        logger.error(f"統合コンテンツ生成中にエラー: {str(e)}")
        raise

# テスト実行用
if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # サンプル記事
    sample_articles = [
        {
            "id": "article1",
            "title": "AIの最新動向についての記事",
            "summary": "この記事はAIの最新動向について解説しています。近年、生成AIの発展により様々な分野でAIの活用が進んでいます。特に自然言語処理の分野では大きな進歩が見られ、テキスト生成や要約などのタスクにおいて人間に近い性能を発揮するようになってきました。今後もAI技術の発展は続くと予想されています。"
        },
        {
            "id": "article2",
            "title": "クラウドコンピューティングの展望",
            "summary": "クラウドコンピューティングは企業のITインフラを大きく変革しています。AWSやAzure、Google Cloudなどの主要プロバイダーは、より高度なサービスを提供し続けており、サーバーレスアーキテクチャやコンテナ技術の普及が進んでいます。特に最近ではエッジコンピューティングとの連携も注目されており、より効率的なデータ処理の実現が期待されています。"
        }
    ]
    
    # 統合コンテンツ生成
    unified_content = generate_unified_content(sample_articles)
    
    # 結果表示
    print("\n=== 統合テキスト ===\n")
    print(unified_content["full_text"])
    print("\n=== 統計情報 ===")
    print(f"記事数: {unified_content['article_count']}")
    print(f"日付: {unified_content['date']}")
