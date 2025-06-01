# flake8: noqa
import logging
import datetime
from src import config  # 番組名設定を利用

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
            episode_date = datetime.datetime.strptime(
                episode_date, "%Y-%m-%d").date()

        # 日本語の曜日
        weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]
        weekday_jp = weekdays_jp[episode_date.weekday()]

        # 日付をフォーマット
        formatted_date = f"{episode_date.month}月{episode_date.day}日{weekday_jp}曜日"

        # 挨拶文
        # 複数行のf-stringはトリプルクオートで囲む
        intro_text = f"""みなさんこんにちは本日は{formatted_date}です。
{config.PROGRAM_DESCRIPTION}"""

        # エンディングテキスト
        outro_text = """本日は以上です。
明日もお楽しみに。"""

        # Amazon Pollyの文字数制限を考慮したテキスト長端点
        MAX_TEXT_LENGTH = 2800  # Pollyの制限が3000文字なので、安全マージンとして200文字減らしておく

        # ナレーションの文字数を計算
        narration_length = len(intro_text) + len(outro_text)

        # 記事の処理
        articles_to_use = []
        running_length = narration_length

        # 最大5件までの記事を文字数制限内で選択
        for i, article in enumerate(processed_articles):
            # 記事導入ナレーションの長さを推定
            if i == 0:
                narration = f"まず最初に紹介する記事は{article['title']}です。\n\n"
            elif i == len(processed_articles) - 1:
                narration = f"最後の記事は{article['title']}です。\n\n"
            elif i == 1:
                narration = f"次の記事は{article['title']}です。\n\n"
            elif i == 2:
                narration = f"続いてご紹介するのは{article['title']}です。\n\n"
            elif i == 3:
                narration = f"4つ目の記事は{article['title']}です。\n\n"
            else:
                narration = f"{i+1}つ目の記事は{article['title']}です。\n\n"

            # この記事を追加した場合の総文字数を計算
            article_length = len(narration) + \
                len(article['summary']) + 2  # \n\nの分を2文字として加算

            # 文字数制限を超えないかチェック
            if running_length + article_length <= MAX_TEXT_LENGTH and len(articles_to_use) < 5:
                articles_to_use.append({
                    'article': article,
                    'narration': narration
                })
                running_length += article_length
                logger.info(
                    f"記事{i+1}を追加: {article['title'][:20]}... (総文字数: {running_length}/{MAX_TEXT_LENGTH})")
            else:
                logger.warning(
                    f"文字数制限のため記事{i+1}をスキップ: {article['title'][:20]}... (予測文字数: {running_length + article_length}>{MAX_TEXT_LENGTH})")
                # 5件以上の場合は記録のみ
                if len(articles_to_use) >= 5:
                    logger.info(f"記事数の制限(5件)に達しました")
                break  # これ以上は追加できないため処理を終了

        # 統合テキストを生成
        full_text = intro_text + "\n\n"

        # 選択した記事を統合
        for article_info in articles_to_use:
            # 記事導入ナレーション
            full_text += article_info['narration']

            # 記事本文
            full_text += f"{article_info['article']['summary']}\n\n"

        # エンディング
        full_text += outro_text

        logger.info(
            f"統合コンテンツ生成完了: {len(articles_to_use)}件の記事 (総文字数: {len(full_text)}文字)")

        return {
            "full_text": full_text,
            "article_count": len(articles_to_use),
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
