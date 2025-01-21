import httpx
from database.models import Channel, ChannelType, Collection, CollectionType
from notifications.schemas import Description, Response, Status
from utils.config import Config
from utils.logger import logger

STICKER_TEXT = """Новая коллекция от <b>{title}</b> <a href="{cover_url}">👀</a> 

<b>Статус: {status}</b> 

👉 <a href="https://t.me/sticker_bot?start=_tgr_xR9FQYA4ZGEy">Зайти в приложение</a>

⭐️ <a href="https://split.tg/?ref=UQAy9M0k3azm-1dqajatwKLzrtAUIqmZFmIq-OpekOUEhoCY">Купить звезды</a>

Made by <a href="https://t.me/maxshitpostit">Max</a>"""


STICERPACK_TEXT = """Новый пак от <b>{name}</b> 

<b>Цена: {price}</b>
<b>Количество стикеров в паке: {count_stickers}</b> 
<b>Доступно: {left}/{supply}</b>

👉 <a href="https://t.me/sticker_bot?start=_tgr_xR9FQYA4ZGEy">Зайти в приложение</a>

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
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
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
    stickerpack_info = StickerPackInfo(data)
    response: Response = await stickerpack_info.parse()
    
    if response.status == Status.ERROR:
        return response

    text = STICERPACK_TEXT.format(name=stickerpack_info.name,
                                  price=stickerpack_info.price,
                                  count_stickers=stickerpack_info.count_stickers,
                                  supply=stickerpack_info.supply,
                                  left=stickerpack_info.left)
    return Response(Status.SUCCESS, Description.OK, data=text)

async def send_message_about_sticker(channel_id, collection):
    response: Response = await stickerpack_text(collection)
    if response.status == Status.ERROR:
        return response
    alert_text = "🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 "

    await send_message_to_telegram(chat_id=channel_id, text=alert_text)
    await send_message_to_telegram(chat_id=channel_id, text=response.data)
    await send_message_to_telegram(chat_id=channel_id, text=alert_text)
    
async def send_message_about_stickerpacks(channel_id, collection):
    response: Response = await stickerpack_text(collection)
    if response.status == Status.ERROR:
        return response
    alert_text = "🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 "

    await send_message_to_telegram(chat_id=channel_id, text=alert_text)
    await send_message_to_telegram(chat_id=channel_id, text=response.data)
    await send_message_to_telegram(chat_id=channel_id, text=alert_text)


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
        for coll in collection.new_json:
            for channel in channels:
                if channel.type == ChannelType.STICKERS:
                    await send_message_about_stickerpacks(channel_id=channel.channel_id, collection=coll)


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
            
async def send_tech_stickerpacks_message(collection: Collection):
    text = ""
    channels = await Channel.get_all()
    print(collection.current_json)
    for coll in collection.current_json:
        text += f"{coll['name']} - {coll['price']} - {coll['left']}/{coll['supply']}\n"
    for channel in channels:
        if channel.type == ChannelType.TECHNICAL:
            await send_message_to_telegram(chat_id=channel.channel_id, text=text)
