"""Helpers for searching the DA."""

# Standard Library
from __future__ import annotations
from typing import Generator

# Application modules
import digitalarchive.api as api
import digitalarchive.models as models
import digitalarchive.exceptions as exceptions


class ResourceMatcher:
    """Wraps instances of models.Resource to provide search functionality. """

    def __init__(self, resource_model: models.Resource, items_per_page=200, **kwargs):
        """
        Wrapper for search and query related functions.
        :param resource_model: A DA model object from digitalarchive.models
        :param kwargs: Search keywords to match on.
        """
        self.model = resource_model
        self.query = kwargs
        self.list: Generator[models.Resource, None, None]
        self.count: int

        # Check that search keywords are valid for given model.
        for key in self.query:
            if key not in self.model.__dataclass_fields__.keys():
                raise exceptions.InvalidSearchFieldError

        # if this is a request for a single record by ID, return only the record
        if self.query.get("id"):
            response = self._record_by_id()
            self.count = 1
            self.list = (self.model(**item) for item in response["list"])

        # If no resource_id present, treat as a search.
        else:
            # Fetch the first page of records from the API.
            self.query["itemsPerPage"] = items_per_page
            response = api.search(
                model=self.model.endpoint, params=self.query
            )

            # pull out some metadata.
            self.count = response["pagination"]['totalItems']

            # If first page contains all results, set list
            if self.count <= self.query["itemsPerPage"]:
                self.list = (self.model(**item) for item in response["list"])

            # Set up generator to serve remaining results.
            else:
                self.list = self._get_all_search_results(response)

    def _record_by_id(self) -> dict:
        """Get a single record by ID."""
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
            response = api.search(
                model=self.model.endpoint, params=self.query
            )
            resources = [self.model(**item) for item in response["list"]]
            for resource in resources:
                yield resource

            # Fetch new resources if needed.
            page += 1

    def first(self) -> models.Resource:
        """Return only the first record from a SearchResult."""
        return next(self.list)

    def all(self) -> Generator[models.Resource, None, None]:
        """Return all records from a SearchResult."""
        return self.list

    def hydrate(self):
        # Fetch all the records.
        self.list = list(self.list)

        # Hydrate all the records.
        for resource in self.list:
            resource.hydrate()

