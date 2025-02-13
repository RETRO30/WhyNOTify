from aiogram.fsm.state import State, StatesGroup

class AddAccountsStates(StatesGroup):
    waiting_for_accounts_data = State()

class LoginStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_password = State()
