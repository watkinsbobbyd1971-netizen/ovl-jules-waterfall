import asyncio
import aiohttp
import urllib.parse
import json

async def test_search():
    async with aiohttp.ClientSession() as session:
        term = "Harley-Davidson Dyna Super Glide"
        url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(term)}&language=en&format=json"
        headers = {"User-Agent": "JulesBot/1.0 (jules@example.com) python-requests/2.25.1"}
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            print(json.dumps(data, indent=2))

asyncio.run(test_search())
