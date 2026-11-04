import asyncio
import aiohttp
import urllib.parse
import json

async def test_search():
    async with aiohttp.ClientSession() as session:
        url = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Harley-Davidson%20Dyna%20Super%20Glide&utf8=&format=json"
        headers = {"User-Agent": "JulesBot/1.0 (jules@example.com)"}
        async with session.get(url, headers=headers) as resp:
            data = await resp.text()
            print(data)

asyncio.run(test_search())
