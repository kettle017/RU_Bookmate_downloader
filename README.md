# RU_Bookmate_downloader

## 🚀 Быстрый запуск на Mac:

### 1. Подготовка среды:
```bash
# Создать виртуальное окружение
python3 -m venv venv

# Активировать окружение
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Установить FFmpeg (для обработки аудио)
brew install ffmpeg
```

### 2. Запуск скрипта:

#### Простой способ (рекомендуется):
```bash
# Использовать готовый launcher script
./run.sh audiobook <id>
./run.sh list-author <author_uuid>
./run.sh author <author_uuid>
```

#### Альтернативные способы:
```bash
# Использовать полный путь к Python
./venv/bin/python RUBookmatedownloader.py audiobook <id>

# Или после активации виртуального окружения:
source venv/bin/activate
python RUBookmatedownloader.py audiobook <id>
```

### 3. Проверка работы:
```bash
# Показать справку
./run.sh --help

# Показать список книг автора (например, Борис Акунин)
./run.sh list-author HhKS0YIj
```

## Авторизоваться в аккаунт Яндекс
![Авторизация](https://github.com/kettle017/RU_Bookmate_downloader/assets/37309120/bb3453eb-5d44-4410-b2e1-05193c88333e)

## Примеры запуска скрипта:
Для определения нужного флага смотрите на URL, в нем всегда есть подсказка: https://bookmate.ru/<флаг>/<id>\

### Основные команды:
1. Скачать аудиокнигу в максимальном качестве:\
`python RUBookmatedownloader.py audiobook <id> --max_bitrate`
2. Скачать аудиокнигу в обычном качестве:\
`python RUBookmatedownloader.py audiobook <id>`
3. Скачать аудиокнигу без объединения глав:\
`python RUBookmatedownloader.py audiobook <id> --no-merge`
4. Скачать аудиокнигу и сохранить отдельные главы после объединения:\
`python RUBookmatedownloader.py audiobook <id> --keep-chapters`
5. Показать список всех аудиокниг автора:\
`python RUBookmatedownloader.py list-author <author_uuid>`
6. Скачать все аудиокниги автора:\
`python RUBookmatedownloader.py author <author_uuid>`
7. Скачать все аудиокниги автора в максимальном качестве:\
`python RUBookmatedownloader.py author <author_uuid> --max_bitrate`
8. Скачать текстовую книгу:\
`python RUBookmatedownloader.py book <id>`
9. Скачать комикс:\
`python RUBookmatedownloader.py comicbook <id>`
10. Скачать текстовую книгу, разбитую на несколько частей:\
`python RUBookmatedownloader.py serial <id>`
11. Скачать серию текстовых книг, аудиокниг или комиксов:\
`python RUBookmatedownloader.py series <id>`

**Примечания:**
- UUID автора можно найти в профиле автора на Bookmate или в JSON-файле любой его книги
- При скачивании автора все аудиокниги сохраняются в папку `mybooks/series/Имя_Автора/`
- Используйте `list-author` для предварительного просмотра списка книг автора

### Объединение глав аудиокниг:
По умолчанию главы аудиокниг объединяются в один файл автоматически. Если вы скачали главы отдельно или хотите перезаписать существующую объединённую аудиокнигу:

1. Объединить одну аудиокнигу:\
`python merge_audiobook.py "путь/к/папке/аудиокниги"`
2. Объединить все аудиокниги в папке mybooks/audiobook/:\
`python merge_audiobook.py --batch`
3. Принудительно перезаписать существующие объединённые файлы:\
`python merge_audiobook.py --batch --force`
4. Сохранить отдельные главы после объединения:\
`python merge_audiobook.py --batch --keep-chapters`

**Примечание:** По умолчанию отдельные файлы глав удаляются после успешного объединения для экономии места. Используйте `--keep-chapters` чтобы сохранить их.
