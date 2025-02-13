from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from admin.states.channel_states import ChannelStates
from utils.logger import logger
from database.models import Channel, ChannelType
from admin.keyboards.inline import generate_channel_buttons, generate_channels_buttons, generate_back_button

router = Router()

@router.callback_query(lambda c: c.data.startswith("channels"))
async def handle_channels(callback: CallbackQuery):
    await callback.message.edit_text("Channels:", reply_markup=await generate_channels_buttons())

@router.callback_query(lambda c: c.data.startswith("channel:"))
async def handle_channel_selection(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    channel = await Channel.get_by_id(channel_id)
    await callback.message.edit_text(
        f"Channel: {channel.name}\nID: {channel.channel_id}",
        reply_markup=await generate_channel_buttons(channel)
    )
    
@router.callback_query(lambda c: c.data.startswith("delete_channel:"))
async def handle_delete_channel(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    await Channel.delete_by_id(channel_id)
    await callback.message.edit_text("Channel deleted", reply_markup=await generate_back_button("channels:1"))


@router.callback_query(lambda c: c.data == "add_channels")
async def handle_add_channel(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Add channels'"""
    await callback.message.answer("Send text with channels in format:\n`name:channel_id:channel_type`\n\nAvailable types: " + ", ".join([c.value for c in ChannelType]), parse_mode="Markdown")
    await state.set_state(ChannelStates.waiting_for_channels_data)

@router.message(ChannelStates.waiting_for_channels_data)
async def handle_channels_input(message: Message, state: FSMContext):
    """Обработчик получения списка каналов"""
    count = 0
    try:
        channels_data = message.text.strip()
        channels = channels_data.split("\n")

        for channel in channels:
            try:
                name, channel_id, channel_type = channel.split(":")
                await Channel.add(name, channel_id, ChannelType(channel_type))
                count += 1
                logger.success(f"Channel ({name}) added")
            except Exception as e:
                logger.warning(f"Error processing channel: {str(e)}")

    except Exception as e:
        await message.answer(f"Error processing channels: {str(e)}")

    await message.answer(f"Added {count} channels")
    await message.answer("Channels:", reply_markup=await generate_channels_buttons())
    await state.clear()