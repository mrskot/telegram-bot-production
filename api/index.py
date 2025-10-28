from http.server import BaseHTTPRequestHandler
import json
import logging
import threading
import requests

logging.basicConfig(level=logging.INFO)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check"""
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy", 
                "service": "telegram-bot",
                "platform": "vercel"
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        self.send_response(404)
        self.end_headers()
    
    def do_POST(self):
        """Обработка Telegram webhook"""
        try:
            # Читаем данные запроса
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            update = json.loads(post_data)
            
            logging.info(f"📨 Received Telegram update")
            
            # Сразу отвечаем OK Telegram
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "ok", "message": "webhook processed"}
            self.wfile.write(json.dumps(response).encode())
            
            # Асинхронно обрабатываем сообщение
            self._handle_update_async(update)
            
        except Exception as e:
            logging.error(f"❌ Error in webhook: {e}")
            self.send_response(500)
            self.end_headers()
    
    def _handle_update_async(self, update):
        """Асинхронная обработка обновления"""
        def process_update():
            try:
                # Базовый ответ на любое сообщение
                if 'message' in update:
                    message = update['message']
                    chat_id = message['chat']['id']
                    text = message.get('text', '')
                    
                    logging.info(f"💬 Message from {chat_id}: {text}")
                    
                    # Ответ на текстовые сообщения
                    if text:
                        response_text = f"🤖 Получил: '{text}'\nОтправьте фото документа 📸"
                        success = self._send_telegram_message(chat_id, response_text)
                        if success:
                            logging.info(f"✅ Response sent successfully to {chat_id}")
                        else:
                            logging.error(f"❌ Failed to send response to {chat_id}")
                    
                    # Ответ на фото
                    elif 'photo' in message:
                        success = self._send_telegram_message(chat_id, "📸 Вижу фото! Обрабатываю...")
                        if success:
                            logging.info(f"✅ Photo response sent to {chat_id}")
                        
            except Exception as e:
                logging.error(f"❌ Error in async handler: {e}")
        
        thread = threading.Thread(target=process_update)
        thread.start()
    
    def _send_telegram_message(self, chat_id, text):
        """Отправка сообщения в Telegram"""
        try:
            # Прямой токен бота
            token = "8392042106:AAF9kqjIxgClFTilhenMe8NbSwI2GQqBJdA"
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            
            payload = {
                'chat_id': chat_id, 
                'text': text,
                'parse_mode': 'HTML'
            }
            
            logging.info(f"🔄 Sending message to Telegram API...")
            logging.info(f"🔗 URL: {url}")
            logging.info(f"📝 Payload: {payload}")
            
            response = requests.post(url, json=payload, timeout=10)
            
            logging.info(f"📨 Telegram API response: {response.status_code}")
            logging.info(f"📄 Response text: {response.text}")
            
            if response.status_code == 200:
                logging.info(f"✅ Message sent successfully to {chat_id}")
                return True
            else:
                logging.error(f"❌ Telegram API error: {response.status_code}")
                logging.error(f"❌ Error details: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Exception in send_message: {e}")
            return False
