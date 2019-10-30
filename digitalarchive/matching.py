"""Helpers for searching the DA."""

# Standard Library
from __future__ import annotations
import logging
from typing import Generator
from datetime import date

# Application modules
import digitalarchive.api as api
import digitalarchive.models as models
import digitalarchive.exceptions as exceptions


class ResourceMatcher:
    """Wraps instances of models.Resource to provide search functionality. """

    # pylint: disable=protected-access

    def __init__(
        self, resource_model: models._MatchableResource, items_per_page=200, **kwargs
    ):
        """
        Wrapper for search and query related functions.
        :param resource_model: A DA model object from digitalarchive.models
        :param kwargs: Search keywords to match on.
        """
        self.model = resource_model
        self.query = kwargs
        self.list: Generator[models._Resource, None, None]
        self.count: int

        # Check and parse date searches.
        date_range_searches = ["start_date", "end_date"]
        for field in date_range_searches:
            if field in self.query.keys():
                self._process_date_searches()
                break

        # Check that search keywords are valid for given model.
        allowed_search_fields = [*self.model.__dataclass_fields__.keys()]

        if self.model is models.Document:
            allowed_search_fields.extend(date_range_searches)
            allowed_search_fields.append("themes")

        for key in self.query:
            if key not in allowed_search_fields:
                raise exceptions.InvalidSearchFieldError

        # Extract id from searches that are models.
        self._process_related_model_searches()

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

    def _process_related_model_searches(self):
        """
        Process and format searches by related models.

        We have to re-name the fields from plural to singular to match the DA format.
        :return:
        """
        multi_terms = {
            "collections": "collection",
            "publishers": "publisher",
            "repositories": "repository",
            "original_coverages": "coverage",
            "subjects": "subject",
            "contributors": "contributor",
            "donors": "donor",
            "languages": "language",
            "translations": "translation",
            "themes": "theme",
        }

        # Rename each term to singular
        for key, value in multi_terms.items():
            if key in self.query.keys():
                self.query[value] = self.query.pop(key)

        # Build list of terms we need to parse
        terms_to_parse = []
        for term in multi_terms.values():
            if term in self.query.keys():
                terms_to_parse.append(term)

        # transform each term list into a list of IDs
        for term in terms_to_parse:
            self.query[term] = [str(item.id) for item in self.query[term]]

        # Special handling for langauges, translations, themes.
        # Unlike they above, they only accept singular values
        for term in ["language", "translation", "theme"]:
            if term in self.query.keys():
                if len(self.query[term]) > 1:
                    logging.error(f"[!] Cannot filter for more than one {term}")
                    raise exceptions.InvalidSearchFieldError
                # Pull out the singleton.
                self.query[term] = self.query[term][0]

        print("break")

        # # Remove fields we don't need to parse
        # multi_terms = [term for term in multi_terms.items() if term in self.query.keys()]
        # terms.extend([term for term in singular_terms if term in self.query.keys()])

        # Pull out IDs from each term
        # for key, value in multi_terms:
        #     self.query[key] = [str(item.id) for item in self.query[key]]

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

    def _process_date_searches(self):
        """Run formatting and type checks against  date search fields."""
        date_search_terms = ["start_date", "end_date"]

        # Restrict date searches to digitalarchive.models.Document
        if self.model is not models.Document:
            logging.error(
                "[!] Date range searches supported only for digitalarchive.Document model."
            )
            raise exceptions.InvalidSearchFieldError

        # Handle open-ended date searches.
        if "start_date" in self.query.keys() and "end_date" not in self.query.keys():
            self.query["end_date"] = date.today()
        elif "end_date" in self.query.keys() and "start_date" not in self.query.keys():
            # Pull earliest record date from API.
            da_date_range = api.get_date_range()
            start_date = models.Document._parse_date_range_start(da_date_range["begin"])
            self.query["start_date"] = start_date

        # Transform datetime objects into formatted string and return
        for field in date_search_terms:
            search_date = self.query[field]
            if isinstance(search_date, date):
                self.query[
                    field
                ] = f"{search_date.year}{search_date.strftime('%m')}{search_date.strftime('%d')}"

            # Check string length and return if OK.
            elif isinstance(search_date, str) and len(search_date) == 8:
                pass

            # If passed a string but its wrong length, raise.
            elif isinstance(search_date, str) and len(search_date) != 8:
                logging.error("[!] Invalid date string! Format is: YYYYMMDD")
                raise exceptions.MalformedDateSearch

            # If something else passed as keyword, bail out.
            else:
                logging.error("[!] Dates must be type str or datetime.date")
                raise exceptions.MalformedDateSearch

    def first(self) -> models._MatchableResource:
        """Return only the first record from a SearchResult."""
        return next(self.list)

    def all(self) -> Generator[models._MatchableResource, None, None]:
        """Return all records from a SearchResult."""
        return self.list

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
