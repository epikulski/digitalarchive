"""Custom Exceptions."""


class InvalidSearchFieldError(Exception):
    """User attempted to search on a field not valid for a given model."""

class MalformedDateSearch(InvalidSearchFieldError):
    """User passed a improperly formatted date. Required format: 'YYYYMMDD'"""


class NoSuchResourceError(Exception):
    """User attempted to retrieve a resource by ID#, but no such Resource exists"""


class APIServerError(Exception):
    """DA API returned a non-200 code for attempted operation."""

class MalformedLanguageSearch(InvalidSearchFieldError):
    """User passed a langauge search term that was not an instance of models.Language or an ISO 639-2/B string."""
