import requests
import os
import logging

class DeepSeekService:
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        logging.info("✅ DeepSeek service initialized")
    
    def analyze_text(self, extracted_text: str) -> str:
        try:
            if not extracted_text:
                return "Текст не распознан"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = self._build_prompt(extracted_text)
            
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.1
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                analysis = result['choices'][0]['message']['content']
                logging.info("✅ DeepSeek анализ завершен")
                return analysis
            else:
                logging.error(f"❌ Ошибка DeepSeek API: {response.status_code}")
                return f"Ошибка анализа: {response.status_code}"
                
        except Exception as e:
            logging.error(f"❌ Ошибка DeepSeek: {e}")
            return f"Ошибка: {str(e)}"
    
    def _build_prompt(self, extracted_text: str) -> str:
    return f"""
АНАЛИЗ МАРШРУТНОЙ КАРТЫ ПРОИЗВОДСТВЕННОГО ДОКУМЕНТА

ТЕКСТ ДЛЯ АНАЛИЗА:
{extracted_text[:3500]}

ИНСТРУКЦИЯ:
1. Проанализируй ШАПКУ документа (первые 30-40% текста)
2. Найди и извлеки ТОЛЬКО следующие данные:

ОБЯЗАТЕЛЬНЫЕ ПОЛЯ:
- Участок: название производственного участка или цеха
  (ищи: "участок", "цех", "производственный участок", "место изготовления")
  
- Изделие: общее наименование изделия или детали  
  (ищи: "наименование", "изделие", "деталь", "обозначение")

ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ:
- Номер чертежа: номер конструкторской документации
  (ищи: "чертеж", "№ черт.", "КД", "документация", форматы: ТМГ.XXXX.XXX, XXX.XX.XX.XX)
  
- Номер изделия: заводской или инвентарный номер
  (ищи: "№ изделия", "заводской номер", "инвентарный номер", "серийный номер")

ФОРМАТ ОТВЕТА (СТРОГО СОБЛЮДАЙ):
Участок: [найденное значение или "не указано"]
Изделие: [найденное значение или "не указано"]
Номер чертежа: [найденное значение или "не указано"]
Номер изделия: [найденное значение или "не указано"]

ВАЖНО:
- Извлекай данные только из верхней части документа
- Если поле не найдено - пиши "не указано"
- Не добавляй пояснения, только указанный формат
"""
