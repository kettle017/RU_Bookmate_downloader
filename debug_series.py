import asyncio
import httpx
import json
import urllib.parse

BASE_URL = "https://api.bookmate.yandex.net/api/v5"
QUERY = "Крадущийся в тени"
URL = f"{BASE_URL}/series/TRxU8Wa4/parts"

async def main():
    # ... (token reading) ...
    # ... (headers) ...

    try:
        with open("token.txt", "r") as f:
            token = f.read().strip()
    except FileNotFoundError:
        token = ""

    headers = {
        'app-user-agent': "Samsung/Galaxy_A51 Android/12 Bookmate/3.7.3",
        'auth-token': token
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(URL, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'parts' in data:
                print(f"Found {len(data['parts'])} parts")
                for part in data['parts'][:1]:
                    print(f"Part keys: {part.keys()}")
                    print(f"Resource keys: {part['resource'].keys()}")
                    print(f"Title: {part['resource'].get('title')}")
        else:
            print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
