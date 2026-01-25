import os
from pypdf import PdfReader

def check_pdf(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    try:
        reader = PdfReader(file_path)
        print(f"Total Pages: {len(reader.pages)}")
        
        has_text = False
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                print(f"Page {i+1} has text (first 100 chars): {text.strip()[:100]}")
                has_text = True
            else:
                print(f"Page {i+1} appears to be a scan (no text extracted)")
        
        if not has_text:
            print("Conclusion: This PDF appears to be a scan and REQUIRES OCR.")
        else:
            print("Conclusion: This PDF has embedded text.")
            
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    file_path = r"c:\Users\rahul\Documents\GitHub\legal ops 01\Legal-Ops\uploads\Teo Yek Ming (Mendakwa sebagai pemegang jawatan Yayasan.PDF"
    check_pdf(file_path)
