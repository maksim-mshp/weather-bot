from flask import *
import requests
from markdown2 import markdown
import mysql.connector as sql
import sys
import logging 
sys.path.append('/var/www/maksim/data/bots/weather/')
from config import *
from functions import *

app = Flask(__name__, static_folder="assets")
logging.basicConfig(filename="log.log", level=logging.INFO)
def check_token(data, db):
	if ('token' in data):
		token = data['token']
		db.execute('SELECT user FROM wb_api_tokens WHERE token = %s', [token])
		user = db.fetchall()
		if (user != []):
			user = user[0][0]
			db.execute('SELECT active FROM wb_users WHERE tg_id = %s', [user])
			if (db.fetchall()[0][0]):
				return (200, 'OK', user)
			else:
				return (402, 'Account deactivated')
	
	return (401, 'Wrong API token')

@app.route('/')
def index():
	# return 'test' 
	return render_template('index.html')

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
	connection = sql.connect(
		user = db_config['user'],
		password = db_config['password'],
		unix_socket = db_config['unix_socket'],
		database = db_config['database'],
		autocommit = True
	)
	db = connection.cursor()

	res = {
		'status': {
			'code': -1,
			'description': -1
		}
	}

	check = check_token(request.values, db)
	res['status']['code'] = check[0]
	res['status']['description'] = check[1]

	if (check[0] == 200):
		user = check[2]
		db.execute('SELECT active, lat, lon FROM wb_users WHERE tg_id = %s', [user])
		db_res = db.fetchall()[0]

		lat = db_res[1]
		lon = db_res[2]
		res.update([('recommendations', {
			'general': -1,
			'personal': -1
		})])
		res['recommendations']['general'] = generate_message_api(lat, lon, db, user)
		res['recommendations']['personal'] = get_user_clothes_api(res['recommendations']['general'], user, db)
		res.update([('weather', res['recommendations']['general']['weather'])])
		res['recommendations']['general'] = res['recommendations']['general']['clothes']


	return jsonify(res) 

@app.route('/add_clothes', methods=['GET', 'POST'])
def add_clothes():
	connection = sql.connect(
		user = db_config['user'],
		password = db_config['password'],
		unix_socket = db_config['unix_socket'],
		database = db_config['database'],
		autocommit = True
	)
	db = connection.cursor()

	res = {
		'status': {
			'code': -1,
			'description': -1
		}
	}

	check = check_token(request.values, db)
	res['status']['code'] = check[0]
	res['status']['description'] = check[1]

	def update_res(code, description):
		nonlocal res
		res['status']['code'] = code
		res['status']['description'] = description

	if (check[0] == 200):
		user = check[2]
		
		if ('title' in request.values):
			if ('type' in request.values):
				if ('thing' in request.values):
					c_type = request.values['type'].strip()
					c_thing = request.values['thing'].strip()
					c_title = request.values['title'].strip()

					if (c_title == ''):
						update_res(403, 'Wrong title')
						return jsonify(res)

					types = ('headdress', 'outerwear', 'pants', 'shoes')
					things = (
						('warm', 'winter', 'hat', 'optional', 'cap'),
						('warm', 'winter', 'coat', 'sweater', 'selectable', 'hoodie', 't-shirt'),
						('warm', 'jeans', 'shorts'),
						('warm', 'boots', 'selectable', 'sneakers')
					)
					try:
						c_type = types.index(c_type)
						try:
							c_thing = things[c_type].index(c_thing)

							if (c_type == 1 and c_thing == 3):
								c_thing = 1
							else:
								c_type += 1

							st = "INSERT INTO wb_clothes (user, name, type, thing) VALUES (%s, %s, %s, %s)"
							vals = [user, c_title, c_type, c_thing]
							db.execute(st, vals)
						except:
							update_res(405, 'Wrong thing')
					except:
						update_res(404, 'Wrong type')
				else:
					update_res(405, 'Wrong thing')
			else:
				update_res(404, 'Wrong type')
		else:
			update_res(403, 'Wrong title')


	return jsonify(res)

@app.route('/clothes', methods=['GET', 'POST'])
def clothes():
	connection = sql.connect(
		user = db_config['user'],
		password = db_config['password'],
		unix_socket = db_config['unix_socket'],
		database = db_config['database'],
		autocommit = True
	)
	db = connection.cursor()

	res = {
		'status': {
			'code': -1,
			'description': -1
		}
	}

	check = check_token(request.values, db)
	res['status']['code'] = check[0]
	res['status']['description'] = check[1]

	if (check[0] == 200):
		user = check[2]
		res.update([('clothes', [])])

		db.execute('SELECT id, name, type, thing FROM wb_clothes WHERE user = %s', [user])
		db_res = db.fetchall()
		# res['clothes'] = db_res
		for i in db_res:
			if (i[2] != None and i[3] != None):
				res['clothes'].append(
					{
						'id': i[0],
						'title': i[1],
						'type': get_clothes_description(i[2], i[3])[0],
						'thing': get_clothes_description(i[2], i[3])[1]
					}
					
				)


	return jsonify(res)

@app.route('/edit_clothes', methods=['GET', 'POST'])
def edit_clothes():
	connection = sql.connect(
		user = db_config['user'],
		password = db_config['password'],
		unix_socket = db_config['unix_socket'],
		database = db_config['database'],
		autocommit = True
	)
	db = connection.cursor()

	res = {
		'status': {
			'code': -1,
			'description': -1
		}
	}

	def update_res(code, description):
		nonlocal res
		res['status']['code'] = code
		res['status']['description'] = description
		res['status']['description'] = description

	check = check_token(request.values, db)
	res['status']['code'] = check[0]
	res['status']['description'] = check[1]

	if (check[0] == 200):
		user = check[2]
		logging.info(user)
		if ('id' in request.values):
			c_id = request.values['id'].strip()
			logging.info(c_id)
			if (c_id == ''):
				res['status']['code'] = 406
				res['status']['description'] = 'Wrong id'
			else:
				tmp = [False, False, False]
				if ('title' in request.values):
					c_title = request.values['title'].strip()
					if (c_title != ''):
						tmp[0] = True

				if ('type' in request.values):
					c_type = request.values['type'].strip()
					if (c_type != ''):
						tmp[1] = True
				
				if ('thing' in request.values):
					c_thing = request.values['thing'].strip()
					if (c_thing != ''):
						tmp[2] = True

				# logging.info(c_title)

				if (tmp == [False, False, False]):
					update_res(407, 'Nothing to edit')
				elif (tmp == [False, True, False]):
					update_res(405, 'Wrong thing')
				elif (tmp == [False, False, True]):
					update_res(404, 'Wrong type')
				else:
					logging.info('1')
					st = "SELECT user FROM wb_clothes WHERE id = %s"
					db.execute(st, [c_id])
					db_res = db.fetchall()
					if (db_res == [] or db_res[0][0] != user):
						res['status']['code'] = 406
						res['status']['description'] = 'Wrong id'
					else:
						logging.info('2')
						if (tmp[0]):
							st = "UPDATE wb_clothes SET name = %s WHERE id = %s AND user = %s"
							vals = [c_title, c_id, user]
							db.execute(st, vals)
							logging.info('name edited')

						if (tmp[1]):
							types = ('headdress', 'outerwear', 'pants', 'shoes')
							things = (
								('warm', 'winter', 'hat', 'optional', 'cap'),
								('warm', 'winter', 'coat', 'sweater', 'selectable', 'hoodie', 't-shirt'),
								('warm', 'jeans', 'shorts'),
								('warm', 'boots', 'selectable', 'sneakers')
							)
							try:
								c_type = types.index(c_type)
								try:
									c_thing = things[c_type].index(c_thing)

									if (c_type == 1 and c_thing == 3):
										c_thing = 1
									else:
										c_type += 1
		  
									st = "UPDATE wb_clothes SET type = %s, thing = %s WHERE id = %s AND user = %s"
									vals = [c_type, c_thing, int(c_id), user] 
									db.execute(st, vals)
								except:
									update_res(405, 'Wrong thing')
							except:
								update_res(404, 'Wrong type')

		else:
			res['status']['code'] = 406
			res['status']['description'] = 'Wrong id'

	return jsonify(res)

@app.route('/remove_clothes', methods=['GET', 'POST'])
def remove_clothes():
	connection = sql.connect(
		user = db_config['user'],
		password = db_config['password'],
		unix_socket = db_config['unix_socket'],
		database = db_config['database'],
		autocommit = True
	)
	db = connection.cursor()

	res = {
		'status': {
			'code': -1,
			'description': -1
		}
	}

	check = check_token(request.values, db)
	res['status']['code'] = check[0]
	res['status']['description'] = check[1]

	if (check[0] == 200):
		user = check[2]
		if ('id' in request.values):
			c_id = request.values['id'].strip()
			if (c_id == ''):
				res['status']['code'] = 406
				res['status']['description'] = 'Wrong id'
			else:
				st = "SELECT user FROM wb_clothes WHERE id = %s"
				db.execute(st, [c_id])
				db_res = db.fetchall()
				if (db_res == [] or db_res[0][0] != user):
					res['status']['code'] = 407
					res['status']['description'] = 'Wrong id'
				else:
					st = 'DELETE FROM wb_clothes WHERE id = %s AND user = %s'
					vals = [c_id, user]
					db.execute(st, vals)
		else:
			res['status']['code'] = 406
			res['status']['description'] = 'Wrong id'
		st = 'DELETE FROM wb_clothes WHERE id = %s'

	return jsonify(res)

@app.route('/set_location', methods=['GET', 'POST'])
def set_location():
	from geopy.geocoders import Nominatim as geolocation
	from re import fullmatch as check_re
	connection = sql.connect(
		user = db_config['user'],
		password = db_config['password'],
		unix_socket = db_config['unix_socket'],
		database = db_config['database'],
		autocommit = True
	)
	db = connection.cursor()

	res = {
		'status': {
			'code': -1,
			'description': -1
		}
	}

	check = check_token(request.values, db)
	res['status']['code'] = check[0]
	res['status']['description'] = check[1]

	if (check[0] == 200):
		user = check[2]
		if ('city' in request.values):
			geo = geolocation(user_agent="wbot")
			tmp_location = geo.geocode(request.values['city'])
			try:
				lat = tmp_location.latitude
				lon = tmp_location.longitude
	
				st = "UPDATE wb_users SET lat = %s, lon = %s WHERE tg_id = %s"
				vals = [lat, lon, user]
				db.execute(st, vals)
			except AttributeError:
				res['status']['code'] = 408
				res['status']['description'] = 'Wrong city'
		else:
			if ('lat' in request.values):
				if ('lon' in request.values):
					lat = request.values['lat'].strip()
					lon = request.values['lon'].strip()
					if (check_re(r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$", lat + ', ' + lon)):
						st = "UPDATE wb_users SET lat = %s, lon = %s WHERE tg_id = %s"
						vals = [lat, lon, user]
						db.execute(st, vals)
					else:
						res['status']['code'] = 410
						res['status']['description'] = 'Wrong coordinates'
				else:
					res['status']['code'] = 410
					res['status']['description'] = 'Expected longitude'
			else:
				res['status']['code'] = 409
				res['status']['description'] = 'Expected latitude'

	return jsonify(res)

@app.route('/activate', methods=['GET', 'POST'])
def activate():
	connection = sql.connect(
		user = db_config['user'],
		password = db_config['password'],
		unix_socket = db_config['unix_socket'],
		database = db_config['database'],
		autocommit = True
	)
	db = connection.cursor()

	res = {
		'status': {
			'code': -1,
			'description': -1
		}
	}
 
	if ('token' in request.values):
		token = request.values['token']
		db.execute('SELECT user FROM wb_api_tokens WHERE token = %s', [token])
		user = db.fetchall()
		if (user != []):
			res['status']['code'] = 200
			res['status']['description'] = 'OK'
			user = user[0][0]

			db.execute("UPDATE wb_users SET `active` = true, `screen` = 0 WHERE tg_id = %s", [user])
		else:
			res['status']['code'] = 401
			res['status']['description'] = 'Wrong API token'		
	else:
		res['status']['code'] = 401
		res['status']['description'] = 'Wrong API token'
	return jsonify(res)


@app.route('/deactivate', methods=['GET', 'POST'])
def deactivate():
	connection = sql.connect(
		user = db_config['user'],
		password = db_config['password'],
		unix_socket = db_config['unix_socket'],
		database = db_config['database'],
		autocommit = True
	)
	db = connection.cursor()

	res = {
		'status': {
			'code': -1,
			'description': -1
		}
	}
 
	if ('token' in request.values):
		token = request.values['token']
		db.execute('SELECT user FROM wb_api_tokens WHERE token = %s', [token])
		user = db.fetchall()
		if (user != []):
			res['status']['code'] = 200
			res['status']['description'] = 'OK'
			user = user[0][0]

			db.execute("UPDATE wb_users SET `active` = false, `screen` = 0 WHERE tg_id = %s", [user])
		else:
			res['status']['code'] = 401
			res['status']['description'] = 'Wrong API token'		
	else:
		res['status']['code'] = 401
		res['status']['description'] = 'Wrong API token'
	return jsonify(res) 
	

#adding variables
@app.route('/user/<username>')
def show_user(username):
	#returns the username
	return 'Username: %s' % username  