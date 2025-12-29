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
import subprocess
import glob
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import httpx
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
from pathlib import Path
import urllib.parse

UA = {
    1: "Samsung/Galaxy_A51 Android/12 Bookmate/3.7.3",
    2: "Huawei/P40_Lite Android/11 Bookmate/3.7.3",
    3: "OnePlus/Nord_N10 Android/10 Bookmate/3.7.3"
}

HEADERS = {
    'app-user-agent': UA[random.randint(1, 3)],
    'onyx-preinstall': 'false',
    'auth-token': '',
}

BASE_URL = "https://api.bookmate.yandex.net/api/v5"
URLS = {
    "book": {
        "infoUrl": f"{BASE_URL}/books/{{uuid}}",
        "contentUrl": f"{BASE_URL}/books/{{uuid}}/content/v4"
    },
    "audiobook": {
        "infoUrl": f"{BASE_URL}/audiobooks/{{uuid}}",
        "contentUrl": f"{BASE_URL}/audiobooks/{{uuid}}/playlists.json"
    },
    "comicbook": {
        "infoUrl": f"{BASE_URL}/comicbooks/{{uuid}}",
        "contentUrl": f"{BASE_URL}/comicbooks/{{uuid}}/metadata.json"
    },
    "serial": {
        "infoUrl": f"{BASE_URL}/books/{{uuid}}",
        "contentUrl": f"{BASE_URL}/books/{{uuid}}/episodes"
    },
    "series": {
        "infoUrl": f"{BASE_URL}/series/{{uuid}}",
        "contentUrl": f"{BASE_URL}/series/{{uuid}}/parts"
    },
    "author": {
        "audiobooksUrl": f"{BASE_URL}/authors/{{uuid}}/audiobooks?role=author"
    }
}


def get_auth_token():
    if os.path.isfile("token.txt"):
        with open("token.txt", encoding='utf-8') as file:
            return file.read().strip()
    if HEADERS['auth-token']:
        return HEADERS['auth-token']
    auth_token = run_auth_webview()
    if auth_token:
        with open("token.txt", "w", encoding='utf-8') as file:
            file.write(auth_token)
    return auth_token


def run_auth_webview():
    import webview

    def on_loaded(window):
        if "yx4483e97bab6e486a9822973109a14d05.oauth.yandex.ru" in urllib.parse.urlparse(window.get_current_url()).netloc:
            url = urllib.parse.urlparse(window.get_current_url())
            if 'access_token' in urllib.parse.parse_qs(url.fragment):
                window.auth_token = urllib.parse.parse_qs(url.fragment)['access_token'][0]
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
    return re.sub(f'[{chars}]', '', filename).strip()


class BookmateDownloader:
    def __init__(self):
        self.client = None
        self.semaphore = asyncio.Semaphore(3)  # Limit concurrent book/series downloads
        self.chapter_semaphore = asyncio.Semaphore(10) # Limit concurrent chapter downloads

    async def __aenter__(self):
        self.client = httpx.AsyncClient(http2=True, verify=False, timeout=None)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def _request(self, url, method='GET', **kwargs):
        count = 0
        while count < 5:
            try:
                response = await self.client.request(method, url, headers=HEADERS, **kwargs)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    print(f"⚠️ Rate limit hit (429). Sleeping for {5 * (count + 1)}s...")
                    sys.stdout.flush()
                    await asyncio.sleep(5 * (count + 1))
                    count += 1
                    continue
                elif response.is_redirect:
                    url = response.next_request.url
                    continue
                else:
                    print(f"Request failed: {response.status_code} {url}")
                    sys.stdout.flush()
            except Exception as e:
                print(f"Request error: {type(e).__name__}: {e}")
                sys.stdout.flush()
            
            count += 1
            await asyncio.sleep(3 * count)
        
        print(f"Failed to fetch {url} after 5 attempts")
        sys.stdout.flush()
        return None

    async def download_file(self, url, file_path):
        response = await self._request(url)
        if response:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            # print(f"Downloaded: {os.path.basename(file_path)}")
            return True
        return False

    async def get_resource_info(self, resource_type, uuid, series=''):
        info_url = URLS[resource_type]['infoUrl'].format(uuid=uuid)
        response = await self._request(info_url)
        if not response:
            return None
        
        info = response.json()
        if not info:
            return None

        # Handle different response structures if necessary
        if resource_type not in info:
             # Fallback or error
             pass

        title = info[resource_type]["title"]
        title = replace_forbidden_chars(title)
        
        # Determine download directory
        if series:
            # series is expected to be "AuthorName/SeriesName/" or similar
            download_dir = f"mybooks/series/{series}{title}/"
        else:
            download_dir = f"mybooks/{resource_type}/{title}/"
            
        os.makedirs(os.path.dirname(download_dir), exist_ok=True)
        path = f'{download_dir}{title}'
        
        # Save cover
        if "cover" in info[resource_type] and "large" in info[resource_type]["cover"]:
            picture_url = info[resource_type]["cover"]["large"]
            await self.download_file(picture_url, f'{path}.jpeg')
            
        # Save metadata
        with open(f"{path}.json", 'w', encoding='utf-8') as file:
            file.write(json.dumps(info, ensure_ascii=False, indent=2))
            
        print(f"ℹ️ Info saved: {title}")
        sys.stdout.flush()
        return path

    async def get_resource_json(self, resource_type, uuid):
        url = URLS[resource_type]['contentUrl'].format(uuid=uuid)
        response = await self._request(url)
        return response.json() if response else None

    async def download_book(self, uuid, series='', serial_path=None):
        path = serial_path if serial_path else await self.get_resource_info('book', uuid, series)
        if not path:
            return

        if os.path.exists(f"{path}.epub") or os.path.exists(f"{path}.fb2"):
            print(f"⏩ Book already exists: {os.path.basename(path)}")
            sys.stdout.flush()
            return

        print(f"Downloading book: {os.path.basename(path)}")
        sys.stdout.flush()
        url = URLS['book']['contentUrl'].format(uuid=uuid)
        if await self.download_file(url, f'{path}.epub'):
            await asyncio.to_thread(epub_to_fb2, f"{path}.epub", f"{path}.fb2")
            print(f"✅ Book downloaded: {path}.epub")
            sys.stdout.flush()

    async def download_audiobook(self, uuid, series='', max_bitrate=False, merge_chapters=True, cleanup_chapters=True):
        path = await self.get_resource_info('audiobook', uuid, series)
        if not path:
            return

        if merge_chapters and os.path.exists(f"{path}_complete.m4a"):
            print(f"⏩ Audiobook already exists: {os.path.basename(path)}_complete.m4a")
            sys.stdout.flush()
            return

        print(f"Downloading audiobook: {os.path.basename(path)}")
        sys.stdout.flush()
        resp = await self.get_resource_json('audiobook', uuid)
        if not resp:
            return

        bitrate = 'max_bit_rate' if max_bitrate else 'min_bit_rate'
        tracks = resp.get('tracks', [])
        
        tasks = []
        download_dir = os.path.dirname(path)
        existing_files = set(os.listdir(download_dir))
        
        async def download_chapter(url, path):
            async with self.chapter_semaphore:
                return await self.download_file(url, path)

        for track in tracks:
            name = f'Глава_{track["number"]+1}.m4a'
            if name in existing_files:
                continue
                
            download_url = track['offline'][bitrate]['url'].replace(".m3u8", ".m4a")
            file_path = os.path.join(download_dir, name)
            tasks.append(download_chapter(download_url, file_path))

        if tasks:
            print(f"Downloading {len(tracks)} chapters...")
            sys.stdout.flush()
            results = await asyncio.gather(*tasks)
            if not all(results):
                print("⚠️ Some chapters failed to download")
                sys.stdout.flush()
        
        if merge_chapters:
            print(f"Merging audiobook: {os.path.basename(path)}")
            sys.stdout.flush()
            # Run merge in a separate thread to avoid blocking
            await asyncio.to_thread(
                merge_audiobook_chapters_ffmpeg, 
                download_dir, 
                f"{path}_complete.m4a", 
                None, # Metadata is loaded from json inside the function
                cleanup_chapters
            )

    async def download_comicbook(self, uuid, series=''):
        path = await self.get_resource_info('comicbook', uuid, series)
        if not path:
            return
            
        resp = await self.get_resource_json('comicbook', uuid)
        if resp:
            download_url = resp["uris"]["zip"]
            if await self.download_file(download_url, f'{path}.cbr'):
                # Process comicbook (unzip, convert to pdf)
                # This is blocking, so run in thread
                await asyncio.to_thread(self._process_comicbook, path)

    def _process_comicbook(self, path):
        with zipfile.ZipFile(f'{path}.cbr', 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(path))
        shutil.rmtree(os.path.dirname(path)+"/preview", ignore_errors=True)
        create_pdf_from_images(os.path.dirname(path), f"{path}.pdf")

    async def download_serial(self, uuid):
        path = await self.get_resource_info('book', uuid)
        if not path:
            return
            
        resp = await self.get_resource_json('serial', uuid)
        if resp:
            tasks = []
            for episode_index, episode in enumerate(resp["episodes"]):
                name = f"{episode_index+1}. {episode['title']}"
                name = replace_forbidden_chars(name)
                download_dir = f'{os.path.dirname(path)}/{name}'
                os.makedirs(download_dir, exist_ok=True)
                tasks.append(self.download_book(episode['uuid'], serial_path=f'{download_dir}/{name}'))
            
            await asyncio.gather(*tasks)

    async def download_series(self, uuid, max_bitrate=False, merge_chapters=True, cleanup_chapters=True):
        path = await self.get_resource_info('series', uuid)
        if not path:
            return
            
        resp = await self.get_resource_json('series', uuid)
        if not resp:
            return
            
        name = os.path.basename(path)
        print(f"Downloading series: {name}")
        sys.stdout.flush()
        
        tasks = []
        for part_index, part in enumerate(resp['parts']):
            resource_type = part['resource_type']
            resource_uuid = part['resource']['uuid']
            
            # Determine function
            if resource_type == 'book':
                # Try to find audiobook if it's a book
                book_title = part['resource']['title']
                audiobook_uuid = await self._find_audiobook_by_title(book_title)
                
                if audiobook_uuid:
                    print(f"Found audiobook for '{book_title}': {audiobook_uuid}")
                    sys.stdout.flush()
                    tasks.append(self._bounded_download(
                        self.download_audiobook, 
                        audiobook_uuid, 
                        series=f"{name}/{part_index+1}. ",
                        max_bitrate=max_bitrate,
                        merge_chapters=merge_chapters,
                        cleanup_chapters=cleanup_chapters
                    ))
                else:
                    # If no audiobook found, download the book
                    tasks.append(self._bounded_download(
                        self.download_book, 
                        resource_uuid, 
                        series=f"{name}/{part_index+1}. "
                    ))
            elif resource_type == 'audiobook':
                tasks.append(self._bounded_download(
                    self.download_audiobook, 
                    resource_uuid, 
                    series=f"{name}/{part_index+1}. ",
                    max_bitrate=max_bitrate,
                    merge_chapters=merge_chapters,
                    cleanup_chapters=cleanup_chapters
                ))
            elif resource_type == 'comicbook':
                tasks.append(self._bounded_download(
                    self.download_comicbook, 
                    resource_uuid, 
                    series=f"{name}/{part_index+1}. "
                ))
            else:
                print(f"Unknown resource type: {resource_type}")
                sys.stdout.flush()
                continue
            
        await asyncio.gather(*tasks)

    async def download_author_audiobooks(self, uuid, max_bitrate=False, merge_chapters=True, cleanup_chapters=True):
        author_url = URLS['author']['audiobooksUrl'].format(uuid=uuid)
        print(f"Fetching audiobooks for author {uuid}...")
        sys.stdout.flush()
        
        resp = await self._request(author_url)
        if not resp:
            return
            
        data = resp.json()
        if 'audiobooks' not in data:
            print("No audiobooks found")
            sys.stdout.flush()
            return
            
        audiobooks = data['audiobooks']
        
        # Get author name
        author_name = "Unknown Author"
        if audiobooks and audiobooks[0].get('authors'):
            author_name = audiobooks[0]['authors'][0].get('name', 'Unknown Author')
            
        author_folder = replace_forbidden_chars(author_name)
        print(f"Found {len(audiobooks)} audiobooks by {author_name}")
        sys.stdout.flush()
        
        tasks = []
        for i, audiobook in enumerate(audiobooks, 1):
            series_path = f"{author_folder}/{i:02d}. "
            tasks.append(self._bounded_download(
                self.download_audiobook, 
                audiobook['uuid'], 
                series=series_path,
                max_bitrate=max_bitrate,
                merge_chapters=merge_chapters,
                cleanup_chapters=cleanup_chapters
            ))
            
        await asyncio.gather(*tasks)

    async def _bounded_download(self, func, *args, **kwargs):
        async with self.semaphore:
            try:
                await func(*args, **kwargs)
            except Exception as e:
                print(f"Error in download: {e}")
                sys.stdout.flush()

    async def _find_audiobook_by_title(self, title):
        query = urllib.parse.quote(title)
        url = f"{BASE_URL}/search?query={query}"
        response = await self._request(url)
        if not response:
            return None
        
        data = response.json()
        if 'search' in data and 'audiobooks' in data['search']:
            audiobooks = data['search']['audiobooks'].get('objects', [])
            if audiobooks:
                # Return the first match
                return audiobooks[0]['uuid']
        return None


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
        try:
            book = epub.read_epub(epub_path)
        except Exception as e:
            print(f"Error reading epub {epub_path}: {e}")
            return

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


def merge_audiobook_chapters_ffmpeg(audiobook_dir, output_file, metadata=None, cleanup_chapters=True):
    """
    Merge all M4A chapter files in a directory into a single audiobook using ffmpeg
    """
    audiobook_path = Path(audiobook_dir)
    
    # Find all M4A files and sort them naturally
    chapter_files = sorted([f for f in audiobook_path.glob("*.m4a") if "Глава_" in f.name], 
                          key=lambda x: int(x.stem.split('_')[1]))
    
    if not chapter_files:
        print(f"No chapter files found in {audiobook_path}")
        return False
    
    # Look for cover image
    cover_image = None
    for ext in ['.jpeg', '.jpg', '.png']:
        potential_cover = audiobook_path / f"{audiobook_path.name}{ext}"
        if potential_cover.exists():
            cover_image = potential_cover
            break
            
    # Load metadata from json if not provided
    if metadata is None:
        json_file = audiobook_path / f"{audiobook_path.name}.json"
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    if 'audiobook' in info:
                        book_info = info['audiobook']
                        author_name = 'Unknown Author'
                        if 'authors' in book_info and book_info['authors']:
                            author_name = book_info['authors'][0].get('name', 'Unknown Author')
                        
                        metadata = {
                            'title': book_info.get('title', audiobook_path.name),
                            'artist': author_name,
                            'album': book_info.get('title', audiobook_path.name),
                            'album_artist': author_name,
                            'genre': 'Audiobook',
                            'media_type': '2',
                        }
            except Exception:
                pass
    
    # Create a temporary file list for ffmpeg
    filelist_path = audiobook_path / "chapters_list.txt"
    chapters_metadata_path = audiobook_path / "chapters_metadata.txt"
    
    try:
        # Get chapter durations first
        chapter_durations = []
        current_time = 0.0
        
        for chapter_file in chapter_files:
            # Get duration of each chapter using ffprobe
            duration_cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(chapter_file)
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            
            if duration_result.returncode == 0:
                try:
                    duration = float(duration_result.stdout.strip())
                    chapter_durations.append((current_time, current_time + duration, chapter_file))
                    current_time += duration
                except ValueError:
                    chapter_durations.append((current_time, current_time + 180, chapter_file))
                    current_time += 180
            else:
                chapter_durations.append((current_time, current_time + 180, chapter_file))
                current_time += 180
        
        # Write file list for ffmpeg concat
        with open(filelist_path, 'w', encoding='utf-8') as f:
            for chapter_file in chapter_files:
                abs_path = str(chapter_file.absolute()).replace("'", "'\"'\"'")
                f.write(f"file '{abs_path}'\n")
        
        # Create chapters metadata file
        with open(chapters_metadata_path, 'w', encoding='utf-8') as f:
            f.write(";FFMETADATA1\n")
            if metadata:
                for key, value in metadata.items():
                    if value:
                        escaped_value = str(value).replace('=', '\\=').replace(';', '\\;').replace('#', '\\#').replace('\\', '\\\\')
                        f.write(f"{key.upper()}={escaped_value}\n")
            
            for i, (start_time, end_time, chapter_file) in enumerate(chapter_durations):
                chapter_num = i + 1
                f.write("\n[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")
                f.write(f"START={int(start_time * 1000)}\n")
                f.write(f"END={int(end_time * 1000)}\n")
                f.write(f"title=Глава {chapter_num}\n")
        
        # FFmpeg command
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(filelist_path),
            '-i', str(chapters_metadata_path),
        ]
        
        if cover_image:
            cmd.extend(['-i', str(cover_image)])
            cmd.extend(['-c:v', 'copy'])
            cmd.extend(['-c:a', 'copy'])
            cmd.extend(['-disposition:v:0', 'attached_pic'])
            cmd.extend(['-map_metadata', '1'])
        else:
            cmd.extend(['-c', 'copy'])
            cmd.extend(['-map_metadata', '1'])
        
        if metadata:
            for key, value in metadata.items():
                if value:
                    cmd.extend(['-metadata', f'{key}={value}'])
        
        cmd.append(str(output_file))
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode == 0:
            print(f"✅ Successfully merged: {os.path.basename(output_file)}")
            sys.stdout.flush()
            if cleanup_chapters:
                for chapter_file in chapter_files:
                    try:
                        chapter_file.unlink()
                    except OSError:
                        pass
            return True
        else:
            print(f"❌ Error merging audiobook: {result.stderr}")
            sys.stdout.flush()
            return False
            
    finally:
        if filelist_path.exists():
            filelist_path.unlink()
        if chapters_metadata_path.exists():
            chapters_metadata_path.unlink()


def list_author_audiobooks(uuid):
    # This function is synchronous in the original code, but we can make it use the async class
    # Or just keep it simple. Let's use the async class for consistency.
    async def _list():
        async with BookmateDownloader() as downloader:
            author_url = URLS['author']['audiobooksUrl'].format(uuid=uuid)
            resp = await downloader._request(author_url)
            if not resp:
                return
            
            data = resp.json()
            if 'audiobooks' not in data:
                print("No audiobooks found")
                return
                
            audiobooks = data['audiobooks']
            author_name = "Unknown Author"
            if audiobooks and audiobooks[0].get('authors'):
                author_name = audiobooks[0]['authors'][0].get('name', 'Unknown Author')
            
            print(f"\n📚 Audiobooks by {author_name} ({len(audiobooks)} books)")
            print("=" * 70)
            
            total_duration = 0
            for i, audiobook in enumerate(audiobooks, 1):
                title = audiobook['title']
                uuid_book = audiobook['uuid']
                duration = audiobook.get('duration', 0)
                duration_hours = round(duration / 3600, 1)
                
                total_duration += duration
                print(f"{i:2d}. {title}")
                print(f"    UUID: {uuid_book}")
                print(f"    Duration: {duration_hours}h")
                print()
            
            print("=" * 70)
            print(f"📊 Total: {len(audiobooks)} audiobooks, {round(total_duration / 3600, 1)} hours")

    asyncio.run(_list())


async def run_async_main(args):
    async with BookmateDownloader() as downloader:
        if args.command == 'book':
            await downloader.download_book(args.uuid)
        elif args.command == 'audiobook':
            await downloader.download_audiobook(
                args.uuid, 
                max_bitrate=args.max_bitrate, 
                merge_chapters=not args.no_merge, 
                cleanup_chapters=not args.keep_chapters
            )
        elif args.command == 'comicbook':
            await downloader.download_comicbook(args.uuid)
        elif args.command == 'serial':
            await downloader.download_serial(args.uuid)
        elif args.command == 'series':
            await downloader.download_series(
                args.uuid,
                max_bitrate=args.max_bitrate,
                merge_chapters=not args.no_merge,
                cleanup_chapters=not args.keep_chapters
            )
        elif args.command == 'author':
            await downloader.download_author_audiobooks(
                args.uuid,
                max_bitrate=args.max_bitrate,
                merge_chapters=not args.no_merge,
                cleanup_chapters=not args.keep_chapters
            )


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("command", choices=['book', 'audiobook', 'comicbook', 'serial', 'series', 'author', 'list-author'])
    argparser.add_argument("uuid")
    argparser.add_argument("--max_bitrate", action='store_false', help="Use maximum bitrate for audiobooks")
    argparser.add_argument("--no-merge", action='store_true', help="Keep audiobook chapters as separate files (don't merge)")
    argparser.add_argument("--keep-chapters", action='store_true', help="Keep individual chapter files after merging")
    args = argparser.parse_args()

    HEADERS['auth-token'] = get_auth_token()

    if args.command == 'list-author':
        list_author_audiobooks(args.uuid)
    else:
        asyncio.run(run_async_main(args))


if __name__ == "__main__":
    main()

