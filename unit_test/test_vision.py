"""
Test Script: Multi-Modal Vision & Chart Extraction Diagnostic
Validates image extraction from PDFs, size filtering (ignoring small icons/logos),
base64 encoding, and payload formatting for Vision AI providers.
"""

import fitz  # PyMuPDF
import base64
import io
from PIL import Image
from typing import List, Dict, Optional


MIN_IMAGE_WIDTH = 150
MIN_IMAGE_HEIGHT = 150
MAX_IMAGE_DIM = 800


def extract_pdf_images(pdf_path: str) -> List[Dict]:
    """
    Extracts significant images and charts from a PDF file.
    Filters out decorative icons, bullet points, and tiny logos (width/height < 150px).
    Resizes large images to max 800px for ultra-fast Vision AI processing.
    """
    doc = fitz.open(pdf_path)
    extracted_images = []

    for i, page in enumerate(doc):
        page_num = i + 1
        image_list = page.get_images(full=True)

        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                width = base_image["width"]
                height = base_image["height"]
                ext = base_image["ext"]

                # Filter out tiny icons, logos, and separators
                if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                    continue

                # Optimize and resize for fast Vision API call
                pil_img = Image.open(io.BytesIO(image_bytes))
                if pil_img.mode in ("RGBA", "P"):
                    pil_img = pil_img.convert("RGB")

                # Scale down if larger than MAX_IMAGE_DIM to reduce memory and transmission time
                if max(pil_img.size) > MAX_IMAGE_DIM:
                    pil_img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM), Image.Resampling.LANCZOS)

                buffer = io.BytesIO()
                pil_img.save(buffer, format="JPEG", quality=85)
                b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

                extracted_images.append({
                    "page": page_num,
                    "index": img_idx + 1,
                    "width": width,
                    "height": height,
                    "base64": b64_str,
                })
            except Exception as e:
                # Silently skip corrupted image streams
                continue

    doc.close()
    return extracted_images


def test_vision_extraction_pipeline():
    print("=================================================================")
    print("Testing Multi-Modal Vision & Chart Extraction Pipeline")
    print("=================================================================")

    # Test 1: Synthesize a PDF with a large chart-like image and a tiny icon
    doc = fitz.open()
    page = doc.new_page()

    # 1. Create a large simulated chart image (400x300)
    chart_img = Image.new("RGB", (400, 300), color=(240, 240, 240))
    chart_buffer = io.BytesIO()
    chart_img.save(chart_buffer, format="PNG")
    chart_bytes = chart_buffer.getvalue()

    # 2. Create a tiny icon (24x24) that should be filtered out
    icon_img = Image.new("RGB", (24, 24), color=(255, 0, 0))
    icon_buffer = io.BytesIO()
    icon_img.save(icon_buffer, format="PNG")
    icon_bytes = icon_buffer.getvalue()

    # Insert both into the PDF
    page.insert_image(fitz.Rect(50, 50, 450, 350), stream=chart_bytes)
    page.insert_image(fitz.Rect(50, 400, 74, 424), stream=icon_bytes)

    pdf_bytes = doc.tobytes()
    doc.close()

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    extracted = extract_pdf_images(tmp_path)
    print(f"\n[Test 1] Total extracted & filtered images: {len(extracted)}")
    
    # Assert that only the 400x300 image was extracted, and the 24x24 was filtered out!
    assert len(extracted) == 1, f"Expected 1 image, got {len(extracted)}"
    assert extracted[0]["width"] == 400
    assert extracted[0]["height"] == 300
    assert len(extracted[0]["base64"]) > 100
    print(f"  ✓ Large chart (400x300) on Page {extracted[0]['page']} preserved.")
    print(f"  ✓ Tiny icon (24x24) successfully filtered out.")

    import os
    os.unlink(tmp_path)

    print("\n=================================================================")
    print("Multi-modal Vision extraction tests completed successfully! ✓")
    print("=================================================================")


if __name__ == "__main__":
    test_vision_extraction_pipeline()
