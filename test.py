import json
import re
import sys
import traceback
from pathlib import Path

import pymupdf

# ===== 設定 =====
PDF_PATH = Path("2026年・令和8年度試験/基本情報技術者試験/基本情報技術者試験過去問_午前.pdf")
OUTPUT_PATH = Path("2026年・令和8年度試験/基本情報技術者試験/基本情報技術者試験過去問_午前.json")

EXAM_NAME = "基本情報技術者試験"
QUESTION_TYPE = "午前"

CHOICE_LABELS = ("ア", "イ", "ウ", "エ")

# ログ表示設定
DEBUG = True
SHOW_EVERY_PAGE_TEXT = True
SHOW_EVERY_QUESTION = True
MAX_TEXT_PREVIEW = 1200


def log(message: str) -> None:
    """処理状況をコンソールへ表示する。"""
    print(f"[INFO] {message}", flush=True)


def log_warning(message: str) -> None:
    print(f"[WARN] {message}", flush=True)


def log_error(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr, flush=True)


def normalize_digits(value: str) -> str:
    return value.translate(str.maketrans("０１２３４５６７８９", "0123456789"))


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\ufeff", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)
    return text.strip()


def extract_pages(pdf_path: Path) -> list[dict]:
    log("STEP 1/6: PDFファイルの存在を確認します。")
    log(f"入力パス: {pdf_path.resolve()}")

    if not pdf_path.is_file():
        raise FileNotFoundError(
            f"入力PDFが存在しません: {pdf_path.resolve()}\n"
            "実行時のカレントディレクトリとPDFの配置を確認してください。"
        )

    log("STEP 2/6: PDFを開き、ページごとに文字列を抽出します。")
    pages = []

    with pymupdf.open(pdf_path) as document:
        page_count = len(document)
        log(f"PDFを開けました。ページ数: {page_count}")

        if page_count == 0:
            raise ValueError("PDFにページがありません。")

        for page_index, page in enumerate(document):
            page_number = page_index + 1
            text = page.get_text("text", sort=True)
            normalized = normalize_text(text)

            pages.append({
                "page_number": page_number,
                "text": normalized,
            })

            log(
                f"[ページ {page_number}/{page_count}] "
                f"抽出文字数={len(text)}、整理後文字数={len(normalized)}"
            )

            if not normalized:
                log_warning(
                    f"ページ {page_number} から文字を抽出できませんでした。"
                    "スキャン画像PDFの可能性があります。"
                )
            elif SHOW_EVERY_PAGE_TEXT:
                preview = normalized[:MAX_TEXT_PREVIEW]
                suffix = "\n...（以下省略）" if len(normalized) > MAX_TEXT_PREVIEW else ""
                print(f"----- ページ {page_number} の抽出テキスト -----")
                print(preview + suffix)
                print("----------------------------------------")

    total_chars = sum(len(page["text"]) for page in pages)
    log(f"ページ抽出完了。総文字数: {total_chars}")

    if total_chars == 0:
        raise ValueError(
            "PDFから文字を1文字も抽出できませんでした。"
            "スキャン画像PDFの場合はOCR処理が必要です。"
        )

    return pages


def split_question_blocks(pages: list[dict]) -> list[dict]:
    log("STEP 3/6: 問題番号を探し、問題単位に分割します。")

    # 問題番号は行頭の「問1」「問 1」「問１」などを対象にする。
    question_pattern = re.compile(
        r"^\s*問\s*([0-9０-９]+)\s*(?:[：:．.]?\s*)(.*)$"
    )

    blocks = []
    current = None
    detected_numbers = []

    for page in pages:
        for line_number, line in enumerate(page["text"].splitlines(), start=1):
            match = question_pattern.match(line)

            if match:
                number = int(normalize_digits(match.group(1)))
                remainder = match.group(2).strip()

                # PDFのヘッダーなどに含まれる問番号を誤検出していないか、
                # コンソールで検出位置を確認できるようにする。
                log(
                    f"[問題番号検出] 問{number} "
                    f"(PDFページ={page['page_number']}, ページ内行={line_number})"
                )
                detected_numbers.append(number)

                if current is not None:
                    blocks.append(current)
                    log(
                        f"[問題ブロック確定] 問{current['question_number']} "
                        f"行数={len(current['lines'])} "
                        f"ページ={current['page_numbers']}"
                    )

                current = {
                    "question_number": number,
                    "page_numbers": [page["page_number"]],
                    "lines": [],
                }

                if remainder:
                    current["lines"].append(remainder)
                continue

            if current is not None:
                if page["page_number"] not in current["page_numbers"]:
                    current["page_numbers"].append(page["page_number"])
                current["lines"].append(line)

    if current is not None:
        blocks.append(current)
        log(
            f"[問題ブロック確定] 問{current['question_number']} "
            f"行数={len(current['lines'])} "
            f"ページ={current['page_numbers']}"
        )

    log(f"問題番号検出数: {len(detected_numbers)}")
    log(f"作成した問題ブロック数: {len(blocks)}")

    if not detected_numbers:
        log_error("問題番号が1件も見つかりませんでした。")
        log_error("PDFから抽出されたテキストの冒頭を確認してください。")
        raise ValueError(
            "問題番号を検出できませんでした。抽出テキストと問題番号の表記を確認してください。"
        )

    if len(detected_numbers) != len(set(detected_numbers)):
        log_warning(
            "同じ問題番号が複数回検出されています。"
            "ページヘッダー等を問題番号と誤認識している可能性があります。"
        )

    return blocks


def parse_question(block: dict) -> dict:
    """問題ブロックから問題文・選択肢を抽出し、詳細ログを出す。"""
    number = block["question_number"]
    log(f"[問{number}] 本文と選択肢の抽出を開始します。")

    # 選択肢ラベルが行頭にある形式を想定。
    # 「ア 選択肢」「ア　選択肢」「ア. 選択肢」などに対応。
    choice_pattern = re.compile(
        r"^\s*([アイウエ])(?:\s+|[、。，．.：:）)])(.*)$"
    )

    question_lines = []
    choices = {label: [] for label in CHOICE_LABELS}
    current_choice = None
    choice_hits = []

    for line_number, line in enumerate(block["lines"], start=1):
        match = choice_pattern.match(line)

        if match:
            label, content = match.groups()
            current_choice = label
            choice_hits.append(label)
            if content.strip():
                choices[label].append(content.strip())
            log(f"[問{number}] 選択肢ラベル検出: {label}（ブロック内行={line_number}）")
            continue

        if current_choice is None:
            question_lines.append(line)
        elif line.strip():
            choices[current_choice].append(line.strip())

    question_text = normalize_text("\n".join(question_lines))
    formatted_choices = {
        label: normalize_text("\n".join(choices[label]))
        for label in CHOICE_LABELS
    }

    log(f"[問{number}] 問題文文字数: {len(question_text)}")
    if DEBUG and question_text:
        print(f"[問{number}] 問題文プレビュー: {question_text[:MAX_TEXT_PREVIEW]}")

    for label, choice_text in formatted_choices.items():
        log(f"[問{number}] 選択肢{label}: 文字数={len(choice_text)}")
        if DEBUG and choice_text:
            print(f"  {label}: {choice_text[:300]}")

    missing_choices = [
        label for label, text in formatted_choices.items() if not text
    ]
    review_notes = []

    if not question_text:
        review_notes.append("問題文を抽出できませんでした。")
    if missing_choices:
        review_notes.append(
            f"選択肢を抽出できませんでした: {', '.join(missing_choices)}"
        )

    # 同じラベルが複数回出た場合、PDFのレイアウトや検出ルールを要確認。
    duplicated_labels = sorted({
        label for label in choice_hits if choice_hits.count(label) > 1
    })
    if duplicated_labels:
        review_notes.append(
            f"選択肢ラベルを複数回検出しました: {', '.join(duplicated_labels)}"
        )

    status = "review_required" if review_notes else "extracted"
    log(
        f"[問{number}] 抽出結果: {status}"
        + (f" / 注意点: {'; '.join(review_notes)}" if review_notes else "")
    )

    return {
        "question_number": number,
        "page_numbers": block["page_numbers"],
        "question_text": question_text,
        "choices": formatted_choices,
        "figures": [],
        "parse_status": status,
        "review_notes": review_notes,
    }


def convert_pdf_to_json(pdf_path: Path) -> dict:
    pages = extract_pages(pdf_path)
    blocks = split_question_blocks(pages)

    log("STEP 4/6: 各問題ブロックから問題文・4択を抽出します。")
    questions = [parse_question(block) for block in blocks]

    extracted_count = sum(q["parse_status"] == "extracted" for q in questions)
    review_count = sum(q["parse_status"] == "review_required" for q in questions)

    log(f"問題抽出処理完了: 全{len(questions)}問")
    log(f"  抽出済み: {extracted_count}問")
    log(f"  要確認: {review_count}問")

    return {
        "exam_name": EXAM_NAME,
        "question_type": QUESTION_TYPE,
        "source_pdf": pdf_path.name,
        "extraction_method": "PyMuPDF page.get_text('text', sort=True)",
        "questions": questions,
        "extraction_summary": {
            "page_count": len(pages),
            "question_count": len(questions),
            "extracted_count": extracted_count,
            "review_required_count": review_count,
        },
    }


def save_and_validate_json(data: dict, output_path: Path) -> None:
    log("STEP 5/6: JSONファイルへ保存します。")
    log(f"出力先: {output_path.resolve()}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=2)
        output_file.write("\n")

    if not output_path.is_file():
        raise OSError(f"JSONファイルが作成されませんでした: {output_path.resolve()}")

    file_size = output_path.stat().st_size
    log(f"ファイル保存完了: {file_size:,} bytes")

    log("STEP 6/6: 保存したJSONを読み直して検証します。")
    with output_path.open("r", encoding="utf-8") as output_file:
        loaded_data = json.load(output_file)

    if not isinstance(loaded_data, dict):
        raise ValueError("JSONの最上位データがオブジェクトではありません。")

    questions = loaded_data.get("questions")
    if not isinstance(questions, list):
        raise ValueError("JSON内にquestions配列がありません。")

    log(f"JSON検証成功: questions={len(questions)}件")
    log("保存したJSONは構文上有効です。")


def main() -> int:
    log("===== PDFからJSONへの変換を開始します =====")
    log(f"現在の作業ディレクトリ: {Path.cwd()}")
    log(f"入力PDF: {PDF_PATH}")
    log(f"出力JSON: {OUTPUT_PATH}")

    try:
        data = convert_pdf_to_json(PDF_PATH)
        save_and_validate_json(data, OUTPUT_PATH)

        summary = data["extraction_summary"]
        log("===== 変換処理が完了しました =====")
        log(f"ページ数: {summary['page_count']}")
        log(f"問題数: {summary['question_count']}")
        log(f"抽出済み: {summary['extracted_count']}")
        log(f"要確認: {summary['review_required_count']}")
        log(f"出力ファイル: {OUTPUT_PATH.resolve()}")
        return 0

    except Exception as error:
        log_error(f"{type(error).__name__}: {error}")
        if DEBUG:
            log_error("詳細なエラー情報:")
            traceback.print_exc()
        log_error("処理を中断しました。上記ログの最初の異常箇所を確認してください。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
