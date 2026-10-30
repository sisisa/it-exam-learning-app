"""
画像形式のIT試験のPDF問題データをOCRを用いてJSON化するPythonの処理
ITパスポート・応用情報技術者試験限定であり、解答例データはテキストベースだったので、
現状は画像ベースとテキストベースが混在している
"""
import json
import sys
import traceback
from pathlib import Path
import io

import pymupdf
import pytesseract
from PIL import Image

# ===== 設定・定数定義 =====
PDF_PATH = Path("data/questions-pdf/応用情報技術者試験/2025_応用情報技術者試験_過去問_午前.pdf")
ANSWER_PDF_PATH = Path("data/questions-pdf/応用情報技術者試験/2025_応用情報技術者試験_過去問_午前_回答例.pdf")
OUTPUT_PATH = Path("data/questions-json/2025_応用情報技術者試験_過去問_午前.json")

EXAM_CODE = "applied-examination"
EXAM_NAME = "応用情報技術者試験"
YEAR_CODE = "2025"  
CHOICE_LABELS = ("ア", "イ", "ウ", "エ")

# 読み込みを開始するページの指定
START_PAGE = 4

# Tesseractを使うために以下のように設定
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ログ表示設定
DEBUG = True

def log(message: str) -> None:
    """処理の進行状況や情報をコンソールに分かりやすく表示します。"""
    print(f"[INFO] {message}", flush=True)


def log_warning(message: str) -> None:
    """処理継続可能な注意喚起のメッセージをコンソールに表示します。"""
    print(f"[WARN] {message}", flush=True)


def log_error(message: str) -> None:
    """処理中断を伴うエラーメッセージを標準エラー出力へ表示します。"""
    print(f"[ERROR] {message}", file=sys.stderr, flush=True)


def normalize_digits(value: str) -> str:
    """全角で記載されている数字を半角数字に変換します。"""
    return value.translate(str.maketrans("０１２３４５６７８９", "0123456789"))

"""
抽出したテキストの不要な特殊文字（ノーブレークスペース等）を置換し、
PDFのフッターやヘッダーに含まれる不要なページ番号行を除去して綺麗に整形
"""
def normalize_text(text: str) -> str:
    if not text:
            return ""
            
    text = text.replace("\u00a0", " ").replace("\ufeff", "")
    
    cleaned_lines = []
    for line in text.splitlines():
        stripped_line = line.strip()
        
        # ページ番号やハイフン付きの孤立した行（例: "1-", "-2-", "5" 等）を判定して除外
        is_page_number_line = False
        if stripped_line:
            unwrapped = stripped_line.strip("－-ー―")
            if unwrapped.isdigit() or (stripped_line.endswith("-") and stripped_line[:-1].isdigit()):
                is_page_number_line = True
                
        if is_page_number_line:
            continue
            
        cleaned_lines.append(line)
        
    text = "\n".join(cleaned_lines)
    
    # 連続する空白や不要な改行の整理
    while "  " in text:
        text = text.replace("  ", " ")
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
        
    return text.strip()

"""
指定されたPDFファイルを開き、指定した開始ページから最終ページまで
OCR（pytesseract）形式で文字を読み取って抽出
"""
def extract_pages(pdf_path: Path, start_page: int = 2) -> list[dict]:
    log(f"問題PDFファイルの読み込みを開始します: {pdf_path.resolve()}")

    if not pdf_path.is_file():
        raise FileNotFoundError(
            f"入力PDFが存在しません: {pdf_path.resolve()}\n"
            "カレントディレクトリとファイルの配置を確認してください。"
        )

    pages = []
    with pymupdf.open(pdf_path) as document:
        page_count = len(document)
        log(f"PDFを開きました。総ページ数: {page_count}（{start_page}ページ目から読み込みを開始します）")

        if page_count == 0:
            raise ValueError("PDFにページがありません。")

        start_index = max(0, start_page - 1)

        for page_index in range(start_index, page_count):
            page = document[page_index]
            page_number = page_index + 1
            
            log(f"[ページ {page_number}/{page_count}] OCR処理を実行中...")
            text = ""
            try:
                # 解像度300dpiで画像化してOCRを実行
                pix = page.get_pixmap(dpi=300)
                image = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(image, lang="jpn")
            except Exception as e:
                log_warning(f"[ページ {page_number}] OCR処理中にエラーが発生しました: {e}")

            normalized = normalize_text(text)

            pages.append({
                "page_number": page_number,
                "text": normalized,
            })

            log(f"[ページ {page_number}/{page_count}] OCR文字数={len(text)}、整理後={len(normalized)}")
            
    return pages

"""
解答例PDFデータから、各問題番号に対する
正解（ア・イ・ウ・エ）をOCRを用いて抽出
"""
def extract_answers_from_pdf(answer_pdf_path: Path) -> dict[int, str]:
    answer_map = {}
    
    if not answer_pdf_path.is_file():
        log_warning(f"解答例PDFが見つからないため、仮の解答（ア）を設定します: {answer_pdf_path}")
        for i in range(1, 101):
            answer_map[i] = "ア"
        return answer_map

    log(f"解答例PDF（テキストPDF）から正解の抽出を開始します: {answer_pdf_path.resolve()}")

    full_text = ""
    with pymupdf.open(answer_pdf_path) as doc:
        for page in doc:
            full_text += page.get_text("text", sort=True) + "\n"

    # テキストを空白・改行区切りでトークン化して解析
    tokens = full_text.split()
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # 「問1」「1.」「問1:」などの表記から数値部分を取得
        q_candidate = token.replace("問", "").replace(".", "").replace(":", "").replace("：", "")
        normalized_cand = normalize_digits(q_candidate)
        
        if normalized_cand.isdigit():
            q_num = int(normalized_cand)
            # 後続のトークンから選択肢（ア・イ・ウ・エ）を探す
            for j in range(1, 4):
                if i + j < len(tokens):
                    next_token = tokens[i + j].strip("：:。.）) ")
                    if next_token in CHOICE_LABELS:
                        answer_map[q_num] = next_token
                        break
        i += 1

    log(f"解答例から {len(answer_map)} 件の正解を取得しました。")
    return answer_map

"""
全ページのテキストから「問1」「問2」などの問題開始位置を検出し、
問題単位のデータブロックに分割
"""
def split_question_blocks(pages: list[dict]) -> list[dict]:
    log("問題番号を基準にテキストを各問題ブロックへ分割します。")

    blocks = []
    current_block = None

    for page in pages:
        for line in page["text"].splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            is_question_start = False
            question_num = None
            remainder = ""

            # 行頭が「問」またはOCR誤認識の「間」から始まる場合を検出
            first_char = stripped[0]
            if first_char in ("問", "間"):
                sub = stripped[1:].strip()
                num_str = ""
                rem_str = sub
                for idx, char in enumerate(sub):
                    if char.isdigit() or char in "０１２３４５６７８９":
                        num_str += char
                    else:
                        rem_str = sub[idx:]
                        break

                if num_str:
                    question_num = int(normalize_digits(num_str))
                    is_question_start = True
                    remainder = rem_str.lstrip("：:．. ")

            if is_question_start:
                if current_block is not None:
                    blocks.append(current_block)

                current_block = {
                    "question_number": question_num,
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

"""
各問題ブロックのテキスト行から、問題文と選択肢（ア・イ・ウ・エ）を分離・抽出
"""
def parse_question(block: dict) -> dict:
    number = block["question_number"]
    full_text = "\n".join(block["lines"])

    positions = {}
    for label in CHOICE_LABELS:
        pos = full_text.find(label)
        # OCRで「エ」が「I」「工」「1」等に誤認識される場合の救済
        if pos == -1 and label == "エ":
            for alt in ("I", "工", "1"):
                alt_pos = full_text.find(alt)
                if alt_pos != -1:
                    pos = alt_pos
                    break
        if pos != -1:
            positions[label] = pos

    # 選択肢が見つからなかった場合
    if not positions:
        return {
            "id": f"{YEAR_CODE}-{EXAM_CODE}-ip-{number:03d}",
            "exam": EXAM_CODE,
            "category": "ストラテジ系",
            "yearCode": YEAR_CODE,
            "question": normalize_text(full_text),
            "options": [{label: ""} for label in CHOICE_LABELS],
            "correctAnswer": "ア",
        }

    # 最初に現れる選択肢ラベルの位置までを「問題文」とする
    min_pos = min(positions.values())
    question_text = normalize_text(full_text[:min_pos])

    # 次の問題番号（例: 「問4」「問5」）がブロック内に混入している場合、選択肢の終了位置をカットする
    next_q_keyword = f"問{number + 1}"
    next_q_pos = full_text.find(next_q_keyword)
    if next_q_pos == -1:
        next_q_pos = full_text.find(f"間{number + 1}")  # OCR誤認対策

    block_end_limit = next_q_pos if next_q_pos != -1 else len(full_text)

    # 各選択肢の文字切り出し
    extracted_choices = {}
    sorted_labels_by_pos = sorted(positions.items(), key=lambda x: x[1])

    for idx, (label, start_idx) in enumerate(sorted_labels_by_pos):
        content_start = start_idx + 1
        
        # 次の選択肢の開始位置、あるいはブロック末尾制限位置までを取得
        if idx + 1 < len(sorted_labels_by_pos):
            content_end = sorted_labels_by_pos[idx + 1][1]
        else:
            content_end = block_end_limit
            
        raw_content = full_text[content_start:content_end]
        cleaned_content = raw_content.lstrip("：:．.）) ")
        extracted_choices[label] = normalize_text(cleaned_content)

    return {
        "id": f"{YEAR_CODE}-{EXAM_CODE}-ip-{number:03d}",
        "exam": EXAM_CODE,
        "category": "ストラテジ系",
        "yearCode": YEAR_CODE,
        "question": question_text,
        "options": [
            {label: extracted_choices.get(label, "")} for label in CHOICE_LABELS
        ],
        "correctAnswer": "ア",  # 後続の解答結合で正しい正解に上書きされます
    }

# PDFの読み込みから問題の分解、解答の結合までの一連の変換フローを統合管理
def convert_pdf_to_json(pdf_path: Path, answer_pdf_path: Path) -> list[dict]:
    # 指定した開始ページ（START_PAGE）からOCR処理を行うよう引数を渡す
    pages = extract_pages(pdf_path, start_page=START_PAGE)
    blocks = split_question_blocks(pages)

    log("各問題ブロックから問題文と4択選択肢の分解を行います。")
    questions = [parse_question(block) for block in blocks]

    answer_map = extract_answers_from_pdf(answer_pdf_path)

    for q in questions:
        parts = q["id"].split("-")
        if parts:
            try:
                q_num = int(parts[-1])
                q["correctAnswer"] = answer_map.get(q_num, "ア")
            except ValueError:
                pass

    return questions

# 完成した問題データを指定されたパスに綺麗なインデント付きJSON形式で保存
def save_json(data: list[dict], output_path: Path) -> None:
    log(f"JSONファイルへ保存します: {output_path.resolve()}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")

    log(f"保存が完了しました。ファイルサイズ: {output_path.stat().st_size:,} bytes")

def main() -> int:
    log("===== PDFからJSONへの変換処理を開始 =====")

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