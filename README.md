# News Subscribe AWS

ITニュース記事の要約と音声合成による配信システム

## 概要

このプロジェクトは、RSSフィードからITニュース記事を取得し、AIを使って要約し、Amazon Pollyを使って音声合成することで、耳でITニュースを聞けるようにするサービスです。

定期的にニュースフィードをチェックし、新しい記事を自動的に処理して音声ファイルとして保存します。

## 主な機能

- **ニュース取得**: 日本語RSSフィードから最新のITニュース記事を自動取得
- **AI要約**: Google Gemini APIまたはOpenAI APIを使用した記事の要約生成
- **音声合成**: Amazon Pollyによる自然な日本語音声への変換
- **クラウド保存**: 生成された音声ファイルをS3に自動保存
- **定期実行**: AWS Lambdaによるサーバーレス定期実行

## アーキテクチャ

```
RSS Feeds → Lambda Function → AI API → Amazon Polly → S3 Storage
```

- **Lambda Function**: メイン処理を実行するサーバーレス関数
- **AI API**: 記事要約のためのAIサービス（Gemini/OpenAI）
- **Amazon Polly**: テキストから音声への変換サービス
- **S3**: 音声ファイルの永続的なストレージ

## 技術スタック

- **ランタイム**: Python 3.9+
- **コンピュート**: AWS Lambda
- **ストレージ**: Amazon S3
- **音声合成**: Amazon Polly
- **AI**: Google Gemini API / OpenAI API
- **デプロイ**: AWS SAM (Serverless Application Model)
- **インフラ**: AWS CloudFormation

## クイックスタート

### 前提条件

- Python 3.9 以上
- AWS アカウント
- Google Cloud または OpenAI アカウント

### ローカル開発環境のセットアップ

1. **リポジトリをクローン**

```bash
git clone <リポジトリURL>
cd news_subscribe_aws
```

2. **仮想環境を作成**

```bash
python -m venv env
source env/bin/activate  # macOS/Linux
env\Scripts\activate     # Windows
```

3. **依存関係をインストール**

```bash
pip install -r requirements.txt
```

4. **環境設定**

`.env.example` をコピーして `.env` を作成します：

```bash
cp .env.example .env
```

環境変数の詳細な設定方法とAPIキーの取得方法については [DEPLOYMENT.md](docs/DEPLOYMENT.md#環境変数の設定) を参照してください。

## ローカルでの実行

ローカル環境でシステムを実行してテストできます：

```bash
# run_local.shスクリプトを使用
./run_local.sh

# または直接Pythonで実行
python lambda_function.py
```

## デプロイ

AWS環境へのデプロイについては、[DEPLOYMENT.md](docs/DEPLOYMENT.md) を参照してください。

以下の環境をサポートしています：
- **ステージング環境** (STG): テスト用環境
- **本番環境** (PROD): 本番運用環境

詳細なデプロイ手順、環境設定、トラブルシューティングについては [DEPLOYMENT.md](docs/DEPLOYMENT.md) をご覧ください。

## プロジェクト構成

```
news_subscribe_aws/
├── lambda_function.py      # Lambda関数のエントリーポイント
├── src/                    # ソースコード
│   ├── rss_fetcher.py     # RSSフィード取得
│   ├── summarizer.py      # AI要約処理
│   ├── text_to_speech.py  # 音声合成処理
│   └── s3_uploader.py     # S3アップロード
├── template.yaml          # SAM テンプレート
├── requirements.txt       # Python依存関係
├── deploy.sh             # デプロイスクリプト
├── deploy-env.sh         # 環境別デプロイスクリプト
└── run_local.sh          # ローカル実行スクリプト
```

## 設定ファイル

- `.env.example` - 環境変数のテンプレート
- `.env` - ローカル開発用の環境変数
- `.env.stg` - ステージング環境用の環境変数
- `.env.prod` - 本番環境用の環境変数

## 開発ガイド

### 新機能の追加

1. `src/` ディレクトリに新しいモジュールを追加
2. `lambda_function.py` で新機能を統合
3. 必要に応じて `requirements.txt` を更新
4. ローカルでテスト後、ステージング環境でテスト

### テスト

```bash
# ユニットテストの実行（テストがある場合）
python -m pytest

# ローカル統合テスト
./run_local.sh
```

## 貢献

プルリクエストは歓迎します。大きな変更の場合は、まずissueを作成して変更内容を相談してください。

## ライセンス

[MIT](LICENSE)
