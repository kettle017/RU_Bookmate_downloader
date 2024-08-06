# RU_Bookmate_downloader
## Установка зависимостей:
`pip install -r requirements.txt`

## Авторизоваться в аккаунт Яндекс
![Авторизация](https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/bb3453eb-5d44-4410-b2e1-05193c88333e)

## Примеры запуска скрипта:
Для определения нужного флага смотрите на URL, в нем всегда есть подсказка: https://bookmate.ru/<флаг>/<id>\
1. Скачать аудиокнигу в максимальном качестве:\
`python RUBookmatedownloader.py --audiobooks <id> --maxbitrate True`
3. Скачать аудиокнигу в обычном качестве:\
`python RUBookmatedownloader.py --audiobooks <id>`
4. Скачать текстовую книгу:\
`python RUBookmatedownloader.py --books <id>`
5. Скачать комикс:\
`python RUBookmatedownloader.py --comicbooks <id>`
6. Скачать текстовую книгу, разбитую на несколько частей:\
`python RUBookmatedownloader.py --serials <id>`
5. Скачать серию текстовых книг, аудиокниг или комиксов:\
`python RUBookmatedownloader.py --series <id>`
