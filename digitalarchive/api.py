"""Principal class for interacting with the DigitalArchive"""

# Standard Library
import logging
from typing import List, AbstractSet, Optional, Dict

# 3rd Party Libraries
import requests

# Library modules
import digitalarchive.models as models


class DigitalArchive:
    """ORM Entrypoint for the DigitalArchive."""
    def __init__(self):
        # Set up typing.
        self.documents: AbstractSet[models.Document] = set()
        self.collections: AbstractSet[models.Collection] = set()
        self.contributors: AbstractSet[models.Contributor] = set()
        self.donors: AbstractSet[models.Donor] = set()
        self.publishers: AbstractSet[models.Publisher] = set()
        self.coverages: AbstractSet[models.Coverage] = set()
        self.repositories: AbstractSet[models.Repository] = set()

    # def import_records(self, filepath: str):
    #     """Import DA records from a .pickle."""
    #     # Load records
    #     records = pickle.load(open(filepath, "rb"))
    #
    #     # separate documents & collections
    #     self.documents = [models.Document(**record) for record in records if record['model'] == "Record"]
    #     self.collections = [models.Collection(**record) for record in records if record['model'] == "Collection"]
    #     logging.info("[*] Imported %s records from %s.", len(records), filepath)

    # def extract_entities(self):
    #     """Extract entities from avaialble records"""
    #     for doc in self.documents:
    #         [self.contributors.append(contributor) for contributor in doc.contributors if contributor not in self.contributors]
    #     pass
    #

    @staticmethod
    def search(model: str, params: Optional[Dict] = None) -> List[dict]:
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
        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                "[!] Search failed for resource type %s with terms %s" % (model, params)
            )

    @staticmethod
    def get(endpoint: str, resource_id: str) -> dict:
        """Retrieve a single record from the DA."""
        url = (
            f"https://digitalarchive.wilsoncenter.org/srv/{endpoint}/{resource_id}.json"
        )
        logging.debug(
            "[*] Querying %s API endpoint for resource id: %s", endpoint, resource_id
        )
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                "[!] Failed to find resource type %s at ID: %s" % (endpoint, resource_id))
