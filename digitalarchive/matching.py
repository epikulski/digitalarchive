"""
digitalrchive.matching

This module provides a ResourceMatcher class that provides search functionality for searchable model types.
"""

# Standard Library
from __future__ import annotations
from typing import Generator, List

# Application modules
import digitalarchive.api as api
import digitalarchive.models as models


class ResourceMatcher:
    """
    Runs a search against the DA API for the provided DA model and keywords.

    ResourceMatcher wraps search results and exposes methods for interacting with the resultant set of resources.

    Attributes:
        list(:obj:`Generator` of :class:`digitalarchive.models.Resource`) A Generator returning individual
            search results. Handles pagination of the DA API.
        count: The number of respondant records to the given search.
    """

    # pylint: disable=protected-access

    def __init__(
        self, resource_model: models.Resource, items_per_page=200, **kwargs
    ):
        """
        Parses search keywords, determines the kind of search to run, and constructs the results.

        :param resource_model: A model from :mod:`digitalarchive.models`.
        :param items_per_age: The number of search hits to include on each page of results.
        :param kwargs: Search keywords to match on.
        """
        self.model = resource_model
        self.query = kwargs
        self.list: Generator[models.Resource, None, None]
        self.count: int

        # if this is a request for a single record by ID, return only the record
        if self.query.get("id"):
            response = self._record_by_id()
            self.count = 1
            self.list = (self.model(**item) for item in response["list"])

        # If no resource_id present, treat as a search.
        else:
            # Fetch the first page of records from the API.
            self.query["itemsPerPage"] = items_per_page
            response = api.search(model=self.model.endpoint, params=self.query)

            # Calculate pagination, with handling depending on model type.
            if self.model in [
                models.Subject,
                models.Repository,
                models.Contributor,
                models.Coverage,
            ]:
                self.count = len(response["list"])
            else:
                self.count = response["pagination"]["totalItems"]

            # If first page contains all results, set list
            if self.count <= self.query["itemsPerPage"]:
                self.list = (self.model(**item) for item in response["list"])

            # If model is subject, skip pagination as the endpoint doesn't do it.
            elif self.model is models.Subject:
                self.list = (self.model(**item) for item in response["list"])

            # Set up generator to serve remaining results.
            else:
                self.list = self._get_all_search_results(response)

    def __repr__(self):
        return f"ResourceMatcher(model={self.model}, query={self.query}, count={self.count})"

    def _record_by_id(self) -> dict:
        """Get a single record by its ID."""
        response = api.get(
            endpoint=self.model.endpoint, resource_id=self.query.get("id")
        )
        # Wrap the response for SearchResult
        return {"list": [response]}

    def _get_all_search_results(self, response) -> models.Resource:
        """Create Generator to handle search result pagination."""
        page = response["pagination"]["page"]

        while page <= response["pagination"]["totalPages"]:
            # Yield resources in the current request.
            self.query["page"] = page
            response = api.search(model=self.model.endpoint, params=self.query)
            resources = [self.model(**item) for item in response["list"]]
            for resource in resources:
                yield resource

            # Fetch new resources if needed.
            page += 1

    def first(self) -> models.Resource:
        """Return only the first record from a search result."""
        if isinstance(self.list, Generator):
            return next(self.list)
        elif isinstance(self.list, list):
            return self.list[0]

    def all(self) -> List[models.Resource]:
        """
        Exhaust the results generator and return a list of all search results."""
        records = list(self.list)
        self.list = records
        return records

    def hydrate(self, recurse: bool = False):
        """Hydrate all of the resources in a search result."""
        # Fetch all the records.
        self.list = list(self.list)

        # Hydrate all the records.
        for resource in self.list:
            if isinstance(resource, models.Document):
                resource.hydrate(recurse=recurse)
            else:
                resource.hydrate()
