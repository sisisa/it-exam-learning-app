import json
import re
import sys
import traceback
from pathlib import Path
import io

import pymupdf
import pytesseract
from PIL import Image

# ===== 設定・定数定義 =====
PDF_PATH = Path("data/questions-pdf/ITパスポート/2025_ITパスポート_過去問.pdf")
ANSWER_PDF_PATH = Path("data/questions-pdf/ITパスポート/2025_ITパスポート_過去問_回答例.pdf")
OUTPUT_PATH = Path("data/questions-json/2025_ITパスポート_過去問.json")

EXAM_CODE = "it-passport"
EXAM_NAME = "ITパスポート"
YEAR_CODE = "2025"  
QUESTION_TYPE = "公開問題"

CHOICE_LABELS = ("ア", "イ", "ウ", "エ")

# Tesseractを使うために以下のように設定
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
    """全角数字を半角数字に変換します。"""
    return value.translate(str.maketrans("０１２３４５６７８９", "0123456789"))


def normalize_text(text: str) -> str:
    """テキストの不要な空白や特殊文字を整理し、不要なページ番号行を除去します。"""
    text = text.replace("\u00a0", " ").replace("\ufeff", "")
    
    lines = []
    for line in text.splitlines():
        # PDFのフッター等に含まれるページ番号や区切り行を除外
        if re.match(r"^\s*(?:[－\-ーー―]?\s*\d+\s*[－\-ーー―]?|\d+-)\s*$", line):
            continue
        lines.append(line)
    text = "\n".join(lines)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)
    return text.strip()


def extract_pages(pdf_path: Path) -> list[dict]:
    """
    指定されたPDFを開き、ページごとのテキストを抽出します。
    テキストが空（画像PDF）の場合は、pytesseractによるOCR処理を実行します。
    """
    log(f"PDFファイルの読み込みを開始します: {pdf_path.resolve()}")

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
            
            # 1. まず通常のテキスト抽出を試みる
            text = page.get_text("text", sort=True)
            
            # 2. テキストが取得できない（画像PDFの）場合、OCRで文字を読み取る
            if not text.strip():
                log(f"[ページ {page_number}] テキスト未検出のためOCRを実行中...")
                try:
                    # ページを画像（解像度を高めるため dpi=200〜300）に変換
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_bytes))
                    
                    # pytesseractで日本語OCRを実行（jpn指定）
                    text = pytesseract.image_to_string(image, lang="jpn")
                except Exception as e:
                    log_warning(f"[ページ {page_number}] OCR処理でエラーが発生しました: {e}")

            normalized = normalize_text(text)

            pages.append({
                "page_number": page_number,
                "text": normalized,
            })

            log(f"[ページ {page_number}/{page_count}] 抽出・OCR文字数={len(text)}、整理後={len(normalized)}")

    return pages


def extract_answers_from_pdf(answer_pdf_path: Path) -> dict[int, str]:
    """解答例PDFから正解（ア・イ・ウ・エ）を抽出します（必要に応じてOCR対応も可）。"""
    answer_map = {}

    if not answer_pdf_path.is_file():
        log_warning(f"解答例PDFが見つからないため、仮の解答（ア）を設定します: {answer_pdf_path}")
        for i in range(1, 101):
            answer_map[i] = "ア"
        return answer_map

    log(f"解答例PDFから正解の抽出を開始します: {answer_pdf_path.resolve()}")

    with pymupdf.open(answer_pdf_path) as doc:
        full_text = ""
        for page in doc:
            t = page.get_text("text", sort=True)
            if not t.strip():
                pix = page.get_pixmap(dpi=200)
                t = pytesseract.image_to_string(Image.open(io.BytesIO(pix.tobytes("png"))), lang="jpn")
            full_text += t + "\n"

    pattern = re.compile(r"(?:問\s*)?([0-9０-９]+)\s*[:：.\s]*([アイウエ])")
    matches = pattern.findall(full_text)

    for q_str, ans_str in matches:
        q_num = int(normalize_digits(q_str))
        answer_map[q_num] = ans_str

    log(f"解答例から {len(answer_map)} 件の正解を取得しました。")
    return answer_map


def split_question_blocks(pages: list[dict]) -> list[dict]:
    """抽出テキストから問題番号を検出し、問題単位にブロック分割します。"""
    log("問題番号を基準にテキストを各問題ブロックへ分割します。")

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
    """各問題ブロックから問題文と選択肢（ア・イ・ウ・エ）を抽出します。"""
    number = block["question_number"]
    full_text = "\n".join(block["lines"])

    # 選択肢ラベル（ア、イ、ウ、エ、およびOCR誤認識しやすいIや工）を検出
    choice_pattern = re.compile(r"(?:^|[\s\n]+)([アイウエ工I])\s*[:：.）]?\s*")
    matches = list(choice_pattern.finditer(full_text))

    if not matches:
        return {
            "id": f"{YEAR_CODE}-{EXAM_CODE}-ip-{number:03d}",
            "exam": EXAM_CODE,
            "category": "ストラテジ系",
            "question": normalize_text(full_text),
            "options": [{label: ""} for label in CHOICE_LABELS],
            "correctAnswer": "ア",
        }

    question_text = normalize_text(full_text[:matches[0].start()])

    extracted_choices = {}
    for i, match in enumerate(matches):
        raw_label = match.group(1)
        label = "エ" if raw_label in ("I", "工") else raw_label

        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        choice_content = full_text[start_pos:end_pos]
        
        if label in CHOICE_LABELS:
            extracted_choices[label] = normalize_text(choice_content)

    return {
        "id": f"{YEAR_CODE}-{EXAM_CODE}-ip-{number:03d}",
        "exam": EXAM_CODE,
        "category": "ストラテジ系",
        "question": question_text,
        "options": [
            {label: extracted_choices.get(label, "")} for label in CHOICE_LABELS
        ],
        "correctAnswer": "ア",
    }


def convert_pdf_to_json(pdf_path: Path, answer_pdf_path: Path) -> list[dict]:
    pages = extract_pages(pdf_path)
    blocks = split_question_blocks(pages)

    log("各問題ブロックから問題文と4択選択肢の分解を行います。")
    questions = [parse_question(block) for block in blocks]

    answer_map = extract_answers_from_pdf(answer_pdf_path)

    for q in questions:
        q_num_match = re.search(r"(\d+)$", q["id"])
        if q_num_match:
            q_num = int(q_num_match.group(1))
            q["correctAnswer"] = answer_map.get(q_num, "ア")

    return questions


def save_json(data: list[dict], output_path: Path) -> None:
    log(f"JSONファイルへ保存します: {output_path.resolve()}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")

    log(f"保存が完了しました。ファイルサイズ: {output_path.stat().st_size:,} bytes")


def main() -> int:
    log("===== OCR対応 PDFからJSONへの変換処理を開始します =====")

    try:
        questions_data = convert_pdf_to_json(PDF_PATH, ANSWER_PDF_PATH)
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