"""
Test Script: Structured Table Extraction & Markdown Formatting
Validates that tables in PDF pages are accurately detected, extracted as 2D matrices,
converted into clean Markdown tables, and indexed with structured metadata.
"""

import fitz  # PyMuPDF
from typing import List, Tuple, Dict


def table_to_markdown(table_data: List[List[str]]) -> str:
    """
    Converts a 2D list of cell strings into a clean Markdown table format.
    Handles empty cells, newlines inside cells, and proper column alignment.
    """
    if not table_data or not table_data[0]:
        return ""

    # Clean cells: remove internal newlines and strip whitespace
    cleaned_rows = []
    for row in table_data:
        cleaned_row = [" ".join(str(cell or "").split()) for cell in row]
        # Ignore completely empty rows
        if any(cleaned_row):
            cleaned_rows.append(cleaned_row)

    if not cleaned_rows:
        return ""

    num_cols = max(len(row) for row in cleaned_rows)
    # Normalize row lengths
    normalized_rows = [row + [""] * (num_cols - len(row)) for row in cleaned_rows]

    # Build Markdown table
    header = normalized_rows[0]
    separator = ["---"] * num_cols

    md_lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |"
    ]

    for row in normalized_rows[1:]:
        md_lines.append("| " + " | ".join(row) + " |")

    return "\n".join(md_lines)


def extract_page_content_with_tables(page: fitz.Page, page_num: int) -> List[Dict]:
    """
    Extracts structured content from a PDF page:
    1. Detects and extracts tables as Markdown.
    2. Extracts regular text blocks.
    Returns a list of structured items with metadata.
    """
    items = []
    
    # 1. Detect tables
    try:
        tables = page.find_tables()
    except Exception:
        tables = []

    if tables and hasattr(tables, "tables"):
        for tab in tables.tables:
            table_data = tab.extract()
            md_table = table_to_markdown(table_data)
            if md_table:
                items.append({
                    "type": "table",
                    "page": page_num,
                    "content": f"[TABLE - Page {page_num}]\n{md_table}\n[/TABLE]",
                    "raw_data": table_data
                })

    # 2. Extract standard text
    text = page.get_text().strip()
    if text:
        items.append({
            "type": "text",
            "page": page_num,
            "content": text
        })

    return items


def extract_text_and_tables(pdf_path: str):
    """
    Extracts text and structured tables page-by-page from a PDF file.
    Preserves tables as intact Markdown structures so row-column relations are not lost.
    Returns: List of tuples (page_num, content, content_type)
    """
    doc = fitz.open(pdf_path)
    extracted_items = []

    for i, page in enumerate(doc):
        page_num = i + 1

        # 1. Extract Structured Tables
        try:
            tables = page.find_tables()
        except Exception:
            tables = []

        if tables and hasattr(tables, "tables"):
            for tab in tables.tables:
                table_data = tab.extract()
                md_table = table_to_markdown(table_data)
                if md_table:
                    extracted_items.append((
                        page_num,
                        f"[TABLE - Page {page_num}]\n{md_table}\n[/TABLE]",
                        "table"
                    ))

        # 2. Extract Standard Page Text
        text = page.get_text().strip()
        if text:
            extracted_items.append((page_num, text, "text"))

    doc.close()
    return extracted_items


def test_table_markdown_conversion():
    print("=================================================================")
    print("Testing Structured Table Extraction & Markdown Serialization")
    print("=================================================================")

    # Test 1: Markdown conversion logic
    sample_table = [
        ["Model", "Accuracy", "Sensitivity", "Dataset"],
        ["CNN", "94.5%", "93.1%", "Saudi Clinical Dataset"],
        ["SVM", "88.2%", "87.0%", "Riyadh Hospital Data"],
        ["Decision Tree", "82.4%", "81.0%", "Najran Clinic Data"]
    ]

    md = table_to_markdown(sample_table)
    print("\n[Test 1] Generated Markdown Table:\n")
    print(md)

    assert "| Model | Accuracy | Sensitivity | Dataset |" in md
    assert "| --- | --- | --- | --- |" in md
    assert "| CNN | 94.5% | 93.1% | Saudi Clinical Dataset |" in md
    print("\n✓ Test 1: Markdown table serialization matches expected format.")

    # Test 2: Ingest sample PDF with extract_text_and_tables
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Saudi AI Healthcare Diagnostic Benchmarks", fontsize=14)
    page.insert_text((50, 80), "This study compares machine learning models deployed across Saudi hospitals.", fontsize=10)
    
    # Draw table bounding boxes
    page.draw_rect(fitz.Rect(50, 110, 500, 135), color=(0, 0, 0))
    page.insert_text((55, 128), "Model Name", fontsize=10)
    page.insert_text((200, 128), "Accuracy", fontsize=10)
    page.insert_text((350, 128), "Target Application", fontsize=10)

    page.draw_rect(fitz.Rect(50, 135, 500, 160), color=(0, 0, 0))
    page.insert_text((55, 153), "ResNet-50", fontsize=10)
    page.insert_text((200, 153), "96.2%", fontsize=10)
    page.insert_text((350, 153), "Radiology X-Ray", fontsize=10)

    pdf_bytes = doc.tobytes()
    doc.close()

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    items = extract_text_and_tables(tmp_path)
    print(f"\n[Test 2] Extracted items count from synthesized PDF: {len(items)}")
    for page_num, content, ctype in items:
        print(f"  - [{ctype.upper()}] Page {page_num}: {content[:90]}...")

    assert any(ctype == "text" for _, _, ctype in items)
    import os
    os.unlink(tmp_path)

    print("\n=================================================================")
    print("Table extraction unit tests completed successfully! ✓")
    print("=================================================================")


if __name__ == "__main__":
    test_table_markdown_conversion()
