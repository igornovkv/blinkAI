import os
import pandas as pd
import json
from dotenv import load_dotenv
from google.cloud import documentai
from google.oauth2 import service_account
import mimetypes

class DocumentExtractor:
    def __init__(self):
        self._load_google_cloud_credentials()
        self._initialize_document_ai_client()
    
    def _load_google_cloud_credentials(self):
        """Load Google Cloud credentials and configuration from .env file."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        env_path = os.path.join(project_root, '.env')
        load_dotenv(env_path)
        
        # Load all required environment variables
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        self.location = os.getenv('DOCUMENT_AI_LOCATION')
        self.processor_general = os.getenv('DOCUMENT_AI_PROCESSOR_ID_GENERAL')
        self.processor_invoice = os.getenv('DOCUMENT_AI_PROCESSOR_ID_INVOICE')
        self.processor_expense = os.getenv('DOCUMENT_AI_PROCESSOR_ID_EXPENSE')
        credentials_path_from_env = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Handle credentials path - make it absolute if it's relative
        if credentials_path_from_env.startswith('./'):
            self.credentials_path = os.path.join(project_root, credentials_path_from_env[2:])
        elif not os.path.isabs(credentials_path_from_env):
            self.credentials_path = os.path.join(project_root, credentials_path_from_env)
        else:
            self.credentials_path = credentials_path_from_env
        
        # Validate the credentials file exists
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Google Cloud credentials file not found: {self.credentials_path}")
        
        # Validate other required fields
        required_vars = [
            'GOOGLE_CLOUD_PROJECT_ID', 'DOCUMENT_AI_LOCATION', 
            'DOCUMENT_AI_PROCESSOR_ID_GENERAL', 'DOCUMENT_AI_PROCESSOR_ID_INVOICE',
            'DOCUMENT_AI_PROCESSOR_ID_EXPENSE', 'GOOGLE_APPLICATION_CREDENTIALS'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                f"Ensure they are set in .env at: {env_path}"
            )
        
        # Set the credentials environment variable for Google Cloud (use absolute path)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
        print(f"✅ Using credentials file: {self.credentials_path}")
    
    def _initialize_document_ai_client(self):
        """Initialize the Document AI client."""
        try:
            self.client = documentai.DocumentProcessorServiceClient()
        except Exception as e:
            raise Exception(f"Failed to initialize Document AI client: {e}")
    
    def _get_processor_name(self, processor_type="general"):
        """Get the full processor name for Document AI."""
        processor_map = {
            "general": self.processor_general,
            "invoice": self.processor_invoice,
            "expense": self.processor_expense
        }
        
        processor_id = processor_map.get(processor_type)
        if not processor_id:
            raise ValueError(f"Invalid processor type: {processor_type}")
        
        return self.client.processor_path(self.project_id, self.location, processor_id)
    
    def _process_document_with_ai(self, file_content, mime_type, processor_type="general"):
        """Process document using Google Cloud Document AI."""
        try:
            processor_name = self._get_processor_name(processor_type)
            
            # Create the document object
            raw_document = documentai.RawDocument(
                content=file_content,
                mime_type=mime_type
            )
            
            # Configure the process request
            request = documentai.ProcessRequest(
                name=processor_name,
                raw_document=raw_document
            )
            
            # Process the document
            result = self.client.process_document(request=request)
            return result.document
            
        except Exception as e:
            print(f"Error processing document with Document AI ({processor_type}): {e}")
            return None
    
    def _extract_key_info_from_document_ai(self, document, start_page_num=1):
        """Extract key information from Document AI response for all pages."""
        if not document:
            return []
        
        all_pages_data = []
        
        # Process each page in the document
        for page_idx, page in enumerate(document.pages):
            page_num = start_page_num + page_idx
            
            extracted_info = {
                "date": None,
                "total_amount": None,
                "costs": [],
                "vendor_name": None,
                "invoice_number": None,
                "currency": None
            }
            
            # Extract entities (these are usually document-level, so we'll assign them to the first page)
            if page_idx == 0:  # Only process entities for the first page to avoid duplicates
                for entity in document.entities:
                    entity_type = entity.type_
                    entity_value = entity.mention_text.strip() if entity.mention_text else ""
                    
                    # Map Document AI entity types to our desired fields
                    if entity_type in ["invoice_date", "due_date", "date"]:
                        if not extracted_info["date"]:
                            extracted_info["date"] = entity_value
                    elif entity_type in ["total_amount", "net_amount", "invoice_total"]:
                        extracted_info["total_amount"] = entity_value
                    elif entity_type in ["supplier_name", "vendor_name", "remit_to_name"]:
                        extracted_info["vendor_name"] = entity_value
                    elif entity_type in ["invoice_id", "invoice_number", "receipt_number"]:
                        extracted_info["invoice_number"] = entity_value
                    elif entity_type == "currency":
                        extracted_info["currency"] = entity_value
            
            # Extract line items from tables on this specific page
            for table in page.tables:
                headers = []
                
                # Extract headers
                if table.header_rows:
                    for cell in table.header_rows[0].cells:
                        header_text = ""
                        for segment in cell.layout.text_anchor.text_segments:
                            header_text += document.text[segment.start_index:segment.end_index]
                        headers.append(header_text.strip().lower())
                
                # Extract data rows
                for row in table.body_rows:
                    row_data = {}
                    for i, cell in enumerate(row.cells):
                        cell_text = ""
                        for segment in cell.layout.text_anchor.text_segments:
                            cell_text += document.text[segment.start_index:segment.end_index]
                        
                        if i < len(headers):
                            row_data[headers[i]] = cell_text.strip()
                        else:
                            row_data[f"column_{i}"] = cell_text.strip()
                    
                    # Try to identify description and amount columns
                    description = None
                    amount = None
                    
                    for key, value in row_data.items():
                        if any(keyword in key for keyword in ["description", "item", "product", "service"]):
                            description = value
                        elif any(keyword in key for keyword in ["amount", "price", "cost", "total"]):
                            amount = value
                    
                    # If we couldn't find specific columns, use the first few columns
                    if not description and len(row_data) > 0:
                        description = list(row_data.values())[0]
                    if not amount and len(row_data) > 1:
                        amount = list(row_data.values())[-1]  # Usually amount is in the last column
                    
                    if description and amount and description.strip() and amount.strip():
                        extracted_info["costs"].append({
                            "description": description,
                            "amount": amount
                        })
            
            # Fallback: extract key information from raw text if entities are empty (only for first page)
            if page_idx == 0 and not any([extracted_info["date"], extracted_info["total_amount"], extracted_info["vendor_name"]]):
                text = document.text
                
                # Simple pattern matching as fallback
                import re
                
                # Look for dates
                date_patterns = [
                    r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                    r'\b\d{2,4}[/-]\d{1,2}[/-]\d{1,2}\b',
                    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match and not extracted_info["date"]:
                        extracted_info["date"] = match.group()
                        break
                
                # Look for total amounts
                amount_patterns = [
                    r'(?:total|amount due|grand total)[:\s]*\$?[\d,]+\.?\d*',
                    r'\$[\d,]+\.\d{2}'
                ]
                
                for pattern in amount_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches and not extracted_info["total_amount"]:
                        extracted_info["total_amount"] = matches[-1]  # Usually the last/largest amount
                        break
            
            # Add this page's data to the results
            all_pages_data.append({
                'page': page_num,
                'extracted_info': extracted_info
            })
        
        return all_pages_data
    
    def _read_file_content(self, file_path):
        """Read file content and determine MIME type."""
        with open(file_path, 'rb') as f:
            content = f.read()
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            # Default MIME types for common formats
            ext = os.path.splitext(file_path)[1].lower()
            mime_map = {
                '.pdf': 'application/pdf',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.tiff': 'image/tiff',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp'
            }
            mime_type = mime_map.get(ext, 'application/octet-stream')
        
        return content, mime_type
    
    def extract_key_info_from_pdf(self, pdf_path, processor_type="general"):
        """Extract key information from PDF using Document AI."""
        key_data = []
        
        try:
            content, mime_type = self._read_file_content(pdf_path)
            
            print(f"Processing PDF with Document AI ({processor_type} processor)...")
            document = self._process_document_with_ai(content, mime_type, processor_type)
            
            if document:
                print(f"Document has {len(document.pages)} page(s)")
                results = self._extract_key_info_from_document_ai(document, 1)
                if results:
                    key_data.extend(results)  # Use extend instead of append
                    
        except Exception as e:
            print(f"Error processing PDF: {e}")
            
        return key_data
    
    def extract_key_info_from_image(self, image_path, processor_type="general"):
        """Extract key information from image using Document AI."""
        try:
            content, mime_type = self._read_file_content(image_path)
            
            print(f"Processing image with Document AI ({processor_type} processor)...")
            document = self._process_document_with_ai(content, mime_type, processor_type)
            
            if document:
                results = self._extract_key_info_from_document_ai(document, 1)
                return results if results else []
                
        except Exception as e:
            print(f"Error processing image: {e}")
            
        return []
    
    def extract_key_info(self, file_path, processor_type="general"):
        """Extract key information based on file type using specified processor."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        print(f"Using processor: {processor_type}")
        
        if file_ext == '.pdf':
            return self.extract_key_info_from_pdf(file_path, processor_type)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
            return self.extract_key_info_from_image(file_path, processor_type)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def test_all_processors(self, file_path):
        """Test the document with all three processors and return results."""
        results = {}
        processors = ["general", "invoice", "expense"]
        
        for processor in processors:
            try:
                print(f"\n{'='*50}")
                print(f"Testing with {processor.upper()} processor")
                print(f"{'='*50}")
                
                key_data = self.extract_key_info(file_path, processor)
                results[processor] = key_data
                
                if key_data:
                    print(f"\n✅ {processor.upper()} processor results:")
                    self.print_key_info(key_data)
                else:
                    print(f"❌ No data extracted with {processor} processor")
                    
            except Exception as e:
                print(f"❌ Error with {processor} processor: {e}")
                results[processor] = []
        
        return results
    
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
    
    file_path = "/Users/sonma/Desktop/Projects/blink_ai_project/blinkAI/backend/module_data_extraction/Sales_Invoice_151724.pdf"
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found!")
    else:
        try:
            print("🔍 Extracting key information using Google Cloud Document AI...")
            
            # Test all processors
            all_results = extractor.test_all_processors(file_path)
            
            # Save results from each processor
            for processor_name, key_data in all_results.items():
                if key_data:
                    csv_output = extractor.save_key_info_to_csv(
                        key_data, 
                        f"key_information_{processor_name}.csv"
                    )
                    if csv_output:
                        print(f"\n✅ {processor_name.upper()} results saved to: {csv_output}")
            
            # You can also test with a specific processor:
            # key_data = extractor.extract_key_info(file_path, "invoice")
            # extractor.print_key_info(key_data)
            
        except Exception as e:
            print(f"❌ Error processing file: {e}")