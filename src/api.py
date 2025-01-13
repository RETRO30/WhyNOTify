from httpx import AsyncClient

class Proxy:
    ip: str
    port: int
    username: str
    password: str
    

class TelegramApi:
    def __init__(self):
        pass
    
    async def login(self):
        pass
    
    async def get_auth_data(self):
        pass
    
    
class StickersApi:
    def __init__(self, auth_data: str, proxy: str):   
        self.auth_data = auth_data
        self.proxy = proxy
        self.session = None
    
    async def session_setup(self) -> int:
        """Setup the session for the API client.

        If the session is not already set up, this method will create a new
        `httpx.AsyncClient` instance and assign it to `self.session`. The
        `proxy` parameter is passed to the `AsyncClient` constructor.

        Returns:
            int: 0 if the session was successfully set up, -1 otherwise.
        """
        if self.session is None:
            try:
                self.session = AsyncClient(proxy=self.proxy)
            except Exception as e:
                
        return 0
    
    def auth(self):        
        pass
    
    def get_collections(self):
        pass