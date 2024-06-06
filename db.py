import sqlite3
import time

import settings

from aiogram.types import Message

DB_FILENAME = settings.DB_FILENAME

def check_database():
	with sqlite3.connect(DB_FILENAME) as con:
		con.execute("""CREATE TABLE IF NOT EXISTS users (
		user_id TEXT,
		balance FLOAT,
		bet INT,
		jp_count INT,
		roll_count INT,
		reset_count INT,
		slot_type INT,
		recently_balance_msg INT,
		recently_balance_msg_time FLOAT,
		last_dice_time FLOAT,
		username TEXT
	) """)


async def update_user_balance(chat_id: int, new_balance: float):
	with sqlite3.connect(DB_FILENAME) as cn:
		cn.execute(f"UPDATE users SET balance = {new_balance} WHERE user_id = '{chat_id}'")


async def get_user_recently_balance_msg(chat_id: int) -> int:
	with sqlite3.connect(DB_FILENAME) as cn:
		result = int(list(cn.execute(f"SELECT recently_balance_msg FROM users WHERE user_id = '{chat_id}'"))[0][0])
	return result


async def update_user_recently_balance_msg(chat_id: int, message: Message) -> None:
	with sqlite3.connect(DB_FILENAME) as cn:
		cn.execute(f"UPDATE users SET recently_balance_msg = {int(message.message_id)} WHERE user_id = '{chat_id}'")


async def update_user_recently_balance_msg_time(chat_id: int) -> None:
	with sqlite3.connect(DB_FILENAME) as cn:
		cn.execute(f"UPDATE users SET recently_balance_msg_time = {float(time.time())} WHERE user_id = '{chat_id}'")


async def get_user_recently_balance_msg_time(chat_id: int) -> float:
	with sqlite3.connect(DB_FILENAME) as cn:
		result = float(
			list(cn.execute(f"SELECT recently_balance_msg_time FROM users WHERE user_id = '{chat_id}'"))[0][0])
	return result


async def increment_user_jp_count(chat_id: int) -> None:
	with sqlite3.connect(DB_FILENAME) as cn:
		cn.execute(f"UPDATE users SET jp_count = jp_count + 1 WHERE user_id = '{chat_id}'")


async def increment_user_roll_count(chat_id: int) -> None:
	with sqlite3.connect(DB_FILENAME) as cn:
		cn.execute(f"UPDATE users SET roll_count = roll_count + 1 WHERE user_id = '{chat_id}'")


async def get_user_balance(chat_id: int) -> float:
	with sqlite3.connect(DB_FILENAME) as cn:
		balance = float(list(cn.execute(f"SELECT balance FROM users WHERE user_id = '{chat_id}'"))[0][0])
	return balance


async def get_user_last_dice_time(chat_id: int) -> float:
	with sqlite3.connect(DB_FILENAME) as cn:
		last_dice_time = float(list(cn.execute(f"SELECT last_dice_time FROM users WHERE user_id = '{chat_id}'"))[0][0])
	return last_dice_time


async def update_user_last_dice_time(chat_id: int) -> None:
	with sqlite3.connect(DB_FILENAME) as cn:
		cn.execute(f"UPDATE users SET last_dice_time = {float(time.time())} WHERE user_id = '{chat_id}'")


async def get_user_bet(chat_id: int) -> int:
	with sqlite3.connect(DB_FILENAME) as cn:
		bet = int(list(cn.execute(f"SELECT bet FROM users WHERE user_id = '{chat_id}'"))[0][0])
	return bet


async def get_user_slot_type(chat_id: int) -> int:
	with sqlite3.connect(DB_FILENAME) as cn:
		slot_type = int(list(cn.execute(f"SELECT slot_type FROM users WHERE user_id = '{chat_id}'"))[0][0])
	return slot_type


async def check_is_user_exist(chat_id: int) -> bool:
	with sqlite3.connect(DB_FILENAME) as cn:
		cur = cn.cursor()
		cur.execute(f"SELECT user_id FROM users WHERE user_id = '{chat_id}'")
		return cur.fetchone() is not None  # False если такого user_id нет


async def add_new_user_to_db(chat_id: int, username: str) -> None:
	with sqlite3.connect(DB_FILENAME) as cn:
		cn.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
				   (chat_id, 100, 1, 0, 0, 0, 0, 0, 0, 0, username))


async def reset_user_bet(chat_id: int) -> None:
	with sqlite3.connect(DB_FILENAME) as cn:
		cn.execute(f"UPDATE users SET bet = 0 WHERE user_id = '{chat_id}'")


async def update_user_bet(chat_id: int, bet: int) -> None:
	with sqlite3.connect(DB_FILENAME) as cn:
		cn.execute(f"UPDATE users SET bet = {bet} WHERE user_id = '{chat_id}'")


async def update_user_slot_type(chat_id: int, slot_type: int):
	with sqlite3.connect(DB_FILENAME) as cn:
		cn.execute(f"UPDATE users SET slot_type = '{slot_type}' WHERE user_id = '{chat_id}'")


