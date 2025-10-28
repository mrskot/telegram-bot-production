from flask import Flask, request, jsonify
import json
import traceback
import os
import sys
import requests

app = Flask(__name__)

# ДИАГНОСТИКА: Перед любым импортом
print("=" * 50)
print("🚀 api/index.py ЗАПУЩЕН!")
print("📋 Переменные окружения:")
for key in os.environ:
    if 'TELEGRAM' in key or 'BOT' in key:
        print(f"   {key}: {os.environ[key][:10]}...")
print("=" * 50)

try:
    # Пробуем импортировать твой сервис
    print("🟡 Пытаемся импортировать TelegramService...")
    from lib.telegram import TelegramService
    print("✅ TelegramService импортирован успешно!")
    
    # Инициализируем бота
    bot = TelegramService()
    print("✅ Бот инициализирован!")
    
except Exception as e:
    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    print("🔍 Traceback:")
    print(traceback.format_exc())
    bot = None

@app.route('/')
def home():
    print("🟡 Получен запрос на /")
    return "✅ Бот работает! Отправь сообщение в Telegram."

@app.route('/test')
def test():
    print("🟡 Получен запрос на /test")
    return jsonify({
        "status": "success", 
        "message": "✅ Сервер работает!",
        "bot_initialized": bot is not None
    })

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Установка вебхука для бота"""
    try:
        if not bot:
            return jsonify({"status": "error", "message": "Bot not initialized"}), 500
            
        webhook_url = f"https://{request.host}/webhook"
        print(f"🟡 Устанавливаем вебхук: {webhook_url}")
        
        # Используем твоего бота для установки вебхука
        set_webhook_url = f"https://api.telegram.org/bot{bot.token}/setWebhook"
        payload = {
            'url': webhook_url,
            'drop_pending_updates': True
        }
        
        print(f"🟡 Отправляем запрос к: {set_webhook_url}")
        response = requests.post(set_webhook_url, json=payload, timeout=10)
        result = response.json()
        
        print(f"✅ Результат установки вебхука: {result}")
        return jsonify({"status": "success", "result": result})
        
    except Exception as e:
        print(f"🔴 Ошибка установки вебхука: {e}")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_webhook', methods=['GET'])
def delete_webhook():
    """Удаление вебхука"""
    try:
        if not bot:
            return jsonify({"status": "error", "message": "Bot not initialized"}), 500
            
        delete_webhook_url = f"https://api.telegram.org/bot{bot.token}/deleteWebhook"
        print(f"🟡 Удаляем вебхук: {delete_webhook_url}")
        
        response = requests.post(delete_webhook_url, timeout=10)
        result = response.json()
        
        print(f"✅ Результат удаления вебхука: {result}")
        return jsonify({"status": "success", "result": result})
        
    except Exception as e:
        print(f"🔴 Ошибка удаления вебхука: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_webhook_info', methods=['GET'])
def get_webhook_info():
    """Получение информации о вебхуке"""
    try:
        if not bot:
            return jsonify({"status": "error", "message": "Bot not initialized"}), 500
            
        webhook_info_url = f"https://api.telegram.org/bot{bot.token}/getWebhookInfo"
        print(f"🟡 Получаем информацию о вебхуке: {webhook_info_url}")
        
        response = requests.post(webhook_info_url, timeout=10)
        result = response.json()
        
        print(f"✅ Информация о вебхуке: {result}")
        return jsonify({"status": "success", "result": result})
        
    except Exception as e:
        print(f"🔴 Ошибка получения информации о вебхуке: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    print("=" * 50)
    print("🟡 📨 ПОЛУЧЕН ЗАПРОС НА /webhook")
    print(f"🟡 Метод: {request.method}")
    print(f"🟡 Headers: {dict(request.headers)}")
    print("=" * 50)
    
    if request.method == 'GET':
        return "✅ Webhook endpoint is ready for POST requests"
    
    if not bot:
        print("🔴 Бот не инициализирован!")
        return jsonify({"status": "error", "message": "Bot not initialized"}), 500
    
    try:
        # Получаем данные
        if request.is_json:
            update_data = request.get_json()
        else:
            update_data = request.form.to_dict()
            
        print(f"📊 Данные запроса: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
        
        # Обрабатываем вебхук
        result = bot.handle_webhook(update_data)
        
        print(f"✅ Webhook обработан, результат: {result}")
        return jsonify({"status": "success", "result": result})
        
    except Exception as e:
        print(f"🔴 КРИТИЧЕСКАЯ ОШИБКА В WEBHOOK: {e}")
        print("🔍 Traceback:")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/debug')
def debug():
    print("🟡 Получен запрос на /debug")
    return jsonify({
        "status": "success",
        "python_version": sys.version,
        "bot_initialized": bot is not None,
        "environment_keys": [k for k in os.environ.keys() if 'TELEGRAM' in k or 'BOT' in k]
    })

@app.route('/send_test_message', methods=['GET'])
def send_test_message():
    """Тестовая отправка сообщения"""
    try:
        if not bot:
            return jsonify({"status": "error", "message": "Bot not initialized"}), 500
            
        # Нужно указать твой chat_id для теста
        test_chat_id = request.args.get('chat_id')
        if not test_chat_id:
            return jsonify({"status": "error", "message": "No chat_id provided"}), 400
            
        test_text = "✅ Тестовое сообщение от сервера!"
        print(f"🟡 Отправляем тестовое сообщение в chat_id: {test_chat_id}")
        
        result = bot.send_message(test_chat_id, test_text)
        
        print(f"✅ Результат отправки: {result}")
        return jsonify({"status": "success", "result": result})
        
    except Exception as e:
        print(f"🔴 Ошибка отправки тестового сообщения: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Обработчик ошибок
@app.errorhandler(404)
def not_found(error):
    print(f"🔴 404 ошибка: {error}")
    return "❌ Страница не найдена", 404

@app.errorhandler(500)
def internal_error(error):
    print(f"🔴 500 ошибка: {error}")
    return "❌ Внутренняя ошибка сервера", 500

if __name__ == '__main__':
    print("🎯 Запускаем Flask приложение...")
    app.run(debug=True)
