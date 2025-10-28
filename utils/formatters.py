def format_data_for_display(data):
    return (
        f"<b>Распознанные данные:</b>\n\n"
        f"Участок: <b>{data['Участок']}</b>\n"
        f"Изделие: <b>{data['Изделие']}</b>\n"
        f"Номер чертежа: <b>{data['Номер чертежа']}</b>\n"
        f"Номер изделия: <b>{data['Номер изделия']}</b>"
    )

def format_data_for_edit(data):
    return (
        f"<b>Текущие данные:</b>\n\n"
        f"Участок: <b>{data['Участок']}</b>\n"
        f"Изделие: <b>{data['Изделие']}</b>\n"
        f"Номер чертежа: <b>{data['Номер чертежа']}</b>\n"
        f"Номер изделия: <b>{data['Номер изделия']}</b>\n\n"
        f"<i>Нажмите на поле которое хотите исправить:</i>"
    )

def parse_extracted_data(text):
    data = {
        'Участок': 'не указано',
        'Изделие': 'не указано', 
        'Номер чертежа': 'не указано',
        'Номер изделия': 'не указано'
    }
    
    try:
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Участок:'):
                data['Участок'] = line.replace('Участок:', '').strip()
            elif line.startswith('Изделие:'):
                data['Изделие'] = line.replace('Изделие:', '').strip()
            elif line.startswith('Номер чертежа:'):
                data['Номер чертежа'] = line.replace('Номер чертежа:', '').strip()
            elif line.startswith('Номер изделия:'):
                data['Номер изделия'] = line.replace('Номер изделия:', '').strip()
    except Exception as e:
        print(f"❌ Ошибка парсинга данных: {e}")
    
    return data
