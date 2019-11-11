"""Helpers for searching the DA."""

# Standard Library
from __future__ import annotations
from typing import Generator, List

# Application modules
import digitalarchive.api as api
import digitalarchive.models as models


class ResourceMatcher:
    """
    A wrapper for search results.

    ResourceMatcher wraps search results and exposes methods for intereacting with a result set.

    Attributes:
        list(:obj:`Generator` of :class:`digitalarchive.models._MatchableResource`) A Generator returning individual search results. Handles pagination of the DA API.
        count: The number of respondant records to the given search.

    """

    # pylint: disable=protected-access

    def __init__(
        self, resource_model: models._MatchableResource, items_per_page=200, **kwargs
    ):
        """
        Wrapper for search and query related functions.
        :param resource_model: A DA model object from digitalarchive.models
        :param items_per_age: The number of search hits to include on each page of results.
        :param kwargs: Search keywords to match on.
        """
        self.model = resource_model
        self.query = kwargs
        self.list: Generator[models._Resource, None, None]
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
        """Get a single record by ID."""
        response = api.get(
            endpoint=self.model.endpoint, resource_id=self.query.get("id")
        )
        # Wrap the response for SearchResult
        return {"list": [response]}

    def _get_all_search_results(self, response) -> models._MatchableResource:
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

    def first(self) -> models._MatchableResource:
        """Return only the first record from a search result."""
        if isinstance(self.list, Generator):
            return next(self.list)
        elif isinstance(self.list, list):
            return self.list[0]

    def all(self) -> List[models._MatchableResource]:
        """Return all results from a search."""
        records = list(self.list)
        self.list = records
        return records

    def hydrate(self, recurse: bool = False):
        """Hydrate all of the Resources in a resultset."""
        # Fetch all the records.
        self.list = list(self.list)

        # Hydrate all the records.
        for resource in self.list:
            if isinstance(resource, models.Document):
                resource.hydrate(recurse=recurse)
            else:
                resource.hydrate()
