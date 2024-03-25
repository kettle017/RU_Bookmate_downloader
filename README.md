# RU_Bookmate_downloader
<h2 align="left">Установка зависимостей:</h2>
<h3 align="left"><pre>pip install httpx[http2] pillow pywebview reportlab ebooklib BeautifulSoup4</pre></h3>
<h2 align="left">Авторизоваться в аккаунт Яндекс</h2>
<img src=https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/bb3453eb-5d44-4410-b2e1-05193c88333e/>

<h2 align="left">Примеры запуска скрипта:</h2>
Для определения нужного флага смотрите на URL, в нем всегда есть полдсказка!
1)Скачать аудиокнигу с ID в максимальном качестве
<h3 align="left"><pre>python RUBookmatedownloader.py --maxbitrate True --audiobooks ID</pre></h3>
2)Скачать аудиокнигу с ID в обычном качестве
<h3 align="left"><pre>python RUBookmatedownloader.py --audiobooks ID</pre></h3>
3)Скачать книгу с ID
<h3 align="left"><pre>python RUBookmatedownloader.py --books ID</pre></h3>
4)Скачать комикс с ID
<h3 align="left"><pre>python RUBookmatedownloader.py --comicbooks ID</pre></h3>
5)Скачать серию текстовых книг
<h3 align="left"><pre>python RUBookmatedownloader.py --serials ID</pre></h3>
5)Скачать серию аудиокниг
<h3 align="left"><pre>python RUBookmatedownloader.py --series ID</pre></h3>