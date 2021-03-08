import mysql.connector as sql
import telebot
from telebot import types
from tendo import singleton
from datetime import datetime

# Импорт настроек (токены + настройки для подключения к БД)
from config import *
from functions import *

tmp_time = datetime.now()
connection = sql.connect(
    user = db_config['user'],
    password = db_config['password'],
    unix_socket = db_config['unix_socket'],
    database = db_config['database'],
	autocommit = True
)
db = connection.cursor()


bot = telebot.TeleBot(TOKEN)

main_kb = types.ReplyKeyboardMarkup(True)
main_kb.add(
	types.KeyboardButton('👔 Что надеть?'),
	types.KeyboardButton('➕ Добавить одежду')
)
main_kb.row(
	types.KeyboardButton('🗄️ Моя одежда'),
	types.KeyboardButton('🏠 Сменить город')
)
main_kb.row(
	types.KeyboardButton('⏰ Расписание'),
	types.KeyboardButton('✏️ Редактировать одежду')
)

no_kb = types.ReplyKeyboardRemove()

def send_success(uuid):
	bot.send_message(uuid, f"Успешно ✅", reply_markup = main_kb)
def send_idk(uuid):
	bot.send_message(uuid, f"Я не знаю что ответить 😢", reply_markup = main_kb)

def get_screen(uuid):
	st = "SELECT screen FROM wb_users WHERE tg_id = %s"
	vals = [uuid]
	db.execute(st, vals)
	db_res = db.fetchall()[0][0]

	if (db_res[0] != '9'):
		res = int(db_res)
	else:
		res = tuple(map(int, db_res.split('_')))

	return res
def check_active(uuid):
	st = "SELECT active FROM wb_users WHERE tg_id = %s"
	vals = [uuid]
	db.execute(st, vals)
	active = db.fetchall()[0][0]

	if (active == 0):
		bot.send_message(uuid, "⚠ Ваш профиль неактивен! Отправьте /activate для активации", reply_markup = no_kb)
		return False
	return True
def send_weather(uuid):
	if check_active(uuid):
		if get_screen(uuid) == 0:
			st = "SELECT lat, lon FROM wb_users WHERE tg_id = %s"
			vals = [uuid]
			db.execute(st, vals)

			data = db.fetchall()[0]
			lat = data[0]
			lon = data[1]

			message = generate_message(lat, lon, db, uuid)
			
			bot.send_message(uuid, message, parse_mode='html', reply_markup = main_kb)
		else:
			send_idk(uuid)


def send_schedule():
	now = datetime.now()

	days_of_week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

	h, m, d = now.hour, now.minute, days_of_week[now.weekday()]	
	st = 'SELECT user FROM `wb_schedule` WHERE `time` = "%s:%s:00" AND ' + d + ' = 1'

	vals = [h, m]
	db.execute(st, vals)

	db_res = db.fetchall()

	for item in db_res:
		st = "SELECT active FROM wb_users WHERE tg_id = %s"
		vals = [item[0]]
		db.execute(st, vals)
		active = db.fetchall()[0][0]
		if (active == 1):
			send_weather(item[0])
			print(tmp_time.isoformat() + ' – sended to user ' + str(item[0]))
	
	exit()

send_schedule()