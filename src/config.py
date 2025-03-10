import os
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込み
load_dotenv()

# AWS 設定
AWS_REGION = os.environ.get('AWS_REGION')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

# S3 設定
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
S3_PREFIX = os.environ.get('S3_PREFIX', 'audio/')

# OpenAI API 設定
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')

# Amazon Polly 設定
POLLY_VOICE_ID = os.environ.get('POLLY_VOICE_ID', 'Takumi')  # 日本語男性音声
POLLY_ENGINE = os.environ.get('POLLY_ENGINE', 'neural')  # standard または neural

# RSS フィード設定
RSS_FEEDS = [
    {
        'url': 'https://b.hatena.ne.jp/hotentry/it.rss',
        'name': 'はてなブックマーク - テクノロジー'
    },
    {
        'url': 'https://www.businessinsider.jp/feed/index.xml',
        'name': 'BUSINESS INSIDER JAPAN'
    }
]

# ローカル保存パス設定
LOCAL_AUDIO_DIR = os.environ.get('LOCAL_AUDIO_DIR', 'audio/')
LOCAL_DATA_DIR = os.environ.get('LOCAL_DATA_DIR', 'data/')

# アプリケーション設定
MAX_ARTICLES_PER_FEED = int(os.environ.get('MAX_ARTICLES_PER_FEED', '5'))
SUMMARY_MAX_LENGTH = int(os.environ.get('SUMMARY_MAX_LENGTH', '300'))
API_DELAY_SECONDS = float(os.environ.get('API_DELAY_SECONDS', '1.0'))

# ロギング設定
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')