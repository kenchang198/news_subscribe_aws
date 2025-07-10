import hashlib
import time
import random
import logging

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