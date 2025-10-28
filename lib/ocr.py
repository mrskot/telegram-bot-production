import requests
import os
import logging
import time

class OCRService:
    def __init__(self):
        self.api_key = os.getenv('OCR_SPACE_API_KEY')
        self.max_retries = 3
        logging.info("✅ OCR service initialized")
    
    def extract_text_from_bytes(self, file_content: bytes) -> str:
        for attempt in range(self.max_retries):
            try:
                logging.info(f"🔄 OCR attempt {attempt + 1}")
                
                files = {'file': ('document.jpg', file_content, 'image/jpeg')}
                
                response = requests.post(
                    'https://api.ocr.space/parse/image',
                    files=files,
                    data={
                        'apikey': self.api_key,
                        'language': 'rus',
                        'isOverlayRequired': False,
                        'OCREngine': 2,
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if not result.get('IsErroredOnProcessing', True):
                        parsed_results = result.get('ParsedResults', [])
                        if parsed_results:
                            text = parsed_results[0].get('ParsedText', '')
                            logging.info("✅ OCR text extracted successfully")
                            return text.strip()
                
                error_msg = result.get('ErrorMessage', 'Unknown error')
                logging.warning(f"⚠️ OCR attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    
            except Exception as e:
                logging.error(f"❌ OCR error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                continue
        
        logging.error(f"❌ All {self.max_retries} OCR attempts failed")
        return None
