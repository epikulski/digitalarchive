"""ORM Models for DigitalArchive resource types.

todo: figure out a better way to represent unhydrated fields than 'none'.
"""
# pylint: disable=missing-class-docstring

from __future__ import annotations

# Standard Library
import logging
import copy
from dataclasses import dataclass
from typing import List, Any, Optional, Union

# Application Modules
import digitalarchive.matching as matching
import digitalarchive.api as api
import digitalarchive.exceptions as exceptions


class UnhydratedField:
    """A field that may be populated after the model is hydrated."""
    pass


@dataclass(eq=False)
class _Resource:
    """
    Abstract parent class for all DigitalArchive objects.

    We add custom hash and eq fields so hydrated and unhydrated records are equal.
    """

    id: str

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not self.__class__ == other.__class__:
            return NotImplemented
        else:
            return self.id == other.id


@dataclass(eq=False)
class _MatchableResource(_Resource):
    """Abstract class for Resources that can be searched against."""

    @classmethod
    def match(cls, **kwargs) -> matching.ResourceMatcher:
        """Find a record based on passed kwargs. Returns all if none passed"""
        return matching.ResourceMatcher(cls, **kwargs)


@dataclass(eq=False)
class _HydrateableResource(_Resource):
    """Abstract class for Resources that can be accessed and hydrated individually."""

    def pull(self):
        """Update a given record using data from the remote DA."""
        data = api.get(endpoint=self.endpoint, resource_id=self.id)
        self.__init__(**data)

    def hydrate(self):
        """
        Fix inconsistencies between views and hydrate.

        Note: Some models expose inconsistent fields between
        search results and when it is accessed directly via the
        collection.json endpoint.
        """
        # Preserve unhydrated fields.
        unhydrated_fields = copy.copy(self.__dict__)

        # Hydrate
        self.pull()
        hydrated_fields = vars(self)

        # Merge fields
        for key, value in unhydrated_fields.items():
            if hydrated_fields.get(key) is UnhydratedField:
                hydrated_fields[key] = value

        # Re-initialize the object.
        self.__init__(**hydrated_fields)


@dataclass(eq=False)
class Subject(_MatchableResource, _HydrateableResource):
    name: str

    # Optional fields
    uri: Union[str, UnhydratedField] = UnhydratedField
    value: Union[str, UnhydratedField] = UnhydratedField

    # Private fields
    endpoint: str = "subject"


@dataclass(eq=False)
class Language(_Resource):
    name: Union[str, UnhydratedField] = UnhydratedField


@dataclass(eq=False)
class _Asset(_HydrateableResource):
    """
    Abstract class representing fpr Translations, Transcriptions, and MediaFiles.

    Note: We don't define raw, html, or pdf here because they are not present on
    the stub version of Assets.
    """

    # pylint: disable=too-many-instance-attributes

    filename: str
    content_type: str
    extension: str
    asset_id: str
    source_created_at: str
    source_updated_at: str

    def __post_init__(self):
        """
        Instantiate some required fields for child classes.


        Note: This is awkward but necessary because dataclasses don't let
        you have non-default arguments in a child class. However,
        the MediaFile record type has a 'path' field instead of a 'url' field,
        which makes inheritance of a shared hydrate method awkward.
        """
        self.url = UnhydratedField
        self.raw = UnhydratedField
        self.pdf = UnhydratedField
        self.html = UnhydratedField

    def hydrate(self):
        response = api.SESSION.get(
            f"https://digitalarchive.wilsoncenter.org/{self.url}"
        )

        if response.status_code == 200:
            # Preserve the raw content from the DA in any case.
            self.raw = response.content

            # Add add helper attributes for the common filetypes.
            if self.extension == "html":
                self.html = response.text
                self.pdf = None
            elif self.extension == "pdf":
                self.pdf = response.content
                self.html = None
            else:
                logging.warning(
                    "[!] Unknown file format '%s' encountered!", self.extension
                )

        else:
            raise exceptions.APIServerError(
                f"[!] Hydrating asset ID#: %s failed with code: %s",
                self.id,
                response.status_code,
            )


@dataclass(eq=False)
class Transcript(_Asset):
    url: str
    html: Union[str, UnhydratedField] = UnhydratedField
    pdf: Union[str, UnhydratedField] = UnhydratedField
    raw: Union[str, UnhydratedField] = UnhydratedField

    def __post_init__(self):
        """See note on _Asset __post_init__ function."""
        pass  # pylint: disable=unnecessary-pass


@dataclass(eq=False)
class Translation(_Asset):
    url: str
    language: Union[Language, dict]
    html: Union[str, UnhydratedField] = UnhydratedField
    pdf: Union[str, UnhydratedField] = UnhydratedField
    raw: Union[str, UnhydratedField] = UnhydratedField

    def __post_init__(self):
        self.language = Language(*self.language)


@dataclass(eq=False)
class MediaFile(_Asset):
    path: str
    raw: Union[str, UnhydratedField] = UnhydratedField
    html: Union[str, UnhydratedField] = UnhydratedField
    pdf: Union[str, UnhydratedField] = UnhydratedField

    def __post_init__(self):
        self.url: str = self.path


@dataclass(eq=False)
class Contributor(_MatchableResource, _HydrateableResource):
    name: str
    value: Union[UnhydratedField, str] = UnhydratedField
    uri: Union[UnhydratedField, str] = UnhydratedField
    endpoint: str = "contributor"


@dataclass(eq=False)
class Donor(_Resource):
    name: str
    endpoint: str = "donor"


@dataclass(eq=False)
class Coverage(_MatchableResource, _HydrateableResource):
    """
    todo: instances of "any" below should be models.Coverage.
    """
    uri: str
    name: str
    value: Union[str, UnhydratedField] = UnhydratedField
    parent: Union[Any, UnhydratedField, None] = UnhydratedField
    children: Union[Any, UnhydratedField] = UnhydratedField
    endpoint: str = "coverage"

    def __post_init__(self):
        """

        DA returns dicts for parent in some cases, empty lists in others. Standardize on None.

        We also parse the children and parent fields, if they are present.
        """
        if isinstance(self.parent, list):
            self.parent = None

        # Parse the parent, if it is present.
        if not (
            isinstance(self.parent, Coverage) or
            self.parent is None or
            self.parent is UnhydratedField
        ):
            self.parent = Coverage(**self.parent)

        # If children are unhydrated or already parsed, don't attempt to parse
        if not (
            self.children is UnhydratedField or
            isinstance(self.children[0], Coverage)
        ):
            self.children = [Coverage(**child) for child in self.children]


@dataclass(eq=False)
class Collection(_MatchableResource, _HydrateableResource):
    # pylint: disable=too-many-instance-attributes
    # Required Fields
    name: str
    slug: str

    # Optional Fields
    uri: Union[str, UnhydratedField] = UnhydratedField
    parent: Optional[
        Any
    ] = UnhydratedField  # TODO: This should be Collection, figure out how to do it.

    model: Union[str, UnhydratedField] = UnhydratedField
    value: Union[str, UnhydratedField] = UnhydratedField
    description: Union[str, UnhydratedField] = UnhydratedField
    short_description: Union[str, UnhydratedField] = UnhydratedField
    main_src: Union[str, UnhydratedField] = UnhydratedField
    thumb_src: Union[str, UnhydratedField] = UnhydratedField
    no_of_documents: Union[str, UnhydratedField] = UnhydratedField
    is_inactive: Union[str, UnhydratedField] = UnhydratedField
    source_created_at: Union[str, UnhydratedField] = UnhydratedField
    source_updated_at: Union[str, UnhydratedField] = UnhydratedField
    first_published_at: Union[str, UnhydratedField] = UnhydratedField

    # Internal Fields
    endpoint: str = "collection"


@dataclass(eq=False)
class Repository(_MatchableResource, _HydrateableResource):
    name: str
    uri: Union[str, UnhydratedField] = UnhydratedField
    value: Union[str, UnhydratedField] = UnhydratedField
    endpoint: str = "repository"


@dataclass(eq=False)
class Publisher(_Resource):
    name: str
    value: str
    endpoint: str = "publisher"


@dataclass(eq=False)
class Type(_Resource):
    name: str


@dataclass(eq=False)
class Right(_Resource):
    name: str
    rights: str


@dataclass(eq=False)
class Classification(_Resource):
    name: str


@dataclass(eq=False)
class Document(_MatchableResource, _HydrateableResource):

    # pylint: disable=too-many-instance-attributes

    # Required Fields
    uri: str
    title: str
    description: str
    doc_date: str
    frontend_doc_date: str
    slug: str
    source_created_at: str
    source_updated_at: str
    first_published_at: str

    # Optional Fields
    source: Union[str, UnhydratedField] = UnhydratedField
    type: Union[Type, UnhydratedField] = UnhydratedField
    rights: Union[Right, UnhydratedField] = UnhydratedField
    pdf_generated_at: Union[str, UnhydratedField] = UnhydratedField
    date_range_start: Union[str, UnhydratedField] = UnhydratedField
    sort_string_by_coverage: Union[str, UnhydratedField] = UnhydratedField
    main_src: Optional[
        Any
    ] = UnhydratedField  # TODO: Never seen one of these in the while, so not sure how to handle.
    model: Union[str, UnhydratedField] = UnhydratedField

    # Optional Lists:

    donors: Union[List[Donor], UnhydratedField] = UnhydratedField
    subjects: Union[List[Subject], UnhydratedField] = UnhydratedField
    transcripts: Union[List[Transcript], UnhydratedField] = UnhydratedField
    translations: Union[List[Translation], UnhydratedField] = UnhydratedField
    media_files: Union[List[MediaFile], UnhydratedField] = UnhydratedField
    languages: Union[List[Language], UnhydratedField] = UnhydratedField
    contributors: Union[List[Contributor], UnhydratedField] = UnhydratedField
    creators: Union[List[Contributor], UnhydratedField] = UnhydratedField
    original_coverages: Union[List[Coverage], UnhydratedField] = UnhydratedField
    collections: Union[List[Collection], UnhydratedField] = UnhydratedField
    attachments: Union[
        List[Any], UnhydratedField
    ] = UnhydratedField  # TODO: Should be "document" -- fix.
    links: Union[
        List[Any], UnhydratedField
    ] = UnhydratedField  # TODO: Should be "document" -- fix.
    repositories: Union[List[Repository], UnhydratedField] = UnhydratedField
    publishers: Union[List[Publisher], UnhydratedField] = UnhydratedField
    classifications: Union[List[Classification], UnhydratedField] = UnhydratedField

    # Private properties
    endpoint: str = "record"

    def __post_init__(self):
        """Process lists of subordinate classes."""
        child_fields = {
            "subjects": Subject,
            "transcripts": Transcript,
            "media_files": MediaFile,
            "languages": Language,
            "creators": Contributor,
            "collections": Collection,
            "attachments": Document,
            "links": Document,
            "publishers": Publisher,
            "translations": Translation,
            "contributors": Contributor,
            "original_coverages": Coverage,
            "repositories": Repository,
            "classifications": Classification,
        }

        # If we are dealing with an unhydrated record, don't attempt to process child records.
        for field in child_fields:
            if self.__getattribute__(field) is UnhydratedField:
                return

        # If record is hydrated, transform child records to appropriate model.
        for field in child_fields:

            # Check if list is empty, skip if yes.
            if len(self.__getattribute__(field)) == 0:
                pass

            # If field is a list of dicts, transform those dicts to models and update self.
            else:
                sample_resource = self.__getattribute__(field)[0]
                if isinstance(sample_resource, dict):
                    parsed_resources = [
                        child_fields[field](**resource)
                        for resource in self.__getattribute__(field)
                    ]
                    setattr(self, field, parsed_resources)

    @classmethod
    def match(cls, **kwargs) -> matching.ResourceMatcher:
        """Custom matcher limits results to correct model.
        Known search options:
            * q: a str search term.

        """
        kwargs["model"] = "Record"
        return matching.ResourceMatcher(cls, **kwargs)

    def hydrate(self):
        """
        Hydrates document and subordinate assets.

        todo: See if i can implement the hydration and merge steps using super from _HydrateableResource
        """
        # Preserve unhydrated fields.
        unhydrated_fields = copy.copy(self.__dict__)

        # Hydrate
        self.pull()
        hydrated_fields = vars(self)

        # Merge fields
        for key, value in unhydrated_fields.items():
            if hydrated_fields.get(key) is UnhydratedField:
                hydrated_fields[key] = value

        # Re-initialize the object.
        self.__init__(**hydrated_fields)

        # Hydrate Assets
        [transcript.hydrate() for transcript in self.transcripts]
        [translation.hydrate() for translation in self.translations]
        [media_file.hydrate() for media_file in self.media_files]
        [collection.hydrate() for collection in self.collections]
