from httpx import AsyncClient as HttpAsyncClient

from utils.logger import logger
from utils.config import Config
from database.models import Account, Proxy

def get_proxy_string(proxy: Proxy) -> str:
    return f"{proxy.scheme}://{proxy.username}:{proxy.password}@{proxy.hostname}:{proxy.port}"

class StickersApi:
    def __init__(self, account: Account):
        self.account: Account = account
        self.http_session = None

    async def http_session_setup(self) -> int:
        """Setup the session for the API client.

        If the session is not already set up, this method will create a new
        `httpx.AsyncClient` instance and assign it to `self.session`. The
        `proxy` parameter is passed to the `AsyncClient` constructor.

        Returns:
            int: 0 if the session was successfully set up, -1 otherwise.
        """
        if self.http_session is None:
            try:
                self.http_session = HttpAsyncClient(proxy=get_proxy_string(self.account.proxy))
            except Exception as e:
                logger.error(f"{self.account} | Error setting up HTTP session: {e}")
                return -1
        return 0

    def auth(self) -> int:
        if self.http_session is None:
            logger.error(f"{self.account} HTTP session is not set up")
            return -1
        if self.auth_data is None:
            return -1

        # TODO make request to auth

    def get_collections(self):
        pass