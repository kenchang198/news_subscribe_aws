# News Subscribe AWS - デプロイメントガイド

このドキュメントでは、News Subscribe AWS システムのデプロイ方法について詳しく説明します。

## 目次
1. [前提条件](#前提条件)
2. [初回セットアップ](#初回セットアップ)
3. [環境別デプロイ](#環境別デプロイ)
4. [従来のデプロイ方法](#従来のデプロイ方法)
5. [ローカル実行](#ローカル実行)
6. [デプロイ後の確認](#デプロイ後の確認)
7. [定期実行の設定](#定期実行の設定)
8. [トラブルシューティング](#トラブルシューティング)
9. [セキュリティに関する注意事項](#セキュリティに関する注意事項)
10. [参考情報](#参考情報)

## 前提条件

### 必要なツール
- Python 3.9 以上
- AWS CLI がインストールされ、適切な認証情報で設定されていること
- AWS SAM CLI がインストールされていること

### AWS リソース
- AWS アカウント
- IAM ユーザー（プログラマティックアクセス可能）
- 必要な AWS 権限（Lambda、S3、CloudFormation、IAM、Amazon Polly、EventBridge）

### 必要な権限
IAM ユーザーには以下の権限が必要です：
- CloudFormation フルアクセス
- Lambda 関数の作成・更新・削除
- IAM ロールの作成・更新
- S3 バケットへのアクセス
- Amazon Polly へのアクセス
- EventBridge ルールの作成・更新

## 初回セットアップ

### 1. 環境変数の設定
```bash
# .env.example をコピーして .env を作成
cp .env.example .env

# .env ファイルを編集して必要な値を設定
# 特に以下の項目は必須：
# - S3_BUCKET_NAME
# - GOOGLE_API_KEY または OPENAI_API_KEY
# - AI_PROVIDER
```

### 2. AWS 認証情報の設定
```bash
# AWS CLI の設定
aws configure

# または環境変数で設定
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=ap-northeast-1
```

### 3. S3 バケットの作成（初回のみ）
```bash
# バケットを作成（バケット名は世界で一意である必要があります）
aws s3 mb s3://your-unique-bucket-name --region ap-northeast-1
```

## 環境別デプロイ

このプロジェクトでは STG（ステージング）環境と本番環境の2つの環境をサポートしています。

### 環境設定ファイルの準備

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

### 環境変数の設定

各環境ファイル（`.env`、`.env.stg`、`.env.prod`）に以下の環境変数を設定してください：

```
# AWS 設定
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key

# S3 設定
S3_BUCKET_NAME=your-bucket-name  # 環境ごとに異なるバケット名を推奨
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

#### APIキーの取得方法

- **Google Gemini API**: 
  1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
  2. Googleアカウントでログイン
  3. 「API キーを作成」をクリック
  4. 作成されたAPIキーをコピーして `GOOGLE_API_KEY` に設定

- **OpenAI API**: 
  1. [OpenAI Platform](https://platform.openai.com/) にアクセス
  2. アカウントを作成またはログイン
  3. API Keysセクションで新しいキーを作成
  4. 作成されたAPIキーをコピーして `OPENAI_API_KEY` に設定

- **AWS認証情報**: 
  1. AWS IAMコンソールにアクセス
  2. ユーザーを選択し、「セキュリティ認証情報」タブを開く
  3. 「アクセスキーを作成」をクリック
  4. アクセスキーIDとシークレットアクセスキーを安全に保存

**重要**: 各環境で `S3_BUCKET_NAME` やその他の設定を環境に応じて変更してください。

### デプロイコマンド

#### 基本的なデプロイ

```bash
# ステージング環境へのデプロイ
./deploy.sh stg

# 本番環境へのデプロイ
./deploy.sh prod
```

#### 確認付きデプロイ（推奨）

特に本番環境へのデプロイ時は、確認プロンプトがある `deploy-env.sh` の使用を推奨します：

```bash
# ステージング環境へのデプロイ
./deploy-env.sh stg

# 本番環境へのデプロイ（確認プロンプトあり）
./deploy-env.sh prod
```

### 環境別リソース

各環境では以下のリソースが作成されます：

| リソース | ステージング環境 | 本番環境 |
|---------|----------------|---------|
| Lambda関数名 | `news-processing-stg` | `news-processing-prod` |
| CloudFormationスタック名 | `news-subscribe-stg` | `news-subscribe-prod` |
| S3バケット名 | 環境設定ファイルで指定 | 環境設定ファイルで指定 |
| スケジュール名 | `NewsProcessingSchedule-stg` | `NewsProcessingSchedule-prod` |

### S3バケットの扱い

デプロイスクリプトは既存のS3バケットの有無を確認し、以下のように動作します：

1. **バケットが存在する場合**: 既存のバケットを使用
2. **バケットが存在しない場合**: 
   - `S3_BUCKET_NAME` が設定されている場合：指定された名前で新規作成
   - `S3_BUCKET_NAME` が空の場合：自動生成された名前で新規作成

### デプロイプロセスの詳細

1. **環境変数の読み込み**: 指定された環境の設定ファイルから環境変数を読み込みます
2. **SAMビルド**: `sam build` コマンドで Lambda 関数のビルドを実行
3. **S3バケットの確認/作成**: デプロイ用のS3バケットを確認し、必要に応じて作成
4. **SAMデプロイ**: `sam deploy` コマンドでリソースをデプロイ
5. **環境変数の設定**: Lambda 関数に環境変数を設定

### デプロイパラメータ

`deploy.sh` は以下のパラメータを自動的に設定します：
- `S3BucketName`: 音声ファイル保存用バケット
- `S3Prefix`: S3 内のプレフィックス
- `OpenAIApiKey`: OpenAI API キー
- `GoogleApiKey`: Google API キー
- `AIProvider`: AI プロバイダー（gemini/openai）
- `PollyVoiceId`: 音声合成に使用する声
- `SummaryMaxLength`: 要約の最大文字数
- `ProgramName`: 番組名
- `TimeZone`: タイムゾーン

## 従来のデプロイ方法

環境別デプロイを推奨しますが、従来の方法でデプロイすることも可能です：

### 標準的なデプロイ
```bash
# デプロイスクリプトを実行
./deploy.sh
```

このスクリプトは以下を実行します：
1. `.env` ファイルから環境変数を読み込み
2. SAM アプリケーションをビルド
3. CloudFormation スタックとしてデプロイ

### 手動デプロイ（詳細制御）
```bash
# 1. SAM アプリケーションをビルド
sam build

# 2. デプロイ（初回）
sam deploy --guided

# 3. デプロイ（2回目以降）
sam deploy
```

#### SAM の設定ファイル
- **`template.yaml`**: Lambda 関数やリソースの定義、パラメータのデフォルト値
- **`samconfig.toml`**: デプロイ設定（スタック名、リージョン等）
  - `sam deploy` はカレントディレクトリの `samconfig.toml` を自動的に読み込みます
  - このファイルは `.gitignore` に含まれるため、各開発者が個別に作成する必要があります

#### パラメータの優先順位
デプロイ時に使用されるパラメータの優先順位：
1. **`deploy.sh` が指定する値**（最優先）
   - `.env` ファイルから読み込んだ値
   - または `deploy.sh` 内のデフォルト値
2. **`template.yaml` の `Default` 値**
   - `deploy.sh` が指定しないパラメータのみ使用

#### 手動デプロイ時のパラメータ指定
```bash
# 特定のパラメータのみ変更
sam deploy --parameter-overrides \
  S3BucketName=my-bucket \
  AIProvider=openai

# パラメータファイルを使用
sam deploy --parameter-overrides file://parameters.json
```

## ローカル実行

### 開発環境での実行
```bash
# ローカル実行スクリプトを使用
./run_local.sh
```

このスクリプトは：
1. Python 仮想環境を作成（初回のみ）
2. 必要な依存関係をインストール
3. Lambda 関数をローカルで実行
4. 生成されたエピソードファイルを表示

### 手動でのローカル実行
```bash
# 仮想環境を作成・有効化
python3 -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を読み込んで実行
export $(grep -v '^#' .env | xargs)
python lambda_function.py
```

## デプロイ後の確認

デプロイが成功したら、以下を確認してください：

1. **Lambda関数**: AWS コンソールで Lambda 関数が作成されていることを確認
2. **環境変数**: Lambda 関数の設定で環境変数が正しく設定されていることを確認
3. **S3バケット**: 指定した S3 バケットが存在することを確認
4. **実行権限**: Lambda 関数が S3 と Polly にアクセスできることを確認

## 定期実行の設定

Lambda 関数を定期的に実行するには、EventBridge (CloudWatch Events) を設定します：

1. AWS コンソールから EventBridge (CloudWatch Events) にアクセス
2. 新しいルールを作成
3. スケジュール式を設定（例: `cron(0 1 * * ? *)` で毎日午前1時に実行）
4. ターゲットとして環境に応じた Lambda 関数を選択

## トラブルシューティング

### よくある問題と解決方法

#### 1. デプロイが失敗する
```bash
# CloudFormation スタックの状態を確認
aws cloudformation describe-stacks --stack-name news-subscribe-aws

# エラーイベントを確認
aws cloudformation describe-stack-events --stack-name news-subscribe-aws | head -20
```

1. **AWS認証情報**: `aws configure list` で認証情報が正しく設定されているか確認
2. **権限不足**: IAM ユーザーに必要な権限があるか確認
3. **リージョン**: 正しいリージョンが設定されているか確認

#### 2. Lambda関数が実行されない場合

1. **環境変数**: Lambda 関数の設定で環境変数が正しく設定されているか確認
2. **実行ロール**: Lambda 関数の実行ロールに必要な権限があるか確認
3. **CloudWatch Logs**: エラーログを確認

#### 3. S3バケットエラー

1. **バケット名**: バケット名がグローバルに一意であるか確認
2. **リージョン**: バケットとLambda関数が同じリージョンにあるか確認
3. **アクセス権限**: Lambda関数がバケットにアクセスできるか確認

#### 4. API キーエラー
- `.env` ファイルの API キーが正しいか確認
- API キーのクォーテーション（引用符）を確認
- AI_PROVIDER の設定が正しいか確認

#### 5. ローカル実行時のエラー
```bash
# Python バージョンを確認
python --version

# AWS 認証情報を確認
aws sts get-caller-identity

# 環境変数が正しく設定されているか確認
env | grep -E "(S3_BUCKET|API_KEY|AI_PROVIDER)"
```

### ログの確認

#### CloudWatch Logs
```bash
# Lambda 関数のログを確認
aws logs tail /aws/lambda/news-subscribe-aws-NewsProcessingFunction-xxxxx --follow
```

#### ローカルデバッグ
```python
# lambda_function.py の先頭に追加してデバッグ
import logging
logging.basicConfig(level=logging.DEBUG)
```

## セキュリティに関する注意事項

- API キーや認証情報は環境設定ファイルに記載し、絶対にコードにハードコーディングしない
- `.env.*` ファイルは `.gitignore` に含まれていることを確認
- 本番環境へのデプロイは慎重に実行し、必要に応じてレビューを受ける

## 参考情報

### SAM デプロイの詳細

#### ファイルの役割
- **`.env`**: 環境固有の設定（APIキー等）を保存
- **`deploy.sh`**: `.env` から値を読み込み、SAM に渡す
- **`template.yaml`**: AWS リソースの定義とパラメータのスキーマ
- **`samconfig.toml`**: デプロイの基本設定（スタック名等）

#### 動作の流れ
1. `./deploy.sh` を実行
2. `.env` ファイルの内容が環境変数にロード
3. `sam build` で Lambda 関数をビルド
4. `sam deploy` で AWS にデプロイ
   - `samconfig.toml` の設定が自動的に使用される
   - `--parameter-overrides` で指定した値が優先される

### ディレクトリ構造
```
news_subscribe_aws/
├── deploy.sh           # デプロイスクリプト
├── deploy-env.sh       # 環境別デプロイスクリプト
├── template.yaml       # SAM テンプレート
├── samconfig.toml      # SAM 設定（.gitignore に含まれる）
├── lambda_function.py  # メインハンドラー
├── src/               # ソースコード
├── requirements.txt   # Python 依存関係
├── .env.example      # 環境変数サンプル
└── docs/
    └── DEPLOYMENT.md  # このファイル
```

### 関連ドキュメント
- [AWS SAM ドキュメント](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS Lambda ドキュメント](https://docs.aws.amazon.com/lambda/)
- [Amazon Polly ドキュメント](https://docs.aws.amazon.com/polly/)

### サポート
問題が解決しない場合は、以下の情報と共に Issue を作成してください：
- エラーメッセージの全文
- 実行したコマンド
- 環境情報（OS、Python バージョン、AWS CLI バージョン）
- CloudWatch Logs の関連部分