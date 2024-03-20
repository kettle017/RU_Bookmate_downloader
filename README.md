# RU_Bookmate_downloader
Для работы скрипта требуется client_token.
<h2 align="left">Действия для получения токена:</h2>
Перейти по ссылке: https://oauth.yandex.ru/authorize?response_type=token&client_id=4483e97bab6e486a9822973109a14d05

Авторизоваться в аккаунт Яндекс

На странице "Авторизация в приложении Букмейт не удалась" скопировать токен после access_token= и до &.</h3>
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/188556ef-4adf-4621-bd79-6c8fcfb216fd/>

<h2 align="left">Настройка скрипта и установка зависимостей:</h2>
Установка зависимостей:
<h3 align="left"><pre>pip install httpx pillow </pre></h3>
Установка client_token:
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/5ee6807e-9c68-4ffe-859e-bf192aa38f14/>

<h2 align="left">Примеры запуска скрипта:</h2>
1)Скачать аудиокнигу с ID в максимальном качестве
<h3 align="left"><pre>python RUBookmatedownloader.py --maxbitrate True --audiobookid ID</pre></h3>
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/de670e55-4e60-4f5d-a7ee-2fc211d086d8/>
2)Скачать аудиокнигу с ID в обычном качестве
<h3 align="left"><pre>python RUBookmatedownloader.py --audiobookid ID</pre></h3>
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/7631e8cc-e625-40c0-b7ef-a08ccf10449a/>
3)Скачать книгу с ID
<h3 align="left"><pre>python RUBookmatedownloader.py --textbookid ID</pre></h3>
<img src=(https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/d105a7a2-a3d8-4a23-9b3d-1b0e8cfc64e0/> 
4)Скачать комикс с ID
<h3 align="left"><pre>python RUBookmatedownloader.py --comicbookid ID</pre></h3>
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/9f50377e-55da-4d3a-830e-32e68b3ea847/>
