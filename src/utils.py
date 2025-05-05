import hashlib
import time
import random
import logging
import re

logger = logging.getLogger(__name__)

def create_article_id(url):
    """
    URLからハッシュを生成して短い一意のIDを作成する
    
    Args:
        url (str): 記事のURL
        
    Returns:
        str: 10文字のハッシュベースのID
    """
    if not url:
        timestamp = int(time.time())
        random_suffix = random.randint(100, 999)
        logger.warning(f"URLが空のため、タイムスタンプベースのIDを生成: {timestamp}_{random_suffix}")
        return f"{timestamp}_{random_suffix}"
        
    try:
        # URLからmd5ハッシュを生成し、最初の10文字を使用
        return hashlib.md5(url.encode()).hexdigest()[:10]
    except Exception as e:
        logger.error(f"記事ID生成エラー: {str(e)}")
        # エラー時はタイムスタンプベースのIDを生成
        timestamp = int(time.time())
        random_suffix = random.randint(100, 999)
        return f"{timestamp}_{random_suffix}"
def contains_japanese(text):
    """
    テキストに日本語文字（ひらがな、カタカナ、漢字）が含まれているかをチェックする
    
    Args:
        text (str): チェックするテキスト
        
    Returns:
        bool: 日本語文字が含まれている場合はTrue、そうでない場合はFalse
    """
    if not text:
        return False
        
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    
    return bool(japanese_pattern.search(text))
