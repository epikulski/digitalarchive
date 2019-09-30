"""Helper class to async hydrate a set of DA records"""

import asyncio
import aiohttp
import logging
import time

class Hydrator:

    def __init__(self, records:list, max_concurrent_requests=200):
        self.records = records    
        self.session = None
        self.max_concurrent_requests = max_concurrent_requests

    async def refresh_session(self):
        self.session = aiohttp.ClientSession()

    async def fetch(self, url: str, params={}) -> dict:

        # Low effort attempt to avoid rate limit.
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0"}
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                return await response.json()
        
        except asyncio.TimeoutError:
            logging.exception("[!] Timeout error during fetch! Recovering...")
            time.sleep(15)
            self.refresh_session()
            return await self.fetch(url, params)

    async def hydrate_record(self, semaphore: asyncio.Semaphore, record: dict) -> dict:
        async with semaphore:
            record.update(await self.fetch(f"https://digitalarchive.wilsoncenter.org/srv/record/{record['id']}.json"))
            logging.info("Fetched record ID# %s", record['id'])
            return record
    
    async def hydrate_records(self, records: list):
        await self.refresh_session()
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        records = await asyncio.gather(
            *[self.hydrate_record(semaphore, record) for record in records]
        )

        # Explicitely close our session.
        await self.session.close()
        return records
    
    def rehydrate(self):
        self.records = asyncio.run(self.hydrate_records(self.records))
        return self.records

    
if __name__ == "__main__":
    from update_graph import find_all_records
    records = find_all_records(limit=100)

    # Separate records into documents and collections
    documents = []
    collections = []

    for record in records:
        if record["model"] == "Record":
            documents.append(record)
        elif record["model"] == "Collection":
            collections.append(record)

    hydrator = Hydrator(documents)
    new_docs = hydrator.rehydrate()


    print("End of script")


