import mysql.connector as sql
import telebot
import requests
import json
from telebot import types
from tendo import singleton
from geopy.geocoders import Nominatim as geolocation
from datetime import datetime
from multiprocessing import *
import math
from re import fullmatch as check_re

# Импорт настроек (токены + настройки для подключения к БД)
from config import *
from functions import *

tmp_time = datetime.now()
print('\n\n')
print(tmp_time.isoformat(), '– PROGRAMM STARTED!')

connection = sql.connect(
    user = db_config['user'],
    password = db_config['password'],
    unix_socket = db_config['unix_socket'],
    database = db_config['database']
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

##################### НАЧАЛО РАСПИСАНИЯ ########################

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
			print(tmp_time.isoformat(), '– sended to user ' + str(item[0]))

p = Process(target=send_schedule)
p.start()
    
me = singleton.SingleInstance()

##################### КОНЕЦ РАСПИСАНИЯ ########################

def confirm():
	connection.commit()

def set_type(id, ctype):
	st = "UPDATE wb_clothes set type = %s WHERE id = %s"
	vals = [ctype, id]
	db.execute(st, vals)
	confirm()

def set_thing(id, cthing):
	st = "UPDATE wb_clothes set thing = %s WHERE id = %s"
	vals = [cthing, id]
	db.execute(st, vals)
	confirm()

def get_clothes_info(id):
	st = "SELECT * FROM wb_clothes WHERE id = %s"
	vals = [id]
	db.execute(st, vals)
	res = db.fetchall()[0]
	return (res[1], res[2], res[3], res[4])

def remove_clothes(id):
	st = "DELETE FROM wb_clothes WHERE id = %s"
	vals = [id]
	db.execute(st, vals)
	confirm()


def set_screen(uuid, screen):
	st = "UPDATE wb_users SET screen = %s WHERE tg_id = %s"
	vals = [screen, uuid]
	db.execute(st, vals)
	confirm()

def generate_inline_keyboard(buttons):
	keyboard = types.InlineKeyboardMarkup()
	for item in buttons:
		temp_btn = types.InlineKeyboardButton(text = item['text'], callback_data = item['callback'])
		keyboard.add(temp_btn)
	return keyboard

def set_location(uuid, location):
	st = "UPDATE wb_users SET lat = %s, lon = %s, screen = 0 WHERE tg_id = %s"
	vals = [location['latitude'], location['longitude'], uuid]
	db.execute(st, vals)
	confirm()

	send_success(uuid)
def set_city(uuid, text):
	geo = geolocation(user_agent="wbot")
	tmp_location = geo.geocode(text)
	try:
		set_location(uuid, {
			'latitude': tmp_location.latitude,
			'longitude': tmp_location.longitude
		})
	except AttributeError:
		bot.send_message(uuid, f"Неверно указан город, попробуйте ещё раз ❌", reply_markup = no_kb)
		set_screen(uuid, 1)

def save_new_name(uuid, name, c_id, msg_id):
	st = 'UPDATE wb_clothes SET name = %s WHERE id = %s'
	vals = [name, c_id]
	db.execute(st, vals)
	confirm()
	set_screen(uuid, 0)
	send_success(uuid)

def set_new_time(uuid, time):
	match = check_re(r'^(([01][0-9]|[012][0-3]):([0-5][0-9]))*$', time)
	if (match):
		set_screen(uuid, 0)
		st = 'UPDATE wb_schedule SET time = %s WHERE user = %s'
		vals = [time + ':00', uuid]
		db.execute(st, vals)
		confirm()

		send_success(uuid)
	else:
		msg = "❌ Неправильный формат, попробуйте ещё раз. Отправлять нужно строго в формате ЧЧ:ММ (по московскому времени)"
		bot.send_message(uuid, msg, reply_markup = no_kb)


@bot.message_handler(commands=['start'])
def start(message):
	uuid = message.chat.id

	st = "SELECT * FROM wb_users WHERE tg_id = %s"
	vals = [uuid]
	db.execute(st, vals)
	res = db.fetchall()
		

	if (res == []):
		bot.send_message(uuid, "Здравствуйте! Для продолжения отправьте название своего города или своё местоположение", reply_markup = no_kb)

		st = "INSERT INTO wb_users (tg_id, screen) VALUES (%s, %s)"
		db.execute(st, [uuid, 1])
		confirm()

		st = 'INSERT INTO wb_schedule (user) VALUES (%s)'
		db.execute(st, [uuid])
		confirm()
	
	else:
		send_weather(uuid)
@bot.message_handler(content_types=['location'])
def location(message):
	uuid = message.chat.id
	if check_active(uuid):
		if (get_screen(uuid) == 1):
			set_location(uuid, {
				'latitude': message.location.latitude,
				'longitude': message.location.longitude
			})
@bot.message_handler(commands=['deactivate'])
def deactivate(message):
	uuid = message.chat.id


	st = "UPDATE `wb_users` SET `active` = false, `screen` = 0 WHERE `tg_id` = %s"
	vals = [uuid]
	db.execute(st, vals)
	confirm()

	res = db.fetchall()

	send_success(uuid)
@bot.message_handler(commands=['activate'])
def activate(message):
	uuid = message.chat.id

	st = "UPDATE `wb_users` SET `active` = true, `screen` = 0 WHERE `tg_id` = %s"
	vals = [uuid]
	db.execute(st, vals)
	confirm()

	res = db.fetchall()

	send_success(uuid)
@bot.message_handler(commands=['setlocation'])
def setlocation(message):
	uuid = message.chat.id
	if check_active(uuid):
		st = "UPDATE wb_users SET screen = 1 WHERE tg_id = %s"
		vals = [uuid]
		db.execute(st, vals)
		confirm()

		bot.send_message(uuid, "Отправьте новое местоположение", reply_markup = no_kb)

@bot.message_handler(commands=['my_clothes'])
def my_clothes(message):
	uuid = message.chat.id
	if check_active(uuid):
		st = "SELECT id, name, type, thing FROM wb_clothes WHERE user = %s"

		vals = [uuid]
		db.execute(st, vals)
		msg = "<u><b>Ваша одежда:</b></u>\n\n"
		for item in db.fetchall():
			if (item[2] == None or item[3] == None):
				# remove_clothes(item[0])
				pass
			else:
				c_name = item[1]
				c_description = get_clothes_description(item[2], item[3])
				c_type = c_description[0]
				c_thing = c_description[1]
				
				msg += f"– {c_name}, тип: {c_type}, вид: {c_thing}\n"

		bot.send_message(uuid, msg, parse_mode = 'html', reply_markup = main_kb)


@bot.message_handler(commands=['edit_clothes'])
def edit_clothes(message, offset = 0, edit = False, msg_id = -1):
	uuid = message.chat.id
	if check_active(uuid):
		st = "SELECT COUNT(id) FROM wb_clothes WHERE user = %s"
		vals = [uuid]
		

		db.execute(st, vals)
		quantity = int(db.fetchall()[0][0])

		page = math.ceil(offset / 5)
		if ((offset % 5) == 0):
			page += 1
		c_page = math.ceil(quantity / 5)

		st = "SELECT id, name FROM wb_clothes WHERE user = %s AND type IS NOT NULL AND thing IS NOT NULL LIMIT %s, 5"

		vals = [uuid, offset]
		db.execute(st, vals)

		buttons = []

		for c_id, c_name in db.fetchall():
			buttons.append({'text': c_name, 'callback': '{"func":"edit","id":' + str(c_id) + ',"o":' + str(offset) + '}'})
		keyboard = generate_inline_keyboard(buttons)

		if (page == 1 and c_page == 1):
			pass
		elif (page == 1):
			keyboard.add(types.InlineKeyboardButton(text = '➡️', callback_data = '{"func":"np","o":' + str(offset) + '}'))
		elif (page == c_page):
			keyboard.add(types.InlineKeyboardButton(text = '⬅️', callback_data = '{"func":"pp","o":' + str(offset) + '}'))
		else:
			keyboard.row(
				types.InlineKeyboardButton(text = '⬅️', callback_data = '{"func":"pp","o":' + str(offset) + '}'),
				types.InlineKeyboardButton(text = '➡️', callback_data = '{"func":"np","o":' + str(offset) + '}')
			)
		

		msg = f'Редактирование одежды\n\nСтраница {page} из {c_page}'

		if (edit):
			bot.edit_message_text(chat_id = uuid, message_id = msg_id, text = msg, reply_markup = keyboard, parse_mode = 'html')
		else:
			bot.send_message(uuid, msg, parse_mode = 'html', reply_markup = keyboard)


@bot.message_handler(commands=['schedule'])
def schedule(message, edit = False):
	uuid = message.chat.id
	if check_active(uuid):
		days_of_week = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']

		st = 'SELECT mon, tue, wed, thu, fri, sat, sun, time FROM wb_schedule WHERE user = %s'
		vals = [uuid]
		db.execute(st, vals)
		days_res = []
		db_res = db.fetchall()[0]
		schedule_time = db_res[7]

		if (schedule_time == None):
			msg = 'Расписание пока не установлено. \n\n<i>Расписание — это рекомендации одежды в определённое время. Например, Вы можете настроить расписание так, что Вам автоматически будут приходить рекомендации в будни в 8:00.</i>'
		else:
			for num, day in enumerate(db_res[:7]):
				if (day == 1):
					days_res.append(days_of_week[num])

			if (days_res == []):
				days_res.append('дни не выбраны,')


			msg = f'<u><b>Текущее расписание:</b></u> \n{ ", ".join(days_res) } в { str(schedule_time)[:-3] }'

		buttons = (
			{'text': 'Изменить дни ✏️', 'callback': '{"func":"edit_days"}'},
			{'text': 'Изменить время ⏰', 'callback': '{"func":"edit_time"}'},
			{'text': 'Удалить расписание ❌', 'callback': '{"func":"delete_time"}'},
		)

		keyboard = generate_inline_keyboard(buttons)

		if (edit):
			bot.edit_message_text(chat_id = uuid, message_id = message.message_id, text = msg, reply_markup = keyboard, parse_mode = 'html')
		else:
			bot.send_message(uuid, msg, parse_mode = 'html', reply_markup = keyboard)


@bot.message_handler(commands=['add_clothes'])
def add_clothes(message):
	uuid = message.chat.id
	if check_active(uuid):
		text = "Введите название вещи"
		set_screen(uuid, 2)
		bot.send_message(uuid, text, reply_markup = no_kb)

def choose_type(uuid, name, edit=False, msg_id=-1, thing_id=-1):
	if check_active(uuid):
		set_screen(uuid, 0)
		if (edit):
			pass
		else:
			st = "INSERT INTO wb_clothes (user, name) VALUES (%s, %s)"
			vals = [uuid, name]
			db.execute(st, vals)
			confirm()
			st = "SELECT LAST_INSERT_ID()"
			db.execute(st)
			thing_id = db.fetchall()[0][0]

		msg = f"Выберете тип и вид одежды.\n\n<u><b>Название:</b></u> {name}\nТип:"
		buttons = (
			{'text': 'Головной убор', 'callback': '{"func":"headdress","id":' + str(thing_id) + '}'},
			{'text': 'Верхняя одежда', 'callback': '{"func":"outerwear","id":' + str(thing_id) + '}'},
			{'text': 'Штаны', 'callback': '{"func":"pants","id":' + str(thing_id) + '}'},
			{'text': 'Обувь', 'callback': '{"func":"shoes","id":' + str(thing_id) + '}'},
			{'text': 'Назад 🔙', 'callback': '{"func":"back_to_name","id":' + str(thing_id) + '}'},
		)

		keyboard = generate_inline_keyboard(buttons)

		if (edit):
			bot.edit_message_text(chat_id = uuid, message_id = msg_id, text = msg, reply_markup = keyboard, parse_mode = 'html')
		else:
			bot.send_message(uuid, msg, reply_markup = keyboard, parse_mode = 'html')

@bot.callback_query_handler(func = lambda call: True)
def answer(call):
	uuid = call.message.chat.id

	exceptions = ['np', 'pp', 'edit_days', 'edit_time', 'delete_time', 'delete_y', 'delete_n']

	if check_active(uuid):
		data = json.loads(call.data)
		if (data['func'] not in exceptions and data['func'][0] != '%'):
			clothes_data = get_clothes_info(data['id'])
			c_name = clothes_data[1]
			c_type = clothes_data[2]
			c_thing = clothes_data[3]

		if (data['func'] == 'headdress'):
			set_type(data['id'], 0)
			c_type = 0
			msg = f"Отлично 👍\nТеперь выберете тип и вид одежды.\n\n<u><b>Название:</b></u> {c_name}\n<u><b>Тип:</b></u> Головной убор\n\nВид:"

			buttons = (
				{'text': 'Тёплая шапка', 'callback': '{"func":"addc01","id":' + str(data['id']) + '}'},
				{'text': 'Зимняя шапка', 'callback': '{"func":"addc02","id":' + str(data['id']) + '}'},
				{'text': 'Шапка', 'callback': '{"func":"addc03","id":' + str(data['id']) + '}'},
				{'text': 'Шапка (можно и без неё)', 'callback': '{"func":"addc04","id":' + str(data['id']) + '}'},
				{'text': 'Кепка', 'callback': '{"func":"addc05","id":' + str(data['id']) + '}'},
				{'text': 'Назад 🔙', 'callback': '{"func":"thing_back","id":' + str(data['id']) + '}'},
			)
			
			keyboard = generate_inline_keyboard(buttons)

			bot.edit_message_text(chat_id = uuid, message_id = call.message.message_id, text = msg, reply_markup = keyboard, parse_mode = 'html')
		
		elif (data['func'] == 'outerwear'):
			set_type(data['id'], 2)
			c_type = 2
			msg = f"Отлично 👍\nТеперь выберете тип и вид одежды.\n\n<u><b>Название:</b></u> {c_name}\n<u><b>Тип:</b></u> Верхняя одежда\n\nВид:"

			buttons = (
				{'text': 'Очень тёплая куртка', 'callback': '{"func":"addc20","id":' + str(data['id']) + '}'},
				{'text': 'Зимняя курка', 'callback': '{"func":"addc21","id":' + str(data['id']) + '}'},
				{'text': 'Ветровка', 'callback': '{"func":"addc22","id":' + str(data['id']) + '}'},
				{'text': 'Ветровка или худи', 'callback': '{"func":"addc23","id":' + str(data['id']) + '}'},
				{'text': 'Свитер', 'callback': '{"func":"addc11","id":' + str(data['id']) + '}'},
				{'text': 'Худи', 'callback': '{"func":"addc24","id":' + str(data['id']) + '}'},
				{'text': 'Футболка', 'callback': '{"func":"addc25","id":' + str(data['id']) + '}'},
				{'text': 'Назад 🔙', 'callback': '{"func":"thing_back","id":' + str(data['id']) + '}'},
			)
			
			keyboard = generate_inline_keyboard(buttons)

			bot.edit_message_text(chat_id = uuid, message_id = call.message.message_id, text = msg, reply_markup = keyboard, parse_mode = 'html')

		elif (data['func'] == 'pants'):
			set_type(data['id'], 3)
			c_type = 3
			msg = f"Отлично 👍\nТеперь выберете тип и вид одежды.\n\n<u><b>Название:</b></u> {c_name}\n<u><b>Тип:</b></u> Штаны\n\nВид:"

			buttons = (
				{'text': 'Тёплые штаны', 'callback': '{"func":"addc30","id":' + str(data['id']) + '}'},
				{'text': 'Джинсы', 'callback': '{"func":"addc31","id":' + str(data['id']) + '}'},
				{'text': 'Шорты', 'callback': '{"func":"addc32","id":' + str(data['id']) + '}'},
				{'text': 'Назад 🔙', 'callback': '{"func":"thing_back","id":' + str(data['id']) + '}'},
			)
			
			keyboard = generate_inline_keyboard(buttons)

			bot.edit_message_text(chat_id = uuid, message_id = call.message.message_id, text = msg, reply_markup = keyboard, parse_mode = 'html')

		elif (data['func'] == 'shoes'):
			set_type(data['id'], 4)
			c_type = 4
			msg = f"Отлично 👍\nТеперь выберете тип и вид одежды.\n\n<u><b>Название:</b></u> {c_name}\n<u><b>Тип:</b></u> Обувь\n\nВид:"

			buttons = (
				{'text': 'Сапоги', 'callback': '{"func":"addc40","id":' + str(data['id']) + '}'},
				{'text': 'Тёплые ботинки', 'callback': '{"func":"addc41","id":' + str(data['id']) + '}'},
				{'text': 'Ботинки или кроссовки', 'callback': '{"func":"addc42","id":' + str(data['id']) + '}'},
				{'text': 'Кроссовки', 'callback': '{"func":"addc43","id":' + str(data['id']) + '}'},
				{'text': 'Назад 🔙', 'callback': '{"func":"thing_back","id":' + str(data['id']) + '}'},
			)
			
			keyboard = generate_inline_keyboard(buttons)

			bot.edit_message_text(chat_id = uuid, message_id = call.message.message_id, text = msg, reply_markup = keyboard, parse_mode = 'html')



		elif (data['func'][0:4] == 'addc'):
			c_type = data['func'][4]
			c_thing = data['func'][5]

			st = "UPDATE wb_clothes SET name = %s, type = %s, thing = %s WHERE id = %s"
			vals = [c_name, c_type, c_thing, data['id']]
			db.execute(st, vals)
			confirm()

			bot.send_message(chat_id = uuid, text = 'Успешно ✅', reply_markup = main_kb)
			bot.delete_message(chat_id = uuid, message_id = call.message.message_id)


		elif (data['func'] == 'np'):
			edit_clothes(call.message, int(data['o']) + 5, True, call.message.message_id)

		elif (data['func'] == 'pp'):
			edit_clothes(call.message, int(data['o']) - 5, True, call.message.message_id)

		elif (data['func'] == 'edit' or data['func'] == 'rmc_n'):
			buttons = (
				{'text': 'Изменить название ✏️', 'callback': '{"func":"edit_name","id":' + str(data['id']) + '}'},
				{'text': 'Изменить тип ✏️', 'callback': '{"func":"edit_type","id":' + str(data['id']) + '}'},
				{'text': 'Удалить ❌', 'callback': '{"func":"remove","id":' + str(data['id']) + ',"o":' + str(data['o']) +'}'},
				{'text': 'Назад 🔙', 'callback': '{"func":"edit_back","id":' + str(data['id']) + ',"o":' + str(data['o']) +'}'},
			)

			keyboard = generate_inline_keyboard(buttons)

			msg = f'Редактируем {c_name}'

			bot.edit_message_text(chat_id = uuid, message_id = call.message.message_id, text = msg, reply_markup = keyboard, parse_mode = 'html')

		elif (data['func'] == 'edit_back'):
			edit_clothes(call.message, int(data['o']), True, call.message.message_id)

		elif (data['func'] == 'edit_type'):
			choose_type(uuid, c_name, True, call.message.message_id, data['id'])

		elif (data['func'] == 'remove'):
			buttons = (
				{'text': 'Да', 'callback': '{"func":"rmc_y","id":' + str(data['id']) + '}'},
				{'text': 'Назад 🔙', 'callback': '{"func":"rmc_n","id":' + str(data['id']) + ',"o":' + str(data['o']) +'}'},
			)
			keyboard = generate_inline_keyboard(buttons)
			msg = f'Вы уверены что хотите удалить {c_name}?'
			bot.edit_message_text(chat_id = uuid, message_id = call.message.message_id, text = msg, reply_markup = keyboard, parse_mode = 'html')

		elif (data['func'] == 'rmc_y'):
			remove_clothes(data['id'])
			bot.send_message(chat_id = uuid, text = 'Успешно ✅', reply_markup = main_kb)
			bot.delete_message(chat_id = uuid, message_id = call.message.message_id)
		
		elif (data['func'] == 'edit_name'):
			uuid = call.message.chat.id
			msg = "Введите название вещи"
			new_screen = '9_' + str(data['id']) + '_' + str(call.message.message_id)
			set_screen(uuid, new_screen)

			bot.delete_message(chat_id = uuid, message_id = call.message.message_id)
			bot.send_message(chat_id = uuid, text = msg, reply_markup = no_kb)

		elif (data['func'] == 'edit_days'):
			days_of_week = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']

			st = 'SELECT mon, tue, wed, thu, fri, sat, sun FROM wb_schedule WHERE user = %s'
			vals = [uuid]
			db.execute(st, vals)
			days_res = []
			db_res = db.fetchall()[0]

			for num, day in enumerate(db_res):
				if (day == 1):
					days_res.append(days_of_week[num] + ' ✅')
				else:
					days_res.append(days_of_week[num])

			buttons = []

			for num, day in enumerate(days_res):
				buttons.append({'text': day, 'callback': '{"func":"%_' + str(num) +'"}'},)
			buttons.append({'text': 'Назад 🔙', 'callback': '{"func":"%_b"}'},)


			keyboard = generate_inline_keyboard(buttons)

			bot.edit_message_text(chat_id = uuid, message_id = call.message.message_id, text = call.message.text, reply_markup = keyboard)

		elif (data['func'][0] == '%'):
			action = data['func'][2:]
			if (action == 'b'):
				schedule(call.message, True)
			else:
				days_of_week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
				st = 'SELECT ' + days_of_week[int(action)] + ' FROM wb_schedule WHERE user = %s'
				vals = [uuid]
				db.execute(st, vals)
				if (db.fetchall()[0][0] == 0):
					day_value = 1
				else:
					day_value = 0

				st = 'UPDATE wb_schedule SET ' + days_of_week[int(action)] + ' = %s WHERE user = %s'
				vals = [day_value, uuid]
				db.execute(st, vals)
				confirm()

				days_of_week = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']

				st = 'SELECT mon, tue, wed, thu, fri, sat, sun, time FROM wb_schedule WHERE user = %s'
				vals = [uuid]
				db.execute(st, vals)
				days_res_btn = []
				days_res = []
				db_res = db.fetchall()[0]
				for num, day in enumerate(db_res[:7]):
					if (day == 1):
						days_res_btn.append(days_of_week[num] + ' ✅')
						days_res.append(days_of_week[num])
					else:
						days_res_btn.append(days_of_week[num])

				buttons = []

				for num, day in enumerate(days_res_btn):
					buttons.append({'text': day, 'callback': '{"func":"%_' + str(num) +'"}'},)
				buttons.append({'text': 'Назад 🔙', 'callback': '{"func":"%_b"}'},)

				schedule_time = db_res[7]
				if (days_res == []):
					days_res.append('дни не выбраны,')

				msg = f'<u><b>Текущее расписание:</b></u> \n{ ", ".join(days_res) } в { str(schedule_time)[:-3] }'

				keyboard = generate_inline_keyboard(buttons)

				bot.edit_message_text(chat_id = uuid, message_id = call.message.message_id, text = msg, reply_markup = keyboard, parse_mode = 'html')
		
		elif (data['func'] == 'edit_time'):
			set_screen(uuid, 6)

			msg = 'Отправьте новое время в формате ЧЧ:ММ (по московскому времени)'

			bot.delete_message(chat_id = uuid, message_id = call.message.message_id)
			bot.send_message(chat_id = uuid, text = msg, reply_markup = no_kb)

		elif (data['func'] == 'delete_time'):
			buttons = (
				{'text': 'Да', 'callback': '{"func":"delete_y"}'},
				{'text': 'Назад 🔙', 'callback': '{"func":"delete_n"}'}
			)
			keyboard = generate_inline_keyboard(buttons)
			msg = 'Вы уверены, что хотите удалить расписание?'
			bot.edit_message_text(chat_id = uuid, message_id = call.message.message_id, text = msg, reply_markup = keyboard, parse_mode = 'html')

		elif (data['func'] == 'delete_n'):
			schedule(call.message, True)

		elif (data['func'] == 'delete_y'):
			st = 'UPDATE wb_schedule SET time = NULL, mon = 0, tue = 0, wed = 0, thu = 0, fri = 0, sat = 0, sun = 0 WHERE user = %s'
			db.execute(st, [uuid])
			confirm()

			bot.delete_message(chat_id = uuid, message_id = call.message.message_id)
			send_success(uuid)

		elif (data['func'] == 'thing_back'):
			choose_type(uuid, c_name, True, call.message.message_id, data['id'])
		elif (data['func'] == 'back_to_name'):
			set_screen(data['id'], 2)
			add_clothes(call.message)
			bot.delete_message(chat_id = uuid, message_id = call.message.message_id)

@bot.message_handler(content_types=['text'])
def text(message):
	uuid = message.chat.id
	screen = get_screen(uuid)
	text = message.text
	if check_active(uuid):
		if (text == '➕ Добавить одежду'):
			add_clothes(message)
		elif (text == '👔 Что надеть?'):
			send_weather(uuid)
		elif (text == '🗄️ Моя одежда'):
			my_clothes(message)
		elif (text == '🏠 Сменить город'):
			setlocation(message)
		elif (text == '⏰ Расписание'):
			schedule(message)
		elif (text == '✏️ Редактировать одежду'):
			edit_clothes(message)
		else:
			if (isinstance(screen, int)):
				if (screen == 1):
					set_city(uuid, text)
				elif (screen == 2):
					choose_type(uuid, text)
				elif (screen == 6):
					set_new_time(uuid, text)
				else:
					send_idk(uuid)
			else:
				if (screen[0] == 9):
					save_new_name(uuid, text, screen[1], screen[2])
				else:
					send_idk(uuid)

bot.polling(none_stop=True)

def threadwrap(threadfunc):
    def wrapper():
        while True:
            try:
                threadfunc()
            except BaseException as e:
                th_name = threading.current_thread().name
                print(f'Падение потока датчика {th_name}, перезапуск...')
    return wrapper