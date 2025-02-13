from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.logger import logger
from database.models import Stickerpack
from admin.keyboards.inline import generate_back_button, generate_stickerpack_buttons, generate_stickerpacks_buttons
from admin.states.stickerpack_states import StickerPacksStates

router = Router()

@router.callback_query(lambda c: c.data.startswith("stickerpacks"))
async def handle_stickerpacks(callback: CallbackQuery):
    await callback.message.edit_text("Stickerpacks:", reply_markup=await generate_stickerpacks_buttons())

@router.callback_query(lambda c: c.data.startswith("stickerpack:"))
async def handle_stickerpack_selection(callback: CallbackQuery):
    stickerpack_id = int(callback.data.split(":")[1])
    stickerpack = await Stickerpack.get_by_id(stickerpack_id)
    await callback.message.edit_text(
        f"Stickerpack: {stickerpack.name}",
        reply_markup=await generate_stickerpack_buttons(stickerpack)
    )
    
@router.callback_query(lambda c: c.data.startswith("delete_stickerpack:"))
async def handle_delete_stickerpack(callback: CallbackQuery):
    stickerpack_id = int(callback.data.split(":")[1])
    await Stickerpack.delete_by_id(stickerpack_id)
    await callback.message.edit_text("Stickerpack deleted", reply_markup=await generate_back_button("stickerpacks:1"))
    
    
    
@router.callback_query(lambda c: c.data == "add_stickerpacks")
async def handle_add_stickerpack(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Add stickerpacks'"""
    await callback.message.answer("Send text with stickerpacks in format:\n`name:stickerpack_id`", parse_mode="Markdown")
    await state.set_state(StickerPacksStates.waiting_for_stickerpacks_data)

@router.message(StickerPacksStates.waiting_for_stickerpacks_data)
async def handle_stickerpacks_input(message: Message, state: FSMContext):
    """Обработчик получения списка стикерпаков"""
    count = 0
    try:
        stickerpacks_data = message.text.strip()
        stickerpacks = stickerpacks_data.split("\n")

        for stickerpack in stickerpacks:
            try:
                name, stickerpack_id = stickerpack.split(":")
                await Stickerpack.add(name, stickerpack_id)
                count += 1
                logger.success(f"Stickerpack ({name}) added")
            except Exception as e:
                logger.warning(f"Error processing stickerpack: {str(e)}")

    except Exception as e:
        await message.answer(f"Error processing stickerpacks: {str(e)}")

    await message.answer(f"Added {count} stickerpacks")
    await message.answer("Stickerpacks:", reply_markup=await generate_stickerpacks_buttons())
    await state.clear()
