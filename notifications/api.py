from urllib.parse import unquote
from httpx import AsyncClient as HttpAsyncClient
from pyrogram import Client as TelegramClient
from pyrogram.raw.functions.messages import RequestWebView
from datetime import datetime, timedelta

from utils.logger import logger
from utils.config import Config
from database.models import Account


class AuthData:
    data: str
    exp: datetime


async def parse_proxy(proxy: str) -> dict:
    return {
        "scheme": proxy.split('://')[0],
        "hostname": proxy.split('@')[1].split(':')[0],
        "port": int(proxy.split('@')[1].split(':')[1]),
        "username": proxy.split('@')[0].split(':')[0],
        "password": proxy.split('@')[0].split(':')[1],
    }


class StickersApi:
    def __init__(self, account: Account):
        self.account = account
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
                self.http_session = HttpAsyncClient(proxy=self.account.proxy)
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
