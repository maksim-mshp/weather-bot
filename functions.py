import requests
import json
from config import *

def deemojify(text):
	import re
	regrex_pattern = re.compile(pattern = "["
		u"\U0001F600-\U0001F64F"  # emoticons
		u"\U0001F300-\U0001F5FF"  # symbols & pictographs
		u"\U0001F680-\U0001F6FF"  # transport & map symbols
		u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
								"]+", flags = re.UNICODE)
	return regrex_pattern.sub(r'',text)

def average_list(list):
	return sum(list) / len(list)

def average_weather(api_data):
	av_temp_list = []
	av_feels_list = []
	av_humidity_list = []

	av_temp_list.append(api_data['current']['temp'])
	av_feels_list.append(api_data['current']['feels_like'])
	av_humidity_list.append(api_data['current']['humidity'])

	for idx in range(11):
		av_temp_list.append(api_data['hourly'][idx]['temp'])
		av_feels_list.append(api_data['hourly'][idx]['feels_like'])
		av_humidity_list.append(api_data['hourly'][idx]['humidity'])

	result = (
		int(average_list(av_temp_list)),
		int(average_list(av_feels_list)),
		int(average_list(av_humidity_list))
	)

	return result

def get_weather_description(api_data):
	umbrella = False

	# Определяем дождь
	max_rain_wcode = '000'
	max_rain_description = -1
	add_code = '000'
	add_description = -1
	snow = False
	api_data['hourly'].insert(0, api_data['current'])
	for idx in range(12):
		wcode = str(api_data['hourly'][idx]['weather'][0]['id'])
		wdesc = api_data['hourly'][idx]['weather'][0]['description']

		if (wcode == '615' or wcode == '616'):
			max_rain_wcode = wcode
			max_rain_description = wdesc
			snow = True
			umbrella = True
			break
		
		if (wcode[0] == '2' or wcode[0] == '3' or wcode[0] == '5'):
			umbrella = True
			max_rain_wcode = wcode
			max_rain_description = wdesc

		if (wcode[0] == '6'):
			snow = True
			add_code = wcode
			add_description = wdesc
			break

			if (int(wcode) > int(add_code)):
				add_code = wcode
				add_description = wdesc
			else:
				if (add_code[0] != '6'):
					add_code = wcode
					add_description = wdesc
		else:
			if (wcode[0] == '7'):
				if (int(wcode) > int(add_code)):
					add_code = wcode
					add_description = wdesc
			else:
				if (add_code[0] != '7'):
					add_code = wcode
					add_description = wdesc
				else:
					if (add_code[0] == '8'):
						if (int(wcode) > int(add_code)):
							add_code = wcode
							add_description = wdesc

	if (max_rain_description == -1):
		res_description = add_description
	else:
		res_description = max_rain_description

	return (res_description, umbrella, snow)

def get_clothes(temp, feels_like):
	aver = av_temp = int((temp + feels_like) / 2)

	if (aver <= -20):
		return (1, True, 0, 0, 0)
	elif (-20 < aver <= -10):
		return (2, True, 1, 0, 0)
	elif (-10 < aver <= 5):
		return (3, True, 2, 1, 1)
	elif (5 < aver <= 15):
		return (4, False, 3, 1, 2)
	elif (15 < aver <= 20):
		return (0, False, 4, 1, 3)
	else:
		return (5, False, 5, 2, 3)

def get_img_url(temp, feels_like, rain, snow):
	av_temp = int((temp + feels_like) / 2)
	link = 'https://maksim.cherny.sh/weather_bot_images/'

	if (snow):
		link += '28.jpg'
		sourse = 'https://unsplash.com/photos/5CqcTSl7UH0'
	elif (rain):
		link += '27.jpg'
		sourse = 'https://unsplash.com/photos/tjbXOTqM0U8'
	else:
		if (av_temp <= -20):
			link += '24.jpg'
			sourse = 'https://unsplash.com/photos/9KAnqm0mTxc'
		elif (-20 < av_temp <= -10):
			link += '25.jpg'
			sourse = 'https://unsplash.com/photos/i69IbnCdxRs'
		elif (-10 < av_temp <= 5):
			link += '26.jpg'
			sourse = 'https://unsplash.com/photos/Lss2BdwBKho'
		elif (5 < av_temp <= 15):
			link += '23.jpg'
			sourse = 'https://unsplash.com/photos/MrETbReEVjw'
		elif (15 < av_temp <= 20):
			link += '22.jpg'
			sourse = 'https://unsplash.com/photos/8wJ5XMpepG8'
		else:
			link += '21.jpg'
			sourse = 'https://unsplash.com/photos/NDCy2-9JhUs'

	return (link, sourse)

def get_msg_text(data, snow):
	clothes_desc = []

	text = f"<u><b>Погода:</b></u> сегодня будет {data['weather']['description']}, "
	text += f"{data['weather']['temp']} °C, ощущается как {data['weather']['feels_like']} °C. "
	text += f"Влажность составит {data['weather']['humidity']}%.\n\n"
	img_data = get_img_url(data['weather']['temp'], data['weather']['feels_like'], data['clothes']['umbrella'], snow)
	img_url = img_data[0]
	text += f"<a href='{img_url}'>&#8205;</a>"

	headdress_d = {
		1: 'тёплую шапку',
		2: 'зимнюю шапку',
		3: 'шапку',
		4: 'шапку (можно без неё)',
		5: 'кепку'
	}

	outerwear_d = {
		0: 'очень тёплую куртку',
		1: 'зимнюю куртку',
		2: 'лёгкую куртку',
		3: 'ветровку или худи',
		4: 'худи',
		5: 'футболку'
	}

	pants_d = {
		0: 'тёплые штаны',
		1: 'джинсы',
		2: 'шорты',
	}

	shoes_d = {
		0: 'сапоги',
		1: 'тёплые ботинки',
		2: 'ботинки или кроссовки',
		3: 'кроссовки',
	}

	try:
		clothes_desc.append(headdress_d[data['clothes']['headdress']])
	except KeyError as e:
		pass

	if (data['clothes']['sweater']):
		clothes_desc.append('свитер')

	try:
		clothes_desc.append(outerwear_d[data['clothes']['outerwear']])
	except KeyError as e:
		pass

	try:
		clothes_desc.append(pants_d[data['clothes']['pants']])
	except KeyError as e:
		pass

	try:
		clothes_desc.append(shoes_d[data['clothes']['shoes']])
	except KeyError as e:
		pass

	if (data['clothes']['umbrella']):
		clothes_desc.append('взять с собой зонтик или дождевик')

	text += "<u><b>Сегодня стоит надеть</b></u> " + ', '.join(clothes_desc[:-2]) + ', ' + clothes_desc[-2] + ' и ' + clothes_desc[-1]
	text += f"\n\nИсточник картинки: <a href='{img_data[1]}'>Unsplash</a>"
	return text

def generate_message(lat, lon):
	url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&units=metric&lang=ru&exclude=minutely,daily,alerts&appid={weather_token}'
	response = requests.get(url)
	api_data = json.loads(response.text)

	average_data = {
		'weather': {
			'temp': -1,
			'feels_like': -1,
			'humidity': -1,
			'description': '',
		}, 
		'clothes': {
			# 0 - ничего, 1 - теплая шапка, 2 - шапка зимняя, 3 - шапка, 4 - шапка (можно и без неё), 5 - кепка
			'headdress': -1, 
			'sweater': False,
			# 0 - очень теплая, 1 - зимняя, 2 - ветровка, 3 - ветровка/худи, 4 - худи, 5 - футболка
			'outerwear': -1,
			# 0 - теплые, 1 - джинсы, 2 - шорты
			'pants': -1,
			# 0 - сапоги, 1 - теплые ботинки, 2 - ботинки/кроссовки, 3 - кроссовки
			'shoes': -1,
			'umbrella': False
		}
	}

	# Средние значения
	av = average_weather(api_data)
	average_data['weather']['temp'] = av[0]
	average_data['weather']['feels_like'] = av[1]
	average_data['weather']['humidity'] = av[2]

	weather_desc = get_weather_description(api_data)
	average_data['weather']['description'] = weather_desc[0]
	average_data['clothes']['umbrella'] = weather_desc[1]

	clothes = get_clothes(av[0], av[1])

	average_data['clothes']['headdress'] = clothes[0]
	average_data['clothes']['sweater'] = clothes[1]
	average_data['clothes']['outerwear'] = clothes[2]
	average_data['clothes']['pants'] = clothes[3]
	average_data['clothes']['shoes'] = clothes[4]


	return get_msg_text(average_data, weather_desc[2])

def get_clothes_description(c_type, c_thing):
	types = ('головной убор', 'верхняя одежда', 'верхняя одежда', 'штаны', 'обувь')
	clothes = (
		{
			1: 'тёплая шапка',
			2: 'зимняя шапка',
			3: 'шапка',
			4: 'шапка (можно и без неё)',
			5: 'кепка'
		}, {
			1: 'свитер'
		}, {
			0: 'очень тёплая куртка',
			1: 'зимняя куртка',
			2: 'ветровка',
			3: 'ветровка или худи',
			4: 'худи',
			5: 'футболка'
		}, {
			0: 'тёплые штаны',
			1: 'джинсы',
			2: 'шорты',
		}, {
			0: 'сапоги',
			1: 'тёплые ботинки',
			2: 'ботинки или кроссовки',
			3: 'кроссовки',
		}
	)
	
	d_type = 'неизвестно'
	d_thing = 'неизвестно'
	
	try:
		d_type = types[c_type]
	except IndexError:
		pass

	try:
		try:
			d_thing = clothes[c_type][c_thing]
		except IndexError:
			pass
	except KeyError:
		pass

	return (d_type, d_thing)



