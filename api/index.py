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
                    
                    # Простой ответ - сразу отправляем
                    response_text = "🤖 Бот работает! Отправьте фото документа 📸"
                    
                    # Упрощенная отправка
                    token = "8392042106:AAF9kqjIxgClFTilhenMe8NbSwI2GQqBJdA"
                    url = f"https://api.telegram.org/bot{token}/sendMessage"
                    
                    payload = {
                        'chat_id': chat_id, 
                        'text': response_text
                    }
                    
                    logging.info(f"🔄 Sending to Telegram...")
                    
                    try:
                        response = requests.post(url, json=payload, timeout=5)
                        logging.info(f"📨 Telegram response: {response.status_code}")
                        
                        if response.status_code == 200:
                            logging.info(f"✅ Message sent to {chat_id}")
                        else:
                            logging.error(f"❌ Telegram error: {response.text}")
                    except requests.exceptions.Timeout:
                        logging.error("❌ Telegram API timeout")
                    except Exception as e:
                        logging.error(f"❌ Send error: {e}")
                        
            except Exception as e:
                logging.error(f"❌ Error in async handler: {e}")
        
        thread = threading.Thread(target=process_update)
        thread.daemon = True  # Делаем поток демоном
        thread.start()
