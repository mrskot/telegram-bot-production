import logging
from lib.telegram import TelegramService
from lib.bitrix import BitrixService
from lib.supabase_client import supabase_client
from utils.formatters import format_data_for_edit

def handle_callback_query(callback_query):
    try:
        chat_id = callback_query['message']['chat']['id']
        callback_data = callback_query['data']
        username = callback_query['from'].get('username', 'unknown')
        
        logging.info(f"🔄 Handling callback: {callback_data}")
        
        if callback_data.startswith('verify_ok_'):
            session_id = callback_data.replace('verify_ok_', '')
            handle_verification_ok(chat_id, session_id, username)
            
        elif callback_data.startswith('verify_edit_'):
            session_id = callback_data.replace('verify_edit_', '')
            handle_verification_edit(chat_id, session_id)
            
        elif callback_data.startswith('edit_field_'):
            parts = callback_data.split('_')
            session_id = parts[2]
            field_name = '_'.join(parts[3:])
            handle_edit_field(chat_id, session_id, field_name)
            
        elif callback_data.startswith('edit_done_'):
            session_id = callback_data.replace('edit_done_', '')
            handle_edit_done(chat_id, session_id)
            
        elif callback_data.startswith('edit_ok_'):
            session_id = callback_data.replace('edit_ok_', '')
            handle_edit_ok(chat_id, session_id, username)
            
    except Exception as e:
        logging.error(f"❌ Error handling callback: {e}")

def handle_verification_ok(chat_id, session_id, username):
    session = supabase_client.get_session(session_id)
    if not session:
        TelegramService().send_message(chat_id, "❌ Сессия не найдена")
        return
    
    bitrix_service = BitrixService()
    item_id = bitrix_service.send_data(session['parsed_data'], chat_id, username)
    bitrix_id = bitrix_service.extract_bitrix_id(item_id)
    
    final_data = format_final_data(session['parsed_data'])
    telegram = TelegramService()
    
    if bitrix_id:
        message = f"✅ Супер! Данные переданы, ID заявки: {bitrix_id}\n\n{final_data}"
    else:
        message = f"⚠️ Данные обработаны, но возникла ошибка при отправке в Битрикс24\n\n{final_data}"
    
    telegram.send_message(chat_id, message)
    supabase_client.delete_session(session_id)

def handle_verification_edit(chat_id, session_id):
    session = supabase_client.get_session(session_id)
    if not session:
        TelegramService().send_message(chat_id, "❌ Сессия не найдена")
        return
    
    telegram = TelegramService()
    telegram.send_message(
        chat_id, 
        format_data_for_edit(session['parsed_data']), 
        telegram.create_edit_buttons(session_id)
    )
    supabase_client.update_session(session_id, {'status': 'editing'})

def handle_edit_field(chat_id, session_id, field_name):
    session = supabase_client.get_session(session_id)
    if not session:
        TelegramService().send_message(chat_id, "❌ Сессия не найдена")
        return
    
    supabase_client.update_session(session_id, {
        'field_to_edit': field_name,
        'status': 'awaiting_edit'
    })
    
    current_value = session['parsed_data'].get(field_name, 'не указано')
    telegram = TelegramService()
    telegram.send_message(
        chat_id, 
        f"✏️ Введите новое значение для <b>{field_name}</b>:\n\n"
        f"Текущее значение: <code>{current_value}</code>\n\n"
        f"Просто напишите новое значение сообщением:"
    )

def handle_edit_done(chat_id, session_id):
    session = supabase_client.get_session(session_id)
    if not session:
        TelegramService().send_message(chat_id, "❌ Сессия не найдена")
        return
    
    corrected_data = format_final_data(session['parsed_data'])
    telegram = TelegramService()
    telegram.send_message(
        chat_id, 
        f"✅ Редактирование завершено!\n\n{corrected_data}\n\nВсё верно?", 
        telegram.create_ok_button(session_id)
    )

def handle_edit_ok(chat_id, session_id, username):
    session = supabase_client.get_session(session_id)
    if not session:
        TelegramService().send_message(chat_id, "❌ Сессия не найдена")
        return
    
    bitrix_service = BitrixService()
    item_id = bitrix_service.send_data(session['parsed_data'], chat_id, username)
    bitrix_id = bitrix_service.extract_bitrix_id(item_id)
    
    final_data = format_final_data(session['parsed_data'])
    telegram = TelegramService()
    
    if bitrix_id:
        message = f"✅ Данные переданы, ID заявки: {bitrix_id}\n\n{final_data}"
    else:
        message = f"⚠️ Данные обработаны, но возникла ошибка при отправке в Битрикс24\n\n{final_data}"
    
    telegram.send_message(chat_id, message)
    supabase_client.delete_session(session_id)

def format_final_data(parsed_data):
    return (
        f"Участок: <b>{parsed_data['Участок']}</b>\n"
        f"Изделие: <b>{parsed_data['Изделие']}</b>\n"
        f"Номер чертежа: <b>{parsed_data['Номер чертежа']}</b>\n"
        f"Номер изделия: <b>{parsed_data['Номер изделия']}</b>"
    )
