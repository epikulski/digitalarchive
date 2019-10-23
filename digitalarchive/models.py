"""ORM Models for DigitalArchive resource types.

todo: figure out a better way to represent unhydrated fields than 'none'.
"""
# pylint: disable=missing-class-docstring

from __future__ import annotations

# Standard Library
import logging
from dataclasses import dataclass, field
from typing import List, Any, Optional, Union

# Application Modules
import digitalarchive.matching as matching
import digitalarchive.api as api
import digitalarchive.exceptions as exceptions


@dataclass
class Resource:
    """Abstract parent class for all DigitalArchive objects."""

    id: str

    @classmethod
    def match(cls, **kwargs) -> matching.ResourceMatcher:
        """Find a record based on passed kwargs. Returns all if none passed"""
        return matching.ResourceMatcher(cls, **kwargs)

    def pull(self):
        """Update a given record using data from the remote DA."""
        data = api.get(endpoint=self.endpoint, resource_id=self.id)
        self.__init__(**data)

    def hydrate(self):
        """Alias for Resource.pull"""
        self.pull()


@dataclass
class Subject(Resource):
    name: str

    # Optional fields
    uri: Optional[str] = None
    value: Optional[str] = None

    # Private fields
    endpoint: str = "subject"


@dataclass
class Language(Resource):
    name: Optional[str] = None


@dataclass
class _Asset(Resource):
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


@dataclass
class Transcript(_Asset):
    url: str
    html: Optional[str] = None
    pdf: Optional[bytes] = None
    raw: Optional[bytes] = None

    def __post_init__(self):
        """See note on _Asset __post_init__ function."""
        pass  # pylint: disable=unnecessary-pass


@dataclass
class Translation(_Asset):
    url: str
    language: Union[Language, dict]
    html: Optional[str] = None
    pdf: Optional[bytes] = None
    raw: Optional[bytes] = None

    def __post_init__(self):
        self.language = Language(**self.language)


@dataclass
class MediaFile(_Asset):
    path: str
    raw: Optional[bytes] = None
    html: Optional[str] = None
    pdf: Optional[str] = None

    def __post_init__(self):
        self.url: str = self.path


@dataclass
class Contributor(Resource):
    name: str
    endpoint: str = "contributor"


@dataclass
class Donor(Resource):
    name: str
    endpoint: str = "donor"


@dataclass
class Coverage(Resource):
    uri: str
    name: str
    parent: Any
    endpoint: str = "coverage"


@dataclass
class Collection(Resource):
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


@dataclass
class Repository(Resource):
    name: str
    uri: Optional[str] = None
    value: Optional[str] = None
    endpoint: str = "repository"


@dataclass
class Publisher(Resource):
    name: str
    value: str
    endpoint: str = "publisher"


@dataclass
class Type(Resource):
    name: str


@dataclass
class Right(Resource):
    name: str
    rights: str


@dataclass
class Classification(Resource):
    name: str


@dataclass
class Document(Resource):

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
