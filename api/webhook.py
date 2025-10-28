from http.server import BaseHTTPRequestHandler
import json
import os
import logging
import threading
from lib.telegram import TelegramService
from lib.ocr import OCRService
from lib.deepseek import DeepSeekService
from lib.callback_handler import handle_callback_query
from lib.supabase_client import supabase_client
from utils.formatters import parse_extracted_data, format_data_for_display

logging.basicConfig(level=logging.INFO)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check и главная страница"""
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy", 
                "service": "telegram-bot",
                "platform": "vercel",
                "version": "3.0.0"
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        self.send_response(404)
        self.end_headers()
    
    def do_POST(self):
        """Обработка всех POST запросов"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            update = json.loads(post_data)
            
            logging.info(f"📨 Received update from Telegram")
            
            # Обработка callback от кнопок
            if 'callback_query' in update:
                handle_callback_query(update['callback_query'])
                self._send_response(200, {"status": "callback_processed"})
                return
            
            # Обработка сообщений
            if 'message' in update:
                message = update['message']
                chat_id = message['chat']['id']
                
                # Текстовые сообщения (редактирование полей)
                if 'text' in message:
                    self._handle_text_message(chat_id, message['text'])
                    self._send_response(200, {"status": "text_processed"})
                    return
                
                # Фото документов
                if 'photo' in message:
                    self._handle_photo_async(chat_id, message['photo'])
                    self._send_response(200, {"status": "photo_processing"})
                    return
            
            self._send_response(200, {"status": "ok"})
            
        except Exception as e:
            logging.error(f"❌ Error in webhook: {e}")
            self._send_response(500, {"error": str(e)})
    
    def _send_response(self, code, data):
        """Утилита для отправки ответов"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _handle_text_message(self, chat_id, text):
        """Обработка текстовых сообщений для редактирования"""
        try:
            # Ищем активную сессию с ожиданием редактирования
            for session_id, session in supabase_client.sessions.items():
                if (session['chat_id'] == chat_id and 
                    session.get('status') == 'awaiting_edit'):
                    
                    field_to_edit = session.get('field_to_edit')
                    if field_to_edit:
                        # Обновляем данные в сессии
                        session['parsed_data'][field_to_edit] = text
                        session['status'] = 'editing'
                        session['field_to_edit'] = None
                        
                        # Показываем обновленные данные
                        telegram = TelegramService()
                        telegram.send_edit_view(chat_id, session_id, session['parsed_data'])
                    return
                    
        except Exception as e:
            logging.error(f"❌ Error handling text message: {e}")
    
    def _handle_photo_async(self, chat_id, photos):
        """Асинхронная обработка фото"""
        thread = threading.Thread(
            target=self._process_photo, 
            args=(chat_id, photos)
        )
        thread.start()
    
    def _process_photo(self, chat_id, photos):
        """Обработка фото документа"""
        try:
            telegram = TelegramService()
            ocr = OCRService()
            deepseek = DeepSeekService()
            
            telegram.send_message(chat_id, "📥 Загружаю фото...")
            
            # Создаем сессию
            session = supabase_client.create_session(chat_id)
            session_id = session['id']
            
            # Берем фото среднего качества
            photo = photos[-2] if len(photos) >= 2 else photos[-1]
            file_id = photo['file_id']
            
            # Скачиваем файл
            telegram.send_message(chat_id, "🔍 Распознаю текст...")
            file_content = telegram.download_file(file_id)
            if not file_content:
                telegram.send_message(chat_id, "❌ Ошибка загрузки файла")
                return
            
            # Извлекаем текст через OCR
            extracted_text = ocr.extract_text_from_bytes(file_content)
            if not extracted_text:
                telegram.send_message(
                    chat_id, 
                    "❌ Не удалось распознать текст. Попробуйте другое фото."
                )
                return
            
            # Анализируем через DeepSeek
            telegram.send_message(chat_id, "🤖 Анализирую документ...")
            analysis_result = deepseek.analyze_text(extracted_text)
            
            # Парсим и сохраняем результат
            parsed_data = parse_extracted_data(analysis_result)
            supabase_client.update_session(session_id, {
                'extracted_data': analysis_result,
                'parsed_data': parsed_data,
                'status': 'pending_verification'
            })
            
            # Показываем результаты
            formatted_data = format_data_for_display(parsed_data)
            telegram.send_message(
                chat_id,
                f"{formatted_data}\n\n<b>Проверьте данные:</b>",
                telegram.create_verification_buttons(session_id)
            )
            
            logging.info(f"✅ Photo processed for chat {chat_id}")
            
        except Exception as e:
            logging.error(f"❌ Error processing photo: {e}")
            telegram = TelegramService()
            telegram.send_message(chat_id, "❌ Произошла ошибка при обработке фото")
