# RU_Bookmate_downloader
Для работы скрипта требуется client_token.
<h2 align="left">Действия для получения токена:</h2>
Перейти по ссылке: https://oauth.yandex.ru/authorize?response_type=token&client_id=4483e97bab6e486a9822973109a14d05

Авторизоваться в аккаунт Яндекс

На странице "Авторизация в приложении Букмейт не удалась" скопировать токен после access_token= и до &.</h3>
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/26156434-edcc-425b-bfeb-40a385ffb054)/>

<h2 align="left">Настройка скрипта и установка зависимостей:</h2>
Установка зависимостей:
<h3 align="left"><pre>pip install httpx pillow </pre></h3>
Установка client_token:
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/056728f0-2454-4064-a16a-2df1dfa2a2a6/>

<h2 align="left">Примеры запуска скрипта:</h2>
1)Скачать аудиокнигу с ID в максимальном качестве
<h3 align="left"><pre>python RUBookmatedownloader.py --maxbitrate True --audiobookid ID</pre></h3>
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/56018e1d-f751-42a7-8f92-905f4f22aa2e/>
2)Скачать аудиокнигу с ID в обычном качестве
<h3 align="left"><pre>python RUBookmatedownloader.py --audiobookid ID</pre></h3>
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/3cd63219-9339-4418-aeb7-2e575798bec7/>
3)Скачать книгу с ID
<h3 align="left"><pre>python RUBookmatedownloader.py --textbookid ID</pre></h3>
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/69f3abba-6662-4802-9b51-5e7d1b244c0c/> 
4)Скачать комикс с ID
<h3 align="left"><pre>python RUBookmatedownloader.py --comicbookid ID</pre></h3>
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/aa6319cf-f6e5-4e53-b733-a7ed2a7fe757/>
