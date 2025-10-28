# api/index.py
from flask import Flask, request, jsonify
import json
import traceback
import sys

app = Flask(__name__)

# Импортируем твой сервис
try:
    from lib.telegram import TelegramService
    bot = TelegramService()
    print("✅ TelegramService успешно инициализирован!")
except Exception as e:
    print(f"❌ Ошибка импорта TelegramService: {e}")
    print(traceback.format_exc())
    bot = None

@app.route('/')
def home():
    return "✅ Бот работает! Отправь сообщение в Telegram."

@app.route('/webhook', methods=['POST'])
def webhook():
    print("🟡 Получен запрос на /webhook")
    
    if not bot:
        return "❌ Бот не инициализирован", 500
    
    try:
        update_data = request.get_json()
        print(f"📨 Данные вебхука: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
        
        result = bot.handle_webhook(update_data)
        return jsonify({"status": "success", "result": result})
        
    except Exception as e:
        print(f"🔴 Критическая ошибка в webhook: {e}")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/test')
def test():
    print("🟡 Тестовый запрос на /test")
    return "✅ Тест пройден! Сервер работает."

if __name__ == '__main__':
    print("🚀 Запускаем Flask приложение...")
    app.run(debug=True)
