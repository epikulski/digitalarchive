"""Principal class for interacting with the DigitalArchive."""

# Standard Library
import logging
import asyncio
from typing import Optional, Dict

# 3rd Party Libraries
import requests
import aiohttp
import multidict

# Library modules
import digitalarchive.exceptions as exceptions

# Global Variables
SESSION = requests.session()


async def search(
    model: str,
    params: Optional[multidict.MultiDict] = None,
    session: aiohttp.ClientSession = None,
) -> dict:
    """
    Search for DA records by endpoint and term.

    We have to massage the params we pass to the search endpoint as the API matches on
    inconsistent things.
    """
    # pylint: disable=bad-continuation

    # avoid mutable default arguments.
    if params is None:
        params = {}
    if session is None:
        session = aiohttp.ClientSession()

    # Send Query.
    logging.debug("[*] Querying %s API endpoint with params: %s", model, str(params))
    url = f"https://digitalarchive.wilsoncenter.org/srv/{model}.json"

    response = await session.get(url, params=params)

    async with response:
        # Bail out if non-200 response.
        if response.status != 200:
            raise exceptions.NoSuchResourceError(
                "[!] Search failed for resource type %s with terms %s" % (model, params)
            )

        # Return response body.
        return await response.json()


async def get(
    endpoint: str, resource_id: str, session: aiohttp.ClientSession = None
) -> dict:
    """Retrieve a single record from the DA.

    todo: add logic to cleanup session if we created it for this request.
    """

    # Create an aiohttp session if we need one.
    if session is None:
        session = aiohttp.ClientSession()

    url = f"https://digitalarchive.wilsoncenter.org/srv/{endpoint}/{resource_id}.json"
    logging.debug(
        "[*] Querying %s API endpoint for resource id: %s", endpoint, resource_id
    )

    response = await session.get(url)
    async with response:
        if response.status != 200:
            raise Exception(
                "[!] Failed to find resource type %s at ID: %s"
                % (endpoint, resource_id)
            )
        else:
            return await response.json()


async def get_asset(url, session: aiohttp.ClientSession = None) -> bytes:
    """
    Retrieve a single asset from the DA API.

    Assets (Translations, Transcripts, Media Files) have a different endpoint than other records and
    don't return JSON, so we have different handling here.

    todo: add logic to cleanup session if we created it for this request.
    """
    # Create an aiohttp session if we need one.
    if session is None:
        session = aiohttp.ClientSession()

    # Send our request.
    response = await session.get(url)
    async with response:
        if response.status == 200:
            return await response.read()
        else:
            raise exceptions.APIServerError(
                f"[!] Hydrating asset at %s: %s failed with code: %s",
                url,
                response.status,
            )


def get_date_range() -> dict:
    url = "https://digitalarchive.wilsoncenter.org/srv/record/date_range.json"
    response = SESSION.get(url)
    return response.json()
