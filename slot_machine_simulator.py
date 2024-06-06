import logging
import time
from datetime import datetime
import asyncio

import db
import text
import settings

from aiogram import F, Bot, Dispatcher, Router, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message, ContentType, CallbackQuery

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize bot and dispatcher
API_TOKEN = settings.API_TOKEN

bot = Bot(token=API_TOKEN)
memory_storage = MemoryStorage()
dp = Dispatcher(storage=memory_storage)
router: Router = Router()

class SettingsDialog(StatesGroup):
    waiting_for_setting_select = State()
    waiting_for_bet_value_select = State()
    waiting_for_slot_type_select = State()
    available_settings = ['изменить ставку', 'изменить тип автомата']
    available_bet_values = ['1', '2', '5', '10']
    available_slot_types = ['Classic', 'Bar$ & Seven$']


constructSettingsKeyboardMarkup = lambda: ReplyKeyboardMarkup(resize_keyboard=True,
    keyboard=[[KeyboardButton(text="Изменить ставку")], [KeyboardButton(text="Изменить тип автомата")],
              [KeyboardButton(text="Назад")]])

constructSelectBetKeyboardMarkup = lambda: ReplyKeyboardMarkup(resize_keyboard=True,
    keyboard=[[KeyboardButton(text='1')],[KeyboardButton(text='2')], [KeyboardButton(text='5')], [KeyboardButton(text='10')]])

constructSelectSlotTypeKeyboardMarkup = lambda: ReplyKeyboardMarkup(resize_keyboard=True,
    keyboard=[[KeyboardButton(text='Classic')],[KeyboardButton(text='Bar$ & Seven$')]])

constructHomeKeyboardMarkup = lambda: ReplyKeyboardMarkup(resize_keyboard=True,
    keyboard=[[KeyboardButton(text="🎰")], [KeyboardButton(text="Настройки")], [KeyboardButton(text='Баланс и информация')]])


@router.message(F.text.lower() == 'настройки', F.text)
async def settings_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id,
                           "Что желаете изменить?",
                           reply_markup=constructSettingsKeyboardMarkup())
    await state.set_state(SettingsDialog.waiting_for_setting_select)


@router.message(F.text.lower() == 'назад', F.text)
async def go_back_handler(message: Message, state: FSMContext):
    await bot.send_message(message.chat.id,'Крути!', reply_markup=constructHomeKeyboardMarkup())


@router.message(F.text.lower() == 'баланс и информация', F.text)
async def settings_info_handler(message: Message, state: FSMContext):
    user_balance = await db.get_user_balance(message.chat.id)
    slot_type_number = await db.get_user_slot_type(message.chat.id)
    slot_type = SettingsDialog.available_slot_types[slot_type_number]
    user_bet = await db.get_user_bet(message.chat.id)
    user_last_dice_time_ts = await db.get_user_last_dice_time(message.chat.id)
    dt_obj = datetime.fromtimestamp(user_last_dice_time_ts)
    user_last_dice_time = dt_obj.strftime("%d/%m/%y %H:%M:%S")
    await bot.send_message(message.chat.id,
                           f"Ваш баланс: {int(user_balance)}\n"+
                           f"Тип автомата: {slot_type}\n"+
                           f"Ставка: {user_bet}\n"+
                           f"Последняя игра: {user_last_dice_time}",
                           reply_markup=constructHomeKeyboardMarkup())


@router.message(SettingsDialog.waiting_for_setting_select,F.text)
async def setting_select_handler(message: Message, state: FSMContext):
    if message.text.lower() not in SettingsDialog.available_settings:
        await message.answer('Крути!', reply_markup=constructHomeKeyboardMarkup())
        await state.finish()
        return

    if message.text.lower() == SettingsDialog.available_settings[0]:
        await db.reset_user_bet(message.chat.id)
        await bot.send_message(message.chat.id,
                               "Выберите ставку",
                               reply_markup=constructSelectBetKeyboardMarkup())
        await state.set_state(SettingsDialog.waiting_for_bet_value_select)

    elif message.text.lower() == SettingsDialog.available_settings[1]:
        await bot.send_message(message.chat.id, text.classic_mode,
                               reply_markup=constructSelectSlotTypeKeyboardMarkup())
        await bot.send_message(message.chat.id, text.bars_and_sevens)
        await bot.send_message(message.chat.id, text.reference)
        await state.set_state(SettingsDialog.waiting_for_slot_type_select)


@router.message(SettingsDialog.waiting_for_bet_value_select,F.text)
async def bet_value_select_handler(message: Message, state: FSMContext):
    if message.text.lower() not in SettingsDialog.available_bet_values:
        await message.answer('Крути!', reply_markup=constructHomeKeyboardMarkup())
        await state.finish()
        return

    await db.update_user_bet(message.chat.id, int(message.text))
    await bot.send_message(message.chat.id, f"Ставка изменена на {message.text}",
                           reply_markup=constructHomeKeyboardMarkup())
    await state.finish()


@router.message(SettingsDialog.waiting_for_slot_type_select,F.text)
async def slot_type_select_handler(message: Message, state: FSMContext):
    if message.text not in SettingsDialog.available_slot_types:
        await message.answer('Крути!', reply_markup=constructHomeKeyboardMarkup())
        await state.finish()
        return

    if message.text == SettingsDialog.available_slot_types[0]:
        await db.update_user_slot_type(message.chat.id, 0)
    elif message.text == SettingsDialog.available_slot_types[1]:
        await db.update_user_slot_type(message.chat.id, 1)

    await bot.send_message(message.chat.id,
                           f"Тип игрового автомата изменен на {message.text}",
                           reply_markup=constructHomeKeyboardMarkup())
    await state.finish()


@router.message(Command(commands=['start']))
async def start_handler(message: Message):
    if not await db.check_is_user_exist(message.chat.id):
        await db.add_new_user_to_db(message.chat.id, message.chat.username)
    await bot.send_message(message.chat.id, text.start_message,
                           reply_markup=constructHomeKeyboardMarkup())
    try:
        await bot.unpin_chat_message(message.chat.id)
    except:
        pass
    sent_balance_msg = await bot.send_message(message.chat.id,
                                              'Баланс: 100')
    await db.update_user_recently_balance_msg_time(message.chat.id)
    await db.update_user_recently_balance_msg(message.chat.id, sent_balance_msg)
    await bot.pin_chat_message(message.chat.id,
                               sent_balance_msg.message_id,
                               disable_notification=True)

async def get_new_balance(old_balance, bet, slot_res, message) -> float:
    await db.increment_user_roll_count(message.chat.id)
    new_balance = old_balance - bet
    multiplier = await get_win_multiplier(slot_res, bet, message.chat.id)
    if multiplier == 0:
        return new_balance
    if multiplier in (12, 14):
        await db.increment_user_jp_count(message.chat.id)
        await bot.send_message(message.chat.id,
                               f'JACKPOT!',
                               reply_to_message_id=message.message_id)
    new_balance = new_balance + bet * multiplier
    win_value = float(bet * multiplier)
    await bot.send_message(message.chat.id,
                           f'Вы выиграли {int(win_value)}!',
                           reply_to_message_id=message.message_id)
    return new_balance

async def calc_slot_res(value: int) -> str:  # 10 -> 4
    res = ''
    while value > 0:
        res = str(value % 4) + res
        value //= 4
    res = res[::-1]
    while len(res) < 3:
        res += '0'
    return res

async def get_win_multiplier(roll_res: str, bet: int, chat_id: int):
    slot_type = await db.get_user_slot_type(chat_id)
    if slot_type == 0:
        if roll_res == '333':
            return 12  # 777
        elif roll_res == '000':
            return 9  # BBB
        elif roll_res == '222':
            return 8  # LLL
        elif roll_res == '111':
            return 5  # GGG
        elif roll_res[0:2] == '33':
            return 3  # 77*
        elif roll_res[0:2] == '00':
            return 2  # BB*
        elif roll_res[0:2] == '22':
            return 2  # LL*
        elif roll_res[0:2] == '11':
            return 1  # GG*
        elif roll_res[1:3] == '11':
            return 1  # *GG
    elif slot_type == 1:
        if roll_res == '333':
            return 14  # 777
        elif roll_res == '000':
            return 14  # BBB
        elif roll_res == '303':
            return 7  # 7B7
        elif roll_res == '330':
            return 7  # 77B
        elif roll_res == '033':
            return 7  # B77
        elif roll_res == '030':
            return 3.5  # B7B
        elif roll_res == '003':
            return 3.5  # BB7
        elif roll_res == '300':
            return 3.5  # 7BB
    return 0  # lose

@router.message(F.dice)
async def dice_handler(message: Message, state: FSMContext):
    await state.finish()
    if message.forward_date or message.dice.emoji != '🎰':
        await bot.send_message(message.chat.id, text.content_type_error,
                               reply_markup=constructHomeKeyboardMarkup(),
                               reply_to_message_id=message.message_id)
        return

    slot_res = await calc_slot_res(message.dice.value - 1)
    balance = await db.get_user_balance(message.chat.id)
    bet = await db.get_user_bet(message.chat.id)
    last_dice_time = await db.get_user_last_dice_time(message.chat.id)
    if bet > balance:
        await bot.send_message(message.chat.id, text.balance_error,
                               reply_to_message_id=message.message_id)
    elif time.time() - last_dice_time > 0.5:
        await db.update_user_last_dice_time(message.chat.id)
        new_balance = await get_new_balance(balance, bet, slot_res, message)
        last_balance_msg_time = await db.get_user_recently_balance_msg_time(message.chat.id)
        await db.update_user_balance(message.chat.id, new_balance)
        balance_msg = f'Баланс: {int(new_balance)}'
        if (time.time() - last_balance_msg_time) > 86400:
            await bot.unpin_chat_message(message.chat.id)
            sent_balance_msg = await bot.send_message(message.chat.id,
                                                      balance_msg,
                                                      reply_to_message_id=message.message_id)
            await db.update_user_recently_balance_msg_time(message.chat.id)
            await db.update_user_recently_balance_msg(message.chat.id, sent_balance_msg)
            await bot.pin_chat_message(message.chat.id,
                                       sent_balance_msg.message_id,
                                       disable_notification=True)
        elif balance != new_balance:
            await bot.edit_message_text(chat_id=message.chat.id,
                                        message_id=await db.get_user_recently_balance_msg(message.chat.id),
                                        text=balance_msg)

    else:
        await bot.send_message(message.chat.id, text.click_too_fast,
                               reply_to_message_id=message.message_id)


async def main():
    # Create database if not exists
    db.check_database()

    dp.include_router(router)
    await dp.start_polling(bot, skip_updates=False)


if __name__ == '__main__':
    asyncio.run(main())
