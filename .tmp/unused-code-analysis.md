# ローカル・本番両方から未使用のコードと関数

## 1. 完全に未使用のコード（両環境で使用されていない）

### a) False条件で無効化されているコード
**ファイル**: `lambda_function.py` (lines 361-384)
```python
if processed_articles and False:  # False条件で無効化
```

これにより以下が完全に未使用：
- **`src/narration_generator.py`**
  - `generate_narration_texts()` 関数
- **`src/polly_synthesizer.py`**
  - `synthesize_and_upload_narrations()` 関数

### b) どこからも参照されていないファイル
- なし（すべてのファイルは何らかの形で参照されている）

## 2. 部分的に未使用のコード

### a) Lambda関数では未使用だがローカルで使用される可能性があるファイル
- **`src/main.py`** - 独立した実行ファイル
- **`src/fetch_news.py`** - ニュース取得の別実装
- **`src/text_to_speech.py`** - 音声合成の別実装（src/main.pyでのみ使用）

### b) テスト専用ファイル
- **`test_fetch_news.py`** - src/fetch_news.pyのテスト用

## 3. 使用されているファイル

以下のファイルは実際に使用されています：
- **`src/utils.py`** - `create_article_id()`関数が`src/process_article.py`で使用
- **`src/process_article.py`** - 記事処理で使用
- **`src/fetch_rss.py`** - RSSフィード取得で使用
- **`src/s3_uploader.py`** - S3アップロードで使用
- **`src/config.py`** - 設定管理で使用
- **`src/unified/`** ディレクトリ内のすべてのファイル - 統合音声生成で使用

## 推奨事項

1. **削除候補**：
   - `src/narration_generator.py` - False条件で完全に無効化
   - `synthesize_and_upload_narrations()`関数（src/polly_synthesizer.py内）

2. **整理候補**：
   - `src/main.py`、`src/fetch_news.py`、`src/text_to_speech.py`を`legacy/`または`alternative/`ディレクトリに移動

3. **維持すべきファイル**：
   - `src/utils.py` - 実際に使用されている
   - その他の`src/`内のファイル - Lambda関数で使用