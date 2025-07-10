import re
import logging

logger = logging.getLogger(__name__)


def clean_article_title(title):
    """
    Clean article title by removing site names and other unwanted suffixes.
    
    Args:
        title (str): Original article title
        
    Returns:
        str: Cleaned article title
    """
    if not title:
        return title
    
    # パターン1: " - サイト名" 形式を除去
    # 例: "記事タイトル - 日本経済新聞"
    title = re.sub(r'\s*[-－]\s*[^-－]+$', '', title)
    
    # パターン2: " | サイト名" 形式を除去
    # 例: "記事タイトル | テクノエッジ TechnoEdge"
    title = re.sub(r'\s*\|\s*[^|]+$', '', title)
    
    # パターン3: "【サイト名】" 形式を除去
    # 例: "記事タイトル【ITmedia NEWS】"
    title = re.sub(r'【[^】]+】\s*$', '', title)
    
    # パターン4: "(サイト名)" 形式を除去
    # 例: "記事タイトル(マイナビニュース)"
    title = re.sub(r'\([^)]+\)\s*$', '', title)
    
    # パターン5: "｜サイト名" 形式を除去（全角パイプ）
    # 例: "記事タイトル｜日経クロステック"
    title = re.sub(r'\s*｜\s*[^｜]+$', '', title)
    
    # 前後の空白を除去
    title = title.strip()
    
    logger.debug(f"Title cleaned: '{title}'")
    
    return title


# テスト用
if __name__ == "__main__":
    test_cases = [
        "NVIDIA時価総額、世界初の4兆ドル突破　AI成長期待で - 日本経済新聞",
        "破産した秀和システムの出版事業を引き継いだ会社からの連絡を読んで、思わず笑ってしまった（CloseBox） | テクノエッジ TechnoEdge",
        "Google、新たなAI技術を発表【ITmedia NEWS】",
        "Apple、新型iPhone発表(マイナビニュース)",
        "Microsoft、クラウドサービス拡充｜日経クロステック",
        "通常のタイトル"
    ]
    
    for title in test_cases:
        cleaned = clean_article_title(title)
        print(f"Original: {title}")
        print(f"Cleaned:  {cleaned}")
        print()