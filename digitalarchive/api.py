"""Principal class for interacting with the DigitalArchive."""

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
    if model == "record":
        # concatenate all of the keyword fields into the 'q' param
        keywords = []
        for field in ["name", "title", "description", "slug", "q"]:
            if params.get(field) is not None:
                keywords.append(params.get(field))
        params["q"] = " ".join(keywords)

        # Strip out fields the search endpoint doesn't support.
        # todo: raise an error here for "unsupported search field"?
        for field in ["name", "title", "description", "slug"]:
            if params.get(field) is not None:
                params.pop(field)

        # Format the model name to match API docs.
        params["model"] = model.capitalize()

        # Send query. Both collections and records use the records.json endpoint.
        logging.debug("[*] Querying %s API endpoint with params: %s", model, str(params))
        url = f"https://digitalarchive.wilsoncenter.org/srv/record.json"
        response = SESSION.get(url, params=params)

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
