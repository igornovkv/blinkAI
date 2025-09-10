import os
import json
from dotenv import load_dotenv
from google.cloud import documentai
import mimetypes

class InvoiceExtractor:
    def __init__(self):
        self._load_google_cloud_credentials()
        self._initialize_document_ai_client()
    
    def _load_google_cloud_credentials(self):
        """Load Google Cloud credentials and configuration from .env file."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        env_path = os.path.join(project_root, '.env')
        load_dotenv(env_path)
        
        # Load required environment variables
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        self.location = os.getenv('DOCUMENT_AI_LOCATION')
        self.processor_invoice = os.getenv('DOCUMENT_AI_PROCESSOR_ID_INVOICE')
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
        
        # Set the credentials environment variable for Google Cloud (use absolute path)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
        print(f"✅ Using credentials file: {self.credentials_path}")
    
    def _initialize_document_ai_client(self):
        """Initialize the Document AI client."""
        try:
            self.client = documentai.DocumentProcessorServiceClient()
        except Exception as e:
            raise Exception(f"Failed to initialize Document AI client: {e}")
    
    def _get_processor_name(self):
        """Get the full processor name for Document AI invoice processor."""
        if not self.processor_invoice:
            raise ValueError("Invoice processor ID not found in environment variables")
        
        return self.client.processor_path(self.project_id, self.location, self.processor_invoice)
    
    def _read_file_content(self, file_path):
        """Read file content and determine MIME type."""
        with open(file_path, 'rb') as f:
            content = f.read()
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
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
    
    def extract_key_invoice_data(self, file_path):
        """
        Extract only the key invoice information we need.
        Trust Document AI to give us the right entity types directly.
        """
        try:
            content, mime_type = self._read_file_content(file_path)
            processor_name = self._get_processor_name()
            
            raw_document = documentai.RawDocument(content=content, mime_type=mime_type)
            request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
            
            print("🤖 Processing invoice...")
            result = self.client.process_document(request=request)
            document = result.document
            
            # Initialize the data we want (only supplier name now)
            invoice_data = {
                "total_cost": None,
                "invoice_id": None,
                "invoice_date": None,
                "supplier_name": None,
                "extraction_status": "success"
            }
            
            print(f"📋 Found {len(document.entities)} entities")
            
            # Just look for the entities directly as Document AI provides them
            for entity in document.entities:
                entity_type = entity.type_
                entity_value = entity.mention_text.strip() if entity.mention_text else ""
                
                print(f"Found entity: {entity_type} = {entity_value}")  # Debug line
                
                # Direct matching - let's see what Document AI actually gives us
                if entity_type == "total_amount" and invoice_data["total_cost"] is None:
                    invoice_data["total_cost"] = entity_value
                elif entity_type == "invoice_id" and invoice_data["invoice_id"] is None:
                    invoice_data["invoice_id"] = entity_value
                elif entity_type == "invoice_date" and invoice_data["invoice_date"] is None:
                    invoice_data["invoice_date"] = entity_value
                elif entity_type == "supplier_name" and invoice_data["supplier_name"] is None:
                    invoice_data["supplier_name"] = entity_value
            
            # Count successful extractions
            found_count = sum(1 for value in [invoice_data["total_cost"], invoice_data["invoice_id"], 
                                            invoice_data["invoice_date"], invoice_data["supplier_name"]] if value is not None)
            
            print(f"🎯 Successfully extracted {found_count}/4 key pieces of information")
            
            return invoice_data
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "total_cost": None,
                "invoice_id": None,
                "invoice_date": None,
                "supplier_name": None,
                "extraction_status": "error",
                "error_message": str(e)
            }
    
    def process_invoice(self, file_path):
        """Process invoice and extract key information."""
        print(f"🔍 Processing invoice: {os.path.basename(file_path)}")
        print(f"📄 File type: {os.path.splitext(file_path)[1]}")
        print("🎯 Extracting: Total Cost, Invoice ID, Invoice Date, Supplier Name")
        print("-" * 80)
        
        # Extract key information
        result = self.extract_key_invoice_data(file_path)
        
        return result
    
    def save_invoice_results(self, result, output_path="key_invoice_data.json"):
        """Save the extracted key invoice information to JSON."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            return output_path
        except Exception as e:
            print(f"Error saving JSON: {e}")
            return None
    
    def display_results(self, result):
        """Display the extracted key information in a clean format."""
        print(f"\n{'📋 ' + '='*50}")
        print("EXTRACTED INVOICE INFORMATION")
        print('='*52)
        
        if result.get("extraction_status") == "success":
            print(f"💰 Total Cost:     {result['total_cost'] or 'Not found'}")
            print(f"🔢 Invoice ID:     {result['invoice_id'] or 'Not found'}")
            print(f"📅 Invoice Date:   {result['invoice_date'] or 'Not found'}")
            print(f"🏢 Supplier Name:  {result['supplier_name'] or 'Not found'}")
            
            # Count successful extractions
            found_items = [k for k, v in result.items() if k not in ['extraction_status', 'error_message'] and v is not None]
            print(f"\n✅ Successfully extracted: {len(found_items)}/4 items")
            
            if len(found_items) < 4:
                missing_items = [k.replace('_', ' ').title() for k, v in result.items() 
                               if k not in ['extraction_status', 'error_message'] and v is None]
                print(f"❓ Could not find: {', '.join(missing_items)}")
                
        else:
            print("❌ Extraction failed")
            if result.get("error_message"):
                print(f"Error: {result['error_message']}")

# Usage
if __name__ == "__main__":
    extractor = InvoiceExtractor()
    
    file_path = "/Users/sonma/Desktop/Projects/blink_ai_project/blinkAI/backend/module_data_extraction/invoice_template.png"
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found!")
    else:
        try:
            print("🚀 EXTRACTING KEY INVOICE INFORMATION")
            print("="*50)
            print("Target Information:")
            print("• Total Cost")
            print("• Invoice ID") 
            print("• Invoice Date")
            print("• Supplier Name")
            print()
            
            # Process the invoice
            result = extractor.process_invoice(file_path)
            
            # Display results
            extractor.display_results(result)
            
            # Save results
            output_file = extractor.save_invoice_results(result)
            if output_file:
                print(f"\n💾 Results saved to: {output_file}")
                
        except Exception as e:
            print(f"❌ Error processing invoice: {e}")