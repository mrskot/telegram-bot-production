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
                "platform": "vercel",
                "bot_token_set": bool(os.getenv('BOT_TOKEN'))
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
                        ocr_text = ocr.extract_text_from_bytes(image_bytes)
                        
                        if ocr_text:
                            logging.info(f"📄 OCR text length: {len(ocr_text)}")
                            
                            # Анализируем через DeepSeek
                            telegram.send_message(chat_id, "🤖 Анализирую данные...")
                            analysis_result = deepseek.analyze_text(ocr_text)
                            
                            if analysis_result and "не указано" not in analysis_result:
                                # Парсим результат анализа в структурированные данные
                                parsed_data = self._parse_analysis_result(analysis_result)
                                
                                # Отправляем в Битрикс
                                telegram.send_message(chat_id, "📝 Создаю заявку...")
                                bitrix_result = bitrix.send_data(
                                    parsed_data, 
                                    chat_id,
                                    username=message.get('from', {}).get('username', 'unknown')
                                )
                                
                                if bitrix_result:
                                    telegram.send_message(
                                        chat_id, 
                                        f"✅ Заявка создана!\n"
                                        f"🏭 Участок: {parsed_data.get('Участок', 'Н/Д')}\n"
                                        f"🔧 Изделие: {parsed_data.get('Изделие', 'Н/Д')}\n"
                                        f"📐 Чертеж: {parsed_data.get('Номер чертежа', 'Н/Д')}\n"
                                        f"🔢 Изделие: {parsed_data.get('Номер изделия', 'Н/Д')}"
                                    )
                                else:
                                    telegram.send_message(chat_id, "❌ Ошибка создания заявки в Битрикс")
                            else:
                                telegram.send_message(chat_id, "❌ Не удалось проанализировать данные или данные неполные")
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
    
    def _parse_analysis_result(self, analysis_text: str) -> dict:
        """Парсит текстовый результат анализа в структурированные данные"""
        try:
            parsed_data = {}
            lines = analysis_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('Участок:'):
                    parsed_data['Участок'] = line.replace('Участок:', '').strip()
                elif line.startswith('Изделие:'):
                    parsed_data['Изделие'] = line.replace('Изделие:', '').strip()
                elif line.startswith('Номер чертежа:'):
                    parsed_data['Номер чертежа'] = line.replace('Номер чертежа:', '').strip()
                elif line.startswith('Номер изделия:'):
                    parsed_data['Номер изделия'] = line.replace('Номер изделия:', '').strip()
            
            logging.info(f"📊 Parsed data: {parsed_data}")
            return parsed_data
            
        except Exception as e:
            logging.error(f"❌ Error parsing analysis result: {e}")
            return {}
