import os
from dotenv import load_dotenv
import logging  # logging をインポート

# --- .env ファイルのパスを明示的に指定 ---
# config.py の場所を基準に .env ファイルの絶対パスを組み立てる
# (プロジェクトルートに .env があると仮定)
dotenv_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '.env'))
logger_config_path = logging.getLogger(__name__ + ".config_path")
logger_config_path.info(f"Attempting to load .env file from: {dotenv_path}")

# .env ファイルから環境変数を読み込み (パスを明示的に指定)
# override=True は、もし複数回 load_dotenv が呼ばれた場合に上書きを許可する
dotenv_loaded = load_dotenv(dotenv_path=dotenv_path, override=True)
if not dotenv_loaded:
    logger_config_path.warning(
        f".env file specified but not loaded from: {dotenv_path}")
# --- ここまで ---

# --- デバッグログ追加 --- #
logger_config = logging.getLogger(__name__ + ".config")  # config 用ロガー
loaded_google_key = os.environ.get('GOOGLE_API_KEY')
if loaded_google_key:
    logger_config.info(
        "src/config.py: GOOGLE_API_KEY loaded from environment.")
    # セキュリティのためキーの一部のみ表示
    logger_config.info(
        f"src/config.py: GOOGLE_API_KEY starts with: {loaded_google_key[:5]}...")
else:
    logger_config.warning(
        "src/config.py: GOOGLE_API_KEY not found in environment after load_dotenv()!")
# --- デバッグログ追加 ここまで --- #

# Lambda環境かどうかを判定
IS_LAMBDA = os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None

# AWS 設定
AWS_REGION = os.environ.get('AWS_REGION', 'ap-northeast-1')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

# S3 設定
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
S3_PREFIX = os.environ.get('S3_PREFIX', 'audio/')

# OpenAI API 設定（レガシーサポート用）
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')

# Google Gemini API 設定
GOOGLE_API_KEY = loaded_google_key
GEMINI_MODEL = os.environ.get(
    'GEMINI_MODEL', 'gemini-pro')  # gemini-proをデフォルトに変更

# AI プロバイダー設定
AI_PROVIDER = os.environ.get('AI_PROVIDER', 'gemini')  # 'openai' または 'gemini'

# Amazon Polly 設定
POLLY_VOICE_ID_EN = os.environ.get('POLLY_VOICE_ID_EN', 'Matthew')  # 英語男性音声
POLLY_VOICE_ID_JA = os.environ.get('POLLY_VOICE_ID_JA', 'Takumi')   # 日本語男性音声
POLLY_ENGINE = os.environ.get('POLLY_ENGINE', 'neural')  # standard または neural

# フィード設定
# 複数のフィードを登録
RSS_FEEDS = {
    'hatena_it': 'https://b.hatena.ne.jp/hotentry/it.rss',
    # 'business_insider': 'https://www.businessinsider.jp/feed/index.xml'
}

# レガシーサポート用
MEDIUM_FEED_URL = os.environ.get(
    'MEDIUM_FEED_URL', 'https://medium.com/feed/tag/programming')

# アプリケーション設定
MAX_ARTICLES_PER_FEED = int(os.environ.get('MAX_ARTICLES_PER_FEED', '5'))
SUMMARY_MAX_LENGTH = int(os.environ.get(
    'SUMMARY_MAX_LENGTH', '800'))  # 要約の長さを増やす
API_DELAY_SECONDS = float(os.environ.get('API_DELAY_SECONDS', '1.0'))

# 環境に応じたパス設定
if IS_LAMBDA:
    AUDIO_DIR = '/tmp'
    S3_OBJECT_DATA_DIR = 'data'
else:
    AUDIO_DIR = 'audio'
    LOCAL_DATA_DIR = 'data'
    S3_OBJECT_DATA_DIR = 'data'

# ロギング設定
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
