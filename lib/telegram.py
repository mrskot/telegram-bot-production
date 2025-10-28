import requests
import os
import logging

class TelegramService:
    def __init__(self):
        # ПРЯМАЯ ПОДСТАНОВКА токена (временно для тестирования)
        self.token = "8392042106:AAF9kqjIxgClFTilhenMe8NbSwI2GQqBJdA"
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        logging.info("✅ Telegram service initialized with DIRECT token")
    
    def download_file(self, file_id: str):
        try:
            file_info_url = f"{self.api_url}/getFile"
            response = requests.post(file_info_url, data={"file_id": file_id})
            file_info = response.json()
            
            if not file_info.get('ok'):
                logging.error(f"❌ File info error: {file_info}")
                return None
            
            file_path = file_info['result']['file_path']
            file_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            
            file_response = requests.get(file_url)
            if file_response.status_code == 200:
                logging.info(f"✅ File downloaded: {file_path}")
                return file_response.content
            return None
            
        except Exception as e:
            logging.error(f"❌ Error downloading file: {e}")
            return None

    def send_message(self, chat_id, text, reply_markup=None):
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': chat_id, 
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            if reply_markup:
                payload['reply_markup'] = reply_markup
                
            response = requests.post(url, json=payload, timeout=10)
            success = response.status_code == 200
            
            if success:
                logging.info(f"✅ Message sent to {chat_id}")
            else:
                logging.error(f"❌ Telegram API error: {response.text}")
            
            return success
            
        except Exception as e:
            logging.error(f"❌ Error sending message: {e}")
            return False

    # Остальные методы без изменений...
    def send_edit_view(self, chat_id, session_id, parsed_data):
        from utils.formatters import format_data_for_edit
        text = format_data_for_edit(parsed_data)
        keyboard = self.create_edit_buttons(session_id)
        return self.send_message(chat_id, text, keyboard)
    
    def create_verification_buttons(self, session_id):
        return {
            "inline_keyboard": [
                [
                    {"text": "✏️ Скорректировать", "callback_data": f"verify_edit_{session_id}"},
                    {"text": "✅ Всё верно", "callback_data": f"verify_ok_{session_id}"}
                ]
            ]
        }
    
    def create_edit_buttons(self, session_id):
        return {
            "inline_keyboard": [
                [
                    {"text": "🏭 Участок", "callback_data": f"edit_field_{session_id}_Участок"},
                    {"text": "🔧 Изделие", "callback_data": f"edit_field_{session_id}_Изделие"}
                ],
                [
                    {"text": "📐 Номер чертежа", "callback_data": f"edit_field_{session_id}_Номер чертежа"},
                    {"text": "🔢 Номер изделия", "callback_data": f"edit_field_{session_id}_Номер изделия"}
                ],
                [
                    {"text": "✅ Завершить", "callback_data": f"edit_done_{session_id}"}
                ]
            ]
        }
    
    def create_ok_button(self, session_id):
        return {
            "inline_keyboard": [
                [{"text": "✅ ОК", "callback_data": f"edit_ok_{session_id}"}]
            ]
        }
