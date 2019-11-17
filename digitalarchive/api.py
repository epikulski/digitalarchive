"""
digitalarchive.api

This module contains functions for requesting data from the DigitalArchive API.
"""

# Standard Library
import logging
from typing import Optional, Dict

# 3rd Party Libraries
import requests

# Library modules
import digitalarchive.exceptions as exceptions

# Global Variables
SESSION = requests.session()


def search(model: str, params: Optional[Dict] = None) -> dict:
    """
    Search for DA records by endpoint and term.

    We have to massage the params we pass to the search endpoint as the API matches on
    inconsistent things.
    """
    # pylint: disable=bad-continuation

    # avoid mutable default arguments.
    if params is None:
        params = {}

    # Send Query.
    logging.debug("[*] Querying %s API endpoint with params: %s", model, str(params))
    url = f"https://digitalarchive.wilsoncenter.org/srv/{model}.json"
    response = SESSION.get(url, params=params)

    # Bail out if non-200 response.
    if response.status_code != 200:
        raise exceptions.NoSuchResourceError(
            "[!] Search failed for resource type %s with terms %s" % (model, params)
        )

    # Return response body.
    return response.json()


def get(endpoint: str, resource_id: str) -> dict:
    """Retrieve a single record from the DA."""
    url = f"https://digitalarchive.wilsoncenter.org/srv/{endpoint}/{resource_id}.json"
    logging.debug(
        "[*] Querying %s API endpoint for resource id: %s", endpoint, resource_id
    )
    response = SESSION.get(url)

    # Bail out if non-200 code.
    if response.status_code != 200:
        raise exceptions.NoSuchResourceError(
            "[!] Failed to find resource type %s at ID: %s" % (endpoint, resource_id)
        )

    # Return response body.
    return response.json()


def get_date_range() -> dict:
    """Get the earliest and latest possible document dates for the DigitalArchive."""
    url = "https://digitalarchive.wilsoncenter.org/srv/record/date_range.json"
    response = SESSION.get(url)
    return response.json()
