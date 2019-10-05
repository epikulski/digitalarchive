"""Helpers for searching the DA by Resource classes."""

# Standard Library
from __future__ import annotations
from dataclasses import dataclass
from typing import List

# Application modules
import digitalarchive.api as api
import digitalarchive.models as models


class SearchResult:
    """A results wrapper for a search against the DA API."""

    def __init__(self, resource: models.Resource, **kwargs):
        """
        Generate metadata about the results of a search query.

        :param resource: A DA model from digitalarchive.models.
        :param kwargs: Search Terms.
        """
        self.uri: str = kwargs.get("uri")
        self.sorting: dict = kwargs.get("sorting")
        self.filtering: dict = kwargs.get("filtering")
        self.list: List[models.Resource] = [resource(**item) for item in kwargs.get("list")]


class ResourceMatcher:
    """Wraps instances of models.Resource to provide search functionality. """

    def __init__(self, resource: models.Resource, **kwargs):
        """
        Wrapper for search and query related functions.
        :param resource: A DA model object from digitalarchive.models
        :param kwargs:
        """
        # Run a kwarg search for the passed object, return the resultset.

        # Set some properties for the search
        # * count of results
        # * list of results -- maybe a generator later?

        # if this is a request for a single record by ID, return only the record
        if kwargs.get("id"):
            response = api.DigitalArchive.get(endpoint=resource.endpoint, resource_id=kwargs.get("id"))
            # Wrap the response for SearchResult
            response = {"list": [response]}

        # If no resource_id present, treat as a search.
        else:
            response = api.DigitalArchive.search(endpoint=resource.endpoint, params=kwargs)

        self.query = kwargs
        self.result = SearchResult(resource, **response)
        self.count = len(self.result.list)

    def first(self) -> models.Resource:
        """Return only the first record from a SearchResult."""
        return self.result.list[0]

    def all(self) -> List[models.Resource]:
        """Return all records from a SearchResult.
        todo: Add logic here for paginating through all the results in the set.
        """
        return self.result.list

    def hydrate(self) -> SearchResult:
        """Rehydrate all the Resources in a SearchResult."""
        for resource in self.result.list:
            resource.pull()
        return self.result
