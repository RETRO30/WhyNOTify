from datetime import datetime


class AuthData:
    def __init__(self, data: str, exp: datetime):
        self.data = data
        self.exp = exp