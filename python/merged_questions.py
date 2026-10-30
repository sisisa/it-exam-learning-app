"""
JSON化した問題データを統合・ID付与し、
data/(fe・ap・itのどれか)に保存するPythonの処理
"""
import json
from pathlib import Path

# ディレクトリ設定
PROJECT_DIR = Path.cwd()
SOURCE_DIR = PROJECT_DIR / "data" / "questions-json"
OUTPUT_DIR = PROJECT_DIR / "data" / "ap"
OUTPUT_FILE = OUTPUT_DIR / "questions.json"

def merge_questions():
    # JSONファイルをファイル名順に取得
    json_files = sorted(SOURCE_DIR.glob("*.json"))

    if not json_files:
        print("結合対象のJSONファイルが見つかりません。")
        return

    merged_questions = []

    # 各JSONファイルの問題データを結合
    for json_file in json_files:
        with json_file.open("r", encoding="utf-8") as file:
            questions = json.load(file)

        if not isinstance(questions, list):
            raise ValueError(
                f"{json_file.name}: JSONの最上位要素は配列にしてください。"
            )

        merged_questions.extend(questions)
        print(f"読み込み完了: {json_file.name} ({len(questions)}件)")

    # 既存のIDを上書きして連番を採番
    for index, question in enumerate(merged_questions, start=1):
        question["id"] = index

    # 出力先ディレクトリを作成
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 結合した問題データをJSONファイルに出力
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            merged_questions,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(f"\n結合完了: {len(merged_questions)}件")
    print(f"出力先: {OUTPUT_FILE}")


if __name__ == "__main__":
    merge_questions()