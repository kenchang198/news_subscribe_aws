# News Subscribe AWS

ITニュース記事の要約と音声合成による配信システム

## 概要

このプロジェクトは、RSSフィードからITニュース記事を取得し、AIを使って要約し、Amazon Pollyを使って音声合成することで、
耳でITニュースを聞けるようにするサービスです。

## 機能

- 日本語RSSフィードからニュース記事の取得
- AI（Google Gemini APIまたはOpenAI API）による記事の日本語要約
- Amazon Pollyによる日本語音声合成
- S3への音声ファイル保存
- リソース最適化（英語処理を省略）

## 技術スタック

- Python 3.9+
- AWS Lambda
- Amazon S3
- Amazon Polly
- Google Gemini API
- OpenAI API (レガシーサポート)
- AWS SAM (Serverless Application Model)

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
GEMINI_MODEL=gemini-pro  # または他の利用可能なモデル

# AI プロバイダー設定（'openai' または 'gemini'）
AI_PROVIDER=gemini

# Amazon Polly 設定
POLLY_VOICE_ID_EN=Matthew
POLLY_VOICE_ID_JA=Takumi
POLLY_ENGINE=neural
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

### 環境別デプロイ

このプロジェクトでは STG（ステージング）環境と本番環境の2つの環境をサポートしています。

#### 環境設定ファイル

環境ごとに設定ファイルを作成してください：

- `.env.stg` - ステージング環境用
- `.env.prod` - 本番環境用

テンプレートファイルをコピーして各環境用の設定ファイルを作成します：

```bash
# ステージング環境設定の作成
cp .env.example .env.stg

# 本番環境設定の作成
cp .env.example .env.prod
```

各環境ファイルで `S3_BUCKET_NAME` やその他の設定を環境に応じて変更してください。

#### デプロイコマンド

```bash
# ステージング環境へのデプロイ
./deploy.sh stg

# 本番環境へのデプロイ
./deploy.sh prod

# または、確認付きデプロイ（特に本番環境推奨）
./deploy-env.sh stg   # ステージング環境
./deploy-env.sh prod  # 本番環境（確認プロンプトあり）
```

#### 環境別リソース

各環境では以下のリソースが作成されます：

- **Lambda関数名**: `news-processing-stg` / `news-processing-prod`
- **CloudFormationスタック名**: `news-subscribe-stg` / `news-subscribe-prod`
- **S3バケット名**: 環境設定ファイルで指定
- **スケジュール名**: `NewsProcessingSchedule-stg` / `NewsProcessingSchedule-prod`

### 従来のデプロイ方法（非推奨）

従来の方法でデプロイすることも可能ですが、環境別デプロイを推奨します：

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
