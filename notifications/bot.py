import asyncio
from typing import List
import httpx
from database.models import Channel, ChannelType, Collection, CollectionType
from notifications.schemas import Description, Response, Status
from utils.config import Config
from utils.logger import logger

STICKER_TEXT = """Новая коллекция от <b>{title}</b> <a href="{cover_url}">👀</a> 

<b>Статус: {status}</b> 

👉 <a href="https://t.me/sticker_bot">Зайти в приложение</a>

⭐️ <a href="https://split.tg/?ref=UQAy9M0k3azm-1dqajatwKLzrtAUIqmZFmIq-OpekOUEhoCY">Купить звезды</a>

Made by <a href="https://t.me/maxshitpostit">Max</a>"""

STICERPACK_TEXT_INFO = """Новый пак <b>{name}</b> от <b>{title}</b>
<b>Цена: {price}</b>
<b>Количество стикеров в паке: {count_stickers}</b> 
<b>Доступно: {left}/{supply}</b>\n\n"""

STICERPACK_TEXT = """{data}
👉 <a href="https://t.me/sticker_bot">Зайти в приложение</a>

⭐️ <a href="https://split.tg/?ref=UQAy9M0k3azm-1dqajatwKLzrtAUIqmZFmIq-OpekOUEhoCY">Купить звезды</a>

Made by <a href="https://t.me/maxshitpostit">Max</a>"""


class StickerInfo:

    def __init__(self, data: dict):
        self.data = data
        self.cover_url: str = None
        self.title: str = None
        self.status: str = None

    async def parse(self) -> Response:
        try:
            self.cover_url = [media["url"] for media in self.data["media"] if media["type"] == "cover"]
            self.title = self.data["title"]
            self.status = self.data["status"].capitalize()
            return Response(Status.SUCCESS, Description.OK)
        except Exception as e:
            await send_tech_messages(text=f"Error parsing sticker info: {e}")
            logger.error(f"Error parsing sticker info: {e}")
            return Response(Status.ERROR, Description.INVALID_RESPONSE, data=str(e))


class StickerPackInfo:

    def __init__(self, data: dict):
        self.data = data
        self.name: str = None
        self.price: str = None
        self.supply: str = None
        self.left: str = None
        self.count_stickers: str = None

    async def parse(self) -> Response:
        try:
            self.title = self.data["title"]
            self.name = self.data["name"]
            self.price = str(self.data["price"])
            self.supply = str(self.data["supply"])
            self.left = str(self.data["left"])
            self.count_stickers = str(len(self.data["stickers"]))
            return Response(Status.SUCCESS, Description.OK)
        except Exception as e:
            await send_tech_messages(text=f"Error parsing stickerpack info: {e}")
            logger.error(f"Error parsing stickerpack info: {e}")
            return Response(Status.ERROR, Description.INVALID_RESPONSE, data=str(e))


async def send_message_to_telegram(chat_id, text, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{Config.telegram_bot.notification_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    try:
        response = await httpx.AsyncClient().post(url, json=payload)
        if response.status_code != 200:
            logger.error(f"Failed to send message: {response.json()}")
    except Exception as e:
        logger.error(f"Error sending message: {e}")


async def sticker_text(data) -> Response:
    sticker_info = StickerInfo(data)
    response: Response = await sticker_info.parse()

    if response.status == Status.ERROR:
        return response

    text = STICKER_TEXT.format(title=sticker_info.title,
                               cover_url=sticker_info.cover_url[0] if sticker_info.cover_url else "",
                               status=sticker_info.status)
    return Response(Status.SUCCESS, Description.OK, data=text)


async def stickerpack_text(data) -> Response:
    stickers_text = ""
    for pack in data:
        stickerpack_info = StickerPackInfo(pack)
        response: Response = await stickerpack_info.parse()

        if response.status == Status.ERROR:
            return response
        
        stickers_text += STICERPACK_TEXT_INFO.format(name=stickerpack_info.name,
                                            title=stickerpack_info.title,
                                            price=stickerpack_info.price,
                                            count_stickers=stickerpack_info.count_stickers,
                                            left=stickerpack_info.left,
                                            supply=stickerpack_info.supply)
    

    text = STICERPACK_TEXT.format(data=stickers_text)
    return Response(Status.SUCCESS, Description.OK, data=text)


async def send_message_about_sticker(channel_id, collection):
    response: Response = await sticker_text(collection)
    if response.status == Status.ERROR:
        return response
    alert_text = "🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 "

    await send_message_to_telegram(chat_id=channel_id, text=alert_text)
    await send_message_to_telegram(chat_id=channel_id, text=response.data)
    await send_message_to_telegram(chat_id=channel_id, text=alert_text)


async def send_message_about_stickerpacks(channel_id, collection: list):
    response: Response = await stickerpack_text(collection)
    if response.status == Status.ERROR:
        return response
    alert_text = "🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 "

    await send_message_to_telegram(chat_id=channel_id, text=alert_text)
    await send_message_to_telegram(chat_id=channel_id, text=response.data)
    await send_message_to_telegram(chat_id=channel_id, text=alert_text)
    return Response(Status.SUCCESS, Description.OK)


async def send_messages(collection: Collection):
    channels = await Channel.get_all()
    if collection.type == CollectionType.STICKERS:
        for coll in collection.new_json:
            for channel in channels:
                if channel.type == ChannelType.STICKERS:
                    await send_message_about_sticker(channel_id=channel.channel_id, collection=coll)
        for coll in collection.update_json:
            for channel in channels:
                if channel.type == ChannelType.STICKERS:
                    await send_message_about_sticker(channel_id=channel.channel_id, collection=coll)
                    
    if collection.type == CollectionType.STICKERPACKS:
        if len(collection.new_json) == 0:
            return
        logger.debug(f"Send messages for stickerpacks: {len(collection.new_json)}")
        for channel in channels:
            if channel.type == ChannelType.STICKERS:
                response: Response = await send_message_about_stickerpacks(channel_id=channel.channel_id, collection=collection.new_json)
                if response.status == Status.ERROR:
                    logger.error(f"Error sending message: {response.data}")
            
                        
            


async def send_tech_messages(text: str):
    channels = await Channel.get_all()

    for channel in channels:
        if channel.type == ChannelType.TECHNICAL:
            await send_message_to_telegram(chat_id=channel.channel_id, text=text)


async def send_tech_collections_message(collection: Collection):
    text = ""
    channels = await Channel.get_all()
    for coll in collection.current_json:
        text += f"{coll['title']} - {coll['status']}\n"
    for channel in channels:
        if channel.type == ChannelType.TECHNICAL:
            await send_message_to_telegram(chat_id=channel.channel_id, text=text)


async def send_tech_stickerpacks_message(collections: List[Collection]):
    text = ""
    channels = await Channel.get_all()
    for collection in collections:
        for coll in collection.current_json:
            text += f"{coll['name']} - {coll['price']} - {coll['left']}/{coll['supply']}\n"
    for channel in channels:
        if channel.type == ChannelType.TECHNICAL:
            await send_message_to_telegram(chat_id=channel.channel_id, text=text)
