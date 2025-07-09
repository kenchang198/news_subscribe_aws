# News Subscribe AWS - デプロイアーキテクチャ設計

## 概要
本プロジェクトは AWS Lambda を使用したニュース収集・音声合成システムです。RSS フィードからニュースを取得し、AI による要約を経て、Amazon Polly で音声ファイルを生成し、S3 に保存します。

## アーキテクチャ構成

### 1. インフラストラクチャ
- **AWS Lambda Function**: メインのニュース処理ロジック
- **Amazon S3**: 生成された音声ファイルの保存
- **Amazon Polly**: テキストから音声への変換
- **EventBridge (CloudWatch Events)**: 定期実行のスケジューリング
- **CloudFormation (SAM)**: インフラのコード化とデプロイ管理

### 2. デプロイツール
- **AWS SAM (Serverless Application Model)**: Lambda 関数のビルドとデプロイ

## デプロイフロー

### デプロイ手順
1. `.env` ファイルに環境変数を設定
2. `deploy.sh` スクリプトを実行
3. SAM が自動的にビルドとデプロイを実行

## 環境変数と設定

### 必須環境変数
- `S3_BUCKET_NAME`: 音声ファイル保存用 S3 バケット名
- `GOOGLE_API_KEY` または `OPENAI_API_KEY`: AI プロバイダーの API キー
- `AI_PROVIDER`: 使用する AI プロバイダー（gemini/openai）

### オプション環境変数
- `S3_PREFIX`: S3 内のプレフィックス（デフォルト: audio/）
- `POLLY_VOICE_ID`: Amazon Polly の音声 ID（デフォルト: Takumi）
- `SUMMARY_MAX_LENGTH`: 要約の最大文字数（デフォルト: 400）
- `TIME_ZONE`: タイムゾーン（デフォルト: Asia/Tokyo）
- `PROGRAM_NAME`: 番組名
- `OPENAI_MODEL`: OpenAI モデル名（デフォルト: gpt-3.5-turbo）
- `GEMINI_MODEL`: Gemini モデル名（デフォルト: gemini-1.5-pro）

## セキュリティ考慮事項

### API キーの管理
- API キーは環境変数として管理
- `.env` ファイルは Git 管理から除外
- 本番環境では AWS Systems Manager Parameter Store または Secrets Manager の使用を推奨

### IAM ロール
Lambda 関数には以下の権限が必要：
- S3: フルアクセス（指定バケットのみ）
- Polly: フルアクセス
- CloudWatch Logs: ログ書き込み権限

## デプロイ関連ファイル構成

### 必要なファイル
- `deploy.sh`: メインデプロイスクリプト
- `template.yaml`: SAM テンプレート
- `samconfig.toml`: SAM 設定ファイル（プロジェクト直下）
- `.env.example`: 環境変数のサンプル
- `requirements.txt`: Python 依存関係

### ローカル実行用
- `run_local.sh`: ローカル環境での実行スクリプト

## 今後の改善計画
1. Secrets Manager の導入による API キー管理の強化
2. CloudFormation スタックの分離（インフラ/アプリケーション）
3. ステージング環境の追加
4. 自動テストの拡充