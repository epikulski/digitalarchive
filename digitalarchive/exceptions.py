"""Custom Exceptions."""


class InvalidSearchFieldError(Exception):
    """User attempted to search on a field not valid for a given model."""


class NoSuchResourceError(Exception):
    """User attempted to retrieve a resource by ID#, but no such Resource exists"""


class APIServerError(Exception):
    """DA API returned a non-200 code for attempted operation."""
