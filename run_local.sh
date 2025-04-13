#!/bin/bash

# ローカル環境で実行するためのシェルスクリプト

# 必要なディレクトリを作成
mkdir -p audio
mkdir -p data
mkdir -p data/episodes

# Python仮想環境がなければ作成
if [ ! -d "env" ]; then
    echo "Python仮想環境を作成します..."
    # pythonコマンドがpyenvによって管理されている場合、pythonのバージョンを明示
    # pyenv global 3.11.8などでpythonのバージョンを設定してから実行してください
    python3 -m venv env || python -m venv env
    if [ $? -ne 0 ]; then
        echo "Python仮想環境の作成に失敗しました。Python 3.9以上がインストールされていることを確認してください。"
        exit 1
    fi
fi

# 仮想環境をアクティベート
if [ -f "env/bin/activate" ]; then
    source env/bin/activate
else
    echo "仮想環境のアクティベーションファイルが見つかりません。"
    exit 1
fi

# 依存パッケージをインストール
echo "必要なパッケージをインストールします..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "依存パッケージのインストールに失敗しました。"
    exit 1
fi

# AWS認証情報が設定されていることを確認
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo ".envファイルから認証情報を読み込みます..."
    export $(grep -v '^#' .env | xargs)
fi

# アプリケーションを実行
echo "アプリケーションを実行します..."
python lambda_function.py

# ブラウザでエピソードリストを開く（macOSの場合）
LATEST_EPISODE=$(ls -t data/episodes | head -1)
if [ ! -z "$LATEST_EPISODE" ]; then
    echo "最新のエピソードを表示します: $LATEST_EPISODE"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "data/episodes/$LATEST_EPISODE"
    else
        echo "エピソードを確認するには次のファイルを開いてください: data/episodes/$LATEST_EPISODE"
    fi
fi

echo "処理が完了しました！"
