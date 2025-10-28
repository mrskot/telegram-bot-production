import os
import logging
import uuid

class SupabaseService:
    def __init__(self):
        self.sessions = {}
        logging.info("✅ Temporary session service initialized")
    
    def create_session(self, chat_id: int, extracted_data: str = None):
        session_id = str(uuid.uuid4())[:8]
        session_data = {
            'id': session_id,
            'chat_id': chat_id,
            'extracted_data': extracted_data,
            'parsed_data': {
                'Участок': 'не указано',
                'Изделие': 'не указано',
                'Номер чертежа': 'не указано', 
                'Номер изделия': 'не указано'
            },
            'status': 'pending_verification'
        }
        self.sessions[session_id] = session_data
        logging.info(f"✅ Session created: {session_id}")
        return session_data
    
    def get_session(self, session_id: str):
        session = self.sessions.get(session_id)
        if session:
            logging.info(f"✅ Session retrieved: {session_id}")
        return session
    
    def update_session(self, session_id: str, updates: dict):
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            logging.info(f"✅ Session updated: {session_id}")
            return self.sessions[session_id]
        return None
    
    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
            logging.info(f"✅ Session deleted: {session_id}")
            return True
        return False
    
    def upload_file(self, file_content: bytes, file_path: str, bucket: str = 'documents'):
        # Временная заглушка - возвращаем фиктивный URL
        file_url = f"https://example.com/{file_path}"
        logging.info(f"✅ File uploaded (mock): {file_url}")
        return file_url
    
    def get_file_url(self, file_path: str, bucket: str = 'documents'):
        return f"https://example.com/{file_path}"

supabase_client = SupabaseService()
