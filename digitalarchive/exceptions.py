"""
digitalarchive.exceptions

This module contains custom exceptions for the `digitalarchive` library.
"""


class InvalidSearchFieldError(Exception):
    """User attempted to search on a field that is not valid valid for the given model."""


class MalformedDateSearch(InvalidSearchFieldError):
    """User passed a improperly formatted date to a Document search. Expected format: 'YYYYMMDD'"""


class NoSuchResourceError(Exception):
    """User attempted to retrieve a DA resource by ID#, but no such resource existed"""


class APIServerError(Exception):
    """ The DA API returned a non-200 code for the attempted operation."""


class MalformedLanguageSearch(InvalidSearchFieldError):
    """Language search terms must be instance of models.Language or ISO 639-2/B string."""
