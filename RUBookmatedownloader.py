import random
import os
import time
import sys
import warnings
import json
import argparse
import shutil
import collections.abc
collections.Iterable = collections.abc.Iterable
collections.Mapping = collections.abc.Mapping
collections.MutableSet = collections.abc.MutableSet
collections.MutableMapping = collections.abc.MutableMapping
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import httpx
import asyncio
import zipfile
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
headers = {
        'app-user-agent': UA[random.randint(1,3)],
        'mcc':'',
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

def get_auth_token():
    import webview
    import urllib.parse
    from time import sleep

    def get_current_url(window):
        global auth_token
        while "yx4483e97bab6e486a9822973109a14d05.oauth.yandex.ru" not in urllib.parse.urlparse(window.get_current_url()).netloc:
            pass
        url = urllib.parse.urlparse(window.get_current_url())
        auth_token = urllib.parse.parse_qs(url.fragment)['access_token'][0]
        window.destroy()
        return auth_token

    window = webview.create_window('Вход в аккаунт', 'https://oauth.yandex.ru/authorize?response_type=token&client_id=4483e97bab6e486a9822973109a14d05')
    webview.start(get_current_url, window)
    return auth_token

def replace_forbidden_chars(filename):
    forbidden_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    new_filename = filename

    for char in forbidden_chars:
        new_filename = new_filename.replace(char, ' ')

    return new_filename

async def download_file(url, file_path):
    is_download = False
    count = 0
    while(not is_download):
        async with httpx.AsyncClient(http2=True,verify=False) as client:
            response = await client.get(url,headers=headers,timeout=None)
            if response.status_code == 200:
                is_download = True
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                print(f"File downloaded successfully to {file_path}")
            elif (response.is_redirect):
                response = await client.get(response.next_request.url)
                if response.status_code == 200:
                    is_download = True
                    with open(file_path, 'wb') as file:
                        file.write(response.content)
                    print(f"File downloaded successfully to {file_path}")
            else:
                print(f"Failed to download file. Status code: {response.status_code}")
                count+=1
                if count == 3:
                    print("Failed to download the file check if the id is correct or try again later")
                    sys.exit()
                time.sleep(5)
            

async def send_request(url, headers):
    is_download = False
    count = 0
    while(not is_download):
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers,timeout=None)
            if response.status_code == 200:
                is_download = True
                return(response)
            else:
                print(f"Failed to send request. Status code: {response.status_code}")
                count+=1
                if count == 3:
                    print("Failed to download the file check if the id is correct or try again later")
                    sys.exit()
                time.sleep(5)
                
def create_pdf_from_images(images_folder, output_pdf):
    c = canvas.Canvas(output_pdf, pagesize=letter)
    width, height = letter

    images = [img for img in os.listdir(images_folder) if img.endswith(".jpeg")]

    for image in images:
        img_path = os.path.join(images_folder, image)
        img = Image.open(img_path)
        c.drawImage(img_path, 0, 0, width, height)
        c.showPage()
        img.close()
    c.save()
    for image in images:
        img_path = os.path.join(images_folder, image)
        os.remove(img_path)
    print(f"File downloaded successfully to {output_pdf}")
    

def epub_to_fb2(epub_path,fb2_path):
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


def download_text_book(uuid,series):
    info_url = f"https://api.bookmate.yandex.net/api/v5/books/{uuid}"
    info = json.loads(asyncio.run(send_request(info_url,None)).text)
    picture_url = info["book"]["cover"]["large"]
    name = info["book"]["title"]
    name = replace_forbidden_chars(name)
    url = f"https://api.bookmate.yandex.net/api/v5/books/{uuid}/content/v4"
    download_dir = f"mybooks/textbooks/{series}{name}/"
    os.makedirs(os.path.dirname(download_dir), exist_ok=True)
    asyncio.run(download_file(picture_url,f'{download_dir}{name}.jpeg'))
    if info:
        with open(f"{download_dir}{name}.json", 'w', encoding='utf-8') as file:
            file.write(json.dumps(info,ensure_ascii=False))
        print(f"File downloaded successfully to {download_dir}{name}.json")
    resp = asyncio.run(send_request(url,headers))
    if resp:
        with open(f"{download_dir}{name}.epub", 'wb') as file:
            file.write(resp.content)
        print(f"File downloaded successfully to {download_dir}{name}.epub")
    epub_to_fb2(f"{download_dir}{name}.epub",f"{download_dir}{name}.fb2")

def download_comic_book(uuid,series):
    info_url = f"https://api.bookmate.yandex.net/api/v5/comicbooks/{uuid}"
    info = json.loads(asyncio.run(send_request(info_url,None)).text)
    picture_url = info["comicbook"]["cover"]["large"]

    name = info["comicbook"]["title"]
    name = replace_forbidden_chars(name)
    url =  f"https://api.bookmate.yandex.net/api/v5/comicbooks/{uuid}/metadata.json"
    download_dir = f"mybooks/comicbooks/{series}{name}/"
    os.makedirs(os.path.dirname(download_dir), exist_ok=True)
    resp = asyncio.run(send_request(url, headers))
    if resp :
        download_url = json.loads(resp.text)["uris"]["zip"]
        asyncio.run(download_file(download_url,f'{download_dir}{name}.cbr'))
    with zipfile.ZipFile(f'{download_dir}{name}.cbr', 'r') as zip_ref:
        zip_ref.extractall(download_dir)
    # os.remove(f'{download_dir}{name}.zip')
    shutil.rmtree(download_dir+"preview", ignore_errors=False, onerror=None)

    create_pdf_from_images(download_dir, f"{download_dir}{name}.pdf")

    asyncio.run(download_file(picture_url,f'{download_dir}{name}.jpeg'))
    if info:
        with open(f"{download_dir}{name}.json", 'w', encoding='utf-8') as file:
            file.write(json.dumps(info,ensure_ascii=False))
        print(f"File downloaded successfully to {download_dir}{name}.json")

def download_audio_book (uuid,series):
    info_url = f"https://api.bookmate.yandex.net/api/v5/audiobooks/{uuid}"
    info = json.loads(asyncio.run(send_request(info_url,None)).text)
    picture_url = info["audiobook"]["cover"]["large"]
    name = info["audiobook"]["title"]
    name = replace_forbidden_chars(name)
    url = f'https://api.bookmate.yandex.net/api/v5/audiobooks/{uuid}/playlists.json'
    download_dir = f"mybooks/audiobooks/{series}{name}/"
    os.makedirs(os.path.dirname(download_dir), exist_ok=True)
    asyncio.run(download_file(picture_url,f'{download_dir}{name}.jpeg'))
    if info:
        with open(f"{download_dir}{name}.json", 'w', encoding='utf-8') as file:
            file.write(json.dumps(info,ensure_ascii=False))
        print(f"File downloaded successfully to {download_dir}{name}.json")
    resp = asyncio.run(send_request(url, headers))
    if resp :
        json_data = json.loads(resp.text)['tracks']
        download_urls = []
        bitrate = 1 if args.maxbitrate else 2
        if bitrate == 1:
            for child in range(0,len(json_data)):
                download_urls.append(json_data[child]['offline']['max_bit_rate']['url'])
        if bitrate == 2:
            for child in range(0,len(json_data)):
                download_urls.append(json_data[child]['offline']['min_bit_rate']['url'])

        files = os.listdir(download_dir)
        count = sum(1 for file in files if file.startswith('Глава_'))

        for download_url in range(count,len(download_urls)):
            download_urls[download_url] = download_urls[download_url].replace(".m3u8",".m4a")
            asyncio.run(download_file(download_urls[download_url],f'{download_dir}Глава_{download_url+1}.m4a'))

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--audiobooks", help="audiobookid, take from the book url")                                          
    argparser.add_argument("--maxbitrate", help="max-bitrate for download audiobook, defaul min-bitrate",default=False)         
    argparser.add_argument("--books", help="textbookid, take from the book url")                                           
    argparser.add_argument("--comicbooks", help="comiksid, take from the book url")                                            
    argparser.add_argument("--series", help="series, take from the audiobooks series url")                                            
    argparser.add_argument("--serials", help="serials, take from the book serial url")                                            

    args = argparser.parse_args()

    if os.path.isfile("token.txt"):
        with open("token.txt") as file:
            headers['auth-token'] = file.read()
    
    if not headers['auth-token']:
        headers['auth-token'] = get_auth_token()
        with open("token.txt", "w") as file:
            file.write(headers['auth-token'])

    if ((args.audiobooks == None) and (args.books == None) and (args.comicbooks == None) and (args.series == None) and (args.serials == None)):
        print("the following arguments are required: --audiobooks or --books or --comicbooks or --series or --serials")

    if (args.books):
       download_text_book(args.books,"")

    if (args.comicbooks):
        download_comic_book(args.comicbooks,"")

    if (args.audiobooks):
        download_audio_book(args.audiobooks,"")
    
    if (args.series):
        url = f'https://api.bookmate.yandex.net/api/v5/series/{args.series}/parts'
        info_url = f'https://api.bookmate.yandex.net/api/v5/series/{args.series}'
        book_urls = json.loads(asyncio.run(send_request(url,headers=headers)).text)['parts']
        name = json.loads(asyncio.run(send_request(info_url,headers=headers)).text)['series']['title']
        print(name)
        for child in range(0,len(book_urls)):
            print(book_urls[child]['resource_type'])
            if book_urls[child]['resource_type'] == "audiobook":
                print(book_urls[child]['resource']['uuid'])
                download_audio_book(book_urls[child]['resource']['uuid'],f"{name}/{child+1}. ")
            if book_urls[child]['resource_type'] == "comicbook":
                print(book_urls[child]['resource']['uuid'])
                download_comic_book(book_urls[child]['resource']['uuid'],f"{name}/{child+1}. ")
            if book_urls[child]['resource_type'] == "book":
                print(book_urls[child]['resource']['uuid'])
                download_text_book(book_urls[child]['resource']['uuid'],f"{name}/{child+1}. ")

    if (args.serials):
        url = f'https://api.bookmate.yandex.net/api/v5/books/{args.serials}/episodes'
        info_url = f'https://api.bookmate.yandex.net/api/v5/books/{args.serials}'
        book_urls = json.loads(asyncio.run(send_request(url,headers=headers)).text)['episodes']
        serials_name = json.loads(asyncio.run(send_request(info_url,headers=headers)).text)['book']['title']
        for child in range(0,len(book_urls)):
                episod_url = f"https://api.bookmate.yandex.net/api/v5/books/{book_urls[child]['uuid']}/content/v4"
                name = f"{child+1}. {book_urls[child]['title']}"
                download_dir = f"mybooks/textbooks/{serials_name}/{name}/{child+1}. "
                os.makedirs(os.path.dirname(download_dir), exist_ok=True)
                resp = asyncio.run(send_request(episod_url,headers))
                if resp:
                    with open(f"{download_dir}{name}.epub", 'wb') as file:
                        file.write(resp.content)
                    print(f"File downloaded successfully to {download_dir}{name}.epub")
                epub_to_fb2(f"{download_dir}{name}.epub",f"{download_dir}{name}.fb2")





