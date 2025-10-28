import requests
import logging
import json
import os

class BitrixService:
    def __init__(self):
        self.webhook_url = os.getenv('BITRIX24_WEBHOOK_URL')
        self.entity_type_id = os.getenv('BITRIX24_ENTITY_TYPE_ID', '1086')
        logging.info("✅ Bitrix service initialized")
    
    def send_data(self, parsed_data: dict, chat_id: int, username: str = "unknown"):
        try:
            bitrix_data = {
                "entityTypeId": int(self.entity_type_id),
                "fields": {
                    "ufCrm28_1737543613": parsed_data.get('Номер чертежа', 'не указано'),
                    "ufCrm28_1753194216": parsed_data.get('Участок', 'не указано'),
                    "ufCrm28_1753194194": parsed_data.get('Изделие', 'не указано'),
                    "ufCrm28_1736772873": parsed_data.get('Номер изделия', 'не указано')
                }
            }
            
            logging.info(f"🔄 Sending to Bitrix24")
            
            response = requests.post(
                self.webhook_url,
                json=bitrix_data,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            logging.info(f"📨 Bitrix24 response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    logging.info("✅ Data sent to Bitrix24 successfully")
                    return result['result']
                else:
                    error = result.get('error', 'Unknown error')
                    logging.error(f"❌ Bitrix24 error: {error}")
                    return False
            else:
                logging.error(f"❌ HTTP error Bitrix24: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error sending to Bitrix24: {e}")
            return False
    
    def extract_bitrix_id(self, item_id):
        try:
            if isinstance(item_id, dict):
                if 'item' in item_id and 'id' in item_id['item']:
                    return item_id['item']['id']
                elif 'id' in item_id:
                    return item_id['id']
            elif isinstance(item_id, (int, str)):
                return str(item_id)
            
            logging.warning(f"⚠️ Непонятный формат ответа от Битрикс24: {item_id}")
            return None
            
        except Exception as e:
            logging.error(f"❌ Ошибка извлечения ID из ответа Битрикс24: {e}")
            return None
