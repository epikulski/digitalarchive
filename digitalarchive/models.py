"""
digitalarchive.models

The module provides documented models and an ORM for interacting with the DA API.
"""
from __future__ import annotations

# Standard Library
import logging
import copy
from datetime import datetime, date
from dataclasses import dataclass
from typing import List, Any, Optional, Union
from abc import ABC

# Application Modules
import digitalarchive.matching as matching
import digitalarchive.api as api
import digitalarchive.exceptions as exceptions


class UnhydratedField:
    """A field whose content is unknown until its parent :class:`_Resource` has been hydrated."""

    pass


@dataclass(eq=False)
class Resource(ABC):
    """
    Abstract parent for all DigitalArchive objects.

    We add custom hash and eq fields so that hydrated and unhydrated records are equal.
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
class MatchingMixin:
    """Abstract parent for Resources that can be searched against."""

    @classmethod
    def match(cls, **kwargs) -> matching.ResourceMatcher:
        """Find a resource using passed keyword arguments.

        Note:
            If called without arguments, returns all records in the DA .
        """

        # Check that we no invalid search terms were passed.
        for key in kwargs:
            if key not in cls.__dataclass_fields__.keys():
                raise exceptions.InvalidSearchFieldError

        # Prepare the "term" search field.
        # If we've got both a name and a value, join them.
        if kwargs.get("name") and kwargs.get("value"):
            kwargs["term"] = " ".join([kwargs.pop("name"), kwargs.pop("value")])

        # Otherwise, treat the one that exists as the term.
        elif kwargs.get("name"):
            kwargs["term"] = kwargs.pop("name")
        elif kwargs.get("value"):
            kwargs["term"] = kwargs.pop("value")

        return matching.ResourceMatcher(cls, **kwargs)


@dataclass(eq=False)
class HydrateMixin:
    """Mixin for resources that can be individually accessed and hydrated."""

    def pull(self):
        """Update the resource using data from the DA API."""
        data = api.get(endpoint=self.endpoint, resource_id=self.id)
        self.__init__(**data)

    def hydrate(self):
        """
        Populate all unhydrated fields of a resource.
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


class TimestampsMixin:
    """Mixin for resources that have publication timestamp metadata."""

    # pylint: disable=too-few-public-methods

    def _process_timestamps(self):
        # Turn date fields from strings into datetimes.
        datetime_fields = [
            "source_created_at",
            "source_updated_at",
            "first_published_at",
        ]

        for field in datetime_fields:
            if isinstance(self.__getattribute__(field), str):
                setattr(
                    self, field, datetime.fromisoformat(self.__getattribute__(field))
                )


@dataclass(eq=False)
class Subject(Resource, MatchingMixin, HydrateMixin):
    """
    A historical topic to which documents can be related.

    Attributes:
        id (str): The ID of the record.
        name (str): The name of the subject.
        value (str): An alias for :attr:`~digitalarchive.models.Subject.name`.
        uri (str): The URI for the Subject in the API.
    """

    name: str

    # Optional fields
    value: Union[str, UnhydratedField] = UnhydratedField
    uri: Union[str, UnhydratedField] = UnhydratedField

    # Private fields
    endpoint: str = "subject"


@dataclass(eq=False)
class Language(Resource):
    """
    The original language of a resource.

    Attributes:
        id (str): An ISO 639-2/B language code.
        name (str): The ISO language name for the language.
    """

    name: Union[str, UnhydratedField] = UnhydratedField


@dataclass(eq=False)
class Asset(Resource, ABC, HydrateMixin):
    """
    Abstract parent for Translations, Transcriptions, and MediaFiles.

    Note:
        We don't define raw, html, or pdf here because they are not present on
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
        Instantiate some required fields for child assets.

        This is awkward but necessary because dataclasses don't let
        you have non-default arguments in a child class. However,
        the MediaFile record type has a 'path' field instead of a 'url' field,
        which makes inheritance of a shared hydrate method awkward.
        """
        self.url = UnhydratedField
        self.raw = UnhydratedField
        self.pdf = UnhydratedField
        self.html = UnhydratedField

    def hydrate(self):
        """Populate all unhydrated fields of a :class:`digitalarchive.models._Asset`."""
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
class Transcript(Asset):
    """A transcript of a document in its original language.

    Attributes:
          id (str): The ID# of the Transcript.
          url (str): A URL to accessing the hydrated Transcript.
          html (str): The html of of the Transcript.
          pdf (bytes): A bytes object of the Transcript pdf content.
          raw (str or bytes): The raw content recieved from the DA API for the Transcript.
          filename (str): The filename of the Transcript on the content server.
          content_type (str): The MIME type of the Transcript file.
          extension (str): The file extension of the Transcript.
          asset_id (str): The Transcript's unique ID on the content server.
          source_created_at (str): ISO 8601 timestamp of the first time the Translation was published.
          source_updated_at (str): ISO 8601 timestamp of the last time the Translation was modified.
    """

    url: str
    html: Union[str, UnhydratedField] = UnhydratedField
    pdf: Union[bytes, UnhydratedField] = UnhydratedField
    raw: Union[str, bytes, UnhydratedField] = UnhydratedField

    def __post_init__(self):
        """See note on Asset __post_init__ function."""
        pass  # pylint: disable=unnecessary-pass


@dataclass(eq=False)
class Translation(Asset):
    """
    A translation of a Document into a another language.

    Attributes:
        id (str): The ID# of the Translation.
        language (:class:`digitalarchive.models.Language`) The langauge of the Translation.
        html (str): The HTML-formatted text of the Translation.
        pdf (bytes): A bytes object of the Translation pdf content.
        raw (str or bytes): The raw content recieved from the DA API for the Translation.
        filename (str): The filename of the Translation on the content server.
        content_type (str): The MIME type of the Translation file.
        extension (str): The file extension of the Translation.
        asset_id (str): The Translation's unique ID on the content server.
        source_created_at (str): ISO 8601 timestamp of the first time the Translation was published.
        source_updated_at (str): ISO 8601 timestamp of the last time the Translation was modified.
    """

    url: str
    language: Union[Language, dict]
    html: Union[str, UnhydratedField, None] = UnhydratedField
    pdf: Union[bytes, UnhydratedField, None] = UnhydratedField
    raw: Union[str, UnhydratedField] = UnhydratedField

    def __post_init__(self):
        self.language = Language(**self.language)


@dataclass(eq=False)
class MediaFile(Asset):
    """
    An original scan of a Document.

    Attributes:
        id (str): The ID# of the MediaFile.
        pdf (bytes): A bytes object of the MediaFile content.
        raw (str or bytes): The raw content received from the DA API for the MediaFile.
        filename (str): The filename of the MediaFile on the content server.
        content_type (str): The MIME type of the MediaFile file.
        extension (str): The file extension of the MediaFile.
        asset_id (str): The MediaFile's unique ID on the content server.
        source_created_at (str): ISO 8601 timestamp of the first time the MediaFile was published.
        source_updated_at (str): ISO 8601 timestamp of the last time the MediaFile was modified.
    """

    path: str
    raw: Union[str, UnhydratedField] = UnhydratedField
    pdf: Union[str, UnhydratedField] = UnhydratedField

    def __post_init__(self):
        self.url: str = self.path


@dataclass(eq=False)
class Contributor(Resource, MatchingMixin, HydrateMixin):
    """
    An individual person or organization that contributed to the creation of the document.

    Contributors are typically the Document's author, but for meeting minutes and similar documents,
    a Contributor may simply be somebody who was in attendance at the meeting.

    Attributes:
        id (str): The ID# of the Contributor.
        name (str): The name of the contributor.
        uri (str): The URI of the contributor metadata on the DA API.
    """

    name: str
    value: Union[UnhydratedField, str] = UnhydratedField
    uri: Union[UnhydratedField, str] = UnhydratedField
    endpoint: str = "contributor"


@dataclass(eq=False)
class Donor(Resource):
    """
    An entity whose resources helped publish or translate a document.

    Attributes:
        id (str): The ID# of the Donor.
        name (str): The name of the Donor.
    """

    name: str
    endpoint: str = "donor"


@dataclass(eq=False)
class Coverage(Resource, MatchingMixin, HydrateMixin):
    """
    A geographical area referenced by a Document.

    Attributes:
        id (str): The ID# of the geographic Coverage.
        name (str): The name of geographic coverage area.
        value (str): An alias to :attr:`~digitalarchive.models.Coverage.name`.
        uri (str): URI to the Coverage's metadata on the DA API.
        parent (:class:`~digitalarchive.models.Coverage`): The parent coverage,
            if any
        children: (list of :class:`~digitalarchive.models.Covereage`):
            Subordinate geographical areas, if any.
    """

    name: str
    uri: str
    value: Union[str, UnhydratedField] = UnhydratedField
    parent: Union[Any, UnhydratedField, None] = UnhydratedField
    children: Union[list, UnhydratedField] = UnhydratedField
    endpoint: str = "coverage"

    def __post_init__(self):
        """
        Standardize output of coverage data across differnet DA endpoints.

        The DA returns dicts for parent in some cases, empty lists in others. We standardize on None. We also parse the
        children and parent fields, if they are present.
        """
        if isinstance(self.parent, list):
            self.parent = None

        # Parse the parent, if it is present.
        if not (
            isinstance(self.parent, Coverage)
            or self.parent is None
            or self.parent is UnhydratedField
        ):
            self.parent = Coverage(**self.parent)

        # If children are unhydrated or already parsed, don't attempt to parse
        if not (
            self.children is UnhydratedField or isinstance(self.children[0], Coverage)
        ):
            self.children = [Coverage(**child) for child in self.children]


@dataclass(eq=False)
class Collection(Resource, MatchingMixin, HydrateMixin, TimestampsMixin):
    """
    A collection of Documents on a single topic

    Attributes:
        name (str): The title of the collection.
        slug (str): A url-friendly name of the collection.
        uri (str): The URI of the record on the DA API.
        parent(:class:`digitalarchive.models.Collection`): A `Collection` containing the `Collection`.
        model (str): A sting name of the model used to differentiate `Collection` and `Document` searches in the DA API.
        value (str): A string identical to the `title` field.
        description (str): A 1-2 sentence description of the `Collection`'s content.
        short_description (str): A short description that appears in search views.
        main_src (str): Placeholder
        no_of_documents (str):  The count of documents contained in the collection.
        is_inactive (str): Whether the collection is displayed in the collections list.
        source_created_at(:class:`datetime.datetime`): Timestamp of when the Document was first added to the DA.
        source_updated_at(:class:`datetime.datetime`): Timestamp of when the Document was last edited.
        first_published_at(:class:`datetime.datetime`): Timestamp of when the document was first made publically
            accessible.
    """

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
    source_created_at: Union[str, UnhydratedField, datetime] = UnhydratedField
    source_updated_at: Union[str, UnhydratedField, datetime] = UnhydratedField
    first_published_at: Union[str, UnhydratedField, datetime] = UnhydratedField

    # Internal Fields
    endpoint: str = "collection"

    def __post_init__(self):
        # Turn date fields from strings into datetimes.
        self._process_timestamps()


@dataclass(eq=False)
class Repository(Resource, MatchingMixin, HydrateMixin):
    """
    The archive or library possessing the original, physical Document.

    Attributes:
        id (str): The ID# of the Repository.
        name (str): The name of the repository
        uri (str): The URI for the Repository's metadata on the Digital Archive API.
        value (str): An alias to :attr:`~digitalarchive.models.Repository.name`
    """

    name: str
    uri: Union[str, UnhydratedField] = UnhydratedField
    value: Union[str, UnhydratedField] = UnhydratedField
    endpoint: str = "repository"


@dataclass(eq=False)
class Publisher(Resource):
    """
    An organization involved in the publication of the document.

    Attributes:
        id (str): The ID# of the Publisher.
        name (str): The name of the Publisher.
    """

    name: str
    value: str
    endpoint: str = "publisher"


@dataclass(eq=False)
class Type(Resource):
    """
    The type of a document (memo, report, etc).

    Attributes:
        id (str): The ID# of the Type.
        name (str): The name of the resource Type.
    """

    name: str


@dataclass(eq=False)
class Right(Resource):
    """
    A copyright notice attached to the Document.

    Attributes:
        id (str): The ID# of the Copyright type.
        name (str): The name of the Copyright type.
        rights (str): A description of the copyright requirements.
    """

    name: str
    rights: str


@dataclass(eq=False)
class Classification(Resource):
    """
    A classification marking applied to the original Document.

    Attributes:
        id (str): The ID# of the Classification type.
        name (str): A description of the Classification type.
    """

    name: str


@dataclass(eq=False)
class Document(Resource, MatchingMixin, HydrateMixin, TimestampsMixin):
    """
    A Document corresponding to a single record page on digitalarchive.wilsoncenter.org.

    Note:
        Avoid constructing Documents directly--use the `match` function to create
        Documents by keyword search or by ID.


    **Attributes present on all Documents:**

    Attributes:
        id (str): The ID# of the record in the DA.
        title (str): The title of a document.
        description (str): A one-sentence description of the document's content.
        doc_date (str): The date of the document's creation in ``YYYYMMDD`` format.
        frontend_doc_date (str): How the date appears when presented on the DA website.
        slug (str): A url-friendly name for the document. Not currently used.
        source_created_at(:class:`datetime.datetime`): Timestamp of when the Document was first added to the DA.
        source_updated_at(:class:`datetime.datetime`): Timestamp of when the Document was last edited.
        first_published_at(:class:`datetime.datetime`): Timestamp of when the document was first made publically
            accessible.

    **Attributes present only on hydrated Documents**

    These attributes are aliases of :class:`UnhydratedField` until :func:`Document.hydrate` is called on the Document.

    Attributes:
        source (str): The archive where the document was retrieved from.
        type (:class:`digitalarchive.models.Type`): The type of the document (meeting minutes, report, etc.)
        rights (:obj:`list` of :class:`digitalarchive.models.Right`): A list of entities holding the copyright of the
            Document.
        pdf_generated_at (str): The date that the  combined source, translations, and transcriptions PDF. was generated.
        date_range_start (:class:`datetime.date`): A rounded-down date used to standardize approximate dates for
            date-range matching.
        sort_string_by_coverage (str): An alphanumeric identifier used by the API to sort search results.
        main_src (str): The original Source that a Document was retrieved from.
        model (str): The model of a record, used to differentiate collections and keywords in searches.
        donors (:obj:`list` of :class:`digitalarchive.models.Donor`): A list of donors whose funding make the acquisiton
            or translation of a document possible.
        subjects (:obj:`list` of :class:`digitalarchive.models.Subject`): A list of subjects that the document is tagged
            with.
        transcripts (:obj:`list` of :class:`digitalarchive.models.Transcript`): A list of transcripts of the document's
            contents.
        translations (:obj:`list` of :class:`digitalarchive.models.Translation`): A list of translations of the original
            document.
        media_files (:obj:`list` of :class:`digitalarchive.models.MediaFile`): A list of attached original scans of the
            document.
        languages(:obj:`list` of  :class:`digitalarchive.models.Language`): A list of langauges contained in the
            document.
        creators (:obj:`list` of :class:`digitalarhive.models.Creator`): A list of persons who authored the document.
        original_coverages (:obj:`list` of :class:`digitalarchive.models.Coverage`): A list of geographic locations
            referenced in the document.
        collections (:obj:`list` of :class:`digitalarchive.models.Collection`): A list of Collections that contain this
            document.
        attachments (:obj:`list` of :class:`digitalarchive.models.Document`): A list of Documents that were attached to
            the Document.
        links (:obj:`list` of :class:`digitalarchive.models.Document`): A list of topically related documents.
        respositories (:obj:`list` of :class:`digitalarchive.models.Repository`): A list of archives/libraries
            containing this document.
        publishers (:obj:`list` of :class:`digitalarchive.models.Publisher`): A list of Publishers that released the
            document.
        classifications (:obj:`list` of :class:`digitalarchive.models.Publisher`): A list of security classification
            markings present on the document.
    """

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
    date_range_start: Union[str, date, UnhydratedField] = UnhydratedField
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
        """Parse lists of child objects."""

        # Parse related records
        self._parse_child_records()

        # Process DA timestamps.
        self._process_timestamps()

        # Process the date_range_start field to facilitate searches.
        if isinstance(self.date_range_start, str):
            self.date_range_start = self._parse_date_range_start(self.date_range_start)

    @classmethod
    def match(cls, **kwargs) -> matching.ResourceMatcher:
        """
        Search for a Document by keyword, or fetch one by ID.

        Matching on the Document model runs a full-text search using keywords passed via the  title and description
        keywords. Results can also be limited by dates or by related records, as described below.

        Note:
            Title and description keywords are not searched for individually. All
            non-date or child record searches are concatenated to single querystring.

        Note:
            Collection and other related record searches use `INNER JOIN` logic when
            passed multiple related resources.

        **Allowed search fields:**

        Args:
            title (:obj:`str`, optional): Title search keywords.
            description (:obj:`str`, optional): Title search keywords.
            start_date (:class:`datetime.date`, optional): Return only Documents with a `doc_date` after the passed
                `start_date`.
            end_date (:class:`datetime.date`, optional): Return only Documents with a `doc_date` before the passed
                `end_date`.
            collections (:obj:`list` of :class:`digitalarchive.models.Collection`, optional): Restrict results to
                Documents contained in all of the passed Collections.
            publishers (:obj:`list` of :class:`digitalarchive.models.Publisher`, optional): Restrict results to
                Documents published by all of the passed Publishers.
            repositories (:obj:`list` of :class:`digitalarchive.models.Repository`, optional) Restrict results to
                Documents contained in all of the passed Repositories.
            coverages (:obj:`list` of :class:`digitalarchive.models.Coverage`, optional) Restrict results to Documents
                relating to all of the passed geographical Coverages.
            subjects (:obj:`list` of :class:`digitalarchive.models.Subject`) Restrict results to Documents tagged with
                all of the passed subjects
            contributors (:obj:`list of :class:`digitalarchive.models.Contributor`) Restrict results to Documents whose
                authors include all of the passed contributors.
            donors (list(:class:`digitalarchive.models.Donor`)) Restrict results to Documents who were obtained or
                translated with support from all of the passed donors.
            languages (:class:`digitalarchive.models.Language` or str) Restrict results to Documents by language of
                original document. If passing a string, you must pass an ISO 639-2/B language code.
            translation (:class:`digitalarchive.models.Translation`) Restrict results to Documents for which there
                is a translation available in the passed Language.
            theme (:class:`digitalarchive.models.Theme`) Restrict results to Documents belonging to the passed Theme.

        Returns:
            An instance of (:class:`digitalarchive.matching.ResourceMatcher`) containing any records responsive to the
                search.
        """
        # Limit search to only Documents (this excludes Collections from search result).
        kwargs["model"] = "Record"

        # Check that search keywords are valid.
        allowed_search_fields = [
            *cls.__dataclass_fields__.keys(),
            "start_date",
            "end_date",
            "themes",
        ]
        for key in kwargs:
            if key not in allowed_search_fields:
                logging.error(
                    f"[!] {key} is not a valid search term for {cls}. Valid terms: {allowed_search_fields}"
                )
                raise exceptions.InvalidSearchFieldError

        # Process date searches if they are present.
        if any(key in kwargs.keys() for key in ["start_date", "end_date"]):
            kwargs = Document._process_date_searches(kwargs)

        # Process language searches if they are present.
        if "languages" in kwargs.keys():
            kwargs = Document._process_language_search(kwargs)

        # Process any related model searches.
        if any(
            key in kwargs.keys()
            for key in [
                "collections",
                "publishers",
                "repositories",
                "original_coverages",
                "subjects",
                "contributors",
                "donors",
                "languages",
                "translations",
                "themes",
            ]
        ):
            kwargs = Document._process_related_model_searches(kwargs)

        # Prepare the 'q' fulltext search field.
        keywords = []
        for field in ["name", "title", "description", "slug", "q"]:
            if kwargs.get(field) is not None:
                keywords.append(kwargs.pop(field))
        kwargs["q"] = " ".join(keywords)

        # Reformat fields that accept lists. This makes the queries inner joins rather than union all.
        for field in ["donor", "subject", "contributor", "coverage", "collection"]:
            if field in kwargs.keys():
                kwargs[f"{field}[]"] = kwargs.pop(field)

        # Run the match.
        return matching.ResourceMatcher(cls, **kwargs)

    def hydrate(self, recurse: bool = False):
        """
        Downloads the complete version of the Document with metadata for any related objects.

        Args:
            recurse (bool): If true, also hydrate subordinate and related records records.
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
        if recurse is True:
            [transcript.hydrate() for transcript in self.transcripts]
            [translation.hydrate() for translation in self.translations]
            [media_file.hydrate() for media_file in self.media_files]
            [collection.hydrate() for collection in self.collections]

    def _parse_child_records(self):
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
            "donors": Donor,
            "type": Type,
            "rights": Right,
        }

        # If we are dealing with an unhydrated record, don't attempt to process child records.
        for field in child_fields:
            if self.__getattribute__(field) is UnhydratedField:
                continue

            # If we are dealing with a dict, parse it and update self.
            elif isinstance(self.__getattribute__(field), dict):
                parsed_resource = child_fields[field](**self.__getattribute__(field))
                setattr(self, field, parsed_resource)

            # Rights are the only field that isn't a list, so we have special handling here to bail out of loop.
            elif isinstance(self.__getattribute__(field), Right):
                continue

            # # If record is hydrated, transform child records to appropriate model.
            # Check if list is empty, skip if yes.
            elif len(self.__getattribute__(field)) == 0:
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

    @staticmethod
    def _parse_date_range_start(doc_date: str) -> date:
        """Transform a DA-style date string to a Python datetime."""
        year = int(doc_date[:4])
        month = int(doc_date[4:6])
        day = int(doc_date[-2:])
        return date(year, month, day)

    @staticmethod
    def _process_date_searches(query: dict) -> dict:
        """Run formatting and type checks against  date search fields."""
        date_search_terms = ["start_date", "end_date"]

        # Handle open-ended date searches.
        if "start_date" in query.keys() and "end_date" not in query.keys():
            query["end_date"] = date.today()
        elif "end_date" in query.keys() and "start_date" not in query.keys():
            # Pull earliest record date from API.
            da_date_range = api.get_date_range()
            start_date = Document._parse_date_range_start(da_date_range["begin"])
            query["start_date"] = start_date

        # Transform datetime objects into formatted string and return
        for field in date_search_terms:
            search_date = query[field]
            if isinstance(search_date, date):
                query[
                    field
                ] = f"{search_date.year}{search_date.strftime('%m')}{search_date.strftime('%d')}"

            # If passed a string but its wrong length, raise.
            elif isinstance(search_date, str) and len(search_date) != 8:
                logging.error("[!] Invalid date string! Format is: YYYYMMDD")
                raise exceptions.MalformedDateSearch

            # If something else passed as keyword, bail out.
            elif not (isinstance(search_date, str) or isinstance(search_date, date)):
                logging.error("[!] Dates must be type str or datetime.date")
                raise exceptions.MalformedDateSearch

        # Return the reformatted query
        return query

    @staticmethod
    def _process_related_model_searches(query: dict) -> dict:
        """
        Process and format searches by related models.

        We have to re-name the fields from plural to singular to match the DA format.
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
            if key in query.keys():
                query[value] = query.pop(key)

        # Build list of terms we need to parse
        terms_to_parse = []
        for term in multi_terms.values():
            if term in query.keys():
                terms_to_parse.append(term)

        # transform each term list into a list of IDs
        for term in terms_to_parse:
            query[term] = [str(item.id) for item in query[term]]

        # Special handling for langauges, translations, themes.
        # Unlike they above, they only accept singular values
        for term in ["language", "translation", "theme"]:
            if term in query.keys():
                if len(query[term]) > 1:
                    logging.error(f"[!] Cannot filter for more than one {term}")
                    raise exceptions.InvalidSearchFieldError
                # Pull out the singleton.
                query[term] = query[term][0]

        # Return the reformatted query.
        return query

    @staticmethod
    def _process_language_search(query: dict) -> dict:
        """
        Process a language search

        Looks up the DA's language ID# for user provided ISO 639-2/B language codes and updates the query.

        Args:
            query (dict): A ResourceMatcher query.

        Returns:
            dict: A query dict with a ISO 639-2/B string replaced with appropriate Language object.
        """
        parsed_languages = []
        for language in query["languages"]:
            # Check if ID# is instance of language, bail on yes.
            if isinstance(language, Language):
                parsed_languages.append(language)

            # If str, lookup ID# of language
            elif isinstance(language, str) and len(language) == 3:
                parsed_languages.append(Language(id=language))

            else:
                raise exceptions.MalformedLanguageSearch

            # Replace kwarg with Langauge object.
            query["languages"] = parsed_languages
            return query


@dataclass(eq=False)
class Theme(Resource, HydrateMixin):
    """
    A parent container for collections on a single geopolitical topic.

    Note:
        Themes never appear on any record model, but can be passed as a search param to Document.

    Attributes:
        id (str): The ID# of the Theme.
        slug (str): A url-friendly version of the theme title.
        title (str): The name of the Theme.
        description (str): A short description of the Theme contents.
        main_src: A URI for the Theme's banner image on the Digital Archive website.
        has_map (str): A boolean value for whether the Theme has an accompanying map on the Digital Archive website.
        has_timeline(str) : A boolean value for whether the Theme has a Timeline on the Digital Archive website.
        featured_collections (list of :class:`~digitalarchive.models.Collection`): A list of related collections.
        dates_with_events (list): A list of date ranges that the Theme has timeline entries for.
    """

    # Required fields
    slug: str

    # Optional Fields
    title: Union[str, UnhydratedField] = UnhydratedField
    value: Union[str, UnhydratedField] = UnhydratedField
    description: Union[str, UnhydratedField] = UnhydratedField
    main_src: Union[str, UnhydratedField] = UnhydratedField
    uri: Union[str, UnhydratedField] = UnhydratedField
    featured_resources: Union[List[dict], UnhydratedField] = UnhydratedField
    has_map: Union[str, UnhydratedField] = UnhydratedField
    has_timeline: Union[str, UnhydratedField] = UnhydratedField
    featured_collections: Union[List[Collection], UnhydratedField] = UnhydratedField
    dates_with_events: Union[list, UnhydratedField] = UnhydratedField

    # Private fields.
    endpoint: str = "theme"

    def __post_init__(self):
        """Parse out any child collections that were passed"""
        if self.featured_collections is not UnhydratedField:
            parsed_collections = []
            for collection in self.featured_collections:
                if isinstance(collection, Collection):
                    parsed_collections.append(collection)
                else:
                    parsed_collections.append(Collection(**collection))

            self.featured_collections = parsed_collections

    def pull(self):
        """
        Downloads the complete Theme object from the DA and re-initializes the dataclass..

        Note: The Theme pull method differs from from the pull methods of other models as Themes use the `slug`
        attribute as a primary key, rather than the `id` attribute.
        """
        data = api.get(endpoint=self.endpoint, resource_id=self.slug)
        self.__init__(**data)
