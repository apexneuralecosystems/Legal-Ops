"""
Test PDF OCR extraction on the uploaded file.
"""
import os

file_path = "uploads/ctx_2 marks answer   .pdf"

print(f"Testing PDF OCR on: {file_path}")
print(f"File exists: {os.path.exists(file_path)}")

if not os.path.exists(file_path):
    print("File not found!")
    exit(1)

print("\n--- Testing pdf2image + pytesseract OCR ---")
try:
    from pdf2image import convert_from_path
    import pytesseract
    
    print("Converting PDF to images...")
    images = convert_from_path(file_path, dpi=150, first_page=1, last_page=3)
    print(f"Converted {len(images)} pages to images")
    
    pages_text = []
    for i, image in enumerate(images):
        print(f"Running OCR on page {i+1}...")
        text = pytesseract.image_to_string(image)
        pages_text.append(text)
        print(f"Page {i+1}: {len(text)} chars extracted")
    
    content = "\n\n".join(pages_text)
    print(f"\nTotal extracted: {len(content)} chars")
    print(f"\n=== CONTENT PREVIEW ===\n{content[:1500]}")
    
except Exception as e:
    print(f"OCR Failed: {e}")
    import traceback
    traceback.print_exc()
