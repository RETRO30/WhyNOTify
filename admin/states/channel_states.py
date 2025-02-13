from aiogram.fsm.state import State, StatesGroup

class ChannelStates(StatesGroup):
    waiting_for_channels_data = State()
