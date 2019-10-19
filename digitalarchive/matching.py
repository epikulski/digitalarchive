"""Helpers for searching the DA by Resource classes."""

# Standard Library
from __future__ import annotations
from typing import List

# Application modules
import digitalarchive.api as api
import digitalarchive.models as models
import digitalarchive.exceptions as exceptions


class SearchResult:
    """A results wrapper for a search against the DA API."""
    #pylint: disable=too-few-public-methods

    def __init__(self, resource: models.Resource, **kwargs):
        """
        Generate metadata about the results of a search query.

        :param resource: A DA model from digitalarchive.models.
        :param kwargs: Search Terms.
        """
        self.uri = kwargs.get("uri")
        self.sorting = kwargs.get("sorting")
        self.filtering = kwargs.get("filtering")
        self.list: List[models.Resource] = [
            resource(**item) for item in kwargs.get("list")
        ]


class ResourceMatcher:
    """Wraps instances of models.Resource to provide search functionality. """

    def __init__(self, resource: models.Resource, **kwargs):
        """
        Wrapper for search and query related functions.
        :param resource: A DA model object from digitalarchive.models
        :param kwargs: Search keywords to match on.
        """
        # Run a kwarg search for the passed object, return the resultset.

        # Set some properties for the search
        # * count of results
        # * list of results -- maybe a generator later?

        # Check that search keywords are valid for given model.
        for key in kwargs:
            if key not in resource.__dataclass_fields__.keys():
                raise exceptions.InvalidSearchField

        # if this is a request for a single record by ID, return only the record
        if kwargs.get("id"):
            response = api.DigitalArchive.get(
                endpoint=resource.endpoint, resource_id=kwargs.get("id")
            )
            # Wrap the response for SearchResult
            response = {"list": [response]}

        # If no resource_id present, treat as a search.
        else:
            response = api.DigitalArchive.search(model=resource.endpoint, params=kwargs)

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
        """Rehydrate all the Resources in a SearchResult.

        Probably I need to do a yield/generator thing so that the user can iterate
        through an all query and new pages are only fetched when needed. ` """
        for resource in self.result.list:
            resource.pull()
        return self.result
