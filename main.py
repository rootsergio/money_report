import re
import datetime
import csv
from aiogram import executor, types
from aiogram.utils.helper import Helper, HelperMode, Item
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

import db
import settings
from bot import dp
from bot import send_message, send_document
from db import db_crud


GLOBAL_USER_TIMEOUT = {}


class States(Helper):
    mode = HelperMode.snake_case
    CONFIRMATION = Item()


@dp.message_handler(commands=['test'])
async def cmd_start(message: types.Message):
    await message.answer(f"Информация о пользователе{message.chat.values}")


@dp.message_handler(commands=['report'])
async def cmd_start(message: types.Message):
    if message.chat.id != settings.ADMIN_CHAT:
        await message.answer(f"Отчёт не доступен")
    else:
        description, rows = await db.db_select()
        if rows:
            # New empty list called 'result'. This will be written to a file.
            result = list()
            # The row name is the first entry for each entity in the description tuple.
            column_names = list()
            for i in description:
                column_names.append(i[0])
            result.append(column_names)
            for row in rows:
                result.append(row)
            # Write result to file.
            with open('report.csv', 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for row in result:
                    csvwriter.writerow(row)
        await send_document('report.csv', open('report.csv', 'rb'))


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Укажите перечисленную сумму числом")


@dp.message_handler(content_types=types.ContentType.TEXT)
async def get_amount_of_money(message: types.Message):
    amount = message.text
    user_profile = message.chat.values
    user_profile_str = f"user_id: {user_profile.get('id')}\n" \
                       f"first_name: {user_profile.get('first_name')}\n" \
                       f"last_name: {user_profile.get('last_name')}\n" \
                       f"username: @{user_profile.get('username')}\n"
    global GLOBAL_USER_TIMEOUT
    if GLOBAL_USER_TIMEOUT.get(user_profile.get('id')):
        delta = datetime.datetime.now() - GLOBAL_USER_TIMEOUT.get(user_profile.get('id'))
        if delta.seconds < settings.TIMEOUT_SECONDS:
            await message.answer(f'До отправки повторного сообщения установлен таймаут = '
                                 f'{settings.TIMEOUT_SECONDS - delta.seconds} секунд')
            return
    else:
        GLOBAL_USER_TIMEOUT[user_profile.get('id')] = datetime.datetime.now()

    if not re.match(r'^\d*([.|,]\d{1,2})?$', amount):
        await message.answer('Сумма указана неверно, возможные варианты написания суммы:\n1500\n1500.80\n1500,80')
    else:
        state = dp.current_state(user=settings.ADMIN_CHAT, chat=settings.ADMIN_CHAT)
        await state.update_data(**user_profile, amount=amount)
        await send_message(f"Пользователь:\n{user_profile_str} отправил сумму:\n{amount}")
        buttons = [types.InlineKeyboardButton(text="Да", callback_data="conf_yes"),
                   types.InlineKeyboardButton(text="Нет", callback_data="conf_no")]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await send_message(f"Подтверждение поступления суммы", keyboard=keyboard)
        await state.set_state(States.CONFIRMATION)


@dp.callback_query_handler(Text(startswith="conf_"), state=States.CONFIRMATION)
async def confirmation_amount(call: types.CallbackQuery, state: FSMContext):
    result = call.data.split("_")[1]
    data = await state.get_data()
    if result == 'yes':
        insert_query = """INSERT INTO money (`user_id`, `first_name`, `last_name`, `username`, `amount`, `last_date`) 
                VALUES(?, ?, ?, ?, ?, ?)"""
        await db_crud(insert_query, (data.get('id'), data.get('first_name'),
                                     data.get('last_name'), f"@{data.get('username')}", data.get('amount'),
                                     datetime.datetime.now()))
        await send_message(chat_id=data.get('id'), message='Сумма подтверждена')
        await call.message.edit_text('Сумма подтверждена')
    else:
        await send_message(chat_id=data.get('id'), message='Сумма не подтверждена')
        await call.message.edit_text('Сумма не подтверждена')
    await call.answer()
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
