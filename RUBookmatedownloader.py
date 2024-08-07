import asyncio
import zipfile
import random
import os
import time
import re
import sys
import warnings
import json
import argparse
import shutil
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import httpx
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

UA = {
    1: "Samsung/Galaxy_A51 Android/12 Bookmate/3.7.3",
    2: "Huawei/P40_Lite Android/11 Bookmate/3.7.3",
    3: "OnePlus/Nord_N10 Android/10 Bookmate/3.7.3"
    # 4: "Google/Pixel_4a Android/9 Bookmate/3.7.3",
    # 5: "Oppo/Reno_4 Android/8 Bookmate/3.7.3",
    # 6: "Xiaomi/Redmi_Note_9 Android/10 Bookmate/3.7.3",
    # 7: "Motorola/Moto_G_Power Android/10 Bookmate/3.7.3",
    # 8: "Sony/Xperia_10 Android/10 Bookmate/3.7.3",
    # 9: "LG/Velvet Android/10 Bookmate/3.7.3",
    # 10: "Realme/6_Pro Android/10 Bookmate/3.7.3",
}
HEADERS = {
    'app-user-agent': UA[random.randint(1, 3)],
    'mcc': '',
    'mnc': '',
    'imei': '',
    'subscription-country': '',
    'app-locale': '',
    'bookmate-version': '',
    'bookmate-websocket-version': '',
    'device-idfa': '',
    'onyx-preinstall': 'false',
    'auth-token': '',
    'accept-encoding': '',
    'user-agent': ''
}
URLS = {
    "book": {
        "infoUrl": "https://api.bookmate.yandex.net/api/v5/books/{uuid}",
        "contentUrl": "https://api.bookmate.yandex.net/api/v5/books/{uuid}/content/v4"
    },
    "audiobook": {
        "infoUrl": "https://api.bookmate.yandex.net/api/v5/audiobooks/{uuid}",
        "contentUrl": "https://api.bookmate.yandex.net/api/v5/audiobooks/{uuid}/playlists.json"
    },
    "comicbook": {
        "infoUrl": "https://api.bookmate.yandex.net/api/v5/comicbooks/{uuid}",
        "contentUrl": "https://api.bookmate.yandex.net/api/v5/comicbooks/{uuid}/metadata.json"
    },
    "serial": {
        "infoUrl": "https://api.bookmate.yandex.net/api/v5/books/{uuid}",
        "contentUrl": "https://api.bookmate.yandex.net/api/v5/books/{uuid}/episodes"
    },
    "series": {
        "infoUrl": "https://api.bookmate.yandex.net/api/v5/series/{uuid}",
        "contentUrl": "https://api.bookmate.yandex.net/api/v5/series/{uuid}/parts"
    }
}


def get_auth_token():
    if os.path.isfile("token.txt"):
        with open("token.txt", encoding='utf-8') as file:
            return file.read()
    if HEADERS['auth-token']:
        return HEADERS['auth-token']
    auth_token = run_auth_webview()
    with open("token.txt", "w", encoding='utf-8') as file:
        file.write(auth_token)
    return auth_token


def run_auth_webview():
    import webview
    import urllib.parse

    def on_loaded(window):
        if "yx4483e97bab6e486a9822973109a14d05.oauth.yandex.ru" in urllib.parse.urlparse(window.get_current_url()).netloc:
            url = urllib.parse.urlparse(window.get_current_url())
            window.auth_token = urllib.parse.parse_qs(url.fragment)[
                'access_token'][0]
            window.destroy()

    window = webview.create_window(
        'Вход в аккаунт', 'https://oauth.yandex.ru/authorize?response_type=token&client_id=4483e97bab6e486a9822973109a14d05')
    window.events.loaded += on_loaded
    window.auth_token = None
    webview.start()
    return window.auth_token


def replace_forbidden_chars(filename):
    forbidden_chars = '\\/:*?"<>|'
    chars = re.escape(forbidden_chars)
    return re.sub(f'[{chars}]', '', filename)


async def download_file(url, file_path):
    is_download = False
    count = 0
    while not is_download:
        async with httpx.AsyncClient(http2=True, verify=False) as client:
            response = await client.get(url, headers=HEADERS, timeout=None)
            if response.status_code == 200:
                is_download = True
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                print(f"File downloaded successfully to {file_path}")
            elif response.is_redirect:
                response = await client.get(response.next_request.url)
                if response.status_code == 200:
                    is_download = True
                    with open(file_path, 'wb') as file:
                        file.write(response.content)
                    print(f"File downloaded successfully to {file_path}")
            else:
                print(
                    f"Failed to download file. Status code: {response.status_code}")
                count += 1
                if count == 3:
                    print(
                        "Failed to download the file check if the id is correct or try again later")
                    sys.exit()
                time.sleep(5)


async def send_request(url):
    is_download = False
    count = 0
    while not is_download:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=HEADERS, timeout=None)
            if response.status_code == 200:
                is_download = True
                return response
            else:
                print(
                    f"Failed to send request. Status code: {response.status_code}")
                count += 1
                if count == 3:
                    print(
                        "Failed to download the file check if the id is correct or try again later")
                    sys.exit()
                time.sleep(5)


def create_pdf_from_images(images_folder, output_pdf):
    c = canvas.Canvas(output_pdf, pagesize=letter)
    width, height = letter

    images = filter(lambda file: file.endswith(".jpeg"), os.listdir(images_folder))

    for image in images:
        img_path = os.path.join(images_folder, image)
        with Image.open(img_path):
            c.drawImage(img_path, 0, 0, width, height)
            c.showPage()
        os.remove(img_path)
    c.save()
    print(f"File downloaded successfully to {output_pdf}")


def epub_to_fb2(epub_path, fb2_path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        book = epub.read_epub(epub_path)

    fb2_content = '<?xml version="1.0" encoding="UTF-8"?>\n<fb2 xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:l="http://www.w3.org/1999/xlink">\n<body>'
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content()
            soup = BeautifulSoup(content, 'html.parser')
            text_content = soup.get_text()
            fb2_content += f'<p>{text_content}</p>'

    fb2_content += '</body>\n</fb2>'

    with open(fb2_path, 'w', encoding='utf-8') as fb2_file:
        fb2_file.write(fb2_content)

    print(f"fb2 file save to {fb2_path}")


def get_resource_info(resource_type, uuid, series=''):
    info_url = URLS[resource_type]['infoUrl'].format(uuid=uuid)
    info = asyncio.run(send_request(info_url)).json()
    if info:
        picture_url = info[resource_type]["cover"]["large"]
        name = info[resource_type]["title"]
        name = replace_forbidden_chars(name)
        download_dir = f"mybooks/{'series' if series else resource_type}/{series}{name}/"
        path = f'{download_dir}{name}'
        os.makedirs(os.path.dirname(download_dir), exist_ok=True)
        asyncio.run(download_file(picture_url, f'{path}.jpeg'))
        with open(f"{path}.json", 'w', encoding='utf-8') as file:
            file.write(json.dumps(info, ensure_ascii=False))
        print(f"File downloaded successfully to {path}.json")
    return path


def get_resource_json(resource_type, uuid):
    url = URLS[resource_type]['contentUrl'].format(uuid=uuid)
    return asyncio.run(send_request(url)).json()


def download_book(uuid, series='', serial_path=None):
    path = serial_path if serial_path else get_resource_info(
        'book', uuid, series)
    asyncio.run(download_file(
        URLS['book']['contentUrl'].format(uuid=uuid), f'{path}.epub'))
    epub_to_fb2(f"{path}.epub", f"{path}.fb2")


def download_audiobook(uuid, series='', max_bitrate=False):
    path = get_resource_info('audiobook', uuid, series)
    resp = get_resource_json('audiobook', uuid)
    if resp:
        bitrate = 'max_bit_rate' if max_bitrate else 'min_bit_rate'
        json_data = resp['tracks']
        files = os.listdir(os.path.dirname(path))
        for track in json_data:
            name = f'Глава_{track["number"]+1}.m4a'
            if name not in files:
                download_url = track['offline'][bitrate]['url'].replace(".m3u8", ".m4a")
                asyncio.run(download_file(
                    download_url, f'{os.path.dirname(path)}/{name}'))


def download_comicbook(uuid, series=''):
    path = get_resource_info('comicbook', uuid, series)
    resp = get_resource_json('comicbook', uuid)
    if resp:
        download_url = resp["uris"]["zip"]
        asyncio.run(download_file(download_url, f'{path}.cbr'))
        with zipfile.ZipFile(f'{path}.cbr', 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(path))
        shutil.rmtree(os.path.dirname(path)+"/preview",
                      ignore_errors=False, onerror=None)
        create_pdf_from_images(os.path.dirname(path), f"{path}.pdf")


def download_serial(uuid):
    path = get_resource_info('book', uuid)
    resp = get_resource_json('serial', uuid)
    if resp:
        for episode_index, episode in enumerate(resp["episodes"]):
            name = f"{episode_index+1}. {episode['title']}"
            download_dir = f'{os.path.dirname(path)}/{name}'
            os.makedirs(download_dir, exist_ok=True)
            download_book(episode['uuid'],
                          serial_path=f'{download_dir}/{name}')


def download_series(uuid):
    path = get_resource_info('series', uuid)
    resp = get_resource_json('series', uuid)
    name = os.path.basename(path)
    print(name)
    for part_index, part in enumerate(resp['parts']):
        print(part['resource_type'], part['resource']['uuid'])
        func = FUNCTION_MAP[part['resource_type']]
        func(part['resource']['uuid'], f"{name}/{part_index+1}. ")


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("command", choices=FUNCTION_MAP.keys())
    argparser.add_argument("uuid")
    argparser.add_argument("--max_bitrate", action='store_false')
    args = argparser.parse_args()

    HEADERS['auth-token'] = get_auth_token()

    func = FUNCTION_MAP[args.command]
    if args.command == 'audiobook':
        func(args.uuid, max_bitrate=args.max_bitrate)
    else:
        func(args.uuid)


FUNCTION_MAP = {
    'book': download_book,
    'audiobook': download_audiobook,
    'comicbook': download_comicbook,
    'serial': download_serial,
    'series': download_series
}

if __name__ == "__main__":
    main()
