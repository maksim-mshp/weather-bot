# Telegram-бот «Одевайся по погоде»

Мессенджер Telegram в январе 2021 года стал самым скачиваемым приложением в мире и достигло 63 млн, обогнав TikTok и WhatsApp. Об этом свидетельствуют данные компании Sensor Tower, занимающейся аналитикой цифровых рынков. Именно поэтому Telegram-боты пользуются огромной популярностью у всевозможных компаний. Чат-боты уже используются в самых различных сферах: можно вызвать такси, заказать еду или найти авиабилет.

Цель проекта – разработать чат-бота для подбора одежды в зависимости от погоды на улице. Выбор того, что надеть – это повседневная задача каждого человека, у которого много одежды. Проект состоит из чат-бота и базы данных MySQL для хранения данных пользователей. Чат-бот разработан на языке программирования Python. 

Запуск программы происходит через crontab
```
0 * * * * python3 main.py >> output.log 2>&1
* * * * * python3 schedule.py >> schedule.log 2>&1
```