import cv2
import pytesseract
import pandas as pd
from PIL import Image
import pdfplumber
from pdf2image import convert_from_path
import os

class DocumentExtractor:
    def __init__(self):  # Fixed: double underscores
        # Set tesseract path if needed (Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def extract_from_pdf(self, pdf_path):
        """Extract text from PDF"""
        text_data = []
        
        # First try direct text extraction
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_data.append({
                            'page': page_num + 1,
                            'text': text.strip()
                        })
        except:
            pass
        
        # If no text found, use OCR
        if not text_data:  # Fixed: syntax error here
            images = convert_from_path(pdf_path)  # Fixed: missing variable declaration
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image)
                if text.strip():
                    text_data.append({
                        'page': i + 1,
                        'text': text.strip()
                    })
        
        return text_data
    
    def extract_from_image(self, image_path):
        """Extract text from image"""
        # Preprocess image for better OCR
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply some preprocessing (you can enhance this)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Extract text
        text = pytesseract.image_to_string(gray)
        
        return [{
            'page': 1,
            'text': text.strip()
        }]
    
    def process_file(self, file_path):
        """Process file based on extension"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_from_pdf(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            return self.extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def to_csv(self, extracted_data, output_path):
        """Convert extracted data to CSV"""
        df = pd.DataFrame(extracted_data)
        df.to_csv(output_path, index=False)
        return output_path

# Usage
if __name__ == "__main__":  # Fixed: double underscores
    extractor = DocumentExtractor()
    
    # Process file - CHANGE THIS TO YOUR ACTUAL FILE PATH
    file_path = "/Users/sonma/Desktop/Projects/blink_ai_project/blinkAI/backend/module_data_extraction/sales_invoice_test.pdf"  # Change this to your actual file
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found!")
        print("Please update the file_path variable with the correct path to your document.")
    else:
        try:
            data = extractor.process_file(file_path)
            
            # Save to CSV
            output_csv = extractor.to_csv(data, "extracted_data.csv")
            print(f"Data extracted to: {output_csv}")
            print(f"Extracted {len(data)} pages/sections of text")
        except Exception as e:
            print(f"Error processing file: {e}")