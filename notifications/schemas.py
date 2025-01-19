from datetime import datetime
import enum
from typing import Any


class AuthData:
    def __init__(self, data: str, exp: datetime):
        self.data = data
        self.exp = exp
        
    async def valid(self):
        return datetime.now() < self.exp
        
class Status(enum.Enum):
    SUCCESS = 0
    ERROR = 1
    
class Description(enum.Enum):
    OK = 0
    SESSION_EXPIRED = 1
    INVALID_RESPONSE = 2
    ERROR_SETTING_UP_HTTP_SESSION = 3
    ERROR_SETTING_UP_TELEGRAM_CLIENT = 4
    INVALID_COLLECTION_TYPE = 5
    
        
class Response:
    def __init__(self, status: Status, description: Description, data: Any = None):
        self.status = status
        self.description = description
        self.data = data