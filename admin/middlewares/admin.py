from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from utils.config import Config

class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, types.Message) or isinstance(event, types.CallbackQuery):
            user_id = event.from_user.id
            if str(user_id) not in Config.telegram_bot.admins:
                # Если пользователь не администратор, игнорируем обработку
                return
        # Если администратор, передаём событие дальше
        return await handler(event, data)
