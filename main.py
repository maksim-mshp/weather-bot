import mysql.connector as sql
import telebot
import requests
import json
from telebot import types
from tendo import singleton

# Импорт настроек (токены + настройки для подключения к БД)
from config import *
from functions import *

me = singleton.SingleInstance()
connection = sql.connect(
    user = db_config['user'],
    password = db_config['password'],
    unix_socket = db_config['unix_socket'],
    database = db_config['database']
)
db = connection.cursor()

bot = telebot.TeleBot(TOKEN)

def confirm():
	connection.commit()
def get_screen(uuid):
	st = "SELECT screen FROM wb_users WHERE tg_id = %s"
	vals = [uuid]
	db.execute(st, vals)
	return int(db.fetchall()[0][0])
def check_active(uuid):
	st = "SELECT active FROM wb_users WHERE tg_id = %s"
	vals = [uuid]
	db.execute(st, vals)
	active = db.fetchall()[0][0]

	if (active == 0):
		bot.send_message(uuid, "⚠ Ваш профиль неактивен! Отправьте /activate для активации")
		return False
	return True
def send_success(uuid):
	bot.send_message(uuid, f"Успешно ✅")
def send_idk(uuid):
	bot.send_message(uuid, f"Я не знаю что ответить 😢")
def set_location(uuid, location):
	st = "UPDATE wb_users SET city = NULL, lat = %s, lon = %s, screen = 0 WHERE tg_id = %s"
	vals = [location.latitude, location.longitude, uuid]
	db.execute(st, vals)
	confirm()

	send_success(uuid)
def set_city(uuid, text):
	st = "UPDATE wb_users SET city = %s, lat = NULL, lon = NULL, screen = 0 WHERE tg_id = %s"
	vals = [text, uuid]
	db.execute(st, vals)
	confirm()

	send_success(uuid)

def send_weather(uuid):
	st = "SELECT city, lat, lon FROM wb_users WHERE tg_id = %s"
	vals = [uuid]
	db.execute(st, vals)

	data = db.fetchall()[0]
	city = data[0]
	lat = data[1]
	lon = data[2]

	if (city == None):
		weather = get_weather_location(lat, lon)
	else:
		weather = get_weather_city(city)

	if (weather['cod'] == '404'):
		message = "Город не найден ❌"
	elif (weather['cod'] == 200):
		message = f"""
Температура: {weather['main']['temp']} С°
Ощущается как: {weather['main']['feels_like']} С°
Влажность: {weather['main']['humidity']}%
Сейчас на улице {weather['weather'][0]['description']}.
		"""
	else:
		message = f"❌ API Error: {weather['cod']} - {weather['message']}"
	
	bot.send_message(uuid, message)


def deemojify(text):
	import re
	regrex_pattern = re.compile(pattern = "["
		u"\U0001F600-\U0001F64F"  # emoticons
		u"\U0001F300-\U0001F5FF"  # symbols & pictographs
		u"\U0001F680-\U0001F6FF"  # transport & map symbols
		u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
								"]+", flags = re.UNICODE)
	return regrex_pattern.sub(r'',text)

@bot.message_handler(commands=['start'])
def welcome(message):
	uuid = message.chat.id

	st = "SELECT * FROM wb_users WHERE tg_id = %s"
	vals = [uuid]
	db.execute(st, vals)
	res = db.fetchall()
		

	if (res == []):
		bot.send_message(uuid, "Здравствуйте! Для продолжения отправьте название своего города или своё местоположение")

		st = "INSERT INTO wb_users (tg_id, screen) VALUES (%s, %s)"
		db.execute(st, [uuid, 1])
		confirm()
	
	else:
		if check_active(uuid):
			if get_screen(uuid) == 0:
				send_weather(uuid)
			else:
				send_idk(uuid)

@bot.message_handler(content_types=['location'])
def lalala(message):
	uuid = message.chat.id
	if check_active(uuid):
		if (get_screen(uuid) == 1):
			set_location(uuid, message.location)
		

@bot.message_handler(commands=['deactivate'])
def welcome(message):
	uuid = message.chat.id


	st = "UPDATE `wb_users` SET `active` = false, `screen` = 0 WHERE `tg_id` = %s"
	vals = [uuid]
	db.execute(st, vals)
	confirm()

	res = db.fetchall()

	bot.send_message(uuid, f"✅ Успешно")

@bot.message_handler(commands=['activate'])
def welcome(message):
	uuid = message.chat.id

	st = "UPDATE `wb_users` SET `active` = true, `screen` = 0 WHERE `tg_id` = %s"
	vals = [uuid]
	db.execute(st, vals)
	confirm()

	res = db.fetchall()

	bot.send_message(uuid, f"✅ Успешно")

@bot.message_handler(commands=['setlocation'])
def welcome(message):
	uuid = message.chat.id
	if check_active(uuid):
		st = "UPDATE wb_users SET screen = 1 WHERE tg_id = %s"
		vals = [uuid]
		db.execute(st, vals)
		confirm()

		bot.send_message(uuid, "Отправьте новое местоположение")


@bot.message_handler(content_types=['text'])
def lalala(message):
	uuid = message.chat.id
	if check_active(uuid):
		if (get_screen(uuid) == 1):
			set_city(uuid, deemojify(message.text))
		else:
			send_idk(uuid)


bot.polling(none_stop=True)

