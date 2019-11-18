"""Helpers for searching the DA."""

# Standard Library
from __future__ import annotations
import asyncio

# 3rd Party Libraries
import aiohttp
import multidict

# Application modules
import digitalarchive.api as api
import digitalarchive.models as models


class ResourceMatcher:
    """
    A wrapper for search results.

    ResourceMatcher wraps search results and exposes methods for intereacting with a result set.

    Attributes:
        list (:obj:`Generator` of :class:`digitalarchive.models._MatchableResource`) A Generator returning individual
            search results. Handles pagination of the DA API.
        count (int): The number of respondant records to the given search.

    """
    # pylint: disable=protected-access

    def __init__(
        self, resource_model: models._MatchableResource, query: multidict.MultiDict, items_per_page=200
    ):
        """
        Wrapper for search and query related functions.
        :param resource_model: A DA model object from digitalarchive.models
        :param items_per_age: The number of search hits to include on each page of results.
        :param kwargs: Search keywords to match on.
        """
        self.model = resource_model
        self.query = query

        # Set up typing for attributes populated after the search.
        self.list: list
        self.count: int
        self.current_page: int
        self.total_pages: int

        # if this is a request for a single record by ID, return only the record
        if self.query.get("id"):
            response = self._record_by_id()
            self.count = 1
            self.list = [self.model(**item) for item in response["list"]]

        # If no resource_id present, treat as a search.
        else:
            # Fetch the first page of records from the API.
            self.query["itemsPerPage"] = items_per_page
            response = asyncio.run(api.search(model=self.model.endpoint, params=self.query))

            # Calculate pagination, with handling depending on model type.
            if self.model in [
                models.Subject,
                models.Repository,
                models.Contributor,
                models.Coverage,
            ]:
                self.count = len(response["list"])
                self.current_page = 1
                self.total_pages = 1

            else:
                self.count = response["pagination"]["totalItems"]
                self.current_page = response["pagination"]["page"]
                self.total_pages = response["pagination"]["totalPages"]

            # Set list to first page of results.
            self.list = [self.model(**item) for item in response["list"]]

    def __repr__(self):
        return f"ResourceMatcher(model={self.model}, query={self.query}, count={self.count})"

    def _record_by_id(self) -> dict:
        """Get a single record by ID."""
        response = asyncio.run(
            api.get(endpoint=self.model.endpoint, resource_id=self.query.get("id"))
        )
        # Wrap the response for SearchResult
        return {"list": [response]}

    async def _get_all_search_results(self):
        # Calculate the queries we will need to send.
        session = aiohttp.ClientSession()
        pages = range(self.current_page, (self.total_pages + 1))
        queries = []
        for page in pages:
            query = self.query.copy()
            query["page"] = page
            queries.append(query)

        # Prepare the searches we will need to send.
        responses = [api.search(model=self.model.endpoint, params=query, session=session) for query in queries]

        # Run our searches and extract payloads.
        responses = await asyncio.gather(*responses)
        results = []
        for response in responses:
            results.extend(response["list"])

        # Parse the payloads and clean up session.
        self.list = [self.model(**result) for result in results]
        await session.close()

    def first(self) -> models._MatchableResource:
        """Return only the first record from a search result."""
        return self.list[0]

    def all(self) -> list:
        """
        Return all results from a search.

        Returns:
            list of :class:`digitalarchive.models._MatchableResource.
        """
        # If there was only one page of results, return it immediately.
        if self.current_page == self.total_pages:
            return self.list
        else:
            asyncio.run(self._get_all_search_results())
            return self.list

    def hydrate(self, recurse: bool = False):
        """Hydrate all of the Resources in a resultset."""
        # Fetch all the records.
        self.list = list(self.list)
        asyncio.run(self._async_hydrate(recurse=recurse))

    async def _async_hydrate(self, recurse: bool):
        session = aiohttp.ClientSession()
        await asyncio.gather(
            *[
                resource._async_hydrate(session=session, recurse=recurse)
                for resource in self.list
            ]
        )
        await session.close()
