"""ORM Models for DigitalArchive resource types.

todo: figure out a better way to represent unhydrated fields than 'none'.
"""
# pylint: disable=missing-class-docstring

from __future__ import annotations

# Standard Library
import logging
import copy
from dataclasses import dataclass, field
from typing import List, Any, Optional, Union

# Application Modules
import digitalarchive.matching as matching
import digitalarchive.api as api
import digitalarchive.exceptions as exceptions


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
            if hydrated_fields.get(key) is None:
                hydrated_fields[key] = value

        # Re-initialize the object.
        self.__init__(**hydrated_fields)


@dataclass(eq=False)
class Subject(_MatchableResource, _HydrateableResource):
    name: str

    # Optional fields
    uri: Optional[str] = None
    value: Optional[str] = None

    # Private fields
    endpoint: str = "subject"


@dataclass(eq=False)
class Language(_Resource):
    name: Optional[str] = None


@dataclass(eq=False)
class _Asset(_HydrateableResource):
    """
    Abstract class representing fpr Translations, Transcriptions, and MediaFiles.

    Note: We don't define raw, html, or pdf here because they are not present on
    the stub version of Assets.
    """

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
        self.url = None
        self.raw = None
        self.pdf = None
        self.html = None

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
            elif self.extension == "pdf":
                self.pdf = response.content
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
    html: Optional[str] = None
    pdf: Optional[bytes] = None
    raw: Optional[bytes] = None

    def __post_init__(self):
        """See note on _Asset __post_init__ function."""
        pass  # pylint: disable=unnecessary-pass


@dataclass(eq=False)
class Translation(_Asset):
    url: str
    language: Union[Language, dict]
    html: Optional[str] = None
    pdf: Optional[bytes] = None
    raw: Optional[bytes] = None

    def __post_init__(self):
        self.language = Language(**self.language)


@dataclass(eq=False)
class MediaFile(_Asset):
    path: str
    raw: Optional[bytes] = None
    html: Optional[str] = None
    pdf: Optional[str] = None

    def __post_init__(self):
        self.url: str = self.path


@dataclass(eq=False)
class Contributor(_MatchableResource, _HydrateableResource):
    name: str
    endpoint: str = "contributor"


@dataclass(eq=False)
class Donor(_Resource):
    name: str
    endpoint: str = "donor"


@dataclass(eq=False)
class Coverage(_MatchableResource, _HydrateableResource):
    uri: str
    name: str
    parent: Any
    endpoint: str = "coverage"


@dataclass(eq=False)
class Collection(_MatchableResource, _HydrateableResource):
    # Required Fields
    name: str
    slug: str

    # Optional Fields
    uri: Optional[str] = None
    parent: Optional[
        Any
    ] = None  # TODO: This should be Collection, figure out how to do it.

    model: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    main_src: Optional[str] = None
    thumb_src: Optional[str] = None
    no_of_documents: Optional[str] = None
    is_inactive: Optional[str] = None
    source_created_at: Optional[str] = None
    source_updated_at: Optional[str] = None
    first_published_at: Optional[str] = None

    # Internal Fields
    endpoint: str = "collection"


@dataclass(eq=False)
class Repository(_MatchableResource, _HydrateableResource):
    name: str
    uri: Optional[str] = None
    value: Optional[str] = None
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
    source: Optional[str] = None
    type: Optional[Type] = None
    rights: Optional[Right] = None
    pdf_generated_at: Optional[str] = None
    date_range_start: Optional[str] = None
    sort_string_by_coverage: Optional[str] = None
    main_src: Optional[
        Any
    ] = None  # TODO: Never seen one of these in the while, so not sure how to handle.
    model: Optional[str] = None

    # Optional Lists:

    donors: List[Donor] = field(default_factory=list)
    subjects: List[Subject] = field(default_factory=list)
    transcripts: List[Transcript] = field(default_factory=list)
    translations: List[Translation] = field(default_factory=list)
    media_files: List[MediaFile] = field(default_factory=list)
    languages: List[Language] = field(default_factory=list)
    contributors: List[Contributor] = field(default_factory=list)
    creators: List[Contributor] = field(default_factory=list)
    original_coverages: List[Coverage] = field(default_factory=list)
    collections: List[Collection] = field(default_factory=list)
    attachments: List[Any] = field(
        default_factory=list
    )  # TODO: Should be "document" -- fix.
    links: List[Any] = field(default_factory=list)  # TODO: Should be "document" -- fix.
    repositories: List[Repository] = field(default_factory=list)
    publishers: List[Publisher] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    # Private properties
    endpoint: str = "record"

    def __post_init__(self):
        """Process lists of subordinate classes."""
        self.subjects = [Subject(**subject) for subject in self.subjects]
        self.transcripts = [Transcript(**transcript) for transcript in self.transcripts]
        self.media_files = [MediaFile(**media_file) for media_file in self.media_files]
        self.languages = [Language(**language) for language in self.languages]
        self.creators = [Contributor(**creator) for creator in self.creators]
        self.collections = [Collection(**collection) for collection in self.collections]
        self.attachments = [Document(**attachment) for attachment in self.attachments]
        self.links = [Document(**document) for document in self.links]
        self.publishers = [Publisher(**publisher) for publisher in self.publishers]
        self.translations = [Translation(**transl) for transl in self.translations]
        self.contributors = [Contributor(**contrib) for contrib in self.contributors]
        self.original_coverages = [Coverage(**cov) for cov in self.original_coverages]
        self.repositories = [Repository(**repo) for repo in self.repositories]
        self.classifications = [
            Classification(**classification) for classification in self.classifications
        ]

    @classmethod
    def match(cls, **kwargs) -> matching.ResourceMatcher:
        """Custom matcher limits results to correct model.
        Known search options:
            * q: a str search term.

        """
        kwargs["model"] = "Record"
        return matching.ResourceMatcher(cls, **kwargs)

    def hydrate(self):
        """Hydrates document and subordinate assets."""
        # Hydrate the document
        self.pull()

        # Hydrate Assets
        [transcript.hydrate() for transcript in self.transcripts]
        [translation.hydrate() for translation in self.translations]
        [media_file.hydrate() for media_file in self.media_files]
        [collection.hydrate() for collection in self.collections]
