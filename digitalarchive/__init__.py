"""
An unofficial Python client and ORM for the Wilson Center's Digital Archive.

Usage:
    >>> import digitalarchive
    >>> soviet_docs = digitalarchive.Document.match(name="soviet").all()

Full documentation at: <https://digitalarchive.readthedocs.io/en/latest/>

:copyright: (c) 2019 Evan Pikulski
:license: MIT, see LICENSE for more details.
"""
# __init__.py
__version__ = "0.1.7"

# Import all DA models for convenience.
from .models import (
    Subject,
    Contributor,
    Coverage,
    Collection,
    Repository,
    Document,
    Language,
    Transcript,
    Translation,
    MediaFile,
    Donor,
    Publisher,
    Type,
    Right,
    Classification,
    Theme,
)
