import sys
from pathlib import Path
import pymupdf

PDF_PATH = Path("data/questions-pdf/ITパスポート/2025_ITパスポート_過去問.pdf")

def diagnose_pdf(pdf_path: Path) -> None:
    print(f"===== PDF診断ツール: {pdf_path.name} =====")
    if not pdf_path.is_file():
        print(f"[ERROR] ファイルが存在しません: {pdf_path.resolve()}")
        return

    with pymupdf.open(pdf_path) as doc:
        print(f"総ページ数: {len(doc)}")
        text_page_count = 0
        image_only_page_count = 0

        for index, page in enumerate(doc):
            page_num = index + 1
            text = page.get_text("text")
            images = page.get_images()

            # strip() の括弧を追加して文字列の長さを取得するように修正
            stripped_text_len = len(text.strip())

            if stripped_text_len > 0:
                text_page_count += 1
                status = "【テキストPDF】（文字データが存在します）"
            elif images:
                image_only_page_count += 1
                status = "【画像PDF / スキャンPDF】（文字データがなく、画像として保存されています）"
            else:
                status = "【空ページまたは特殊レイアウト】"

            print(f"ページ {page_num}: 抽出文字数={stripped_text_len}, 画像数={len(images)} -> {status}")

        print("\n--- 診断結果サマリ ---")
        print(f"テキスト抽出できたページ: {text_page_count} ページ")
        print(f"画像のみ（文字データなし）のページ: {image_only_page_count} ページ")
        
        if image_only_page_count > 0:
            print("\n[結論] このPDFはテキストレイヤーを持たない画像（スキャン）PDFです。")
        else:
            print("\n[結論] このPDFは通常のテキストPDFです。")

if __name__ == "__main__":
    diagnose_pdf(PDF_PATH)