# News Subscribe AWS - デプロイ手順書

## 目次
1. [前提条件](#前提条件)
2. [初回セットアップ](#初回セットアップ)
3. [デプロイ方法](#デプロイ方法)
4. [ローカル実行](#ローカル実行)
5. [トラブルシューティング](#トラブルシューティング)
6. [参考情報](#参考情報)

## 前提条件

### 必要なツール
- Python 3.9 以上
- AWS CLI
- AWS SAM CLI

### AWS リソース
- AWS アカウント
- IAM ユーザー（プログラマティックアクセス可能）
- S3 バケット（音声ファイル保存用）

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

## デプロイ方法

### 標準的なデプロイ
```bash
# デプロイスクリプトを実行
./deploy.sh
```

このスクリプトは以下を実行します：
1. `.env` ファイルから環境変数を読み込み
2. SAM アプリケーションをビルド
3. CloudFormation スタックとしてデプロイ

#### パラメータの優先順位
デプロイ時に使用されるパラメータの優先順位：
1. **`deploy.sh` が指定する値**（最優先）
   - `.env` ファイルから読み込んだ値
   - または `deploy.sh` 内のデフォルト値
2. **`template.yaml` の `Default` 値**
   - `deploy.sh` が指定しないパラメータのみ使用

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

## SAM デプロイの詳細

### ファイルの役割
- **`.env`**: 環境固有の設定（APIキー等）を保存
- **`deploy.sh`**: `.env` から値を読み込み、SAM に渡す
- **`template.yaml`**: AWS リソースの定義とパラメータのスキーマ
- **`samconfig.toml`**: デプロイの基本設定（スタック名等）

### 動作の流れ
1. `./deploy.sh` を実行
2. `.env` ファイルの内容が環境変数にロード
3. `sam build` で Lambda 関数をビルド
4. `sam deploy` で AWS にデプロイ
   - `samconfig.toml` の設定が自動的に使用される
   - `--parameter-overrides` で指定した値が優先される

## トラブルシューティング

### よくある問題と解決方法

#### 1. デプロイが失敗する
```bash
# CloudFormation スタックの状態を確認
aws cloudformation describe-stacks --stack-name news-subscribe-aws

# エラーイベントを確認
aws cloudformation describe-stack-events --stack-name news-subscribe-aws | head -20
```

#### 2. 権限エラー
- IAM ユーザーの権限を確認
- S3 バケットポリシーを確認
- Lambda 実行ロールの権限を確認

#### 3. API キーエラー
- `.env` ファイルの API キーが正しいか確認
- API キーのクォーテーション（引用符）を確認
- AI_PROVIDER の設定が正しいか確認

#### 4. ローカル実行時のエラー
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

## 参考情報

### ディレクトリ構造
```
news_subscribe_aws/
├── deploy.sh           # デプロイスクリプト
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