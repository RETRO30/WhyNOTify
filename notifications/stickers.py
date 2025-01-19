from httpx import AsyncClient as HttpAsyncClient

from utils.logger import logger
from utils.config import Config
from database.models import Account, Proxy, Collections, CollectionType
from notifications.schemas import ParsedData, Response, Status, Description, AuthData
from telegram import TelegramApi

def get_proxy_string(proxy: Proxy) -> str:
    return f"{proxy.scheme}://{proxy.username}:{proxy.password}@{proxy.hostname}:{proxy.port}"

class StickersApi:
    def __init__(self, account: Account):
        self.account: Account = account
        self.http_session = None
        self.BASE_URL = "https://api.stickerdom.store/api/v1"
        self.headers =  {
            "accept": "application/json",
            "accept-language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
            "cache-control": "no-cache",
            "content-type": "text/plain;charset=UTF-8",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Microsoft Edge\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\", \"Microsoft Edge WebView2\";v=\"131\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site"
        }

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
                return Response(Status.ERROR, Description.ERROR_SETTING_UP_HTTP_SESSION)
        return Response(Status.SUCCESS, Description.OK)

    async def auth(self, auth_data: AuthData) -> Response:
        if self.http_session is None:
            logger.error(f"{self.account} HTTP session is not set up")
            return Response(Status.ERROR, Description.ERROR_SETTING_UP_HTTP_SESSION)
        url = f"{self.BASE_URL}/auth"
        body = auth_data.data
        headers = self.headers
        response = await self.http_session.post(url, data=body, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                if data["ok"]:
                    logger.success(f"{self.account} | Auth successful")
                    self.headers["authorization"] = f"Bearer {data['data']}"
                    return Response(Status.SUCCESS, Description.OK, data["data"])
                else:
                    return Response(Status.ERROR, Description.SESSION_EXPIRED)
            except Exception as e:
                logger.error(f"{self.account} | Error getting auth data: {e}")
                return Response(Status.ERROR, Description.INVALID_RESPONSE)
        else:
            logger.error(f"{self.account} | Error getting auth data: {response.status_code}, {response.text}")
            return Response(Status.ERROR, Description.INVALID_RESPONSE)
        
        

    async def get_collections(self):
        if self.http_session is None:
            logger.error(f"{self.account} HTTP session is not set up")
            return Response(Status.ERROR, Description.ERROR_SETTING_UP_HTTP_SESSION)
        url = f"{self.BASE_URL}/collections"
        headers = self.headers
        response = await self.http_session.get(url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                if data["ok"]:
                    return Response(Status.SUCCESS, Description.OK, data["data"])
                else:
                    return Response(Status.ERROR, Description.SESSION_EXPIRED)
            except Exception as e:
                logger.error(f"{self.account} | Error getting collections: {e}")
                return Response(Status.ERROR, Description.INVALID_RESPONSE)
        else:
            logger.error(f"{self.account} | Error getting collections: {response.status_code}, {response.text}")
            return Response(Status.ERROR, Description.INVALID_RESPONSE)
        
        
class Stickers:
    def __init__(self, account: Account):
        self.account: Account = account
        self.api = StickersApi(account)
        self.telegram_api = TelegramApi(account)
        self.bot_tag = "sticker_bot"
        self.webapp_url = "https://stickerdom.store/"
        self.auth_data: AuthData | None = None
        
    async def setup(self):
        response: Response = self.api.http_session_setup()
        if response.status == Status.ERROR:
            return response
        response: Response = await self.telegram_api.setup_client()
        if response.status == Status.ERROR:
            return response
        
        response: Response = await self.telegram_api.get_auth_data(bot_tag=self.bot_tag, url=self.webapp_url)
        if response.status == Status.ERROR:
            return response
        
        auth_data: AuthData = response.data
        if auth_data is None:
            return Response(Status.ERROR, Description.INVALID_RESPONSE)
        
        if not auth_data.valid():
            return Response(Status.ERROR, Description.SESSION_EXPIRED)
        
        auth_data: AuthData = response.data
        
        response: Response = await self.api.auth(auth_data=auth_data)
        if response.status == Status.ERROR:
            return response      
        
        
    async def check_updates(self, last_collection: Collections) -> Response:
        if self.auth_data is None:
            return Response(Status.ERROR, Description.SESSION_EXPIRED)
        if not self.auth_data.valid():
            return Response(Status.ERROR, Description.SESSION_EXPIRED)
        if last_collection.type != CollectionType.STICKERS:
            return Response(Status.ERROR, Description.INVALID_COLLECTION_TYPE)
        response: Response = await self.api.get_collections()
        if response.status == Status.ERROR:
            return response
        
        collections = response.data
        if collections is None:
            return Response(Status.ERROR, Description.INVALID_RESPONSE)
        
        new = []
        update = []
        
        current_ids = [collection["id"] for collection in collections]
        last_ids = [collection["id"] for collection in last_collection.current_json]
        
        if len(current_ids) > len(last_ids):
            new = [collection for collection in collections if collection["id"] not in last_ids]
        
        for last_collection in last_collection.current_json:
            for collection in collections:
                if last_collection["id"] == collection["id"]:
                    if last_collection["data"] != collection["data"]:
                        update.append(collection)
        
        return Response(Status.SUCCESS, Description.OK, data={"new": new, "update": update, "current": collections})
            
            
            
        
    
        