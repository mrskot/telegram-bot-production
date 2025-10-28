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
ПРОАНАЛИЗИРУЙ этот текст технического документа и извлеки ТОЛЬКО ключевую информацию из ВЕРХНЕЙ ЧАСТИ документа (первые 30% текста).

ТЕКСТ:
{extracted_text[:3000]}

ИЗВЛЕКИ ТОЛЬКО:
1. Участок/цех (только ПЕРВЫЙ указанный участок, обычно в шапке)
2. Наименование изделия (общее название)
3. Номер чертежа (формат типа ТМГ.1000.2234 или ТМГ 2X2K2.250.01.00.00)
4. Номер изделия

ФОРМАТ ОТВЕТА (строго):
Участок: [первый участок из шапки]
Изделие: [наименование изделия]
Номер чертежа: [номер чертежа]
Номер изделия: [номер изделия]

Если что-то не найдено - пиши "не указано"
"""
