# News Subscribe AWS

ITニュース記事の要約と音声合成による配信システム

## 概要

このプロジェクトは、RSSフィードからITニュース記事を取得し、AIを使って要約し、Amazon Pollyを使って音声合成することで、
耳でITニュースを聞けるようにするサービスです。

## 機能

- 日本語RSSフィードからニュース記事の取得
- AI（Google Gemini APIまたはOpenAI API）による記事の日本語要約
- Amazon Pollyによる日本語音声合成
- 統合音声生成（複数記事を一つのポッドキャスト形式音声ファイルに統合）
- S3への音声ファイル保存
- エピソードメタデータの自動生成
- リソース最適化（英語処理を省略）

## 技術スタック

- Python 3.9+
- AWS Lambda
- Amazon S3
- Amazon Polly
- Google Gemini API
- OpenAI API (レガシーサポート)
- AWS SAM (Serverless Application Model)

## アーキテクチャ

### 統合音声生成システム

本システムでは、複数の記事を一つの音声ファイルに統合する「統合音声生成」機能を採用しています：

- `src/unified/content_generator.py` - 記事とナレーションを統合したコンテンツ生成
- `src/unified/speech_synthesizer.py` - 統合音声の合成とS3アップロード
- `src/unified/metadata_processor.py` - 統合メタデータの生成と管理

この統合アプローチにより、個別の音声ファイルではなく、ポッドキャスト形式の連続した音声コンテンツを提供します。

## 統合音声生成について

本システムの特徴的な機能として、複数のニュース記事を一つの連続した音声ファイルに統合する「統合音声生成」があります：

- **シームレスな聴取体験**: 個別の音声ファイルではなく、ポッドキャスト形式の連続音声
- **自動ナレーション**: 記事間の繋ぎナレーションを自動生成
- **文字数制限対応**: Amazon Pollyの制限内で最適な記事数を自動選択
- **日付ベースのエピソード管理**: 日付ごとのエピソード形式で管理

従来の個別音声ファイル生成機能も残されていますが、現在は統合音声生成がメインの機能として使用されています。

## セットアップ

### 前提条件

- AWS CLI がインストールされていること
- AWS SAM CLI がインストールされていること
- Python 3.9 以上がインストールされていること

#### pyenvをお使いの場合

pyenvでPythonのバージョンを管理している場合は、以下のコマンドでPythonのバージョンを設定してから実行してください：

```bash
# Pythonのバージョンを指定（例：Python 3.11.8）
pyenv global 3.11.8

# バージョンを確認
python --version
```

### ローカル開発環境のセットアップ

1. リポジトリをクローン

```bash
git clone <リポジトリURL>
cd news_subscribe_aws
```

2. 仮想環境を作成

```bash
python -m venv env
source env/bin/activate  # macOS/Linux
env\Scripts\activate     # Windows
```

3. 依存関係をインストール

```bash
pip install -r requirements.txt
```

4. `.env` ファイルの作成

`.env.example` をコピーして `.env` を作成し、必要な環境変数を設定します。

```bash
cp .env.example .env
```

### 環境変数の設定

`.env` ファイルに以下の環境変数を設定してください：

```
# AWS 設定
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key

# S3 設定
S3_BUCKET_NAME=your-bucket-name
S3_PREFIX=audio/

# AI API 設定
# OpenAI API（レガシーサポート）
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Google Gemini API
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-1.5-pro  # または他の利用可能なモデル

# AI プロバイダー設定（'openai' または 'gemini'）
AI_PROVIDER=gemini

# Amazon Polly 設定
POLLY_VOICE_ID_EN=Matthew  # 英語男性音声
POLLY_VOICE_ID=Takumi      # 日本語男性音声 
POLLY_ENGINE=neural        # standard または neural

# 番組設定
PROGRAM_NAME=Tech News Radio

# アプリケーション設定
MAX_ARTICLES_PER_FEED=5
SUMMARY_MAX_LENGTH=400  # 要約の最大文字数
API_DELAY_SECONDS=1.0

# ロギング設定
LOG_LEVEL=INFO
```

### Google Gemini API キーの取得方法

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. 「API キーを作成」をクリック
4. 作成されたAPIキーをコピーして `.env` ファイルの `GOOGLE_API_KEY` に設定

## ローカルでの実行

```bash
# run_local.shを使用する場合
./run_local.sh

# または直接実行する場合
python lambda_function.py
```

## AWS へのデプロイ

AWS SAM を使用してデプロイします：

```bash
sam build
sam deploy --guided  # 初回のみ
sam deploy  # 2回目以降
```

## 定期実行の設定

Lambda 関数を定期的に実行するには、EventBridge (CloudWatch Events) を設定します：

1. AWS コンソールから EventBridge (CloudWatch Events) にアクセス
2. 新しいルールを作成
3. スケジュール式を設定（例: `cron(0 1 * * ? *)` で毎日午前1時に実行）
4. ターゲットとしてこの Lambda 関数を選択

## ライセンス

[MIT](LICENSE)
