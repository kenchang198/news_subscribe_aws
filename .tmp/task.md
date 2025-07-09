# デプロイ関連ファイルの整理タスク

## 完了タスク
- [x] プロジェクト構造とデプロイ関連ファイルの確認
- [x] 必要/不要なファイルの分類
- [x] feature/organize-deploy-files ブランチの作成
- [x] .tmp/design.md にデプロイアーキテクチャを記載
- [x] .gitignore に .aws-sam/ を追加（既に追加済みを確認）
- [x] parameters.example.txt を削除
- [x] samconfig.toml から機密情報（API キー）を削除
- [x] .env.example ファイルの作成
- [x] docs/DEPLOYMENT.md に詳細なデプロイ手順を作成
- [x] .tmp/task.md にタスク管理を記載

## 実施内容まとめ

### 1. ファイル整理
- 重複していた `parameters.example.txt` を削除（YAML 形式を残す）
- `.aws-sam/` ディレクトリが既に `.gitignore` に含まれていることを確認

### 2. セキュリティ改善
- `deploy/samconfig.toml` から Google API キーを削除
- `.env.example` ファイルを作成し、環境変数の設定方法を明確化

### 3. ドキュメント整備
- `.tmp/design.md`: デプロイアーキテクチャの設計書を作成
- `docs/DEPLOYMENT.md`: 詳細なデプロイ手順書を作成
  - 前提条件
  - 初回セットアップ
  - デプロイ方法
  - ローカル実行方法
  - トラブルシューティング

### 4. 削除されたファイル
- `parameters.example.txt`

### 5. 作成されたファイル
- `.env.example`
- `.tmp/design.md`
- `docs/DEPLOYMENT.md`
- `.tmp/task.md`（このファイル）

### 6. 修正されたファイル
- `deploy/samconfig.toml`（API キーを削除）

## 次のステップ（推奨）
1. README.md にデプロイ手順へのリンクを追加
2. GitHub Actions ワークフローの環境変数設定方法をドキュメント化
3. AWS Secrets Manager または Systems Manager Parameter Store の導入検討