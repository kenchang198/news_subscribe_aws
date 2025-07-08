import datetime
import re
from src.config import PROGRAM_NAME


def remove_site_name_from_title(title):
    """
    タイトルからサイト名を除去する
    
    Args:
        title (str): 元のタイトル
        
    Returns:
        str: サイト名を除去したタイトル
    """
    if not title:
        return title
    
    # よくあるサイト名の表記パターンを除去
    patterns = [
        r'^[^：]*：\s*',          # "サイト名：タイトル" → "タイトル"
        r'^[^:]*:\s*',            # "サイト名:タイトル" → "タイトル"
        r'^【[^】]*】\s*',         # "【サイト名】タイトル" → "タイトル"
        r'^\[[^\]]*\]\s*',        # "[サイト名]タイトル" → "タイトル"
        r'^（[^）]*）\s*',         # "（サイト名）タイトル" → "タイトル"
        r'^\([^)]*\)\s*',         # "(サイト名)タイトル" → "タイトル"
        r'^[^｜]*｜\s*',          # "サイト名｜タイトル" → "タイトル"
        r'^[^|]*\|\s*',           # "サイト名|タイトル" → "タイトル"
        r'^[^－]*－\s*',          # "サイト名－タイトル" → "タイトル"
        r'^[^-]*-\s*',            # "サイト名-タイトル" → "タイトル"
        r'^\S+\s*:\s*',           # "サイト名 : タイトル" → "タイトル"
    ]
    
    cleaned_title = title
    for pattern in patterns:
        cleaned_title = re.sub(pattern, '', cleaned_title)
        # パターンにマッチした場合は他のパターンを試さない
        if cleaned_title != title:
            break
    
    # 先頭と末尾の空白を除去
    cleaned_title = cleaned_title.strip()
    
    # 空文字列になった場合は元のタイトルを返す
    if not cleaned_title:
        return title
    
    return cleaned_title


def generate_narration_texts(
    episode_date: datetime.date,
    articles: list[dict]
) -> dict[str, str]:
    """
    エピソードの日付と記事リストに基づいて、ナレーションテキストを生成する。

    Args:
        episode_date: エピソードの日付。
        articles: 記事情報のリスト。各要素は少なくとも 'title' キーを持つ辞書。

    Returns:
        ナレーションの種類をキー、生成されたテキストを値とする辞書。
        例: {'intro': '...', 'transition_1': '...', 'outro': '...'}
    """
    narrations = {}
    num_articles = len(articles)

    # --- 挨拶 ---
    month = episode_date.month
    day = episode_date.day
    # 曜日を取得 (0:月, 1:火, ..., 6:日)
    weekday_index = episode_date.weekday()
    # 日本語の曜日リスト
    weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]
    weekday_jp = weekdays_jp[weekday_index]

    # 複数行のf-stringはトリプルクオートで囲む
    narrations['intro'] = f"""みなさんこんにちは本日は{month}月{day}日{weekday_jp}曜日です。
本日も{PROGRAM_NAME}を元気よく初めていきます。"""

    # --- 記事紹介と繋ぎ ---
    for i, article in enumerate(articles):
        original_title = article.get('title', '（タイトル不明）')
        title = remove_site_name_from_title(original_title)
        key = f"transition_{i+1}"  # 1記事目の紹介からtransition_1とする

        if i == 0:
            narrations[key] = f"まず最初に紹介する記事は{title}です。"
        elif i == num_articles - 1 and num_articles > 1:  # 最後の記事 (記事が複数ある場合)
            narrations[key] = f"最後の記事は{title}です。"
        elif i == 1:
            narrations[key] = f"次の記事は{title}です。"
        elif i == 2:
            narrations[key] = f"続いてご紹介するのは{title}です。"
        elif i == 3:
            narrations[key] = f"4つ目の記事は{title}です。"
        # 必要に応じて 5つ目以降のテンプレートを追加
        else:
            narrations[key] = f"{i+1}つ目の記事は{title}です。"  # デフォルトの繋ぎ

    # --- エンディング ---
    # 複数行の文字列はトリプルクオートで囲む
    narrations['outro'] = """本日のニュースは以上です。
明日もお楽しみに。"""

    return narrations


# --- 動作確認用 ---
if __name__ == '__main__':
    today = datetime.date.today()
    sample_articles = [
        {'title': 'AIが小説を執筆'},
        {'title': '量子コンピュータの最新動向'},
        {'title': '次世代Webフレームワーク登場'},
        {'title': 'メタバースのビジネス活用事例'},
        {'title': 'サイバーセキュリティ脅威レポート'}
    ]
    generated_texts = generate_narration_texts(today, sample_articles)
    for key, text in generated_texts.items():
        print(f"--- {key} ---")
        print(text)
        print()

    # print内の改行を削除
    print("\n--- 記事が1つの場合 ---")
    single_article = [{'title': '注目の技術トレンド'}]
    generated_texts_single = generate_narration_texts(today, single_article)
    for key, text in generated_texts_single.items():
        print(f"--- {key} ---")
        print(text)
        print()
