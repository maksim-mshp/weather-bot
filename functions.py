import requests
import json
from config import *

def get_weather_city(city):
	url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={weather_token}&lang=ru'
	response = requests.get(url)

	return json.loads(response.text)
	
def get_weather_location(lat, lon):
	url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={weather_token}&lang=ru'
	response = requests.get(url)

	return json.loads(response.text)

def get_forecast_city(city):
	url = f'http://api.openweathermap.org/forecast/2.5/forecast?q={city}&units=metric&appid={weather_token}&lang=ru'
	response = requests.get(url)

	return json.loads(response.text)

def get_forecast_location(lat, lon):
	url = f'http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={weather_token}&lang=ru'
	response = requests.get(url)

	return json.loads(response.text)