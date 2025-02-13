from io import BytesIO
from aiogram import Bot, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.config import Config
from utils.logger import logger
from database.models import Account, Proxy
from admin.keyboards.inline import generate_account_buttons, generate_back_button, generate_accounts_buttons
from admin.states.account_states import AddAccountsStates, LoginStates
from pyrogram import Client as TelegramClient
from pyrogram import errors as TelegramErrors

router = Router()

@router.callback_query(lambda c: c.data.startswith("accounts"))
async def handle_accounts(callback: CallbackQuery):
    await callback.message.edit_text("Accounts:", reply_markup=await generate_accounts_buttons())

@router.callback_query(lambda c: c.data.startswith("account:"))
async def handle_account_selection(callback: CallbackQuery):
    account_id = int(callback.data.split(":")[1])
    account = await Account.get_by_id(account_id)
    await callback.message.edit_text(
        f"Account: {account.phone_number}",
        reply_markup=await generate_account_buttons(account)
    )
    
@router.callback_query(lambda c: c.data.startswith("delete_account:"))
async def handle_delete_channel(callback: CallbackQuery):
    account_id = int(callback.data.split(":")[1])
    await Account.delete_by_id(account_id)
    await callback.message.edit_text("Channel deleted", reply_markup=await generate_back_button("accounts:1"))

@router.callback_query(lambda c: c.data == "add_accounts")
async def handle_add_accounts(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Add accounts'"""
    await callback.message.answer("Send file with accounts in format:\n`phone_number:proxy_scheme:hostname:port:username:password`", parse_mode="Markdown")
    await state.set_state(AddAccountsStates.waiting_for_accounts_data)

@router.message(AddAccountsStates.waiting_for_accounts_data)
async def handle_file(message: Message, bot: Bot, state: FSMContext):
    """Обработчик получения файла с аккаунтами"""
    count = 0
    try:
        if not message.document:
            await message.answer("You must send a file.")
            await message.answer("Accounts:", reply_markup=await generate_accounts_buttons())
            await state.clear()
            return

        # Скачиваем файл
        file = await bot.download(message.document)
        file_stream = BytesIO(file.read())
        file_stream.seek(0)

        # Читаем содержимое
        content = file_stream.read().decode('utf-8').strip()
        account_rows = content.split("\n")

        for account_row in account_rows:
            try:
                phone_number, scheme, hostname, port, username, password = account_row.split(":")
                new_account = await Account.add(phone_number)
                new_proxy = await Proxy.add(scheme, hostname, int(port), username, password, new_account)
                count += 1
                logger.success(f"Account ({phone_number}) added")
            except Exception as e:
                logger.warning(f"Error processing account: {str(e)}")

    except Exception as e:
        await message.answer(f"Error processing file: {str(e)}")

    await message.answer(f"Added {count} accounts")
    await message.answer("Accounts:", reply_markup=await generate_accounts_buttons())
    await state.clear()
    
    
@router.callback_query(lambda c: c.data.startswith("activate_account:"))
async def handle_activate_account(callback: CallbackQuery, state: FSMContext):
    """Обработчик активации аккаунта"""
    account_id = int(callback.data.split(":")[1])
    await state.update_data(account_id=account_id)

    account = await Account.get_by_id(account_id)
    proxy = await Proxy.get_by_account(account)
    await state.update_data(account=account)

    client = TelegramClient(f"session_{account_id}",
                            Config.telegram_api.id,
                            Config.telegram_api.hash,
                            proxy={
                                "scheme": proxy.scheme,
                                "hostname": proxy.hostname,
                                "port": proxy.port,
                                "username": proxy.username,
                                "password": proxy.password
                            },
                            in_memory=True)

    await client.connect()
    result = await client.send_code(phone_number=account.phone_number)
    await callback.message.answer("Input code")
    await state.update_data(client=client, hash=result.phone_code_hash)
    await state.set_state(LoginStates.waiting_for_code)

@router.message(LoginStates.waiting_for_code)
async def handle_code_input(message: Message, state: FSMContext):
    """Обработчик ввода кода подтверждения"""
    code = message.text.strip()
    data = await state.get_data()
    account = data.get("account")
    client = data.get("client")
    hash = data.get("hash")

    try:
        await client.sign_in(phone_number=account.phone_number, phone_code=code, phone_code_hash=hash)
        await message.answer("Activated!")
        await message.answer("Accounts:", reply_markup=await generate_accounts_buttons())
        session_string = await client.export_session_string()
        await Account.update_session(account.id, session_string)
        await client.disconnect()
        await state.clear()
    except TelegramErrors.SessionPasswordNeeded:
        await message.answer("Input 2FA password")
        await state.set_state(LoginStates.waiting_for_password)
    except TelegramErrors.CodeInvalid:
        await message.answer("Invalid code. Try again.")
    except Exception as e:
        await message.answer(f"Error: {e}")
        await client.disconnect()
        await state.clear()

@router.message(LoginStates.waiting_for_password)
async def handle_password_input(message: Message, state: FSMContext):
    """Обработчик ввода пароля 2FA"""
    password = message.text.strip()
    data = await state.get_data()
    account = data.get("account")
    client = data.get("client")

    try:
        await client.check_password(password=password)
        await message.answer("Activated!")
        await message.answer("Accounts:", reply_markup=await generate_accounts_buttons())
        session_string = await client.export_session_string()
        await Account.update_session(account.id, session_string)
        await client.disconnect()
        await state.clear()
    except TelegramErrors.CodeInvalid:
        await message.answer("Invalid password. Try again.")
    except Exception as e:
        await message.answer(f"Error: {e}")
        await client.disconnect()
        await state.clear()