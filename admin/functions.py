from io import BytesIO
from utils.logger import logger
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message
from typing import Tuple

from database.models import Account, AccountStatus, ChannelType, Proxy, Channel, Stickerpack

async def main_menu_text():
    count_accounts = await Account.get_total_count()
    text = f"Total accounts: {count_accounts}\n"
    for status in AccountStatus:
        count = await Account.get_count_by_status(status)
        text += f"{status.name}: {count}\n"
    
    count_channels = await Channel.get_total_count()
    text += f"\nTotal channels: {count_channels}\n"
    for channel_type in ChannelType:
        count = await Channel.get_count_by_type(channel_type)
        text += f"{channel_type.name}: {count}\n"
    return text

    

async def process_add_accounts(message: Message, bot: Bot):
    
    count = 0
    try:
        # Проверяем, что отправлен файл
        if not message.document:
            await message.answer("Please send a text file")
            return

         # Скачиваем файл
        file = await bot.download(message.document)
        file_stream = BytesIO(file.read())
        file_stream.seek(0)

        # Читаем содержимое из потока
        content = file_stream.read().decode('utf-8')

        content = content.strip()
        account_rows = content.split('\n')
        
        for account_row in account_rows:
                phone_number, scheme, hostname, port, username, password = account_row.split(':')
                try:
                    new_account = await Account.add(phone_number)
                    new_proxy = await Proxy.add(scheme, hostname, int(port), username, password, new_account)
                    count += 1
                    logger.success(f"Account ({phone_number}) added")
                except Exception as e:
                    logger.warning(f"Error processing account: {str(e)}")
                
    except Exception as e:
        await message.answer(f"Error processing file: {str(e)}")
        
    return count
        
        
# Генерация кнопок для аккаунтов с пагинацией
async def generate_account_buttons(page: int = 1):
    ACCOUNTS_PER_PAGE = 5  # Количество аккаунтов на страницу
    accounts: Tuple[Account] = await Account.get_all()
    if accounts:
        accounts = list(accounts)
    else:
        accounts = []
    start_index = (page - 1) * ACCOUNTS_PER_PAGE
    end_index = start_index + ACCOUNTS_PER_PAGE
    page_accounts = accounts[start_index:end_index]

    # Клавиатура с аккаунтами
    keyboard = InlineKeyboardBuilder()
    for account in page_accounts:
        button_text = ""
        if account.status == AccountStatus.ACTIVE:
            button_text = f"🟢 {account.phone_number}"
        elif account.status == AccountStatus.PENDING:
            button_text = f"🟠 {account.phone_number}"
        else:
            button_text = f"🔴 {account}"
        keyboard.row(InlineKeyboardButton(text=button_text, callback_data=f"account:{account.id}"))

    # Добавляем кнопки пагинации
    if page > 1:
        keyboard.row(InlineKeyboardButton(text="⬅️", callback_data=f"accounts:{page - 1}"))
    if end_index < len(accounts):
        keyboard.row(InlineKeyboardButton(text="➡️", callback_data=f"accounts:{page + 1}"))
    # Добавляем кнопку "Add accounts"
    keyboard.row(InlineKeyboardButton(text="Add accounts", callback_data="add_accounts"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="admin_panel"))
    return keyboard.as_markup()


async def generate_channel_buttons(page: int = 1):
    CHANNELS_PER_PAGE = 5  # Количество каналов на страницу
    channels: Tuple[Channel] = await Channel.get_all()
    if channels:
        channels = list(channels)
    else:
        channels = []
        
    start_index = (page - 1) * CHANNELS_PER_PAGE
    end_index = start_index + CHANNELS_PER_PAGE
    page_channels = channels[start_index:end_index]

    # Клавиатура с каналами
    keyboard = InlineKeyboardBuilder()
    for channel in page_channels:
        keyboard.row(InlineKeyboardButton(text=channel.name, callback_data=f"channel:{channel.id}"))

    # Добавляем кнопки пагинации
    if page > 1:
        keyboard.row(InlineKeyboardButton(text="⬅️", callback_data=f"channels:{page - 1}"))
    if end_index < len(channels):
        keyboard.row(InlineKeyboardButton(text="➡️", callback_data=f"channels:{page + 1}"))
    # Добавляем кнопку "Add channels"
    keyboard.row(InlineKeyboardButton(text="Add channels", callback_data="add_channels"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="admin_panel"))
    return keyboard.as_markup()


async def generate_stickerpack_buttons(page: int = 1):
    STICKERPACKS_PER_PAGE = 5  # Количество стикерпаков на страницу
    stickerpacks: Tuple[Stickerpack] = await Stickerpack.get_all()
    if stickerpacks:
        stickerpacks = list(stickerpacks)
    else:
        stickerpacks = []
        
    start_index = (page - 1) * STICKERPACKS_PER_PAGE
    end_index = start_index + STICKERPACKS_PER_PAGE
    page_stickerpacks = stickerpacks[start_index:end_index]
    
    keyboard = InlineKeyboardBuilder()
    for stickerpack in page_stickerpacks:
        keyboard.row(InlineKeyboardButton(text=stickerpack.name, callback_data=f"stickerpack:{stickerpack.id}"))
        
    # Добавляем кнопки пагинации
    if page > 1:
        keyboard.row(InlineKeyboardButton(text="⬅️", callback_data=f"stickerpacks:{page - 1}"))
    if end_index < len(stickerpacks):
        keyboard.row(InlineKeyboardButton(text="➡️", callback_data=f"stickerpacks:{page + 1}"))
    # Добавляем кнопку "Add stickerpacks"
    keyboard.row(InlineKeyboardButton(text="Add stickerpacks", callback_data="add_stickerpacks"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="admin_panel"))
    return keyboard.as_markup()


async def stickerpack_keyboard(stickerpack: Stickerpack):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Delete", callback_data=f"delete_stickerpack:{stickerpack.id}"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="stickerpacks:1"))
    return keyboard.as_markup()


async def account_text(account: Account):
    proxy: Proxy = await Proxy.get_by_account(account)
    if proxy is None:
        return f"Account: {account.phone_number}\nStatus: {account.status}"
    return f"Account: {account.phone_number}\nStatus: {account.status}\nProxy: {proxy.scheme}://{proxy.username}:{proxy.password}@{proxy.hostname}:{proxy.port}"


async def account_keyboard(account: Account):
    keyboard = InlineKeyboardBuilder()
    if account.status == AccountStatus.PENDING:
        keyboard.row(InlineKeyboardButton(text="Activate", callback_data=f"activate_account:{account.id}"))
    keyboard.row(InlineKeyboardButton(text="Delete", callback_data=f"delete_account:{account.id}"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="accounts:1"))
    return keyboard.as_markup()

async def channel_keyboard(channel: Channel):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Delete", callback_data=f"delete_channel:{channel.id}"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="channels:1"))
    return keyboard.as_markup()

async def admin_panel_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Channels", callback_data="channels:1"))
    keyboard.row(InlineKeyboardButton(text="Accounts", callback_data="accounts:1"))
    keyboard.row(InlineKeyboardButton(text="Stickerpacks", callback_data="stickerpacks:1"))
    return keyboard.as_markup()


def prepare_proxy(proxy: Proxy) -> dict:
    return {
        "scheme": proxy.scheme,
        "hostname": proxy.hostname,
        "port": proxy.port,
        "username": proxy.username,
        "password": proxy.password
    }