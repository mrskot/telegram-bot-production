# ... остальной код ...

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
        # Распознаем текст - ИСПРАВЛЕННЫЙ ВЫЗОВ
        telegram.send_message(chat_id, "🔍 Распознаю текст...")
        ocr_text = ocr.extract_text_from_bytes(image_bytes)  # ← ИСПРАВЛЕНО!
        
        if ocr_text:
            logging.info(f"📄 OCR text length: {len(ocr_text)}")
            
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

# ... остальной код ...
