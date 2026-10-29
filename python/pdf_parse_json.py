import json
import re
import sys
import traceback
from pathlib import Path
import pymupdf

# ===== 設定・定数定義 =====
PDF_PATH = Path("data/questions-pdf/ITパスポート/2025_ITパスポート_過去問.pdf")
ANSWER_PDF_PATH = Path("data/questions-pdf/ITパスポート/2025_ITパスポート_過去問_回答例.pdf")
OUTPUT_PATH = Path("data/questions-json/2025_ITパスポート_過去問.json")

# ※指定のJSONサンプルに合わせて設定
# ITパスポート:it-passport
# 基本情報技術者試験：fundamental-examination
# 応用情報技術者試験：applied-examination
EXAM_CODE = "it-passport"
YEAR_CODE = "2025"  

EXAM_NAME = "ITパスポート"
CHOICE_LABELS = ("ア", "イ", "ウ", "エ")

# ログ表示設定
DEBUG = True

def log(message: str) -> None:
    """処理状況を標準出力へ表示する関数です。"""
    print(f"[INFO] {message}", flush=True)


def log_warning(message: str) -> None:
    """警告メッセージを標準出力へ表示する関数です。"""
    print(f"[WARN] {message}", flush=True)


def log_error(message: str) -> None:
    """エラーメッセージを標準エラー出力へ表示する関数です。"""
    print(f"[ERROR] {message}", file=sys.stderr, flush=True)

def normalize_digits(value: str) -> str:
    """全角数字を半角数字に変換"""
    return value.translate(str.maketrans("０１２３４５６７８９", "0123456789"))

def normalize_text(text: str) -> str:
    """テキストの不要な空白や特殊文字を整理し、ページ番号行を除去して正規化します。"""
    text = text.replace("\u00a0", " ").replace("\ufeff", "")
    
    # 【追加】PDFのフッター等に含まれるページ番号行（例: "－ 8 －", "- 8 -"）を除去する
    lines = []
    for line in text.splitlines():
        if re.match(r"^\s*[－\-ーー―]\s*\d+\s*[－\-ーー―]\s*$", line):
            continue
        lines.append(line)
    text = "\n".join(lines)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)
    return text.strip()

def extract_pages(pdf_path: Path) -> list[dict]:
    """
    指定された問題PDFファイルを開き、ページごとにテキストを抽出・正規化
    """
    log(f"問題PDFファイルの読み込みを開始します: {pdf_path.resolve()}")

    if not pdf_path.is_file():
        raise FileNotFoundError(
            f"入力PDFが存在しません: {pdf_path.resolve()}\n"
            "カレントディレクトリとファイルの配置を確認してください。"
        )

    pages = []
    with pymupdf.open(pdf_path) as document:
        page_count = len(document)
        log(f"PDFを開きました。総ページ数: {page_count}")

        if page_count == 0:
            raise ValueError("PDFにページが存在しません。")

        for page_index, page in enumerate(document):
            page_number = page_index + 1
            text = page.get_text("text", sort=True)
            normalized = normalize_text(text)

            pages.append({
                "page_number": page_number,
                "text": normalized,
            })

            log(f"[ページ {page_number}/{page_count}] 抽出文字数={len(text)}、整理後={len(normalized)}")

    return pages


def extract_answers_from_pdf(answer_pdf_path: Path) -> dict[int, str]:
    """
    解答例PDFから問1〜問20等の正解（ア・イ・ウ・エ）を直接抽出し、
    問題番号と正解文字（例: {1: "ウ", 2: "ア", ...}）の対応辞書を作成
    ※解答例PDFが存在しない・取得できない場合はデフォルトで「ア」を設定
    """
    answer_map = {}

    if not answer_pdf_path.is_file():
        log_warning(f"解答例PDFが見つからないため、仮の解答（ア）を設定します: {answer_pdf_path}")
        # ファイルが存在しない場合の仮置き
        for i in range(1, 101):
            answer_map[i] = "ア"
        return answer_map

    log(f"解答例PDFから正解の抽出を開始します: {answer_pdf_path.resolve()}")

    with pymupdf.open(answer_pdf_path) as doc:
        full_text = ""
        for page in doc:
            full_text += page.get_text("text", sort=True) + "\n"

    # 例: 「問1 ア」「問 1 : イ」「1 ウ」などのパターンを検出して、数字と「ア・イ・ウ・エ」を取得
    pattern = re.compile(r"(?:問\s*)?([0-9０-９]+)\s*[:：.\s]*([アイウエ])")
    matches = pattern.findall(full_text)

    for q_str, ans_str in matches:
        q_num = int(normalize_digits(q_str))
        answer_map[q_num] = ans_str  # 変換せずそのまま「ア・イ・ウ・エ」を保持

    log(f"解答例から {len(answer_map)} 件の正解（ア〜エ）を取得しました。")
    return answer_map


def split_question_blocks(pages: list[dict]) -> list[dict]:
    """
    抽出テキストから「問1」「問2」などの問題開始パターンを検出し、
    問題単位のデータブロックに分割
    """
    log("問題番号を基準にテキストを各問題ブロックへ分割")

    # 行頭の「問1」「問 1」「問１」などを検出する正規表現
    question_pattern = re.compile(
        r"^\s*問\s*([0-9０-９]+)\s*(?:[：:．.]?\s*)(.*)$"
    )

    blocks = []
    current_block = None

    for page in pages:
        for line in page["text"].splitlines():
            match = question_pattern.match(line)

            if match:
                number = int(normalize_digits(match.group(1)))
                remainder = match.group(2).strip()

                if current_block is not None:
                    blocks.append(current_block)

                current_block = {
                    "question_number": number,
                    "page_numbers": [page["page_number"]],
                    "lines": [],
                }

                if remainder:
                    current_block["lines"].append(remainder)
                continue

            if current_block is not None:
                if page["page_number"] not in current_block["page_numbers"]:
                    current_block["page_numbers"].append(page["page_number"])
                current_block["lines"].append(line)

    if current_block is not None:
        blocks.append(current_block)

    log(f"合計 {len(blocks)} 件の問題ブロックを作成しました。")
    return blocks


def parse_question(block: dict) -> dict:
    """
    各問題ブロックから問題文と選択肢（ア・イ・ウ・エ）を分離・抽出し、
    指定された構造のデータオブジェクトを作成します。
    ※ 1行に複数の選択肢が並ぶパターンや途中で折り返されているケースにも対応します。
    """
    number = block["question_number"]
    full_text = "\n".join(block["lines"])

    # 【改良】行頭だけでなく、空白や改行の直後にある「ア」「イ」「ウ」「エ」を検出できるように修正
    choice_pattern = re.compile(r"(?:^|[\s\n]+)([アイウエ])\s*[:：.）]?\s+")

    matches = list(choice_pattern.finditer(full_text))

    if not matches:
        # 選択肢ラベルが見つからない場合のフォールバック構造
        return {
           "id": f"{YEAR_CODE}-{EXAM_CODE}-ip-{number:03d}",
            "exam": EXAM_CODE,
            "category": "ストラテジ系",
            "yearCode": YEAR_CODE,            
            "question": normalize_text(full_text),
            "options": [{label: ""} for label in CHOICE_LABELS],
            "correctAnswer": "ア",
        }

    # 最初に見つかった選択肢ラベルの前までを「問題文」とする
    question_text = normalize_text(full_text[:matches[0].start()])

    # 各選択肢のテキスト領域を順番に切り出して取得
    choices = {label: "" for label in CHOICE_LABELS}
    for i, match in enumerate(matches):
        label = match.group(1)
        start_pos = match.end()
        # 次の選択肢の開始位置、または全テキストの終了位置までを取得
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        choice_content = full_text[start_pos:end_pos]
        choices[label] = normalize_text(choice_content)

    return {
       "id": f"{YEAR_CODE}-{EXAM_CODE}-ip-{number:03d}",
        "exam": EXAM_CODE,
        "category": "ストラテジ系",
        "yearCode": YEAR_CODE,
        "question": question_text,
        "options": [
            {label: choices[label]} for label in CHOICE_LABELS
        ],
        "correctAnswer": "ア",
    }


def convert_pdf_to_json(pdf_path: Path, answer_pdf_path: Path) -> list[dict]:
    """
    PDFからの抽出・パース・解答例の合成を行い、最終的なJSON用データ配列を構築
    """
    pages = extract_pages(pdf_path)
    blocks = split_question_blocks(pages)

    log("各問題ブロックから問題文と4択選択肢の分解を行います。")
    questions = [parse_question(block) for block in blocks]

    # 解答例PDFから「ア・イ・ウ・エ」形式で正解を取得
    answer_map = extract_answers_from_pdf(answer_pdf_path)

    # 各問題の correctAnswer に正解（ア・イ・ウ・エ）を直接設定
    for q in questions:
        q_num_match = re.search(r"(\d+)$", q["id"])
        if q_num_match:
            q_num = int(q_num_match.group(1))
            # 解答例マップにデータがあれば設定、なければ「ア」を仮置き
            q["correctAnswer"] = answer_map.get(q_num, "ア")

    return questions


def save_json(data: list[dict], output_path: Path) -> None:
    """指定されたJSON形式でファイル保存を行います。"""
    log(f"JSONファイルへ保存します: {output_path.resolve()}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")

    log(f"保存が完了しました。ファイルサイズ: {output_path.stat().st_size:,} bytes")


def main() -> int:
    log("===== PDFからJSONへの変換処理を開始します =====")

    try:
        # 問題PDFと解答例PDFの処理・JSONデータ生成
        questions_data = convert_pdf_to_json(PDF_PATH, ANSWER_PDF_PATH)

        # 保存実行
        save_json(questions_data, OUTPUT_PATH)

        log(f"===== 処理が正常に完了しました（全 {len(questions_data)} 問） =====")
        return 0

    except Exception as error:
        log_error(f"エラーが発生しました: {type(error).__name__}: {error}")
        if DEBUG:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())