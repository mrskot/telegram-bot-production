from http.server import BaseHTTPRequestHandler
import json
import logging

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
            
            # Всегда отвечаем OK Telegram
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "ok", "message": "webhook processed"}
            self.wfile.write(json.dumps(response).encode())
            
            # Асинхронно обрабатываем сообщение
            self._handle_update_async(update)
            
        except Exception as e:
            logging.error(f"❌ Error: {e}")
            self.send_response(500)
            self.end_headers()
    
    def _handle_update_async(self, update):
        """Асинхронная обработка обновления"""
        import threading
        
        def process_update():
            try:
                # Импортируем здесь чтобы избежать циклических импортов
                from lib.telegram import TelegramService
                from lib.ocr import OCRService
                from lib.deepseek import DeepSeekService
                from lib.callback_handler import handle_callback_query
                from lib.supabase_client import supabase_client
                from utils.formatters import parse_extracted_data, format_data_for_display
                
                # Обработка callback от кнопок
                if 'callback_query' in update:
                    handle_callback_query(update['callback_query'])
                    return
                
                # Обработка сообщений
                if 'message' in update:
                    message = update['message']
                    chat_id = message['chat']['id']
                    
                    # Текстовые сообщения
                    if 'text' in message:
                        self._handle_text_message(chat_id, message['text'])
                        return
                    
                    # Фото документов
                    if 'photo' in message:
                        self._handle_photo_message(chat_id, message['photo'])
                        return
                        
            except Exception as e:
                logging.error(f"❌ Error in async handler: {e}")
        
        thread = threading.Thread(target=process_update)
        thread.start()
    
    def _handle_text_message(self, chat_id, text):
        """Обработка текстовых сообщений"""
        try:
            from lib.telegram import TelegramService
            from lib.supabase_client import supabase_client
            
            # Ищем активную сессию редактирования
            for session_id, session in supabase_client.sessions.items():
                if (session['chat_id'] == chat_id and 
                    session.get('status') == 'awaiting_edit'):
                    
                    field_to_edit = session.get('field_to_edit')
                    if field_to_edit:
                        # Обновляем данные
                        session['parsed_data'][field_to_edit] = text
                        session['status'] = 'editing'
                        session['field_to_edit'] = None
                        
                        # Показываем обновленные данные
                        telegram = TelegramService()
                        from utils.formatters import format_data_for_edit
                        telegram.send_edit_view(chat_id, session_id, session['parsed_data'])
                    return
                    
        except Exception as e:
            logging.error(f"❌ Error handling text: {e}")
    
    def _handle_photo_message(self, chat_id, photos):
        """Обработка фото"""
        try:
            from lib.telegram import TelegramService
            from lib.ocr import OCRService
            from lib.deepseek import DeepSeekService
            from lib.supabase_client import supabase_client
            from utils.formatters import parse_extracted_data, format_data_for_display
            
            telegram = TelegramService()
            ocr = OCRService()
            deepseek = DeepSeekService()
            
            telegram.send_message(chat_id, "📥 Загружаю фото...")
            
            # Создаем сессию
            session = supabase_client.create_session(chat_id)
            session_id = session['id']
            
            # Берем фото
            photo = photos[-2] if len(photos) >= 2 else photos[-1]
            file_id = photo['file_id']
            
            # Скачиваем файл
            telegram.send_message(chat_id, "🔍 Распознаю текст...")
            file_content = telegram.download_file(file_id)
            if not file_content:
                telegram.send_message(chat_id, "❌ Ошибка загрузки файла")
                return
            
            # OCR
            extracted_text = ocr.extract_text_from_bytes(file_content)
            if not extracted_text:
                telegram.send_message(chat_id, "❌ Не удалось распознать текст")
                return
            
            # AI анализ
            telegram.send_message(chat_id, "🤖 Анализирую документ...")
            analysis_result = deepseek.analyze_text(extracted_text)
            
            # Парсим результат
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
            
        except Exception as e:
            logging.error(f"❌ Error processing photo: {e}")
            from lib.telegram import TelegramService
            TelegramService().send_message(chat_id, "❌ Ошибка обработки фото")
