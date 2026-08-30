"""
Diagnostic test script to validate Policy Gap Analysis logic:
- Fetching document list from ChromaDB
- Extracting document text page-by-page
- Constructing prompt and measuring token volume
- Enforcing MAX_CHUNKS_PER_DOC_FOR_COMPARE chunk caps
- Optional LLM invocation via Ollama
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import get_or_create_collection, generate_answer, ITU_AI_READINESS_DIMENSIONS

MAX_CHUNKS_PER_DOC_FOR_COMPARE = 10


def list_documents(collection):
    """Lists document filenames and chunk counts from ChromaDB."""
    if collection.count() == 0:
        return {}
    all_items = collection.get(include=["metadatas"])
    counts = {}
    for meta in all_items["metadatas"]:
        source = meta["source"]
        counts[source] = counts.get(source, 0) + 1
    return counts


def get_doc_text(collection, filename):
    """Fetches text of a document from ChromaDB ordered by page number up to chunk cap."""
    result = collection.get(
        where={"source": filename},
        include=["documents", "metadatas"]
    )
    if not result["documents"]:
        return ""
    pairs = sorted(
        zip(result["documents"], result["metadatas"]),
        key=lambda p: p[1]["page"]
    )
    pairs = pairs[:MAX_CHUNKS_PER_DOC_FOR_COMPARE]
    return "\n\n".join(chunk for chunk, _ in pairs)


def build_compare_prompt(doc_a_name, text_a, doc_b_name, text_b):
    """Builds the structured policy comparison prompt mapped to ITU AI Readiness 2.0 dimensions."""
    dimensions_list = "\n".join(f"- {d}" for d in ITU_AI_READINESS_DIMENSIONS)

    return f"""You are an AI policy analyst evaluating documents against the ITU AI Readiness 2.0 framework's 13 official dimensions:
{dimensions_list}

Compare the two policy/strategy documents below and produce a structured gap analysis. Structure your analysis using the exact dimension names above as section headers (bold). Under each dimension header, write 1-2 sentences of specific findings grounded in the actual document text — do not write generic filler like 'not mentioned' for every dimension; only include a dimension if the documents contain relevant content for it, and skip dimensions with no evidence in either document rather than listing them as empty. Also note if the gap relates to ITU-T Y.3172 pipeline nodes (SRC, Collector, Pre-producer, Model, Policy, Distributor, SINK) where relevant — this is most relevant to the 'AI & Policies' and 'Digital Infrastructure' dimensions.

Focus on: (1) topics covered in one document but missing in the other, (2) differences in depth or specificity on shared topics, (3) concrete recommendations to close the identified gaps. Cite which document each point comes from. Do not fabricate information not present in either document.

=== Document A: {doc_a_name} ===
{text_a}

=== Document B: {doc_b_name} ===
{text_b}

Provide your analysis in exactly this format:
1. Topics only in Document A (organized by ITU dimension, using headers)
2. Topics only in Document B (organized by ITU dimension, using headers)
3. Shared topics with notable differences (organized by ITU dimension, using headers)
4. Recommendations to close the gaps (organized by ITU dimension, using headers)
"""


def main():
    print(f"{'=' * 60}")
    print("Policy Gap Analysis Diagnostic Test")
    print(f"{'=' * 60}\n")

    collection = get_or_create_collection()

    # ==============================
    # Test 1: List Documents
    # ==============================
    print("[Test 1] Listing documents from ChromaDB...")
    counts = list_documents(collection)

    if not counts:
        print("  ✗ No documents in database. Please upload at least 2 PDFs first.")
        sys.exit(1)

    print(f"  Total documents: {len(counts)}")
    doc_names = []
    for name, n in counts.items():
        print(f"    - {name}: {n} chunks")
        doc_names.append(name)

    if len(counts) < 2:
        print("\n  ⚠ Need at least 2 documents for comparison.")
        sys.exit(1)

    print("  ✓ Done — 2 or more documents available.\n")

    # ==============================
    # Test 2: Extract text for comparison
    # ==============================
    doc_a = doc_names[0]
    doc_b = doc_names[1]

    print("[Test 2] Extracting text for Document A and B...")
    print(f"  Document A: {doc_a}")
    print(f"  Document B: {doc_b}")

    text_a = get_doc_text(collection, doc_a)
    text_b = get_doc_text(collection, doc_b)

    print(f"  Text length A: {len(text_a)} chars")
    print(f"  Text length B: {len(text_b)} chars")

    if not text_a or not text_b:
        print("  ✗ One of the documents has empty text!")
        sys.exit(1)

    print("  ✓ Done — Both documents contain extracted text.\n")

    # ==============================
    # Test 3: Non-existent document test
    # ==============================
    print("[Test 3] Testing non-existent document handling...")
    fake_text = get_doc_text(collection, "nonexistent_file_12345.pdf")
    if fake_text == "":
        print("  ✓ get_doc_text() returned empty string for missing file as expected.\n")
    else:
        print(f"  ✗ Expected empty string, got {len(fake_text)} chars\n")

    # ==============================
    # Test 4: Chunk Cap Check
    # ==============================
    print(f"[Test 4] Checking MAX_CHUNKS_PER_DOC_FOR_COMPARE = {MAX_CHUNKS_PER_DOC_FOR_COMPARE}...")
    result_a = collection.get(where={"source": doc_a}, include=["documents"])
    result_b = collection.get(where={"source": doc_b}, include=["documents"])
    total_chunks_a = len(result_a["documents"])
    total_chunks_b = len(result_b["documents"])

    actual_chunks_a = text_a.count("\n\n") + 1 if text_a else 0
    actual_chunks_b = text_b.count("\n\n") + 1 if text_b else 0

    print(f"  Document A: {total_chunks_a} in DB -> {actual_chunks_a} chunks included (cap: {MAX_CHUNKS_PER_DOC_FOR_COMPARE})")
    print(f"  Document B: {total_chunks_b} in DB -> {actual_chunks_b} chunks included (cap: {MAX_CHUNKS_PER_DOC_FOR_COMPARE})")

    limited_a = actual_chunks_a <= MAX_CHUNKS_PER_DOC_FOR_COMPARE
    limited_b = actual_chunks_b <= MAX_CHUNKS_PER_DOC_FOR_COMPARE
    if limited_a and limited_b:
        print("  ✓ Chunk cap enforced correctly.\n")
    else:
        print("  ✗ Chunk cap exceeded!\n")

    # ==============================
    # Test 5: Build Prompt & Size Check
    # ==============================
    print("[Test 5] Building comparison prompt and measuring size...")
    prompt = build_compare_prompt(doc_a, text_a, doc_b, text_b)
    print(f"  Total prompt length: {len(prompt)} chars (~{len(prompt) // 4} approx tokens)")
    print(f"  First 200 chars:\n  {prompt[:200]}...\n")

    if "--call-llm" in sys.argv:
        print("[Test 5b] Sending prompt to Ollama...")
        try:
            answer = generate_answer(prompt, "ollama", "llama3.1", None)
            print(f"  ✓ LLM responded successfully — Output length: {len(answer)} chars")
            print(f"  First 500 chars of output:\n  {answer[:500]}")
        except Exception as e:
            print(f"  ✗ Call failed: {e}")
    else:
        print("[Test 5b] Skipping LLM call (pass --call-llm to execute)")

    print(f"\n{'=' * 60}")
    print("Test Summary:")
    print(f"  Available documents: {len(counts)}")
    print(f"  Missing doc handling: {'✓ Passed' if fake_text == '' else '✗ Failed'}")
    print(f"  Chunk cap check: {'✓ Enforced' if (limited_a and limited_b) else '✗ Failed'}")
    print(f"  Prompt size: {len(prompt)} chars")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
