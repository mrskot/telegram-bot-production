from http.server import BaseHTTPRequestHandler
import json
import logging
import os
import requests
import time
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

# Временное хранилище данных
temp_data_store = {}

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
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            update = json.loads(post_data)
            
            logging.info(f"📨 Received Telegram update")
            
            # Обработка сообщений
            if 'message' in update:
                self.handle_message(update['message'])
            
            # Обработка callback-ов (кнопок)
            elif 'callback_query' in update:
                self.handle_callback(update['callback_query'])
            
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
    
    def handle_message(self, message):
        """Обработка входящих сообщений"""
        chat_id = message['chat']['id']
        
        # Обработка ТЕКСТА
        if 'text' in message:
            text = message.get('text', '')
            logging.info(f"💬 Text from {chat_id}: {text}")
            
            if text.startswith('/'):
                self.handle_command(chat_id, text)
            else:
                # Проверяем, не ожидаем ли мы ввод для редактирования
                editing_key = f"editing_{chat_id}"
                if editing_key in temp_data_store:
                    self.handle_field_edit(chat_id, text, editing_key)
                else:
                    response_text = "🤖 Отправьте фото маршрутной карты для создания заявки 📸"
                    telegram.send_message(chat_id, response_text)
        
        # Обработка ФОТО
        elif 'photo' in message:
            self.handle_photo(chat_id, message)
    
    def handle_command(self, chat_id, text):
        """Обработка команд"""
        if text == '/start':
            welcome_text = (
                "🏭 Бот для создания заявок по маршрутным картам\n\n"
                "Отправьте фото маршрутной карты, и я:\n"
                "1. 📸 Распознаю текст с фото\n"
                "2. 🤖 Проанализирую данные\n" 
                "3. ✅ Предложу проверить информацию\n"
                "4. 📝 Создам заявку в Битрикс24"
            )
            telegram.send_message(chat_id, welcome_text)
    
    def handle_photo(self, chat_id, message):
        """Обработка фотографий маршрутных карт"""
        try:
            logging.info(f"📸 Photo from {chat_id}")
            
            # Уведомляем о начале обработки
            telegram.send_message(chat_id, "🔄 Начинаю обработку фото...")
            
            # Скачиваем фото
            photo = message['photo'][-1]
            file_id = photo['file_id']
            image_bytes = telegram.download_file(file_id)
            
            if not image_bytes:
                telegram.send_message(chat_id, "❌ Ошибка загрузки фото")
                return
            
            # Распознаем текст
            telegram.send_message(chat_id, "🔍 Распознаю текст...")
            ocr_text = ocr.extract_text_from_bytes(image_bytes)
            
            if not ocr_text:
                telegram.send_message(chat_id, "❌ Не удалось распознать текст на фото")
                return
            
            logging.info(f"📄 OCR text length: {len(ocr_text)}")
            
            # Анализируем через DeepSeek
            telegram.send_message(chat_id, "🤖 Анализирую данные...")
            analysis_result = deepseek.analyze_text(ocr_text)
            
            if not analysis_result:
                telegram.send_message(chat_id, "❌ Ошибка анализа данных")
                return
            
            # Парсим результат анализа
            parsed_data = self.parse_analysis_result(analysis_result)
            
            if not parsed_data:
                telegram.send_message(chat_id, "❌ Не удалось извлечь структурированные данные")
                return
            
            # Сохраняем данные для подтверждения
            session_id = f"{chat_id}_{int(time.time())}"
            temp_data_store[session_id] = {
                'parsed_data': parsed_data,
                'chat_id': chat_id,
                'timestamp': time.time()
            }
            
            # Показываем данные для подтверждения
            self.show_confirmation(chat_id, session_id, parsed_data)
            
        except Exception as e:
            logging.error(f"❌ Error processing photo: {e}")
            telegram.send_message(chat_id, "❌ Произошла ошибка при обработке")
    
    def handle_callback(self, callback):
        """Обработка нажатий на кнопки"""
        try:
            chat_id = callback['message']['chat']['id']
            data = callback['data']
            
            if data.startswith('confirm_'):
                session_id = data.replace('confirm_', '')
                self.create_bitrix_task(chat_id, session_id)
            
            elif data.startswith('edit_'):
                session_id = data.replace('edit_', '')
                self.start_editing(chat_id, session_id)
            
            elif data.startswith('field_'):
                parts = data.split('_')
                session_id = parts[1]
                field_name = parts[2]
                self.request_field_edit(chat_id, session_id, field_name)
            
            elif data.startswith('save_'):
                session_id = data.replace('save_', '')
                self.show_confirmation(chat_id, session_id)
                
        except Exception as e:
            logging.error(f"❌ Callback error: {e}")
            telegram.send_message(chat_id, "❌ Ошибка обработки запроса")
    
    def handle_field_edit(self, chat_id, new_value, editing_key):
        """Обработка ввода нового значения для поля"""
        try:
            editing_data = temp_data_store[editing_key]
            session_id = editing_data['session_id']
            field_name = editing_data['field_name']
            
            # Обновляем значение в данных
            if session_id in temp_data_store:
                temp_data_store[session_id]['parsed_data'][field_name] = new_value
            
            # Удаляем состояние редактирования
            del temp_data_store[editing_key]
            
            # Показываем обновленные данные
            self.show_confirmation(chat_id, session_id)
            
        except Exception as e:
            logging.error(f"❌ Field edit error: {e}")
            telegram.send_message(chat_id, "❌ Ошибка при редактировании")
    
    def show_confirmation(self, chat_id, session_id, parsed_data=None):
        """Показ данных для подтверждения"""
        if not parsed_data:
            data = temp_data_store.get(session_id)
            if not data:
                telegram.send_message(chat_id, "❌ Данные устарели")
                return
            parsed_data = data['parsed_data']
        
        confirmation_text = (
            f"📋 Проверьте распознанные данные:\n\n"
            f"🏭 Участок: {parsed_data.get('Участок', 'не указано')}\n"
            f"🔧 Изделие: {parsed_data.get('Изделие', 'не указано')}\n"
            f"📐 Номер чертежа: {parsed_data.get('Номер чертежа', 'не указано')}\n"
            f"🔢 Номер изделия: {parsed_data.get('Номер изделия', 'не указано')}"
        )
        
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Всё верно", "callback_data": f"confirm_{session_id}"},
                    {"text": "✏️ Исправить", "callback_data": f"edit_{session_id}"}
                ]
            ]
        }
        
        telegram.send_message(chat_id, confirmation_text, keyboard)
    
    def start_editing(self, chat_id, session_id):
        """Начало редактирования полей"""
        data = temp_data_store.get(session_id)
        if not data:
            telegram.send_message(chat_id, "❌ Данные устарели")
            return
        
        parsed_data = data['parsed_data']
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🏭 Участок", "callback_data": f"field_{session_id}_Участок"}],
                [{"text": "🔧 Изделие", "callback_data": f"field_{session_id}_Изделие"}],
                [{"text": "📐 Номер чертежа", "callback_data": f"field_{session_id}_Номер чертежа"}],
                [{"text": "🔢 Номер изделия", "callback_data": f"field_{session_id}_Номер изделия"}],
                [{"text": "✅ Завершить редактирование", "callback_data": f"save_{session_id}"}]
            ]
        }
        
        telegram.send_message(chat_id, "Выберите поле для редактирования:", keyboard)
    
    def request_field_edit(self, chat_id, session_id, field_name):
        """Запрос на редактирование конкретного поля"""
        telegram.send_message(
            chat_id, 
            f"Введите новое значение для поля '{field_name}':"
        )
        # Сохраняем состояние ожидания ввода
        temp_data_store[f"editing_{chat_id}"] = {
            'session_id': session_id,
            'field_name': field_name,
            'timestamp': time.time()
        }
    
    def create_bitrix_task(self, chat_id, session_id):
        """Создание заявки в Битрикс"""
        try:
            data = temp_data_store.get(session_id)
            if not data:
                telegram.send_message(chat_id, "❌ Данные устарели")
                return
            
            parsed_data = data['parsed_data']
            
            telegram.send_message(chat_id, "📝 Создаю заявку в Битрикс24...")
            
            bitrix_result = bitrix.send_data(
                parsed_data, 
                chat_id,
                username="telegram_user"
            )
            
            if bitrix_result:
                # Очищаем временные данные
                if session_id in temp_data_store:
                    del temp_data_store[session_id]
                
                success_text = (
                    f"✅ Заявка успешно создана!\n\n"
                    f"🏭 Участок: {parsed_data.get('Участок', 'Н/Д')}\n"
                    f"🔧 Изделие: {parsed_data.get('Изделие', 'Н/Д')}\n"
                    f"📐 Чертеж: {parsed_data.get('Номер чертежа', 'Н/Д')}\n"
                    f"🔢 Номер: {parsed_data.get('Номер изделия', 'Н/Д')}"
                )
                telegram.send_message(chat_id, success_text)
            else:
                telegram.send_message(chat_id, "❌ Ошибка создания заявки в Битрикс24")
                
        except Exception as e:
            logging.error(f"❌ Bitrix task creation error: {e}")
            telegram.send_message(chat_id, "❌ Ошибка при создании заявки")
    
    def parse_analysis_result(self, analysis_text):
        """Парсинг результата анализа DeepSeek"""
        try:
            parsed_data = {}
            lines = analysis_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Гибкое распознавание полей
                if line.startswith('Участок:'):
                    parsed_data['Участок'] = line.replace('Участок:', '').strip()
                elif line.startswith('Изделие:'):
                    parsed_data['Изделие'] = line.replace('Изделие:', '').strip()
                elif line.startswith('Номер чертежа:'):
                    parsed_data['Номер чертежа'] = line.replace('Номер чертежа:', '').strip()
                elif line.startswith('Номер изделия:'):
                    parsed_data['Номер изделия'] = line.replace('Номер изделия:', '').strip()
            
            # Валидация обязательных полей
            if not parsed_data.get('Участок') or not parsed_data.get('Изделие'):
                logging.warning("⚠️ Missing required fields")
                return None
            
            logging.info(f"📊 Parsed data: {parsed_data}")
            return parsed_data
            
        except Exception as e:
            logging.error(f"❌ Error parsing analysis result: {e}")
            return None
