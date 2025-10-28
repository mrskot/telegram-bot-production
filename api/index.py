from http.server import BaseHTTPRequestHandler
import json
import logging
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
            
            # Обрабатываем сообщение СРАЗУ (без потоков)
            if 'message' in update:
                message = update['message']
                chat_id = message['chat']['id']
                text = message.get('text', '')
                
                logging.info(f"💬 Message from {chat_id}: {text}")
                
                # ПРОСТОЙ ОТВЕТ - без сложной логики
                response_text = "🤖 Бот работает! Отправьте фото 📸"
                
                # Отправляем сообщение
                token = "8392042106:AAF9kqjIxgClFTilhenMe8NbSwI2GQqBJdA"
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                
                payload = {
                    'chat_id': chat_id, 
                    'text': response_text
                }
                
                logging.info(f"🔄 Sending response...")
                
                response = requests.post(url, json=payload, timeout=10)
                logging.info(f"📨 Telegram API response: {response.status_code}")
                
                if response.status_code == 200:
                    logging.info("✅ Message sent successfully!")
                else:
                    logging.error(f"❌ Telegram error: {response.text}")
            
            # Всегда отвечаем OK Telegram
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "ok", "message": "processed"}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            self.send_response(500)
            self.end_headers()
