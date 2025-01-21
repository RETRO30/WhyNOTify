from io import BytesIO
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message
from typing import Tuple

from admin.functions import *
from utils.config import Config
from admin.middlewares import AdminMiddleware
from database.models import Account, AccountStatus, ChannelType, Proxy, Channel
from database.database import get_session, init_db
from sqlalchemy.future import select
from pyrogram import Client as TelegramClient, errors as TelegramErrors, types as TelegramTypes

from utils.logger import logger

# Инициализация бота и диспетчера
bot = Bot(token=Config.telegram_bot.admin_token)
dp = Dispatcher()

dp.message.middleware(AdminMiddleware())
dp.callback_query.middleware(AdminMiddleware())


# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(await main_menu_text(), reply_markup=await admin_panel_keyboard())


@dp.callback_query(lambda c: c.data == "admin_panel")
async def handle_admin_panel(callback: CallbackQuery):
    await callback.message.edit_text(await main_menu_text(), reply_markup=await admin_panel_keyboard())


# Обработчик аккаунтов
@dp.callback_query(lambda c: c.data.startswith("accounts:"))
async def handle_pagination(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await callback.message.edit_text("Added accounts:", reply_markup=await generate_account_buttons(page=page))


class AddAccountsStates(StatesGroup):
    waiting_for_accounts_data = State()


# Обработчик кнопки "Add accounts"
@dp.callback_query(lambda c: c.data == "add_accounts")
async def handle_add_accounts(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Send file with accounts in format: phone_number:proxy_scheme:hostname:port:username:password")
    await state.set_state(AddAccountsStates.waiting_for_accounts_data)


# Обработчик для получения файла
@dp.message(AddAccountsStates.waiting_for_accounts_data)
async def handle_file(message: Message, state: FSMContext):
    result: int = await process_add_accounts(message, bot)

    await message.answer(f"Added {result} accounts")

    await message.answer("Added accounts:", reply_markup=await generate_account_buttons())
    await state.clear()


# Обработчик выбора аккаунта
@dp.callback_query(lambda c: c.data.startswith("account:"))
async def handle_account_selection(callback: CallbackQuery):
    account_id = int(callback.data.split(":")[1])

    account: Account = await Account.get_by_id(account_id)
    await callback.message.edit_text(await account_text(account), reply_markup=await account_keyboard(account))


@dp.callback_query(lambda c: c.data.startswith("delete_account:"))
async def handle_delete_account(callback: CallbackQuery):
    account_id = int(callback.data.split(":")[1])
    await Account.delete_by_id(account_id)
    await callback.answer("Account deleted", show_alert=True)


class LoginStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_password = State()


@dp.callback_query(lambda c: c.data.startswith("activate_account:"))
async def handle_activate_account(callback: CallbackQuery, state: FSMContext):
    account_id = int(callback.data.split(":")[1])
    await state.update_data(account_id=account_id)

    account: Account = await Account.get_by_id(account_id)
    proxy: Proxy = await Proxy.get_by_account(account)
    await state.update_data(account=account)

    client: TelegramClient = TelegramClient(f"session_{account_id}",
                                            Config.telegram_api.id,
                                            Config.telegram_api.hash,
                                            proxy=prepare_proxy(proxy),
                                            in_memory=True)

    await client.connect()
    result: TelegramTypes.SentCode = await client.send_code(phone_number=account.phone_number)
    await callback.message.answer("Input code")
    await state.update_data(client=client, hash=result.phone_code_hash)
    await state.set_state(LoginStates.waiting_for_code)


@dp.message(LoginStates.waiting_for_code)
async def handle_code_input(message: Message, state: FSMContext):
    code = message.text.strip()
    data = await state.get_data()
    account: Account = data.get("account")
    client: TelegramClient = data.get("client")
    hash: str = data.get("hash")

    try:
        await client.sign_in(phone_number=account.phone_number, phone_code=code, phone_code_hash=hash)
        await message.answer("Activated!")
        await message.answer("Added accounts:", reply_markup=await generate_account_buttons())
        session_string = await client.export_session_string()
        await Account.update_session(account.id, session_string)
        await client.disconnect()
        await state.clear()
    except TelegramErrors.SessionPasswordNeeded:
        await message.answer("Input 2fa")
        await state.set_state(LoginStates.waiting_for_password)
    except TelegramErrors.CodeInvalid:
        await message.answer("Invalid Code. Try Again.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
        await client.disconnect()
        await state.clear()


@dp.message(LoginStates.waiting_for_password)
async def handle_password_input(message: Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    account: Account = data.get("account")
    client: TelegramClient = data.get("client")

    try:
        await client.check_password(password=password)
        await message.answer("Activated!")
        await message.answer("Added accounts:", reply_markup=await generate_account_buttons())
        session_string = await client.export_session_string()
        await Account.update_session(account.id, session_string)
        await client.disconnect()
        await state.clear()
    except TelegramErrors.CodeInvalid:
        await message.answer("Invalid Code. Try Again.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
        await client.disconnect()
        await state.clear()


@dp.callback_query(lambda c: c.data.startswith("channels:"))
async def handle_channels(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await callback.message.edit_text("Channels:", reply_markup=await generate_channel_buttons(page=page))


@dp.callback_query(lambda c: c.data.startswith("channel:"))
async def handle_channel_selection(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    channel: Channel = await Channel.get_by_id(channel_id)
    await callback.message.edit_text(f"Channel: {channel.name}\nId: {channel.channel_id}\nType: {channel.type.value}",
                                     reply_markup=await channel_keyboard(channel))


@dp.callback_query(lambda c: c.data.startswith("delete_channel:"))
async def handle_delete_channel(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    await Channel.delete_by_id(channel_id)
    await callback.answer("Channel deleted", show_alert=True)


class ChannelStates(StatesGroup):
    waiting_for_channels_data = State()


@dp.callback_query(lambda c: c.data.startswith("add_channels"))
async def handle_add_channel(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        f"Send text with channels in format: name:channel_id:channel_type (channel types: {', '.join([c.value for c in ChannelType])})")
    await state.set_state(ChannelStates.waiting_for_channels_data)


@dp.message(ChannelStates.waiting_for_channels_data)
async def handle_channels_input(message: Message, state: FSMContext):
    channels_data = message.text.strip()
    channels = channels_data.split("\n")
    count = 0
    try:
        for channel in channels:
            name, channel_id, channel_type = channel.split(":")
            try:
                await Channel.add(name, channel_id, ChannelType(channel_type))
                count += 1
            except Exception as e:
                logger.warning(f"Error processing channel: {str(e)}")
    except Exception as e:
        await message.answer(f"Error processing channels: {str(e)}")

    await message.answer(f"Added {count} channels")
    await message.answer("Added channels:", reply_markup=await generate_channel_buttons())
    await state.clear()


@dp.callback_query(lambda c: c.data.startswith("stickerpacks:"))
async def handle_stickerpacks(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await callback.message.edit_text("Stickerpacks:", reply_markup=await generate_stickerpack_buttons(page=page))
    

@dp.callback_query(lambda c: c.data.startswith("stickerpack:"))
async def handle_stickerpack_selection(callback: CallbackQuery):
    stickerpack_id = int(callback.data.split(":")[1])
    stickerpack: Stickerpack = await Stickerpack.get_by_id(stickerpack_id)
    await callback.message.edit_text(f"Stickerpack: {stickerpack.name}\nId: {stickerpack.stickerpack_id}", reply_markup=await stickerpack_keyboard(stickerpack))
    
@dp.callback_query(lambda c: c.data.startswith("delete_stickerpack:"))
async def handle_delete_stickerpack(callback: CallbackQuery):
    stickerpack_id = int(callback.data.split(":")[1])
    await Stickerpack.delete_by_id(stickerpack_id)
    await callback.answer("Stickerpack deleted", show_alert=True)
    
class AddStickerpacksStates(StatesGroup):
    waiting_for_stickerpacks_data = State()
    
@dp.callback_query(lambda c: c.data.startswith("add_stickerpacks"))
async def handle_add_stickerpack(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Send text with stickerpacks in format: name:stickerpack_id")
    await state.set_state(AddStickerpacksStates.waiting_for_stickerpacks_data)
    
@dp.message(AddStickerpacksStates.waiting_for_stickerpacks_data)
async def handle_stickerpacks_input(message: Message, state: FSMContext):
    stickerpacks_data = message.text.strip()
    stickerpacks = stickerpacks_data.split("\n")
    count = 0
    try:
        for stickerpack in stickerpacks:
            name, stickerpack_id = stickerpack.split(":")
            try:
                await Stickerpack.add(name, stickerpack_id)
                count += 1
            except Exception as e:
                logger.warning(f"Error processing stickerpack: {str(e)}")
    except Exception as e:
        await message.answer(f"Error processing stickerpacks: {str(e)}")

async def main():
    try:

        # Инициализируем базу данных
        await init_db()
        logger.success("Database connected")

        logger.success("Bot started")
        # Запускаем бота
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        logger.info("Bot stopped.")


# Запуск бота
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
