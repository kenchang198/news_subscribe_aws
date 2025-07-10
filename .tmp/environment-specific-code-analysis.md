# 環境別コード分析レポート

## 調査概要
本番（Lambda）環境とローカル環境で片側からしか使用されないコードの特定

## 調査方法
1. IS_LAMBDA環境変数の使用箇所を特定
2. 各ファイルの環境別分岐を分析
3. 環境別のインポートや関数呼び出しを調査

## IS_LAMBDA使用ファイル一覧
- /Users/ken/dev/python/news_subscribe_aws/src/s3_uploader.py
- /Users/ken/dev/python/news_subscribe_aws/src/main.py
- /Users/ken/dev/python/news_subscribe_aws/src/fetch_news.py
- /Users/ken/dev/python/news_subscribe_aws/src/config.py
- /Users/ken/dev/python/news_subscribe_aws/src/unified/speech_synthesizer.py
- /Users/ken/dev/python/news_subscribe_aws/src/unified/metadata_processor.py
- /Users/ken/dev/python/news_subscribe_aws/lambda_function.py
- /Users/ken/dev/python/news_subscribe_aws/src/polly_synthesizer.py

## 環境別コード分析

### 1. lambda_function.py

#### Lambda環境でのみ実行されるコード:
- `load_processed_ids()` (lines 42-60): boto3を使用してS3から処理済みIDを読み込む
- `save_processed_ids()` (lines 87-100): boto3を使用してS3に処理済みIDを保存
- `update_episodes_list()` (lines 122-136, 164-171): S3へのエピソードリスト保存
- 統合音声生成処理 (lines 303-305): S3キーの設定
- エピソードデータ保存 (lines 333-340): S3へのアップロード

#### ローカル環境でのみ実行されるコード:
- `load_processed_ids()` (lines 62-73): ローカルファイルから処理済みIDを読み込む  
- `save_processed_ids()` (lines 102-108): ローカルファイルに処理済みIDを保存
- `update_episodes_list()` (lines 138-141, 173-177): ローカルファイルへの保存
- 統合音声生成処理 (lines 307-308): ローカルファイルパスの設定
- エピソードデータ保存 (lines 342-345): ローカルファイルへの保存
- `__main__` ブロック (lines 402-469): ローカル実行専用のコード
  - ディレクトリ作成
  - デバッグモード（統合音声生成テスト）
  - Lambda関数の実行

## 使用されているが環境によって異なる実装を持つモジュール

### Lambda関数で使用されているモジュール:
- `src.fetch_rss` - RSSフィード取得
- `src.process_article` - 記事処理
- `src.s3_uploader` - S3アップロード（環境別実装）
- `src.narration_generator` - ナレーション生成（現在False条件で無効化）
- `src.polly_synthesizer` - 音声合成（環境別実装）
- `src.unified` - 統合音声生成
- `src.config` - 設定管理（環境別設定）

### 未使用または代替実装のモジュール:
- `src.main.py` - 独立した実行ファイル（Lambda関数では未使用）
- `src.fetch_news.py` - ニュース取得の別実装（Lambda関数では未使用）
- `src.text_to_speech.py` - 音声合成の別実装（`src.main.py`でのみ使用）
- `test_fetch_news.py` - テスト用ファイル

## 調査結果のまとめ

### 環境別のコード分類

#### Lambda環境専用コード:
1. **S3操作関連**
   - boto3を使用したS3へのファイルアップロード
   - S3からのファイル読み込み
   - S3 URLの生成

2. **一時ファイル管理**
   - `/tmp/`ディレクトリの使用
   - Lambdaの制約に対応したファイル処理

#### ローカル環境専用コード:
1. **ファイルシステム操作**
   - ローカルディレクトリへのファイル保存
   - `audio/`, `data/`ディレクトリの使用

2. **開発・テスト用コード**
   - `__main__`ブロック内のデバッグモード
   - `.env`ファイルからの設定読み込み
   - S3アップロードのシミュレーション

3. **代替実装**
   - `src.main.py` - Lambda関数とは異なる実装
   - `src.fetch_news.py` - RSSフィード取得の別実装
   - `src.text_to_speech.py` - Polly使用の別実装

### 無効化されているコード:
- `src.narration_generator.py` - False条件で無効化（lambda_function.py:363）
- `src.polly_synthesizer.py` - ナレーション生成と一緒に無効化

### 推奨事項:
1. **代替実装の整理**: `src.main.py`, `src.fetch_news.py`, `src.text_to_speech.py`は現在のLambda関数では使用されていないため、別ディレクトリに移動するか削除を検討

2. **無効化されたコードの削除**: ナレーション生成関連のコードは統合音声生成に置き換えられたため、削除を検討

3. **環境別コードの整理**: IS_LAMBDAによる分岐は適切に実装されているが、テストカバレッジを向上させるためにユニットテストの追加を推奨