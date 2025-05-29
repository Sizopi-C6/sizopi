from django.contrib import messages
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class DatabaseNoticeMiddleware:
    """
    Middleware untuk menangkap database notices dari trigger PostgreSQL
    dan mengkonversinya menjadi Django messages
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        self.capture_and_convert_notices(request)
        
        return response

    def capture_and_convert_notices(self, request):
        try:
            if hasattr(connection, 'connection') and connection.connection:
                raw_conn = connection.connection
                
                if hasattr(raw_conn, 'notices') and raw_conn.notices:
                    while raw_conn.notices:
                        notice = raw_conn.notices.pop(0)
                        
                        if hasattr(notice, 'message'):
                            msg = notice.message.strip()
                        else:
                            msg = str(notice).strip()
                        
                        if 'NOTICE:' not in msg:
                            continue
                            
                        if 'NOTICE:' in msg:
                            msg = msg.split('NOTICE:', 1)[1].strip()
                        
                        if msg.startswith('SUKSES:'):
                            clean_msg = msg.replace('SUKSES:', '').strip()
                            messages.success(request, clean_msg, extra_tags='trigger-notice')
                            
                        elif msg.startswith('INFO:'):
                            clean_msg = msg.replace('INFO:', '').strip()
                            messages.info(request, clean_msg, extra_tags='trigger-notice')
                            
                        elif msg.startswith('WARNING:'):
                            clean_msg = msg.replace('WARNING:', '').strip()
                            messages.warning(request, clean_msg, extra_tags='trigger-notice')
                            
                        elif msg.startswith('ERROR:'):
                            clean_msg = msg.replace('ERROR:', '').strip()
                            messages.error(request, clean_msg, extra_tags='trigger-notice')
                        else:
                            messages.info(request, msg, extra_tags='trigger-notice')
                        
                        logger.info(f"Database notice captured: {msg}")
                        
        except Exception as e:
            logger.error(f"Error capturing database notices: {e}")