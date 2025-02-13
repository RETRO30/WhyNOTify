from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Account, AccountStatus, Channel, Stickerpack

async def generate_accounts_buttons(page: int = 1):
    ACCOUNTS_PER_PAGE = 5
    accounts = await Account.get_all()
    accounts = list(accounts) if accounts else []

    start_index = (page - 1) * ACCOUNTS_PER_PAGE
    end_index = start_index + ACCOUNTS_PER_PAGE
    page_accounts = accounts[start_index:end_index]

    keyboard = InlineKeyboardBuilder()
    for account in page_accounts:
        button_text = f"🟢 {account.phone_number}" if account.status == AccountStatus.ACTIVE else f"🔴 {account.phone_number}"
        keyboard.row(InlineKeyboardButton(text=button_text, callback_data=f"account:{account.id}"))

    if page > 1:
        keyboard.row(InlineKeyboardButton(text="⬅️", callback_data=f"accounts:{page - 1}"))
    if end_index < len(accounts):
        keyboard.row(InlineKeyboardButton(text="➡️", callback_data=f"accounts:{page + 1}"))

    keyboard.row(InlineKeyboardButton(text="Add accounts", callback_data="add_accounts"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="admin_panel"))
    return keyboard.as_markup()

async def generate_channels_buttons(page: int = 1):
    CHANNELS_PER_PAGE = 5
    channels = await Channel.get_all()
    channels = list(channels) if channels else []

    start_index = (page - 1) * CHANNELS_PER_PAGE
    end_index = start_index + CHANNELS_PER_PAGE
    page_channels = channels[start_index:end_index]

    keyboard = InlineKeyboardBuilder()
    for channel in page_channels:
        keyboard.row(InlineKeyboardButton(text=channel.name, callback_data=f"channel:{channel.id}"))

    if page > 1:
        keyboard.row(InlineKeyboardButton(text="⬅️", callback_data=f"channels:{page - 1}"))
    if end_index < len(channels):
        keyboard.row(InlineKeyboardButton(text="➡️", callback_data=f"channels:{page + 1}"))

    keyboard.row(InlineKeyboardButton(text="Add channels", callback_data="add_channels"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="admin_panel"))
    return keyboard.as_markup()

async def generate_stickerpacks_buttons(page: int = 1):
    STICKERPACKS_PER_PAGE = 5
    stickerpacks = await Stickerpack.get_all()
    stickerpacks = list(stickerpacks) if stickerpacks else []

    start_index = (page - 1) * STICKERPACKS_PER_PAGE
    end_index = start_index + STICKERPACKS_PER_PAGE
    page_stickerpacks = stickerpacks[start_index:end_index]

    keyboard = InlineKeyboardBuilder()
    for stickerpack in page_stickerpacks:
        keyboard.row(InlineKeyboardButton(text=stickerpack.name, callback_data=f"stickerpack:{stickerpack.id}"))

    if page > 1:
        keyboard.row(InlineKeyboardButton(text="⬅️", callback_data=f"stickerpacks:{page - 1}"))
    if end_index < len(stickerpacks):
        keyboard.row(InlineKeyboardButton(text="➡️", callback_data=f"stickerpacks:{page + 1}"))

    keyboard.row(InlineKeyboardButton(text="Add stickerpacks", callback_data="add_stickerpacks"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="admin_panel"))
    return keyboard.as_markup()

async def admin_panel_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Channels", callback_data="channels:1"))
    keyboard.row(InlineKeyboardButton(text="Accounts", callback_data="accounts:1"))
    keyboard.row(InlineKeyboardButton(text="Stickerpacks", callback_data="stickerpacks:1"))
    return keyboard.as_markup()

async def generate_stickerpack_buttons(stickerpack: Stickerpack):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Delete", callback_data=f"delete_stickerpack:{stickerpack.id}"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="stickerpacks:1"))
    return keyboard.as_markup()

async def generate_channel_buttons(channel: Channel):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Delete", callback_data=f"delete_channel:{channel.id}"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="channels:1"))
    return keyboard.as_markup()

async def generate_account_buttons(account: Account):
    keyboard = InlineKeyboardBuilder()
    if account.status != AccountStatus.ACTIVE:
        keyboard.row(InlineKeyboardButton(text="Activate", callback_data=f"activate_account:{account.id}"))
    keyboard.row(InlineKeyboardButton(text="Delete", callback_data=f"delete_account:{account.id}"))
    keyboard.row(InlineKeyboardButton(text="Back", callback_data="accounts:1"))
    return keyboard.as_markup()    
    
async def generate_back_button(to: str):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="Back", callback_data=to))
    return keyboard.as_markup()
