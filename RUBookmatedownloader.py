import random
import os
import time
import json
import argparse
import shutil
import collections.abc
collections.Iterable = collections.abc.Iterable
collections.Mapping = collections.abc.Mapping
collections.MutableSet = collections.abc.MutableSet
collections.MutableMapping = collections.abc.MutableMapping
import httpx
import asyncio
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

UA = {
    1: "Samsung/Galaxy_A51 Android/12 Bookmate/3.7.3",
    2: "Huawei/P40_Lite Android/11 Bookmate/3.7.3",
    3: "OnePlus/Nord_N10 Android/10 Bookmate/3.7.3",
    4: "Google/Pixel_4a Android/9 Bookmate/3.7.3",
    5: "Oppo/Reno_4 Android/8 Bookmate/3.7.3",
    6: "Xiaomi/Redmi_Note_9 Android/10 Bookmate/3.7.3",
    7: "Motorola/Moto_G_Power Android/10 Bookmate/3.7.3",
    8: "Sony/Xperia_10 Android/10 Bookmate/3.7.3",
    9: "LG/Velvet Android/10 Bookmate/3.7.3",
    10: "Realme/6_Pro Android/10 Bookmate/3.7.3",
}
headers = {
        'app-user-agent': UA[random.randint(1,10)],
        'mcc':'',
        'mnc': '',
        'imei': '',
        'subscription-country': '',
        'app-locale': '',
        'bookmate-version': '',
        'bookmate-websocket-version': '',
        'device-idfa': '', 
        'onyx-preinstall': 'false',
        'auth-token': '',  #<================================================================================ ADD TOKEN
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
    while(not is_download):
        async with httpx.AsyncClient(http2=True) as client:
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
                time.sleep(5)
            

async def send_request(url, headers):
    is_download = False
    while(not is_download):
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers,timeout=None)
            if response.status_code == 200:
                is_download = True
                return(response)
            else:
                print(f"Failed to send request. Status code: {response.status_code}")
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


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--audiobookid", help="udiobookid, take from the book url")                                          
    argparser.add_argument("--maxbitrate", help="max-bitrate for download audiobook, defaul min-bitrate",default=False)         
    argparser.add_argument("--textbookid", help="textbookid, take from the book url")                                           
    argparser.add_argument("--comicbookid", help="comiksid, take from the book url")                                            

    args = argparser.parse_args()

    if os.path.isfile("token.txt"):
        with open("token.txt") as file:
            headers['auth-token'] = file.read()
    
    if not headers['auth-token']:
        headers['auth-token'] = get_auth_token()
        with open("token.txt", "w") as file:
            file.write(headers['auth-token'])

    if ((args.textbookid == None) and (args.audiobookid == None) and (args.comicbookid == None)):
        print("the following arguments are required: --textbookid or --audiobookid or --comiksid")

    if (args.textbookid):
        info_url = f"https://api.bookmate.yandex.net/api/v5/books/{args.textbookid}"
        info = json.loads(asyncio.run(send_request(info_url,None)).text)
        picture_url = info["book"]["cover"]["large"]
        name = info["book"]["title"]
        name = replace_forbidden_chars(name)
        url = f"https://api.bookmate.yandex.net/api/v5/books/{args.textbookid}/content/v4"
        download_dir = f"mybooks/textbooks/{name}/"
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

    if (args.comicbookid):
        info_url = f"https://api.bookmate.yandex.net/api/v5/comicbooks/{args.comicbookid}"
        info = json.loads(asyncio.run(send_request(info_url,None)).text)
        picture_url = info["comicbook"]["cover"]["large"]

        name = info["comicbook"]["title"]
        name = replace_forbidden_chars(name)
        url =  f"https://api.bookmate.yandex.net/api/v5/comicbooks/{args.comicbookid}/metadata.json"
        download_dir = f"mybooks/comicbooks/{name}/"
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

    if (args.audiobookid):
        info_url = f"https://api.bookmate.yandex.net/api/v5/audiobooks/{args.audiobookid}"
        info = json.loads(asyncio.run(send_request(info_url,None)).text)
        picture_url = info["audiobook"]["cover"]["large"]
        name = info["audiobook"]["title"]
        name = replace_forbidden_chars(name)
        url = f'https://api.bookmate.yandex.net/api/v5/audiobooks/{args.audiobookid}/playlists.json'
        download_dir = f"mybooks/audiobooks/{name}/"
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
            for download_url in range(0,len(download_urls)):
                download_urls[download_url] = download_urls[download_url].replace(".m3u8",".m4a")
                asyncio.run(download_file(download_urls[download_url],f'{download_dir}Глава_{download_url+1}.m4a'))