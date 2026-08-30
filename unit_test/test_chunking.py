"""
Diagnostic test script to validate chunk_text() behavior on real PDF text.
Imports functions directly from backend.py without modifying ChromaDB or Ollama.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import extract_text, chunk_text, CHUNK_SIZE, CHUNK_OVERLAP


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_chunking.py <path_to_pdf>")
        print("Example: python test_chunking.py ./my_document.pdf")
        sys.exit(0)

    pdf_path = sys.argv[1]
    if not os.path.isfile(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    print(f"{'=' * 60}")
    print(f"Testing chunk_text() on: {os.path.basename(pdf_path)}")
    print(f"CHUNK_SIZE = {CHUNK_SIZE}  |  CHUNK_OVERLAP = {CHUNK_OVERLAP}")
    print(f"{'=' * 60}\n")

    pages = extract_text(pdf_path)
    print(f"Extracted non-empty pages: {len(pages)}\n")

    if not pages:
        print("No text extracted — file is empty or encrypted.")
        sys.exit(0)

    all_chunks = []
    for page_num, page_text in pages:
        page_chunks = chunk_text(page_text)
        all_chunks.extend(page_chunks)

    total = len(all_chunks)
    print(f"[A] Total chunks: {total}")

    if total == 0:
        print("No chunks produced.")
        sys.exit(0)

    lengths = [len(c) for c in all_chunks]
    min_len = min(lengths)
    max_len = max(lengths)
    avg_len = sum(lengths) / total

    print(f"[B] Shortest chunk: {min_len} chars")
    print(f"    Longest chunk: {max_len} chars")
    print(f"    Average length: {avg_len:.1f} chars\n")

    oversized = [(i, c) for i, c in enumerate(all_chunks) if len(c) > CHUNK_SIZE]
    print(f"[C] Chunks exceeding CHUNK_SIZE ({CHUNK_SIZE}): {len(oversized)} / {total}")

    if oversized:
        print("    --- Oversized Chunks Details ---")
        for idx, chunk in oversized:
            preview = chunk[:120].replace('\n', '\\n')
            print(f"    Chunk #{idx}: {len(chunk)} chars | \"{preview}...\"")
    print()

    if total < 2:
        print("[D] Only 1 chunk — no overlap to measure.\n")
        avg_overlap = 0
    else:
        overlaps = []
        for i in range(total - 1):
            c1 = all_chunks[i]
            c2 = all_chunks[i + 1]
            max_possible = min(len(c1), len(c2))
            measured = 0
            for length in range(1, max_possible + 1):
                if c1[-length:] == c2[:length]:
                    measured = length
            overlaps.append(measured)

        avg_overlap = sum(overlaps) / len(overlaps)
        non_zero = sum(1 for o in overlaps if o > 0)
        zero_count = sum(1 for o in overlaps if o == 0)

        print(f"[D] Overlap between consecutive chunks ({len(overlaps)} pairs):")
        print(f"    Pairs with overlap > 0: {non_zero}")
        print(f"    Pairs with 0 overlap: {zero_count}")
        if overlaps:
            print(f"    Min overlap: {min(overlaps)} chars")
            print(f"    Max overlap: {max(overlaps)} chars")
            print(f"    Avg overlap: {avg_overlap:.1f} chars")
        print()

    print(f"{'=' * 60}")
    print(f"Summary:")
    print(f"  Chunks exceeding CHUNK_SIZE: {len(oversized)} / {total}")
    print(f"  Average measured overlap: {avg_overlap:.1f} chars (CHUNK_OVERLAP: {CHUNK_OVERLAP})")
    print(f"{'=' * 60}")

    empty_result = chunk_text("")
    if empty_result == []:
        print("\n✓ chunk_text('') correctly returns [] without errors.")
    else:
        print(f"\n✗ chunk_text('') returned {empty_result} instead of []")


if __name__ == "__main__":
    main()
