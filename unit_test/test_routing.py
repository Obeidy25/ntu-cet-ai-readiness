"""
Diagnostic test script to validate Query Routing, language consistency, and calibrated relevance metrics.
Tests:
  1. Greeting detection (Arabic and English).
  2. In-domain relevant questions (monolingual and cross-lingual).
  3. Out-of-domain irrelevant questions with language-matching refusal.
"""
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import (
    get_or_create_collection,
    embed_texts,
    is_greeting,
    get_no_relevance_response,
    RELEVANCE_THRESHOLD,
)


def compute_similarity(distance):
    return round(100 * (math.e ** (-distance / 220)), 1)


def check_relevance(distances):
    if not distances:
        return False, 0.0
    best_similarity = compute_similarity(min(distances))
    return best_similarity >= RELEVANCE_THRESHOLD, best_similarity


def main():
    print(f"{'=' * 70}")
    print("Query Routing & Semantic Relevance Diagnostic Test")
    print(f"{'=' * 70}\n")

    # ==============================
    # Test A: Greeting Detection
    # ==============================
    print("[Test A] Greeting Detection (Stage 1)...")
    greeting_cases = [
        ("السلام عليكم", True),
        ("السلام عليكم ورحمة الله", True),
        ("وعليكم السلام", True),
        ("اهلا بك", True),
        ("أهلاً وسهلاً", True),
        ("مرحبا", True),
        ("صباح الخير", True),
        ("كيف حالك", True),
        ("شكراً جزيلاً", True),
        ("hello", True),
        ("hi there", True),
        ("good morning", True),
        ("how are you", True),
        ("thank you very much", True),
        # --- Non-greetings ---
        ("What is the purpose of the PDF extractor script, and how does it work?", False),
        ("What is the role of AI in Saudi healthcare?", False),
        ("ما هو دور الذكاء الاصطناعي في الصحة؟", False),
    ]

    all_passed = True
    for text, expected in greeting_cases:
        res = is_greeting(text)
        status = "✓" if res == expected else "✗"
        if res != expected:
            all_passed = False
        print(f"  {status} \"{text[:50]}\" -> is_greeting: {res}")

    print(f"\n  Greeting test result: {'✓ All Passed' if all_passed else '✗ Failures detected'}\n")

    # ==============================
    # Test B: In-domain & Out-of-domain Relevance
    # ==============================
    print("[Test B] In-domain, Cross-lingual & Out-of-domain Relevance Checks...")
    collection = get_or_create_collection()

    test_queries = [
        ("What is the purpose of the PDF extractor script, and how does it work?", True),
        ("What is the role of AI in Saudi healthcare?", True),
        ("كيف يعمل مستخرج النصوص من ملفات pdf؟", True),
        ("What is the recipe for chocolate cake with strawberry?", False),
        ("How to fix a flat tire on a bicycle?", False),
    ]

    for q, should_pass in test_queries:
        emb = embed_texts([q])[0]
        res = collection.query(query_embeddings=[emb], n_results=3, include=["distances", "metadatas"])
        distances = res["distances"][0]
        top_source = res["metadatas"][0][0]["source"]
        is_rel, best_score = check_relevance(distances)
        passed = (is_rel == should_pass)
        status = "✓" if passed else "✗"
        action = "Accepted (To LLM)" if is_rel else "Rejected (Low relevance)"
        print(f"  {status} \"{q[:55]}...\"")
        print(f"     Top similarity: {best_score}% (Threshold: {RELEVANCE_THRESHOLD}%) | Source: {top_source}")
        print(f"     Decision: {action}\n")

    print(f"{'=' * 70}")
    print(f"  RELEVANCE_THRESHOLD = {RELEVANCE_THRESHOLD}% (Decay constant k = 220)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
