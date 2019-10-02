from dataclasses import dataclass, field
from typing import List, Any, Optional

from .matching import ResourceMatcher
from .api import DigitalArchive


@dataclass
class Resource:
    id: str

    @classmethod
    def match(cls, **kwargs) -> ResourceMatcher:
        """Find a record based on passed kwargs. Returns all if none passed"""
        return ResourceMatcher(cls, **kwargs)

    def pull(self):
        """Update a given record from the remote DA."""
        data = DigitalArchive.get(endpoint=self.endpoint, resource_id=self.id)
        self.__init__(**data)


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
    name: str


@dataclass
class Asset:
    """todo: Figure out endpoint logic for media files/translations/trascripts"""

    id: str
    filename: str
    content_type: str
    extension: str
    asset_id: str
    source_created_at: str
    source_updated_at: str


@dataclass
class Transcript(Asset):
    url: str
    pass


@dataclass
class Translation(Asset):
    url: str
    language: Language
    pass


@dataclass
class MediaFile(Asset):
    path: str
    pass


@dataclass
class Contributor:
    id: str
    name: str
    _endpoint: str = "contributor"


@dataclass
class Donor:
    id: str
    name: str
    _endpoint: str = "donor"


@dataclass
class Coverage:
    uri: str
    id: str
    name: str
    parent: Any
    _endpoint: str = "coverage"


@dataclass
class Collection:
    id: str
    name: str
    slug: str
    parent: Optional[
        Any
    ] = None  # TODO: This should be Collection, figure out how to do it.
    endpoint: str = "collection"

    @classmethod
    def match(cls, **kwargs) -> ResourceMatcher:
        """Custom matcher limits results to correct model."""
        kwargs["model"] = "Collection"
        return ResourceMatcher(cls, **kwargs)


@dataclass
class Repository:
    id: str
    name: str
    uri: Optional[str] = None
    value: Optional[str] = None
    _endpoint: str = "repository"


@dataclass
class Publisher:
    id: str
    name: str
    value: str
    _endpoint: str = "publisher"


@dataclass
class Type:
    id: str
    name: str


@dataclass
class Right:
    id: str
    name: str
    rights: str


@dataclass
class Classification:
    id: str
    name: str


@dataclass
class Document(Resource):

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
    ] = None  # TODO: Never seen one of these in the while, so not sure
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
        self.translations = [Translation(**translation) for translation in self.translations]
        self.media_files = [MediaFile(**media_file) for media_file in self.media_files]
        self.languages = [Language(**language) for language in self.languages]
        self.contributors = [Contributor(**contributor) for contributor in self.contributors]
        self.creators = [Contributor(**creator) for creator in self.creators]
        self.original_coverages = [Coverage(**coverage) for coverage in self.original_coverages]
        self.collections = [Collection(**collection) for collection in self.collections]
        self.attachments = [Document(**attachment) for attachment in self.attachments]
        self.links = [Document(**document) for document in self.links]
        self.repositories = [Repository(**repository) for repository in self.repositories]
        self.publishers = [Publisher(**publisher) for publisher in self.publishers]
        self.classifications = [Classification(**classification) for classification in self.classifications]

    @classmethod
    def match(cls, **kwargs) -> ResourceMatcher:
        """Custom matcher limits results to correct model.
        Known search options:
            * q: a str search term.

        """
        kwargs["model"] = "Record"
        return ResourceMatcher(cls, **kwargs)
