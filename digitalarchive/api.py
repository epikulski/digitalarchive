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
        """Search for DA records by endpoint and term."""

        # Transform search terms for api call. API matches on inconsistent things.

        # Handle record searches
        if endpoint == "record":
            params["q"] = params[""]

        # Handle non record/collection searches.
        else:
            if params.get("name"):
                params["term"] = params["name"]
            elif params.get("value"):
                params["term"] = params["value"]

        # Construct API URL.
        url = f"https://digitalarchive.wilsoncenter.org/srv/{endpoint}.json"

        logging.debug("[*] Querying %s API endpoint with params: %s", endpoint, str(params))
        response = requests.get(url, params=params)
        return response.json()

    @staticmethod
    def get(endpoint: str, resource_id: str) -> dict:
        """Retrieve a single record from the DA."""
        url = f"https://digitalarchive.wilsoncenter.org/srv/{endpoint}/{resource_id}.json"
        logging.debug("[*] Querying %s API endpoint for resource id: %s", endpoint, resource_id)
        response = requests.get(url)
        return response.json()
