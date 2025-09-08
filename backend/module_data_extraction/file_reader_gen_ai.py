import os
import base64
import pandas as pd
import json
from pdf2image import convert_from_path
from PIL import Image
from dotenv import load_dotenv
import openai
from io import BytesIO

class DocumentExtractor:
    def __init__(self):
        self._load_openai_api_key()
        self.client = openai.OpenAI(api_key=self.openai_api_key)
    
    def _load_openai_api_key(self):
        """Load OPENAI_API_KEY from project-level .env and expose it."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        env_path = os.path.join(project_root, '.env')
        load_dotenv(env_path)
        
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise EnvironmentError(
                f"OPENAI_API_KEY not found. Ensure it is set in the environment or in .env at: {env_path}"
            )
        os.environ['OPENAI_API_KEY'] = self.openai_api_key
    
    def _encode_image_to_base64(self, image):
        """Convert PIL image to base64 string"""
        if isinstance(image, str):  # If it's a file path
            with open(image, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        else:  # If it's a PIL image
            buffer = BytesIO()
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(buffer, format='JPEG', quality=95)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _extract_key_info_directly(self, image, page_num=1):
        """Extract only key information directly from image using OpenAI Vision"""
        try:
            base64_image = self._encode_image_to_base64(image)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this document image and extract ONLY the following key information in JSON format:
                                Required fields:
                                - date: Any date found in the document (invoice date, due date, etc.)
                                - total_amount: The total cost/amount (look for "Total", "Amount Due", "Grand Total", etc.)
                                - costs: List of individual line items with descriptions and amounts
                                - vendor_name: Company/vendor name
                                - invoice_number: Invoice or reference number
                                - currency: Currency used (USD, EUR, etc.)
                                For costs, structure as:
                                "costs": [
                                    {"description": "item description", "amount": "XX.XX"},
                                    {"description": "item description", "amount": "XX.XX"}
                                ]
                                Return ONLY a valid JSON object. If a field cannot be found, use null.
                                Do not include any explanatory text, just the JSON."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0
            )
            
            extracted_data = response.choices[0].message.content.strip()
            
            # Try to parse as JSON to validate
            try:
                json_data = json.loads(extracted_data)
                return {
                    'page': page_num,
                    'extracted_info': json_data
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text
                return {
                    'page': page_num,
                    'extracted_info': extracted_data,
                    'note': 'Failed to parse as JSON'
                }
            
        except Exception as e:
            print(f"Error extracting key info from page {page_num}: {e}")
            return None
    
    def extract_key_info_from_pdf(self, pdf_path):
        """Extract key information from PDF"""
        key_data = []
        
        try:
            images = convert_from_path(pdf_path, dpi=200, fmt='JPEG')
            
            for i, image in enumerate(images):
                print(f"Extracting key information from page {i + 1}/{len(images)}...")
                result = self._extract_key_info_directly(image, i + 1)
                if result:
                    key_data.append(result)
                    
        except Exception as e:
            print(f"Error processing PDF: {e}")
            
        return key_data
    
    def extract_key_info_from_image(self, image_path):
        """Extract key information from image"""
        result = self._extract_key_info_directly(image_path, 1)
        return [result] if result else []
    
    def extract_key_info(self, file_path):
        """Extract key information based on file type"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_key_info_from_pdf(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']:
            return self.extract_key_info_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def save_key_info_to_csv(self, key_data, output_path="key_info_extracted.csv"):
        """Save extracted key information to CSV in a clean format"""
        if not key_data:
            print("No data to save.")
            return None
            
        # Flatten the data for CSV
        flattened_data = []
        
        for item in key_data:
            page = item['page']
            info = item['extracted_info']
            
            if isinstance(info, dict):
                # Create a base record
                base_record = {
                    'page': page,
                    'date': info.get('date'),
                    'vendor_name': info.get('vendor_name'),
                    'invoice_number': info.get('invoice_number'),
                    'total_amount': info.get('total_amount'),
                    'currency': info.get('currency')
                }
                
                # Handle costs - if there are line items, create separate rows
                costs = info.get('costs', [])
                if costs and isinstance(costs, list):
                    for cost_item in costs:
                        if isinstance(cost_item, dict):
                            record = base_record.copy()
                            record['cost_description'] = cost_item.get('description')
                            record['cost_amount'] = cost_item.get('amount')
                            flattened_data.append(record)
                    
                    # If no costs were added (empty or invalid costs), add base record
                    if not any(record for record in flattened_data if record['page'] == page):
                        base_record['cost_description'] = None
                        base_record['cost_amount'] = None
                        flattened_data.append(base_record)
                else:
                    # No costs found, just add base record
                    base_record['cost_description'] = None
                    base_record['cost_amount'] = None
                    flattened_data.append(base_record)
            else:
                # Fallback for non-JSON data
                flattened_data.append({
                    'page': page,
                    'raw_extracted_info': str(info),
                    'date': None,
                    'vendor_name': None,
                    'invoice_number': None,
                    'total_amount': None,
                    'currency': None,
                    'cost_description': None,
                    'cost_amount': None
                })
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(output_path, index=False)
        return output_path
    
    def print_key_info(self, key_data):
        """Print extracted key information in a readable format"""
        for item in key_data:
            print(f"\n--- PAGE {item['page']} ---")
            info = item['extracted_info']
            
            if isinstance(info, dict):
                print(f"📅 Date: {info.get('date', 'Not found')}")
                print(f"🏢 Vendor: {info.get('vendor_name', 'Not found')}")
                print(f"📄 Invoice #: {info.get('invoice_number', 'Not found')}")
                print(f"💰 Total Amount: {info.get('total_amount', 'Not found')} {info.get('currency', '')}")
                
                costs = info.get('costs', [])
                if costs:
                    print("📋 Line Items:")
                    for i, cost in enumerate(costs, 1):
                        if isinstance(cost, dict):
                            desc = cost.get('description', 'No description')
                            amount = cost.get('amount', 'No amount')
                            print(f"   {i}. {desc}: {amount}")
                else:
                    print("📋 Line Items: None found")
            else:
                print(f"Raw extracted data: {info}")

# Usage
if __name__ == "__main__":
    extractor = DocumentExtractor()
    
    file_path = "/Users/sonma/Desktop/Projects/blink_ai_project/blinkAI/backend/module_data_extraction/sales_invoice_test.pdf"
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found!")
    else:
        try:
            print("🔍 Extracting key information using OpenAI Vision...")
            
            # Extract only key information
            key_data = extractor.extract_key_info(file_path)
            
            if key_data:
                # Print results in readable format
                extractor.print_key_info(key_data)
                
                # Save to CSV
                csv_output = extractor.save_key_info_to_csv(key_data, "key_information.csv")
                if csv_output:
                    print(f"\n✅ Key information saved to: {csv_output}")
                    print(f"📊 Processed {len(key_data)} pages")
                
            else:
                print("❌ No key information could be extracted from the document.")
                
        except Exception as e:
            print(f"❌ Error processing file: {e}")