import os
import requests
import json

class TelegramService:
    def __init__(self):
        # ВРЕМЕННЫЙ ТОКЕН ДЛЯ ТЕСТА
        self.token = "8392042106:AAGy5UHlJ9NMLuV9fKtDRLAISFdkdpUown0"
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        
        print("=" * 50)
        print("🟢 TelegramService инициализирован")
        print(f"🔑 Токен: {self.token[:15]}...")
        print(f"🌐 API URL: {self.api_url}")
        print("=" * 50)

    def send_message(self, chat_id, text):
        """Отправка сообщения в Telegram с полной диагностикой"""
        print("=" * 50)
        print("🔍 ОТПРАВКА СООБЩЕНИЯ:")
        print(f"📱 Chat ID: {chat_id}")
        print(f"💬 Текст: {text}")
        print(f"🔑 Токен: {self.token[:15]}...")
        print(f"🌐 API URL: {self.api_url}")
        print("=" * 50)

        url = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text
        }

        try:
            print("🟡 Отправляю запрос к Telegram API...")
            response = requests.post(url, json=payload, timeout=10)
            
            print(f"✅ Ответ Telegram API:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code == 200:
                print("🟢 Сообщение успешно отправлено!")
                return response.json()
            else:
                print(f"🔴 Ошибка Telegram API: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except requests.exceptions.SSLError as e:
            print(f"🔴 SSL Ошибка: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"🔴 Ошибка подключения: {e}")
            return None
        except requests.exceptions.Timeout as e:
            print(f"🔴 Таймаут: {e}")
            return None
        except Exception as e:
            print(f"🔴 Неизвестная ошибка: {e}")
            return None

    def handle_webhook(self, update_data):
        """Обработка вебхука от Telegram"""
        print("=" * 50)
        print("📨 ПОЛУЧЕН ВЕБХУК ОТ TELEGRAM:")
        print(f"📊 Данные: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
        print("=" * 50)

        try:
            # Извлекаем данные из вебхука
            message = update_data.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            
            if chat_id and text:
                print(f"💬 Получено сообщение: '{text}' от chat_id: {chat_id}")
                
                # Отвечаем на сообщение
                response_text = f"Вы сказали: {text}"
                return self.send_message(chat_id, response_text)
            else:
                print("ℹ️ Нет текстового сообщения для обработки")
                return None
                
        except Exception as e:
            print(f"🔴 Ошибка обработки вебхука: {e}")
            return None

# Тестовый код для проверки
if __name__ == "__main__":
    print("🧪 ТЕСТИРУЕМ TelegramService...")
    bot = TelegramService()
    
    # Тест отправки сообщения (закомментируй в продакшене)
    # bot.send_message(123456789, "Тестовое сообщение от бота")
