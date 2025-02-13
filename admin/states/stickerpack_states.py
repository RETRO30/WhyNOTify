from aiogram.fsm.state import State, StatesGroup

class StickerPacksStates(StatesGroup):
    waiting_for_stickerpacks_data = State()
