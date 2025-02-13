from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from utils.logger import logger
from admin.keyboards.inline import admin_panel_keyboard
from handlers import accounts, channels, stickerpacks
from texts import common

router = Router()

@router.message(Command("start"))
async def handle_admin_panel(message: Message):
    await message.answer(await common.main_menu_text(), reply_markup=await admin_panel_keyboard())

@router.callback_query(lambda c: c.data == "admin_panel")
async def handle_admin_panel_callback(callback: CallbackQuery):
    await callback.message.edit_text(await common.main_menu_text(), reply_markup=await admin_panel_keyboard())
