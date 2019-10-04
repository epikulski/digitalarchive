import pickle
import logging
import requests
from typing import List, Set
# from .models import Document, Collection, Contributor, Donor, Publisher, Coverage, Repository, Asset


class DigitalArchive:
    # def __init__(self):
        # Set up Class Typing.
        # self.documents: Set[Document] = []
        # self.collections: Set[Collection] = []
        # self.contributors: Set[Contributor] = []
        # self.donors: Set[Donor] = []
        # self.publishers: Set[Publisher] = []
        # self.coverages: Set[Coverage] = []
        # self.repositories: Set[Repository] = []

    # def import_records(self, filepath: str):
    #     """Import DA records from a .pickle."""
    #     # Load records
    #     records = pickle.load(open(filepath, "rb"))
    #
    #     # separate documents & collections
    #     self.documents = [ Document(**record) for record in records if record['model'] == "Record" ]
    #     self.collections = [ Collection(**record) for record in records if record['model'] == "Collection" ]
    #     logging.info("[*] Imported %s records from %s.", len(records), filepath)

    # def extract_entities(self):
    #     """Extract entities from avaialble records"""
    #     for doc in self.documents:
    #         [self.contributors.append(contributor) for contributor in doc.contributors if contributor not in self.contributors]
    #     pass
    #

    @staticmethod
    def search(endpoint: str, params: dict = None) -> List[dict]:
        """
        Search for DA records by endpoint and term.

        We have to massage the params we pass to the search endpoint as the API matches on
        inconsistent things.

        TODO: Refactor this to be sensible.
        """

        # Handle record searches. We transform some of the parameters
        if endpoint in ["record", "collection"]:

            # concatenate all of the keyword fields into the 'q' param
            keywords = []
            for field in ["name", "title", "description", "slug"]:
                if params.get(field) is not None:
                    keywords.append(params.get(field))
            params["q"] = " ".join(keywords)

            # Strip out fields the search endpoint doesn't support.
            for field in ["name", "title", "description", "slug"]:
                try:
                    params.pop(field)
                except KeyError:
                    pass

            # Format the model name to match API docs.
            params["model"] = endpoint.capitalize()

        # Special handling parameters that are subclasses of Resource.
        for field in ["collection", "publisher", "repository", "coverage", "subject", "contributor", "donor"]:
            if params.get(field) is not None:
                params[field] = params.get(field).id

        # Handle non record/collection searches. These always match on "term".
        else:
            if params.get("name"):
                params["term"] = params["name"]
            elif params.get("value"):
                params["term"] = params["value"]

        logging.debug("[*] Querying %s API endpoint with params: %s", endpoint, str(params))
        url = f"https://digitalarchive.wilsoncenter.org/srv/{endpoint}.json"
        response = requests.get(url, params=params)
        return response.json()

    @staticmethod
    def get(endpoint: str, resource_id: str) -> dict:
        """Retrieve a single record from the DA."""
        url = f"https://digitalarchive.wilsoncenter.org/srv/{endpoint}/{resource_id}.json"
        logging.debug("[*] Querying %s API endpoint for resource id: %s", endpoint, resource_id)
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("[!] Failed to find resource type %s at ID: %s", endpoint, resource_id)
