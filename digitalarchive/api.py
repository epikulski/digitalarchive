"""Principal class for interacting with the DigitalArchive."""

# Standard Library
import logging
from typing import List, Optional, Dict

# 3rd Party Libraries
import requests

# Library modules
import digitalarchive.exceptions as exceptions

# Global Variables
session = requests.session()

def search(model: str, params: Optional[Dict] = None) -> dict:
    """
    Search for DA records by endpoint and term.

    We have to massage the params we pass to the search endpoint as the API matches on
    inconsistent things.

    todo: Add logic for pagination, either here or in searchresult.
    """
    # pylint: disable=bad-continuation

    # avoid mutable default arguments.
    if params is None:
        params = {}

    # Special handling for parameters that are subclasses of Resource.
    # We sub in the ID# instead of the whole dataclass.
    for field in [
        "collection",
        "publisher",
        "repository",
        "coverage",
        "subject",
        "contributor",
        "donor",
    ]:
        if params.get(field) is not None:
            params[field] = params.get(field).id

    # Handle record searches. We transform some of the parameters.
    if model in ["record", "collection"]:
        # concatenate all of the keyword fields into the 'q' param
        keywords = []
        for field in ["name", "title", "description", "slug"]:
            if params.get(field) is not None:
                keywords.append(params.get(field))
        params["q"] = " ".join(keywords)

        # Strip out fields the search endpoint doesn't support.
        for field in ["name", "title", "description", "slug"]:
            if params.get(field) is not None:
                params.pop(field)

        # Format the model name to match API docs.
        params["model"] = model.capitalize()

    # Handle non record or collection searches. These always match on "term".
    else:
        # If we've got both a name and a value, join them.
        if params.get("name") and params.get("value"):
            params["term"] = " ".join([params.get("name"), params.get("value")])

        # Otherwise, treat the one that exists as the term.
        elif params.get("name"):
            params["term"] = params["name"]
        elif params.get("value"):
            params["term"] = params["value"]

    # Send Query.
    logging.debug(
        "[*] Querying %s API endpoint with params: %s", model, str(params)
    )
    url = f"https://digitalarchive.wilsoncenter.org/srv/{model}.json"
    response = session.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise exceptions.NoSuchResourceError(
            "[!] Search failed for resource type %s with terms %s" % (model, params)
        )

def get(endpoint: str, resource_id: str) -> dict:
    """Retrieve a single record from the DA."""
    url = (
        f"https://digitalarchive.wilsoncenter.org/srv/{endpoint}/{resource_id}.json"
    )
    logging.debug(
        "[*] Querying %s API endpoint for resource id: %s", endpoint, resource_id
    )
    response = session.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        raise exceptions.NoSuchResourceError(
            "[!] Failed to find resource type %s at ID: %s" % (endpoint, resource_id))
