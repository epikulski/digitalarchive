from dataclasses import dataclass
from typing import List
from digitalarchive.api import DigitalArchive


class ResourceMatcher:

    def __init__(self, resource, **kwargs):
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
            response = DigitalArchive.get(resource.endpoint, resource_id=kwargs.get("id"))
            # Wrap the response for SearchResult
            response = {"list": [response]}

        # If no resource_id present, treat as a search.
        else:
            response = DigitalArchive.search(resource.endpoint, params=kwargs)

        self.query = kwargs
        self.result = SearchResult(resource, **response)
        self.count = len(self.result.list)

    def first(self):
        return self.result.list[0]

    def all(self):
        return self.result.list

    def hydrate(self):
        """todo: Finish this function."""
        for resource in self.result:
            resource.pull()
        return self.result


class SearchResult:

    def __init__(self, resource, **kwargs):
        """
        The results of a search via the DA API..
        :param resource: A DA model from digitalarchive.models
        :param kwargs: Search Term
        """
        self.uri: str = kwargs.get("uri")
        self.sorting: dict = kwargs.get("sorting")
        self.filtering: dict = kwargs.get("filtering")
        self.list: list = [resource(**item) for item in kwargs.get("list")]