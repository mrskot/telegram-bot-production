from http.server import BaseHTTPRequestHandler
import json
import logging
import os
import requests
from lib.telegram import TelegramService
from lib.ocr import OCRService
from lib.deepseek import DeepSeekService
from lib.bitrix import BitrixService

logging.basicConfig(level=logging.INFO)

# Инициализация сервисов
telegram = TelegramService()
ocr = OCRService()
deepseek = DeepSeekService()
bitrix = BitrixService()

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
            
            # Обрабатываем сообщение
            if 'message' in update:
                message = update['message']
                chat_id = message['chat']['id']
                
                # Обработка ТЕКСТА
                if 'text' in message:
                    text = message.get('text', '')
                    logging.info(f"💬 Text from {chat_id}: {text}")
                    
                    response_text = "🤖 Бот работает! Отправьте фото маршрутной карты 📸"
                    telegram.send_message(chat_id, response_text)
                
                # Обработка ФОТО
                elif 'photo' in message:
                    logging.info(f"📸 Photo from {chat_id}")
                    
                    # Уведомляем о начале обработки
                    telegram.send_message(chat_id, "🔄 Начинаю обработку фото...")
                    
                    # Скачиваем фото
                    photo = message['photo'][-1]  # Берем самое качественное
                    file_id = photo['file_id']
                    image_bytes = telegram.download_file(file_id)
                    
                    if image_bytes:
                        # Распознаем текст
                        telegram.send_message(chat_id, "🔍 Распознаю текст...")
                        ocr_text = ocr.process_image(image_bytes)
                        
                        if ocr_text:
                            # Анализируем через DeepSeek
                            telegram.send_message(chat_id, "🤖 Анализирую данные...")
                            parsed_data = deepseek.parse_route_card(ocr_text)
                            
                            if parsed_data:
                                # Создаем заявку в Битрикс
                                telegram.send_message(chat_id, "📝 Создаю заявку...")
                                bitrix_result = bitrix.create_task(parsed_data)
                                
                                if bitrix_result:
                                    telegram.send_message(
                                        chat_id, 
                                        f"✅ Заявка создана!\n"
                                        f"🏭 Участок: {parsed_data.get('участок', 'Н/Д')}\n"
                                        f"🔧 Изделие: {parsed_data.get('изделие', 'Н/Д')}"
                                    )
                                else:
                                    telegram.send_message(chat_id, "❌ Ошибка создания заявки")
                            else:
                                telegram.send_message(chat_id, "❌ Не удалось проанализировать данные")
                        else:
                            telegram.send_message(chat_id, "❌ Не удалось распознать текст на фото")
                    else:
                        telegram.send_message(chat_id, "❌ Ошибка загрузки фото")
            
            # Всегда отвечаем OK Telegram
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "ok", "message": "processed"}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            self.send_response(200)
            self.end_headers()
