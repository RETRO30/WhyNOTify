from urllib.parse import unquote
from pyrogram import Client as TelegramClient
from pyrogram.raw.functions.messages import RequestWebView
from datetime import datetime, timedelta

from utils.logger import logger
from utils.config import Config
from database.models import Account, Proxy
from notifications.schemas import AuthData
from notifications.schemas import Response, Status, Description


def prepare_proxy(proxy: Proxy) -> dict:
    return {
        "scheme": proxy.scheme,
        "hostname": proxy.hostname,
        "port": proxy.port,
        "username": proxy.username,
        "password": proxy.password
    }


class TelegramApi:
    def __init__(self, account: Account):
        self.account: Account = account
        self.tg_client: TelegramClient | None = None

    async def setup_client(self) -> Response:
        if self.tg_client is None:
            try:
                self.tg_client = TelegramClient(session_string=self.account.session,
                                                api_id=Config.telegram_api.id,
                                                api_hash=Config.telegram_api.hash,
                                                proxy=prepare_proxy(self.account.proxy),
                                                in_memory=True)
                return Response(Status.SUCCESS, Description.OK)
            except Exception as e:
                logger.error(f"{self.account} | Error setting up Telegram client: {e}")
                return Response(Status.ERROR, Description.ERROR_SETTING_UP_TELEGRAM_CLIENT)

    async def get_auth_data(self, bot_tag: str, url: str) -> Response:
        if self.account.session is None:
            logger.error(f"{self.account} | Account not logged in")
            return -1
        try:
            self.tg_client.connect()

            web_view = await self.tg_client.invoke(
                RequestWebView(
                    peer=await self.tg_client.resolve_peer(bot_tag),
                    bot=await self.tg_client.resolve_peer(bot_tag),
                    platform="android",
                    from_bot_menu=False,
                    url=url,
                ))

            auth_url = web_view.url
            auth_data = AuthData(unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])), datetime.now() + timedelta(minutes=45))
            await self.client.disconnect()
            return Response(Status.SUCCESS, Description.OK, data=auth_data)
        except Exception as e:
            logger.error(f"{self.account} | Error getting auth data: {e}")
            return Response(Status.ERROR, Description.INVALID_RESPONSE, data=e)