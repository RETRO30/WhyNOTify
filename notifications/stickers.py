from httpx import AsyncClient as HttpAsyncClient

from notifications.bot import send_tech_messages
from utils.logger import logger
from utils.config import Config
from database.models import Account, Proxy, Collection, CollectionType
from notifications.schemas import Response, Status, Description, AuthData
from telegram import TelegramApi


def get_proxy_string(proxy: Proxy) -> str:
    return f"{proxy.scheme}://{proxy.username}:{proxy.password}@{proxy.hostname}:{proxy.port}"


class StickersApi:

    def __init__(self, account: Account):
        self.account: Account = account
        self.http_session = None
        self.BASE_URL = "https://api.stickerdom.store/api/v1"
        self.headers = {
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
                proxy = await Proxy.get_by_account(self.account)
                self.http_session = HttpAsyncClient(proxy=get_proxy_string(proxy))
                # self.http_session = HttpAsyncClient()
            except Exception as e:
                logger.error(f"{self.account} | Error setting up HTTP session: {e}")
                await send_tech_messages(f"{self.account} | Error setting up HTTP session: {e}")
                return Response(Status.ERROR, Description.ERROR_SETTING_UP_HTTP_SESSION, data=str(e))
        return Response(Status.SUCCESS, Description.OK)

    async def auth(self, auth_data: AuthData) -> Response:
        if self.http_session is None:
            logger.error(f"{self.account} HTTP session is not set up")
            await send_tech_messages(f"{self.account} | HTTP session is not set up")
            return Response(Status.ERROR, Description.ERROR_SETTING_UP_HTTP_SESSION, data=str(e))
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
                await send_tech_messages(f"{self.account} | Error getting auth data: {e}")
                return Response(Status.ERROR, Description.INVALID_RESPONSE)
        else:
            logger.error(f"{self.account} | Error getting auth data: {response.status_code}, {response.text}")
            await send_tech_messages(f"{self.account} | Error getting auth data: {response.status_code}, {response.text}")
            return Response(Status.ERROR, Description.INVALID_RESPONSE)

    async def get_collections(self):
        if self.http_session is None:
            logger.error(f"{self.account} HTTP session is not set up")
            await send_tech_messages(f"{self.account} | HTTP session is not set up")
            return Response(Status.ERROR, Description.ERROR_SETTING_UP_HTTP_SESSION)
        url = f"{self.BASE_URL}/collections"
        # url = "http://test_api:8000/api/v1/collections"
        headers = self.headers
        response = await self.http_session.get(url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                if data["ok"]:
                    logger.success(f"{self.account} | Collections received successfully {len(data['data'])}")
                    return Response(Status.SUCCESS, Description.OK, data["data"])
                elif not data["ok"] and data["errorCode"] == "invalid_auth_token":
                    return Response(Status.ERROR, Description.SESSION_EXPIRED)
                else:
                    logger.error(f"{self.account} | Error getting collections: {data}")
                    await send_tech_messages(f"{self.account} | Error getting collections: {data}")
                    return Response(Status.ERROR, Description.INVALID_RESPONSE, data=str(data))
            except Exception as e:
                logger.error(f"{self.account} | Error getting collections: {e}")
                await send_tech_messages(f"{self.account} | Error getting collections: {e}")
                return Response(Status.ERROR, Description.INVALID_RESPONSE, data=str(e))
        else:
            logger.error(f"{self.account} | Error getting collections: {response.status_code}, {response.text}")
            await send_tech_messages(f"{self.account} | Error getting collections: {response.status_code}, {response.text}")
            return Response(Status.ERROR, Description.INVALID_RESPONSE, data=str(response.text))
        
        
    async def get_stickerpacks(self, id: int):
        if self.http_session is None:
            logger.error(f"{self.account} HTTP session is not set up")
            await send_tech_messages(f"{self.account} | HTTP session is not set up")
            return Response(Status.ERROR, Description.ERROR_SETTING_UP_HTTP_SESSION)
        url = f"{self.BASE_URL}/collection/{id}"
        headers = self.headers
        response = await self.http_session.get(url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                if data["ok"]:
                    logger.success(f"{self.account} | Stickerpacks by {id} received successfully {len(data['data']["characters"])}")
                    return Response(Status.SUCCESS, Description.OK, data["data"]["characters"])
            except Exception as e:
                logger.error(f"{self.account} | Error getting stickerpacks: {e}")
                await send_tech_messages(f"{self.account} | Error getting stickerpacks: {e}")
                return Response(Status.ERROR, Description.INVALID_RESPONSE, data=str(e))
        else:
            logger.error(f"{self.account} | Error getting stickerpacks: {response.status_code}, {response.text}")
            await send_tech_messages(f"{self.account} | Error getting stickerpacks: {response.status_code}, {response.text}")
            return Response(Status.ERROR, Description.INVALID_RESPONSE, data=str(response.text))


class Stickers:

    def __init__(self, account: Account):
        self.account: Account = account
        self.api = StickersApi(account)
        self.telegram_api = TelegramApi(account)
        self.bot_tag = "sticker_bot"
        self.webapp_url = "https://stickerdom.store/"

    async def setup(self):
        response: Response = await self.api.http_session_setup()
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
            logger.error(f"{self.account} | Auth data is None")
            await send_tech_messages(f"{self.account} | Auth data is None")
            return Response(Status.ERROR, Description.INVALID_RESPONSE)

        if not await auth_data.valid():
            logger.error(f"{self.account} | Auth data is invalid")
            return Response(Status.ERROR, Description.SESSION_EXPIRED)

        auth_data: AuthData = response.data

        response: Response = await self.api.auth(auth_data=auth_data)
        if response.status == Status.ERROR:
            return response
        return Response(Status.SUCCESS, Description.OK)

    async def check_updates(self, last_collections: Collection | None) -> Response:
        new = []
        update = []

        response: Response = await self.api.get_collections()
        if response.status == Status.ERROR:
            return response

        collections = response.data
        if collections is None:
            await send_tech_messages(f"{self.account} | Collections is None")
            return Response(Status.ERROR, Description.INVALID_RESPONSE)

        if last_collections is None:
            db_collection = await Collection.add(new_json=new, update_json=update, current_json=collections, type=CollectionType.STICKERS)
            return Response(Status.SUCCESS, Description.OK, data=db_collection)

        if last_collections.type != CollectionType.STICKERS:
            return Response(Status.ERROR, Description.INVALID_COLLECTION_TYPE)

        current_ids = [collection["id"] for collection in collections]
        last_ids = [collection["id"] for collection in last_collections.current_json]

        if len(current_ids) > len(last_ids):
            new = [collection for collection in collections if collection["id"] not in last_ids]

        for last_collection in last_collections.current_json:
            for collection in collections:
                if last_collection["id"] == collection["id"]:
                    if last_collection != collection:
                        update.append(collection)
                        

        db_collection = await Collection.add(new_json=new, update_json=update, current_json=collections, type=CollectionType.STICKERS)

        return Response(Status.SUCCESS, Description.OK, data=db_collection)
    
    async def check_update_stickerpacks(self, id: int, last_collections: Collection | None) -> Response:
        new = []
        update = []
        
        response: Response = await self.api.get_stickerpacks(id=id)
        if response.status == Status.ERROR:
            return response
        if last_collections is None:
            db_collection = await Collection.add(new_json=new, update_json=update, current_json=response.data, type=CollectionType.STICKERPACKS, additional_data=str(id))
            return Response(Status.SUCCESS, Description.OK, data=db_collection)
        stickerpacks = response.data
        if stickerpacks is None:
            await send_tech_messages(f"{self.account} | Stickerpacks is None")
            return Response(Status.ERROR, Description.INVALID_RESPONSE)
        
        if last_collections.type != CollectionType.STICKERPACKS:
            return Response(Status.ERROR, Description.INVALID_COLLECTION_TYPE)
        
        current_ids = [stickerpack["id"] for stickerpack in stickerpacks]
        last_ids = [stickerpack["id"] for stickerpack in last_collections.current_json]
        
        if len(current_ids) > len(last_ids):
            new = [stickerpack for stickerpack in stickerpacks if stickerpack["id"] not in last_ids]

        db_collection = await Collection.add(new_json=new, update_json=update, current_json=stickerpacks, type=CollectionType.STICKERPACKS, additional_data=str(id))
        return Response(Status.SUCCESS, Description.OK, data=db_collection)
