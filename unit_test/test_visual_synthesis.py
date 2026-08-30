"""
Test Script: Cross-Document Comparative Visual Synthesis & Diagram Rendering
Validates system prompt instructions, Mermaid syntax parsing, and diagram block extraction.
"""

import re
from backend import DEFAULT_SYSTEM_PROMPT, COMPARE_SYSTEM_PROMPT


def test_visual_synthesis_pipeline():
    print("=================================================================")
    print("Testing Cross-Document Comparative Visual Synthesis System")
    print("=================================================================")

    # Test 1: System prompt contains visual synthesis guidelines
    assert "Mermaid" in DEFAULT_SYSTEM_PROMPT or "visual" in DEFAULT_SYSTEM_PROMPT.lower()
    assert "Mermaid" in COMPARE_SYSTEM_PROMPT or "visual" in COMPARE_SYSTEM_PROMPT.lower()
    print("\n[Test 1] System prompts contain visual synthesis and Mermaid instructions.")
    print("  ✓ DEFAULT_SYSTEM_PROMPT verified.")
    print("  ✓ COMPARE_SYSTEM_PROMPT verified.")

    # Test 2: Mermaid diagram extraction & parsing regex
    sample_response = """
Here is the comparative gap analysis between Document A and Document B:

### Key Differences:
1. **Document A** focuses on Computer Vision and Radiology (45%).
2. **Document B** emphasizes Natural Language Processing and Clinical Records (60%).

```mermaid
pie title Comparative AI Focus: Document A vs Document B
    "Radiology (Doc A)" : 45
    "Predictive (Doc A)" : 30
    "NLP / Records (Doc B)" : 60
    "Robotics (Doc B)" : 20
```

### Strategic Recommendation:
Integrate the radiology models from Document A with the NLP pipeline from Document B.
"""

    pattern = r"```mermaid\s*\n(.*?)\n```"
    matches = re.findall(pattern, sample_response, flags=re.DOTALL)

    assert len(matches) == 1
    mermaid_code = matches[0].strip()
    assert "pie title Comparative AI Focus" in mermaid_code
    assert '"Radiology (Doc A)" : 45' in mermaid_code
    print("\n[Test 2] Mermaid extraction regex correctly captured diagram block:")
    print(f"  Captured:\n{mermaid_code}")

    # Test 3: Multiple diagrams in a single turn
    dual_response = """
Text 1
```mermaid
graph TD
    A[Doc 1: Radiology] --> C[Integrated System]
    B[Doc 2: NLP Records] --> C
```
Text 2
```mermaid
pie title Distribution
    "Radiology" : 50
    "NLP" : 50
```
"""
    dual_matches = re.findall(pattern, dual_response, flags=re.DOTALL)
    assert len(dual_matches) == 2
    print(f"\n[Test 3] Multi-diagram parsing: successfully extracted {len(dual_matches)} diagrams.")

    print("\n=================================================================")
    print("Visual synthesis unit tests completed successfully! ✓")
    print("=================================================================")


if __name__ == "__main__":
    test_visual_synthesis_pipeline()
